"""Authentication service - JWT and password management."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    email: str
    exp: datetime


class TokenPair(BaseModel):
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class AuthService:
    """Authentication service for user registration and login."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plain password.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: str, email: str) -> str:
        """Create JWT access token.
        
        Args:
            user_id: User UUID string
            email: User email
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: str, email: str) -> str:
        """Create JWT refresh token.
        
        Args:
            user_id: User UUID string
            email: User email
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode JWT token.
        
        Args:
            token: JWT token string
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            TokenData if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            if payload.get("type") != token_type:
                logger.warning(
                    "token_type_mismatch",
                    expected=token_type,
                    actual=payload.get("type"),
                )
                return None
            
            return TokenData(
                user_id=payload["user_id"],
                email=payload["email"],
                exp=datetime.fromtimestamp(payload["exp"]),
            )
        except JWTError as e:
            logger.warning("jwt_decode_error", error=str(e))
            return None

    async def register(
        self,
        email: str,
        username: str,
        password: str,
    ) -> tuple[User, TokenPair]:
        """Register a new user.
        
        Args:
            email: User email
            username: Username
            password: Plain text password
            
        Returns:
            Tuple of (User, TokenPair)
            
        Raises:
            ValueError: If email or username already exists
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            logger.info("registration_failed_email_exists", email=email)
            raise ValueError("Email already registered")
        
        # Check if username already exists
        existing_username = await self.user_repo.get_by_username(username)
        if existing_username:
            logger.info("registration_failed_username_exists", username=username)
            raise ValueError("Username already taken")
        
        # Hash password and create user
        password_hash = self.hash_password(password)
        user = await self.user_repo.create(
            email=email,
            username=username,
            password_hash=password_hash,
        )
        
        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)
        
        logger.info("user_registered", user_id=str(user.id), email=user.email)
        
        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, email: str, password: str) -> tuple[User, TokenPair]:
        """Login user with email and password.
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Tuple of (User, TokenPair)
            
        Raises:
            ValueError: If credentials are invalid
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)
        if not user:
            logger.info("login_failed_user_not_found", email=email)
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            logger.info("login_failed_user_inactive", user_id=str(user.id))
            raise ValueError("Account is inactive")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            logger.info("login_failed_wrong_password", user_id=str(user.id))
            raise ValueError("Invalid credentials")
        
        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)
        
        logger.info("user_logged_in", user_id=str(user.id), email=user.email)
        
        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenPair:
        """Generate new access token using refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            New TokenPair
            
        Raises:
            ValueError: If refresh token is invalid
        """
        token_data = self.verify_token(refresh_token, token_type="refresh")
        if not token_data:
            raise ValueError("Invalid refresh token")
        
        # Verify user still exists and is active
        user = await self.user_repo.get_by_email(token_data.email)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Generate new tokens
        access_token = self.create_access_token(str(user.id), user.email)
        new_refresh_token = self.create_refresh_token(str(user.id), user.email)
        
        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )
