# TokenDance 技术架构设计 - 低层设计 (LLD)

> Version: 1.0.0 | MVP阶段
> Last Updated: 2026-01-08

## 1. 项目目录结构

```
TokenDance/
├── packages/
│   ├── web/                          # 前端项目
│   │   ├── src/
│   │   │   ├── api/                  # API调用封装
│   │   │   │   ├── client.ts
│   │   │   │   ├── chat.ts
│   │   │   │   └── workspace.ts
│   │   │   ├── components/           # 通用组件
│   │   │   │   ├── chat/
│   │   │   │   │   ├── ChatMessage.vue
│   │   │   │   │   ├── ChatInput.vue
│   │   │   │   │   ├── ThinkingBlock.vue
│   │   │   │   │   └── ToolCallBlock.vue
│   │   │   │   ├── common/
│   │   │   │   │   ├── ConfirmDialog.vue
│   │   │   │   │   ├── ProgressIndicator.vue
│   │   │   │   │   └── CitationCard.vue
│   │   │   │   └── layout/
│   │   │   │       ├── Sidebar.vue
│   │   │   │       └── Header.vue
│   │   │   ├── views/                # 页面视图
│   │   │   │   ├── ChatView.vue
│   │   │   │   ├── WorkspaceView.vue
│   │   │   │   └── SettingsView.vue
│   │   │   ├── stores/               # Pinia状态管理
│   │   │   │   ├── chat.ts
│   │   │   │   ├── session.ts
│   │   │   │   └── user.ts
│   │   │   ├── composables/          # 组合式函数
│   │   │   │   ├── useWebSocket.ts
│   │   │   │   ├── useSSE.ts
│   │   │   │   └── useTheme.ts
│   │   │   ├── types/                # TypeScript类型
│   │   │   │   ├── message.ts
│   │   │   │   ├── session.ts
│   │   │   │   └── tool.ts
│   │   │   ├── App.vue
│   │   │   └── main.ts
│   │   ├── package.json
│   │   ├── vite.config.ts
│   │   └── tailwind.config.js
│   │
│   ├── server/                       # 后端项目
│   │   ├── app/
│   │   │   ├── api/                  # API路由
│   │   │   │   ├── __init__.py
│   │   │   │   ├── deps.py           # 依赖注入
│   │   │   │   ├── v1/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── chat.py
│   │   │   │   │   ├── session.py
│   │   │   │   │   ├── workspace.py
│   │   │   │   │   └── artifact.py
│   │   │   │   └── websocket.py
│   │   │   ├── core/                 # 核心引擎
│   │   │   │   ├── __init__.py
│   │   │   │   ├── engine.py         # Agent主循环
│   │   │   │   ├── context.py        # Context管理器
│   │   │   │   ├── planner.py        # 计划管理
│   │   │   │   ├── validator.py      # 结果验证
│   │   │   │   └── llm/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── base.py
│   │   │   │       ├── claude.py
│   │   │   │       └── gemini.py
│   │   │   ├── skills/               # Skill系统
│   │   │   │   ├── __init__.py
│   │   │   │   ├── registry.py       # Skill注册表
│   │   │   │   ├── loader.py         # Skill加载器
│   │   │   │   ├── matcher.py        # Skill匹配器
│   │   │   │   └── parser.py         # SKILL.md解析
│   │   │   ├── tools/                # 工具实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── web_search.py
│   │   │   │   ├── read_url.py
│   │   │   │   ├── code_execute.py
│   │   │   │   ├── file_ops.py
│   │   │   │   └── create_artifact.py
│   │   │   ├── memory/               # 记忆系统
│   │   │   │   ├── __init__.py
│   │   │   │   ├── working.py
│   │   │   │   ├── episode.py
│   │   │   │   └── longterm.py
│   │   │   ├── sandbox/              # 沙箱管理
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py
│   │   │   │   └── container.py
│   │   │   ├── models/               # 数据模型
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── session.py
│   │   │   │   ├── message.py
│   │   │   │   └── artifact.py
│   │   │   ├── schemas/              # Pydantic Schema
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py
│   │   │   │   ├── session.py
│   │   │   │   └── tool.py
│   │   │   ├── services/             # 业务服务
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat_service.py
│   │   │   │   ├── session_service.py
│   │   │   │   └── artifact_service.py
│   │   │   ├── db/                   # 数据库
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py
│   │   │   │   └── migrations/
│   │   │   ├── config.py             # 配置
│   │   │   └── main.py               # 入口
│   │   ├── skills/                   # Skill定义文件
│   │   │   ├── deep_research/
│   │   │   │   ├── SKILL.md
│   │   │   │   └── resources/
│   │   │   │       ├── search.py
│   │   │   │       └── summarize.md
│   │   │   └── ppt/
│   │   │       ├── SKILL.md
│   │   │       └── resources/
│   │   │           ├── layout.py
│   │   │           └── templates/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── shared/                       # 共享定义
│       ├── types/
│       └── constants/
│
├── docker/
│   ├── sandbox/
│   │   └── Dockerfile
│   └── docker-compose.yml
│
├── docs/                             # 文档
├── scripts/                          # 脚本
└── README.md
```

