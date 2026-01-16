"""
Workspace Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.workspace import WorkspaceType


# ============ Base Schemas ============

class WorkspaceBase(BaseModel):
    """Base workspace schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)


# ============ Create Schemas ============

class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a new workspace."""
    workspace_type: Optional[WorkspaceType] = Field(
        WorkspaceType.PERSONAL,
        description="Workspace type (PERSONAL or TEAM)"
    )


# ============ Update Schemas ============

class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=500)
    settings: Optional[dict] = None


# ============ Response Schemas ============

class WorkspaceResponse(WorkspaceBase):
    """Schema for workspace response."""
    id: str
    workspace_type: WorkspaceType
    owner_id: str
    team_id: Optional[str] = None
    filesystem_path: str
    settings: dict = Field(default_factory=dict)
    stats: dict = Field(default_factory=dict)
    session_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkspaceDetail(WorkspaceResponse):
    """Detailed workspace response with extended info."""
    pass


class WorkspaceList(BaseModel):
    """Paginated list of workspaces."""
    items: list[WorkspaceResponse]
    total: int
    limit: int
    offset: int


# ============ Internal Schemas ============

class WorkspaceInDB(WorkspaceBase):
    """Workspace as stored in database."""
    id: str
    workspace_type: WorkspaceType
    owner_id: str
    team_id: Optional[str] = None
    filesystem_path: str
    settings: dict = Field(default_factory=dict)
    stats: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
