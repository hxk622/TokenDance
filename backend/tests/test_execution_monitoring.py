"""
执行监控模块的单元测试

测试 ExecutionMonitor 的功能：
- 记录执行统计
- 计算成功率
- 生成性能报告
- 导出统计数据
"""

import pytest
import json
import tempfile
from pathlib import Path

from app.monitoring import (
    ExecutionMonitor,
    ExecutionStats,
    ExecutionMetrics,
    get_execution_monitor,
    clear_monitor,
    clear_all_monitors,
)
from app.context.unified_context import ExecutionType, ExecutionStatus


class TestExecutionMetrics:
    """测试 ExecutionMetrics 类"""
    
    def test_metrics_initialization(self):
        """测试指标初始化"""
        metrics = ExecutionMetrics(path="skill")
        assert metrics.path == "skill"
        assert metrics.total_count == 0
        assert metrics.success_count == 0
        assert metrics.success_rate == 0.0
        assert metrics.avg_time_ms == 0.0
    
    def test_success_rate_calculation(self):
        """测试成功率计算"""
        metrics = ExecutionMetrics(path="mcp")
        metrics.total_count = 10
        metrics.success_count = 8
        
        assert metrics.success_rate == 0.8
        assert metrics.failure_count == 0
    
    def test_average_time_calculation(self):
        """测试平均时间计算"""
        metrics = ExecutionMetrics(path="llm")
        metrics.total_count = 5
        metrics.total_time_ms = 500.0
        
        assert metrics.avg_time_ms == 100.0
    
    def test_min_max_time_tracking(self):
        """测试最小/最大时间追踪"""
        metrics = ExecutionMetrics(path="skill")
        metrics.min_time_ms = 10.5
        metrics.max_time_ms = 95.3
        
        assert metrics.min_time_ms == 10.5
        assert metrics.max_time_ms == 95.3
    
    def test_metrics_to_dict(self):
        """测试指标转换为字典"""
        metrics = ExecutionMetrics(path="mcp")
        metrics.total_count = 10
        metrics.success_count = 9
        metrics.failure_count = 1
        metrics.total_time_ms = 4500.0
        metrics.min_time_ms = 400.0
        metrics.max_time_ms = 600.0
        
        data = metrics.to_dict()
        assert data["path"] == "mcp"
        assert data["total_count"] == 10
        assert data["success_count"] == 9
        assert "90.00%" in data["success_rate"]
        assert data["error_types"] == {}


