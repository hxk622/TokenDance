# Agent Engine 低层设计 (LLD)

> Version: 1.0.0 | Phase 2
> Last Updated: 2026-01-12

## 1. 概述

Agent Engine 是 TokenDance 的核心推理引擎，负责：
- Agent 决策循环
- 思考链（Chain of Thought）
- 工具调用编排
- Plan Recitation（目标背诵）
- HITL（Human-in-the-Loop）确认

## 2. 架构设计

### 2.1 模块结构

```
backend/app/agent/
├── __init__.py
├── base.py                 # Agent 抽象基类
├── types.py               # Agent 核心类型定义
├── context.py             # Context 管理
├── plan.py                # Plan Recitation 实现
├── tools/
│   ├── __init__.py
│   ├── base.py            # Tool 基类
│   ├── registry.py        # Tool 注册表
│   ├── builtin/           # 内置工具
│   │   ├── web_search.py
│   │   ├── read_url.py
│   │   ├── file_ops.py
│   │   └── code_execute.py
│   └── schema.py          # Tool Schema 定义
├── agents/
│   ├── __init__.py
│   ├── basic.py           # BasicAgent - 简单对话
│   ├── code.py            # CodeAgent - 代码生成
│   └── plan.py            # PlanAgent - 计划执行
└── llm/
    ├── __init__.py
    ├── base.py            # LLM 客户端基类
    ├── anthropic.py       # Claude API
    └── gemini.py          # Gemini API
```

### 2.2 核心类关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      AgentContext                           │
│  - session: Session                                         │
│  - messages: List[Message]                                  │
│  - plan: Plan (TODO list)                                   │
│  - kv_cache: Dict[str, Any]                                 │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                      BaseAgent                              │
│  + run(user_input) -> AsyncGenerator[SSEEvent]              │
│  + step() -> AgentAction                                    │
│  + think(question) -> str                                   │
│  + call_tool(tool_name, args) -> ToolResult                 │
│  + should_continue() -> bool                                │
└─────────────────────────────────────────────────────────────┘
                           ▲
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  BasicAgent   │  │  CodeAgent    │  │  PlanAgent    │
└───────────────┘  └───────────────┘  └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      ToolRegistry                           │
│  + register(tool: BaseTool)                                 │
│  + get(name: str) -> BaseTool                               │
│  + list_available() -> List[ToolSchema]                     │
└─────────────────────────────────────────────────────────────┘
                           ▲
                           │
                  ┌────────┴────────┐
                  │                 │
          ┌───────────────┐  ┌───────────────┐
          │   BaseTool    │  │  ToolSchema   │
          │  + execute()  │  │  (Pydantic)   │
          └───────────────┘  └───────────────┘
```

## 3. 核心类设计

### 3.1 AgentContext

**职责**: 封装 Agent 运行时上下文

```python
@dataclass
class AgentContext:
    """Agent 运行时上下文"""
    session_id: str
    user_id: str
    workspace_id: str
    
    # 消息历史
    messages: List[Message]
    
    # Plan Recitation
    plan: Optional[Plan] = None
    
    # KV Cache（Session 级别）
    kv_cache: Dict[str, Any] = field(default_factory=dict)
    
    # 工具调用历史
    tool_calls: List[ToolCall] = field(default_factory=list)
    
    # Token 使用统计
    tokens_used: int = 0
    max_tokens: int = 200_000  # Claude 3.5 Sonnet
    
    # 执行状态
    iteration: int = 0
    max_iterations: int = 50
