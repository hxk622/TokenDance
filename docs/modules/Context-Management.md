# Context管理机制设计文档

> **核心更新 (2026-01-10)**: 集成多租户、文件系统指针、压缩策略
> - **多租户架构**：Organization → Team → Workspace 三层隔离
> - **Dual Context Streams**：Working Memory（KV-Cache）+ File System（持久化）
> - **智能压缩**：文件系统指针 + 自动换入换出
> - 参考：[FileSystem.md](./FileSystem.md), [Context-Compression.md](./Context-Compression.md), [Multi-Tenancy.md](../architecture/Multi-Tenancy.md)

## 1. 核心问题

**长对话场景下的Context爆炸**：
- 100轮对话 × 1000 tokens/轮 = 100K tokens
- 成本：$300/次请求
- 延迟：10-15秒
- 超过模型窗口限制

**工程矛盾**：
- Agent需要历史信息做决策
- Context越长，成本越高，性能越差
- 简单截断会丢失关键信息

## 2. 设计原则

### 2.1 分层存储原则（Dual Context Streams + 压缩）

基于 Manus 的 "todo.md 是灵魂" 理念，TokenDance 采用 **双重分身 + 智能压缩** 架构：

```
┌─────────────────────────────────────────────────────────────────┐
│  五层记忆架构（多租户 + 压缩）                               │
│                                                                  │
│  Layer 0: FileSystem (长期记忆) 🆕                             │
│  - 无限容量（数 TB），持久化存储                              │
│  - 按 Org/Team/Workspace 物理隔离                             │
│  - 原始数据完整保留，可恢复                                   │
│                         ↓ 压缩指针                              │
│  Layer 1: Global Static Prefix (全局静态前缀)                 │
│  - 工具定义、FSM 状态、核心规则                              │
│  - 每个 Org 独立，内部 Agent 共享（Copy-on-Write）         │
│                         ↓ 挂载                                 │
│  Layer 2: Skill Cache (领域专家知识)                        │
│  - Skill L2 指令                                              │
│  - Team 级别共享，懒加载 + 复用                              │
│                         ↓ 追加                                │
│  Layer 3: Session Cache (会话上下文)                        │
│  - 用户指令、Agent 推理、工具返回                           │
│  - 热数据保留在 KV-Cache，冷数据换出到 FileSystem        │
│  - 压缩指针：摘要 + 路径 + 检索提示                          │
└─────────────────────────────────────────────────────────────────┘

参考详细设计：
- [KV-Cache-Advanced.md](./KV-Cache-Advanced.md) - 层次化缓存架构
- [Context-Compression.md](./Context-Compression.md) - 压缩策略和文件系统指针
```

### 2.2 按需加载原则
```python
# 不预加载所有数据，Agent按需读取

# ❌ 错误做法
context = load_all_messages()  # 加载100K tokens

# ✅ 正确做法
context = {
    "summary": load_summary(),        # 500 tokens
    "recent_messages": load_recent(10),  # 10K tokens
    "file_index": list_workspace_files()  # Agent需要时再读取
}
```

### 2.3 增量更新原则
```python
# 避免每次重新摘要全部历史

# ❌ 低效做法
def update_summary():
    all_messages = load_all()  # 重新处理100轮
    return summarize(all_messages)

# ✅ 高效做法
def update_summary_incremental():
    old_summary = load_latest_summary()
    new_messages = load_unsummarized()
    return merge_summary(old_summary, new_messages)  # 只处理增量
```

## 3. 架构设计

### 3.1 数据模型

