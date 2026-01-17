"""
Artifact Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.artifact import ArtifactType

# ============ Base Schemas ============

class ArtifactBase(BaseModel):
    """Base artifact schema."""
    name: str = Field(..., max_length=255)
    description: str | None = None
    artifact_type: ArtifactType


# ============ Create Schemas ============

class ArtifactCreate(ArtifactBase):
    """Schema for creating an artifact."""
    session_id: str
    file_path: str
    file_size: int = 0
    mime_type: str | None = None
    parent_step: str | None = None
    parent_message_id: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class KVSnapshotCreate(BaseModel):
    """Schema for creating a KV-Cache snapshot artifact."""
    session_id: str
    name: str
    file_path: str
    kv_anchor_id: str
    context_length: int
    model: str
    file_size: int = 0


# ============ Update Schemas ============

class ArtifactUpdate(BaseModel):
    """Schema for updating an artifact."""
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    preview_url: str | None = None
    thumbnail_url: str | None = None
    extra_data: dict[str, Any] | None = None


# ============ Response Schemas ============

class ArtifactResponse(ArtifactBase):
    """Schema for artifact response."""
    id: str
    session_id: str
    file_path: str
    file_size: int
    mime_type: str | None = None
    preview_url: str | None = None
    thumbnail_url: str | None = None
    download_url: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)  #



class ArtifactDetail(ArtifactResponse):
    """Detailed artifact response."""
    parent_step: str | None = None
    parent_message_id: str | None = None
    kv_anchor_id: str | None = None
    context_length: int | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class ArtifactList(BaseModel):
    """List of artifacts."""
    items: list[ArtifactResponse]
    total: int


# ============ PPT Specific Schemas ============

class PPTPage(BaseModel):
    """PPT page schema for preview."""
    index: int
    thumbnail_url: str | None = None
    content: str | None = None


class PPTPreview(BaseModel):
    """PPT preview schema."""
    artifact_id: str
    name: str
    pages: list[PPTPage]
    total_pages: int


class RegeneratePageRequest(BaseModel):
    """Request to regenerate a PPT page."""
    page_index: int
    instructions: str | None = None
