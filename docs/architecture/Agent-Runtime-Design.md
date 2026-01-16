# Agent Runtime 核心设计

> **Version**: 1.0.0
> **Last Updated**: 2026-01-16
> **灵感来源**: OpenCode Agent Runtime 设计哲学

## 核心定位

**TokenDance 不是"通用智能体"，它是 Agent Runtime**

Agent Runtime 是一个运行时环境，让 LLM 从"思考者"变成"执行者"。

核心能力只有四个：
- **读文件** (read_file)
- **写文件** (write_file)
- **跑代码** (run_code)
- **退出信号** (exit_code)

---

## 五条铁律

### 铁律一：面向状态设计，不要描述语言设计

**核心公式**：`Agent = 状态机 + LLM决策器`

#### 1.1 显式状态机定义

```python
from enum import Enum

class AgentState(Enum):
    """Agent 状态机 - 显式定义所有状态"""
    
    # 入口状态
    INIT = "init"                    # 初始化
    PARSING_INTENT = "parsing_intent" # 解析用户意图
    
    # 核心循环状态
    PLANNING = "planning"            # 规划任务
    REASONING = "reasoning"          # 推理决策
    TOOL_CALLING = "tool_calling"    # 调用工具
    OBSERVING = "observing"          # 观察结果
    
    # 控制状态
    WAITING_CONFIRM = "waiting_confirm"  # 等待用户确认 (HITL)
    REFLECTING = "reflecting"        # 自我反思（失败后）
    REPLANNING = "replanning"        # 重新规划
    
    # 退出状态
    SUCCESS = "success"              # 任务成功
    FAILED = "failed"                # 任务失败
    CANCELLED = "cancelled"          # 用户取消
    TIMEOUT = "timeout"              # 超时退出

class StateTransition:
    """状态转移规则 - 明确的入口、出口、信号"""
    
    TRANSITIONS = {
        # 当前状态 → (触发信号, 目标状态)
        AgentState.INIT: [
            ("user_message_received", AgentState.PARSING_INTENT),
        ],
        AgentState.PARSING_INTENT: [
            ("intent_clear", AgentState.PLANNING),
            ("intent_unclear", AgentState.REASONING),  # 需要更多信息
        ],
        AgentState.PLANNING: [
            ("plan_created", AgentState.REASONING),
            ("plan_failed", AgentState.REFLECTING),
        ],
        AgentState.REASONING: [
            ("need_tool", AgentState.TOOL_CALLING),
            ("need_confirm", AgentState.WAITING_CONFIRM),
            ("task_complete", AgentState.SUCCESS),
            ("task_failed", AgentState.REFLECTING),
        ],
        AgentState.TOOL_CALLING: [
            ("tool_success", AgentState.OBSERVING),
            ("tool_failed", AgentState.OBSERVING),  # 失败也要观察
        ],
        AgentState.OBSERVING: [
            ("continue", AgentState.REASONING),
            ("exit_code_success", AgentState.SUCCESS),
            ("exit_code_failure", AgentState.REFLECTING),
        ],
        AgentState.REFLECTING: [
            ("can_retry", AgentState.REPLANNING),
            ("max_retries_reached", AgentState.FAILED),
        ],
        AgentState.REPLANNING: [
            ("new_plan_created", AgentState.REASONING),
            ("cannot_replan", AgentState.FAILED),
        ],
        AgentState.WAITING_CONFIRM: [
            ("user_confirmed", AgentState.TOOL_CALLING),
            ("user_rejected", AgentState.REASONING),
            ("user_cancelled", AgentState.CANCELLED),
        ],
    }
```

#### 1.2 状态驱动的 Agent Engine

