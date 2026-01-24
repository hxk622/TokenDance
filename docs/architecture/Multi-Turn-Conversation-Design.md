# 多轮对话架构设计 (长期方案)

## 一、设计目标

### 核心问题
当前架构中,Session 只支持单次执行,无法真正实现多轮对话:
- ❌ Session 状态为 COMPLETED 后无法继续
- ❌ 追问消息需要断开重连,丢失上下文
- ❌ 不符合"会话"的语义

### 设计目标
1. **真正的多轮对话**: 支持在同一个上下文中持续交互
2. **上下文持久化**: 跨轮次保持记忆和状态
3. **灵活的对话管理**: 支持暂停、恢复、分支、归档
4. **向后兼容**: 不破坏现有 Session 和 Project 架构

---

## 二、架构设计

### 2.1 概念模型

```
Workspace (工作空间)
├── Projects (项目 - 现有)
│   └── Conversations (对话 - 现有,基于 Project)
│
└── Conversations (独立对话 - 新增)
    ├── Turn 1 (对话轮次)
    │   ├── User Message
    │   ├── Session (执行)
    │   └── Assistant Message
    ├── Turn 2
    │   ├── User Message
    │   ├── Session (执行)
    │   └── Assistant Message
    └── ...
```

**关键设计决策**:
1. **保留现有 Project-Conversation 架构** (用于项目协作场景)
2. **新增独立 Conversation 架构** (用于通用对话场景)
3. **引入 Turn 概念** (对话轮次,连接 Message 和 Session)

### 2.2 数据模型

#### Conversation (增强版)

```python
class Conversation(Base):
    """
    对话模型 - 支持多轮交互

    新增字段:
    - turn_count: 对话轮次数
    - shared_memory: 跨轮次的共享记忆
    - context_summary: AI 生成的上下文摘要
    """
    __tablename__ = "conversations"

    id = Column(String(26), primary_key=True)
    workspace_id = Column(String(26), ForeignKey("workspaces.id"))
    project_id = Column(String(26), ForeignKey("projects.id"), nullable=True)  # 可选,兼容 Project 模式

    # 对话元数据
    title = Column(String(200), nullable=False)
    status = Column(Enum(ConversationStatus), default="active")
    conversation_type = Column(Enum(ConversationType), default="chat")

    # 多轮对话支持
    turn_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)

    # 上下文管理
    shared_memory = Column(JSON, nullable=True)  # 🔑 核心: 跨轮次记忆
    context_summary = Column(Text, nullable=True)  # AI 生成的摘要

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)

    # 关系
    turns = relationship("Turn", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")
```

**shared_memory 结构**:
```json
{
  "key_facts": [
    {
      "fact": "2024年全球 AI Agent 市场规模约 50 亿美元",
      "source": "turn_3",
      "confidence": 0.9,
      "timestamp": "2024-01-24T10:00:00Z"
    }
  ],
  "entities": {
    "companies": ["OpenAI", "Anthropic"],
    "products": ["ChatGPT", "Claude"]
  },
  "topics": ["AI Agent", "市场规模"],
  "user_preferences": {
    "detail_level": "high",
    "language": "zh-CN"
  },
  "context": {
    "current_research_topic": "AI Agent 市场",
    "last_findings_summary": "..."
  }
}
```

#### Turn (新增)

```python
class Turn(Base):
    """
    对话轮次 - 一次完整的交互

    Turn = User Message + Agent Execution + Assistant Response
    """
    __tablename__ = "turns"

    id = Column(String(26), primary_key=True)
    conversation_id = Column(String(26), ForeignKey("conversations.id"))
    turn_number = Column(Integer, nullable=False)  # 1, 2, 3, ...

    # 状态
    status = Column(Enum(TurnStatus), default="pending")

    # 关联
    user_message_id = Column(String(26), ForeignKey("messages.id"))
    assistant_message_id = Column(String(26), ForeignKey("messages.id"), nullable=True)
    primary_session_id = Column(String(26), ForeignKey("sessions.id"), nullable=True)

    # 统计
    tokens_used = Column(Integer, default=0)
    duration_ms = Column(Integer, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    conversation = relationship("Conversation", back_populates="turns")
    user_message = relationship("Message", foreign_keys=[user_message_id])
    assistant_message = relationship("Message", foreign_keys=[assistant_message_id])
    sessions = relationship("Session", back_populates="turn")
```

#### Session (重构)

