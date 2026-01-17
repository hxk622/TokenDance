"""
五条铁律集成测试

测试 OpenCode 五条铁律的实现：
1. 铁律一: Agent = 状态机 + LLM 决策器
2. 铁律二: 架构决定成功率上限，不是模型
3. 铁律三: 工具是世界接口，不是插件
4. 铁律四: 智能来自失败，不来自理解
5. 铁律五: PolicyLayer 架构

运行: cd backend && uv run pytest tests/test_five_rules_integration.py -v
"""

import pytest
from datetime import datetime

# 铁律一: 状态机
from app.agent.state import (
    AgentState,
    Signal,
    StateMachine,
    StateHistory,
    InvalidStateTransition,
)

# 铁律四: 失败信号
from app.agent.failure import (
    FailureSignal,
    FailureObserver,
    FailureSummary,
    FailureSource,
    FailureType,
    ExitCode,
)

# 铁律三: 工具是世界接口
from app.agent.tools.world_interface import (
    WorldInterface,
    ToolCategory,
    ToolMetadata,
    CORE_TOOLS,
    EXTENDED_TOOLS,
    validate_core_tools,
)

# 铁律三: Exit Tool
from app.agent.tools.builtin.exit_tool import (
    ExitTool,
    ExitReason,
    ExitContext,
    create_success_exit,
    create_failure_exit,
)

# 铁律五: PolicyLayer
from app.agent.policy import (
    PolicyLayer,
    PolicyLayerConfig,
    WorkState,
    WorkStateManager,
    TaskPhase,
    ActionSpaceManager,
    ControlLoopEngine,
    LoopResult,
    LoopConfig,
    create_policy_layer,
)


class TestIronRule1_StateMachine:
    """铁律一测试: Agent = 状态机 + LLM 决策器"""
    
    def test_initial_state(self):
        """测试初始状态"""
        sm = StateMachine()
        assert sm.current_state == AgentState.INIT
    
    def test_basic_transitions(self):
        """测试基本状态转移"""
        sm = StateMachine()
        
        # INIT -> PARSING_INTENT
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        assert sm.current_state == AgentState.PARSING_INTENT
        
        # PARSING_INTENT -> PLANNING
        sm.transition(Signal.INTENT_CLEAR)
        assert sm.current_state == AgentState.PLANNING
        
        # PLANNING -> REASONING
        sm.transition(Signal.PLAN_CREATED)
        assert sm.current_state == AgentState.REASONING
    
    def test_tool_calling_flow(self):
        """测试工具调用流程"""
        sm = StateMachine()
        
        # 初始流程
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        sm.transition(Signal.INTENT_CLEAR)
        sm.transition(Signal.PLAN_CREATED)
        assert sm.current_state == AgentState.REASONING
        
        # REASONING -> TOOL_CALLING
        sm.transition(Signal.NEED_TOOL)
        assert sm.current_state == AgentState.TOOL_CALLING
        
        # TOOL_CALLING -> OBSERVING
        sm.transition(Signal.TOOL_SUCCESS)
        assert sm.current_state == AgentState.OBSERVING
        
        # OBSERVING -> REASONING
        sm.transition(Signal.CONTINUE)
        assert sm.current_state == AgentState.REASONING
    
    def test_terminal_states(self):
        """测试终止状态"""
        sm = StateMachine()
        
        # 进入成功状态
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        sm.transition(Signal.INTENT_CLEAR)
        sm.transition(Signal.PLAN_CREATED)  # PLANNING -> REASONING
        sm.transition(Signal.TASK_COMPLETE)  # REASONING -> SUCCESS
        
        assert sm.current_state == AgentState.SUCCESS
        assert sm.is_terminal()
    
    def test_history_tracking(self):
        """测试历史追踪"""
        sm = StateMachine()
        
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        sm.transition(Signal.INTENT_CLEAR)
        
        # 初始状态 INIT 也被记录，所以有 3 个记录
        assert len(sm.history.entries) >= 2
        # entries[0] 是初始状态 INIT，entries[1] 是第一次转移后的状态
        assert sm.history.entries[1].state == AgentState.PARSING_INTENT
    
    def test_reset(self):
        """测试重置"""
        sm = StateMachine()
        
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        sm.transition(Signal.INTENT_CLEAR)
        
        sm.reset()
        
        assert sm.current_state == AgentState.INIT
        # 重置后会有一个初始 INIT 状态记录
        assert len(sm.history.entries) == 1
        assert sm.history.entries[0].state == AgentState.INIT


