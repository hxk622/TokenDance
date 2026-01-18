"""
失败学习服务 (Failure Tracker)

Keep the Failures 原则:
- 记录所有失败
- 分析失败模式
- 自动调整策略

功能:
1. 域名黑名单管理
2. 查询失败记录
3. 自动查询改写
4. 错误模式识别
"""
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """失败类型"""
    NETWORK_ERROR = "network_error"         # 网络错误
    TIMEOUT = "timeout"                     # 超时
    BLOCKED = "blocked"                     # 被拦截
    NOT_FOUND = "not_found"                 # 404
    RATE_LIMITED = "rate_limited"           # 限流
    EMPTY_CONTENT = "empty_content"         # 空内容
    PARSE_ERROR = "parse_error"             # 解析错误
    NO_RESULTS = "no_results"               # 搜索无结果
    AUTH_REQUIRED = "auth_required"         # 需要认证
    UNKNOWN = "unknown"


@dataclass
class FailureRecord:
    """失败记录"""
    timestamp: float
    failure_type: FailureType
    url: str | None = None
    query: str | None = None
    domain: str | None = None
    error_message: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "failure_type": self.failure_type.value,
            "url": self.url,
            "query": self.query,
            "domain": self.domain,
            "error_message": self.error_message,
            "context": self.context
        }


@dataclass
class DomainStatus:
    """域名状态"""
    domain: str
    failure_count: int = 0
    success_count: int = 0
    last_failure: float | None = None
    last_success: float | None = None
    is_blacklisted: bool = False
    blacklist_until: float | None = None
    failure_types: list[FailureType] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        total = self.failure_count + self.success_count
        return self.success_count / total if total > 0 else 0.5


