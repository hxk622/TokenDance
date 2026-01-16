"""
ExecutionRouter 单元测试

测试路由决策逻辑、启发式规则和置信度阈值管理。
"""

import pytest
from app.routing.router import (
    ExecutionRouter,
    ExecutionPath,
    RoutingDecision,
    get_execution_router,
    reset_execution_router,
)


class MockSkillMatch:
    """Mock Skill 匹配结果"""
    def __init__(self, skill_id: str, score: float):
        self.skill_id = skill_id
        self.score = score


class MockSkillMatcher:
    """Mock SkillMatcher"""
    def __init__(self, match_result=None):
        self.match_result = match_result
    
    def match(self, message: str):
        return self.match_result


class MockSkillExecutor:
    """Mock SkillExecutor"""
    def __init__(self, can_execute_result=True):
        self.can_execute_result = can_execute_result
    
    def can_execute(self, skill_id: str) -> bool:
        return self.can_execute_result


class TestExecutionRouterBasic:
    """基础路由功能测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_initialization(self):
        """测试路由器初始化"""
        router = ExecutionRouter()
        assert router.skill_confidence_threshold == 0.85
        assert router.structured_task_confidence == 0.75
        assert router.stats["total"] == 0
    
    def test_custom_thresholds(self):
        """测试自定义阈值初始化"""
        router = ExecutionRouter(
            skill_confidence_threshold=0.9,
            structured_task_confidence=0.8,
        )
        assert router.skill_confidence_threshold == 0.9
        assert router.structured_task_confidence == 0.8


class TestSkillPathRouting:
    """Skill 路由路径测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_high_confidence_skill_match(self):
        """测试高置信度 Skill 匹配"""
        matcher = MockSkillMatcher(MockSkillMatch("deep_research", 0.95))
        executor = MockSkillExecutor(can_execute_result=True)
        router = ExecutionRouter(skill_matcher=matcher, skill_executor=executor)
        
        decision = router.route("做深度研究")
        
        assert decision.path == ExecutionPath.SKILL
        assert decision.confidence == 0.95
        assert "deep_research" in decision.reason
        assert decision.fallback_path == ExecutionPath.MCP_CODE
    
    def test_low_confidence_skill_match(self):
        """测试低置信度 Skill 匹配（应该降级）"""
        matcher = MockSkillMatcher(MockSkillMatch("deep_research", 0.70))
        router = ExecutionRouter(
            skill_matcher=matcher,
            skill_confidence_threshold=0.85,
        )
        
        decision = router.route("做深度研究")
        
        # 低于阈值，应该继续检查结构化任务
        assert decision.path != ExecutionPath.SKILL
    
    def test_skill_not_executable(self):
        """测试 Skill 不可执行的情况"""
        matcher = MockSkillMatcher(MockSkillMatch("deep_research", 0.95))
        executor = MockSkillExecutor(can_execute_result=False)
        router = ExecutionRouter(skill_matcher=matcher, skill_executor=executor)
        
        decision = router.route("做深度研究")
        
        # Skill 虽然匹配但不可执行，应该继续检查其他路径
        assert decision.path != ExecutionPath.SKILL


