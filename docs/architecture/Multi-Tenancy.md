# 多租户架构设计文档

> **核心理念**：Organization → Team → Workspace 三层隔离，支持企业级协作
> Version: 1.0.0
> Last Updated: 2026-01-09

## 1. 设计哲学

### 1.1 参考产品形态

**Genspark 的产品层级**：
```
Organization (组织)
  └── Team (团队)
        └── Workspace (工作区)
```

**TokenDance 的扩展设计**：
```
Organization (组织/企业)
  ├── Members (成员管理)
  ├── Billing (统一计费)
  └── Team (团队)
        ├── Members (团队成员)
        ├── Shared Resources (共享资源)
        └── Workspace (工作区)
              ├── Owner (所有者)
              ├── Agents (Agent 实例)
              ├── Tasks (任务)
              ├── Context (上下文)
              └── Files (文件系统)
```

### 1.2 核心设计原则

| 原则 | 说明 | 价值 |
|------|------|------|
| **严格隔离** | 不同 Org 的数据物理隔离 | 安全性、合规性 |
| **灵活共享** | Team 内资源可选择性共享 | 协作效率 |
| **细粒度权限** | RBAC 权限控制到 Workspace 级别 | 权限精细化 |
| **资源配额** | 按 Org/Team 分配资源配额 | 成本控制、公平性 |

---

## 2. 三层租户模型

### 2.1 Organization（组织）

**定义**：企业实体，计费和资源分配的最顶层单位

**数据结构**：

```python
# backend/app/models/organization.py

from sqlalchemy import Column, String, Integer, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

class OrgTier(enum.Enum):
    """组织等级"""
    FREE = "free"           # 免费版
    STARTER = "starter"     # 入门版
    PROFESSIONAL = "professional"  # 专业版
    ENTERPRISE = "enterprise"      # 企业版


class Organization(Base):
    """组织模型"""
    __tablename__ = "organizations"
    
    # 基本信息
    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # URL 友好名称
    
    # 计费信息
    tier = Column(Enum(OrgTier), default=OrgTier.FREE)
    billing_email = Column(String(255))
    
    # 资源配额
    quota = Column(JSON, default={
        "max_teams": 5,              # 最大团队数
        "max_workspaces": 50,        # 最大工作区数
        "max_agents": 100,           # 最大 Agent 数
        "max_storage_gb": 100,       # 最大存储空间（GB）
        "max_monthly_tokens": 10_000_000,  # 月度 Token 配额
        "max_concurrent_tasks": 50   # 最大并发任务数
    })
    
    # 使用统计
    usage_stats = Column(JSON, default={
        "current_teams": 0,
        "current_workspaces": 0,
        "current_agents": 0,
        "storage_used_gb": 0,
        "monthly_tokens_used": 0
    })
    
    # 时间戳
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")
    members = relationship("OrganizationMember", back_populates="organization")
    
    @property
    def is_over_quota(self) -> bool:
        """是否超过配额"""
        stats = self.usage_stats
        quota = self.quota
        
        return (
            stats["current_teams"] >= quota["max_teams"] or
            stats["current_workspaces"] >= quota["max_workspaces"] or
            stats["monthly_tokens_used"] >= quota["max_monthly_tokens"]
        )
```

**权限角色**：

```python
class OrgRole(enum.Enum):
    """组织角色"""
    OWNER = "owner"         # 所有者（创建者）
    ADMIN = "admin"         # 管理员
    MEMBER = "member"       # 普通成员
    BILLING = "billing"     # 计费管理员


class OrganizationMember(Base):
    """组织成员"""
    __tablename__ = "organization_members"
    
    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    role = Column(Enum(OrgRole), default=OrgRole.MEMBER)
    
    invited_by = Column(String(36), ForeignKey("users.id"))
    joined_at = Column(DateTime)
    
    # 关系
    organization = relationship("Organization", back_populates="members")
    user = relationship("User")
```

---

### 2.2 Team（团队）

**定义**：组织内的协作单元，共享资源和知识库

**数据结构**：

