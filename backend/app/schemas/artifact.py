"""
Artifact Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactType


# ============ Base Schemas ============

class ArtifactBase(BaseModel):
    """Base artifact schema."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    artifact_type: ArtifactType


# ============ Create Schemas ============

class ArtifactCreate(ArtifactBase):
    """Schema for creating an artifact."""
    session_id: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    parent_step: Optional[str] = None
    parent_message_id: Optional[str] = None
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
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None


# ============ Response Schemas ============

class ArtifactResponse(ArtifactBase):
    """Schema for artifact response."""
    id: str
    session_id: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    download_url: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactDetail(ArtifactResponse):
    """Detailed artifact response."""
    parent_step: Optional[str] = None
    parent_message_id: Optional[str] = None
    kv_anchor_id: Optional[str] = None
    context_length: Optional[int] = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class ArtifactList(BaseModel):
    """List of artifacts."""
    items: list[ArtifactResponse]
    total: int


# ============ PPT Specific Schemas ============

class PPTPage(BaseModel):
    """PPT page schema for preview."""
    index: int
    thumbnail_url: Optional[str] = None
    content: Optional[str] = None


class PPTPreview(BaseModel):
    """PPT preview schema."""
    artifact_id: str
    name: str
    pages: list[PPTPage]
    total_pages: int


class RegeneratePageRequest(BaseModel):
    """Request to regenerate a PPT page."""
    page_index: int
    instructions: Optional[str] = None