```python
class Session(Base):
    """
    执行会话 - Agent 的执行单元

    重构:
    - 不再是顶层概念
    - 隶属于 Turn
    - 专注于执行过程
    """
    __tablename__ = "sessions"

    id = Column(String(26), primary_key=True)
    workspace_id = Column(String(26), ForeignKey("workspaces.id"))
    conversation_id = Column(String(26), ForeignKey("conversations.id"), nullable=True)  # 新增
    turn_id = Column(String(26), ForeignKey("turns.id"), nullable=True)  # 新增

    # Session 类型
    session_type = Column(Enum(SessionType), default="primary")  # primary/retry/branch
    status = Column(Enum(SessionStatus), default="pending")

    # ... 其他字段保持不变

    # 关系
    turn = relationship("Turn", back_populates="sessions")  # 新增
```

#### Message (增强)

```python
class Message(Base):
    """
    消息模型 - 增强版

    新增:
    - conversation_id: 关联到 Conversation
    - turn_id: 关联到 Turn
    """
    __tablename__ = "messages"

    id = Column(String(26), primary_key=True)
    conversation_id = Column(String(26), ForeignKey("conversations.id"), nullable=True)  # 新增
    turn_id = Column(String(26), ForeignKey("turns.id"), nullable=True)  # 新增
    session_id = Column(String(26), ForeignKey("sessions.id"))

    role = Column(Enum(MessageRole))
    content = Column(Text)

    # ... 其他字段保持不变

    # 关系
    conversation = relationship("Conversation", back_populates="messages")  # 新增
    turn = relationship("Turn")  # 新增
```

---

## 三、API 设计

### 3.1 Conversation API

#### 创建对话
```http
POST /api/v1/conversations
Content-Type: application/json

{
  "workspace_id": "01HXXX",
  "title": "研究 AI Agent 市场",  // 可选
  "conversation_type": "research",
  "initial_message": "帮我调研下 AI Agent 市场"  // 可选
}

Response:
{
  "conversation_id": "01HYYY",
  "turn_id": "01HZZZ",
  "stream_url": "/api/v1/conversations/01HYYY/turns/01HZZZ/stream"
}
```

#### 发送消息 (核心 API)
```http
POST /api/v1/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "content": "2024年全球 AI Agent 市场规模约 50 亿美元 - 这个帮我确认下"
}

Response:
{
  "turn_id": "01H123",
  "session_id": "01H456",
  "stream_url": "/api/v1/conversations/{conversation_id}/turns/{turn_id}/stream",
  "status": "pending"
}
```

#### 获取对话详情
```http
GET /api/v1/conversations/{conversation_id}

Response:
{
  "id": "01HYYY",
  "title": "研究 AI Agent 市场",
  "status": "active",
  "turn_count": 3,
  "message_count": 6,
  "turns": [
    {
      "turn_number": 1,
      "user_message": "帮我调研下 AI Agent 市场",
      "assistant_message": "好的,我来帮你调研...",
      "status": "completed",
      "created_at": "2024-01-24T10:00:00Z"
    },
    {
      "turn_number": 2,
      "user_message": "2024年全球 AI Agent 市场规模约 50 亿美元 - 这个帮我确认下",
      "assistant_message": "正在确认...",
      "status": "running",
      "created_at": "2024-01-24T10:05:00Z"
    }
  ],
  "shared_memory": { ... },
  "created_at": "2024-01-24T10:00:00Z"
}
```

#### 流式获取 Turn 事件
```http
GET /api/v1/conversations/{conversation_id}/turns/{turn_id}/stream?sse_token=xxx

Event Stream:
event: turn_started
data: {"turn_id": "01H123", "turn_number": 2}

event: agent_thinking
data: {"content": "我来确认一下这个数据..."}

event: agent_tool_call
data: {"tool_name": "web_search", "arguments": {...}}

event: turn_completed
data: {"turn_id": "01H123", "status": "completed"}
```

### 3.2 Turn API

#### 重试 Turn
```http
POST /api/v1/turns/{turn_id}/retry

Response:
{
  "new_turn_id": "01H789",
  "session_id": "01H012",
  "stream_url": "/api/v1/conversations/{conversation_id}/turns/{new_turn_id}/stream"
}
```

---

## 四、Agent 架构改造

### 4.1 Agent Worker (新增)

