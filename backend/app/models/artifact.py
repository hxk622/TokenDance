"""
Artifact model - represents outputs/deliverables from a project.

In the Project-First architecture, Artifact is the primary output of a Project.
It supports versioning for rollback and comparison.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.session import Session


class ArtifactType(PyEnum):
    """Artifact type enum."""
    DOCUMENT = "document"    # Markdown, PDF documents
    PPT = "ppt"              # PowerPoint presentations
    REPORT = "report"        # Research reports
    CODE = "code"            # Code files
    DATA = "data"            # CSV, JSON data files
    IMAGE = "image"          # Generated images, screenshots
    KV_SNAPSHOT = "kv_snapshot"  # KV-Cache snapshot for context restoration


class Artifact(Base):
    """
    Artifact model - outputs generated during a project.

    Features:
    - Various types (document, ppt, report, code, data, image, kv_snapshot)
    - Links to file storage (MinIO)
    - Tracks parent step for context (which step generated this)
    - Supports KV-Cache snapshots for "Contextual Hot-link"
    - Version control with parent_version_id chain
    - Content preview for quick display
    """

    __tablename__ = "artifacts"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Project relationship (new in Project-First architecture)
    project_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True, index=True  # Nullable for migration period
    )

    # Session relationship (kept for backward compatibility, will be deprecated)
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=True, index=True  # Changed to nullable
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # File storage
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO path
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # bytes
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Preview (for documents, PPTs)
    preview_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Version control (new in Project-First architecture)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("artifacts.id", ondelete="SET NULL"),
        nullable=True
    )  # Points to previous version of this artifact
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Content preview (for quick display without loading full content)
    content_preview: Mapped[str | None] = mapped_column(Text, nullable=True)  # First ~500 chars
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Context linking
    parent_step: Mapped[str | None] = mapped_column(String(100), nullable=True)  # step_id that created this
    parent_message_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # KV-Cache anchor (for kv_snapshot type)
    kv_anchor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    context_length: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Extra data (named 'extra_data' to avoid conflict with SQLAlchemy reserved 'metadata')
    extra_data: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="artifacts",
        foreign_keys=[project_id]
    )
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="artifacts",
        foreign_keys=[session_id]
    )
    # Self-referential relationship for version chain
    parent_version: Mapped["Artifact | None"] = relationship(
        "Artifact",
        remote_side=[id],
        foreign_keys=[parent_version_id]
    )

    def __repr__(self) -> str:
        return f"<Artifact(id={self.id}, name={self.name}, type={self.artifact_type.value})>"

    @property
    def is_document(self) -> bool:
        """Check if this is a document artifact."""
        return self.artifact_type == ArtifactType.DOCUMENT

    @property
    def is_ppt(self) -> bool:
        """Check if this is a PPT artifact."""
        return self.artifact_type == ArtifactType.PPT

    @property
    def is_kv_snapshot(self) -> bool:
        """Check if this is a KV-Cache snapshot."""
        return self.artifact_type == ArtifactType.KV_SNAPSHOT

    @property
    def download_url(self) -> str:
        """Generate download URL for this artifact."""
        # This will be resolved by the file service
        return f"/api/v1/artifacts/{self.id}/download"

    def get_file_extension(self) -> str:
        """Get file extension from name."""
        if "." in self.name:
            return self.name.rsplit(".", 1)[-1].lower()
        return ""

    def set_content_preview(self, content: str, max_length: int = 500) -> None:
        """Set content preview from full content."""
        self.content_preview = content[:max_length] if content else None
        self.word_count = len(content.split()) if content else 0

    def create_new_version(self, content: str | None = None) -> "Artifact":
        """Create a new version of this artifact.

        Returns a new Artifact instance with:
        - Incremented version number
        - parent_version_id pointing to this artifact
        - This artifact's is_latest set to False
        """
        new_artifact = Artifact(
            project_id=self.project_id,
            session_id=self.session_id,
            name=self.name,
            description=self.description,
            artifact_type=self.artifact_type,
            file_path=self.file_path,  # Will be updated with actual new path
            file_size=self.file_size,
            mime_type=self.mime_type,
            version=self.version + 1,
            parent_version_id=self.id,
            is_latest=True,
        )
        self.is_latest = False
        return new_artifact

    @classmethod
    def create_kv_snapshot(
        cls,
        session_id: str,
        name: str,
        file_path: str,
        kv_anchor_id: str,
        context_length: int,
        model: str,
        file_size: int = 0
    ) -> "Artifact":
        """Factory method to create a KV-Cache snapshot artifact."""
        return cls(
            session_id=session_id,
            name=name,
            artifact_type=ArtifactType.KV_SNAPSHOT,
            file_path=file_path,
            file_size=file_size,
            kv_anchor_id=kv_anchor_id,
            context_length=context_length,
            extra_data={
                "model": model,
                "snapshot_type": "kv_cache"
            }
        )
