"""Models package - import all models to ensure proper ORM initialization."""
from app.models.agent_config import AgentConfig  # noqa: F401
from app.models.agent_lesson import AgentLesson  # noqa: F401
from app.models.agent_state import AgentState  # noqa: F401
from app.models.artifact import Artifact, ArtifactType  # noqa: F401

# Project-First architecture models
from app.models.conversation import (  # noqa: F401
    Conversation,
    ConversationPurpose,
    ConversationStatus,
)
from app.models.message import Message, MessageRole  # noqa: F401
from app.models.organization import Organization  # noqa: F401
from app.models.project import Project, ProjectStatus, ProjectType  # noqa: F401
from app.models.project_version import ProjectVersion, VersionChangeType  # noqa: F401
from app.models.research_task import ResearchTask, ResearchTaskStatus  # noqa: F401
from app.models.session import Session, SessionStatus  # noqa: F401
from app.models.turn import Turn, TurnStatus  # noqa: F401
from app.models.user_preference import (  # noqa: F401
    ExpertiseLevel,
    ReportStyle,
    ResearchDepth,
    UserResearchPreference,
)
from app.models.skill import Skill  # noqa: F401
from app.models.team import MemberRole, Team, TeamMember  # noqa: F401
from app.models.trust_config import TrustAuditLog, TrustConfig  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.workspace import Workspace  # noqa: F401

__all__ = [
    # User & Workspace
    "User",
    "Workspace",
    # Project-First architecture
    "Project",
    "ProjectType",
    "ProjectStatus",
    "Conversation",
    "ConversationStatus",
    "ConversationPurpose",
    "ProjectVersion",
    "VersionChangeType",
    # Session (legacy, kept for compatibility)
    "Session",
    "SessionStatus",
    # Turn (multi-turn conversation)
    "Turn",
    "TurnStatus",
    # Message
    "Message",
    "MessageRole",
    # Artifact
    "Artifact",
    "ArtifactType",
    # Skill
    "Skill",
    # Trust
    "TrustConfig",
    "TrustAuditLog",
    # Team & Organization
    "Team",
    "TeamMember",
    "MemberRole",
    "Organization",
    # Agent
    "AgentState",
    "AgentConfig",
    "AgentLesson",
    # Research
    "ResearchTask",
    "ResearchTaskStatus",
    # User Preference
    "UserResearchPreference",
    "ExpertiseLevel",
    "ResearchDepth",
    "ReportStyle",
]
