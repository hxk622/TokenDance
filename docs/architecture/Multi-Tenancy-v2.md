# 多租户架构设计文档（v2.0）

> **⚠️ 文档将合并**: 此文件将于 **2026-03-01** 成为主版本 [`docs/architecture/multi-tenancy.md`](multi-tenancy.md)，v1 版本将归档
>
> 这是最新版本，推荐使用。

> **核心理念**：Personal+Workspace（个人）vs Teams+Workspace（团队协作）
> **超越 Manus**：Workspace = KV-Cache 物理隔离环境 + 长期资产沉淀
> **UI 哲学**：从 "被动观察" 到 "主动指挥" - 可控的透明度
> Version: 2.0.1
> Last Updated: 2026-01-12

**相关文档**：
- [UI Design Principles](./UI-Design-Principles.md) - 详细的交互设计原则
- [Development Plan v2.0](../../GETTING_STARTED.md) - 开发路线图

---

## 0. 第一性原理：为什么需要 Workspace 和 Teams？

### 0.1 如果 AI 足够完美，为什么还需要 Workspace？

从第一性原理来看，如果 AI 足够完美，确实只需要一个对话框。但现实中存在四个核心问题：

#### 问题 1：消除"上下文污染"与"注意力发散"

- **物理极限**：LLM 的 Context Window 纯净度直接影响推理质量
- **场景冲突**：如果"写代码"、"订机票"、"写周报"混在同一个 Agent，Context 会极其混乱
- **解决方案**：**Workspace = 物理隔离的 KV-Cache 环境**
  - 在"财务分析 Workspace"里，静态前缀全是金融公式和 Excel 插件
  - 在"代码开发 Workspace"里，静态前缀全是编译器和 GitHub API
  - Logits Masking 自动收窄到该领域，反应更精准、速度更快

#### 问题 2：从"单次任务"到"长期资产"的沉淀

- **Manus 的局限**：每次对话都是"临时工"，没有长期记忆
- **TokenDance 的差异化**：**Workspace = 持久化的 Agent 实例 + 长期记忆**
  - 场景：你有一个"每日竞品监控"任务
  - 需要长期记忆：关注的竞品列表、历史报告格式、特定的筛选偏好
  - Workspace 里的 Agent 不是新模型，而是**挂载了特定知识库和历史状态的持久化实例**
  - **结论**：让 Agent 从"临时工"变成"长期员工"

#### 问题 3："黑盒调度"的信任与调试难题

- **幻觉依然存在**：即便后台自动调度，AI 仍会出错
- **调试困境**：如果后台自动调度了 10 个 Agent，其中一个出错，你根本不知道是谁、在哪一步出错
- **解决方案**：**Workspace = 白盒化的执行空间**
  - 用户可以看到不同 Agent（子任务模块）在看板上同步推进
  - **超越点**：用户可以在 Workspace 看板上直接点击某个 Agent 的状态，调整它的 Logits 约束或补充信息，而不需要重启整个任务

#### 问题 4：权限与资源隔离（TokenDance 的核心逻辑）

- **资源管理绕不开**：不同 Agent 消耗的算力（Token）和调用的 API 成本不同
- **场景**：
  - Workspace A：使用廉价的小模型（如 Llama-3-8B）处理日常琐事，节省 Token
  - Workspace B：使用昂贵的专家模型（如 GPT-4o 或 Claude 3.5）处理核心代码
- **结论**：用户创建不同 Workspace 实例，其实是在进行**"算力预算管理"**

---

### 0.2 为什么需要 Teams？

#### Figma Teams vs Genspark Workspace vs TokenDance Teams

- **Figma Teams**：一群人围着一个"设计稿"协作
- **Genspark Workspace**：一个人指挥一群"AI Agent"干活
- **TokenDance Teams**：**多人共享多个 Agent 的"思维状态"并协同治理**

#### Teams 的核心价值：从"共享文件"转向"共享状态 (State)"

**1. KV-Cache 的资产化**

- 如果团队专家通过一系列复杂 Prompt 和交互，把一个 Agent 的 KV-Cache "喂"到了一个非常专业的金融分析状态
- 他可以将这个**"预热好的 KV-Cache 快照"直接同步给团队成员**
- 团队成员不需要重新训练或重新输入背景资料，直接"挂载"专家的思维状态即可开始工作
- **这是一种前所未有的知识传递方式**

**2. 权限分级：基于 Masking 的"能力脱敏"**