class TestStructuredTaskDetection:
    """结构化任务检测测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_csv_file_detection(self):
        """测试 CSV 文件相关任务"""
        router = ExecutionRouter()
        decision = router.route("查找 data.csv 中状态为 Active 的行数")
        
        assert decision.path == ExecutionPath.MCP_CODE
        assert decision.confidence >= 0.75
    
    def test_json_file_detection(self):
        """测试 JSON 文件相关任务"""
        router = ExecutionRouter()
        decision = router.route("读取 config.json 文件")
        
        assert decision.path == ExecutionPath.MCP_CODE
        assert decision.confidence >= 0.75
    
    def test_dataframe_keyword(self):
        """测试 DataFrame 关键词"""
        router = ExecutionRouter()
        decision = router.route("在 dataframe 中筛选值大于 100 的行")
        
        assert decision.path == ExecutionPath.MCP_CODE
    
    def test_sql_query_detection(self):
        """测试 SQL 查询检测"""
        router = ExecutionRouter()
        decision = router.route("执行 SELECT * FROM users WHERE status = 'active'")
        
        assert decision.path == ExecutionPath.MCP_CODE
        assert decision.confidence >= 0.85
    
    def test_calculation_detection(self):
        """测试计算任务检测"""
        router = ExecutionRouter()
        decision = router.route("计算列表的平均值: average([1, 2, 3, 4, 5])")
        
        assert decision.path == ExecutionPath.MCP_CODE
    
    def test_data_processing_keywords(self):
        """测试数据处理关键词"""
        router = ExecutionRouter()
        message = "将 CSV 转换为 JSON 格式"
        decision = router.route(message)
        
        assert decision.path == ExecutionPath.MCP_CODE
    
    def test_code_execution_request(self):
        """测试显式代码执行请求"""
        router = ExecutionRouter()
        # 需要同时包含"代码"关键词和"处理数据"等结构化任务关键词
        decision = router.route("写一个 Python 脚本来查询 CSV 数据")
        
        assert decision.path == ExecutionPath.MCP_CODE


class TestLLMReasoningFallback:
    """LLM 推理降级测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_unstructured_question(self):
        """测试非结构化问题"""
        router = ExecutionRouter()
        decision = router.route("你认为 AI 的未来如何？")
        
        assert decision.path == ExecutionPath.LLM_REASONING
    
    def test_writing_task(self):
        """测试写作任务"""
        router = ExecutionRouter()
        decision = router.route("帮我写一篇关于机器学习的文章")
        
        assert decision.path == ExecutionPath.LLM_REASONING
    
    def test_general_advice(self):
        """测试一般建议"""
        router = ExecutionRouter()
        decision = router.route("给我一些项目管理的建议")
        
        assert decision.path == ExecutionPath.LLM_REASONING
    
    def test_no_skill_match_no_structured_keywords(self):
        """测试无 Skill 匹配且无结构化关键词"""
        router = ExecutionRouter()
        decision = router.route("你好，今天天气怎么样？")
        
        assert decision.path == ExecutionPath.LLM_REASONING


class TestThresholdManagement:
    """阈值管理测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_update_skill_threshold(self):
        """测试更新 Skill 置信度阈值"""
        router = ExecutionRouter(skill_confidence_threshold=0.85)
        router.update_threshold(skill_threshold=0.95)
        
        assert router.skill_confidence_threshold == 0.95
    
    def test_update_structured_threshold(self):
        """测试更新结构化任务阈值"""
        router = ExecutionRouter(structured_task_confidence=0.75)
        router.update_threshold(structured_threshold=0.80)
        
        assert router.structured_task_confidence == 0.80
    
    def test_threshold_bounds(self):
        """测试阈值边界约束"""
        router = ExecutionRouter()
        
        # 测试上界
        router.update_threshold(skill_threshold=1.5)
        assert router.skill_confidence_threshold == 1.0
        
        # 测试下界
        router.update_threshold(skill_threshold=-0.5)
        assert router.skill_confidence_threshold == 0.0


class TestStatistics:
    """统计信息测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_stats_tracking(self):
        """测试统计追踪"""
        router = ExecutionRouter()
        
        # 执行多个路由决策
        router.route("做深度研究")
        router.route("查询 CSV 文件")
        router.route("你好")
        
        stats = router.get_stats()
        assert stats["total"] == 3
    
    def test_path_distribution(self):
        """测试执行路径分布统计"""
        router = ExecutionRouter()
        
        # 强制指定结构化任务
        for _ in range(10):
            router.route("计算 average([1,2,3])")
        
        stats = router.get_stats()
        assert stats["total"] == 10
        assert stats["mcp_code_ratio"] >= 0.5  # 至少一半应该是 MCP
    
    def test_reset_stats(self):
        """测试重置统计"""
        router = ExecutionRouter()
        router.route("测试")
        router.route("测试")
        
        assert router.stats["total"] == 2
        
        router.reset_stats()
        assert router.stats["total"] == 0