```

### 3.2 BaseAgent

**职责**: Agent 抽象基类，定义决策循环框架

```python
class BaseAgent(ABC):
    """Agent 抽象基类"""
    
    def __init__(
        self,
        context: AgentContext,
        llm: BaseLLM,
        tools: ToolRegistry,
        db: AsyncSession
    ):
        self.context = context
        self.llm = llm
        self.tools = tools
        self.db = db
        self.stopped = False
        
    async def run(self, user_input: str) -> AsyncGenerator[SSEEvent, None]:
        """主运行循环 - SSE 流式输出"""
        # 1. 添加用户消息
        await self._add_user_message(user_input)
        
        while self._should_continue():
            try:
                # 2. Plan Recitation - 追加 TODO 到 context 末尾
                await self._recite_plan()
                
                # 3. 思考 (Thinking)
                async for thinking_event in self._think():
                    yield thinking_event
                
                # 4. 决策 - 选择工具或回答
                action = await self._decide()
                
                if action.type == ActionType.TOOL_CALL:
                    # 5a. 工具调用
                    async for tool_event in self._execute_tool(action):
                        yield tool_event
                        
                elif action.type == ActionType.ANSWER:
                    # 5b. 最终回答
                    async for content_event in self._stream_answer(action):
                        yield content_event
                    break
                    
                elif action.type == ActionType.CONFIRM_REQUIRED:
                    # 5c. HITL 确认
                    yield SSEEvent(type='confirm_required', data=action.data)
                    await self._wait_for_confirmation()
                    
            except Exception as e:
                yield SSEEvent(type='error', data={'message': str(e)})
                break
        
        # 6. 完成
        yield SSEEvent(
            type='done',
            data={
                'status': 'completed',
                'message_id': self.context.current_message_id,
                'tokens_used': self.context.tokens_used
            }
        )
    
    @abstractmethod
    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - 子类实现"""
        pass
    
    @abstractmethod
    async def _decide(self) -> AgentAction:
        """决策 - 子类实现"""
        pass
    
    async def _recite_plan(self) -> None:
        """Plan Recitation - 追加当前 TODO 到 context"""
        if not self.context.plan or not self.context.plan.todos:
            return
        
        # 构造 Plan Recitation 文本
        recitation = "## Current Plan (TODO List)\n"
        for i, todo in enumerate(self.context.plan.todos, 1):
            status = "✅" if todo.completed else "⬜"
            recitation += f"{status} {i}. {todo.title}\n"
        
        # 追加到 context（不存入数据库，仅用于当前轮）
        self.context.append_system_message(recitation)
    
    async def _execute_tool(
        self, 
        action: AgentAction
    ) -> AsyncGenerator[SSEEvent, None]:
        """执行工具调用"""
        tool_name = action.tool_name
        tool_args = action.tool_args
        tool_id = str(uuid.uuid4())
        
        # 1. 发送 tool_call 事件
        yield SSEEvent(
            type='tool_call',
            data={
                'id': tool_id,
                'name': tool_name,
                'args': tool_args,
                'status': 'pending'
            }
        )
        
        try:
            # 2. 获取工具
            tool = self.tools.get(tool_name)
            
            # 3. HITL 检查
            if tool.requires_confirmation:
                yield SSEEvent(
                    type='confirm_required',
                    data={
                        'action_id': tool_id,
                        'tool': tool_name,
                        'args': tool_args,
                        'description': tool.description
                    }
                )
                # 等待用户确认
                confirmed = await self._wait_for_confirmation(tool_id)
                if not confirmed:
                    yield SSEEvent(
                        type='tool_result',
                        data={
                            'id': tool_id,
                            'status': 'cancelled',
                            'result': 'User cancelled the operation'
                        }
                    )
                    return
            
            # 4. 执行工具
            yield SSEEvent(
                type='tool_call',
                data={'id': tool_id, 'status': 'running'}
            )
            
            result = await tool.execute(**tool_args)
            
            # 5. 返回结果
            yield SSEEvent(
                type='tool_result',
                data={
                    'id': tool_id,
                    'status': 'success',
                    'result': result
                }
            )
            
            # 6. 追加到 context
            await self._add_tool_call(tool_name, tool_args, result)
            
        except Exception as e:
            yield SSEEvent(
                type='tool_result',
                data={
                    'id': tool_id,
                    'status': 'error',
                    'error': str(e)
                }
            )
            # 保留错误在 context（Keep the Failures）
            await self._add_tool_call(tool_name, tool_args, error=str(e))
    
    def _should_continue(self) -> bool:
        """判断是否继续执行"""
        if self.stopped:
            return False
        if self.context.iteration >= self.context.max_iterations:
            return False
        if self.context.tokens_used >= self.context.max_tokens * 0.95:
            return False
        return True
    
    async def stop(self):
        """停止执行"""
        self.stopped = True
```

### 3.3 思考链（Chain of Thought）

**设计原则**:
1. **可见思考** - 所有思考过程通过 SSE `thinking` 事件发送
2. **追加式** - 思考内容追加到 Message.thinking 字段
3. **结构化** - 使用 XML 标签标记思考类型

```python
async def _think(self) -> AsyncGenerator[SSEEvent, None]:
    """思考过程 - 流式输出"""
    # 1. 构造思考 Prompt
    thinking_prompt = self._build_thinking_prompt()
    
    # 2. 调用 LLM - 流式输出
    thinking_content = ""
    async for chunk in self.llm.stream(thinking_prompt):
        thinking_content += chunk
        
        # 实时发送 thinking 事件
        yield SSEEvent(
            type='thinking',
            data={'content': chunk}
        )
    
    # 3. 保存思考内容
    self.context.current_thinking = thinking_content
    
def _build_thinking_prompt(self) -> str:
    """构造思考 Prompt"""
    return f"""
<REASONING>
Analyze the current situation step by step:

1. What is the user asking for?
2. What information do I have?
3. What information do I need?
4. What tools should I use?
5. What is my next action?

