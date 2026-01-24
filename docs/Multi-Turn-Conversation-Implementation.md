# Multi-Turn Conversation Implementation

## 概述

本文档记录了多轮对话架构的完整实现。这是一个"长期主义"的解决方案,支持真正的多轮对话,包括上下文保持、记忆管理和智能追问。

## 架构设计

### 核心概念

```
Project (项目)
  └── Conversation (对话)
        ├── Turn 1 (轮次 1)
        │     ├── User Message
        │     ├── Session (Agent 执行)
        │     └── Assistant Message
        ├── Turn 2 (轮次 2)
        │     ├── User Message
        │     ├── Session (Agent 执行)
        │     └── Assistant Message
        └── shared_memory (跨轮次共享记忆)
```

### 关键特性

1. **Turn 概念**: 每个 Turn = 用户消息 + Agent 执行 + 助手响应
2. **shared_memory**: 跨轮次的上下文保持,包括:
   - `key_facts`: 关键事实 (最多 50 条)
   - `entities`: 实体识别 (公司、产品、人物等)
   - `topics`: 讨论主题
   - `context`: 当前上下文
3. **智能记忆合并**: 自动去重、大小限制、优先级管理
4. **Agent Worker**: 后台进程持续监听执行任务
5. **SSE 流式推送**: 实时推送 Agent 执行事件

## 已完成的实现

### Phase 1: 数据模型和迁移 ✅

#### 1. Turn 模型 (`app/models/turn.py`)

```python
class Turn(Base):
    """对话轮次模型"""
    id: str  # ULID
    conversation_id: str
    turn_number: int  # 轮次编号
    status: TurnStatus  # PENDING, RUNNING, COMPLETED, FAILED
    user_message_id: str
    assistant_message_id: str
    primary_session_id: str
    tokens_used: int
    duration_ms: int
```

**关键方法**:
- `start()`: 开始执行
- `complete(assistant_message_id, tokens_used)`: 完成执行
- `fail(error_message)`: 标记失败

#### 2. Conversation 模型更新

新增字段:
- `turn_count`: 轮次计数
- `message_count`: 消息计数
- `shared_memory`: JSON 字段存储跨轮次记忆
- `last_message_at`: 最后消息时间

#### 3. 数据库迁移 (`alembic/versions/add_multi_turn_conversation.py`)

- 创建 `turns` 表
- 添加 `conversation_id`, `turn_id` 到 `messages` 和 `sessisession_type` 枚举 (primary, retry, branch, background)
- 创建必要的索引和外键

**运行迁移**:
```bash
cd backend
alembic upgrade head
```

### Phase 2: API 实现 ✅

#### 1. ConversationService (`app/services/conversation_service.py`)

**核心方法**:

```python
# 创建对话
async def create_conversation(
    workspace_id: str,
    title: str = None,
    conversation_type: ConversationType = ConversationType.CHAT,
    initial_message: str = None,
) -> tuple[Conversation, Turn | None]

# 发送消息 (核心)
async def send_message(
    conversation_id: str,
    content: str,
    parent_message_id: str = None,
) -> Turn

# 更新 shared_memory
async def update_shared_memory(
    conversation_id: str,
    memory_update: dict,
    merge: bool = True,
) -> None

# 获取消息历史
async def get_message_history(
    conversation_id: str,
    limit: int = 20,
) -> list[Message]
```

**智能记忆合并**:
- `key_facts`: 自动去重,最多保留 50 条
- `entities`: 按类型合并,去重
- `topics`: 列表合并,去重
- `context`: 直接覆盖

#### 2. Conversation API (`app/api/v1/conversations.py`)