```python
# backend/app/models/team.py

class Team(Base):
    """团队模型"""
    __tablename__ = "teams"
    
    # 基本信息
    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)  # 在 org 内唯一
    description = Column(Text)
    
    # 团队配置
    settings = Column(JSON, default={
        "default_llm_model": "gpt-4",
        "allow_workspace_creation": True,
        "enable_shared_knowledge_base": True
    })
    
    # 共享资源路径
    shared_resources_path = Column(String(500))  # e.g., "orgs/org-123/teams/team-456/shared/"
    
    # 时间戳
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    workspaces = relationship("Workspace", back_populates="team", cascade="all, delete-orphan")
    
    # 唯一约束：org 内 slug 唯一
    __table_args__ = (
        UniqueConstraint('org_id', 'slug', name='uq_team_slug_per_org'),
    )
```

**权限角色**：

```python
class TeamRole(enum.Enum):
    """团队角色"""
    LEAD = "lead"           # 团队负责人
    MEMBER = "member"       # 团队成员
    GUEST = "guest"         # 访客（只读）


class TeamMember(Base):
    """团队成员"""
    __tablename__ = "team_members"
    
    id = Column(String(36), primary_key=True)
    team_id = Column(String(36), ForeignKey("teams.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    
    joined_at = Column(DateTime)
    
    # 关系
    team = relationship("Team", back_populates="members")
    user = relationship("User")
```

---

### 2.3 Workspace（工作区）

**定义**：个人或小组的独立工作空间，包含 Agent、任务、文件

**数据结构**：

```python
# backend/app/models/workspace.py

class WorkspaceVisibility(enum.Enum):
    """工作区可见性"""
    PRIVATE = "private"     # 私有（只有所有者）
    TEAM = "team"           # 团队可见
    ORG = "org"             # 组织可见


class Workspace(Base):
    """工作区模型"""
    __tablename__ = "workspaces"
    
    # 基本信息
    id = Column(String(36), primary_key=True)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)  # 在 team 内唯一
    description = Column(Text)
    
    # 可见性
    visibility = Column(Enum(WorkspaceVisibility), default=WorkspaceVisibility.PRIVATE)
    
    # 文件系统路径（物理隔离）
    filesystem_path = Column(String(500), nullable=False)
    # e.g., "orgs/org-123/teams/team-456/workspaces/ws-789/"
    
    # 配置
    settings = Column(JSON, default={
        "llm_model": "gpt-4",
        "enable_auto_save": True,
        "max_context_tokens": 128000
    })
    
    # 统计
    stats = Column(JSON, default={
        "total_tasks": 0,
        "completed_tasks": 0,
        "active_agents": 0,
        "storage_used_mb": 0
    })
    
    # 时间戳
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime)
    
    # 关系
    team = relationship("Team", back_populates="workspaces")
    owner = relationship("User")
    collaborators = relationship("WorkspaceCollaborator", back_populates="workspace")
    agents = relationship("Agent", back_populates="workspace")
    tasks = relationship("Task", back_populates="workspace")
    
    # 唯一约束：team 内 slug 唯一
    __table_args__ = (
        UniqueConstraint('team_id', 'slug', name='uq_workspace_slug_per_team'),
    )
```

**协作权限**：

```python
class WorkspaceRole(enum.Enum):
    """工作区角色"""
    OWNER = "owner"         # 所有者
    EDITOR = "editor"       # 编辑者
    VIEWER = "viewer"       # 查看者


class WorkspaceCollaborator(Base):
    """工作区协作者"""
    __tablename__ = "workspace_collaborators"
    
    id = Column(String(36), primary_key=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.VIEWER)
    
    invited_by = Column(String(36), ForeignKey("users.id"))
    invited_at = Column(DateTime)
    
    # 关系
    workspace = relationship("Workspace", back_populates="collaborators")
    user = relationship("User")
```

---

## 3. 数据隔离策略

### 3.1 物理隔离（FileSystem）

**目录结构**：

```bash
/data/
└── orgs/
    └── org-{org_id}/                    # Organization 级别隔离
        ├── .metadata                     # 组织元数据
        ├── billing/                      # 计费数据
        └── teams/
            └── team-{team_id}/          # Team 级别隔离
                ├── .metadata             # 团队元数据
                ├── shared/               # 团队共享资源
                │   ├── knowledge_base/
                │   ├── templates/
                │   └── tools/
                └── workspaces/
                    └── ws-{workspace_id}/  # Workspace 级别隔离
                        ├── tasks/
                        ├── context/
                        ├── cache/
                        ├── drafts/
                        ├── logs/
                        └── .tokendance/
```