```sql
-- 消息表（支持摘要标记）
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    role TEXT NOT NULL,  -- user/assistant/system/tool
    content TEXT,
    
    -- 工具调用元数据
    tool_name TEXT,
    tool_args JSONB,
    tool_result JSONB,
    
    -- 摘要标记
    is_summarized BOOLEAN DEFAULT FALSE,
    summary_id UUID REFERENCES conversation_summaries(id),
    
    -- Token计数
    token_count INT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_messages_session (session_id, created_at),
    INDEX idx_messages_unsummarized (session_id, is_summarized)
);

-- 对话摘要表
CREATE TABLE conversation_summaries (
    id UUID PRIMARY KEY,
    session_id UUID NOT NULL,
    
    -- 摘要覆盖的消息范围
    start_message_id UUID NOT NULL,
    end_message_id UUID NOT NULL,
    message_count INT,
    
    -- 摘要内容（结构化 + 文本）
    summary JSONB NOT NULL,  -- 结构化数据
    summary_text TEXT NOT NULL,  -- 给Agent看的版本
    
    -- 压缩效果
    original_token_count INT,
    summary_token_count INT,
    compression_ratio FLOAT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_summaries_session (session_id, created_at DESC)
);

-- 摘要结构（JSONB格式）
{
  "user_goal": "搭建TokenDance平台",
  "completed_tasks": [
    "创建了7个设计文档",
    "实现了Skill三级加载机制"
  ],
  "key_decisions": [
    {
      "decision": "使用Plan Recitation防止Lost-in-the-Middle",
      "reason": "TODO列表放末尾，避免被遗忘",
      "timestamp": "2026-01-08T10:00:00Z"
    }
  ],
  "current_status": "正在设计Memory模块",
  "pending_todos": ["创建Memory-Design.md"],
  "important_context": {
    "tech_stack": "Vue3 + FastAPI + PostgreSQL",
    "workspace_path": "/Users/x/TokenDance",
    "key_files": ["docs/architecture/HLD.md"]
  }
}
```

### 3.2 核心组件