class TestExecutionMonitor:
    """测试 ExecutionMonitor 类"""
    
    @pytest.fixture
    def monitor(self):
        """创建监控器实例"""
        clear_all_monitors()
        return ExecutionMonitor(session_id="test_session_1")
    
    def test_monitor_initialization(self, monitor):
        """测试监控器初始化"""
        assert monitor.stats.session_id == "test_session_1"
        assert monitor.stats.total_executions == 0
        assert monitor.stats.total_success == 0
        assert monitor.stats.total_failure == 0
    
    def test_record_execution_success(self, monitor):
        """测试记录成功的执行"""
        monitor.record_execution(
            execution_type=ExecutionType.SKILL,
            status=ExecutionStatus.SUCCESS,
            duration_ms=50.5,
        )
        
        assert monitor.stats.total_executions == 1
        assert monitor.stats.total_success == 1
        assert monitor.stats.total_failure == 0
        assert monitor.stats.skill_metrics.success_count == 1
    
    def test_record_execution_failure(self, monitor):
        """测试记录失败的执行"""
        monitor.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            status=ExecutionStatus.FAILED,
            duration_ms=100.0,
            error_type="timeout",
        )
        
        assert monitor.stats.total_executions == 1
        assert monitor.stats.total_success == 0
        assert monitor.stats.total_failure == 1
        assert monitor.stats.mcp_metrics.failure_count == 1
        assert monitor.stats.mcp_metrics.error_types["timeout"] == 1
    
    def test_multiple_executions(self, monitor):
        """测试记录多个执行"""
        # 记录 Skill 执行
        monitor.record_execution(
            execution_type=ExecutionType.SKILL,
            status=ExecutionStatus.SUCCESS,
            duration_ms=50.0,
        )
        monitor.record_execution(
            execution_type=ExecutionType.SKILL,
            status=ExecutionStatus.FAILED,
            duration_ms=60.0,
            error_type="not_found",
        )
        
        # 记录 MCP 执行
        monitor.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            status=ExecutionStatus.SUCCESS,
            duration_ms=200.0,
        )
        monitor.record_execution(
            execution_type=ExecutionType.MCP_CODE,
            status=ExecutionStatus.SUCCESS,
            duration_ms=300.0,
        )
        
        # 记录 LLM 执行
        monitor.record_execution(
            execution_type=ExecutionType.LLM_REASONING,
            status=ExecutionStatus.SUCCESS,
            duration_ms=500.0,
        )
        
        # 验证统计
        assert monitor.stats.total_executions == 5
        assert monitor.stats.total_success == 4
        assert monitor.stats.total_failure == 1
        
        # 验证路径分布
        assert monitor.stats.skill_metrics.total_count == 2
        assert monitor.stats.mcp_metrics.total_count == 2
        assert monitor.stats.llm_metrics.total_count == 1
    
    def test_path_distribution(self, monitor):
        """测试执行路径分布计算"""
        # 创建不平衡的分布
        for _ in range(5):
            monitor.record_execution(
                execution_type=ExecutionType.SKILL,
                status=ExecutionStatus.SUCCESS,
                duration_ms=50.0,
            )
        
        for _ in range(3):
            monitor.record_execution(
                execution_type=ExecutionType.MCP_CODE,
                status=ExecutionStatus.SUCCESS,
                duration_ms=200.0,
            )
        
        for _ in range(2):
            monitor.record_execution(
                execution_type=ExecutionType.LLM_REASONING,
                status=ExecutionStatus.SUCCESS,
                duration_ms=500.0,
            )
        
        distribution = monitor.get_path_distribution()
        assert distribution["skill"] == 0.5
        assert distribution["mcp"] == 0.3
        assert distribution["llm"] == 0.2
    
    def test_success_rates(self, monitor):
        """测试按路径的成功率计算"""
        # Skill: 1/2 = 50%
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 50.0)
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.FAILED, 60.0, "error")
        
        # MCP: 3/4 = 75%
        for _ in range(3):
            monitor.record_execution(ExecutionType.MCP_CODE, ExecutionStatus.SUCCESS, 200.0)
        monitor.record_execution(ExecutionType.MCP_CODE, ExecutionStatus.FAILED, 250.0, "error")
        
        # LLM: 2/2 = 100%
        for _ in range(2):
            monitor.record_execution(ExecutionType.LLM_REASONING, ExecutionStatus.SUCCESS, 500.0)
        
        rates = monitor.get_success_rates()
        assert rates["skill"] == 0.5
        assert rates["mcp"] == 0.75
        assert rates["llm"] == 1.0
        assert rates["overall"] == 6/8  # 6 success out of 8 total
    
    def test_latency_statistics(self, monitor):
        """测试延迟统计"""
        # 记录不同延迟的执行
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 30.0)
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 50.0)
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 70.0)
        
        latency = monitor.get_latency_stats()
        assert latency["skill"]["min_ms"] == 30.0
        assert latency["skill"]["max_ms"] == 70.0
        assert latency["skill"]["avg_ms"] == 50.0
    
    def test_error_summary(self, monitor):
        """测试错误摘要"""
        monitor.record_execution(
            ExecutionType.SKILL,
            ExecutionStatus.FAILED,
            50.0,
            error_type="not_found"
        )
        monitor.record_execution(
            ExecutionType.SKILL,
            ExecutionStatus.FAILED,
            50.0,
            error_type="not_found"
        )
        monitor.record_execution(
            ExecutionType.MCP_CODE,
            ExecutionStatus.FAILED,
            200.0,
            error_type="timeout"
        )
        
        errors = monitor.get_error_summary()
        assert errors["skill"]["not_found"] == 2
        assert errors["mcp"]["timeout"] == 1
        assert "timeout" not in errors["skill"]
    
    def test_generate_report(self, monitor):
        """测试生成性能报告"""
        # 创建一些执行记录
        for _ in range(3):
            monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 50.0)
        
        for _ in range(2):
            monitor.record_execution(ExecutionType.MCP_CODE, ExecutionStatus.SUCCESS, 200.0)
        
        monitor.record_execution(ExecutionType.MCP_CODE, ExecutionStatus.FAILED, 250.0, "error")
        
        report = monitor.generate_report()
        
        # 验证报告包含关键信息
        assert "Agent Execution Performance Report" in report
        assert "test_session_1" in report
        assert "Total Executions:     6" in report
        assert "Success:              5" in report
        assert "Failure:              1" in report
    
    def test_export_json(self, monitor):
        """测试导出为 JSON"""
        # 记录一些执行
        monitor.record_execution(ExecutionType.SKILL, ExecutionStatus.SUCCESS, 50.0)
        monitor.record_execution(ExecutionType.MCP_CODE, ExecutionStatus.FAILED, 200.0, "error")
        
        # 导出到临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            monitor.export_json(str(filepath))
            
            # 验证文件存在并包含正确数据
            assert filepath.exists()
            
            with open(filepath) as f:
                data = json.load(f)
            
            assert data["stats"]["session_id"] == "test_session_1"
            assert data["stats"]["total_executions"] == 2
            assert data["stats"]["total_success"] == 1
            assert data["stats"]["total_failure"] == 1
            assert len(data["execution_records"]) == 2


