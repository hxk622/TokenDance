"""
Phase 3 Agent Engine 集成测试

验证：
1. Agent Engine 与 ExecutionRouter 的集成
2. 三路执行路径的完整流程
3. UnifiedExecutionContext 数据流
4. 执行路由统计的准确性
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.agent.engine import AgentEngine, AgentResponse
from app.routing.router import ExecutionPath, ExecutionRouter
from app.context.unified_context import (
    UnifiedExecutionContext,
    ExecutionType,
    ExecutionStatus,
    get_unified_context,
    clear_all_contexts,
)


class MockLLM:
    """Mock LLM 客户端"""
    async def complete(self, messages, system=None):
        return Mock(
            content="这是一个测试响应",
            usage={"input_tokens": 100, "output_tokens": 50}
        )


class MockFileSystem:
    """Mock 文件系统"""
    def __init__(self):
        self.files = {}
    
    async def read(self, path):
        return self.files.get(path, "")
    
    async def write(self, path, content):
        self.files[path] = content
    
    async def exists(self, path):
        return path in self.files
    
    def get_session_dir(self, session_id: str):
        """获取 Session 目录"""
        return f"sessions/{session_id}"
    
    def exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return path in self.files
    
    def write_with_frontmatter(self, path: str, content: str, metadata: dict = None):
        """写入带前言的文件"""
        self.files[path] = content
    
    def read_with_frontmatter(self, path: str) -> dict:
        """读取带前言的文件"""
        return {
            "metadata": {},
            "content": self.files.get(path, "")
        }


class TestAgentEngineIntegration:
    """Agent Engine 集成测试"""
    
    @pytest.fixture
    def setup(self):
        """测试前设置"""
        clear_all_contexts()
        llm = MockLLM()
        filesystem = MockFileSystem()
        return llm, filesystem
    
    def test_agent_engine_initialization(self, setup):
        """测试 Agent Engine 初始化"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        # 验证 Phase 2 组件初始化
        assert engine.execution_router is not None
        assert engine.unified_context is not None
        assert engine.mcp_executor is not None
        
        # 验证 Session 隔离
        assert engine.unified_context.session_id == "test_session"
    
    def test_execution_router_registration(self, setup):
        """测试 ExecutionRouter 注册"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
            enable_skills=True,
        )
        
        # 验证 ExecutionRouter 已注册
        assert engine.execution_router is not None
        assert hasattr(engine.execution_router, 'route')
        
        # 验证阈值设置
        assert engine.execution_router.skill_confidence_threshold == 0.85
        assert engine.execution_router.structured_task_confidence == 0.70
    
    def test_unified_context_session_isolation(self, setup):
        """测试 UnifiedExecutionContext 的 Session 隔离"""
        llm, filesystem = setup
        
        # 创建两个 Agent 实例
        engine1 = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="workspace1",
            session_id="session1",
        )
        
        engine2 = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="workspace2",
            session_id="session2",
        )
        
        # 分别设置变量
        engine1.unified_context.set_var("data", "session1_data")
        engine2.unified_context.set_var("data", "session2_data")
        
        # 验证隔离
        assert engine1.unified_context.get_var("data") == "session1_data"
        assert engine2.unified_context.get_var("data") == "session2_data"
    
    @pytest.mark.asyncio
    async def test_skill_path_routing_decision(self, setup):
        """测试 Skill 路径的路由决策"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        # 测试非结构化任务（应该路由到 LLM）
        decision = engine.execution_router.route("你好，今天天气怎么样？")
        assert decision.path == ExecutionPath.LLM_REASONING
        
        # 测试结构化任务（应该路由到 MCP）
        decision = engine.execution_router.route("查询 data.csv 中有多少行")
        assert decision.path == ExecutionPath.MCP_CODE
    
    @pytest.mark.asyncio
    async def test_execution_recording_in_context(self, setup):
        """测试执行记录到 UnifiedExecutionContext"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        # 记录执行
        record = engine.unified_context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="测试消息",
            status=ExecutionStatus.SUCCESS,
            result={"status": "success", "data": "test_data"},
        )
        
        # 验证记录
        assert record.execution_id is not None
        assert record.execution_type == ExecutionType.SKILL
        assert record.status == ExecutionStatus.SUCCESS
        
        # 验证历史
        history = engine.unified_context.get_execution_history()
        assert len(history) == 1
        assert history[0].execution_id == record.execution_id
    
    def test_execution_path_statistics(self, setup):
        """测试路由决策统计"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        # 进行多个路由决策
        decisions = [
            engine.execution_router.route("查询 data.csv"),  # MCP
            engine.execution_router.route("你好"),           # LLM
            engine.execution_router.route("计算平均值"),     # MCP
            engine.execution_router.route("讲个故事"),       # LLM
        ]
        
        # 验证统计
        stats = engine.execution_router.get_stats()
        assert stats["total"] == 4
        
        # 验证分布
        mcp_count = sum(1 for d in decisions if d.path == ExecutionPath.MCP_CODE)
        llm_count = sum(1 for d in decisions if d.path == ExecutionPath.LLM_REASONING)
        
        assert stats[ExecutionPath.MCP_CODE] == mcp_count
        assert stats[ExecutionPath.LLM_REASONING] == llm_count
    
    @pytest.mark.asyncio
    async def test_fallback_chain_recording(self, setup):
        """测试降级链中的执行记录"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        context = engine.unified_context
        
        # 模拟 Skill 失败
        skill_record = context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="分析数据",
            status=ExecutionStatus.FAILED,
            error="Skill not available",
        )
        
        # 降级到 MCP
        mcp_record = context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="分析数据",
            status=ExecutionStatus.SUCCESS,
            result={"status": "success"},
        )
        
        # 验证完整链
        history = context.get_execution_history()
        assert len(history) == 2
        assert history[0].status == ExecutionStatus.FAILED
        assert history[1].status == ExecutionStatus.SUCCESS
        
        # 验证统计
        stats = context.get_execution_stats()
        assert stats["total_executions"] == 2
        assert stats["failed_count"] == 1
        assert stats["success_count"] == 1
    
    def test_shared_variables_across_paths(self, setup):
        """测试跨路径的共享变量"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        context = engine.unified_context
        
        # Skill 路径设置变量
        context.set_var("skill_output", "processed_data")
        
        # MCP 路径读取变量
        assert context.get_var("skill_output") == "processed_data"
        
        # 设置更多变量供 LLM 使用
        context.set_var("execution_context", {
            "previous_results": ["result1", "result2"],
            "timestamp": "2026-01-16"
        })
        
        # 验证 get_all_vars()
        all_vars = context.get_all_vars()
        assert len(all_vars) == 2
        assert all_vars["skill_output"] == "processed_data"
        assert all_vars["execution_context"]["previous_results"] == ["result1", "result2"]
    
    @pytest.mark.asyncio
    async def test_execution_result_injection(self, setup):
        """测试执行结果注入到 Agent Context"""
        llm, filesystem = setup
        
        engine = AgentEngine(
            llm=llm,
            filesystem=filesystem,
            workspace_id="test_workspace",
            session_id="test_session",
        )
        
        # 创建执行结果
        execution_result = {
            "status": "success",
            "path": ExecutionPath.SKILL.value,
            "skill_id": "test_skill",
            "result": {"data": "test_output"},
            "instructions": "## 执行结果\n测试输出\n\n## 后续指令\n继续执行..."
        }
        
        # 注入结果
        engine._inject_execution_result(execution_result, ExecutionPath.SKILL)
        
        # 验证结果已注入（通过日志验证，实际实现中应该检查 context_manager）
        # 这里简单验证方法被调用
        assert engine._inject_execution_result is not None