```python
# packages/core/context/manager.py

from typing import List, Optional
from pydantic import BaseModel

class ConversationSummary(BaseModel):
    """对话摘要结构"""
    user_goal: str
    completed_tasks: List[str]
    key_decisions: List[dict]
    current_status: str
    pending_todos: List[str]
    important_context: dict

class ConversationManager:
    """对话Context管理器（多租户 + 压缩）"""
    
    # 配置参数
    SUMMARY_THRESHOLD = 50000      # 超过此tokens触发摘要
    KEEP_RECENT_TURNS = 10         # 保留最近N轮完整消息
    INCREMENTAL_BATCH_SIZE = 5     # 增量更新批次大小
    COMPRESSION_THRESHOLD = 10240  # > 10KB 自动压缩到文件系统 🆕
    
    def __init__(
        self,
        session_id: str,
        workspace_id: str,      # 🆕 Workspace ID
        org_id: str,            # 🆕 Organization ID
        team_id: str,           # 🆕 Team ID
        db,
        llm,
        file_manager,
        compressor,             # 🆕 ContextCompressor 实例
        decompressor            # 🆕 ContextDecompressor 实例
    ):
        self.session_id = session_id
        self.workspace_id = workspace_id
        self.org_id = org_id
        self.team_id = team_id
        self.db = db
        self.llm = llm
        self.file_manager = file_manager  # FileManager 实例
        self.compressor = compressor
        self.decompressor = decompressor
    
    async def get_context_for_agent(self) -> dict:
        """
        获取Agent的上下文（核心接口）
        
        实现 Dual Context Streams：
        1. Working Memory: 数据库摘要 + 最近消息（精简）
        2. File System: workspace/ 文件（完整）
        
        返回结构：
        {
            "working_memory": {        # Stream 1: 数据库
                "summary": Optional[str],
                "messages": List[Message]
            },
            "file_system": {           # Stream 2: 文件系统（参考 FileSystem.md）
                "memory": str,         # workspace/context/memory.md
                "learnings": str,      # workspace/context/learnings.md
                "rules": str,          # workspace/context/rules.md
                "active_tasks": List   # workspace/tasks/*.md (in_progress)
            }
        }
        """
        # 1. 获取所有消息
        messages = await self.db.get_messages(self.session_id)
        total_tokens = sum(m.token_count for m in messages)
        
        # 2. 判断是否需要摘要
        if total_tokens < self.SUMMARY_THRESHOLD:
            return {
                "summary": None,
                "messages": messages,
                "workspace": await self.fs.get_file_index(self.session_id)
            }
        
        # 3. 处理摘要
        await self._ensure_summary_updated(messages)
        
        # 4. 构建Context
        return await self._build_context_with_summary()
    
    async def _ensure_summary_updated(self, messages: List):
        """确保摘要是最新的"""
        summary = await self.db.get_latest_summary(self.session_id)
        
        if not summary:
            # 首次摘要
            await self._create_initial_summary(messages)
        else:
            # 检查是否需要增量更新
            unsummarized_count = len([m for m in messages if not m.is_summarized])
            
            if unsummarized_count >= self.INCREMENTAL_BATCH_SIZE:
                await self._update_summary_incremental(messages)
    
    async def _create_initial_summary(self, messages: List):
        """首次创建摘要"""
        # 计算要摘要的范围（保留最近N轮）
        cutoff_index = max(0, len(messages) - self.KEEP_RECENT_TURNS)
        to_summarize = messages[:cutoff_index]
        
        if not to_summarize:
            return
        
        # 调用LLM生成摘要
        summary = await self._generate_summary(to_summarize)
        
        # 保存到数据库
        await self.db.create_summary(
            session_id=self.session_id,
            start_message_id=to_summarize[0].id,
            end_message_id=to_summarize[-1].id,
            message_count=len(to_summarize),
            summary=summary.model_dump(),
            summary_text=self._format_summary_text(summary),
            original_token_count=sum(m.token_count for m in to_summarize),
            summary_token_count=await self.llm.count_tokens(
                self._format_summary_text(summary)
            )
        )
        
        # 标记消息为已摘要
        for msg in to_summarize:
            await self.db.mark_message_summarized(msg.id)
    
    async def _update_summary_incremental(self, messages: List):
        """增量更新摘要"""
        existing = await self.db.get_latest_summary(self.session_id)
        new_messages = [m for m in messages if not m.is_summarized]
        
        # 计算要新增摘要的范围
        cutoff = max(0, len(new_messages) - self.KEEP_RECENT_TURNS)
        to_add = new_messages[:cutoff]
        
        if not to_add:
            return
        
        # 增量摘要：基于旧摘要 + 新消息
        old_summary = ConversationSummary(**existing.summary)
        updated_summary = await self._merge_summary(old_summary, to_add)
        
        # 保存新摘要
        await self.db.create_summary(
            session_id=self.session_id,
            start_message_id=existing.start_message_id,  # 起点不变
            end_message_id=to_add[-1].id,
            message_count=existing.message_count + len(to_add),
            summary=updated_summary.model_dump(),
            summary_text=self._format_summary_text(updated_summary),
            original_token_count=existing.original_token_count + 
                                sum(m.token_count for m in to_add),
            summary_token_count=await self.llm.count_tokens(
                self._format_summary_text(updated_summary)
            )
        )
        
        # 标记消息
        for msg in to_add:
            await self.db.mark_message_summarized(msg.id)
    
    async def _generate_summary(self, messages: List) -> ConversationSummary:
        """生成摘要（调用LLM）"""
        prompt = f"""
请将以下对话压缩为结构化摘要。保留核心信息，丢弃冗余细节。

对话内容：
{self._format_messages_for_llm(messages)}

要求：
1. 提取用户的核心目标（user_goal）
2. 列出已完成的关键任务（completed_tasks），按时间顺序
3. 记录重要决策及原因（key_decisions），包含timestamp
4. 总结当前状态（current_status），一句话
5. 提取待办事项（pending_todos）
6. 保留重要上下文（important_context）：
   - 技术栈
   - 文件路径
   - 配置信息
   - 外部依赖

返回JSON格式，严格遵循ConversationSummary结构。
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,  # 低温度保证稳定
            response_format="json"
        )
        
        return ConversationSummary.model_validate_json(response.content)
    
    async def _merge_summary(
        self, 
        old: ConversationSummary,
        new_messages: List
    ) -> ConversationSummary:
        """增量合并摘要"""
        prompt = f"""
现有摘要：
{old.model_dump_json(indent=2)}

新增对话：
{self._format_messages_for_llm(new_messages)}

请更新摘要：
1. 合并新完成的任务到completed_tasks
2. 添加新的关键决策到key_decisions
3. 更新current_status为最新状态
4. 更新pending_todos（移除已完成，添加新增）
5. 合并important_context

保持摘要简洁，移除已过时的信息。
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            response_format="json"
        )
        
        return ConversationSummary.model_validate_json(response.content)
    
    async def _build_context_with_summary(self) -> dict:
        """构建带摘要的Context"""
        summary = await self.db.get_latest_summary(self.session_id)
        recent = await self.db.get_messages(
            self.session_id,
            is_summarized=False
        )
        
        return {
            "summary": summary.summary_text if summary else None,
            "messages": recent,
            "workspace": await self.fs.get_file_index(self.session_id)
        }
    
    def _format_summary_text(self, summary: ConversationSummary) -> str:
        """将结构化摘要转为给Agent看的文本"""
        return f"""# CONVERSATION SUMMARY

This is a summary of prior messages in this conversation. The user still sees the full conversation.

## Overview
{summary.user_goal}

## Progress
**Current Status**: {summary.current_status}

**Completed Tasks**:
{chr(10).join(f'- {task}' for task in summary.completed_tasks)}

**Key Decisions**:
{chr(10).join(f'- {d["decision"]}: {d["reason"]}' for d in summary.key_decisions)}

**Pending TODOs**:
{chr(10).join(f'- {todo}' for todo in summary.pending_todos)}

**Important Context**:
{chr(10).join(f'- {k}: {v}' for k, v in summary.important_context.items())}
"""
    
    def _format_messages_for_llm(self, messages: List) -> str:
        """格式化消息用于摘要生成"""
        lines = []
        for msg in messages:
            if msg.role == "tool":
                # 工具结果只保留摘要
                lines.append(f"[Tool: {msg.tool_name}] {msg.tool_result.get('summary', '')[:200]}")
            else:
                # 用户/助手消息截断
                content = msg.content[:1000] if len(msg.content) > 1000 else msg.content
                lines.append(f"[{msg.role}] {content}")
        
        return "\n\n".join(lines)
```