- 利用 Logits Masking，在团队中不同成员对同一个 Agent 的操作权限是不同的
- 实习生：调用财务 Agent 时，send_payment（发起支付）的 Token 被物理掩码，他只能看数据
- 财务主管：掩码解锁，他可以调用完整的金流指令
- **传统权限管理是粗粒度的（能不能进这个群），TokenDance Teams 权限是原子级的（能不能输出某个指令）**

**3. 多人协作的"人机链路（Human-in-the-Loop）"**

- 场景：Agent A 写代码，Agent B 测压力
- 团队功能允许"开发者 A"监督代码 Agent，同时"测试员 B"监督压力测试 Agent
- 他们在同一个 Teams 视图下，能够看到全链路的 Agent 状态流转

**4. 资源治理：Token 的统一分配与审计**

- 企业需要 Teams 维度来分配"算力额度"
- 比如：研发部这月有 10 亿 Token 预算，市场部有 2 亿
- 系统可以通过状态机自动监控：当某个团队 Token 消耗过快，自动在 Logits 层对该团队所有 Agent 施加"低成本模型掩码"，强制切换到更便宜的模型（如从 GPT-4 降级到 Llama-8B）

---

### 0.3 总结：TokenDance 的差异化定位

| 对比维度 | Manus | Genspark | Figma | TokenDance |
|---------|-------|----------|-------|------------|
| **核心单位** | 对话 | Workspace（单人+多Agent） | Team（多人协作） | **Personal+Workspace（个人）<br>Teams+Workspace（团队协作）** |
| **协作方式** | 不支持 | 单人操作 | 多人协作设计 | **多人共享 Agent 状态** |
| **资源管理** | 不可见 | 不可见 | 不涉及 | **算力预算管理（Token分配）** |
| **知识传递** | 无 | 无 | 文件共享 | **KV-Cache 快照共享** |
| **权限粒度** | 无 | 无 | 文件/图层权限 | **Logits Masking 原子级权限** |

**核心观点**：

- **Workspace 不是为了让用户看到"工具"，而是为了让用户看到"进度、资产和逻辑隔离"**
- **Teams 不是"聊天室"，而是"共享的智能池"：专家 Agent 技能共享（智力沉淀） + 基于 Token 预算的权限管控（行政治理）**

---

## 1. 两种模式并存

### 1.1 模式 1：Personal + Workspace（个人模式）

**类似 Manus，但更强大**

```
User (个人用户)
  └── Personal Workspaces
        ├── Workspace 1: "财务分析"
        │     ├── KV-Cache 状态（金融领域预热）
        │     ├── Logits Masking（金融工具集）
        │     ├── Agent 实例（长期记忆）
        │     └── 文件系统
        │           ├── context/     (长期上下文)
        │           ├── cache/       (7天临时缓存)
        │           └── artifacts/   (产出物)
        │
        └── Workspace 2: "代码开发"
              ├── KV-Cache 状态（编程领域预热）
              ├── Logits Masking（编程工具集）
              ├── Agent 实例（挂载特定 Skill）
              └── 文件系统
```

**特点**：

- ✅ 无需创建 Organization/Team
- ✅ 用户直接创建多个 Workspace
- ✅ 每个 Workspace 物理隔离（独立 KV-Cache）
- ✅ Workspace 之间不共享状态（防止污染）
- ✅ 适合个人开发者、自由职业者

---

### 1.2 模式 2：Teams + Workspace（团队协作模式）

**超越 Figma + Genspark**

```
Organization (企业)
  ├── Billing (统一计费)
  │
  ├── Team 1: "研发部"
  │     ├── Members (团队成员)
  │     │     ├── 张三 (Lead, 完整权限)
  │     │     ├── 李四 (Member, 标准权限)
  │     │     └── 王五 (Intern, Logits Masking 掩码敏感操作)
  │     │
  │     ├── Shared Agent States (共享的 KV-Cache 快照)
  │     │     ├── "金融分析专家 Agent" (张三贡献)
  │     │     └── "代码审查 Agent" (李四贡献)
  │     │
  │     ├── Token Budget: 10亿/月
  │     ├── Logits Masking Policy (团队级权限策略)
  │     │     ├── send_payment: 仅 Lead 可用
  │     │     └── execute_shell: Member 以上可用
  │     │
  │     └── Workspaces
  │           ├── Workspace A: "后端开发"
  │           │     ├── Owner: 张三
  │           │     ├── Collaborators: 李四(Editor), 王五(Viewer)
  │           │     ├── 多人实时看到 Agent 推理过程
  │           │     ├── 支持"人机链路"干预
  │           │     └── 挂载 Team 共享的 Agent 状态
  │           │
  │           └── Workspace B: "前端开发"
  │                 └── ...
  │
  └── Team 2: "市场部"
        ├── Token Budget: 2亿/月
        └── ...
```