## 2. 数据库Schema

### 2.1 ER图

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     users       │       │   workspaces    │       │    sessions     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │──┐    │ id (PK)         │
│ email           │  │    │ user_id (FK)    │◄─┘    │ workspace_id(FK)│◄─┐
│ name            │  └───►│ name            │       │ title           │  │
│ avatar_url      │       │ settings        │       │ status          │  │
│ preferences     │       │ created_at      │       │ skill_id        │  │
│ created_at      │       │ updated_at      │       │ context_summary │  │
│ updated_at      │       └─────────────────┘       │ created_at      │  │
└─────────────────┘                                 │ updated_at      │  │
                                                    └─────────────────┘  │
                                                            │            │
                          ┌─────────────────┐               │            │
                          │    messages     │◄──────────────┘            │
                          ├─────────────────┤                            │
                          │ id (PK)         │                            │
                          │ session_id (FK) │                            │
                          │ role            │                            │
                          │ content         │       ┌─────────────────┐  │
                          │ thinking        │       │   artifacts     │  │
                          │ tool_calls      │       ├─────────────────┤  │
                          │ citations       │       │ id (PK)         │  │
                          │ created_at      │       │ session_id (FK) │◄─┘
                          └─────────────────┘       │ type            │
                                                    │ name            │
┌─────────────────┐       ┌─────────────────┐       │ file_path       │
│     skills      │       │  user_memories  │       │ metadata        │
├─────────────────┤       ├─────────────────┤       │ created_at      │
│ id (PK)         │       │ id (PK)         │       └─────────────────┘
│ name            │       │ user_id (FK)    │
│ description     │       │ content         │
│ version         │       │ embedding (vec) │
│ metadata        │       │ category        │
│ enabled         │       │ created_at      │
│ created_at      │       └─────────────────┘
└─────────────────┘
```

### 2.2 表结构定义

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    avatar_url TEXT,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 工作空间表
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 会话表
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(200),
    status VARCHAR(20) DEFAULT 'active', -- active, completed, failed
    skill_id VARCHAR(100),  -- 当前激活的Skill
    context_summary TEXT,   -- 压缩后的上下文摘要
    todo_list JSONB,        -- Plan Recitation用
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 消息表
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system, tool
    content TEXT,
    thinking TEXT,             -- Agent思考过程
    tool_calls JSONB,          -- [{id, name, args, result, status}]
    citations JSONB,           -- [{index, url, title, snippet}]
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 产出物表
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- ppt, document, report, code
    name VARCHAR(200) NOT NULL,
    file_path TEXT NOT NULL,   -- MinIO路径
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Skill注册表
CREATE TABLE skills (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 用户长期记忆表 (向量存储)
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),    -- pgvector
    category VARCHAR(50),      -- preference, knowledge, history
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建向量索引
CREATE INDEX ON user_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 创建常用查询索引
CREATE INDEX idx_sessions_workspace ON sessions(workspace_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
CREATE INDEX idx_user_memories_user ON user_memories(user_id);
```

## 3. API设计

### 3.1 RESTful API

#### 3.1.1 会话管理

