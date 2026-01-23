"""
Project model - represents a complete work unit in the Project-First architecture.

A Project is the top-level abstraction that contains:
- Artifacts: Persistent outputs (documents, PPTs, code, etc.)
- Conversations: Multi-turn interactions with AI
- Context: Bound context (intent, decisions, failures)
- Versions: Version snapshots for rollback support
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.datetime_utils import utc_now_naive

if TYPE_CHECKING:
    from app.models.artifact import Artifact
    from app.models.conversation import Conversation
    from app.models.project_version import ProjectVersion
    from app.models.workspace import Workspace


class ProjectType(PyEnum):
    """Project type enum.

    Defines the primary purpose of a project:
    - RESEARCH: Deep research tasks
    - DOCUMENT: Document writing
    - SLIDES: PPT generation
    - CODE: Code projects
    - DATA_ANALYSIS: Data analysis tasks
    - QUICK_TASK: Lightweight projects for quick questions
    """
    RESEARCH = "research"
    DOCUMENT = "document"
    SLIDES = "slides"
    CODE = "code"
    DATA_ANALYSIS = "data_analysis"
    QUICK_TASK = "quick_task"


class ProjectStatus(PyEnum):
    """Project status enum.

    Status transitions:
    - DRAFT: Just created, no work done yet
    - IN_PROGRESS: Active work in progress
    - COMPLETED: Work finished successfully
    - ARCHIVED: Soft-deleted or auto-archived
    """
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(Base):
    """
    Project model - the core work unit in Project-First architecture.

    Features:
    - Bound context that persists across all conversations
    - Artifacts management with version control
    - Multiple conversations per project
    - Auto-archiving for inactive quick tasks
    """

    __tablename__ = "projects"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Workspace relationship
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Type and status
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, values_callable=lambda x: [e.value for e in x]),
        default=ProjectType.QUICK_TASK,
        nullable=False
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, values_callable=lambda x: [e.value for e in x]),
        default=ProjectStatus.DRAFT,
        nullable=False
    )

    # Core: User's original intent
    intent: Mapped[str] = mapped_column(Text, nullable=False)

    # Core: Bound context (persists across all conversations)
    # NOTE: Using default_factory pattern to avoid mutable default bug
    context: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "decisions": [],      # Decision history
            "failures": [],       # Failure records (Keep the Failures)
            "key_findings": [],   # Key discoveries
            "tags": [],           # Tags for organization
        },
        nullable=False
    )

    # Settings
    settings: Mapped[dict] = mapped_column(
        JSON,
        default=lambda: {
            "llm_model": "claude-3-5-sonnet-20241022",
            "skill_id": None,
        },
        nullable=False
    )

    # Statistics
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    artifact_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, onupdate=utc_now_naive, nullable=False
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="projects")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Conversation.created_at"
    )
    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact",
        back_populates="project",
        cascade="all, delete-orphan",
        foreign_keys="Artifact.project_id"
    )
    versions: Mapped[list["ProjectVersion"]] = relationship(
        "ProjectVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectVersion.version_number"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title={self.title}, type={self.project_type.value})>"

    @property
    def is_quick_task(self) -> bool:
        """Check if this is a quick task (lightweight project)."""
        return self.project_type == ProjectType.QUICK_TASK

    @property
    def is_active(self) -> bool:
        """Check if project is active (not archived or completed)."""
        return self.status in [ProjectStatus.DRAFT, ProjectStatus.IN_PROGRESS]

    @property
    def is_archived(self) -> bool:
        """Check if project is archived."""
        return self.status == ProjectStatus.ARCHIVED

    def add_decision(self, decision: str, reason: str | None = None) -> None:
        """Add a decision to the context."""
        if "decisions" not in self.context:
            self.context["decisions"] = []
        self.context["decisions"].append({
            "decision": decision,
            "reason": reason,
            "timestamp": utc_now_naive().isoformat()
        })

    def add_failure(self, failure_type: str, message: str, learning: str | None = None) -> None:
        """Add a failure record to the context (Keep the Failures)."""
        if "failures" not in self.context:
            self.context["failures"] = []
        self.context["failures"].append({
            "type": failure_type,
            "message": message,
            "learning": learning,
            "timestamp": utc_now_naive().isoformat()
        })

    def add_finding(self, finding: str, source: str | None = None) -> None:
        """Add a key finding to the context."""
        if "key_findings" not in self.context:
            self.context["key_findings"] = []
        self.context["key_findings"].append({
            "finding": finding,
            "source": source,
            "timestamp": utc_now_naive().isoformat()
        })

    def get_failures_summary(self) -> str:
        """Get a summary of failures for Plan Recitation."""
        failures = self.context.get("failures", [])
        if not failures:
            return ""

        lines = ["## ⚠️ Historical Failures (Avoid Repeating)"]
        for f in failures[-5:]:  # Keep last 5
            learning = f.get("learning", f.get("message", "Unknown error"))
            lines.append(f"- {f.get('type', 'Error')}: {learning}")

        return "\n".join(lines)