**路径生成规则**：

```python
# backend/app/filesystem/paths.py

class PathManager:
    """路径管理器"""
    
    BASE_DIR = Path("/data/orgs")
    
    @classmethod
    def get_org_path(cls, org_id: str) -> Path:
        """获取组织路径"""
        return cls.BASE_DIR / f"org-{org_id}"
    
    @classmethod
    def get_team_path(cls, org_id: str, team_id: str) -> Path:
        """获取团队路径"""
        return cls.get_org_path(org_id) / "teams" / f"team-{team_id}"
    
    @classmethod
    def get_workspace_path(cls, org_id: str, team_id: str, workspace_id: str) -> Path:
        """获取工作区路径"""
        return cls.get_team_path(org_id, team_id) / "workspaces" / f"ws-{workspace_id}"
    
    @classmethod
    def get_shared_resources_path(cls, org_id: str, team_id: str) -> Path:
        """获取团队共享资源路径"""
        return cls.get_team_path(org_id, team_id) / "shared"
```

### 3.2 逻辑隔离（Database）

**Row-Level Security（PostgreSQL）**：

```sql
-- 启用 RLS
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

-- 策略：用户只能访问自己所属组织的数据
CREATE POLICY workspace_org_isolation ON workspaces
    USING (
        team_id IN (
            SELECT t.id FROM teams t
            JOIN organization_members om ON t.org_id = om.org_id
            WHERE om.user_id = current_user_id()
        )
    );

-- 策略：用户只能访问可见的 Workspace
CREATE POLICY workspace_visibility ON workspaces
    USING (
        visibility = 'org' OR
        (visibility = 'team' AND team_id IN (
            SELECT team_id FROM team_members WHERE user_id = current_user_id()
        )) OR
        (visibility = 'private' AND owner_id = current_user_id()) OR
        id IN (
            SELECT workspace_id FROM workspace_collaborators WHERE user_id = current_user_id()
        )
    );
```

### 3.3 KV-Cache 隔离

**Redis 命名空间**：

```python
# backend/app/kv_cache/redis_keys.py

class RedisKeyManager:
    """Redis Key 管理器"""
    
    @staticmethod
    def kv_cache_key(org_id: str, workspace_id: str, session_id: str) -> str:
        """生成 KV-Cache Key"""
        return f"kv_cache:org:{org_id}:ws:{workspace_id}:session:{session_id}"
    
    @staticmethod
    def global_prefix_key(org_id: str) -> str:
        """生成 Global Prefix Key（Org 级别共享）"""
        return f"global_prefix:org:{org_id}"
    
    @staticmethod
    def skill_cache_key(org_id: str, team_id: str, skill_name: str) -> str:
        """生成 Skill Cache Key（Team 级别共享）"""
        return f"skill_cache:org:{org_id}:team:{team_id}:skill:{skill_name}"
```

---

## 4. 权限控制（RBAC）

### 4.1 权限矩阵

| 资源 | Owner | Admin | Member | Billing | Guest |
|------|-------|-------|--------|---------|-------|
| **Organization** |
| 查看组织信息 | ✅ | ✅ | ✅ | ✅ | ✅ |
| 修改组织信息 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 删除组织 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 邀请成员 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 管理计费 | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Team** |
| 创建团队 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 修改团队 | ✅ (owner) | ✅ | Team Lead | ❌ | ❌ |
| 删除团队 | ✅ (owner) | ✅ | Team Lead | ❌ | ❌ |
| 添加成员 | ✅ | ✅ | Team Lead | ❌ | ❌ |
| **Workspace** |
| 创建工作区 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 修改工作区 | Owner/Editor | Owner/Editor | Owner/Editor | ❌ | ❌ |
| 删除工作区 | Owner | Owner | Owner | ❌ | ❌ |
| 查看工作区 | ✅ | ✅ | 按可见性 | ❌ | Viewer |
| 执行任务 | Owner/Editor | Owner/Editor | Owner/Editor | ❌ | ❌ |