class TestPatternDetection:
    """模式检测测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_file_extension_patterns(self):
        """测试文件扩展名模式"""
        router = ExecutionRouter()
        
        test_cases = [
            ("处理 data.csv", ExecutionPath.MCP_CODE),
            ("读取 config.json", ExecutionPath.MCP_CODE),
            ("导入 file.xlsx", ExecutionPath.MCP_CODE),
            ("解析 data.yaml", ExecutionPath.MCP_CODE),
        ]
        
        for message, expected_path in test_cases:
            decision = router.route(message)
            assert decision.path == expected_path, f"Failed for: {message}"
    
    def test_data_structure_patterns(self):
        """测试数据结构模式"""
        router = ExecutionRouter()
        
        test_cases = [
            ("在 table 中查询",),
            ("处理这个 list",),
            ("遍历和转换 array",),
            ("修改 dictionary 并转换为 JSON",),
        ]
        
        for message, in test_cases:
            decision = router.route(message)
            assert decision.path == ExecutionPath.MCP_CODE
    
    def test_math_operation_patterns(self):
        """测试数学操作模式"""
        router = ExecutionRouter()
        
        test_cases = [
            ("sum(values)",),
            ("count(items)",),
            ("average(scores)",),
            ("max(numbers)",),
        ]
        
        for message, in test_cases:
            decision = router.route(message)
            assert decision.path == ExecutionPath.MCP_CODE


class TestSingletonPattern:
    """单例模式测试"""
    
    def setup_method(self):
        """每个测试前重置全局实例"""
        reset_execution_router()
    
    def test_get_singleton_instance(self):
        """测试获取单例实例"""
        router1 = get_execution_router()
        router2 = get_execution_router()
        
        assert router1 is router2
    
    def test_reset_singleton(self):
        """测试重置单例"""
        router1 = get_execution_router()
        reset_execution_router()
        router2 = get_execution_router()
        
        assert router1 is not router2


class TestRoutingDecision:
    """路由决策对象测试"""
    
    def test_routing_decision_attributes(self):
        """测试路由决策属性"""
        decision = RoutingDecision(
            path=ExecutionPath.MCP_CODE,
            confidence=0.95,
            reason="Test reason",
            fallback_path=ExecutionPath.LLM_REASONING,
        )
        
        assert decision.path == ExecutionPath.MCP_CODE
        assert decision.confidence == 0.95
        assert decision.reason == "Test reason"
        assert decision.fallback_path == ExecutionPath.LLM_REASONING
    
    def test_routing_decision_default_fallback(self):
        """测试默认的降级路径"""
        decision = RoutingDecision(
            path=ExecutionPath.LLM_REASONING,
            confidence=1.0,
            reason="Test",
        )
        
        assert decision.fallback_path is None


class TestEdgeCases:
    """边界情况测试"""
    
    def setup_method(self):
        """每个测试前重置路由器"""
        reset_execution_router()
    
    def test_empty_message(self):
        """测试空消息"""
        router = ExecutionRouter()
        decision = router.route("")
        
        # 应该降级到 LLM 推理
        assert decision.path == ExecutionPath.LLM_REASONING
    
    def test_very_long_message(self):
        """测试很长的消息"""
        router = ExecutionRouter()
        long_message = "这是一条很长的消息。" * 100
        decision = router.route(long_message)
        
        # 应该能够处理
        assert decision.path in [
            ExecutionPath.SKILL,
            ExecutionPath.MCP_CODE,
            ExecutionPath.LLM_REASONING,
        ]
    
    def test_special_characters(self):
        """测试特殊字符"""
        router = ExecutionRouter()
        decision = router.route("查询 @#$%^&*")
        
        # 应该能够处理
        assert decision.path in [
            ExecutionPath.SKILL,
            ExecutionPath.MCP_CODE,
            ExecutionPath.LLM_REASONING,
        ]
    
    def test_mixed_case_keywords(self):
        """测试混合大小写关键词"""
        router = ExecutionRouter()
        
        # 关键词应该不区分大小写
        decision = router.route("Query the CSV")
        assert decision.path == ExecutionPath.MCP_CODE
        
        decision = router.route("QUERY THE CSV")
        assert decision.path == ExecutionPath.MCP_CODE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
