"""
Context Graph 服务测试

测试:
1. ContextGraphService 基本功能
2. FailureObserver 失败观测
3. 决策轨迹记录
4. 3-Strike Protocol
"""

import pytest
from datetime import datetime

from app.services.context_graph import (
    ContextGraphService,
    DecisionTrace,
    FailureObserver,
    FailureSignal,
    FailureTaxonomy,
    RecoveryStrategy,
    get_context_graph_service,
)
from app.services.context_graph.service import DecisionType, StorageMode
from app.services.context_graph.failure_observer import (
    create_failure_signal_from_tool_result,
)


class TestFailureSignal:
    """FailureSignal 测试"""

    def test_create_failure_signal(self) -> None:
        """测试创建失败信号"""
        signal = FailureSignal(
            signal_id="test-123",
            timestamp=datetime.now(),
            source="tool",
            tool_name="run_code",
            exit_code=1,
            error_message="Command not found",
            taxonomy=FailureTaxonomy.TOOL_EXECUTION_ERROR,
        )

        assert signal.exit_code == 1
        assert signal.taxonomy == FailureTaxonomy.TOOL_EXECUTION_ERROR
        assert signal.is_retryable is True

    def test_get_learning(self) -> None:
        """测试获取失败教训"""
        signal = FailureSignal(
            signal_id="test-123",
            timestamp=datetime.now(),
            source="tool",
            taxonomy=FailureTaxonomy.TOOL_TIMEOUT,
            exit_code=124,
        )

        learning = signal.get_learning()
        assert "超时" in learning

    def test_get_recovery_strategy(self) -> None:
        """测试获取恢复策略"""
        signal = FailureSignal(
            signal_id="test-123",
            timestamp=datetime.now(),
            source="tool",
            taxonomy=FailureTaxonomy.SELECTION_MISS,
            exit_code=1,
        )

        strategy = signal.get_recovery_strategy()
        assert strategy.action == "expand_context"
        assert strategy.params.get("window_size") == 30

    def test_to_dict(self) -> None:
        """测试序列化"""
        signal = FailureSignal(
            signal_id="test-123",
            timestamp=datetime.now(),
            source="tool",
            tool_name="pytest",
            exit_code=1,
            error_message="Test failed",
            taxonomy=FailureTaxonomy.TEST_FAIL,
        )

        data = signal.to_dict()
        assert data["signal_id"] == "test-123"
        assert data["taxonomy"] == "test_fail"
        assert data["exit_code"] == 1


class TestCreateFailureSignalFromToolResult:
    """测试从工具结果创建失败信号"""

    def test_success_returns_none(self) -> None:
        """成功时返回 None"""
        result = create_failure_signal_from_tool_result(
            tool_name="run_code",
            tool_args={"code": "print('hello')"},
            exit_code=0,
            stdout="hello",
            stderr="",
            duration_ms=100,
        )
        assert result is None

    def test_timeout_detection(self) -> None:
        """测试超时检测"""
        result = create_failure_signal_from_tool_result(
            tool_name="run_code",
            tool_args={"code": "sleep 100"},
            exit_code=124,
            stdout="",
            stderr="timeout: command timed out",
            duration_ms=30000,
        )

        assert result is not None
        assert result.taxonomy == FailureTaxonomy.TOOL_TIMEOUT

    def test_permission_denied_detection(self) -> None:
        """测试权限拒绝检测"""
        result = create_failure_signal_from_tool_result(
            tool_name="write_file",
            tool_args={"path": "/etc/passwd"},
            exit_code=1,
            stdout="",
            stderr="permission denied",
            duration_ms=10,
        )

        assert result is not None
        assert result.taxonomy == FailureTaxonomy.TOOL_PERMISSION_DENIED

    def test_not_found_detection(self) -> None:
        """测试文件不存在检测"""
        result = create_failure_signal_from_tool_result(
            tool_name="read_file",
            tool_args={"path": "/nonexistent/file.txt"},
            exit_code=1,
            stdout="",
            stderr="No such file or directory",
            duration_ms=5,
        )

        assert result is not None
        assert result.taxonomy == FailureTaxonomy.SELECTION_MISS

    def test_test_fail_detection(self) -> None:
        """测试测试失败检测"""
        result = create_failure_signal_from_tool_result(
            tool_name="pytest",
            tool_args={"args": ["tests/"]},
            exit_code=1,
            stdout="",
            stderr="1 failed, 2 passed",
            duration_ms=5000,
        )

        assert result is not None
        assert result.taxonomy == FailureTaxonomy.TEST_FAIL


