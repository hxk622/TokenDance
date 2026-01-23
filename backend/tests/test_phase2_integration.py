"""
Phase 2 集成测试

验证：
1. ExecutionRouter 路由决策
2. UnifiedExecutionContext 上下文管理
3. 完整的 Skill → MCP → LLM 降级流程
4. 跨路径数据传递
"""

import pytest

from app.context.unified_context import (
    ExecutionStatus,
    ExecutionType,
    UnifiedExecutionContext,
    clear_all_contexts,
    get_unified_context,
)
from app.routing.router import (
    ExecutionPath,
    ExecutionRouter,
    reset_execution_router,
)


class TestUnifiedExecutionContext:
    """统一执行上下文测试"""

    def setup_method(self):
        """清空上下文"""
        clear_all_contexts()

    def test_context_creation(self):
        """测试上下文创建"""
        context = UnifiedExecutionContext()
        assert context.session_id is not None
        assert context.shared_vars == {}
        assert context.execution_history == []

    def test_shared_variables(self):
        """测试共享变量"""
        context = UnifiedExecutionContext()

        # 设置变量
        context.set_var("result", 42)
        context.set_var("data", {"name": "test"})

        # 获取变量
        assert context.get_var("result") == 42
        assert context.get_var("data") == {"name": "test"}
        assert context.get_var("nonexistent", "default") == "default"

    def test_variable_persistence_across_paths(self):
        """测试变量在不同执行路径间的持久化"""
        context = UnifiedExecutionContext()

        # Skill 路径设置变量
        context.set_var("skill_result", "processed_data")

        # MCP 路径读取变量
        assert context.get_var("skill_result") == "processed_data"

    def test_delete_variable(self):
        """测试删除变量"""
        context = UnifiedExecutionContext()
        context.set_var("temp", "value")

        assert context.has_var("temp")
        context.delete_var("temp")
        assert not context.has_var("temp")

    def test_clear_all_variables(self):
        """测试清空所有变量"""
        context = UnifiedExecutionContext()
        context.set_var("var1", "value1")
        context.set_var("var2", "value2")

        assert len(context.shared_vars) == 2
        context.clear_vars()
        assert len(context.shared_vars) == 0

    def test_execution_recording(self):
        """测试执行记录"""
        context = UnifiedExecutionContext()

        # 记录执行
        record = context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="测试",
            status=ExecutionStatus.SUCCESS,
            result="success",
            tokens_used=100,
        )

        assert record.execution_id is not None
        assert record.execution_type == ExecutionType.SKILL
        assert record.status == ExecutionStatus.SUCCESS
        assert record.result == "success"
        assert len(context.execution_history) == 1

    def test_execution_record_update(self):
        """测试更新执行记录"""
        context = UnifiedExecutionContext()

        # 记录初始执行
        record = context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="测试",
            status=ExecutionStatus.PENDING,
        )
        execution_id = record.execution_id

        # 更新记录
        updated = context.update_execution_record(
            execution_id=execution_id,
            status=ExecutionStatus.SUCCESS,
            result="completed",
            tokens_used=200,
        )

        assert updated is not None
        assert updated.status == ExecutionStatus.SUCCESS
        assert updated.result == "completed"
        assert updated.duration is not None

    def test_execution_history_filtering(self):
        """测试执行历史筛选"""
        context = UnifiedExecutionContext()

        # 记录多种类型的执行
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="skill1",
            status=ExecutionStatus.SUCCESS,
        )
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="mcp1",
            status=ExecutionStatus.SUCCESS,
        )
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="skill2",
            status=ExecutionStatus.FAILED,
        )

        # 筛选 Skill 执行
        skill_records = context.get_execution_history(execution_type=ExecutionType.SKILL)
        assert len(skill_records) == 2

        # 获取最后一条
        last = context.get_last_execution()
        assert last.user_message == "skill2"

    def test_execution_statistics(self):
        """测试执行统计"""
        context = UnifiedExecutionContext()

        # 记录多条记录
        for i in range(5):
            context.record_execution(
                execution_type=ExecutionType.SKILL if i % 2 == 0 else ExecutionType.MCP_CODE,
                user_message=f"message{i}",
                status=ExecutionStatus.SUCCESS if i < 3 else ExecutionStatus.FAILED,
            )

        stats = context.get_execution_stats()
        assert stats["total_executions"] == 5
        assert stats["success_count"] == 3
        assert stats["failed_count"] == 2
        assert "skill" in stats["by_type"]
        assert "mcp_code" in stats["by_type"]

    def test_tool_registry(self):
        """测试工具注册"""
        context = UnifiedExecutionContext()

        # 注册工具
        context.tools.register_tool(
            "requests",
            {"timeout": 30},
            enabled=True,
        )

        # 检查可用性
        assert context.tools.is_tool_available("requests")
        assert context.tools.get_tool("requests") is not None

        # 禁用工具
        context.tools.disable_tool("requests")
        assert not context.tools.is_tool_available("requests")

    def test_session_isolation(self):
        """测试会话隔离"""
        # 创建两个独立的上下文
        context1 = get_unified_context("session1")
        context2 = get_unified_context("session2")

        # 设置不同的变量
        context1.set_var("data", "session1_data")
        context2.set_var("data", "session2_data")

        # 验证隔离
        assert context1.get_var("data") == "session1_data"
        assert context2.get_var("data") == "session2_data"

    def test_context_serialization(self):
        """测试上下文序列化"""
        context = UnifiedExecutionContext()
        context.set_var("test", "value")
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="test",
            status=ExecutionStatus.SUCCESS,
        )

        # 转换为字典
        data = context.to_dict()
        assert "session_id" in data
        assert "shared_vars" in data
        assert "execution_history" in data

        # 转换为 JSON
        json_str = context.to_json()
        assert "session_id" in json_str