**端点**:

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/conversations` | 创建对话 |
| POST | `/conversations/{id}/messages` | 发送消息 (核心) |
| GET | `/conversations/{id}` | 获取对话详情 |
| GET | `/conversations` | 列出对话 |
| GET | `/conversations/{id}/turns/{turn_id}/stream` | 流式获取 Turn 事件 |
| POST | `/conversations/{id}/archive` | 归档对话 |

**发送消息流程**:
```
1. 客户端 POST /conversations/{id}/messages
2. 创建 Turn 和 User Message
3. 通过 Redis pub/sub 通知 Agent Worker
4. 返回 Turn 信息和 stream_url
5. 客户端连接 stream_url 接收实时事件
```

### Phase 3: Agent Worker ✅

#### 1. AgentWorker (`app/agent/worker.py`)

**职责**:
1. 监听 Redis `agent:execute` 频道
2. 加载 Conversation 完整上下文
3. 注入 shared_memory 到 Working Memory
4. 执行 Agent 并流式发送事件
5. 提取和更新 shared_memory
6. 保存执行结果

**核心流程**:
```python
async def execute_turn(conversation_id, turn_id, user_input):
    # 1. 加载上下文
    conversation = await service.get_conversation(conversation_id)
    message_history = await service.get_message_history(conversation_id)
    shared_memory = conversation.shared_memory

    # 2. 创建 Session
    session = await session_service.create_session(...)

    # 3. 创建 Working Memory 并注入上下文
    memory = await create_working_memory(...)
    await self._inject_shared_memory(memory, shared_memory, message_history)

    # 4. 执行 Agent
    async for event in agent.run(user_input):
        await event_store.store_event(turn_id, event.type, event.data)

    # 5. 提取和更新 shared_memory
    updated_memory = await self._extract_and_merge_memory(...)
    await service.update_shared_memory(conversation_id, updated_memory)
```

**启动 Worker**:
```bash
cd backend
uv run python scripts/start_agent_worker.py
```

#### 2. SSEEventStore 增强 (`app/services/sse_event_store.py`)

新增方法:
- `get_events(turn_id)`: 获取所有事件
- `stream_events(turn_id, timeout)`: 实时流式推送事件

### Phase 4: 测试 ✅

#### 1. 单元测试 (`tests/services/test_conversation_service.py`)

15+ 测试用例,覆盖:
- 对话创建 (有/无初始消息)
- 多轮消息发送
- shared_memory 合并和去重
- key_facts 大小限制
- 消息历史排序
- 对话归档
- 并发 Turn 处理

**运行测试**:
```bash
cd backend
pytest tests/services/test_conversation_service.py -v
```

#### 2. 集成测试 (`tests/integration/test_multi_turn_conversation.py`)

测试场景:
- 完整 3 轮对话流程
- 上下文保持
- 并发 Turn 处理
- 记忆大小限制
- 对话归档工作流

**运行测试**:
```bash
cd backend
pytest tests/integration/test_multi_turn_conversation.py -v
```

#### 3. 流程测试脚本 (`scripts/test_multi_turn_flow.py`)

端到端测试脚本,验证:
- 创建对话
- 发送消息
- shared_memory 保持
- 消息历史

**运行测试**:
```bash
cd backend
uv run python scripts/test_multi_turn_flow.py
```

## 部署步骤

### 1. 运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 2. 启动 Agent Worker (后台进程)

```bash
cd backend
# 开发环境
uv run python scripts/start_agent_worker.py

# 生产环境 (使用 systemd 或 supervisor)
# 参考 docs/deployment/agent-worker-service.md
```

### 3. 重启后端服务

```bash
cd backend
# 后端会自动加载新的 API 路由
uv run uvicorn app.main:app --reload
```

### 4. 验证部署

```bash
# 检查 API 文档
open http://localhost:8000/api/v1/docs

# 测试创建对话
curl -X POST http://localhost:8000/api/v1/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "your_workspace_id",
    "title": "Test Conversation",
    "conversation_type": "chat",
    "initial_message": "Hello"
  }'
