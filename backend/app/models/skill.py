"""
Skill model - registry for available skills.
"""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Skill(Base):
    """
    Skill model - registry entry for an available skill.

    Skills are loaded from SKILL.md files in the skills/ directory.
    This table serves as a cache/registry for quick lookup.

    Features:
    - Three-level lazy loading metadata (L1/L2/L3)
    - Version tracking
    - Usage statistics
    - Enable/disable control
    """

    __tablename__ = "skills"

    # Primary key (skill identifier, e.g., "deep_research")
    id: Mapped[str] = mapped_column(String(100), primary_key=True)

    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0", nullable=False)

    # Skill file path
    skill_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # L1 Metadata (always loaded) - stored as JSON for quick access
    l1_metadata: Mapped[dict] = mapped_column(
        JSON,
        default={
            "triggers": [],      # Keywords/patterns that activate this skill
            "capabilities": [],  # What this skill can do
            "category": None,    # Category for grouping
        },
        nullable=False
    )

    # L2/L3 info
    l2_token_estimate: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    has_l3_resources: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Matching
    embedding_vector: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded vector for semantic matching

    # Statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    avg_tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Control
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.name}, version={self.version})>"

    @property
    def triggers(self) -> list[str]:
        """Get skill triggers."""
        return self.l1_metadata.get("triggers", [])

    @property
    def capabilities(self) -> list[str]:
        """Get skill capabilities."""
        return self.l1_metadata.get("capabilities", [])

    @property
    def category(self) -> str | None:
        """Get skill category."""
        return self.l1_metadata.get("category")

    def matches_query(self, query: str) -> bool:
        """Simple keyword matching for skill selection."""
        query_lower = query.lower()
        for trigger in self.triggers:
            if trigger.lower() in query_lower:
                return True
        return False

    def increment_usage(self, tokens_used: int = 0, success: bool = True) -> None:
        """Update usage statistics."""
        self.usage_count += 1

        # Update average tokens
        if tokens_used > 0:
            total_tokens = self.avg_tokens_used * (self.usage_count - 1) + tokens_used
            self.avg_tokens_used = total_tokens // self.usage_count

        # Update success rate
        if self.usage_count > 1:
            current_successes = self.success_rate * (self.usage_count - 1)
            if success:
                current_successes += 1
            self.success_rate = current_successes / self.usage_count

    def to_l1_format(self) -> dict:
        """Convert to L1 format for system prompt injection."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "triggers": self.triggers,
            "capabilities": self.capabilities
        }
