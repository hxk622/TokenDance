"""
ControlLoop Engine - 控制循环引擎

实现铁律五 PolicyLayer 的第三个组件：ControlLoop

ControlLoop 管理：
- 状态机驱动的主循环
- 失败信号处理
- 迭代次数限制
- 超时控制

核心理念：
- 状态机驱动，而非简单的 while 循环
- 每个状态有明确的处理逻辑
- 失败信号触发学习和调整

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Awaitable
from enum import Enum
from datetime import datetime, timedelta
import asyncio

from app.agent.state import AgentState, Signal, StateMachine
from app.agent.failure import FailureSignal, FailureObserver


class LoopResult(Enum):
    """循环结果"""
    CONTINUE = "continue"        # 继续循环
    BREAK = "break"              # 跳出循环
    SUCCESS = "success"          # 成功完成
    FAILED = "failed"            # 失败
    TIMEOUT = "timeout"          # 超时
    MAX_ITERATIONS = "max_iterations"  # 达到最大迭代


@dataclass
class LoopConfig:
    """循环配置"""
    max_iterations: int = 20          # 最大迭代次数
    timeout_seconds: int = 600        # 超时时间（秒）
    iteration_delay_ms: int = 0       # 迭代间延迟（毫秒）
    enable_timeout: bool = True       # 是否启用超时
    enable_3_strike: bool = True      # 是否启用 3-Strike Protocol


@dataclass
class LoopContext:
    """循环上下文"""
    iteration: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    last_signal: Optional[Signal] = None
    last_result: Optional[LoopResult] = None
    
    # 累计统计
    total_tool_calls: int = 0
    total_llm_calls: int = 0
    total_failures: int = 0
    
    def elapsed_seconds(self) -> float:
        """获取已用时间（秒）"""
        return (datetime.now() - self.started_at).total_seconds()
    
    def is_timeout(self, timeout_seconds: int) -> bool:
        """检查是否超时"""
        return self.elapsed_seconds() > timeout_seconds


# 状态处理器类型
StateHandler = Callable[["ControlLoopEngine"], Awaitable[LoopResult]]


class ControlLoopEngine:
    """控制循环引擎
    
    实现铁律一和铁律五：
    - 状态机驱动的主循环
    - PolicyLayer 的核心协调器
    """
    
    def __init__(
        self,
        state_machine: StateMachine,
        failure_observer: FailureObserver,
        config: Optional[LoopConfig] = None,
    ):
        self.state_machine = state_machine
        self.failure_observer = failure_observer
        self.config = config or LoopConfig()
        
        # 循环上下文
        self.context = LoopContext()
        
        # 状态处理器注册表
        self._handlers: Dict[AgentState, StateHandler] = {}
        
        # 回调
        self._on_iteration_start: Optional[Callable] = None
        self._on_iteration_end: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
    
    def register_handler(
        self,
        state: AgentState,
        handler: StateHandler,
    ) -> None:
        """注册状态处理器"""
        self._handlers[state] = handler
    
    def set_callbacks(
        self,
        on_iteration_start: Optional[Callable] = None,
        on_iteration_end: Optional[Callable] = None,
        on_state_change: Optional[Callable] = None,
    ) -> None:
        """设置回调函数"""
        self._on_iteration_start = on_iteration_start
        self._on_iteration_end = on_iteration_end
        self._on_state_change = on_state_change
    
    async def run(self) -> LoopResult:
        """运行控制循环
        
        核心执行流程：
        1. 检查终止条件
        2. 执行状态处理器
        3. 处理结果信号
        4. 状态转移
        """
        self.context = LoopContext()
        
        while True:
            self.context.iteration += 1
            
            # 迭代开始回调
            if self._on_iteration_start:
                await self._on_iteration_start(self.context)
            
            # 检查终止条件
            result = self._check_termination_conditions()
            if result != LoopResult.CONTINUE:
                self.context.last_result = result
                return result
            
            # 获取当前状态
            current_state = self.state_machine.current_state
            
            # 检查是否是终止状态
            if self.state_machine.is_terminal():
                result = self._map_terminal_state_to_result(current_state)
                self.context.last_result = result
                return result
            
            # 执行状态处理器
            handler = self._handlers.get(current_state)
            if handler:
                try:
                    result = await handler(self)
                    
                    if result != LoopResult.CONTINUE:
                        self.context.last_result = result
                        return result
                        
                except Exception as e:
                    # 处理器异常
                    self._handle_handler_error(e)
                    
            # 迭代结束回调
            if self._on_iteration_end:
                await self._on_iteration_end(self.context)
            
            # 迭代间延迟
            if self.config.iteration_delay_ms > 0:
                await asyncio.sleep(self.config.iteration_delay_ms / 1000)
        
        return LoopResult.CONTINUE
    
    def _check_termination_conditions(self) -> LoopResult:
        """检查终止条件"""
        # 检查最大迭代次数
        if self.context.iteration > self.config.max_iterations:
            return LoopResult.MAX_ITERATIONS
        
        # 检查超时
        if self.config.enable_timeout:
            if self.context.is_timeout(self.config.timeout_seconds):
                return LoopResult.TIMEOUT
        
        return LoopResult.CONTINUE
    
    def _map_terminal_state_to_result(self, state: AgentState) -> LoopResult:
        """将终止状态映射到循环结果"""
        mapping = {
            AgentState.SUCCESS: LoopResult.SUCCESS,
            AgentState.FAILED: LoopResult.FAILED,
            AgentState.TIMEOUT: LoopResult.TIMEOUT,
            AgentState.CANCELLED: LoopResult.BREAK,
        }
        return mapping.get(state, LoopResult.BREAK)
    
    def _handle_handler_error(self, error: Exception) -> None:
        """处理状态处理器错误"""
        self.context.total_failures += 1
        
        # 创建失败信号
        signal = FailureSignal.from_tool_result(
            tool_name="state_handler",
            success=False,
            error=str(error),
        )
        
        # 观察失败
        self.failure_observer.observe(signal)
    
    def transition(self, signal: Signal) -> bool:
        """执行状态转移
        
        Returns:
            是否转移成功
        """
        old_state = self.state_machine.current_state
        
        try:
            self.state_machine.transition(signal)
            self.context.last_signal = signal
            
            # 状态变化回调
            if self._on_state_change:
                self._on_state_change(old_state, self.state_machine.current_state, signal)
            
            return True
        except Exception:
            return False
    
    def record_tool_call(self) -> None:
        """记录工具调用"""
        self.context.total_tool_calls += 1
    
    def record_llm_call(self) -> None:
        """记录 LLM 调用"""
        self.context.total_llm_calls += 1
    
    def record_failure(self) -> None:
        """记录失败"""
        self.context.total_failures += 1
    
    def should_stop_on_3_strike(self, signal: FailureSignal) -> bool:
        """检查是否应该因 3-Strike 停止"""
        if not self.config.enable_3_strike:
            return False
        
        return self.failure_observer.should_stop_retry(signal)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取循环摘要"""
        return {
            "iterations": self.context.iteration,
            "elapsed_seconds": self.context.elapsed_seconds(),
            "current_state": self.state_machine.current_state.value,
            "is_terminal": self.state_machine.is_terminal(),
            "last_signal": self.context.last_signal.value if self.context.last_signal else None,
            "last_result": self.context.last_result.value if self.context.last_result else None,
            "stats": {
                "tool_calls": self.context.total_tool_calls,
                "llm_calls": self.context.total_llm_calls,
                "failures": self.context.total_failures,
            },
            "config": {
                "max_iterations": self.config.max_iterations,
                "timeout_seconds": self.config.timeout_seconds,
                "enable_timeout": self.config.enable_timeout,
                "enable_3_strike": self.config.enable_3_strike,
            },
        }
    
    def reset(self) -> None:
        """重置循环引擎"""
        self.context = LoopContext()
        self.state_machine.reset()
        self.failure_observer.clear()


def create_control_loop(
    state_machine: StateMachine,
    failure_observer: FailureObserver,
    max_iterations: int = 20,
    timeout_seconds: int = 600,
) -> ControlLoopEngine:
    """创建控制循环引擎"""
    config = LoopConfig(
        max_iterations=max_iterations,
        timeout_seconds=timeout_seconds,
    )
    
    return ControlLoopEngine(
        state_machine=state_machine,
        failure_observer=failure_observer,
        config=config,
    )