```yaml
# 创建会话
POST /api/v1/sessions
Request:
  {
    "workspace_id": "uuid",
    "title": "string (optional)"
  }
Response:
  {
    "id": "uuid",
    "workspace_id": "uuid",
    "title": "New Chat",
    "status": "active",
    "created_at": "2026-01-08T10:00:00Z"
  }

# 获取会话列表
GET /api/v1/sessions?workspace_id={uuid}&limit=20&offset=0
Response:
  {
    "items": [...],
    "total": 100,
    "limit": 20,
    "offset": 0
  }

# 获取会话详情
GET /api/v1/sessions/{session_id}
Response:
  {
    "id": "uuid",
    "title": "AI研究调研",
    "status": "active",
    "skill_id": "deep_research",
    "messages": [...],
    "artifacts": [...],
    "created_at": "..."
  }

# 删除会话
DELETE /api/v1/sessions/{session_id}
Response: 204 No Content
```

#### 3.1.2 聊天接口

```yaml
# 发送消息 (SSE流式响应)
POST /api/v1/chat/{session_id}/message
Request:
  {
    "content": "帮我调研AI Agent市场",
    "attachments": [
      {"type": "file", "file_id": "uuid"}
    ]
  }
Response: SSE Stream
  event: thinking
  data: {"content": "分析用户需求..."}

  event: tool_call
  data: {"id": "tc_1", "name": "web_search", "args": {"query": "AI Agent market 2024"}, "status": "running"}

  event: tool_result
  data: {"id": "tc_1", "status": "success", "result": "..."}

  event: content
  data: {"content": "根据调研结果...", "citations": [...]}

  event: done
  data: {"message_id": "uuid", "tokens_used": 1500}

# 确认执行 (HITL)
POST /api/v1/chat/{session_id}/confirm
Request:
  {
    "action_id": "uuid",
    "confirmed": true
  }
Response:
  {
    "status": "confirmed",
    "next_action": "..."
  }

# 停止生成
POST /api/v1/chat/{session_id}/stop
Response:
  {
    "status": "stopped"
  }
```

#### 3.1.3 产出物管理

```yaml
# 获取产出物列表
GET /api/v1/artifacts?session_id={uuid}
Response:
  {
    "items": [
      {
        "id": "uuid",
        "type": "ppt",
        "name": "AI发展趋势.pptx",
        "download_url": "...",
        "preview_url": "...",
        "created_at": "..."
      }
    ]
  }

# 下载产出物
GET /api/v1/artifacts/{artifact_id}/download
Response: Binary file

# 预览产出物
GET /api/v1/artifacts/{artifact_id}/preview
Response:
  {
    "type": "ppt",
    "pages": [
      {"index": 1, "thumbnail_url": "...", "content": "..."}
    ]
  }

# 重新生成单页(PPT)
POST /api/v1/artifacts/{artifact_id}/regenerate
Request:
  {
    "page_index": 3,
    "instructions": "内容更简洁一些"
  }
Response: SSE Stream
```

#### 3.1.4 工作空间管理

```yaml
# 获取工作空间
GET /api/v1/workspaces
Response:
  {
    "items": [
      {
        "id": "uuid",
        "name": "默认工作空间",
        "session_count": 10,
        "created_at": "..."
      }
    ]
  }

# 获取文件列表
GET /api/v1/workspaces/{workspace_id}/files
Response:
  {
    "items": [
      {
        "id": "uuid",
        "name": "report.pdf",
        "size": 1024000,
        "type": "application/pdf",
        "created_at": "..."
      }
    ]
  }

# 上传文件
POST /api/v1/workspaces/{workspace_id}/files
Request: multipart/form-data
Response:
  {
    "id": "uuid",
    "name": "report.pdf",
    "url": "..."
  }
```

### 3.2 WebSocket API

```yaml
# 连接
WS /api/v1/ws?token={jwt_token}

# 客户端消息
{
  "type": "subscribe",
  "session_id": "uuid"
}

{
  "type": "unsubscribe",
  "session_id": "uuid"
}

{
  "type": "ping"
}

# 服务端消息
{
  "type": "pong"
}

{
  "type": "session_update",
  "session_id": "uuid",
  "data": {
    "status": "completed"
  }
}

{
  "type": "notification",
  "data": {
    "title": "PPT生成完成",
    "message": "您的PPT已生成完毕",
    "artifact_id": "uuid"
  }
}
```

## 4. 核心类设计

### 4.1 Agent Engine

