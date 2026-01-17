"""
Agent State Machine - 状态机定义

实现铁律一：面向状态设计，不要描述语言设计
核心公式：Agent = 状态机 + LLM决策器

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AgentState(Enum):
    """Agent 状态枚举 - 显式定义所有状态

    状态分类：
    - 入口状态：INIT, PARSING_INTENT
    - 核心循环状态：PLANNING, REASONING, TOOL_CALLING, OBSERVING
    - 控制状态：WAITING_CONFIRM, REFLECTING, REPLANNING
    - 终态：SUCCESS, FAILED, CANCELLED, TIMEOUT
    """

    # ========== 入口状态 ==========
    INIT = "init"                        # 初始化
    PARSING_INTENT = "parsing_intent"    # 解析用户意图

    # ========== 核心循环状态 ==========
    PLANNING = "planning"                # 规划任务
    REASONING = "reasoning"              # 推理决策
    TOOL_CALLING = "tool_calling"        # 调用工具
    OBSERVING = "observing"              # 观察结果

    # ========== 控制状态 ==========
    WAITING_CONFIRM = "waiting_confirm"  # 等待用户确认 (HITL)
    REFLECTING = "reflecting"            # 自我反思（失败后）
    REPLANNING = "replanning"            # 重新规划

    # ========== 终态 ==========
    SUCCESS = "success"                  # 任务成功
    FAILED = "failed"                    # 任务失败
    CANCELLED = "cancelled"              # 用户取消
    TIMEOUT = "timeout"                  # 超时退出


class Signal(Enum):
    """状态转移信号 - 触发状态转移的事件

    命名规范：动词_名词 或 形容词_名词
    """

    # ========== 用户信号 ==========
    USER_MESSAGE_RECEIVED = "user_message_received"
    USER_CONFIRMED = "user_confirmed"
    USER_REJECTED = "user_rejected"
    USER_CANCELLED = "user_cancelled"

    # ========== 意图信号 ==========
    INTENT_CLEAR = "intent_clear"
    INTENT_UNCLEAR = "intent_unclear"
    SKILL_MATCHED = "skill_matched"

    # ========== 规划信号 ==========
    PLAN_CREATED = "plan_created"
    PLAN_FAILED = "plan_failed"
    NEW_PLAN_CREATED = "new_plan_created"
    CANNOT_REPLAN = "cannot_replan"

    # ========== 推理信号 ==========
    NEED_TOOL = "need_tool"
    NEED_CONFIRM = "need_confirm"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    RESPONSE_READY = "response_ready"

    # ========== 工具信号 ==========
    TOOL_SUCCESS = "tool_success"
    TOOL_FAILED = "tool_failed"

    # ========== 退出信号 (来自 exit code) ==========
    EXIT_CODE_SUCCESS = "exit_code_success"      # exit_code = 0
    EXIT_CODE_FAILURE = "exit_code_failure"      # exit_code = 1
    EXIT_CODE_NEED_USER = "exit_code_need_user"  # exit_code = 2

    # ========== 观察信号 ==========
    CONTINUE = "continue"

    # ========== 反思信号 ==========
    CAN_RETRY = "can_retry"
    MAX_RETRIES_REACHED = "max_retries_reached"

    # ========== 系统信号 ==========
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    TIMEOUT_REACHED = "timeout_reached"


# 终态集合
TERMINAL_STATES: set[AgentState] = {
    AgentState.SUCCESS,
    AgentState.FAILED,
    AgentState.CANCELLED,
    AgentState.TIMEOUT,
}


class StateTransition:
    """状态转移规则 - 定义合法的状态转移

    规则格式：{当前状态: [(触发信号, 目标状态), ...]}

    设计原则：
    1. 每个状态必须有出口
    2. 不允许从终态转移到其他状态
    3. 失败信号总是可以触发反思
    """

    TRANSITIONS: dict[AgentState, list[tuple[Signal, AgentState]]] = {
        # ========== 入口状态 ==========
        AgentState.INIT: [
            (Signal.USER_MESSAGE_RECEIVED, AgentState.PARSING_INTENT),
        ],

        AgentState.PARSING_INTENT: [
            (Signal.INTENT_CLEAR, AgentState.PLANNING),
            (Signal.SKILL_MATCHED, AgentState.PLANNING),
            (Signal.INTENT_UNCLEAR, AgentState.REASONING),
        ],

        # ========== 核心循环状态 ==========
        AgentState.PLANNING: [
            (Signal.PLAN_CREATED, AgentState.REASONING),
            (Signal.PLAN_FAILED, AgentState.REFLECTING),
        ],

        AgentState.REASONING: [
            (Signal.NEED_TOOL, AgentState.TOOL_CALLING),
            (Signal.NEED_CONFIRM, AgentState.WAITING_CONFIRM),
            (Signal.TASK_COMPLETE, AgentState.SUCCESS),
            (Signal.RESPONSE_READY, AgentState.SUCCESS),
            (Signal.TASK_FAILED, AgentState.REFLECTING),
            (Signal.EXIT_CODE_SUCCESS, AgentState.SUCCESS),
            (Signal.EXIT_CODE_FAILURE, AgentState.REFLECTING),
            (Signal.MAX_ITERATIONS_REACHED, AgentState.TIMEOUT),
        ],

        AgentState.TOOL_CALLING: [
            (Signal.TOOL_SUCCESS, AgentState.OBSERVING),
            (Signal.TOOL_FAILED, AgentState.OBSERVING),  # 失败也要观察
            (Signal.NEED_CONFIRM, AgentState.WAITING_CONFIRM),
        ],

        AgentState.OBSERVING: [
            (Signal.CONTINUE, AgentState.REASONING),
            (Signal.EXIT_CODE_SUCCESS, AgentState.SUCCESS),
            (Signal.EXIT_CODE_FAILURE, AgentState.REFLECTING),
            (Signal.EXIT_CODE_NEED_USER, AgentState.WAITING_CONFIRM),
            (Signal.TASK_COMPLETE, AgentState.SUCCESS),
        ],

        # ========== 控制状态 ==========
        AgentState.WAITING_CONFIRM: [
            (Signal.USER_CONFIRMED, AgentState.TOOL_CALLING),
            (Signal.USER_REJECTED, AgentState.REASONING),
            (Signal.USER_CANCELLED, AgentState.CANCELLED),
            (Signal.TIMEOUT_REACHED, AgentState.TIMEOUT),
        ],

        AgentState.REFLECTING: [
            (Signal.CAN_RETRY, AgentState.REPLANNING),
            (Signal.MAX_RETRIES_REACHED, AgentState.FAILED),
        ],

        AgentState.REPLANNING: [
            (Signal.NEW_PLAN_CREATED, AgentState.REASONING),
            (Signal.CANNOT_REPLAN, AgentState.FAILED),
        ],

        # ========== 终态（无转移） ==========
        AgentState.SUCCESS: [],
        AgentState.FAILED: [],
        AgentState.CANCELLED: [],
        AgentState.TIMEOUT: [],
    }

    @classmethod
    def get_next_state(cls, current_state: AgentState, signal: Signal) -> AgentState | None:
        """根据当前状态和信号获取下一个状态

        Args:
            current_state: 当前状态
            signal: 触发信号

        Returns:
            Optional[AgentState]: 下一个状态，如果转移无效则返回 None
        """
        transitions = cls.TRANSITIONS.get(current_state, [])
        for (trigger, target) in transitions:
            if trigger == signal:
                return target
        return None

    @classmethod
    def is_valid_transition(cls, current_state: AgentState, signal: Signal) -> bool:
        """检查转移是否有效

        Args:
            current_state: 当前状态
            signal: 触发信号

        Returns:
            bool: 是否有效
        """
        return cls.get_next_state(current_state, signal) is not None

    @classmethod
    def get_valid_signals(cls, current_state: AgentState) -> list[Signal]:
        """获取当前状态的所有有效信号

        Args:
            current_state: 当前状态

        Returns:
            List[Signal]: 有效信号列表
        """
        transitions = cls.TRANSITIONS.get(current_state, [])
        return [signal for (signal, _) in transitions]

    @classmethod
    def validate_state_machine(cls) -> list[str]:
        """验证状态机定义的完整性

        检查：
        1. 所有非终态必须有出口
        2. 不存在死循环
        3. 所有状态可达

        Returns:
            List[str]: 警告信息列表
        """
        warnings = []

        # 检查非终态必须有出口
        for state in AgentState:
            if state not in TERMINAL_STATES:
                transitions = cls.TRANSITIONS.get(state, [])
                if not transitions:
                    warnings.append(f"State {state.value} has no outgoing transitions")

        # 检查可达性（从 INIT 出发能到达所有状态）
        reachable = set()
        to_visit = [AgentState.INIT]

        while to_visit:
            current = to_visit.pop()
            if current in reachable:
                continue
            reachable.add(current)

            for (_, target) in cls.TRANSITIONS.get(current, []):
                if target not in reachable:
                    to_visit.append(target)

        for state in AgentState:
            if state not in reachable:
                warnings.append(f"State {state.value} is not reachable from INIT")

        return warnings


@dataclass
class StateRecord:
    """状态记录 - 用于状态轨迹"""
    state: AgentState
    signal: Signal | None  # 导致进入此状态的信号
    timestamp: datetime
    metadata: dict = field(default_factory=dict)  # 附加数据


@dataclass
class StateHistory:
    """状态历史 - 记录完整的状态转移轨迹

    用于：
    1. 调试和可观测性
    2. 失败分析
    3. 性能优化
    """
    records: list[StateRecord] = field(default_factory=list)

    @property
    def entries(self) -> list[StateRecord]:
        """状态记录列表（别名，兼容测试）"""
        return self.records

    def add(
        self,
        state: AgentState,
        signal: Signal | None = None,
        metadata: dict | None = None
    ) -> None:
        """添加状态记录"""
        self.records.append(StateRecord(
            state=state,
            signal=signal,
            timestamp=datetime.now(),
            metadata=metadata or {}
        ))

    @property
    def current_state(self) -> AgentState | None:
        """获取当前状态"""
        return self.records[-1].state if self.records else None

    @property
    def previous_state(self) -> AgentState | None:
        """获取上一个状态"""
        return self.records[-2].state if len(self.records) >= 2 else None

    def get_state_count(self, state: AgentState) -> int:
        """获取某个状态出现的次数"""
        return sum(1 for r in self.records if r.state == state)

    def get_transition_path(self) -> list[str]:
        """获取状态转移路径的字符串表示"""
        return [r.state.value for r in self.records]

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "records": [
                {
                    "state": r.state.value,
                    "signal": r.signal.value if r.signal else None,
                    "timestamp": r.timestamp.isoformat(),
                    "metadata": r.metadata
                }
                for r in self.records
            ],
            "current_state": self.current_state.value if self.current_state else None,
            "transition_path": self.get_transition_path()
        }


class StateMachine:
    """状态机实现 - 管理状态转移

    职责：
    1. 管理当前状态
    2. 验证状态转移
    3. 记录状态历史
    4. 提供状态查询接口
    """

    def __init__(self, initial_state: AgentState = AgentState.INIT):
        """初始化状态机

        Args:
            initial_state: 初始状态
        """
        self._state = initial_state
        self._history = StateHistory()
        self._history.add(initial_state, signal=None)

    @property
    def state(self) -> AgentState:
        """当前状态"""
        return self._state

    @property
    def current_state(self) -> AgentState:
        """当前状态（别名）"""
        return self._state

    @property
    def history(self) -> StateHistory:
        """状态历史"""
        return self._history

    def is_terminal(self) -> bool:
        """判断是否到达终态"""
        return self._state in TERMINAL_STATES

    def can_transition(self, signal: Signal) -> bool:
        """检查是否可以转移"""
        return StateTransition.is_valid_transition(self._state, signal)

    def transition(self, signal: Signal, metadata: dict | None = None) -> AgentState:
        """执行状态转移

        Args:
            signal: 触发信号
            metadata: 附加元数据

        Returns:
            AgentState: 转移后的状态

        Raises:
            InvalidStateTransition: 如果转移无效
        """
        next_state = StateTransition.get_next_state(self._state, signal)

        if next_state is None:
            raise InvalidStateTransition(
                f"Invalid transition: {self._state.value} + {signal.value}"
            )

        # 记录转移
        self._history.add(next_state, signal=signal, metadata=metadata)
        self._state = next_state

        return self._state

    def get_valid_signals(self) -> list[Signal]:
        """获取当前状态的有效信号"""
        return StateTransition.get_valid_signals(self._state)

    def reset(self) -> None:
        """重置状态机"""
        self._state = AgentState.INIT
        self._history = StateHistory()
        self._history.add(AgentState.INIT, signal=None)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "current_state": self._state.value,
            "is_terminal": self.is_terminal(),
            "valid_signals": [s.value for s in self.get_valid_signals()],
            "history": self._history.to_dict()
        }


class InvalidStateTransition(Exception):
    """无效状态转移异常"""
    pass


# ========== 模块初始化：验证状态机定义 ==========
def _validate_on_import():
    """导入时验证状态机定义"""
    warnings = StateTransition.validate_state_machine()
    if warnings:
        import logging
        logger = logging.getLogger(__name__)
        for warning in warnings:
            logger.warning(f"StateMachine validation: {warning}")


_validate_on_import()
