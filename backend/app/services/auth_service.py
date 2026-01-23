"""Authentication service - JWT and password management with multiple auth providers."""
import re
from datetime import datetime, timedelta

from jose import JWTError, jwt

from app.core.datetime_utils import utc_now_naive
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator

from app.core.config import settings
from app.core.logging import get_logger
from app.models.user import AuthProvider, User
from app.models.workspace import Workspace
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.services.gmail_oauth_service import GmailOAuthService
from app.services.wechat_oauth_service import WeChatOAuthService

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

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', v):
            raise ValueError('Username must be 4-20 characters, letters, numbers, and underscores only')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class WeChatAuthRequest(BaseModel):
    """WeChat OAuth request."""
    code: str
    state: str | None = None


class GmailAuthRequest(BaseModel):
    """Gmail OAuth request."""
    code: str
    state: str | None = None


class AuthService:
    """Authentication service for user registration and login with multiple providers."""

    def __init__(self, user_repo: UserRepository, workspace_repo: WorkspaceRepository | None = None):
        self.user_repo = user_repo
        self.workspace_repo = workspace_repo
        self.wechat_service = WeChatOAuthService()
        self.gmail_service = GmailOAuthService()

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
        expire = utc_now_naive() + timedelta(
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
        expire = utc_now_naive() + timedelta(
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
    def verify_token(token: str, token_type: str = "access") -> TokenData | None:
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
            logger.error("jwt_decode_error", error=str(e))
            return None

    async def register(
        self,
        email: str,
        username: str,
        password: str,
    ) -> tuple[User, TokenPair, Workspace]:
        """Register a new user with email and password.

        Args:
            email: User email
            username: Username
            password: Plain text password

        Returns:
            Tuple of (User, TokenPair, Workspace)

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
            auth_provider=AuthProvider.EMAIL_PASSWORD.value,
        )

        # Create default workspace for the user
        workspace = None
        if self.workspace_repo:
            workspace = await self.workspace_repo.create(
                owner_id=str(user.id),
                name="默认工作区",
                slug="default",
                description="Your personal workspace",
            )
            logger.info(
                "default_workspace_created",
                user_id=str(user.id),
                workspace_id=workspace.id,
            )

        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)

        logger.info("user_registered", user_id=str(user.id), email=user.email)

        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        ), workspace

    async def login(self, email: str, password: str) -> tuple[User, TokenPair, str | None]:
        """Login user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Tuple of (User, TokenPair, default_workspace_id)

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

        # Get user's default workspace, create if not exists
        default_workspace_id = None
        if self.workspace_repo:
            workspaces, _ = await self.workspace_repo.get_by_owner(str(user.id), limit=1)
            if workspaces:
                default_workspace_id = workspaces[0].id
            else:
                # Auto-create default workspace for existing user
                workspace = await self.workspace_repo.create(
                    owner_id=str(user.id),
                    name="默认工作区",
                    slug="default",
                    description="Your personal workspace",
                )
                default_workspace_id = workspace.id
                logger.info(
                    "default_workspace_created_on_login",
                    user_id=str(user.id),
                    workspace_id=workspace.id,
                )

        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)

        logger.info("user_logged_in", user_id=str(user.id), email=user.email)

        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        ), default_workspace_id

    async def login_with_wechat(self, code: str) -> tuple[User, TokenPair]:
        """Login or register user with WeChat OAuth.

        Args:
            code: WeChat authorization code

        Returns:
            Tuple of (User, TokenPair)

        Raises:
            ValueError: If WeChat OAuth fails
        """
        # Get access token from WeChat
        token_data = await self.wechat_service.get_access_token(code)
        if not token_data:
            raise ValueError("Failed to get WeChat access token")

        access_token = token_data.get("access_token")
        openid = token_data.get("openid")

        # Get user info from WeChat
        user_info = await self.wechat_service.get_user_info(access_token, openid)
        if not user_info:
            raise ValueError("Failed to get WeChat user info")

        # Check if user already exists by WeChat OpenID
        user = await self.user_repo.get_by_wechat_openid(openid)

        if user:
            # User exists, update info if needed
            if user_info.get("nickname") != user.wechat_nickname:
                user = await self.user_repo.update_wechat_info(
                    user_id=user.id,
                    openid=openid,
                    unionid=token_data.get("unionid"),
                    nickname=user_info.get("nickname"),
                    headimgurl=user_info.get("headimgurl"),
                )
        else:
            # Create new user
            username = self.wechat_service.generate_username(user_info.get("nickname"))
            email = self.wechat_service.generate_email(openid)

            # Check if username already exists
            existing_username = await self.user_repo.get_by_username(username)
            if existing_username:
                username = f"{username}_{openid[:4]}"

            user = await self.user_repo.create(
                email=email,
                username=username,
                auth_provider=AuthProvider.WECHAT.value,
                display_name=user_info.get("nickname"),
                avatar_url=user_info.get("headimgurl"),
            )

            # Update WeChat info
            user = await self.user_repo.update_wechat_info(
                user_id=user.id,
                openid=openid,
                unionid=token_data.get("unionid"),
                nickname=user_info.get("nickname"),
                headimgurl=user_info.get("headimgurl"),
            )

        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)

        logger.info("user_logged_in_wechat", user_id=str(user.id), openid=openid)

        return user, TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login_with_gmail(self, code: str) -> tuple[User, TokenPair]:
        """Login or register user with Gmail OAuth.

        Args:
            code: Gmail authorization code

        Returns:
            Tuple of (User, TokenPair)

        Raises:
            ValueError: If Gmail OAuth fails
        """
        # Get access token from Google
        token_data = await self.gmail_service.get_access_token(code)
        if not token_data:
            raise ValueError("Failed to get Gmail access token")

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        # Get user info from Google
        user_info = await self.gmail_service.get_user_info(access_token)
        if not user_info:
            raise ValueError("Failed to get Gmail user info")

        sub = user_info.get("sub")
        gmail_email = user_info.get("email")

        # Check if user already exists by Gmail sub
        user = await self.user_repo.get_by_gmail_sub(sub)

        if user:
            # User exists, update info if needed
            expires_at = None
            if token_data.get("expires_in"):
                expires_at = utc_now_naive() + timedelta(seconds=token_data["expires_in"])

            user = await self.user_repo.update_gmail_info(
                user_id=user.id,
                sub=sub,
                email=gmail_email,
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
        else:
            # Create new user
            username = self.gmail_service.generate_username(
                user_info.get("name"),
                gmail_email
            )

            # Check if username already exists
            existing_username = await self.user_repo.get_by_username(username)
            if existing_username:
                username = f"{username}_{sub[:4]}"

            expires_at = None
            if token_data.get("expires_in"):
                expires_at = utc_now_naive() + timedelta(seconds=token_data["expires_in"])

            user = await self.user_repo.create(
                email=gmail_email,
                username=username,
                auth_provider=AuthProvider.GMAIL.value,
                display_name=user_info.get("name"),
                avatar_url=user_info.get("picture"),
            )

            # Update Gmail info
            user = await self.user_repo.update_gmail_info(
                user_id=user.id,
                sub=sub,
                email=gmail_email,
                name=user_info.get("name"),
                picture=user_info.get("picture"),
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )

        # Generate tokens
        access_token = self.create_access_token(str(user.id), user.email)
        refresh_token = self.create_refresh_token(str(user.id), user.email)

        logger.info("user_logged_in_gmail", user_id=str(user.id), sub=sub)

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
