"""
Project Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.project import ProjectStatus, ProjectType

# ============ Context Schemas ============

class ProjectContext(BaseModel):
    """Project context schema."""
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    failures: list[dict[str, Any]] = Field(default_factory=list)
    key_findings: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ProjectSettings(BaseModel):
    """Project settings schema."""
    llm_model: str = "claude-3-5-sonnet-20241022"
    skill_id: str | None = None


# ============ Base Schemas ============

class ProjectBase(BaseModel):
    """Base project schema."""
    title: str = Field(..., max_length=200)
    description: str | None = None
    project_type: ProjectType = ProjectType.QUICK_TASK


# ============ Create Schemas ============

class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    workspace_id: str = Field(..., description="Workspace ID")
    intent: str = Field(..., description="User's original intent")
    title: str | None = Field(None, max_length=200, description="Project title (auto-generated if not provided)")
    description: str | None = None
    project_type: ProjectType = Field(default=ProjectType.QUICK_TASK)
    settings: ProjectSettings | None = None


# ============ Update Schemas ============

class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    status: ProjectStatus | None = None
    context: ProjectContext | None = None
    settings: ProjectSettings | None = None


class ProjectStatusUpdate(BaseModel):
    """Schema for updating project status only."""
    status: ProjectStatus


# ============ Response Schemas ============

class ProjectResponse(ProjectBase):
    """Schema for project response."""
    id: str
    workspace_id: str
    status: ProjectStatus
    intent: str
    total_tokens_used: int = 0
    conversation_count: int = 0
    artifact_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetail(ProjectResponse):
    """Detailed project response with context and settings."""
    context: ProjectContext = Field(default_factory=ProjectContext)
    settings: ProjectSettings = Field(default_factory=ProjectSettings)


class ProjectList(BaseModel):
    """Paginated list of projects."""
    items: list[ProjectResponse]
    total: int
    limit: int
    offset: int


# ============ Internal Schemas ============

class ProjectInDB(ProjectBase):
    """Project as stored in database."""
    id: str
    workspace_id: str
    status: ProjectStatus
    intent: str
    context: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    total_tokens_used: int = 0
    conversation_count: int = 0
    artifact_count: int = 0
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