class FailureTracker:
    """失败追踪器

    特性:
    - 自动域名黑名单
    - 查询失败模式分析
    - 智能查询改写建议
    """

    def __init__(
        self,
        blacklist_threshold: int = 3,
        blacklist_duration: int = 3600,  # 1 小时
        max_records: int = 1000
    ):
        """
        Args:
            blacklist_threshold: 连续失败多少次后加入黑名单
            blacklist_duration: 黑名单持续时间 (秒)
            max_records: 最大记录数
        """
        self.blacklist_threshold = blacklist_threshold
        self.blacklist_duration = blacklist_duration
        self.max_records = max_records

        # 失败记录
        self._records: list[FailureRecord] = []

        # 域名状态
        self._domain_status: dict[str, DomainStatus] = {}

        # 查询失败计数
        self._query_failures: dict[str, int] = defaultdict(int)

        # 统计
        self._stats = {
            "total_failures": 0,
            "domains_blacklisted": 0,
            "queries_rewritten": 0
        }

    def record_failure(
        self,
        failure_type: FailureType,
        url: str | None = None,
        query: str | None = None,
        error_message: str = "",
        context: dict[str, Any] | None = None
    ) -> FailureRecord:
        """记录失败

        Args:
            failure_type: 失败类型
            url: 失败的 URL
            query: 失败的查询
            error_message: 错误信息
            context: 额外上下文

        Returns:
            FailureRecord: 失败记录
        """
        # 提取域名
        domain = None
        if url:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().removeprefix('www.')

        record = FailureRecord(
            timestamp=time.time(),
            failure_type=failure_type,
            url=url,
            query=query,
            domain=domain,
            error_message=error_message,
            context=context or {}
        )

        # 添加记录
        self._records.append(record)

        # LRU 清理
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records:]

        # 更新域名状态
        if domain:
            self._update_domain_status(domain, failure_type)

        # 更新查询失败计数
        if query:
            self._query_failures[query.lower()] += 1

        self._stats["total_failures"] += 1

        logger.info(
            f"Failure recorded: {failure_type.value} "
            f"domain={domain} query={query[:50] if query else None}"
        )

        return record

    def record_success(self, url: str) -> None:
        """记录成功"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower().removeprefix('www.')

        if domain in self._domain_status:
            status = self._domain_status[domain]
            status.success_count += 1
            status.last_success = time.time()

            # 检查是否应该解除黑名单
            if status.is_blacklisted and status.success_rate > 0.5:
                status.is_blacklisted = False
                status.blacklist_until = None
                logger.info(f"Domain {domain} removed from blacklist (success rate improved)")

    def _update_domain_status(self, domain: str, failure_type: FailureType) -> None:
        """更新域名状态"""
        if domain not in self._domain_status:
            self._domain_status[domain] = DomainStatus(domain=domain)

        status = self._domain_status[domain]
        status.failure_count += 1
        status.last_failure = time.time()
        status.failure_types.append(failure_type)

        # 保留最近 10 个失败类型
        status.failure_types = status.failure_types[-10:]

        # 检查是否应该加入黑名单
        recent_failures = [
            r for r in self._records
            if r.domain == domain and time.time() - r.timestamp < 600  # 10分钟内
        ]

        if len(recent_failures) >= self.blacklist_threshold:
            if not status.is_blacklisted:
                status.is_blacklisted = True
                status.blacklist_until = time.time() + self.blacklist_duration
                self._stats["domains_blacklisted"] += 1
                logger.warning(f"Domain {domain} blacklisted ({len(recent_failures)} failures)")

    def is_blacklisted(self, url: str) -> bool:
        """检查 URL 是否在黑名单中"""
        parsed = urlparse(url)
        domain = parsed.netloc.lower().removeprefix('www.')

        if domain not in self._domain_status:
            return False

        status = self._domain_status[domain]

        if not status.is_blacklisted:
            return False

        # 检查是否已过期
        if status.blacklist_until and time.time() > status.blacklist_until:
            status.is_blacklisted = False
            status.blacklist_until = None
            logger.info(f"Domain {domain} blacklist expired")
            return False

        return True

    def get_blacklisted_domains(self) -> list[str]:
        """获取当前黑名单域名"""
        blacklisted = []
        for domain, status in self._domain_status.items():
            if status.is_blacklisted:
                if status.blacklist_until and time.time() > status.blacklist_until:
                    status.is_blacklisted = False
                else:
                    blacklisted.append(domain)
        return blacklisted

    def should_retry_query(self, query: str) -> tuple[bool, str]:
        """检查是否应该重试查询，并提供建议

        Returns:
            Tuple[bool, str]: (是否应该重试, 重写建议)
        """
        query_lower = query.lower()
        failure_count = self._query_failures.get(query_lower, 0)

        if failure_count == 0:
            return True, query

        if failure_count >= 3:
            # 尝试改写查询
            rewritten = self._rewrite_query(query)
            self._stats["queries_rewritten"] += 1
            return True, rewritten

        return True, query

    def _rewrite_query(self, query: str) -> str:
        """改写失败的查询

        策略:
        1. 移除过于具体的限定词
        2. 简化长查询
        3. 尝试同义词替换
        """
        # 移除时间限定
        rewritten = re.sub(
            r'\b(2020|2021|2022|2023|2024|2025|2026|recent|latest|new)\b',
            '',
            query,
            flags=re.IGNORECASE
        )

        # 移除过于具体的限定
        rewritten = re.sub(
            r'\b(exact|specific|detailed|comprehensive)\b',
            '',
            rewritten,
            flags=re.IGNORECASE
        )

        # 简化长查询
        words = rewritten.split()
        if len(words) > 10:
            # 保留前 8 个词
            rewritten = ' '.join(words[:8])

        # 清理多余空格
        rewritten = re.sub(r'\s+', ' ', rewritten).strip()

        if rewritten != query:
            logger.info(f"Query rewritten: '{query[:50]}' -> '{rewritten[:50]}'")

        return rewritten if rewritten else query

    def classify_error(self, error: Exception) -> FailureType:
        """根据异常类型分类失败"""
        error_str = str(error).lower()

        if 'timeout' in error_str:
            return FailureType.TIMEOUT

        if 'connection' in error_str or 'network' in error_str:
            return FailureType.NETWORK_ERROR

        if '404' in error_str or 'not found' in error_str:
            return FailureType.NOT_FOUND

        if '403' in error_str or 'forbidden' in error_str or 'blocked' in error_str:
            return FailureType.BLOCKED

        if '429' in error_str or 'rate limit' in error_str or 'too many' in error_str:
            return FailureType.RATE_LIMITED

        if '401' in error_str or 'unauthorized' in error_str or 'auth' in error_str:
            return FailureType.AUTH_REQUIRED

        if 'parse' in error_str or 'decode' in error_str or 'json' in error_str:
            return FailureType.PARSE_ERROR

        if 'empty' in error_str or 'no content' in error_str:
            return FailureType.EMPTY_CONTENT

        if 'no results' in error_str:
            return FailureType.NO_RESULTS

        return FailureType.UNKNOWN

    def get_failure_patterns(self) -> dict[str, Any]:
        """获取失败模式分析"""
        if not self._records:
            return {"patterns": [], "recommendations": []}

        # 统计失败类型
        type_counts = defaultdict(int)
        for record in self._records[-100:]:  # 最近 100 条
            type_counts[record.failure_type.value] += 1

        # 识别主要模式
        patterns = []
        recommendations = []

        total = sum(type_counts.values())

        for ftype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            if count / total > 0.2:  # 超过 20%
                patterns.append({
                    "type": ftype,
                    "count": count,
                    "percentage": round(count / total * 100, 1)
                })

        # 生成建议
        if type_counts.get(FailureType.TIMEOUT.value, 0) / total > 0.3:
            recommendations.append("Consider increasing timeout values")

        if type_counts.get(FailureType.RATE_LIMITED.value, 0) / total > 0.2:
            recommendations.append("Implement request throttling or use multiple search providers")

        if type_counts.get(FailureType.BLOCKED.value, 0) / total > 0.2:
            recommendations.append("Some sources are blocking requests - consider using proxies")

        if type_counts.get(FailureType.NO_RESULTS.value, 0) / total > 0.3:
            recommendations.append("Queries may be too specific - try broader search terms")

        return {
            "patterns": patterns,
            "recommendations": recommendations,
            "total_analyzed": total
        }

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "records_count": len(self._records),
            "domains_tracked": len(self._domain_status),
            "current_blacklist": self.get_blacklisted_domains(),
            "patterns": self.get_failure_patterns()
        }

    def clear(self) -> None:
        """清空所有记录"""
        self._records.clear()
        self._domain_status.clear()
        self._query_failures.clear()
        self._stats = {
            "total_failures": 0,
            "domains_blacklisted": 0,
            "queries_rewritten": 0
        }


# 全局实例
_global_tracker: FailureTracker | None = None


def get_failure_tracker() -> FailureTracker:
    """获取全局失败追踪器"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = FailureTracker()
    return _global_tracker


def record_failure(
    failure_type: FailureType,
    url: str | None = None,
    query: str | None = None,
    error_message: str = ""
) -> FailureRecord:
    """记录失败 (便捷函数)"""
    return get_failure_tracker().record_failure(
        failure_type=failure_type,
        url=url,
        query=query,
        error_message=error_message
    )