```python
# app/core/engine.py

from typing import AsyncIterator
from dataclasses import dataclass
from enum import Enum

class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALLING = "tool_calling"
    WAITING_CONFIRM = "waiting_confirm"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentEvent:
    type: str  # thinking, tool_call, tool_result, content, error, done
    data: dict

class AgentEngine:
    """Agent核心引擎，负责决策循环"""
    
    def __init__(
        self,
        session_id: str,
        llm_provider: BaseLLMProvider,
        context_manager: ContextManager,
        skill_system: SkillSystem,
        tool_executor: ToolExecutor,
        memory: MemorySystem,
        validator: Validator,
    ):
        self.session_id = session_id
        self.llm = llm_provider
        self.context = context_manager
        self.skills = skill_system
        self.tools = tool_executor
        self.memory = memory
        self.validator = validator
        self.state = AgentState.IDLE
        self.max_iterations = 50
        
    async def run(self, user_message: str) -> AsyncIterator[AgentEvent]:
        """执行Agent主循环，流式返回事件"""
        
        # 1. Skill匹配
        matched_skill = await self.skills.match(user_message)
        if matched_skill:
            await self.skills.load_l2(matched_skill.id)
            yield AgentEvent("skill_activated", {"skill": matched_skill.name})
        
        # 2. 添加用户消息到context
        await self.context.add_message("user", user_message)
        
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            self.state = AgentState.THINKING
            
            # 3. 组装prompt (包含Plan Recitation)
            messages = await self.context.build_messages()
            
            # 4. LLM推理
            yield AgentEvent("thinking", {"status": "start"})
            response = await self.llm.chat(messages, stream=True)
            
            thinking_content = ""
            tool_calls = []
            text_content = ""
            
            async for chunk in response:
                if chunk.type == "thinking":
                    thinking_content += chunk.content
                    yield AgentEvent("thinking", {"content": chunk.content})
                elif chunk.type == "tool_call":
                    tool_calls.append(chunk.tool_call)
                    yield AgentEvent("tool_call", {
                        "id": chunk.tool_call.id,
                        "name": chunk.tool_call.name,
                        "args": chunk.tool_call.args,
                        "status": "pending"
                    })
                elif chunk.type == "text":
                    text_content += chunk.content
                    yield AgentEvent("content", {"content": chunk.content})
            
            # 5. 执行工具调用
            if tool_calls:
                self.state = AgentState.TOOL_CALLING
                for tc in tool_calls:
                    # 检查是否需要HITL确认
                    if self.tools.requires_confirmation(tc.name):
                        self.state = AgentState.WAITING_CONFIRM
                        yield AgentEvent("confirm_required", {
                            "action_id": tc.id,
                            "tool": tc.name,
                            "args": tc.args,
                            "description": self.tools.get_description(tc)
                        })
                        confirmed = await self._wait_for_confirmation(tc.id)
                        if not confirmed:
                            yield AgentEvent("tool_result", {
                                "id": tc.id,
                                "status": "cancelled"
                            })
                            continue
                    
                    # 执行工具
                    yield AgentEvent("tool_call", {
                        "id": tc.id,
                        "status": "running"
                    })
                    result = await self.tools.execute(tc)
                    
                    # 验证结果 (双系统验证)
                    if self.validator.should_verify(tc.name):
                        is_valid = await self.validator.verify(tc, result)
                        if not is_valid:
                            result.status = "invalid"
                            result.error = "Result verification failed"
                    
                    yield AgentEvent("tool_result", {
                        "id": tc.id,
                        "status": result.status,
                        "result": result.summary,
                        "error": result.error
                    })
                    
                    # 添加工具结果到context
                    await self.context.add_tool_result(tc.id, result)
                
                # 继续循环，让LLM处理工具结果
                continue
            
            # 6. 没有工具调用，检查是否完成
            if text_content:
                # 添加assistant消息
                await self.context.add_message("assistant", text_content, {
                    "thinking": thinking_content,
                    "citations": self._extract_citations(text_content)
                })
                
                # 更新Memory
                await self.memory.update_working(self.session_id)
                
                # 检查是否还有未完成的TODO
                if await self._check_completion():
                    self.state = AgentState.COMPLETED
                    yield AgentEvent("done", {
                        "status": "completed",
                        "tokens_used": await self.context.get_tokens_used()
                    })
                    break
        
        if iteration >= self.max_iterations:
            self.state = AgentState.FAILED
            yield AgentEvent("done", {
                "status": "max_iterations_reached",
                "tokens_used": await self.context.get_tokens_used()
            })
    
    async def _wait_for_confirmation(self, action_id: str) -> bool:
        """等待用户确认"""
        # 实现确认等待逻辑
        pass
    
    async def _check_completion(self) -> bool:
        """检查任务是否完成 (Check-and-Stop)"""
        # 检查TODO列表是否全部完成
        pass
    
    def _extract_citations(self, content: str) -> list:
        """提取引用"""
        pass
```