class TestExecutionMonitorSingleton:
    """测试监控器单例模式"""
    
    def test_get_execution_monitor_singleton(self):
        """测试获取单例监控器"""
        clear_all_monitors()
        
        monitor1 = get_execution_monitor("session_1")
        monitor2 = get_execution_monitor("session_1")
        
        assert monitor1 is monitor2
    
    def test_multiple_sessions(self):
        """测试多个会话的监控器隔离"""
        clear_all_monitors()
        
        monitor1 = get_execution_monitor("session_1")
        monitor2 = get_execution_monitor("session_2")
        
        assert monitor1 is not monitor2
        assert monitor1.stats.session_id == "session_1"
        assert monitor2.stats.session_id == "session_2"
    
    def test_clear_monitor(self):
        """测试清除单个监控器"""
        clear_all_monitors()
        
        monitor1 = get_execution_monitor("session_1")
        monitor2 = get_execution_monitor("session_2")
        
        clear_monitor("session_1")
        
        # session_1 应该创建新的监控器
        monitor1_new = get_execution_monitor("session_1")
        assert monitor1_new is not monitor1
        
        # session_2 应该保持不变
        monitor2_same = get_execution_monitor("session_2")
        assert monitor2_same is monitor2
    
    def test_clear_all_monitors(self):
        """测试清除所有监控器"""
        clear_all_monitors()
        
        monitor1 = get_execution_monitor("session_1")
        monitor2 = get_execution_monitor("session_2")
        
        clear_all_monitors()
        
        # 应该创建新的监控器
        monitor1_new = get_execution_monitor("session_1")
        monitor2_new = get_execution_monitor("session_2")
        
        assert monitor1_new is not monitor1
        assert monitor2_new is not monitor2


class TestExecutionStats:
    """测试 ExecutionStats 类"""
    
    def test_stats_to_dict(self):
        """测试统计转换为字典"""
        stats = ExecutionStats(session_id="test_session")
        stats.total_executions = 10
        stats.total_success = 8
        stats.total_failure = 2
        
        stats.skill_metrics.total_count = 5
        stats.skill_metrics.success_count = 5
        
        data = stats.to_dict()
        assert data["session_id"] == "test_session"
        assert data["total_executions"] == 10
        assert data["total_success"] == 8
        assert data["total_failure"] == 2
        assert "80.00%" in data["overall_success_rate"]