```python
class AgentWorker:
    """
    Agent Worker - 持续运行的 Agent 执行器

    职责:
    1. 监听 Redis 队列,接收执行任务
    2. 加载 Conversation 的完整上下文
    3. 执行 Agent 并流式发送事件
    4. 更新 shared_memory
    """

    async def execute_turn(
        self,
        conversation_id: str,
        turn_id: str,
        user_input: str,
    ):
        # 1. 加载上下文
        conversation = await self.load_conversation(conversation_id)
        message_history = await self.load_message_history(conversation_id, limit=20)
        shared_memory = conversation.shared_memory or {}

        # 2. 创建 Working Memory (从 shared_memory 恢复)
        memory = await create_working_memory(
            workspace_path=self.get_workspace_path(conversation),
            session_id=session_id,
            initial_task=user_input,
            shared_memory=shared_memory,  # 🔑 传入共享记忆
            message_history=message_history,  # 🔑 传入历史消息
        )

        # 3. 创建 Agent Context
        context = AgentContext(
            conversation_id=conversation_id,
            turn_id=turn_id,
            message_history=message_history,
        )

        # 4. 执行 Agent
        agent = DeepResearchAgent(context=context, memory=memory, ...)
        async for event in agent.run(user_input):
            await self.emit_event(turn_id, event)

        # 5. 更新 shared_memory
        updated_memory = await self.extract_and_merge_memory(
            conversation, agent
        )
        await self.save_shared_memory(conversation_id, updated_memory)
```

### 4.2 Working Memory 增强

```python
class WorkingMemory:
    """
    Working Memory - 增强版

    新增:
    - shared_memory: 跨 Turn 的共享记忆
    - message_history: 历史消息上下文
    """

    def __init__(
        self,
        workspace_path: str,
        session_id: str,
        initial_task: str,
        shared_memory: dict = None,  # 🔑 新增
        message_history: List[Message] = None,  # 🔑 新增
    ):
        self.shared_memory = shared_memory or {}
        self.message_history = message_history or []
        # ... 其他初始化

    async def get_context_for_llm(self) -> str:
        """
        获取用于 LLM 的完整上下文

        包括:
        1. 历史消息 (最近 N 条)
        2. shared_memory 中的关键信息
        3. 当前 task_plan 和 findings
        """
        context_parts = []

        # 1. 历史消息
        if self.message_history:
            context_parts.append("## 对话历史\n")
            for msg in self.message_history[-10:]:
                role = "用户" if msg.role == "user" else "助手"
                context_parts.append(f"**{role}**: {msg.content}\n")

        # 2. 共享记忆中的关键信息
        if self.shared_memory.get("key_facts"):
            context_parts.append("\n## 已知事实\n")
            for fact in self.shared_memory["key_facts"][-5:]:
                context_parts.append(f"- {fact['fact']} (来源: {fact['source']})\n")

        # 3. 当前任务计划
        task_plan = await self.read_task_plan()
        context_parts.append(f"\n## 当前任务计划\n{task_plan}\n")

        return "\n".join(context_parts)
```

---

## 五、实现计划

### Phase 1: 数据模型和迁移 (Week 1)
- [ ] 创建 Turn 模型
- [ ] 增强 Conversation 模型 (添加 shared_memory, turn_count)
- [ ] 增强 Message 模型 (添加 conversation_id, turn_id)
- [ ] 增强 Session 模型 (添加 conversation_id, turn_id)
- [ ] 编写数据库迁移脚本
- [ ] 编写单元测试

### Phase 2: API 实现 (Week 2)
- [ ] 实现 Conversation API
  - [ ] POST /conversations (创建对话)
  - [ ] POST /conversations/{id}/messages (发送消息)
  - [ ] GET /conversations/{id} (获取详情)
  - [ ] GET /conversations/{id}/turns/{turn_id}/stream (流式事件)
- [ ] 实现 Turn API
  - [ ] GET /turns/{id} (获取详情)
  - [ ] POST /turns/{id}/retry (重试)
- [ ] 编写 API 集成测试

### Phase 3: Agent 改造 (Week 3)
- [ ] 实现 AgentWorker
- [ ] 增强 WorkingMemory (支持 shared_memory 和 message_history)
- [ ] 实现 shared_memory 提取和合并逻辑
- [ ] 实现 context_summary 生成
- [ ] 编写 Agent 集成测试

### Phase 4: 前端适配 (Week 4)
- [ ] 创建 ConversationStore (Pinia)
- [ ] 实现多轮对话 UI
- [ ] 适配 SSE 事件处理
- [ ] 编写 E2E 测试

### Phase 5: 向后兼容和迁移 (Week 5)
- [ ] 实现现有 Session 到 Conversation 的迁移工具
- [ ] 保持现有 API 的向后兼容
- [ ] 编写迁移文档
- [ ] 灰度发布