### 4.2 权限检查器

```python
# backend/app/auth/permissions.py

from enum import Enum

class Action(Enum):
    """操作类型"""
    VIEW = "view"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"


class PermissionChecker:
    """权限检查器"""
    
    async def check_org_permission(
        self,
        user_id: str,
        org_id: str,
        action: Action
    ) -> bool:
        """检查组织权限"""
        member = await OrganizationMember.query.filter_by(
            user_id=user_id,
            org_id=org_id
        ).first()
        
        if not member:
            return False
        
        if action == Action.VIEW:
            return True
        elif action in [Action.CREATE, Action.UPDATE]:
            return member.role in [OrgRole.OWNER, OrgRole.ADMIN]
        elif action == Action.DELETE:
            return member.role == OrgRole.OWNER
        
        return False
    
    async def check_workspace_permission(
        self,
        user_id: str,
        workspace_id: str,
        action: Action
    ) -> bool:
        """检查工作区权限"""
        workspace = await Workspace.query.get(workspace_id)
        if not workspace:
            return False
        
        # 1. 检查所有者
        if workspace.owner_id == user_id:
            return True
        
        # 2. 检查协作者
        collaborator = await WorkspaceCollaborator.query.filter_by(
            workspace_id=workspace_id,
            user_id=user_id
        ).first()
        
        if collaborator:
            if action == Action.VIEW:
                return True
            elif action in [Action.UPDATE, Action.EXECUTE]:
                return collaborator.role in [WorkspaceRole.OWNER, WorkspaceRole.EDITOR]
            elif action == Action.DELETE:
                return collaborator.role == WorkspaceRole.OWNER
        
        # 3. 检查可见性
        if action == Action.VIEW:
            if workspace.visibility == WorkspaceVisibility.ORG:
                return await self._is_org_member(user_id, workspace.team.org_id)
            elif workspace.visibility == WorkspaceVisibility.TEAM:
                return await self._is_team_member(user_id, workspace.team_id)
        
        return False
```

---

## 5. 资源配额管理

### 5.1 配额检查器

```python
# backend/app/billing/quota.py

class QuotaChecker:
    """配额检查器"""
    
    async def check_can_create_workspace(self, org_id: str) -> bool:
        """检查是否可以创建工作区"""
        org = await Organization.query.get(org_id)
        
        if org.usage_stats["current_workspaces"] >= org.quota["max_workspaces"]:
            raise QuotaExceededError(
                f"Workspace quota exceeded: {org.quota['max_workspaces']}"
            )
        
        return True
    
    async def check_can_create_agent(self, org_id: str) -> bool:
        """检查是否可以创建 Agent"""
        org = await Organization.query.get(org_id)
        
        if org.usage_stats["current_agents"] >= org.quota["max_agents"]:
            raise QuotaExceededError(
                f"Agent quota exceeded: {org.quota['max_agents']}"
            )
        
        return True
    
    async def check_token_quota(self, org_id: str, tokens: int) -> bool:
        """检查 Token 配额"""
        org = await Organization.query.get(org_id)
        
        if (org.usage_stats["monthly_tokens_used"] + tokens) > org.quota["max_monthly_tokens"]:
            raise QuotaExceededError(
                f"Monthly token quota exceeded: {org.quota['max_monthly_tokens']}"
            )
        
        return True
```

### 5.2 使用量追踪

```python
# backend/app/billing/usage_tracker.py

class UsageTracker:
    """使用量追踪器"""
    
    async def track_token_usage(
        self,
        org_id: str,
        workspace_id: str,
        tokens: int,
        model: str
    ):
        """追踪 Token 使用量"""
        
        # 1. 更新组织统计
        org = await Organization.query.get(org_id)
        org.usage_stats["monthly_tokens_used"] += tokens
        await org.save()
        
        # 2. 记录详细日志（用于计费）
        usage_log = UsageLog(
            org_id=org_id,
            workspace_id=workspace_id,
            resource_type="tokens",
            amount=tokens,
            model=model,
            timestamp=datetime.now()
        )
        await usage_log.save()
    
    async def track_storage_usage(
        self,
        org_id: str,
        workspace_id: str,
        size_bytes: int
    ):
        """追踪存储使用量"""
        org = await Organization.query.get(org_id)
        org.usage_stats["storage_used_gb"] += size_bytes / (1024 ** 3)
        await org.save()
```