### 3.3 与文件系统集成

```python
# packages/core/context/dual_streams.py

class DualContextStreams:
    """双重分身：Working Memory + File System"""
    
    def __init__(self, conversation_mgr, filesystem):
        self.conversation_mgr = conversation_mgr
        self.fs = filesystem
    
    async def get_full_context(self) -> dict:
        """
        获取完整Context
        
        结构：
        - Hot: 摘要 + 最近消息（内存）
        - Cold: 文件系统索引（磁盘）
        """
        # Working Memory（摘要 + 最近消息）
        memory_context = await self.conversation_mgr.get_context_for_agent()
        
        # File System（全量数据索引）
        file_index = {
            "task": await self.fs.list_dir("task"),
            "research": await self.fs.list_dir("research"),
            "code": await self.fs.list_dir("code"),
            "output": await self.fs.list_dir("output")
        }
        
        return {
            **memory_context,
            "filesystem": {
                "index": file_index,
                "tools": ["read_file", "write_file", "list_files"]
            }
        }
    
    async def store_large_result(
        self, 
        tool_name: str, 
        result: dict
    ) -> dict:
        """
        存储大型工具结果
        
        策略：
        - 小结果（<5KB）：直接放入Message
        - 大结果（>5KB）：存文件系统，Message中只放摘要
        """
        result_size = len(str(result))
        
        if result_size < 5000:
            # 小结果：直接返回
            return {
                "type": "inline",
                "data": result,
                "summary": f"{tool_name} completed"
            }
        
        # 大结果：存文件
        filename = f"temp/{tool_name}_{uuid.uuid4().hex[:8]}.json"
        await self.fs.write(filename, json.dumps(result, indent=2))
        
        # 生成摘要
        summary = await self._summarize_large_result(tool_name, result)
        
        return {
            "type": "file_reference",
            "file_path": filename,
            "summary": summary,
            "size_bytes": result_size
        }
    
    async def _summarize_large_result(self, tool_name: str, result: dict) -> str:
        """摘要大型结果"""
        # 根据工具类型生成摘要
        if tool_name == "web_search":
            return f"搜索返回 {len(result.get('results', []))} 条结果，已存储至文件"
        elif tool_name == "read_url":
            return f"网页内容 {len(result.get('content', ''))} 字符，已存储至文件"
        else:
            return f"{tool_name} 结果已存储至文件"
```

## 4. 与其他模块的集成

### 4.1 与Memory模块集成
```python
# Context管理器为Memory提供数据源

class MemoryManager:
    def __init__(self, context_manager: ConversationManager):
        self.context = context_manager
    
    async def extract_facts(self):
        """从摘要中提取事实"""
        summary = await self.context.db.get_latest_summary(...)
        facts = self._extract_from_summary(summary.summary)
        return facts
```

### 4.2 与Planning模块集成
```python
# Plan Recitation依赖Context管理

class PlanningManager:
    async def get_current_plan(self):
        """从文件系统读取计划"""
        plan = await self.fs.read("task/plan.md")
        return plan
    
    async def update_context_with_plan(self, context: dict):
        """将计划追加到Context末尾（Plan Recitation）"""
        plan = await self.get_current_plan()
        context["system_suffix"] = f"\n\n# CURRENT PLAN\n{plan}"
```