class TestIronRule3_WorldInterface:
    """铁律三测试: 工具是世界接口，不是插件"""
    
    def test_core_tools_defined(self):
        """测试核心工具定义"""
        assert "read_file" in CORE_TOOLS
        assert "write_file" in CORE_TOOLS
        assert "run_code" in CORE_TOOLS
        assert "exit" in CORE_TOOLS
    
    def test_extended_tools_defined(self):
        """测试扩展工具定义"""
        assert "web_search" in EXTENDED_TOOLS
        assert "read_url" in EXTENDED_TOOLS
    
    def test_world_interface_initialization(self):
        """测试世界接口初始化"""
        wi = WorldInterface()
        assert len(wi) == 0
    
    def test_action_space_pruning(self):
        """测试动作空间裁剪"""
        wi = WorldInterface()
        
        # 设置允许的工具
        wi.set_allowed_tools(["web_search"])
        
        # 核心工具始终可用
        available = wi.get_available_tools()
        # 由于没有注册工具，应该返回空
        assert len(available) == 0
    
    def test_tool_metadata(self):
        """测试工具元数据"""
        read_file_meta = CORE_TOOLS["read_file"]
        
        assert read_file_meta.is_essential
        assert not read_file_meta.affects_world
        assert read_file_meta.category == ToolCategory.CORE


class TestIronRule3_ExitTool:
    """铁律三测试: Exit Tool"""
    
    @pytest.mark.asyncio
    async def test_success_exit(self):
        """测试成功退出"""
        tool = ExitTool()
        result = await tool.execute(
            exit_code=0,
            message="任务完成",
            summary="创建了3个文件",
        )
        
        assert result.success
        assert tool.was_successful()
        assert tool.last_exit_context is not None
        assert tool.last_exit_context.exit_code == 0
    
    @pytest.mark.asyncio
    async def test_failure_exit(self):
        """测试失败退出"""
        tool = ExitTool()
        result = await tool.execute(
            exit_code=1,
            message="无法完成",
            failures=["网络错误"],
        )
        
        assert result.success  # exit 操作本身成功
        assert not tool.was_successful()  # 但任务失败
        assert tool.last_exit_context is not None
        assert tool.last_exit_context.exit_code == 1
    
    @pytest.mark.asyncio
    async def test_need_user_exit(self):
        """测试需要用户介入的退出"""
        tool = ExitTool()
        result = await tool.execute(
            exit_code=2,
            message="需要API密钥",
            need_user_for="提供API密钥",
        )
        
        context = tool.get_exit_context()
        assert context.exit_code == 2
        assert context.reason == ExitReason.NEED_USER
    
    def test_convenience_functions(self):
        """测试便捷函数"""
        success = create_success_exit("完成了", ["file1.txt"])
        assert success["exit_code"] == 0
        
        failure = create_failure_exit("失败了", ["错误1"])
        assert failure["exit_code"] == 1


class TestIronRule4_FailureSignal:
    """铁律四测试: 智能来自失败，不来自理解"""
    
    def test_failure_signal_creation(self):
        """测试失败信号创建"""
        signal = FailureSignal.from_tool_result(
            tool_name="web_search",
            success=False,
            error="Connection timeout",
        )
        
        assert not signal.is_success()
        assert signal.is_retryable()
        assert signal.failure_type == FailureType.TIMEOUT
    
    def test_exit_code_semantics(self):
        """测试退出码语义"""
        assert ExitCode.SUCCESS.value == 0
        assert ExitCode.FAILURE.value == 1
        assert ExitCode.NEED_USER.value == 2
        assert ExitCode.FATAL.value == 3
    
    def test_get_learning(self):
        """测试学习信息提取"""
        signal = FailureSignal(
            source=FailureSource.TOOL,
            failure_type=FailureType.TIMEOUT,
            exit_code=1,
            error_message="Operation timed out",
        )
        
        learning = signal.get_learning()
        assert "超时" in learning or "timeout" in learning.lower()
    
    def test_failure_observer(self):
        """测试失败观察者"""
        observer = FailureObserver()
        
        signal = FailureSignal.from_tool_result(
            tool_name="test_tool",
            success=False,
            error="Test error",
        )
        
        result = observer.observe(signal)
        
        assert result["recorded"]
        assert not result["trigger_3_strike"]  # 第一次不触发
    
    def test_3_strike_protocol(self):
        """测试 3-Strike Protocol"""
        observer = FailureObserver()
        
        # 制造3次相同类型的失败
        for _ in range(3):
            signal = FailureSignal(
                source=FailureSource.TOOL,
                failure_type=FailureType.TIMEOUT,
                exit_code=1,
                error_message="Timeout",
                tool_name="test_tool",
            )
            result = observer.observe(signal)
        
        # 第三次应该触发 3-Strike
        assert result["trigger_3_strike"]
    
    def test_failure_summary_for_context(self):
        """测试失败摘要（用于 Plan Recitation）"""
        observer = FailureObserver()
        
        signal = FailureSignal.from_tool_result(
            tool_name="web_search",
            success=False,
            error="Rate limited",
        )
        observer.observe(signal)
        
        summary = observer.get_failure_summary_for_context()
        
        assert "失败" in summary or "web_search" in summary