### 4.2 Context Manager

```python
# app/core/context.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ContextConfig:
    max_tokens: int = 128000  # Claude default
    compression_threshold: float = 0.7  # 70%时触发压缩
    system_prompt_tokens: int = 2000
    skill_metadata_tokens: int = 100  # per skill
    plan_recitation_tokens: int = 200

class ContextManager:
    """Context管理器，负责token预算和压缩"""
    
    def __init__(self, session_id: str, config: ContextConfig):
        self.session_id = session_id
        self.config = config
        self.messages: List[Message] = []
        self.active_skill_id: Optional[str] = None
        self.todo_list: List[dict] = []
        self._tokens_used = 0
        
    async def build_messages(self) -> List[dict]:
        """构建发送给LLM的消息列表"""
        messages = []
        
        # 1. System Prompt (固定，利于KV Cache)
        messages.append({
            "role": "system",
            "content": await self._build_system_prompt()
        })
        
        # 2. L1 Skill元数据 (固定)
        # 已包含在system prompt中
        
        # 3. L2 Skill指令 (如果激活)
        if self.active_skill_id:
            skill_instructions = await self._get_skill_instructions()
            messages.append({
                "role": "system",
                "content": f"[Active Skill Instructions]\n{skill_instructions}"
            })
        
        # 4. 对话历史 (可能压缩)
        history = await self._get_compressed_history()
        messages.extend(history)
        
        # 5. Plan Recitation (末尾)
        if self.todo_list:
            messages.append({
                "role": "system",
                "content": self._build_plan_recitation()
            })
        
        return messages
    
    async def add_message(self, role: str, content: str, metadata: dict = None):
        """添加消息"""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            tokens=self._count_tokens(content)
        )
        self.messages.append(message)
        self._tokens_used += message.tokens
        
        # 检查是否需要压缩
        await self._maybe_compress()
    
    async def add_tool_result(self, tool_call_id: str, result: ToolResult):
        """添加工具调用结果"""
        # 对结果进行摘要（Dual Context Streams）
        summary = await self._summarize_tool_result(result)
        
        # 全量结果存储到文件系统
        await self._store_full_result(tool_call_id, result)
        
        # 摘要放入context
        await self.add_message("tool", summary, {
            "tool_call_id": tool_call_id,
            "full_result_ref": f"tool_results/{tool_call_id}"
        })
    
    async def _maybe_compress(self):
        """检查并执行压缩"""
        usage = self._tokens_used / self.config.max_tokens
        if usage > self.config.compression_threshold:
            await self._compress()
    
    async def _compress(self):
        """压缩上下文"""
        # 策略1: 对话历史摘要
        old_messages = self.messages[:-5]  # 保留最近5条
        if old_messages:
            summary = await self._summarize_messages(old_messages)
            self.messages = [
                Message(role="system", content=f"[Previous conversation summary]\n{summary}")
            ] + self.messages[-5:]
        
        # 策略2: 工具结果精简 (已在add_tool_result中处理)
        
        # 重新计算tokens
        self._tokens_used = sum(m.tokens for m in self.messages)
    
    def _build_plan_recitation(self) -> str:
        """构建Plan Recitation内容"""
        lines = ["[Current Task Progress]"]
        for i, todo in enumerate(self.todo_list, 1):
            status = "✓" if todo.get("completed") else "○"
            lines.append(f"{status} {i}. {todo['title']}")
        lines.append("\n[Remember] Stay focused on completing the above tasks.")
        return "\n".join(lines)
    
    def update_todo_list(self, todos: List[dict]):
        """更新TODO列表"""
        self.todo_list = todos
    
    async def _build_system_prompt(self) -> str:
        """构建系统提示"""
        # 包含角色定义、行为准则、L1 Skill元数据等
        pass
    
    async def _get_skill_instructions(self) -> str:
        """获取当前Skill的L2指令"""
        pass
    
    async def _get_compressed_history(self) -> List[dict]:
        """获取压缩后的对话历史"""
        pass
    
    async def _summarize_tool_result(self, result: ToolResult) -> str:
        """摘要工具结果 (Read-then-Summarize)"""
        # 使用小模型进行快速摘要
        pass
    
    async def _summarize_messages(self, messages: List[Message]) -> str:
        """摘要对话历史"""
        pass
    
    def _count_tokens(self, text: str) -> int:
        """计算token数"""
        # 使用tiktoken或估算
        pass
```