**特点**：

- ✅ 多人共享 Agent 状态（KV-Cache 快照）
- ✅ 原子级权限控制（Logits Masking）
- ✅ Token 预算按 Team 分配
- ✅ 实时协作（多人看到同一个 Agent 推理）
- ✅ 知识沉淀（专家 Agent 技能包可发布到 Team）

---

## 2. 数据模型设计

### 2.1 User（用户）

```python
# backend/app/models/user.py

class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)  # UUID
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 用户类型
    user_type = Column(Enum("personal", "organization"), default="personal")
    
    # Personal 模式的默认配额
    personal_quota = Column(JSON, default={
        "max_workspaces": 10,
        "max_monthly_tokens": 1_000_000,
        "max_storage_gb": 10
    })
    
    # 时间戳
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    personal_workspaces = relationship(
        "Workspace",
        foreign_keys="Workspace.owner_id",
        primaryjoin="and_(Workspace.owner_id==User.id, Workspace.team_id==None)"
    )
    organization_memberships = relationship("OrganizationMember")
    team_memberships = relationship("TeamMember")
```

---

### 2.2 Workspace（工作区）- 两种模式共用

**核心设计**：Workspace 既可以是 Personal（team_id=None），也可以属于 Team

```python
# backend/app/models/workspace.py

class WorkspaceType(enum.Enum):
    """工作区类型"""
    PERSONAL = "personal"    # Personal 模式
    TEAM = "team"            # Team 模式

class WorkspaceVisibility(enum.Enum):
    """工作区可见性（仅 Team 模式有效）"""
    PRIVATE = "private"      # 私有（只有所有者）
    TEAM = "team"            # 团队可见
    ORG = "org"              # 组织可见

class Workspace(Base):
    """工作区模型（统一）"""
    __tablename__ = "workspaces"
    
    # 基本信息
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 归属（两种模式）
    workspace_type = Column(Enum(WorkspaceType), nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=True)  # Personal 模式时为 NULL
    
    # 可见性（仅 Team 模式有效）
    visibility = Column(Enum(WorkspaceVisibility), default=WorkspaceVisibility.PRIVATE)
    
    # KV-Cache 状态（核心）
    kv_cache_snapshot_id = Column(String(36), nullable=True)  # 指向 Redis 中保存的 KV-Cache 快照
    
    # Logits Masking 规则
    logits_masking_rules = Column(JSON, default={
        "enabled_tools": ["browser", "file", "python"],
        "disabled_actions": [],
        "model_preference": "gpt-4"
    })
    
    # 文件系统路径（物理隔离）
    # Personal: /data/users/user-{id}/workspaces/ws-{id}/
    # Team:     /data/orgs/org-{id}/teams/team-{id}/workspaces/ws-{id}/
    filesystem_path = Column(String(500), nullable=False)
    
    # 配置
    settings = Column(JSON, default={
        "llm_model": "gpt-4",
        "enable_auto_save": True,
        "max_context_tokens": 128000,
        "compression_threshold": 10240  # 10KB
    })
    
    # 统计
    stats = Column(JSON, default={
        "total_tasks": 0,
        "completed_tasks": 0,
        "active_agents": 0,
        "storage_used_mb": 0,
        "monthly_tokens_used": 0
    })
    
    # 时间戳
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    last_accessed_at = Column(DateTime)
    
    # 关系
    owner = relationship("User")
    team = relationship("Team", back_populates="workspaces")
    collaborators = relationship("WorkspaceCollaborator")
    agents = relationship("Agent")
    tasks = relationship("Task")
    
    # 唯一约束
    __table_args__ = (
        # Personal 模式：user 内 slug 唯一
        Index('idx_personal_workspace_slug', 'owner_id', 'slug', 
              unique=True, 
              postgresql_where=text("team_id IS NULL")),
        # Team 模式：team 内 slug 唯一
        Index('idx_team_workspace_slug', 'team_id', 'slug', 
              unique=True, 
              postgresql_where=text("team_id IS NOT NULL")),
    )
    
    @property
    def is_personal(self) -> bool:
        """是否为 Personal 模式"""
        return self.workspace_type == WorkspaceType.PERSONAL
```

---

### 2.3 Organization（组织）- 仅 Team 模式

