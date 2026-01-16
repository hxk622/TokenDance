from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.agent_config_repository import (
    AgentConfigRepository,
    LLMProviderRepository,
    LLMModelRepository
)
from app.schemas.agent_config import (
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentConfigResponse,
    AgentConfigListResponse,
    LLMProviderResponse,
    LLMModelResponse
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/agent-configs", tags=["Agent Configurations"])


@router.post("", response_model=AgentConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_config(
    config_data: AgentConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent configuration"""
    permission_service = PermissionService(db)
    
    # Check workspace access
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=config_data.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    repo = AgentConfigRepository(db)
    config = await repo.create(
        created_by=current_user.id,
        **config_data.model_dump()
    )
    
    return config


@router.get("", response_model=AgentConfigListResponse)
async def list_agent_configs(
    workspace_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List agent configurations for a workspace"""
    permission_service = PermissionService(db)
    
    # Check workspace access
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    repo = AgentConfigRepository(db)
    items, total = await repo.get_by_workspace(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset
    )
    
    return AgentConfigListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{config_id}", response_model=AgentConfigResponse)
async def get_agent_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent configuration by ID"""
    repo = AgentConfigRepository(db)
    config = await repo.get_by_id(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=config.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    return config


@router.patch("/{config_id}", response_model=AgentConfigResponse)
async def update_agent_config(
    config_id: str,
    config_data: AgentConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update agent configuration"""
    repo = AgentConfigRepository(db)
    config = await repo.get_by_id(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=config.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    # Update configuration
    updated_config = await repo.update(
        config_id,
        updated_by=current_user.id,
        **config_data.model_dump(exclude_unset=True)
    )
    
    return updated_config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete agent configuration"""
    repo = AgentConfigRepository(db)
    config = await repo.get_by_id(config_id)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent configuration not found"
        )
    
    # Check workspace access
    permission_service = PermissionService(db)
    has_access = await permission_service.check_workspace_access(
        user_id=current_user.id,
        workspace_id=config.workspace_id
    )
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace"
        )
    
    success = await repo.delete(config_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete agent configuration"
        )


@router.get("/providers", response_model=List[LLMProviderResponse])
async def list_llm_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available LLM providers"""
    repo = LLMProviderRepository(db)
    providers = await repo.get_all(active_only=True)
    return providers


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
async def get_llm_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get LLM provider by ID"""
    repo = LLMProviderRepository(db)
    provider = await repo.get_by_id(provider_id)
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM provider not found"
        )
    
    return provider


@router.get("/providers/{provider_id}/models", response_model=List[LLMModelResponse])
async def list_llm_models(
    provider_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List LLM models for a provider"""
    repo = LLMModelRepository(db)
    models = await repo.get_by_provider(provider_id, active_only=True)
    return models


@router.get("/models", response_model=List[LLMModelResponse])
async def list_all_llm_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available LLM models"""
    repo = LLMModelRepository(db)
    models = await repo.get_all(active_only=True)
    return models