```python
class StateBasedAgentEngine:
    """状态驱动的 Agent 引擎"""
    
    def __init__(self):
        self.state = AgentState.INIT
        self.state_history = []  # 状态轨迹
        self.context = {}
    
    async def run(self, user_message: str) -> AgentResult:
        """状态机驱动的执行循环"""
        
        self.emit_signal("user_message_received", {"message": user_message})
        
        while not self._is_terminal_state():
            # 1. 根据当前状态执行对应 Handler
            handler = self._get_state_handler(self.state)
            signal, data = await handler(self.context)
            
            # 2. 记录状态轨迹
            self.state_history.append({
                "state": self.state,
                "signal": signal,
                "timestamp": now()
            })
            
            # 3. 状态转移
            self._transition(signal)
        
        return self._build_result()
    
    def _is_terminal_state(self) -> bool:
        """判断是否到达终态"""
        return self.state in [
            AgentState.SUCCESS,
            AgentState.FAILED,
            AgentState.CANCELLED,
            AgentState.TIMEOUT
        ]
    
    def _transition(self, signal: str):
        """根据信号进行状态转移"""
        transitions = StateTransition.TRANSITIONS.get(self.state, [])
        for (trigger, target) in transitions:
            if trigger == signal:
                self.state = target
                return
        
        # 未找到匹配的转移规则
        raise InvalidStateTransition(f"No transition for {self.state} + {signal}")
```

#### 1.3 关键原则

**不要这样设计**（语言描述）：
```
❌ "Agent，你觉得这个任务应该怎么做？"
❌ "请分析用户的需求并给出建议"
❌ "如果你认为有必要，可以调用工具"
```

**应该这样设计**（状态驱动）：
```
✅ 当前状态：REASONING
   输入：用户消息 + 历史上下文 + 可用工具列表
   输出：选择一个明确的动作（TOOL_CALL / RESPOND / EXIT）
   退出信号：tool_call_requested | response_ready | exit_success
```

---

### 铁律二：成功率上限由架构决定，不是模型决定

**核心洞察**：模型是填充者，架构是天花板。

#### 2.1 架构决定的因素

```
┌─────────────────────────────────────────────────────────┐
│           成功率 = min(架构上限, 模型能力)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  架构决定的因素（天花板）：                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • 状态机设计的完备性                              │    │
│  │ • 失败恢复机制的健壮性                            │    │
│  │ • 工具接口的稳定性                                │    │
│  │ • Context 管理的效率                              │    │
│  │ • 原子化拆分的粒度                                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  模型决定的因素（填充）：                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │ • 单步推理的准确性                                │    │
│  │ • 语义理解的深度                                  │    │
│  │ • 指令遵循的一致性                                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 2.2 架构优先原则

```python
# ❌ 错误：依赖模型能力
async def execute_task(task: str):
    response = await llm.generate(f"完成这个任务：{task}")
    return response  # 成功率 = 模型单次准确率 ≈ 60-80%

# ✅ 正确：架构保障成功率
async def execute_task(task: str):
    # 1. 原子化拆分（架构保障）
    steps = await atomic_decomposer.decompose(task)  # 每步 99.9%
    
    # 2. 逐步执行 + 失败恢复（架构保障）
    for step in steps:
        for attempt in range(MAX_RETRIES):
            result = await executor.execute_step(step)
            
            if result.exit_code == 0:  # 成功信号
                break
            
            # 失败：记录 + 反思 + 重试（架构保障）
            await failure_recorder.record(step, result)
            step = await reflector.revise_step(step, result)
    
    # 成功率 = 0.999^n × 重试成功率 ≈ 95%+
    return aggregate_results(steps)
