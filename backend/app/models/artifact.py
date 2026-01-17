"""
Artifact model - represents outputs/deliverables from a session.
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
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
    Artifact model - outputs generated during a session.

    Features:
    - Various types (document, ppt, report, code, data, image, kv_snapshot)
    - Links to file storage (MinIO)
    - Tracks parent step for context (which step generated this)
    - Supports KV-Cache snapshots for "Contextual Hot-link"
    """

    __tablename__ = "artifacts"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Session relationship
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType), nullable=False
    )

    # File storage
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO path
    file_size: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # bytes
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Preview (for documents, PPTs)
    preview_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

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
    session: Mapped["Session"] = relationship("Session", back_populates="artifacts")

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