class TestCrosPathDataFlow:
    """跨路径数据流测试"""

    def setup_method(self):
        """清空上下文"""
        clear_all_contexts()

    def test_skill_to_mcp_data_transfer(self):
        """测试 Skill → MCP 数据传递"""
        context = get_unified_context("test_session")

        # 模拟 Skill 执行并设置结果
        context.set_var("processed_data", {"items": [1, 2, 3]})
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="处理数据",
            status=ExecutionStatus.SUCCESS,
            result="processed_data",
        )

        # MCP 路径读取数据
        data = context.get_var("processed_data")
        assert data == {"items": [1, 2, 3]}

    def test_mcp_to_llm_data_transfer(self):
        """测试 MCP → LLM 数据传递"""
        context = get_unified_context("test_session")

        # MCP 执行并设置结果
        context.set_var("code_output", "result = 42")
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="执行代码",
            status=ExecutionStatus.SUCCESS,
        )

        # LLM 推理可访问结果
        output = context.get_var("code_output")
        assert output == "result = 42"

    def test_fallback_chain_data_preservation(self):
        """测试降级链中的数据保存"""
        context = get_unified_context("test_session")

        # Skill 尝试但失败
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="分析",
            status=ExecutionStatus.FAILED,
        )
        context.set_var("partial_result", "some_analysis")

        # MCP 接管并继续
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="分析",
            status=ExecutionStatus.SUCCESS,
        )

        # 验证数据连续性
        partial = context.get_var("partial_result")
        assert partial == "some_analysis"

        # 验证历史完整
        history = context.execution_history
        assert len(history) == 2
        assert history[0].execution_type == ExecutionType.SKILL
        assert history[1].execution_type == ExecutionType.MCP_CODE


class TestExecutionRouterIntegration:
    """ExecutionRouter 集成测试"""

    def setup_method(self):
        """重置路由器和上下文"""
        reset_execution_router()
        clear_all_contexts()

    @pytest.mark.asyncio
    async def test_router_decision_logging(self):
        """测试路由决策是否记录到上下文"""
        get_unified_context()
        router = ExecutionRouter()

        # 做出路由决策
        decision = await router.route("查询 data.csv")

        # 验证决策信息
        assert decision.path == ExecutionPath.MCP_CODE
        assert decision.confidence >= 0.75
        assert "Structured task" in decision.reason

    @pytest.mark.asyncio
    async def test_router_statistics_tracking(self):
        """测试路由器统计追踪"""
        router = ExecutionRouter()

        # 执行多个路由决策
        await router.route("做深度研究")
        await router.route("查询 CSV")
        await router.route("你好")
        await router.route("计算平均值")

        stats = router.get_stats()
        assert stats["total"] == 4
        assert stats["mcp_code_ratio"] >= 0.25