```

#### 2.3 TokenDance 的架构保障清单

| 架构机制 | 成功率贡献 | 状态 |
|---------|----------|------|
| 原子化拆分 | 60% → 99.9% | ✅ 已实现 |
| Plan Recitation | 防止 Lost-in-Middle | ✅ 已实现 |
| Keep the Failures | 避免重复错误 | ✅ 已实现 |
| External-Loop 验证 | 真实反馈驱动 | ✅ 已实现 |
| **状态机设计** | 明确状态转移 | 🆕 本次新增 |
| **exit code 驱动** | 确定性退出 | 🆕 本次新增 |

---

### 铁律三：Tool 不是插件，Tool 是世界接口

**核心洞察**：Tool 是 Agent 与现实世界交互的唯一方式。不是"插件市场"，是"现实投影仪"。

#### 3.1 核心 Tool 哲学

```
┌─────────────────────────────────────────────────────────┐
│                  Agent 的世界模型                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│                    ┌───────────┐                        │
│                    │   Agent   │                        │
│                    │  (LLM)    │                        │
│                    └─────┬─────┘                        │
│                          │                              │
│                   ┌──────┴──────┐                       │
│                   │  Tool Layer │ ← 唯一的世界接口       │
│                   │  (4个核心)   │                       │
│                   └──────┬──────┘                       │
│          ┌───────────────┼───────────────┐              │
│          │               │               │              │
│    ┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐       │
│    │ 文件系统   │  │  代码执行    │  │  退出信号  │       │
│    │ read/write│  │  run_code   │  │  exit_code│       │
│    └───────────┘  └─────────────┘  └───────────┘       │
│          │               │               │              │
│          └───────────────┴───────────────┘              │
│                          │                              │
│                   ┌──────▼──────┐                       │
│                   │  现实世界    │                       │
│                   │ (网络、磁盘) │                       │
│                   └─────────────┘                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 最小化 Tool Set

**TokenDance 核心 Tool（4+2 模型）**：

| Tool | 职责 | 世界投影 |
|------|------|---------|
| `read_file` | 读取任意内容 | 获取世界状态 |
| `write_file` | 写入任意内容 | 改变世界状态 |
| `run_code` | 执行代码/命令 | 与世界交互 |
| `exit` | 退出信号 | 标记任务完成/失败 |
| `web_search` | 搜索信息 | 扩展感知范围（可选） |
| `read_url` | 读取网页 | 扩展感知范围（可选） |

```python
class CoreTools:
    """TokenDance 核心 Tool 集合"""
    
    # 一级核心（Agent 的"四肢"）
    ESSENTIAL = [
        "read_file",   # 感知
        "write_file",  # 行动
        "run_code",    # 交互
        "exit",        # 信号
    ]
    
    # 二级扩展（Agent 的"延伸"）
    EXTENDED = [
        "web_search",  # 扩展感知
        "read_url",    # 扩展感知
    ]
    
    # 三级领域专用（按 Skill 加载）
    DOMAIN_SPECIFIC = [
        # Deep Research Skill 可能需要的
        "create_artifact",
        # PPT Skill 可能需要的
        "generate_slide",
        # ...
    ]
```

#### 3.3 Tool 是世界接口的实现

```python
class ToolAsWorldInterface:
    """Tool 作为世界接口的实现"""
    
    async def read_file(self, path: str) -> WorldState:
        """
        读文件 = 感知世界状态
        
        这不仅仅是"读取文件内容"，而是：
        - 感知项目结构
        - 获取配置信息
        - 理解当前上下文
        - 获取历史决策
        """
        content = await self.fs.read(path)
        return WorldState(
            type="file_content",
            data=content,
            path=path,
            timestamp=now()
        )
    
    async def write_file(self, path: str, content: str) -> WorldChange:
        """
        写文件 = 改变世界状态
        
        这不仅仅是"写入文件"，而是：
        - 创建新的 artifact
        - 记录决策结果
        - 保存工作进度
        - 输出最终产物
        """
        await self.fs.write(path, content)
        return WorldChange(
            type="file_written",
            path=path,
            size=len(content),
            timestamp=now()
        )
    
    async def run_code(self, code: str, language: str = "python") -> WorldFeedback:
        """
        执行代码 = 与世界交互
        
        这是 Agent 获取真实反馈的核心方式：
        - 验证假设
        - 测试实现
        - 获取运行时信息
        - 调用外部 API
        """
        result = await self.sandbox.execute(code, language)
        return WorldFeedback(
            type="execution_result",
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,  # 关键信号！
            timestamp=now()
        )
    
    async def exit(self, code: int, reason: str) -> None:
        """
        退出 = 标记任务状态
        
        exit_code 是最诚实的反馈：
        - 0: 任务成功完成
        - 1: 任务失败
        - 2: 需要用户介入
        - -1: 超时
        """
        self.state_machine.emit_signal(
            "exit_code_success" if code == 0 else "exit_code_failure",
            {"code": code, "reason": reason}
        )
```

