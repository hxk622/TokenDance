"""Authentication API endpoints with multiple auth providers."""
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.dependencies import get_auth_service, get_current_user
from app.core.logging import get_logger
from app.models.user import User
from app.schemas.user import (
    LoginResponse,
    RefreshTokenRequest,
    RegisterResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import (
    AuthService,
    GmailAuthRequest,
    WeChatAuthRequest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user with email and password.

    Args:
        user_data: User registration data
        auth_service: Authentication service

    Returns:
        User, token pair, and default workspace ID

    Raises:
        HTTPException: If email or username already exists or validation fails
    """
    try:
        user, tokens, workspace = await auth_service.register(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
        )

        return RegisterResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
            ),
            default_workspace_id=workspace.id if workspace else "",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Login user with email and password.

    Args:
        credentials: User login credentials
        auth_service: Authentication service

    Returns:
        User, token pair, and default workspace ID

    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        user, tokens, default_workspace_id = await auth_service.login(
            email=credentials.email,
            password=credentials.password,
        )

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
            ),
            default_workspace_id=default_workspace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get("/wechat/authorize")
async def wechat_authorize():
    """Get WeChat OAuth authorization URL.

    Returns:
        Authorization URL for WeChat login
    """
    from app.services.wechat_oauth_service import WeChatOAuthService

    wechat_service = WeChatOAuthService()
    auth_url = wechat_service.get_authorization_url(
        redirect_uri=settings.WECHAT_REDIRECT_URI
    )

    return {"authorization_url": auth_url}


@router.post("/wechat/callback", response_model=LoginResponse)
async def wechat_callback(
    request: WeChatAuthRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Handle WeChat OAuth callback.

    Args:
        request: WeChat OAuth request with authorization code
        auth_service: Authentication service

    Returns:
        User and token pair

    Raises:
        HTTPException: If WeChat OAuth fails
    """
    try:
        user, tokens, default_workspace_id = await auth_service.login_with_wechat(
            code=request.code
        )

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
            ),
            default_workspace_id=default_workspace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get("/gmail/authorize")
async def gmail_authorize():
    """Get Gmail OAuth authorization URL.

    Returns:
        Authorization URL for Gmail login
    """
    from app.services.gmail_oauth_service import GmailOAuthService

    gmail_service = GmailOAuthService()
    auth_url = gmail_service.get_authorization_url()

    return {"authorization_url": auth_url}


@router.post("/gmail/callback", response_model=LoginResponse)
async def gmail_callback(
    request: GmailAuthRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Handle Gmail OAuth callback.

    Args:
        request: Gmail OAuth request with authorization code
        auth_service: Authentication service

    Returns:
        User and token pair

    Raises:
        HTTPException: If Gmail OAuth fails
    """
    try:
        user, tokens, default_workspace_id = await auth_service.login_with_gmail(
            code=request.code
        )

        return LoginResponse(
            user=UserResponse.model_validate(user),
            tokens=TokenResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_type=tokens.token_type,
            ),
            default_workspace_id=default_workspace_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request
        auth_service: Authentication service

    Returns:
        New token pair

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)

        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        User information
    """
    return UserResponse.model_validate(current_user)