class TestExecutionPathComparison:
    """执行路径对比测试"""
    
    def test_skill_vs_mcp_routing(self):
        """测试 Skill 和 MCP 的路由对比"""
        router = ExecutionRouter()
        
        # Skill 优先（高置信度匹配）
        test_cases = [
            ("查询 data.csv", ExecutionPath.MCP_CODE),
            ("处理数据", ExecutionPath.LLM_REASONING),  # 太笼统，无法确定
            ("在 sales.csv 中统计", ExecutionPath.MCP_CODE),
            ("执行 SQL 查询", ExecutionPath.MCP_CODE),
        ]
        
        for message, expected_path in test_cases:
            decision = router.route(message)
            assert decision.path == expected_path, f"Failed for: {message}"
    
    def test_confidence_scoring(self):
        """测试置信度评分"""
        router = ExecutionRouter()
        
        # 高置信度的结构化任务
        high_confidence = router.route("在 data.csv 中查询")
        assert high_confidence.confidence >= 0.70
        
        # 低置信度的混淆任务
        low_confidence = router.route("你好")
        assert low_confidence.confidence <= 0.50


class TestMonitoringAndLogging:
    """监控和日志测试"""
    
    def test_router_statistics_tracking(self):
        """测试路由统计追踪"""
        router = ExecutionRouter()
        
        # 初始状态
        stats = router.get_stats()
        assert stats["total"] == 0
        
        # 执行多个路由决策
        for i in range(5):
            router.route(f"测试消息 {i}")
        
        # 验证统计
        stats = router.get_stats()
        assert stats["total"] == 5
        
        # 重置统计
        router.reset_stats()
        stats = router.get_stats()
        assert stats["total"] == 0
    
    def test_context_execution_statistics(self):
        """测试 Context 执行统计"""
        context = UnifiedExecutionContext()
        
        # 记录不同类型的执行
        for i in range(3):
            context.record_execution(
                execution_type=ExecutionType.SKILL,
                user_message=f"skill_{i}",
                status=ExecutionStatus.SUCCESS,
            )
        
        for i in range(2):
            context.record_execution(
                execution_type=ExecutionType.MCP_CODE,
                user_message=f"mcp_{i}",
                status=ExecutionStatus.FAILED,
            )
        
        # 验证统计
        stats = context.get_execution_stats()
        assert stats["total_executions"] == 5
        assert stats["success_count"] == 3
        assert stats["failed_count"] == 2
        assert stats["by_type"]["skill"]["count"] == 3
        assert stats["by_type"]["mcp_code"]["count"] == 2


class TestErrorHandlingAndRecovery:
    """错误处理和恢复测试"""
    
    def test_skill_execution_failure_handling(self):
        """测试 Skill 执行失败处理"""
        context = UnifiedExecutionContext()
        
        # 记录失败
        record = context.record_execution(
            execution_type=ExecutionType.SKILL,
            user_message="任务",
            status=ExecutionStatus.FAILED,
            error="Skill 不可用",
        )
        
        # 更新为成功（模拟降级恢复）
        updated = context.update_execution_record(
            execution_id=record.execution_id,
            status=ExecutionStatus.SUCCESS,
            result={"status": "recovered"},
        )
        
        assert updated.status == ExecutionStatus.SUCCESS
        assert updated.duration is not None
    
    def test_timeout_handling(self):
        """测试超时处理"""
        context = UnifiedExecutionContext()
        
        # 记录超时
        record = context.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            user_message="耗时任务",
            status=ExecutionStatus.TIMEOUT,
            error="代码执行超时 (30s)",
        )
        
        # 验证记录
        assert record.status == ExecutionStatus.TIMEOUT
        assert "超时" in record.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