---

### 铁律四：智能来自失败，不来自理解

**核心洞察**：exit code 是最诚实的老师。Agent 的核心设计是让失败可被观测。

#### 4.1 失败信号系统

```python
@dataclass
class FailureSignal:
    """失败信号 - 让失败可被观测"""
    
    # 信号来源
    source: str  # "tool" | "validation" | "timeout" | "user"
    
    # 失败类型
    failure_type: str  # "execution_error" | "validation_failed" | "timeout" | "rejected"
    
    # 关键：exit_code
    exit_code: int  # 0=成功, 非0=失败
    
    # 错误信息
    error_message: str
    stderr: str
    
    # 上下文
    tool_name: Optional[str]
    tool_args: Optional[dict]
    
    # 时间戳
    timestamp: datetime
    
    def is_retryable(self) -> bool:
        """判断是否可重试"""
        return self.exit_code in [1, 2]  # 可恢复的错误
    
    def get_learning(self) -> str:
        """从失败中提取教训"""
        if "timeout" in self.error_message.lower():
            return "操作超时，考虑增加超时时间或优化操作"
        if "permission" in self.error_message.lower():
            return "权限不足，检查文件/API权限"
        if "not found" in self.error_message.lower():
            return "资源不存在，检查路径/URL是否正确"
        return f"执行失败：{self.error_message}"

class FailureObserver:
    """失败观测器 - 收集和分析失败信号"""
    
    def __init__(self):
        self.failure_history: List[FailureSignal] = []
    
    async def observe(self, signal: FailureSignal):
        """观测失败信号"""
        # 1. 记录到历史
        self.failure_history.append(signal)
        
        # 2. 记录到 Context Graph（持久化学习）
        await self.context_graph.record_failure(signal)
        
        # 3. 记录到 progress.md（三文件工作法）
        await self.progress_file.append(
            f"❌ 失败 [{signal.timestamp}]: {signal.failure_type}\n"
            f"   Exit Code: {signal.exit_code}\n"
            f"   Error: {signal.error_message}\n"
            f"   Learning: {signal.get_learning()}\n"
        )
    
    async def get_similar_failures(self, current_task: str) -> List[FailureSignal]:
        """获取相似的历史失败"""
        # 从 Context Graph 检索
        return await self.context_graph.retrieve_similar_failures(
            query=current_task,
            k=5
        )
    
    async def should_abort(self) -> bool:
        """判断是否应该放弃（3-Strike Protocol）"""
        recent = self.failure_history[-3:]
        if len(recent) < 3:
            return False
        
        # 连续3次相同类型的失败
        if all(f.failure_type == recent[0].failure_type for f in recent):
            return True
        
        return False
```

#### 4.2 exit code 驱动的反馈循环

```python
class ExitCodeDrivenLoop:
    """exit code 驱动的反馈循环"""
    
    async def execute_with_feedback(
        self, 
        tool_name: str, 
        args: dict
    ) -> Tuple[Any, FailureSignal]:
        """执行工具并获取 exit code 反馈"""
        
        result = await self.tools.execute(tool_name, **args)
        
        # 构建失败信号（即使成功也记录）
        signal = FailureSignal(
            source="tool",
            failure_type="success" if result.exit_code == 0 else "execution_error",
            exit_code=result.exit_code,
            error_message=result.stderr if result.exit_code != 0 else "",
            stderr=result.stderr,
            tool_name=tool_name,
            tool_args=args,
            timestamp=now()
        )
        
        # 观测信号
        if result.exit_code != 0:
            await self.failure_observer.observe(signal)
        
        return result, signal
    
    async def learn_from_failure(
        self, 
        signal: FailureSignal
    ) -> Optional[str]:
        """从失败中学习，返回改进建议"""
        
        # 1. 获取相似历史失败
        similar = await self.failure_observer.get_similar_failures(
            f"{signal.tool_name}: {signal.error_message}"
        )
        
        # 2. 如果有相似失败，提取历史教训
        if similar:
            lessons = [f.get_learning() for f in similar]
            return f"历史教训：{'; '.join(lessons)}"
        
        # 3. 否则，基于当前失败生成建议
        return signal.get_learning()
```

