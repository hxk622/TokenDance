"""
Multi-Tenancy数据模型

三层模型: Organization -> Team -> Workspace
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class OrgStatus(str, Enum):
    """组织状态"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class MemberRole(str, Enum):
    """成员角色"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Organization(BaseModel):
    """组织模型"""
    id: str
    name: str
    slug: str

    settings: dict[str, Any] = Field(default_factory=dict)

    # 资源配额
    max_teams: int = 10
    max_workspaces: int = 100
    max_sessions: int = 1000
    storage_quota_gb: int = 100

    status: OrgStatus = OrgStatus.ACTIVE

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class User(BaseModel):
    """用户模型"""
    id: str
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None

    preferences: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True
    email_verified: bool = False

    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class OrganizationMember(BaseModel):
    """组织成员模型"""
    id: str
    org_id: str
    user_id: str
    role: MemberRole
    permissions: list[str] = Field(default_factory=list)
    joined_at: datetime

    # 关联对象（可选加载）
    organization: Organization | None = None
    user: User | None = None

    class Config:
        from_attributes = True


class Team(BaseModel):
    """团队模型"""
    id: str
    org_id: str
    name: str
    slug: str
    description: str | None = None

    settings: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True

    created_at: datetime
    updated_at: datetime

    # 关联对象（可选加载）
    organization: Organization | None = None

    class Config:
        from_attributes = True


class TeamMember(BaseModel):
    """团队成员模型"""
    id: str
    team_id: str
    user_id: str
    role: MemberRole
    joined_at: datetime

    # 关联对象（可选加载）
    team: Team | None = None
    user: User | None = None

    class Config:
        from_attributes = True


class Workspace(BaseModel):
    """工作空间模型"""
    id: str
    org_id: str
    team_id: str
    user_id: str  # 创建者

    name: str
    description: str | None = None

    settings: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True

    created_at: datetime
    updated_at: datetime

    # 关联对象（可选加载）
    organization: Organization | None = None
    team: Team | None = None
    user: User | None = None

    class Config:
        from_attributes = True


class SessionStatus(str, Enum):
    """会话状态"""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(BaseModel):
    """会话模型"""
    id: str
    workspace_id: str
    user_id: str

    title: str | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    skill_id: str | None = None
    context_summary: str | None = None

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    # 关联对象（可选加载）
    workspace: Workspace | None = None
    user: User | None = None

    class Config:
        from_attributes = True


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """消息模型"""
    id: str
    session_id: str
    role: MessageRole
    content: str | None = None
    thinking: str | None = None  # Agent推理过程
    tool_calls: list[dict[str, Any]] | None = None
    citations: list[dict[str, Any]] | None = None
    token_count: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactType(str, Enum):
    """产物类型"""
    DOCUMENT = "document"
    PPT = "ppt"
    CODE = "code"
    DATA = "data"


class Artifact(BaseModel):
    """产物模型"""
    id: str
    session_id: str
    type: ArtifactType
    name: str
    file_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    size_bytes: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# 创建/更新模型（用于API请求）
# ============================================

class OrganizationCreate(BaseModel):
    """创建组织"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    settings: dict[str, Any] = Field(default_factory=dict)


class TeamCreate(BaseModel):
    """创建团队"""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern="^[a-z0-9-]+$")
    description: str | None = None


class WorkspaceCreate(BaseModel):
    """创建工作空间"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    team_id: str


class SessionCreate(BaseModel):
    """创建会话"""
    workspace_id: str
    title: str | None = None
    skill_id: str | None = None