```python
# backend/app/models/organization.py

class OrgTier(enum.Enum):
    """组织等级"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class Organization(Base):
    """组织模型（企业）"""
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    
    # 计费信息
    tier = Column(Enum(OrgTier), default=OrgTier.FREE)
    billing_email = Column(String(255))
    
    # 资源配额
    quota = Column(JSON, default={
        "max_teams": 5,
        "max_workspaces": 50,
        "max_agents": 100,
        "max_storage_gb": 100,
        "max_monthly_tokens": 10_000_000
    })
    
    # 使用统计
    usage_stats = Column(JSON, default={
        "current_teams": 0,
        "current_workspaces": 0,
        "monthly_tokens_used": 0
    })
    
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    teams = relationship("Team", back_populates="organization")
    members = relationship("OrganizationMember")
```

---

### 2.4 Team（团队）- 仅 Team 模式

**核心设计**：Team 是"共享的智能池"

```python
# backend/app/models/team.py

class Team(Base):
    """团队模型"""
    __tablename__ = "teams"
    
    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Token 预算（核心）
    token_budget = Column(JSON, default={
        "monthly_limit": 10_000_000_000,  # 100亿 Token
        "current_usage": 0,
        "warning_threshold": 0.9,  # 90% 告警
        "auto_downgrade": True  # 超额自动降级模型
    })
    
    # Logits Masking 策略（团队级）
    team_masking_policy = Column(JSON, default={
        "restricted_actions": {
            "send_payment": ["lead"],       # 仅 Lead 可用
            "delete_data": ["lead"],
            "execute_shell": ["lead", "member"]  # Member 以上可用
        }
    })
    
    # 共享 Agent 状态池
    # 存储在 Redis: shared_agents:team:{team_id}:agent:{agent_id}
    shared_agent_registry = Column(JSON, default=[])
    # 示例: [
    #   {"agent_id": "...", "name": "金融分析专家", "contributor_id": "user-123", "kv_cache_snapshot_id": "..."},
    #   {"agent_id": "...", "name": "代码审查 Agent", "contributor_id": "user-456", "kv_cache_snapshot_id": "..."}
    # ]
    
    # 共享资源路径
    shared_resources_path = Column(String(500))
    # e.g., "orgs/org-123/teams/team-456/shared/"
    
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 关系
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember")
    workspaces = relationship("Workspace", back_populates="team")
    
    __table_args__ = (
        UniqueConstraint('org_id', 'slug', name='uq_team_slug_per_org'),
    )
```

---

### 2.5 权限角色

```python
# backend/app/models/permissions.py

# Organization 角色
class OrgRole(enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    BILLING = "billing"

# Team 角色（核心权限）
class TeamRole(enum.Enum):
    LEAD = "lead"       # 团队负责人（完整 Logits 权限）
    MEMBER = "member"   # 团队成员（标准权限）
    INTERN = "intern"   # 实习生（受限权限，敏感操作被 Masking）
    GUEST = "guest"     # 访客（只读）

# Workspace 协作角色
class WorkspaceRole(enum.Enum):
    OWNER = "owner"     # 所有者（完整控制）
    EDITOR = "editor"   # 编辑者（可修改 Agent 状态）
    VIEWER = "viewer"   # 查看者（只读，可查看 Agent 推理过程）
```

---

## 3. 核心功能实现

### 3.1 KV-Cache 快照共享（Teams 独有）

**场景**：专家张三调试出一个"金融分析专家 Agent"，希望分享给团队

