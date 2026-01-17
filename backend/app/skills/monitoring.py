"""
Skill 执行监控统计模块

职责：
1. 记录匹配成功率
2. 记录执行耗时
3. 记录 Token 消耗
4. 提供统计查询接口
"""

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MatchEvent:
    """匹配事件"""
    timestamp: float
    query: str
    matched_skill_id: str | None
    score: float
    success: bool
    latency_ms: float
    candidates_count: int = 0


@dataclass
class ExecutionEvent:
    """执行事件"""
    timestamp: float
    skill_id: str
    status: str  # success, failed, timeout
    latency_ms: float
    tokens_used: int
    error: str | None = None


@dataclass
class SkillStats:
    """单个 Skill 的统计数据"""
    skill_id: str
    match_count: int = 0
    match_success_count: int = 0
    execution_count: int = 0
    execution_success_count: int = 0
    execution_failed_count: int = 0
    execution_timeout_count: int = 0
    total_tokens_used: int = 0
    total_match_latency_ms: float = 0.0
    total_execution_latency_ms: float = 0.0

    @property
    def match_success_rate(self) -> float:
        """匹配成功率"""
        if self.match_count == 0:
            return 0.0
        return self.match_success_count / self.match_count

    @property
    def execution_success_rate(self) -> float:
        """执行成功率"""
        if self.execution_count == 0:
            return 0.0
        return self.execution_success_count / self.execution_count

    @property
    def avg_match_latency_ms(self) -> float:
        """平均匹配耗时（毫秒）"""
        if self.match_count == 0:
            return 0.0
        return self.total_match_latency_ms / self.match_count

    @property
    def avg_execution_latency_ms(self) -> float:
        """平均执行耗时（毫秒）"""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_latency_ms / self.execution_count

    @property
    def avg_tokens_per_execution(self) -> float:
        """平均每次执行 Token 消耗"""
        if self.execution_count == 0:
            return 0.0
        return self.total_tokens_used / self.execution_count

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "skill_id": self.skill_id,
            "match": {
                "count": self.match_count,
                "success_count": self.match_success_count,
                "success_rate": round(self.match_success_rate, 4),
                "avg_latency_ms": round(self.avg_match_latency_ms, 2),
            },
            "execution": {
                "count": self.execution_count,
                "success_count": self.execution_success_count,
                "failed_count": self.execution_failed_count,
                "timeout_count": self.execution_timeout_count,
                "success_rate": round(self.execution_success_rate, 4),
                "avg_latency_ms": round(self.avg_execution_latency_ms, 2),
            },
            "tokens": {
                "total_used": self.total_tokens_used,
                "avg_per_execution": round(self.avg_tokens_per_execution, 1),
            },
        }