### 4.3 与Context Graph集成
```python
# Context Graph记录摘要操作

class ContextGraphRecorder:
    async def record_summary_creation(self, summary_id: str):
        """记录摘要创建事件"""
        await self.graph.add_node(
            type="context_operation",
            action="create_summary",
            summary_id=summary_id,
            timestamp=now()
        )
```

## 5. KV-Cache 优化策略 🆕 ⭐

> **核心目标**：KV-Cache 命中率 > 90%，性能提升 7x

### 5.1 问题：为什么需要 KV-Cache 优化？

**KV-Cache 的本质**：
Transformer 模型在生成时，对于已经计算过的 Token，其 Key/Value 可以被缓存和复用，节省 ~90% 的计算量。

**传统 Agent 的问题**：
```python
# ❌ 错误做法：每轮重构 context
Round 1: [System] + [User] + "规划任务"                      # 3000 tokens 计算
Round 2: [System] + [User] + [Plan] + "执行步骤1，可用工具：{A}" # 3200 tokens 重新计算
Round 3: [System] + [User] + [Plan] + [Result1] + "执行步骤2，可用工具：{B}" # 3400 tokens 重新计算

# 问题：
# 1. 每轮的工具描述都变化 → 前缀不稳定
# 2. KV-Cache 命中率 ~0% → 每轮都要重复计算所有 Token
# 3. 10 轮对话总计算量：~35,000 tokens
```

**Manus 的优化方案**：
```python
# ✅ 正确做法：Append-Only + Stable Prefix
Initial:  [System] + [All Tools] + [User]                        # 2000 tokens 计算（KV-Cache 生成）
Round 1:  ... + <|REASONING|>我需要...<|TOOL_CALL|>tool_a(...)  # 新增 500 tokens
Round 2:  ... + <|TOOL_RESULT|>...<|REASONING|>...<|TOOL_CALL|>... # 新增 200 tokens（前面 2500 tokens 缓存命中）
Round 3:  ... + <|TOOL_RESULT|>...<|REASONING|>...<|FINAL_ANSWER|> # 新增 300 tokens（前面 2700 tokens 缓存命中）

# 效果：
# 1. System Prompt + 工具定义永不变化 → KV-Cache 100% 命中
# 2. 每轮只计算新增的 Token → 性能提升 7x
# 3. 10 轮对话总计算量：~5,000 tokens
```

---

### 5.2 优化原则

#### 原则 1：固定 System Prompt

```python
# ❌ 错误：动态注入时间戳
SYSTEM_PROMPT = f"""
你是 TokenDance Agent。
当前时间：{datetime.now()}  # 每次都变！
可用技能：{current_skills}      # 动态变化！
"""

# ✅ 正确：固定不变
SYSTEM_PROMPT = """
<|SYSTEM|>
你是 TokenDance，一个通用 AI Agent 平台。

# 核心能力
你可以通过以下工具完成任务：
<|TOOLS|>
{ALL_TOOL_DEFINITIONS}  # 所有工具一次性加载，永不变化

# 行为规范
1. 使用 <|REASONING|> 标记你的思考过程
2. 使用 <|TOOL_CALL|> 调用工具
3. 接收 <|TOOL_RESULT|> 后继续推理
4. 完成后使用 <|FINAL_ANSWER|> 输出结果
"""

# 关键：
# - System Prompt 在 session 开始时生成，之后永不变化
# - 时间戳等动态信息放在 User Message 或 Tool Output 中
```

---

#### 原则 2：Append-Only Context Growth

```python
class AgentSession:
    def __init__(self, user_query: str):
        # 初始化固定 context
        self.context = [
            {"role": "system", "content": FIXED_SYSTEM_PROMPT},  # 固定
            {"role": "user", "content": user_query}              # 固定
        ]
        self.kv_cache_valid = True
    
    async def execute_step(self):
        # 1. 生成推理（纯追加）
        reasoning = await self.llm.generate(
            messages=self.context,
            stop=["<|TOOL_CALL|>", "<|FINAL_ANSWER|>"],
            use_cache=self.kv_cache_valid  # 使用 KV-Cache
        )
        
        # 追加推理
        self.context.append({
            "role": "assistant",
            "content": f"<|REASONING|>{reasoning}"
        })
        
        # 2. 如果需要调用工具
        if "<|TOOL_CALL|>" in reasoning:
            tool_call = self.parse_tool_call(reasoning)
            result = await self.execute_tool(tool_call)
            
            # 追加工具结果
            self.context.append({
                "role": "tool",
                "content": f"<|TOOL_RESULT|>{result}"
            })
        
        # 关键：KV-Cache 始终有效，因为我们只追加
        self.kv_cache_valid = True

# 效果：
# - Round 1: 计算 2000 tokens (System + User)
# - Round 2: 计算 500 tokens (新增部分)，前 2000 tokens 缓存命中
# - Round 3: 计算 300 tokens (新增部分)，前 2500 tokens 缓存命中
```