---

## 6. 共享机制

### 6.1 团队共享资源

**共享类型**：

```python
class SharedResourceType(enum.Enum):
    """共享资源类型"""
    KNOWLEDGE_BASE = "knowledge_base"   # 知识库
    TEMPLATE = "template"               # 模板
    TOOL = "tool"                       # 工具
    SKILL = "skill"                     # 技能


class SharedResource(Base):
    """共享资源"""
    __tablename__ = "shared_resources"
    
    id = Column(String(36), primary_key=True)
    team_id = Column(String(36), ForeignKey("teams.id"))
    type = Column(Enum(SharedResourceType))
    name = Column(String(255))
    
    # 文件系统路径
    path = Column(String(500))
    # e.g., "orgs/org-123/teams/team-456/shared/knowledge_base/product_docs.md"
    
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime)
    
    # 访问统计
    access_count = Column(Integer, default=0)
```

### 6.2 工作区共享

**共享策略**：

```python
# backend/app/workspace/sharing.py

class WorkspaceSharing:
    """工作区共享管理器"""
    
    async def share_with_user(
        self,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole,
        invited_by: str
    ):
        """与用户共享工作区"""
        
        # 1. 验证权限
        if not await self.permission_checker.check_workspace_permission(
            invited_by,
            workspace_id,
            Action.UPDATE
        ):
            raise PermissionDeniedError()
        
        # 2. 创建协作者
        collaborator = WorkspaceCollaborator(
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            invited_by=invited_by,
            invited_at=datetime.now()
        )
        await collaborator.save()
        
        # 3. 发送通知
        await self.notification_service.send_workspace_invitation(
            user_id,
            workspace_id
        )
    
    async def change_visibility(
        self,
        workspace_id: str,
        new_visibility: WorkspaceVisibility,
        user_id: str
    ):
        """修改工作区可见性"""
        workspace = await Workspace.query.get(workspace_id)
        
        # 只有所有者可以修改可见性
        if workspace.owner_id != user_id:
            raise PermissionDeniedError()
        
        workspace.visibility = new_visibility
        await workspace.save()
```

---

## 7. API 设计

### 7.1 RESTful API 路径

```
# Organization APIs
GET    /api/v1/organizations                  # 列出用户所属的组织
POST   /api/v1/organizations                  # 创建组织
GET    /api/v1/organizations/:org_id          # 获取组织详情
PATCH  /api/v1/organizations/:org_id          # 更新组织
DELETE /api/v1/organizations/:org_id          # 删除组织

# Team APIs
GET    /api/v1/organizations/:org_id/teams    # 列出组织的团队
POST   /api/v1/organizations/:org_id/teams    # 创建团队
GET    /api/v1/teams/:team_id                 # 获取团队详情
PATCH  /api/v1/teams/:team_id                 # 更新团队
DELETE /api/v1/teams/:team_id                 # 删除团队

# Workspace APIs
GET    /api/v1/teams/:team_id/workspaces      # 列出团队的工作区
POST   /api/v1/teams/:team_id/workspaces      # 创建工作区
GET    /api/v1/workspaces/:workspace_id       # 获取工作区详情
PATCH  /api/v1/workspaces/:workspace_id       # 更新工作区
DELETE /api/v1/workspaces/:workspace_id       # 删除工作区

# Sharing APIs
POST   /api/v1/workspaces/:workspace_id/collaborators     # 添加协作者
DELETE /api/v1/workspaces/:workspace_id/collaborators/:user_id  # 移除协作者
PATCH  /api/v1/workspaces/:workspace_id/visibility       # 修改可见性
```

### 7.2 权限中间件