class TestFallbackScenarios:
    """降级场景测试"""

    def setup_method(self):
        """重置"""
        reset_execution_router()
        clear_all_contexts()

    def test_skill_fallback_to_mcp(self):
        """测试 Skill 失败降级到 MCP"""
        context = get_unified_context()

        # 记录 Skill 失败
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="复杂分析",
            status=ExecutionStatus.FAILED,
            error="Skill not available",
        )

        # 降级到 MCP
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="复杂分析",
            status=ExecutionStatus.SUCCESS,
            result="analysis_result",
        )

        # 验证历史链
        history = context.get_execution_history()
        assert len(history) == 2
        assert history[0].status == ExecutionStatus.FAILED
        assert history[1].status == ExecutionStatus.SUCCESS

    def test_mcp_fallback_to_llm(self):
        """测试 MCP 失败降级到 LLM"""
        context = get_unified_context()

        # MCP 执行失败
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="复杂计算",
            status=ExecutionStatus.TIMEOUT,
            error="Code execution timeout",
        )

        # 降级到 LLM
        context.record_execution(
            execution_type=ExecutionType.LLM_REASONING,
            user_message="复杂计算",
            status=ExecutionStatus.SUCCESS,
        )

        # 验证统计
        stats = context.get_execution_stats()
        assert stats["failed_count"] == 1
        assert stats["success_count"] == 1

    def test_complete_fallback_chain(self):
        """测试完整的降级链：Skill → MCP → LLM"""
        context = get_unified_context()

        # Step 1: Skill 尝试但不可用
        context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="任务",
            status=ExecutionStatus.FAILED,
        )

        # Step 2: MCP 尝试但失败
        context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="任务",
            status=ExecutionStatus.FAILED,
        )

        # Step 3: LLM 接管成功
        context.record_execution(
            execution_type=ExecutionType.LLM_REASONING,
            user_message="任务",
            status=ExecutionStatus.SUCCESS,
            result="final_result",
        )

        # 验证完整链
        history = context.get_execution_history()
        assert len(history) == 3
        assert history[0].execution_type == ExecutionType.SKILL
        assert history[1].execution_type == ExecutionType.MCP_CODE
        assert history[2].execution_type == ExecutionType.LLM_REASONING
        assert history[2].status == ExecutionStatus.SUCCESS


class TestConcurrentExecutions:
    """并发执行测试"""

    def setup_method(self):
        """清空上下文"""
        clear_all_contexts()

    def test_multiple_contexts_isolation(self):
        """测试多个上下文的隔离"""
        contexts = [
            get_unified_context(f"session_{i}")
            for i in range(3)
        ]

        # 各自设置不同的变量
        for i, ctx in enumerate(contexts):
            ctx.set_var("value", i * 10)
            ctx.record_execution(
                execution_type=ExecutionType.SKILL,
                user_message=f"task_{i}",
                status=ExecutionStatus.SUCCESS,
            )

        # 验证隔离
        for i, ctx in enumerate(contexts):
            assert ctx.get_var("value") == i * 10
            assert len(ctx.execution_history) == 1


class TestEdgeCases:
    """边界情况测试"""

    def setup_method(self):
        """清空上下文"""
        clear_all_contexts()

    def test_nonexistent_execution_update(self):
        """测试更新不存在的执行记录"""
        context = UnifiedExecutionContext()

        result = context.update_execution_record(
            execution_id="nonexistent",
            status=ExecutionStatus.SUCCESS,
        )

        assert result is None

    def test_empty_execution_history_stats(self):
        """测试空执行历史的统计"""
        context = UnifiedExecutionContext()

        stats = context.get_execution_stats()
        assert stats["total_executions"] == 0
        assert stats["success_count"] == 0
        assert stats["failed_count"] == 0

    def test_get_var_with_default(self):
        """测试获取不存在的变量时使用默认值"""
        context = UnifiedExecutionContext()

        default_value = {"default": True}
        result = context.get_var("nonexistent", default_value)

        assert result == default_value
        assert not context.has_var("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
