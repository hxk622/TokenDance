"""Dependency injection for FastAPI."""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import WorkspaceRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.agent_config_repository import (
    AgentConfigRepository,
    LLMProviderRepository,
    LLMModelRepository
)
from app.services.auth_service import AuthService
from app.services.permission_service import PermissionService
from app.services.agent_config_service import AgentConfigService
from app.services.agent_service import AgentService
from app.core.config import Settings, get_settings

logger = get_logger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.
    
    Yields:
        AsyncSession instance
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """Get UserRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        UserRepository instance
    """
    return UserRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repo),
) -> AuthService:
    """Get AuthService instance.
    
    Args:
        user_repo: UserRepository instance
        
    Returns:
        AuthService instance
    """
    return AuthService(user_repo)


def get_workspace_repo(db: AsyncSession = Depends(get_db)) -> WorkspaceRepository:
    """Get WorkspaceRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        WorkspaceRepository instance
    """
    return WorkspaceRepository(db)


def get_session_repo(db: AsyncSession = Depends(get_db)) -> SessionRepository:
    """Get SessionRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        SessionRepository instance
    """
    return SessionRepository(db)


def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """Get PermissionService instance.
    
    Args:
        db: Database session
        
    Returns:
        PermissionService instance
    """
    return PermissionService(db)


def get_agent_config_repo(db: AsyncSession = Depends(get_db)) -> AgentConfigRepository:
    """Get AgentConfigRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        AgentConfigRepository instance
    """
    return AgentConfigRepository(db)


def get_llm_provider_repo(db: AsyncSession = Depends(get_db)) -> LLMProviderRepository:
    """Get LLMProviderRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        LLMProviderRepository instance
    """
    return LLMProviderRepository(db)


def get_llm_model_repo(db: AsyncSession = Depends(get_db)) -> LLMModelRepository:
    """Get LLMModelRepository instance.
    
    Args:
        db: Database session
        
    Returns:
        LLMModelRepository instance
    """
    return LLMModelRepository(db)


def get_agent_config_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings)
) -> AgentConfigService:
    """Get AgentConfigService instance.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        AgentConfigService instance
    """
    return AgentConfigService(db, settings)


def get_agent_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    config_service: AgentConfigService = Depends(get_agent_config_service)
) -> AgentService:
    """Get AgentService instance.
    
    Args:
        db: Database session
        settings: Application settings
        config_service: AgentConfigService instance
        
    Returns:
        AgentService instance
    """
    return AgentService(db, settings, config_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Authorization header credentials
        user_repo: UserRepository instance
        
    Returns:
        Current User instance
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    token_data = AuthService.verify_token(token, token_type="access")
    if not token_data:
        logger.warning("authentication_failed_invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await user_repo.get_by_email(token_data.email)
    if not user:
        logger.warning(
            "authentication_failed_user_not_found",
            user_id=token_data.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(
            "authentication_failed_user_inactive",
            user_id=str(user.id),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )
    
    return user