```python
# backend/app/services/agent_sharing.py

class AgentSharingService:
    """Agent 状态共享服务"""
    
    async def publish_agent_to_team(
        self,
        workspace_id: str,
        agent_id: str,
        team_id: str,
        user_id: str
    ) -> dict:
        """发布 Agent 到 Team 共享池"""
        
        # 1. 检查权限（至少是 Member）
        if not await self._check_team_permission(user_id, team_id, "member"):
            raise PermissionDeniedError()
        
        # 2. 获取 Agent 的 KV-Cache 快照
        kv_cache_snapshot = await self._export_kv_cache_snapshot(workspace_id, agent_id)
        
        # 3. 保存到 Redis（Team 共享池）
        snapshot_id = str(uuid.uuid4())
        redis_key = f"shared_agents:team:{team_id}:snapshot:{snapshot_id}"
        await redis_client.set(redis_key, msgpack.packb(kv_cache_snapshot))
        
        # 4. 注册到 Team 的 shared_agent_registry
        team = await db.get(Team, team_id)
        team.shared_agent_registry.append({
            "agent_id": snapshot_id,
            "name": f"{agent.name} (by {user.username})",
            "contributor_id": user_id,
            "kv_cache_snapshot_id": snapshot_id,
            "created_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        
        return {"snapshot_id": snapshot_id, "status": "published"}
    
    async def load_shared_agent(
        self,
        workspace_id: str,
        snapshot_id: str,
        user_id: str
    ) -> dict:
        """加载 Team 共享的 Agent 状态到自己的 Workspace"""
        
        # 1. 获取 Team ID
        workspace = await db.get(Workspace, workspace_id)
        if not workspace.team_id:
            raise ValueError("Personal workspace cannot load team agents")
        
        # 2. 从 Redis 加载 KV-Cache 快照
        redis_key = f"shared_agents:team:{workspace.team_id}:snapshot:{snapshot_id}"
        snapshot_bytes = await redis_client.get(redis_key)
        kv_cache_snapshot = msgpack.unpackb(snapshot_bytes)
        
        # 3. 注入到当前 Workspace 的 KV-Cache
        await self._inject_kv_cache(workspace_id, kv_cache_snapshot)
        
        return {"status": "loaded", "snapshot_id": snapshot_id}
```

---

### 3.2 Logits Masking 权限控制（Teams 独有）

**场景**：实习生王五调用财务 Agent，send_payment 被物理掩码

```python
# backend/app/services/logits_masking.py

class LogitsMaskingService:
    """Logits Masking 服务"""
    
    async def apply_team_masking_policy(
        self,
        user_id: str,
        team_id: str,
        available_tools: List[str]
    ) -> List[str]:
        """根据用户在 Team 中的角色，过滤可用工具"""
        
        # 1. 获取用户在 Team 中的角色
        team_member = await db.query(TeamMember).filter_by(
            user_id=user_id,
            team_id=team_id
        ).first()
        
        if not team_member:
            raise PermissionDeniedError("Not a team member")
        
        user_role = team_member.role  # lead / member / intern / guest
        
        # 2. 获取 Team 的 Masking 策略
        team = await db.get(Team, team_id)
        masking_policy = team.team_masking_policy["restricted_actions"]
        
        # 3. 过滤工具
        allowed_tools = []
        for tool in available_tools:
            if tool in masking_policy:
                # 检查该工具是否对当前角色开放
                allowed_roles = masking_policy[tool]
                if user_role.value in allowed_roles:
                    allowed_tools.append(tool)
            else:
                # 未受限的工具默认开放
                allowed_tools.append(tool)
        
        return allowed_tools
    
    async def mask_tool_in_prompt(
        self,
        user_id: str,
        team_id: str,
        system_prompt: str
    ) -> str:
        """在 System Prompt 中物理移除被掩码的工具定义"""
        
        # 1. 获取允许的工具列表
        all_tools = self._extract_tools_from_prompt(system_prompt)
        allowed_tools = await self.apply_team_masking_policy(user_id, team_id, all_tools)
        
        # 2. 重新生成 System Prompt（只包含允许的工具）
        filtered_prompt = self._rebuild_prompt_with_tools(system_prompt, allowed_tools)
        
        return filtered_prompt
```

**效果**：

- 张三（Lead）调用 Agent：看到完整工具列表 `[send_payment, read_data, ...]`
- 王五（Intern）调用同一个 Agent：`send_payment` 从 System Prompt 中物理移除，LLM 根本不知道有这个工具

---

### 3.3 Token 预算自动治理（Teams 独有）

**场景**：研发部 Token 消耗过快，系统自动降级模型