class TestIronRule5_PolicyLayer:
    """铁律五测试: PolicyLayer 架构"""
    
    def test_policy_layer_creation(self):
        """测试策略层创建"""
        policy = create_policy_layer(
            session_id="test-session",
            workspace_id="test-workspace",
        )
        
        assert policy.session_id == "test-session"
        assert policy.workspace_id == "test-workspace"
    
    def test_work_state_manager(self):
        """测试工作状态管理器"""
        manager = WorkStateManager(
            session_id="test",
            workspace_id="test",
        )
        
        manager.start_task("task-1", "测试任务")
        assert manager.get_state().phase == TaskPhase.PLANNING
        
        manager.start_execution()
        assert manager.get_state().phase == TaskPhase.EXECUTING
        
        manager.complete_task()
        assert manager.get_state().phase == TaskPhase.COMPLETED
    
    def test_action_space_manager(self):
        """测试动作空间管理器"""
        from app.agent.policy.action_space import CORE_TOOL_NAMES
        
        manager = ActionSpaceManager()
        
        # 注册工具
        for name in CORE_TOOL_NAMES:
            manager.register_tool(name, is_core=True)
        
        manager.register_tool("custom_tool", is_core=False)
        
        # 测试 Action Space Pruning
        manager.set_allowed_tools(["web_search"])
        
        # 核心工具始终可用
        assert manager.can_use_tool("read_file")
        assert manager.can_use_tool("exit")
        
        # 非核心工具被裁剪
        assert not manager.can_use_tool("custom_tool")
    
    def test_policy_layer_integration(self):
        """测试策略层集成"""
        policy = PolicyLayer(
            session_id="test",
            workspace_id="test",
        )
        
        # 开始任务
        policy.start_task("task-1", "测试任务")
        policy.set_goal("完成测试")
        
        # 添加资源使用
        policy.add_tokens(100, 50)
        policy.add_tool_call()
        
        # 获取摘要
        summary = policy.get_summary()
        
        assert "work_state" in summary
        assert "action_space" in summary
        assert "failure_stats" in summary
        assert "state_machine" in summary
    
    def test_control_loop_config(self):
        """测试控制循环配置"""
        config = LoopConfig(
            max_iterations=10,
            timeout_seconds=300,
            enable_3_strike=True,
        )
        
        assert config.max_iterations == 10
        assert config.timeout_seconds == 300
        assert config.enable_3_strike


class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建状态机
        sm = StateMachine()
        
        # 2. 创建失败观察者
        observer = FailureObserver()
        
        # 3. 模拟工作流
        
        # 用户消息 -> 解析意图
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        assert sm.current_state == AgentState.PARSING_INTENT
        
        # 意图清晰 -> 规划
        sm.transition(Signal.INTENT_CLEAR)
        assert sm.current_state == AgentState.PLANNING
        
        # 规划完成 -> 推理
        sm.transition(Signal.PLAN_CREATED)
        assert sm.current_state == AgentState.REASONING
        
        # 需要工具 -> 工具调用
        sm.transition(Signal.NEED_TOOL)
        assert sm.current_state == AgentState.TOOL_CALLING
        
        # 模拟工具失败
        signal = FailureSignal.from_tool_result(
            tool_name="web_search",
            success=False,
            error="Network error",
        )
        result = observer.observe(signal)
        
        assert result["recorded"]
        
        # 工具成功 -> 观察
        sm.transition(Signal.TOOL_SUCCESS)
        assert sm.current_state == AgentState.OBSERVING
        
        # 观察完成 -> 回到推理
        sm.transition(Signal.CONTINUE)
        assert sm.current_state == AgentState.REASONING
        
        # 任务完成
        sm.transition(Signal.TASK_COMPLETE)
        assert sm.current_state == AgentState.SUCCESS
        assert sm.is_terminal()
    
    def test_failure_recovery_flow(self):
        """测试失败恢复流程"""
        sm = StateMachine()
        observer = FailureObserver()
        
        # 初始流程
        sm.transition(Signal.USER_MESSAGE_RECEIVED)
        sm.transition(Signal.INTENT_CLEAR)
        sm.transition(Signal.PLAN_CREATED)  # PLANNING -> REASONING
        sm.transition(Signal.NEED_TOOL)     # REASONING -> TOOL_CALLING
        
        # 工具失败 -> OBSERVING (失败也要观察)
        sm.transition(Signal.TOOL_FAILED)
        assert sm.current_state == AgentState.OBSERVING
        
        # 观察后发现失败，进入反思
        sm.transition(Signal.EXIT_CODE_FAILURE)
        assert sm.current_state == AgentState.REFLECTING
        
        # 反思后可以重试
        sm.transition(Signal.CAN_RETRY)
        assert sm.current_state == AgentState.REPLANNING
        
        # 重新规划完成
        sm.transition(Signal.NEW_PLAN_CREATED)
        assert sm.current_state == AgentState.REASONING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