---

#### 原则 3：结构化标记 (Structured Tags)

```python
# TokenDance 的标记系统

class StructuredTags:
    SYSTEM = "<|SYSTEM|>"              # System Prompt
    TOOLS = "<|TOOLS|>"                # 工具定义
    USER = "<|USER|>"                  # 用户输入
    REASONING = "<|REASONING|>"        # Agent 思考
    TOOL_CALL = "<|TOOL_CALL|>"        # 工具调用
    TOOL_RESULT = "<|TOOL_RESULT|>"    # 工具结果
    FINAL_ANSWER = "<|FINAL_ANSWER|>"  # 最终答案

# 示例：一个完整的对话流
"""
<|SYSTEM|>
你是 TokenDance Agent。

<|TOOLS|>
1. web_search(query: str) -> List[dict]
2. read_url(url: str) -> str
3. summarize(text: str) -> str

<|USER|>
帮我研究 AI 发展趋势。

<|REASONING|>
我应该先搜索相关信息...

<|TOOL_CALL|>
web_search(query="AI 发展趋势 2026")

<|TOOL_RESULT|>
[搜索结果]

<|REASONING|>
现在开始总结...

<|FINAL_ANSWER|>
根据我的研究...
"""

# 好处：
# 1. 明确语义边界，模型理解更准确
# 2. 便于系统解析和缓存管理
# 3. 支持部分掩码（下一条）
```

---

#### 原则 4：工具定义掩码 (Tool Definition Masking)

```python
# 问题：所有工具定义都加载，但某些步骤只需要部分工具
# 解决：掩码技术（Attention Mask）

class ToolMasking:
    def __init__(self):
        # 工具定义在固定位置
        self.tool_positions = {
            "web_search": (100, 150),    # Token 100-150
            "read_url": (151, 200),
            "code_execute": (201, 250),
            "summarize": (251, 300)
        }
    
    def generate_attention_mask(self, available_tools: List[str]) -> List[int]:
        """生成 Attention Mask，让模型"看不见"不可用的工具"""
        total_tokens = 2000
        mask = [1] * total_tokens  # 默认全部可见
        
        for tool, (start, end) in self.tool_positions.items():
            if tool not in available_tools:
                # 掩码该工具的定义（但不删除）
                mask[start:end] = [0] * (end - start)
        
        return mask

# 效果：
# - 工具定义永远在 context 中 → KV-Cache 100% 命中
# - 通过 Attention Mask 控制可见性 → 模型行为正确
# - 无需重新加载 context → 性能最优
```

---

### 5.3 实现示例

```python
# backend/app/context/kv_cache_optimizer.py

def build_prompt_for_llm(context: dict) -> List[dict]:
    """构建 KV-Cache 友好的 Prompt"""
    messages = []
    
    # 1. 固定 System Prompt（KV-Cache 100% 命中）
    messages.append({
        "role": "system",
        "content": FIXED_SYSTEM_PROMPT  # 永不变化
    })
    
    # 2. 摘要（变化频率低，大部分时候 KV-Cache 命中）
    if context.get("summary"):
        messages.append({
            "role": "system",
            "content": context["summary"]
        })
    
    # 3. 最近消息（Append-Only，KV-Cache 增量更新）
    messages.extend(context["messages"])
    
    return messages
```

---

### 5.4 性能对比

**传统方案**（每轮重构 context）：
```
Round 1: 生成 Plan          → 3000 tokens 计算
Round 2: 调用 web_search    → 3200 tokens 重新计算
Round 3: 调用 read_url      → 3400 tokens 重新计算
...
Round 10: 生成报告       → 5000 tokens 重新计算

总计算量：~35,000 tokens
```