Think carefully and show your reasoning.
</REASONING>
"""
```

### 3.4 Plan Recitation

**设计**:
- Plan 存储在 `Session.todo_list` (JSONB)
- 每轮循环追加到 context 末尾
- 防止 "Lost-in-the-Middle"

```python
@dataclass
class Plan:
    """Plan 数据结构"""
    todos: List[TodoItem]
    created_at: datetime
    updated_at: datetime
    
@dataclass
class TodoItem:
    id: str
    title: str
    description: str
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
class PlanManager:
    """Plan 管理器"""
    
    async def create_plan(
        self,
        session_id: str,
        todos: List[Dict[str, str]]
    ) -> Plan:
        """创建 Plan"""
        plan = Plan(
            todos=[
                TodoItem(
                    id=str(uuid.uuid4()),
                    title=todo['title'],
                    description=todo.get('description', '')
                )
                for todo in todos
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 保存到 Session
        await self._save_to_session(session_id, plan)
        return plan
    
    async def mark_complete(self, session_id: str, todo_id: str):
        """标记 TODO 完成"""
        plan = await self._load_from_session(session_id)
        for todo in plan.todos:
            if todo.id == todo_id:
                todo.completed = True
                break
        
        plan.updated_at = datetime.now()
        await self._save_to_session(session_id, plan)
```

## 4. Tool 系统设计

### 4.1 Tool 基类

```python
class BaseTool(ABC):
    """工具基类"""
    
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    requires_confirmation: bool = False  # 是否需要 HITL 确认
    
    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具 - 返回文本结果"""
        pass
    
    def to_schema(self) -> ToolSchema:
        """转换为工具 Schema（给 LLM）"""
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=self.parameters
        )
```

### 4.2 Tool Registry

```python
class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """注册工具"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        """获取工具"""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found")
        return self._tools[name]
    
    def list_available(self) -> List[ToolSchema]:
        """列出所有可用工具 Schema"""
        return [tool.to_schema() for tool in self._tools.values()]
    
    def to_llm_format(self) -> List[Dict[str, Any]]:
        """转换为 LLM 工具定义格式（Claude Tool Use）"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            }
            for tool in self._tools.values()
        ]
```

### 4.3 内置工具示例

```python
class WebSearchTool(BaseTool):
    """Web 搜索工具"""
    
    name = "web_search"
    description = "Search the web for information"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    async def execute(self, query: str, num_results: int = 5) -> str:
        """执行搜索"""
        # TODO: 调用 Tavily API
        results = await self._search_tavily(query, num_results)
        
        # 格式化返回
        output = f"Search results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['title']}\n"
            output += f"   {result['url']}\n"
            output += f"   {result['snippet']}\n\n"
        
        return output
```

## 5. LLM 接口设计

### 5.1 BaseLLM

```python
class BaseLLM(ABC):
    """LLM 客户端基类"""
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> LLMResponse:
        """完整调用"""
        pass
    
    @abstractmethod
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> AsyncGenerator[str, None]:
        """流式调用"""
        pass
```

### 5.2 Claude 实现

```python
class ClaudeLLM(BaseLLM):
    """Claude API 客户端"""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def stream(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> AsyncGenerator[str, None]:
        """流式调用 Claude"""
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=self._format_messages(messages),
            tools=tools or []
        ) as stream:
            async for text in stream.text_stream:
                yield text
```

## 6. SSE 事件定义

与前端 `api/chat.ts` 保持一致：

```typescript
type SSEEventType =
  | 'thinking'          // Agent 思考过程
  | 'tool_call'         // 工具调用（pending/running）
  | 'tool_result'       // 工具结果（success/error/cancelled）
  | 'content'           // 最终回答内容
  | 'confirm_required'  // HITL 确认请求
  | 'done'              // 完成
  | 'error'             // 错误
```

## 7. 执行流程示例

### 用户: "帮我搜索 Python async 最佳实践"

```
1. User Message 追加到 context
   └─> role: user, content: "帮我搜索 Python async 最佳实践"

2. Plan Recitation (如果存在)
   └─> 追加当前 TODO list

3. Thinking (SSE: thinking)
   └─> "用户想了解 Python async 编程最佳实践..."
   └─> "我应该使用 web_search 工具搜索相关信息"

4. Decide -> TOOL_CALL
   └─> tool: web_search, args: {query: "Python async best practices"}

5. Execute Tool
   └─> SSE: tool_call (pending)
   └─> SSE: tool_call (running)
   └─> 调用 Tavily API
   └─> SSE: tool_result (success)
   └─> 追加到 context

6. Thinking (SSE: thinking)
   └─> "搜索结果显示了5篇文章..."
   └─> "我现在可以总结最佳实践"

7. Decide -> ANSWER
   └─> SSE: content (流式输出最终回答)

8. Done
   └─> SSE: done {status: 'completed', tokens_used: 1234}
```

## 8. 下一步实现顺序

1. ✅ 创建此 LLD 文档
2. ⬜ 实现 Tool 基础系统（base.py, registry.py）
3. ⬜ 实现 LLM 客户端（anthropic.py）
4. ⬜ 实现 Agent 基类（base.py, context.py）
5. ⬜ 实现 BasicAgent（简单对话，无工具）
6. ⬜ 集成 SSE streaming 到 `/api/v1/chat/{session_id}/message`
7. ⬜ 实现内置工具（web_search, read_url）
8. ⬜ 实现 Plan Recitation
9. ⬜ 端到端测试

---

*Generated: 2026-01-12*
