"""
ProjectVersion model - represents a version snapshot of a project.

Supports rollback functionality by storing snapshots of:
- Artifact states at a specific point in time
- Context state (decisions, findings, etc.)
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.project import Project


class VersionChangeType(PyEnum):
    """Type of change that triggered version creation.

    - AUTO: Automatic version created by AI modification
    - MANUAL: Manual save point created by user
    - MILESTONE: Significant milestone (e.g., draft complete)
    - ROLLBACK: Version created from rollback operation
    """
    AUTO = "auto"
    MANUAL = "manual"
    MILESTONE = "milestone"
    ROLLBACK = "rollback"


class ProjectVersion(Base):
    """
    ProjectVersion model - a snapshot of project state.

    Features:
    - Stores artifact IDs at a specific point in time
    - Stores context snapshot (decisions, failures, findings)
    - Supports rollback to any previous version
    - Tracks who/what created the version (user or AI)
    """

    __tablename__ = "project_versions"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Project relationship
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Version number (auto-incremented per project)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Snapshot content
    snapshot: Mapped[dict] = mapped_column(
        JSON,
        default={
            "artifacts": [],      # List of artifact snapshots
            "context": {},        # Context state at this version
        },
        nullable=False
    )
    # Structure of snapshot:
    # {
    #     "artifacts": [
    #         {
    #             "id": "uuid",
    #             "name": "report.md",
    #             "version": 3,
    #             "content_hash": "sha256..."  # For comparison
    #         }
    #     ],
    #     "context": {
    #         "decisions": [...],
    #         "failures": [...],
    #         "key_findings": [...]
    #     }
    # }

    # Change description
    change_summary: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[VersionChangeType] = mapped_column(
        Enum(VersionChangeType, values_callable=lambda x: [e.value for e in x]),
        default=VersionChangeType.AUTO,
        nullable=False
    )

    # Who made the change
    changed_by: Mapped[str] = mapped_column(
        String(50), default="ai", nullable=False
    )  # "user" | "ai" | user_id

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="versions")

    def __repr__(self) -> str:
        return f"<ProjectVersion(project_id={self.project_id}, version={self.version_number})>"

    @property
    def is_auto_version(self) -> bool:
        """Check if this is an auto-generated version."""
        return self.change_type == VersionChangeType.AUTO

    @property
    def is_manual_version(self) -> bool:
        """Check if this is a user-created save point."""
        return self.change_type == VersionChangeType.MANUAL

    @property
    def artifact_count(self) -> int:
        """Get number of artifacts in this version."""
        return len(self.snapshot.get("artifacts", []))

    def get_artifact_ids(self) -> list[str]:
        """Get list of artifact IDs in this version."""
        return [a["id"] for a in self.snapshot.get("artifacts", [])]

    @classmethod
    def create_snapshot(
        cls,
        project_id: str,
        version_number: int,
        artifacts: list[dict],
        context: dict,
        change_summary: str,
        change_type: VersionChangeType = VersionChangeType.AUTO,
        changed_by: str = "ai"
    ) -> "ProjectVersion":
        """Factory method to create a version snapshot."""
        return cls(
            project_id=project_id,
            version_number=version_number,
            snapshot={
                "artifacts": artifacts,
                "context": context
            },
            change_summary=change_summary,
            change_type=change_type,
            changed_by=changed_by
        )