#### 4.3 Keep the Failures 实现

```python
class FailureRetention:
    """Keep the Failures - 保留失败记录"""
    
    async def retain_in_context(
        self, 
        signal: FailureSignal,
        context: dict
    ) -> dict:
        """将失败保留在 Context 中"""
        
        # 失败永远不压缩
        context["failures"] = context.get("failures", [])
        context["failures"].append({
            "type": signal.failure_type,
            "exit_code": signal.exit_code,
            "error": signal.error_message,
            "learning": signal.get_learning(),
            "timestamp": signal.timestamp.isoformat()
        })
        
        return context
    
    async def build_failure_summary(self, failures: List[dict]) -> str:
        """构建失败摘要（用于 Plan Recitation）"""
        
        if not failures:
            return ""
        
        lines = ["## ⚠️ 历史失败（避免重复）"]
        for f in failures[-5:]:  # 保留最近5个
            lines.append(f"- {f['type']}: {f['learning']}")
        
        return "\n".join(lines)
```

---

### 铁律五：策略层架构

**核心洞察**：Agent 需要一个统一的策略层，协调所有组件。

#### 5.1 策略层组件

```
┌─────────────────────────────────────────────────────────────┐
│                      策略层 (Policy Layer)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  WorkState   │  │ ActionSpace  │  │FailureSignal│       │
│  │  工作状态管理 │  │ 动作空间管理  │  │ 失败信号处理 │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                 │
│                    ┌──────▼──────┐                          │
│                    │ControlLoop  │                          │
│                    │ 控制循环     │                          │
│                    └──────┬──────┘                          │
│                           │                                 │
│  ┌──────────────┐  ┌──────▼──────┐  ┌──────────────┐       │
│  │  TextToEdit  │  │ StateRouter │  │  SkillLoader │       │
│  │  文本→编辑   │  │ 状态路由     │  │  技能加载    │       │
│  └──────────────┘  └─────────────┘  └──────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 5.2 策略层实现

```python
class PolicyLayer:
    """策略层 - 统一协调所有组件"""
    
    def __init__(self):
        # 核心组件
        self.work_state = WorkStateManager()
        self.action_space = ActionSpaceManager()
        self.failure_signal = FailureSignalHandler()
        self.control_loop = ControlLoopEngine()
        
        # 辅助组件
        self.text_to_edit = TextToEditConverter()
        self.state_router = StateRouter()
        self.skill_loader = SkillLoader()
    
    async def execute(self, task: str) -> AgentResult:
        """执行任务的统一入口"""
        
        # 1. 初始化工作状态
        await self.work_state.initialize(task)
        
        # 2. 确定动作空间
        available_actions = await self.action_space.get_available_actions(
            task_type=self.work_state.task_type,
            current_state=self.work_state.current_state
        )
        
        # 3. 进入控制循环
        while not self.work_state.is_terminal():
            # 3.1 路由到对应处理器
            handler = self.state_router.route(self.work_state.current_state)
            
            # 3.2 执行处理器
            action, result = await handler.execute(
                context=self.work_state.context,
                available_actions=available_actions
            )
            
            # 3.3 处理失败信号
            if result.exit_code != 0:
                recovery = await self.failure_signal.handle(result)
                if recovery.should_abort:
                    break
                # 应用恢复策略
                await self.work_state.apply_recovery(recovery)
            
            # 3.4 更新工作状态
            await self.work_state.update(action, result)
        
        return self.work_state.get_result()


