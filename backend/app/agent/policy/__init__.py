"""
PolicyLayer - 策略层

实现铁律五：PolicyLayer 架构

PolicyLayer = WorkState + ActionSpace + FailureSignal + ControlLoop

核心职责：
1. WorkState - 管理工作状态
2. ActionSpace - 管理动作空间（Action Space Pruning）
3. FailureSignal - 失败信号系统（来自 failure 模块）
4. ControlLoop - 控制循环引擎

使用方式：
    from app.agent.policy import PolicyLayer

    # 创建策略层
    policy = PolicyLayer(session_id, workspace_id)

    # 配置动作空间
    policy.action_space.set_allowed_tools(["read_file", "write_file"])

    # 运行控制循环
    result = await policy.run()

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass
from typing import Any

# FailureSignal (从 failure 模块导入)
from app.agent.failure import (
    ExitCode,
    FailureObserver,
    FailureSignal,
    FailureSummary,
)

# StateMachine (从 state 模块导入)
from app.agent.state import (
    AgentState,
    Signal,
    StateMachine,
)

# ActionSpace
from .action_space import (
    CORE_TOOL_NAMES,
    EXTENDED_TOOL_NAMES,
    ActionConstraint,
    ActionSpaceManager,
    ActionType,
    ToolPermission,
    create_default_action_space,
)

# ControlLoop
from .control_loop import (
    ControlLoopEngine,
    LoopConfig,
    LoopContext,
    LoopResult,
    StateHandler,
    create_control_loop,
)

# WorkState
from .work_state import (
    ProgressCheckpoint,
    ResourceUsage,
    TaskContext,
    TaskPhase,
    WorkState,
    WorkStateManager,
)


@dataclass
class PolicyLayerConfig:
    """策略层配置"""
    max_iterations: int = 20
    timeout_seconds: int = 600
    enable_3_strike: bool = True
    enable_action_space_pruning: bool = True


class PolicyLayer:
    """策略层 - 统一协调器

    实现铁律五：PolicyLayer = WorkState + ActionSpace + FailureSignal + ControlLoop

    这是 Agent 运行时的核心协调层，负责：
    1. 状态管理（WorkState）
    2. 动作控制（ActionSpace）
    3. 失败学习（FailureSignal）
    4. 循环控制（ControlLoop）
    """

    def __init__(
        self,
        session_id: str,
        workspace_id: str,
        config: PolicyLayerConfig | None = None,
    ):
        self.session_id = session_id
        self.workspace_id = workspace_id
        self.config = config or PolicyLayerConfig()

        # 初始化四大组件

        # 1. WorkState
        self.work_state = WorkStateManager(
            session_id=session_id,
            workspace_id=workspace_id,
        )

        # 2. ActionSpace
        self.action_space = create_default_action_space()

        # 3. FailureSignal (Observer)
        self.failure_observer = FailureObserver()

        # 4. StateMachine
        self.state_machine = StateMachine(initial_state=AgentState.INIT)

        # 5. ControlLoop
        self.control_loop = ControlLoopEngine(
            state_machine=self.state_machine,
            failure_observer=self.failure_observer,
            config=LoopConfig(
                max_iterations=self.config.max_iterations,
                timeout_seconds=self.config.timeout_seconds,
                enable_3_strike=self.config.enable_3_strike,
            ),
        )

    def start_task(self, task_id: str, description: str) -> None:
        """开始任务"""
        self.work_state.start_task(task_id, description)

    def set_goal(self, goal: str) -> None:
        """设置当前目标"""
        self.work_state.set_goal(goal)

    def set_allowed_tools(self, tools: list[str]) -> None:
        """设置允许的工具（Action Space Pruning）"""
        if self.config.enable_action_space_pruning:
            self.action_space.set_allowed_tools(tools)

    def can_use_tool(self, tool_name: str) -> bool:
        """检查是否可以使用工具"""
        return self.action_space.can_use_tool(tool_name)

    def observe_failure(self, signal: FailureSignal) -> dict[str, Any]:
        """观察失败信号"""
        return self.failure_observer.observe(signal)

    def should_stop_on_failure(self, signal: FailureSignal) -> bool:
        """检查是否应该因失败停止"""
        return self.control_loop.should_stop_on_3_strike(signal)

    def transition(self, signal: Signal) -> bool:
        """执行状态转移"""
        return self.control_loop.transition(signal)

    def get_current_state(self) -> AgentState:
        """获取当前状态"""
        return self.state_machine.current_state

    def is_terminal(self) -> bool:
        """检查是否是终止状态"""
        return self.state_machine.is_terminal()

    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """添加 token 使用量"""
        self.work_state.add_tokens(input_tokens, output_tokens)
        self.control_loop.record_llm_call()

    def add_tool_call(self) -> None:
        """添加工具调用"""
        self.work_state.add_tool_call()
        self.control_loop.record_tool_call()

    def complete_task(self) -> None:
        """完成任务"""
        self.work_state.complete_task()

    def fail_task(self, reason: str = "") -> None:
        """任务失败"""
        self.work_state.fail_task(reason)

    def get_summary(self) -> dict[str, Any]:
        """获取策略层摘要"""
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "work_state": self.work_state.get_summary(),
            "action_space": self.action_space.get_pruning_summary(),
            "failure_stats": self.failure_observer.get_statistics(),
            "control_loop": self.control_loop.get_summary(),
            "state_machine": {
                "current_state": self.state_machine.current_state.value,
                "is_terminal": self.state_machine.is_terminal(),
            },
        }

    def reset(self) -> None:
        """重置策略层"""
        self.work_state.reset()
        self.action_space.reset()
        self.failure_observer.clear()
        self.state_machine.reset()
        self.control_loop.reset()


# 便捷函数
def create_policy_layer(
    session_id: str,
    workspace_id: str,
    max_iterations: int = 20,
    timeout_seconds: int = 600,
) -> PolicyLayer:
    """创建策略层"""
    config = PolicyLayerConfig(
        max_iterations=max_iterations,
        timeout_seconds=timeout_seconds,
    )
    return PolicyLayer(
        session_id=session_id,
        workspace_id=workspace_id,
        config=config,
    )


__all__ = [
    # PolicyLayer
    "PolicyLayer",
    "PolicyLayerConfig",
    "create_policy_layer",
    # WorkState
    "WorkState",
    "WorkStateManager",
    "TaskPhase",
    "TaskContext",
    "ResourceUsage",
    "ProgressCheckpoint",
    # ActionSpace
    "ActionSpaceManager",
    "ActionType",
    "ActionConstraint",
    "ToolPermission",
    "CORE_TOOL_NAMES",
    "EXTENDED_TOOL_NAMES",
    "create_default_action_space",
    # ControlLoop
    "ControlLoopEngine",
    "LoopResult",
    "LoopConfig",
    "LoopContext",
    "StateHandler",
    "create_control_loop",
    # Re-exported
    "FailureSignal",
    "FailureObserver",
    "FailureSummary",
    "ExitCode",
    "AgentState",
    "Signal",
    "StateMachine",
]