class TestRecoveryStrategy:
    """RecoveryStrategy 测试"""

    def test_retry_strategy(self) -> None:
        """测试重试策略"""
        strategy = RecoveryStrategy.retry(delay_seconds=5.0)
        assert strategy.action == "retry"
        assert strategy.params["delay_seconds"] == 5.0

    def test_replan_strategy(self) -> None:
        """测试重新规划策略"""
        strategy = RecoveryStrategy.replan("需要不同的方法")
        assert strategy.action == "replan"
        assert "不同的方法" in strategy.suggestion

    def test_rollback_strategy(self) -> None:
        """测试回滚策略"""
        strategy = RecoveryStrategy.rollback("checkpoint-001")
        assert strategy.action == "rollback"
        assert strategy.params["checkpoint_id"] == "checkpoint-001"

    def test_escalate_strategy(self) -> None:
        """测试升级策略"""
        strategy = RecoveryStrategy.escalate("需要管理员权限")
        assert strategy.action == "escalate"
        assert "管理员" in strategy.suggestion


class TestFailureObserver:
    """FailureObserver 测试"""

    @pytest.fixture
    def observer(self) -> FailureObserver:
        """创建测试用观测器"""
        return FailureObserver(max_history=50)

    @pytest.mark.asyncio
    async def test_observe_single_failure(self, observer: FailureObserver) -> None:
        """测试观测单个失败"""
        signal = FailureSignal(
            signal_id="test-001",
            timestamp=datetime.now(),
            source="tool",
            taxonomy=FailureTaxonomy.TOOL_EXECUTION_ERROR,
            exit_code=1,
            error_message="Something went wrong",
        )

        await observer.observe(signal)

        assert len(observer.failure_history) == 1
        assert not observer.should_abort()

    @pytest.mark.asyncio
    async def test_three_strike_protocol(self, observer: FailureObserver) -> None:
        """测试 3-Strike Protocol"""
        # 连续3次相同类型的失败
        for i in range(3):
            signal = FailureSignal(
                signal_id=f"test-{i}",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
                error_message=f"Test failed {i}",
            )
            await observer.observe(signal)

        assert observer.should_abort()
        assert observer.get_consecutive_failure_type() == FailureTaxonomy.TEST_FAIL

    @pytest.mark.asyncio
    async def test_consecutive_reset_on_different_type(
        self, observer: FailureObserver
    ) -> None:
        """测试不同类型失败重置连续计数"""
        # 2次 TEST_FAIL
        for i in range(2):
            signal = FailureSignal(
                signal_id=f"test-{i}",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
            )
            await observer.observe(signal)

        # 1次 LINT_FAIL (不同类型)
        signal = FailureSignal(
            signal_id="test-lint",
            timestamp=datetime.now(),
            source="tool",
            taxonomy=FailureTaxonomy.LINT_FAIL,
            exit_code=1,
        )
        await observer.observe(signal)

        # 连续计数应该重置
        assert len(observer._consecutive_failures) == 1
        assert not observer.should_abort()

    @pytest.mark.asyncio
    async def test_clear_consecutive_on_success(
        self, observer: FailureObserver
    ) -> None:
        """测试成功后清除连续失败"""
        # 2次失败
        for i in range(2):
            signal = FailureSignal(
                signal_id=f"test-{i}",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
            )
            await observer.observe(signal)

        # 模拟成功
        observer.clear_consecutive()

        assert len(observer._consecutive_failures) == 0

    def test_get_failure_summary(self, observer: FailureObserver) -> None:
        """测试生成失败摘要"""
        # 添加一些失败
        observer.failure_history = [
            FailureSignal(
                signal_id="test-1",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
            ),
            FailureSignal(
                signal_id="test-2",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.LINT_FAIL,
                exit_code=1,
            ),
        ]

        summary = observer.get_failure_summary()
        assert "历史失败" in summary
        assert "test_fail" in summary
        assert "lint_fail" in summary

    @pytest.mark.asyncio
    async def test_get_similar_failures(self, observer: FailureObserver) -> None:
        """测试获取相似失败"""
        # 添加一些失败 - 使用不同的关键词以便精确匹配
        observer.failure_history = [
            FailureSignal(
                signal_id="test-1",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
                error_message="pytest assertion error in test_user",
            ),
            FailureSignal(
                signal_id="test-2",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.TEST_FAIL,
                exit_code=1,
                error_message="pytest assertion error in test_auth",
            ),
            FailureSignal(
                signal_id="test-3",
                timestamp=datetime.now(),
                source="tool",
                taxonomy=FailureTaxonomy.LINT_FAIL,
                exit_code=1,
                error_message="ruff linting problem found",
            ),
        ]

        # 使用 "pytest assertion" 精确匹配 TEST_FAIL 类型
        similar = await observer.get_similar_failures("pytest assertion")
        assert len(similar) >= 1
        # 检查返回的结果至少包含 TEST_FAIL (由于关键词匹配，可能不是全部)
        assert any(f.taxonomy == FailureTaxonomy.TEST_FAIL for f in similar)