### 4.3 Tool System

```python
# app/tools/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Type
from enum import Enum

class ToolRiskLevel(Enum):
    LOW = "low"           # 自动执行
    MEDIUM = "medium"     # 展示后确认
    HIGH = "high"         # 必须明确授权

@dataclass
class ToolResult:
    status: str  # success, error, cancelled
    data: Any
    summary: str  # 精简摘要
    error: Optional[str] = None

class BaseTool(ABC):
    """工具基类"""
    
    name: str
    description: str
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    
    @abstractmethod
    async def execute(self, **params) -> ToolResult:
        """执行工具"""
        pass
    
    def get_schema(self) -> dict:
        """获取参数schema (用于LLM tool use)"""
        pass

class ToolRegistry:
    """工具注册表"""
    
    _tools: Dict[str, Type[BaseTool]] = {}
    
    @classmethod
    def register(cls, tool_class: Type[BaseTool]):
        """注册工具"""
        cls._tools[tool_class.name] = tool_class
        return tool_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseTool]]:
        return cls._tools.get(name)
    
    @classmethod
    def get_all_schemas(cls) -> List[dict]:
        """获取所有工具的schema"""
        return [t().get_schema() for t in cls._tools.values()]

tool_registry = ToolRegistry()

# app/tools/web_search.py

@tool_registry.register
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information"
    risk_level = ToolRiskLevel.LOW
    
    async def execute(self, query: str, num_results: int = 5) -> ToolResult:
        """执行网页搜索"""
        try:
            # 调用Tavily API
            results = await tavily_client.search(query, max_results=num_results)
            
            # 生成摘要
            summary = f"Found {len(results)} results for '{query}'"
            
            return ToolResult(
                status="success",
                data=results,
                summary=summary
            )
        except Exception as e:
            return ToolResult(
                status="error",
                data=None,
                summary="Search failed",
                error=str(e)
            )
    
    def get_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Number of results to return"
                    }
                },
                "required": ["query"]
            }
        }

# app/tools/code_execute.py

@tool_registry.register
class CodeExecuteTool(BaseTool):
    name = "code_execute"
    description = "Execute Python code in a sandboxed environment"
    risk_level = ToolRiskLevel.MEDIUM  # 需要确认
    
    def __init__(self, sandbox_manager: SandboxManager):
        self.sandbox = sandbox_manager
    
    async def execute(self, code: str, timeout: int = 30) -> ToolResult:
        """在沙箱中执行代码"""
        try:
            result = await self.sandbox.execute(code, timeout=timeout)
            
            return ToolResult(
                status="success",
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_value": result.return_value
                },
                summary=f"Code executed. Output: {result.stdout[:200]}..."
            )
        except TimeoutError:
            return ToolResult(
                status="error",
                data=None,
                summary="Execution timeout",
                error="Code execution exceeded timeout"
            )
        except Exception as e:
            return ToolResult(
                status="error",
                data=None,
                summary="Execution failed",
                error=str(e)
            )
```

### 4.4 Validator (双系统验证)