---

## 六、测试策略

### 6.1 单元测试

```python
# tests/models/test_conversation.py
def test_conversation_creation():
    """测试创建对话"""
    conversation = Conversation(
        workspace_id="test_workspace",
        title="Test Conversation",
    )
    assert conversation.turn_count == 0
    assert conversation.shared_memory is None

def test_turn_creation():
    """测试创建 Turn"""
    turn = Turn(
        conversation_id="conv_123",
        turn_number=1,
        user_message_id="msg_456",
    )
    assert turn.status == TurnStatus.PENDING
```

### 6.2 集成测试

```python
# tests/api/test_conversation_api.py
async def test_send_message_creates_turn(client, db_session):
    """测试发送消息创建 Turn"""
    # 1. 创建对话
    response = await client.post("/api/v1/conversations", json={
        "workspace_id": "workspace_123",
        "initial_message": "Hello"
    })
    conversation_id = response.json()["conversation_id"]

    # 2. 发送追问消息
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Tell me more"}
    )

    # 3. 验证创建了新的 Turn
    assert response.status_code == 200
    turn_id = response.json()["turn_id"]

    # 4. 验证数据库
    turn = await db_session.get(Turn, turn_id)
    assert turn.turn_number == 2
    assert turn.conversation_id == conversation_id
```

### 6.3 E2E 测试

```typescript
// tests/e2e/multi-turn-conversation.spec.ts
test('multi-turn conversation flow', async ({ page }) => {
  // 1. 创建对话
  await page.goto('/');
  await page.fill('[data-testid="chat-input"]', '帮我调研 AI Agent 市场');
  await page.click('[data-testid="send-button"]');

  // 2. 等待响应
  await page.waitForSelector('[data-testid="assistant-message"]');

  // 3. 发送追问
  await page.fill('[data-testid="chat-input"]', '市场规模是多少?');
  await page.click('[data-testid="send-button"]');

  // 4. 验证对话历史
  const messages = await page.$$('[data-testid="message"]');
  expect(messages.length).toBeGreaterThanOrEqual(4); // 2 user + 2 assistant
});
```

---

## 七、性能优化

### 7.1 shared_memory 大小控制
- 限制 key_facts 数量 (最多 50 条)
- 定期压缩和归档旧数据
- 使用 LLM 生成 context_summary

### 7.2 消息历史加载优化
- 只加载最近 N 条消息 (默认 20)
- 使用分页加载历史消息
- 缓存常用的上下文

### 7.3 数据库查询优化
- 添加索引: conversation_id, turn_id, created_at
- 使用 eager loading 减少 N+1 查询
- 实现查询结果缓存

---

## 八、监控和可观测性

### 8.1 关键指标
- 对话轮次数分布
- 平均对话时长
- shared_memory 大小分布
- Turn 执行成功率

### 8.2 日志
```python
logger.info(
    "turn_executed",
    conversation_id=conversation_id,
    turn_id=turn_id,
    turn_number=turn.turn_number,
    tokens_used=tokens_used,
    duration_ms=duration_ms,
)
```

---

## 九、向后兼容策略

### 9.1 保留现有 API
- `/api/v1/sessions/{id}/stream` 继续工作
- 内部自动创建 Conversation 和 Turn

### 9.2 数据迁移
```python
async def migrate_session_to_conversation(session_id: str):
    """将现有 Session 迁移到 Conversation 架构"""
    session = await session_repo.get(session_id)

    # 1. 创建 Conversation
    conversation = Conversation(
        workspace_id=session.workspace_id,
        title=session.title or "Migrated Session",
        extra_data={"migrated_from_session": session_id},
    )

    # 2. 创建 Turn
    turn = Turn(
        conversation_id=conversation.id,
        turn_number=1,
        primary_session_id=session.id,
    )

    # 3. 更新 Messages
    for message in session.messages:
        message.conversation_id = conversation.id
        message.turn_id = turn.id

    await db.commit()
```

---

## 十、总结

### 核心优势
1. ✅ **真正的多轮对话**: 支持持续交互,不丢失上下文
2. ✅ **灵活的架构**: Turn 概念清晰,易于扩展
3. ✅ **向后兼容**: 不破坏现有功能
4. ✅ **可测试**: 完整的测试覆盖

### 下一步
1. Review 这个设计文档
2. 开始 Phase 1 实现
3. 迭代优化

---

**文档版本**: v1.0
**创建时间**: 2024-01-24
**作者**: Claude & User
**状态**: Draft - 待 Review