**优化后方案**（Append-Only + Stable Prefix）：
```
Initial: 固定 System Prompt → 2000 tokens 计算（KV-Cache 生成）
Round 1: 生成 Plan          → 新增 500 tokens 计算
Round 2: 调用 web_search    → 新增 200 tokens 计算（前面 2500 tokens 缓存命中）
Round 3: 调用 read_url      → 新增 300 tokens 计算（前面 2700 tokens 缓存命中）
...
Round 10: 生成报告       → 新增 800 tokens 计算（前面 4200 tokens 缓存命中）

总计算量：~5,000 tokens
```

**性能提升**：~7x faster（仅计算新增 Token）

---

## 6. 性能优化（其他）

### 5.2 异步摘要生成
```python
# 摘要生成不阻塞用户消息

@router.post("/messages")
async def send_message(message: str, background_tasks: BackgroundTasks):
    # 1. 立即返回响应
    response = await agent.run(message)
    
    # 2. 后台触发摘要更新
    background_tasks.add_task(
        conversation_mgr.check_and_update_summary
    )
    
    return response
```

### 5.3 摘要缓存
```python
# 摘要文本缓存到Redis

class ConversationManager:
    async def get_summary_text(self, session_id: str) -> Optional[str]:
        # 先查缓存
        cached = await self.redis.get(f"summary:{session_id}")
        if cached:
            return cached
        
        # 缓存未命中，查数据库
        summary = await self.db.get_latest_summary(session_id)
        if summary:
            await self.redis.setex(
                f"summary:{session_id}",
                3600,  # 1小时过期
                summary.summary_text
            )
            return summary.summary_text
        
        return None
```

## 6. 监控指标

```python
# packages/core/context/metrics.py

class ContextMetrics:
    """Context管理指标"""
    
    async def collect(self, session_id: str) -> dict:
        return {
            # 压缩效果
            "total_messages": await self.db.count_messages(session_id),
            "summarized_messages": await self.db.count_summarized(session_id),
            "compression_ratio": await self._calc_compression_ratio(session_id),
            
            # Context大小
            "current_context_tokens": await self._calc_current_tokens(session_id),
            "would_be_tokens_without_summary": await self._calc_full_tokens(session_id),
            "tokens_saved": ...,
            
            # 成本节省
            "cost_saved_usd": ...,
            
            # 摘要质量
            "summary_count": await self.db.count_summaries(session_id),
            "avg_summary_latency_ms": ...
        }
```

## 7. 未来扩展

### 7.1 多模态摘要
```python
# 支持图片、代码等多模态内容的摘要

class MultimodalSummarizer:
    async def summarize(self, messages: List):
        text_summary = await self._summarize_text(messages)
        image_summary = await self._summarize_images(messages)
        code_summary = await self._summarize_code(messages)
        
        return {
            "text": text_summary,
            "images": image_summary,
            "code": code_summary
        }
```

### 7.2 语义检索增强
```python
# 结合向量检索，精准定位历史信息

class SemanticContextRetrieval:
    async def retrieve_relevant_history(self, query: str, k: int = 5):
        """根据当前问题检索相关历史"""
        embedding = await self.embed(query)
        
        # 从历史消息中检索
        relevant = await self.vector_db.search(
            collection="message_embeddings",
            query_vector=embedding,
            limit=k
        )
        
        return relevant
```

### 7.3 分支对话管理
```python
# 支持对话分支（用户回退到历史某点）

class ConversationBranch:
    async def create_branch(self, from_message_id: str):
        """从某条消息创建新分支"""
        new_session_id = uuid.uuid4()
        
        # 复制历史到新分支
        await self.db.copy_messages_until(
            from_message_id,
            new_session_id
        )
        
        return new_session_id
```

## 8. 总结

**核心价值**：
1. **成本降低90%**：50K tokens → 10K tokens
2. **延迟降低80%**：10秒 → 2秒
3. **可扩展性**：支持无限长对话
4. **信息保真**：关键信息不丢失

**关键技术**：
1. 滑动窗口 + 增量摘要
2. 结构化摘要 + 自然语言文本
3. 双重分身：Working Memory + File System
4. KV Cache友好设计

**与其他模块的关系**：
- 为Memory提供数据源
- 为Planning提供Plan Recitation支持
- 与Context Graph协同记录决策轨迹
- 所有模块的基础设施