```python
# backend/app/services/token_governance.py

class TokenGovernanceService:
    """Token 预算治理服务"""
    
    async def check_and_enforce_budget(
        self,
        team_id: str,
        requested_tokens: int
    ) -> dict:
        """检查并执行 Token 预算策略"""
        
        # 1. 获取 Team 的 Token 预算
        team = await db.get(Team, team_id)
        budget = team.token_budget
        
        current_usage = budget["current_usage"]
        monthly_limit = budget["monthly_limit"]
        warning_threshold = budget["warning_threshold"]
        
        # 2. 计算使用率
        usage_rate = current_usage / monthly_limit
        
        # 3. 策略判断
        if usage_rate >= 1.0:
            # 超额：拒绝请求
            raise QuotaExceededError("Token budget exhausted")
        
        elif usage_rate >= warning_threshold:
            # 接近上限：触发降级策略
            if budget["auto_downgrade"]:
                return {
                    "allowed": True,
                    "action": "downgrade",
                    "original_model": "gpt-4",
                    "downgraded_model": "llama-3-8b",
                    "reason": f"Token usage at {usage_rate*100:.1f}%"
                }
        
        # 4. 正常通过
        return {"allowed": True, "action": "none"}
    
    async def record_token_usage(
        self,
        team_id: str,
        workspace_id: str,
        tokens_used: int,
        model: str
    ):
        """记录 Token 使用量"""
        
        # 1. 更新 Team 级别统计
        team = await db.get(Team, team_id)
        team.token_budget["current_usage"] += tokens_used
        
        # 2. 更新 Workspace 级别统计
        workspace = await db.get(Workspace, workspace_id)
        workspace.stats["monthly_tokens_used"] += tokens_used
        
        # 3. 记录详细日志（用于后续审计）
        await db.add(TokenUsageLog(
            team_id=team_id,
            workspace_id=workspace_id,
            tokens_used=tokens_used,
            model=model,
            timestamp=datetime.utcnow()
        ))
        
        await db.commit()
```

---

### 3.4 Personal vs Team 模式的创建流程

#### Personal 模式（简单）

```python
# backend/app/api/workspaces.py

@router.post("/workspaces")
async def create_personal_workspace(
    data: WorkspaceCreateRequest,
    user_id: str = Depends(get_current_user)
):
    """创建 Personal Workspace（无需 Organization/Team）"""
    
    # 1. 检查个人配额
    user = await db.get(User, user_id)
    current_count = await db.query(Workspace).filter_by(
        owner_id=user_id,
        workspace_type=WorkspaceType.PERSONAL
    ).count()
    
    if current_count >= user.personal_quota["max_workspaces"]:
        raise QuotaExceededError("Max workspaces reached")
    
    # 2. 创建 Workspace
    workspace = Workspace(
        id=str(uuid.uuid4()),
        workspace_type=WorkspaceType.PERSONAL,
        owner_id=user_id,
        team_id=None,  # Personal 模式
        name=data.name,
        slug=data.slug,
        filesystem_path=f"users/{user_id}/workspaces/{workspace.id}/"
    )
    
    # 3. 初始化文件系统
    await file_manager.create_workspace_structure(workspace.filesystem_path)
    
    await db.add(workspace)
    await db.commit()
    
    return {"workspace_id": workspace.id}
```

#### Team 模式（需要先创建 Organization → Team）

```python
@router.post("/teams/{team_id}/workspaces")
async def create_team_workspace(
    team_id: str,
    data: WorkspaceCreateRequest,
    user_id: str = Depends(get_current_user)
):
    """创建 Team Workspace"""
    
    # 1. 检查用户是否是 Team 成员
    team_member = await db.query(TeamMember).filter_by(
        user_id=user_id,
        team_id=team_id
    ).first()
    
    if not team_member:
        raise PermissionDeniedError()
    
    # 2. 检查 Team 的配额
    team = await db.get(Team, team_id)
    org = await db.get(Organization, team.org_id)
    
    if org.is_over_quota:
        raise QuotaExceededError()
    
    # 3. 创建 Workspace
    workspace = Workspace(
        id=str(uuid.uuid4()),
        workspace_type=WorkspaceType.TEAM,
        owner_id=user_id,
        team_id=team_id,
        name=data.name,
        slug=data.slug,
        filesystem_path=f"orgs/{org.id}/teams/{team_id}/workspaces/{workspace.id}/"
    )
    
    await db.add(workspace)
    await db.commit()
    
    return {"workspace_id": workspace.id}
```

---

## 4. 前端 UI 设计

### 4.1 导航结构

**Personal 模式**

```
顶部导航：
├── 🏠 Home
├── 📦 Workspaces (独立菜单，类似 Genspark)
│     ├── "财务分析"
│     ├── "代码开发"
│     └── + 新建 Workspace
├── 📊 Usage (个人用量统计)
└── ⚙️ Settings
```

**Team 模式（切换到 Organization 后）**

```
顶部导航：
├── 🏢 Organization
│     ├── Overview (概览)
│     ├── Members (成员管理)
│     └── Billing (计费)
│
├── 👥 Teams (独立菜单，类似 Figma Teams)
│     ├── Team 1: "研发部"
│     │     ├── Members (团队成员 + 角色管理)
│     │     ├── Shared Agents (共享的 Agent 技能包)
│     │     ├── Token Budget (Token 预算管理)
│     │     └── Settings
│     └── + 新建 Team
│
├── 📦 Workspaces (独立菜单，类似 Genspark)
│     ├── [按 Team 分组]
│     ├── Team "研发部"
│     │     ├── "后端开发" (Owner: 张三)
│     │     └── "前端开发" (Collaborator)
│     └── + 新建 Workspace
│
└── ⚙️ Settings
```