```python
# backend/app/middleware/auth.py

from functools import wraps

def require_org_permission(action: Action):
    """要求组织权限"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            org_id = kwargs.get('org_id')
            user_id = get_current_user_id()
            
            if not await permission_checker.check_org_permission(
                user_id,
                org_id,
                action
            ):
                raise PermissionDeniedError()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_workspace_permission(action: Action):
    """要求工作区权限"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            workspace_id = kwargs.get('workspace_id')
            user_id = get_current_user_id()
            
            if not await permission_checker.check_workspace_permission(
                user_id,
                workspace_id,
                action
            ):
                raise PermissionDeniedError()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## 8. 计费与使用量

### 8.1 计费模型

```python
# backend/app/billing/pricing.py

class PricingTier:
    """定价层级"""
    
    FREE = {
        "name": "Free",
        "price_monthly": 0,
        "max_teams": 1,
        "max_workspaces": 5,
        "max_agents": 10,
        "max_storage_gb": 10,
        "max_monthly_tokens": 1_000_000
    }
    
    STARTER = {
        "name": "Starter",
        "price_monthly": 29,
        "max_teams": 3,
        "max_workspaces": 20,
        "max_agents": 50,
        "max_storage_gb": 50,
        "max_monthly_tokens": 5_000_000
    }
    
    PROFESSIONAL = {
        "name": "Professional",
        "price_monthly": 99,
        "max_teams": 10,
        "max_workspaces": 100,
        "max_agents": 200,
        "max_storage_gb": 200,
        "max_monthly_tokens": 20_000_000
    }
    
    ENTERPRISE = {
        "name": "Enterprise",
        "price_monthly": None,  # 自定义定价
        "max_teams": None,      # 无限制
        "max_workspaces": None,
        "max_agents": None,
        "max_storage_gb": None,
        "max_monthly_tokens": None
    }
```

### 8.2 用量报表

```python
# backend/app/billing/reports.py

class UsageReport:
    """用量报表生成器"""
    
    async def generate_monthly_report(self, org_id: str, month: str) -> dict:
        """生成月度用量报表"""
        
        # 1. 汇总 Token 使用量
        token_usage = await self._aggregate_token_usage(org_id, month)
        
        # 2. 汇总存储使用量
        storage_usage = await self._aggregate_storage_usage(org_id, month)
        
        # 3. 汇总任务执行量
        task_count = await self._aggregate_task_count(org_id, month)
        
        return {
            "org_id": org_id,
            "month": month,
            "token_usage": token_usage,
            "storage_usage_gb": storage_usage,
            "task_count": task_count,
            "estimated_cost": self._calculate_cost(token_usage, storage_usage)
        }
```

---

## 9. 实施路线图

### Phase 1: 基础架构（Week 1-2）
- [ ] 实现 Organization/Team/Workspace 数据模型
- [ ] 实现路径隔离（FileSystem）
- [ ] 实现 RLS（Row-Level Security）

### Phase 2: 权限系统（Week 3-4）
- [ ] 实现 RBAC 权限检查
- [ ] 实现权限中间件
- [ ] 实现 API 路由

### Phase 3: 资源配额（Week 5-6）
- [ ] 实现配额检查器
- [ ] 实现使用量追踪
- [ ] 实现配额告警

### Phase 4: 共享与协作（Week 7-8）
- [ ] 实现团队共享资源
- [ ] 实现工作区协作
- [ ] 实现可见性控制

### Phase 5: 计费系统（Week 9-10）
- [ ] 实现计费模型
- [ ] 实现用量报表
- [ ] 集成支付网关（Stripe）

---

## 10. 总结

### 10.1 核心价值

✅ **企业级安全**：多层隔离，细粒度权限控制
✅ **灵活协作**：Team 共享 + Workspace 协作
✅ **成本可控**：资源配额 + 用量追踪
✅ **易于扩展**：三层架构，清晰的边界

### 10.2 关键设计

1. **三层隔离**：Organization → Team → Workspace
2. **物理隔离**：FileSystem 按 Org/Team/Workspace 分层
3. **逻辑隔离**：RLS + Redis 命名空间
4. **细粒度权限**：RBAC 权限矩阵
5. **资源配额**：按 Org 分配，实时追踪

---

**下一步**：更新 FileSystem.md、Context-Management.md、HLD.md 以适配多租户架构！🚀