class WorkStateManager:
    """工作状态管理器"""
    
    def __init__(self):
        self.current_state = AgentState.INIT
        self.task_type: str = ""
        self.context: dict = {}
        self.history: List[dict] = []
    
    async def initialize(self, task: str):
        """初始化工作状态"""
        self.task_type = await self._classify_task(task)
        self.context = {
            "task": task,
            "started_at": now(),
            "failures": [],
            "progress": []
        }
    
    def is_terminal(self) -> bool:
        """判断是否到达终态"""
        return self.current_state in [
            AgentState.SUCCESS,
            AgentState.FAILED,
            AgentState.CANCELLED,
            AgentState.TIMEOUT
        ]


class ActionSpaceManager:
    """动作空间管理器"""
    
    def __init__(self):
        self.all_actions = {
            "read_file": ReadFileAction(),
            "write_file": WriteFileAction(),
            "run_code": RunCodeAction(),
            "exit": ExitAction(),
            "web_search": WebSearchAction(),
            "read_url": ReadUrlAction(),
        }
    
    async def get_available_actions(
        self, 
        task_type: str,
        current_state: AgentState
    ) -> List[str]:
        """根据任务类型和当前状态返回可用动作"""
        
        # 核心动作始终可用
        available = ["read_file", "write_file", "run_code", "exit"]
        
        # 根据状态添加额外动作
        if current_state == AgentState.REASONING:
            if task_type == "research":
                available.extend(["web_search", "read_url"])
        
        return available


class ControlLoopEngine:
    """控制循环引擎"""
    
    MAX_ITERATIONS = 50
    
    async def run(
        self, 
        initial_state: AgentState,
        state_handlers: Dict[AgentState, StateHandler]
    ) -> AgentResult:
        """运行控制循环"""
        
        current_state = initial_state
        iteration = 0
        
        while iteration < self.MAX_ITERATIONS:
            iteration += 1
            
            # 获取对应的处理器
            handler = state_handlers.get(current_state)
            if not handler:
                raise InvalidState(f"No handler for state: {current_state}")
            
            # 执行并获取下一个信号
            signal = await handler.execute()
            
            # 状态转移
            next_state = StateTransition.get_next_state(current_state, signal)
            
            # 检查是否到达终态
            if self._is_terminal(next_state):
                return self._build_result(next_state)
            
            current_state = next_state
        
        # 超过最大迭代
        return AgentResult(state=AgentState.TIMEOUT)
```

---

## 与现有架构的整合

### 整合清单

| 现有模块 | 整合方式 | 变更 |
|---------|---------|------|
| AgentEngine | 重构为状态机驱动 | 引入 StateBasedAgentEngine |
| Tool System | 重新定义为世界接口 | 引入 ToolAsWorldInterface |
| Reasoning | 整合到状态处理器 | ReasoningStateHandler |
| Planning | 整合到状态处理器 | PlanningStateHandler |
| Context Management | 增加失败保留 | FailureRetention |
| Memory | 增加失败检索 | FailureObserver |

### 迁移路径

1. **Phase 1**: 引入状态机定义（不改变现有行为）
2. **Phase 2**: 重构 AgentEngine 为状态驱动
3. **Phase 3**: 引入策略层抽象
4. **Phase 4**: 优化 Tool 为世界接口模型
5. **Phase 5**: 完善失败信号系统

---

## 总结

**五条铁律的核心价值**：

1. **状态设计 > 语言设计**：用状态机取代自然语言描述，确定性 > 模糊性
2. **架构 > 模型**：架构决定成功率上限，模型只是填充
3. **世界接口 > 插件市场**：最小化 Tool，最大化泛用性
4. **失败驱动 > 理解驱动**：exit code 是最诚实的反馈
5. **策略层统一协调**：WorkState + ActionSpace + FailureSignal + ControlLoop

**TokenDance 的提升**：

- 从"功能驱动"升级为"状态驱动"
- 从"隐式循环"升级为"显式状态机"
- 从"工具集合"升级为"世界接口"
- 从"保留失败"升级为"失败信号系统"
- 引入统一的"策略层"抽象