---

### 4.2 Workspace 看板（核心界面）

**超越 Genspark 的关键：白盒化执行空间**

```
┌─────────────────────────────────────────────────────────────┐
│ Workspace: "后端开发"                      [⚙️ Settings]    │
├─────────────────────────────────────────────────────────────┤
│ 👥 Collaborators: 张三(Owner), 李四(Editor), 王五(Viewer)   │
│ 🤖 Loaded Shared Agent: "金融分析专家" (from Team 共享池)    │
│ 💰 Token Usage: 1.2M / 10M (本月)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────┬───────────────────────────────────────┐
│  Agent 状态看板      │  实时对话 / 推理过程                   │
│                     │                                       │
│  🟢 Agent A: 运行中  │  [Streaming Output]                  │
│     ├─ Task 1: ✅   │  > 正在分析财务数据...                │
│     ├─ Task 2: 🔄   │  > 调用工具: read_excel()            │
│     └─ Task 3: ⏸️   │  > 生成摘要...                       │
│                     │                                       │
│  ⏸️ Agent B: 暂停    │  [用户可以点击任意 Agent 查看详情]     │
│     └─ Task 4: ⏸️   │                                       │
│                     │  [Logits 分布可视化]                 │
│  [+ 新建 Agent]     │  send_payment: 🚫 (被 Masking)       │
│                     │  read_data: ✅                        │
└─────────────────────┴───────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  文件树 (FileSystem)                                         │
│  📁 context/                                                │
│     ├─ memory.md                                            │
│     └─ learnings.md                                         │
│  📁 cache/                                                  │
│  📁 artifacts/                                              │
│     ├─ report_2026-01-10.md                                │
│     └─ analysis.xlsx                                       │
└─────────────────────────────────────────────────────────────┘
```

**关键交互**：

1. **实时推理可见**：所有 Collaborators 都能实时看到 Agent 的推理过程（类似 Figma 多人光标）
2. **人机链路干预**：用户可以点击某个 Agent，调整它的 Logits 约束或补充信息
3. **Logits 可视化**：显示哪些工具被 Masking（实习生看到 🚫）

---

### 4.3 Team 共享池界面（独有功能）

```
┌─────────────────────────────────────────────────────────────┐
│ Team: "研发部"                            [⚙️ Settings]     │
├─────────────────────────────────────────────────────────────┤
│ 💰 Token Budget: 1.2B / 10B (本月)  [⚠️ 90% 警告]          │
│ 👥 Members: 3 (1 Lead, 2 Members)                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🤖 Shared Agent Pool (共享 Agent 技能包)                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📦 "金融分析专家 Agent"                               │  │
│  │    Contributor: 张三                                  │  │
│  │    KV-Cache Snapshot ID: abc-123                      │  │
│  │    Downloads: 5 次                                    │  │
│  │    [💾 Load to My Workspace]                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 📦 "代码审查 Agent"                                   │  │
│  │    Contributor: 李四                                  │  │
│  │    [💾 Load to My Workspace]                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [+ Publish Agent from Workspace]                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🔒 Logits Masking Policy (团队级权限策略)                   │
│                                                             │
│  send_payment:      仅 Lead 可用                            │
│  delete_data:       仅 Lead 可用                            │
│  execute_shell:     Member 以上可用                         │
│  read_data:         所有人可用                              │
│                                                             │
│  [✏️ Edit Policy]                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 数据隔离策略

### 5.1 文件系统物理隔离

**Personal 模式**

```
/data/
  └── users/
        └── user-{user_id}/
              └── workspaces/
                    ├── ws-{id-1}/
                    │     ├── context/
                    │     ├── cache/
                    │     └── artifacts/
                    └── ws-{id-2}/
```

**Team 模式**

```
/data/
  └── orgs/
        └── org-{org_id}/
              └── teams/
                    └── team-{team_id}/
                          ├── shared/         # Team 共享资源
                          └── workspaces/
                                ├── ws-{id-1}/
                                └── ws-{id-2}/
