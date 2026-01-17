"""
Agent 执行统计和监控模块

负责追踪和分析 Agent 的执行性能，包括：
- 执行路径分布（Skill/MCP/LLM）
- 成功率统计（按路径分别计算）
- 执行延迟追踪（平均/最小/最大）
- 错误分析和分类
- 实时性能报告生成
"""

import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.context.unified_context import ExecutionStatus, ExecutionType

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """单个执行路径的性能指标"""
    path: str
    total_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_time_ms: float = 0.0  # 总执行时间（毫秒）
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    error_types: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def success_rate(self) -> float:
        """成功率（0-1）"""
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    @property
    def avg_time_ms(self) -> float:
        """平均执行时间（毫秒）"""
        if self.total_count == 0:
            return 0.0
        return self.total_time_ms / self.total_count

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "path": self.path,
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": f"{self.success_rate:.2%}",
            "avg_time_ms": f"{self.avg_time_ms:.2f}",
            "min_time_ms": f"{self.min_time_ms:.2f}" if self.min_time_ms != float('inf') else "N/A",
            "max_time_ms": f"{self.max_time_ms:.2f}",
            "error_types": dict(self.error_types),
        }


@dataclass
class ExecutionStats:
    """整体执行统计"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)

    # 按执行路径的指标
    skill_metrics: ExecutionMetrics = field(default_factory=lambda: ExecutionMetrics("skill"))
    mcp_metrics: ExecutionMetrics = field(default_factory=lambda: ExecutionMetrics("mcp"))
    llm_metrics: ExecutionMetrics = field(default_factory=lambda: ExecutionMetrics("llm"))

    # 整体统计
    total_executions: int = 0
    total_success: int = 0
    total_failure: int = 0

    def get_metric(self, execution_type: ExecutionType) -> ExecutionMetrics:
        """根据执行类型获取对应的指标"""
        if execution_type == ExecutionType.SKILL:
            return self.skill_metrics
        elif execution_type == ExecutionType.MCP_CODE:
            return self.mcp_metrics
        elif execution_type == ExecutionType.LLM_REASONING:
            return self.llm_metrics
        else:
            raise ValueError(f"Unknown execution type: {execution_type}")

    @property
    def overall_success_rate(self) -> float:
        """整体成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.total_success / self.total_executions

    @property
    def total_time(self) -> timedelta:
        """总执行时间"""
        return datetime.now() - self.start_time

    def to_dict(self) -> dict:
        """转换为字典格式（便于序列化和报告）"""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "total_time": str(self.total_time),
            "total_executions": self.total_executions,
            "total_success": self.total_success,
            "total_failure": self.total_failure,
            "overall_success_rate": f"{self.overall_success_rate:.2%}",
            "skill_metrics": self.skill_metrics.to_dict(),
            "mcp_metrics": self.mcp_metrics.to_dict(),
            "llm_metrics": self.llm_metrics.to_dict(),
        }