@dataclass
class GlobalStats:
    """全局统计数据"""
    total_match_requests: int = 0
    total_match_success: int = 0
    total_match_no_match: int = 0
    total_executions: int = 0
    total_execution_success: int = 0
    total_execution_failed: int = 0
    total_execution_timeout: int = 0
    total_tokens_used: int = 0
    total_match_latency_ms: float = 0.0
    total_execution_latency_ms: float = 0.0
    start_time: float = field(default_factory=time.time)

    @property
    def match_success_rate(self) -> float:
        """总匹配成功率"""
        if self.total_match_requests == 0:
            return 0.0
        return self.total_match_success / self.total_match_requests

    @property
    def execution_success_rate(self) -> float:
        """总执行成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.total_execution_success / self.total_executions

    @property
    def avg_match_latency_ms(self) -> float:
        """总平均匹配耗时"""
        if self.total_match_requests == 0:
            return 0.0
        return self.total_match_latency_ms / self.total_match_requests

    @property
    def avg_execution_latency_ms(self) -> float:
        """总平均执行耗时"""
        if self.total_executions == 0:
            return 0.0
        return self.total_execution_latency_ms / self.total_executions

    @property
    def uptime_seconds(self) -> float:
        """运行时间（秒）"""
        return time.time() - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "uptime_seconds": round(self.uptime_seconds, 1),
            "match": {
                "total_requests": self.total_match_requests,
                "success": self.total_match_success,
                "no_match": self.total_match_no_match,
                "success_rate": round(self.match_success_rate, 4),
                "avg_latency_ms": round(self.avg_match_latency_ms, 2),
            },
            "execution": {
                "total": self.total_executions,
                "success": self.total_execution_success,
                "failed": self.total_execution_failed,
                "timeout": self.total_execution_timeout,
                "success_rate": round(self.execution_success_rate, 4),
                "avg_latency_ms": round(self.avg_execution_latency_ms, 2),
            },
            "tokens": {
                "total_used": self.total_tokens_used,
            },
        }


class SkillMonitor:
    """Skill 监控器

    记录和统计 Skill 的匹配和执行情况。
    """

    def __init__(
        self,
        max_events: int = 10000,
        retention_hours: int = 24,
    ):
        """初始化监控器

        Args:
            max_events: 最大事件数量（超过后清理旧事件）
            retention_hours: 事件保留时间（小时）
        """
        self.max_events = max_events
        self.retention_hours = retention_hours

        self._lock = threading.RLock()
        self._match_events: list[MatchEvent] = []
        self._execution_events: list[ExecutionEvent] = []
        self._skill_stats: dict[str, SkillStats] = defaultdict(
            lambda: SkillStats(skill_id="")
        )
        self._global_stats = GlobalStats()

    def record_match(
        self,
        query: str,
        matched_skill_id: str | None,
        score: float,
        latency_ms: float,
        candidates_count: int = 0,
    ) -> None:
        """记录匹配事件

        Args:
            query: 用户查询
            matched_skill_id: 匹配到的 Skill ID（None 表示无匹配）
            score: 匹配分数
            latency_ms: 匹配耗时（毫秒）
            candidates_count: 候选数量
        """
        success = matched_skill_id is not None
        event = MatchEvent(
            timestamp=time.time(),
            query=query[:200],  # 截断过长的查询
            matched_skill_id=matched_skill_id,
            score=score,
            success=success,
            latency_ms=latency_ms,
            candidates_count=candidates_count,
        )

        with self._lock:
            self._match_events.append(event)
            self._cleanup_old_events()

            # 更新全局统计
            self._global_stats.total_match_requests += 1
            self._global_stats.total_match_latency_ms += latency_ms

            if success:
                self._global_stats.total_match_success += 1
                # 更新 Skill 统计
                if matched_skill_id not in self._skill_stats:
                    self._skill_stats[matched_skill_id] = SkillStats(
                        skill_id=matched_skill_id
                    )
                stats = self._skill_stats[matched_skill_id]
                stats.match_count += 1
                stats.match_success_count += 1
                stats.total_match_latency_ms += latency_ms
            else:
                self._global_stats.total_match_no_match += 1

        logger.debug(
            f"Match recorded: skill={matched_skill_id}, "
            f"score={score:.3f}, latency={latency_ms:.1f}ms"
        )

    def record_execution(
        self,
        skill_id: str,
        status: str,
        latency_ms: float,
        tokens_used: int,
        error: str | None = None,
    ) -> None:
        """记录执行事件

        Args:
            skill_id: Skill ID
            status: 执行状态 (success, failed, timeout)
            latency_ms: 执行耗时（毫秒）
            tokens_used: Token 消耗
            error: 错误信息（如果有）
        """
        event = ExecutionEvent(
            timestamp=time.time(),
            skill_id=skill_id,
            status=status,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            error=error[:200] if error else None,
        )

        with self._lock:
            self._execution_events.append(event)
            self._cleanup_old_events()

            # 更新全局统计
            self._global_stats.total_executions += 1
            self._global_stats.total_execution_latency_ms += latency_ms
            self._global_stats.total_tokens_used += tokens_used

            if status == "success":
                self._global_stats.total_execution_success += 1
            elif status == "failed":
                self._global_stats.total_execution_failed += 1
            elif status == "timeout":
                self._global_stats.total_execution_timeout += 1

            # 更新 Skill 统计
            if skill_id not in self._skill_stats:
                self._skill_stats[skill_id] = SkillStats(skill_id=skill_id)
            stats = self._skill_stats[skill_id]
            stats.execution_count += 1
            stats.total_execution_latency_ms += latency_ms
            stats.total_tokens_used += tokens_used

            if status == "success":
                stats.execution_success_count += 1
            elif status == "failed":
                stats.execution_failed_count += 1
            elif status == "timeout":
                stats.execution_timeout_count += 1

        logger.debug(
            f"Execution recorded: skill={skill_id}, status={status}, "
            f"latency={latency_ms:.1f}ms, tokens={tokens_used}"
        )

    def _cleanup_old_events(self) -> None:
        """清理旧事件"""
        cutoff_time = time.time() - (self.retention_hours * 3600)

        # 按时间清理
        self._match_events = [
            e for e in self._match_events
            if e.timestamp > cutoff_time
        ]
        self._execution_events = [
            e for e in self._execution_events
            if e.timestamp > cutoff_time
        ]

        # 按数量限制
        if len(self._match_events) > self.max_events:
            self._match_events = self._match_events[-self.max_events:]
        if len(self._execution_events) > self.max_events:
            self._execution_events = self._execution_events[-self.max_events:]

    def get_global_stats(self) -> dict[str, Any]:
        """获取全局统计"""
        with self._lock:
            return self._global_stats.to_dict()

    def get_skill_stats(self, skill_id: str) -> dict[str, Any] | None:
        """获取单个 Skill 的统计"""
        with self._lock:
            if skill_id in self._skill_stats:
                return self._skill_stats[skill_id].to_dict()
            return None

    def get_all_skill_stats(self) -> dict[str, dict[str, Any]]:
        """获取所有 Skill 的统计"""
        with self._lock:
            return {
                skill_id: stats.to_dict()
                for skill_id, stats in self._skill_stats.items()
            }

    def get_top_skills(
        self,
        by: str = "execution_count",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """获取 Top N Skill

        Args:
            by: 排序字段 (execution_count, match_count, tokens_used)
            limit: 返回数量

        Returns:
            Skill 统计列表
        """
        with self._lock:
            stats_list = list(self._skill_stats.values())

        if by == "execution_count":
            stats_list.sort(key=lambda x: x.execution_count, reverse=True)
        elif by == "match_count":
            stats_list.sort(key=lambda x: x.match_count, reverse=True)
        elif by == "tokens_used":
            stats_list.sort(key=lambda x: x.total_tokens_used, reverse=True)

        return [s.to_dict() for s in stats_list[:limit]]

    def get_recent_events(
        self,
        event_type: str = "all",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """获取最近的事件

        Args:
            event_type: 事件类型 (match, execution, all)
            limit: 返回数量

        Returns:
            事件列表
        """
        with self._lock:
            events = []

            if event_type in ("match", "all"):
                for e in self._match_events[-limit:]:
                    events.append({
                        "type": "match",
                        "timestamp": e.timestamp,
                        "query": e.query,
                        "skill_id": e.matched_skill_id,
                        "score": e.score,
                        "success": e.success,
                        "latency_ms": e.latency_ms,
                    })

            if event_type in ("execution", "all"):
                for e in self._execution_events[-limit:]:
                    events.append({
                        "type": "execution",
                        "timestamp": e.timestamp,
                        "skill_id": e.skill_id,
                        "status": e.status,
                        "latency_ms": e.latency_ms,
                        "tokens_used": e.tokens_used,
                        "error": e.error,
                    })

            # 按时间排序
            events.sort(key=lambda x: x["timestamp"], reverse=True)
            return events[:limit]

    def get_summary(self) -> dict[str, Any]:
        """获取统计摘要"""
        with self._lock:
            return {
                "global": self._global_stats.to_dict(),
                "skills_count": len(self._skill_stats),
                "events": {
                    "match_events": len(self._match_events),
                    "execution_events": len(self._execution_events),
                },
                "top_by_execution": self.get_top_skills("execution_count", 5),
                "top_by_tokens": self.get_top_skills("tokens_used", 5),
            }

    def reset(self) -> None:
        """重置所有统计"""
        with self._lock:
            self._match_events.clear()
            self._execution_events.clear()
            self._skill_stats.clear()
            self._global_stats = GlobalStats()
        logger.info("SkillMonitor reset")


# ============================================================================
# 计时器上下文管理器
# ============================================================================

class MatchTimer:
    """匹配计时器上下文管理器"""

    def __init__(
        self,
        monitor: "SkillMonitor",
        query: str,
    ):
        self.monitor = monitor
        self.query = query
        self.start_time: float = 0
        self.matched_skill_id: str | None = None
        self.score: float = 0.0
        self.candidates_count: int = 0

    def __enter__(self) -> "MatchTimer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        latency_ms = (time.time() - self.start_time) * 1000
        self.monitor.record_match(
            query=self.query,
            matched_skill_id=self.matched_skill_id,
            score=self.score,
            latency_ms=latency_ms,
            candidates_count=self.candidates_count,
        )

    def set_result(
        self,
        skill_id: str | None,
        score: float,
        candidates_count: int = 0,
    ) -> None:
        """设置匹配结果"""
        self.matched_skill_id = skill_id
        self.score = score
        self.candidates_count = candidates_count


class ExecutionTimer:
    """执行计时器上下文管理器"""

    def __init__(
        self,
        monitor: "SkillMonitor",
        skill_id: str,
    ):
        self.monitor = monitor
        self.skill_id = skill_id
        self.start_time: float = 0
        self.status: str = "success"
        self.tokens_used: int = 0
        self.error: str | None = None

    def __enter__(self) -> "ExecutionTimer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        latency_ms = (time.time() - self.start_time) * 1000

        if exc_type is not None:
            self.status = "failed"
            self.error = str(exc_val)

        self.monitor.record_execution(
            skill_id=self.skill_id,
            status=self.status,
            latency_ms=latency_ms,
            tokens_used=self.tokens_used,
            error=self.error,
        )

    def set_result(
        self,
        status: str,
        tokens_used: int,
        error: str | None = None,
    ) -> None:
        """设置执行结果"""
        self.status = status
        self.tokens_used = tokens_used
        self.error = error


# ============================================================================
# 全局单例
# ============================================================================

_global_monitor: SkillMonitor | None = None


def get_skill_monitor() -> SkillMonitor:
    """获取全局 SkillMonitor 单例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = SkillMonitor()
    return _global_monitor


def reset_skill_monitor() -> None:
    """重置全局 SkillMonitor"""
    global _global_monitor
    if _global_monitor:
        _global_monitor.reset()
    _global_monitor = None