class TestContextGraphService:
    """ContextGraphService 测试"""

    @pytest.fixture
    def service(self) -> ContextGraphService:
        """创建测试用服务"""
        return ContextGraphService(mode=StorageMode.MEMORY)

    @pytest.mark.asyncio
    async def test_record_state_transition(
        self, service: ContextGraphService
    ) -> None:
        """测试记录状态转移"""
        trace = await service.record_state_transition(
            from_state="INIT",
            to_state="REASONING",
            signal="user_message_received",
            task_id="task-001",
            session_id="session-001",
        )

        assert trace.decision_type == DecisionType.STATE_TRANSITION
        assert trace.from_state == "INIT"
        assert trace.to_state == "REASONING"
        assert trace.signal == "user_message_received"

        # 检查统计
        stats = service.get_statistics()
        assert stats["total_traces"] == 1

    @pytest.mark.asyncio
    async def test_record_tool_call_and_result(
        self, service: ContextGraphService
    ) -> None:
        """测试记录工具调用和结果"""
        # 记录调用
        call_trace = await service.record_tool_call(
            tool_name="run_code",
            tool_args={"code": "print('hello')"},
            task_id="task-001",
            session_id="session-001",
            state_name="TOOL_CALLING",
        )

        assert call_trace.decision_type == DecisionType.TOOL_CALL
        assert call_trace.tool_name == "run_code"

        # 记录成功结果
        result_trace = await service.record_tool_result(
            tool_name="run_code",
            tool_args={"code": "print('hello')"},
            result="hello",
            exit_code=0,
            duration_ms=50,
            stdout="hello",
            stderr="",
            task_id="task-001",
            session_id="session-001",
        )

        assert result_trace.exit_code == 0
        assert service.failure_observer.failure_history == []  # 没有失败

    @pytest.mark.asyncio
    async def test_record_tool_failure(self, service: ContextGraphService) -> None:
        """测试记录工具失败"""
        # 记录失败结果
        result_trace = await service.record_tool_result(
            tool_name="run_code",
            tool_args={"code": "exit 1"},
            result=None,
            exit_code=1,
            duration_ms=50,
            stdout="",
            stderr="Command failed",
            task_id="task-001",
            session_id="session-001",
        )

        assert result_trace.exit_code == 1

        # 检查失败被记录
        assert len(service.failure_observer.failure_history) == 1
        failure = service.failure_observer.failure_history[0]
        assert failure.tool_name == "run_code"
        assert failure.exit_code == 1

    @pytest.mark.asyncio
    async def test_get_recent_traces(self, service: ContextGraphService) -> None:
        """测试获取最近轨迹"""
        # 创建多个轨迹
        for i in range(5):
            await service.record_state_transition(
                from_state=f"STATE_{i}",
                to_state=f"STATE_{i+1}",
                signal=f"signal_{i}",
                session_id="session-001",
            )

        traces = service.get_recent_traces(limit=3)
        assert len(traces) == 3

    @pytest.mark.asyncio
    async def test_get_session_summary(self, service: ContextGraphService) -> None:
        """测试获取会话摘要"""
        session_id = "session-001"

        # 创建一些活动
        await service.record_state_transition(
            from_state="INIT",
            to_state="REASONING",
            signal="start",
            session_id=session_id,
        )

        await service.record_tool_call(
            tool_name="read_file",
            tool_args={"path": "test.py"},
            session_id=session_id,
        )

        await service.record_tool_result(
            tool_name="read_file",
            tool_args={"path": "test.py"},
            result="content",
            exit_code=0,
            duration_ms=10,
            session_id=session_id,
        )

        summary = service.get_session_summary(session_id)

        assert summary["session_id"] == session_id
        assert summary["total_traces"] == 3
        assert summary["state_transitions"] == 1
        assert summary["tool_calls"] == 1
        assert "read_file" in summary["unique_tools"]

    @pytest.mark.asyncio
    async def test_clear_session(self, service: ContextGraphService) -> None:
        """测试清除会话数据"""
        # 创建两个会话的数据
        await service.record_state_transition(
            from_state="INIT",
            to_state="REASONING",
            signal="start",
            session_id="session-001",
        )

        await service.record_state_transition(
            from_state="INIT",
            to_state="REASONING",
            signal="start",
            session_id="session-002",
        )

        # 清除 session-001
        service.clear(session_id="session-001")

        # 检查
        traces = service.get_recent_traces()
        assert all(t.session_id != "session-001" for t in traces)
        assert any(t.session_id == "session-002" for t in traces)

    @pytest.mark.asyncio
    async def test_export_traces(self, service: ContextGraphService) -> None:
        """测试导出轨迹"""
        await service.record_state_transition(
            from_state="INIT",
            to_state="REASONING",
            signal="start",
            session_id="session-001",
        )

        exported = service.export_traces(session_id="session-001")

        assert len(exported) == 1
        assert exported[0]["decision_type"] == "state_transition"
        assert "timestamp" in exported[0]


class TestContextGraphServiceIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self) -> None:
        """测试完整的 Agent 工作流"""
        service = ContextGraphService(mode=StorageMode.MEMORY)
        session_id = "integration-test"
        task_id = "task-001"

        # 1. 开始任务
        await service.record_state_transition(
            from_state="INIT",
            to_state="PARSING_INTENT",
            signal="user_message_received",
            task_id=task_id,
            session_id=session_id,
        )

        # 2. 规划
        await service.record_state_transition(
            from_state="PARSING_INTENT",
            to_state="PLANNING",
            signal="intent_clear",
            task_id=task_id,
            session_id=session_id,
        )

        # 3. 推理
        await service.record_state_transition(
            from_state="PLANNING",
            to_state="REASONING",
            signal="plan_created",
            task_id=task_id,
            session_id=session_id,
        )

        # 4. 工具调用
        await service.record_state_transition(
            from_state="REASONING",
            to_state="TOOL_CALLING",
            signal="need_tool",
            task_id=task_id,
            session_id=session_id,
        )

        await service.record_tool_call(
            tool_name="read_file",
            tool_args={"path": "main.py"},
            task_id=task_id,
            session_id=session_id,
            state_name="TOOL_CALLING",
        )

        # 5. 工具失败
        await service.record_tool_result(
            tool_name="read_file",
            tool_args={"path": "main.py"},
            result=None,
            exit_code=1,
            duration_ms=10,
            stderr="No such file or directory",
            task_id=task_id,
            session_id=session_id,
            state_name="TOOL_CALLING",
        )

        # 6. 观察失败
        await service.record_state_transition(
            from_state="TOOL_CALLING",
            to_state="OBSERVING",
            signal="tool_failed",
            task_id=task_id,
            session_id=session_id,
        )

        # 检查结果
        stats = service.get_statistics()
        assert stats["total_traces"] >= 6
        assert stats["total_failures"] == 1

        summary = service.get_session_summary(session_id)
        assert summary["failures"] == 1
        assert FailureTaxonomy.SELECTION_MISS.value in summary["failure_types"]

        # 检查失败摘要
        failure_summary = service.failure_observer.get_failure_summary()
        assert "selection_miss" in failure_summary


class TestContextGraphServiceSingleton:
    """单例测试"""

    @pytest.mark.asyncio
    async def test_get_singleton(self) -> None:
        """测试获取单例"""
        from app.services.context_graph.service import (
            _service_instance,
            close_context_graph_service,
        )

        # 确保清理
        await close_context_graph_service()

        # 获取服务
        service1 = await get_context_graph_service(mode=StorageMode.MEMORY)
        service2 = await get_context_graph_service()

        # 应该是同一个实例
        assert service1 is service2

        # 清理
        await close_context_graph_service()