class ExecutionMonitor:
    """
    Agent 执行监控器

    用于记录和分析 Agent 的执行性能，包括：
    - 执行路径分布
    - 成功率统计
    - 延迟分析
    - 错误追踪
    """

    def __init__(self, session_id: str):
        """
        初始化监控器

        Args:
            session_id: Session ID
        """
        self.stats = ExecutionStats(session_id=session_id)
        self._execution_records: list[dict] = []

    def record_execution(
        self,
        execution_type: ExecutionType,
        status: ExecutionStatus,
        duration_ms: float,
        error_type: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        记录一次执行

        Args:
            execution_type: 执行类型（SKILL/MCP/LLM）
            status: 执行状态（SUCCESS/FAILED）
            duration_ms: 执行耗时（毫秒）
            error_type: 错误类型（如果失败）
            metadata: 额外的元数据
        """
        # 更新总体统计
        self.stats.total_executions += 1
        if status == ExecutionStatus.SUCCESS:
            self.stats.total_success += 1
        else:
            self.stats.total_failure += 1

        # 获取执行路径的指标
        metrics = self.stats.get_metric(execution_type)
        metrics.total_count += 1

        if status == ExecutionStatus.SUCCESS:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
            if error_type:
                metrics.error_types[error_type] += 1

        # 更新执行时间统计
        metrics.total_time_ms += duration_ms
        metrics.min_time_ms = min(metrics.min_time_ms, duration_ms)
        metrics.max_time_ms = max(metrics.max_time_ms, duration_ms)

        # 记录详细信息
        record = {
            "timestamp": datetime.now().isoformat(),
            "execution_type": execution_type.value,
            "status": status.value,
            "duration_ms": duration_ms,
            "error_type": error_type,
            "metadata": metadata or {},
        }
        self._execution_records.append(record)

        logger.debug(f"Recorded execution: {execution_type.value} {status.value} {duration_ms:.2f}ms")

    def get_stats(self) -> ExecutionStats:
        """获取当前统计信息"""
        return self.stats

    def get_path_distribution(self) -> dict[str, float]:
        """获取执行路径分布（百分比）"""
        total = self.stats.total_executions
        if total == 0:
            return {"skill": 0.0, "mcp": 0.0, "llm": 0.0}

        return {
            "skill": self.stats.skill_metrics.total_count / total,
            "mcp": self.stats.mcp_metrics.total_count / total,
            "llm": self.stats.llm_metrics.total_count / total,
        }

    def get_success_rates(self) -> dict[str, float]:
        """按执行路径获取成功率"""
        return {
            "skill": self.stats.skill_metrics.success_rate,
            "mcp": self.stats.mcp_metrics.success_rate,
            "llm": self.stats.llm_metrics.success_rate,
            "overall": self.stats.overall_success_rate,
        }

    def get_latency_stats(self) -> dict[str, dict[str, float]]:
        """获取延迟统计（单位：毫秒）"""
        def format_metrics(m: ExecutionMetrics) -> dict[str, float]:
            return {
                "avg_ms": round(m.avg_time_ms, 2),
                "min_ms": round(m.min_time_ms, 2) if m.min_time_ms != float('inf') else 0,
                "max_ms": round(m.max_time_ms, 2),
            }

        return {
            "skill": format_metrics(self.stats.skill_metrics),
            "mcp": format_metrics(self.stats.mcp_metrics),
            "llm": format_metrics(self.stats.llm_metrics),
        }

    def get_error_summary(self) -> dict[str, dict[str, int]]:
        """获取错误摘要（按执行路径分类）"""
        return {
            "skill": dict(self.stats.skill_metrics.error_types),
            "mcp": dict(self.stats.mcp_metrics.error_types),
            "llm": dict(self.stats.llm_metrics.error_types),
        }

    def generate_report(self) -> str:
        """生成性能报告"""
        stats = self.stats
        distribution = self.get_path_distribution()
        success_rates = self.get_success_rates()
        latency = self.get_latency_stats()
        errors = self.get_error_summary()

        report = f"""
╔══════════════════════════════════════════════════════════════════╗
║            Agent Execution Performance Report                    ║
╚══════════════════════════════════════════════════════════════════╝

📊 OVERVIEW
────────────────────────────────────────────────────────────────────
Session ID:           {stats.session_id}
Total Time:           {stats.total_time}
Total Executions:     {stats.total_executions}
Success:              {stats.total_success} ({stats.overall_success_rate:.1%})
Failure:              {stats.total_failure}

📈 PATH DISTRIBUTION
────────────────────────────────────────────────────────────────────
Skill Path:           {distribution['skill']:>6.1%} ({stats.skill_metrics.total_count} executions)
MCP Path:             {distribution['mcp']:>6.1%} ({stats.mcp_metrics.total_count} executions)
LLM Path:             {distribution['llm']:>6.1%} ({stats.llm_metrics.total_count} executions)

✅ SUCCESS RATES BY PATH
────────────────────────────────────────────────────────────────────
Skill Path:           {success_rates['skill']:>6.1%} ({stats.skill_metrics.success_count}/{stats.skill_metrics.total_count})
MCP Path:             {success_rates['mcp']:>6.1%} ({stats.mcp_metrics.success_count}/{stats.mcp_metrics.total_count})
LLM Path:             {success_rates['llm']:>6.1%} ({stats.llm_metrics.success_count}/{stats.llm_metrics.total_count})
Overall:              {success_rates['overall']:>6.1%}

⏱️  LATENCY STATISTICS (milliseconds)
────────────────────────────────────────────────────────────────────
Skill Path:
  Average:            {latency['skill']['avg_ms']:>8.2f} ms
  Min:                {latency['skill']['min_ms']:>8.2f} ms
  Max:                {latency['skill']['max_ms']:>8.2f} ms

MCP Path:
  Average:            {latency['mcp']['avg_ms']:>8.2f} ms
  Min:                {latency['mcp']['min_ms']:>8.2f} ms
  Max:                {latency['mcp']['max_ms']:>8.2f} ms

LLM Path:
  Average:            {latency['llm']['avg_ms']:>8.2f} ms
  Min:                {latency['llm']['min_ms']:>8.2f} ms
  Max:                {latency['llm']['max_ms']:>8.2f} ms

❌ ERROR ANALYSIS
────────────────────────────────────────────────────────────────────
Skill Errors:
{self._format_error_dict(errors['skill'])}
MCP Errors:
{self._format_error_dict(errors['mcp'])}
LLM Errors:
{self._format_error_dict(errors['llm'])}

🎯 KEY INSIGHTS
────────────────────────────────────────────────────────────────────
• Fastest Path:       Skill ({latency['skill']['avg_ms']:.1f}ms avg)
• Most Used Path:     {max(distribution, key=distribution.get).upper()}
• Most Reliable:      {max(success_rates, key=lambda x: success_rates[x] if x != 'overall' else 0).upper()} ({max([success_rates[k] for k in ['skill', 'mcp', 'llm']]):.1%})
"""

        return report

    @staticmethod
    def _format_error_dict(errors: dict[str, int]) -> str:
        """格式化错误字典"""
        if not errors:
            return "  • No errors\n"

        lines = []
        for error_type, count in sorted(errors.items(), key=lambda x: -x[1]):
            lines.append(f"  • {error_type}: {count}")
        return "\n".join(lines) + "\n"

    def export_json(self, filepath: str) -> None:
        """导出统计数据为 JSON 文件"""
        data = {
            "stats": self.stats.to_dict(),
            "path_distribution": self.get_path_distribution(),
            "success_rates": self.get_success_rates(),
            "latency_stats": self.get_latency_stats(),
            "error_summary": self.get_error_summary(),
            "execution_records": self._execution_records,
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Exported execution stats to {filepath}")

    def print_summary(self) -> None:
        """打印执行摘要"""
        stats = self.stats
        print(f"\n✅ Session: {stats.session_id}")
        print(f"   Total: {stats.total_executions} | Success: {stats.total_success} | Failed: {stats.total_failure}")
        print(f"   Success Rate: {stats.overall_success_rate:.1%}")

        # 按路径显示
        for metrics in [stats.skill_metrics, stats.mcp_metrics, stats.llm_metrics]:
            if metrics.total_count > 0:
                print(f"   {metrics.path.upper()}: {metrics.total_count} executions, " +
                      f"{metrics.success_rate:.1%} success rate, {metrics.avg_time_ms:.2f}ms avg")


# 全局监控器实例字典（key: session_id）
_monitors: dict[str, ExecutionMonitor] = {}


def get_execution_monitor(session_id: str) -> ExecutionMonitor:
    """获取或创建执行监控器（单例）"""
    if session_id not in _monitors:
        _monitors[session_id] = ExecutionMonitor(session_id)
    return _monitors[session_id]


def clear_monitor(session_id: str) -> None:
    """清除指定 session 的监控器"""
    if session_id in _monitors:
        del _monitors[session_id]


def clear_all_monitors() -> None:
    """清除所有监控器"""
    _monitors.clear()