```

---

### 5.2 Redis KV-Cache 隔离

**Personal 模式**

```
kv_cache:user:{user_id}:ws:{workspace_id}:session:{session_id}
```

**Team 模式**

```
kv_cache:org:{org_id}:team:{team_id}:ws:{workspace_id}:session:{session_id}

# Team 共享 KV-Cache 快照
shared_agents:team:{team_id}:snapshot:{snapshot_id}
```

---

### 5.3 PostgreSQL RLS（Row-Level Security）

```sql
-- Personal Workspace 可见性
CREATE POLICY personal_workspace_policy ON workspaces
FOR SELECT
USING (
    workspace_type = 'personal' 
    AND owner_id = current_setting('app.current_user_id')::uuid
);

-- Team Workspace 可见性
CREATE POLICY team_workspace_policy ON workspaces
FOR SELECT
USING (
    workspace_type = 'team'
    AND (
        -- 所有者可见
        owner_id = current_setting('app.current_user_id')::uuid
        OR
        -- Team 成员可见（根据 visibility）
        (visibility = 'team' AND EXISTS (
            SELECT 1 FROM team_members 
            WHERE team_id = workspaces.team_id 
            AND user_id = current_setting('app.current_user_id')::uuid
        ))
    )
);
```

---

## 6. 实施路线图

### Phase 1: 基础架构（Week 1-2）

- [ ] 实现 User/Workspace 数据模型（支持 Personal 和 Team 两种模式）
- [ ] 实现文件系统物理隔离
- [ ] 实现 Redis KV-Cache 命名空间隔离
- [ ] 实现 RLS 策略

### Phase 2: Personal 模式（Week 3-4）

- [ ] Personal Workspace CRUD API
- [ ] Personal 模式前端界面
- [ ] KV-Cache 快照保存/恢复
- [ ] 配额检查（personal_quota）

### Phase 3: Organization & Team（Week 5-6）

- [ ] Organization/Team 数据模型
- [ ] Organization/Team CRUD API
- [ ] 成员管理（OrganizationMember, TeamMember）
- [ ] Token 预算管理

### Phase 4: Team 高级功能（Week 7-8）

- [ ] **KV-Cache 快照共享**（publish_agent_to_team, load_shared_agent）
- [ ] **Logits Masking 权限控制**（基于 TeamRole）
- [ ] **Token 预算自动治理**（自动降级模型）
- [ ] Team 共享池前端界面

### Phase 5: 协作与实时性（Week 9-10）

- [ ] Workspace 多人协作（WebSocket）
- [ ] 实时 Agent 状态推送
- [ ] Logits 分布可视化
- [ ] 人机链路干预功能

---

## 7. 关键指标（KPI）

### 功能完成度

- [ ] Personal 模式：用户可直接创建 Workspace，无需 Organization
- [ ] Team 模式：支持 Organization → Team → Workspace 三层结构
- [ ] KV-Cache 快照共享：专家 Agent 可发布到 Team
- [ ] Logits Masking：基于角色的原子级权限控制
- [ ] Token 预算治理：自动降级模型

### 用户体验

- [ ] Personal 模式创建 Workspace < 3 秒
- [ ] Team 模式加载共享 Agent < 2 秒
- [ ] 多人协作实时延迟 < 200ms
- [ ] Workspace 看板刷新率 > 30 FPS

### 安全性

- [ ] 数据物理隔离验证通过
- [ ] RLS 策略测试覆盖 100%
- [ ] Logits Masking 无法绕过（物理移除）

---

## 8. 总结

### 8.1 核心差异化

✅ **Personal 模式**：无需创建 Organization，用户直接创建 Workspace，类似 Manus 但更强大  
✅ **Team 模式**：多人共享 Agent 状态（KV-Cache 快照），超越 Figma + Genspark  
✅ **Workspace = KV-Cache 物理隔离环境 + 长期资产沉淀**  
✅ **Teams = 共享的智能池 + 算力治理中心**  
✅ **Logits Masking**：原子级权限控制（能力脱敏）  
✅ **Token 预算自动治理**：成本透明、可控  

### 8.2 超越 Manus 的关键点

| 维度 | Manus | TokenDance |
|------|-------|------------|
| **Workspace** | 无 | 物理隔离的 KV-Cache 环境 + 长期记忆 |
| **协作** | 不支持 | 多人共享 Agent 状态 + 实时协作 |
| **权限** | 无 | Logits Masking 原子级权限 |
| **资源管理** | 不可见 | Token 预算 + 自动治理 |
| **知识传递** | 无 | KV-Cache 快照共享 |

---

**下一步**：基于新架构更新开发计划（Plan）！🚀