```python
# app/core/validator.py

class Validator:
    """结果验证器 (B模型)"""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        # 使用更小/更严格的模型
        self.llm = llm_provider
        
        # 需要验证的工具
        self.verify_tools = {
            "web_search": self._verify_search_result,
            "code_execute": self._verify_code_result,
            "create_artifact": self._verify_artifact,
        }
    
    def should_verify(self, tool_name: str) -> bool:
        """判断是否需要验证"""
        return tool_name in self.verify_tools
    
    async def verify(self, tool_call: ToolCall, result: ToolResult) -> bool:
        """验证工具执行结果"""
        verifier = self.verify_tools.get(tool_call.name)
        if verifier:
            return await verifier(tool_call, result)
        return True
    
    async def _verify_search_result(self, tool_call: ToolCall, result: ToolResult) -> bool:
        """验证搜索结果"""
        # 检查结果是否与query相关
        # 检查来源是否可信
        prompt = f"""
        Verify if the search results are relevant and credible.
        Query: {tool_call.args.get('query')}
        Results: {result.data}
        
        Respond with:
        - VALID: if results are relevant and from credible sources
        - INVALID: if results seem fabricated, irrelevant, or from suspicious sources
        """
        response = await self.llm.chat([{"role": "user", "content": prompt}])
        return "VALID" in response.content.upper()
    
    async def _verify_code_result(self, tool_call: ToolCall, result: ToolResult) -> bool:
        """验证代码执行结果"""
        # 检查输出是否合理
        # 检查是否有异常
        if result.status != "success":
            return False
        
        # 可以添加更多验证逻辑
        return True
    
    async def _verify_artifact(self, tool_call: ToolCall, result: ToolResult) -> bool:
        """验证产出物"""
        # 检查文件是否真实生成
        # 检查内容是否符合要求
        pass
```

## 5. 前端类型定义

```typescript
// packages/web/src/types/message.ts

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  thinking?: string
  tool_calls?: ToolCall[]
  citations?: Citation[]
  created_at: string
}

export interface ToolCall {
  id: string
  name: string
  args: Record<string, any>
  status: 'pending' | 'running' | 'success' | 'error' | 'cancelled'
  result?: any
  error?: string
}

export interface Citation {
  index: number
  url: string
  title: string
  domain: string
  snippet: string
}

// packages/web/src/types/session.ts

export interface Session {
  id: string
  workspace_id: string
  title: string
  status: 'active' | 'completed' | 'failed'
  skill_id?: string
  created_at: string
  updated_at: string
}

// packages/web/src/types/artifact.ts

export interface Artifact {
  id: string
  session_id: string
  type: 'ppt' | 'document' | 'report' | 'code'
  name: string
  download_url: string
  preview_url?: string
  metadata: Record<string, any>
  created_at: string
}

// packages/web/src/types/sse.ts

export interface SSEEvent {
  type: 'thinking' | 'tool_call' | 'tool_result' | 'content' | 'confirm_required' | 'done' | 'error'
  data: any
}

export interface ThinkingEvent {
  type: 'thinking'
  data: {
    content: string
    status?: 'start' | 'end'
  }
}

export interface ToolCallEvent {
  type: 'tool_call'
  data: {
    id: string
    name: string
    args?: Record<string, any>
    status: 'pending' | 'running'
  }
}

export interface ToolResultEvent {
  type: 'tool_result'
  data: {
    id: string
    status: 'success' | 'error' | 'cancelled'
    result?: string
    error?: string
  }
}

export interface ContentEvent {
  type: 'content'
  data: {
    content: string
    citations?: Citation[]
  }
}

export interface ConfirmRequiredEvent {
  type: 'confirm_required'
  data: {
    action_id: string
    tool: string
    args: Record<string, any>
    description: string
  }
}

export interface DoneEvent {
  type: 'done'
  data: {
    status: 'completed' | 'stopped' | 'max_iterations_reached'
    message_id: string
    tokens_used: number
  }
}
```

## 6. 附录

### A. 相关文档

- [HLD文档](./HLD.md)
- [Skill专项设计](../modules/Skill-Design.md)
- [Memory专项设计](../modules/Memory-Design.md)
- [Sandbox专项设计](../modules/Sandbox-Design.md)

### B. 错误码定义

| 错误码 | 说明 |
|-------|------|
| 1001 | 认证失败 |
| 1002 | 权限不足 |
| 2001 | 会话不存在 |
| 2002 | 会话已结束 |
| 3001 | 工具执行失败 |
| 3002 | 工具超时 |
| 4001 | LLM调用失败 |
| 4002 | Token超限 |
| 5001 | 沙箱创建失败 |
| 5002 | 代码执行超时 |