```

## 待完成的工作

### Phase 4: 前端适配 (未开始)

需要实现:

1. **ConversationStore** (Pinia)
   - 管理对话状态
   - 处理多轮消息
   - 连接 SSE 流

2. **更新 ExecutionPage.vue**
   - 使用新的 Conversation API
   - 支持多轮对话 UI
   - 显示 shared_memory

3. **适配 SSE 事件处理**
   - 连接 `/conversations/{id}/turns/{turn_id}/stream`
   - 处理 Turn 事件

### Phase 5: 集成测试和文档 (部分完成)

需要完成:

1. **数据迁移工具**
   - 将现有 Session 迁移到 Conversation
   - 保持向后兼容

2. **部署文档**
   - Agent Worker 服务配置
   - 监控和日志
   - 性能优化

3. **负载测试**
   - 并发对话测试
   - 内存使用测试
   - Redis 性能测试

## 向后兼容性

### 保留的架构

- **Project-First**: 保持不变
- **Session API**: 继续支持单轮执行
- **现有数据**: 不受影响

### 新增的独立功能

- **Conversation API**: 独立的多轮对话系统
- **Turn 模型**: 新增,不影响现有 Session
- **Agent Worker**: 独立后台进程

### 迁移策略

1. **灰度发布**: 先在部分用户中测试
2. **双写模式**: 同时支持 Session 和 Conversation
3. **逐步迁移**: 将现有 Session 逐步迁移到 Conversation

## 性能优化

### 已实现的优化

1. **shared_memory 大小限制**
   - key_facts 最多 50 条
   - 自动移除旧数据

2. **消息历史分页**
   - 默认加载最近 20 条
   - 支持 offset/limit

3. **Redis 事件存储**
   - 自动过期 (30 分钟)
   - 最多存储 500 个事件

### 建议的优化

1. **数据库索引**
   - `conversations.last_message_at`
   - `turns.conversation_id, turn_number`

2. **缓存策略**
   - 缓存 shared_memory
   - 缓存消息历史

3. **异步处理**
   - shared_memory 提取异步化
   - 批量更新优化

## 监控和日志

### 关键指标

1. **Agent Worker**
   - 执行队列长度
   - 平均执行时间
   - 失败率

2. **Conversation**
   - 活跃对话数
   - 平均轮次数
   - shared_memory 大小

3. **Redis**
   - 事件存储大小
   - pub/sub 延迟

### 日志关键字

- `agent_worker_started`
- `turn_executed_successfully`
- `shared_memory_updated`
- `sse_stream_timeout`

## 故障排查

### 常见问题

1. **Agent Worker 未启动**
   - 检查: `ps aux | grep start_agent_worker`
   - 日志: `/tmp/backend.log`

2. **Turn 一直 PENDING**
   - 检查 Redis 连接
   - 检查 Agent Worker 日志
   - 验证 pub/sub 消息

3. **shared_memory 未更新**
   - 检查 `_extract_and_merge_memory` 逻辑
   - 验证 Agent 执行完成
   - 查看数据库 `conversations.shared_memory`

4. **SSE 流断开**
   - 检查 nginx 配置 (禁用 buffering)
   - 增加 timeout 设置
   - 验证 Redis 事件存储

## 文件清单

### 新增文件

```
backend/
├── app/
│   ├── models/
│   │   └── turn.py                          # Turn 模型
│   ├── services/
│   │   └── conversation_service.py          # Conversation 业务逻辑
│   ├── api/v1/
│   │   └── conversations.py                 # Conversation API
│   └── agent/
│       └── worker.py                        # Agent Worker
├── alembic/versions/
│   └── add_multi_turn_conversation.py       # 数据库迁移
├── scripts/
│   ├── start_agent_worker.py                # Worker 启动脚本
│   └── test_multi_turn_flow.py              # 流程测试脚本
├── tests/
│   ├── services/
│   │   └── test_conversation_service.py     # 单元测试
│   └── integration/
│       └── test_multi_turn_conversation.py  # 集成测试
└── docs/
    ├── architecture/
    │   └── Multi-Turn-Conversation-Design.md  # 架构设计文档
    └── Multi-Turn-Conversation-Implementation.md  # 本文档
```

### 修改的文件

```
backend/
├── app/
│   ├── api/v1/
│   │   └── api.py                           # 注册 conversations router
│   └── services/
│       └── sse_event_store.py               # 新增 stream_events 方法
└── alembic/versions/
    └── add_multi_turn_conversation.py       # 修复 typo
```

## 下一步行动

### 立即执行

1. ✅ 运行数据库迁移
2. ✅ 启动 Agent Worker
3. ✅ 运行单元测试
4. ✅ 运行集成测试

### 短期 (1-2 周)

1. ⏳ 实现前端 ConversationStore
2. ⏳ 更新 ExecutionPage 使用新 API
3. ⏳ 端到端测试

### 中期 (1 个月)

1. ⏳ 数据迁移工具
2. ⏳ 性能优化
3. ⏳ 监控和告警

### 长期 (持续)

1. ⏳ 用户反馈收集
2. ⏳ 功能迭代
3. ⏳ 文档完善

## 总结

本次实现完成了多轮对话架构的核心功能:

✅ **数据模型**: Turn 模型、数据库迁移
✅ **业务逻辑**: ConversationService、智能记忆合并
✅ **API 接口**: 完整的 RESTful API
✅ **Agent Worker**: 后台执行进程
✅ **测试覆盖**: 单元测试、集成测试、流程测试

这是一个"长期主义"的解决方案,为未来的功能扩展打下了坚实的基础。

---

**作者**: Claude Code
**日期**: 2026-01-24
**版本**: 1.0
