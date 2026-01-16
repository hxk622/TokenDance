"""
Root Cause Analyzer - 失败根因分析

基于 FailureSignal 序列进行因果聚合、模式分类与修复策略建议。
参考 AGENT_ROBUSTNESS_ASSESSMENT.md 阶段 2.1。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from collections import Counter

from .signal import FailureSignal, FailureType


@dataclass
class RootCause:
    category: str
    confidence: float
    reasons: List[str]
    strategies: List[str]


class RootCauseAnalyzer:
    """对失败链进行聚合分析，输出根因类别与修复策略。"""

    CATEGORY_MAP: Dict[str, List[FailureType]] = {
        "timeout": [FailureType.TIMEOUT],
        "permission": [FailureType.PERMISSION_DENIED],
        "rate_limit": [FailureType.RATE_LIMITED],
        "network": [FailureType.NETWORK_ERROR],
        "input_error": [FailureType.INVALID_PARAMS, FailureType.VALIDATION_FAILED],
        "not_found": [FailureType.RESOURCE_NOT_FOUND],
        "logic": [FailureType.EXECUTION_ERROR],
    }

    STRATEGY_LIBRARY: Dict[str, List[str]] = {
        "timeout": ["增加超时时间", "降低并发/请求量", "分批处理", "使用缓存", "退避重试(backoff)"],
        "permission": ["验证权限/令牌", "使用替代工具", "请求人工授权(HITL)"],
        "rate_limit": ["实施指数退避", "排队处理", "切换备用API/密钥"],
        "network": ["检测网络/代理", "重试与超时", "切换数据源"],
        "input_error": ["校验与清洗输入", "提示用户确认", "提供样例输入"],
        "not_found": ["校验路径/URL", "回退到搜索/索引", "请求用户选择"],
        "logic": ["改变执行路径", "缩小问题范围", "请求更高层次目标澄清"],
    }

    def analyze(self, failure_chain: List[FailureSignal]) -> Optional[RootCause]:
        if not failure_chain:
            return None

        # 仅聚合失败项
        failures = [f for f in failure_chain if not f.is_success()]
        if not failures:
            return None

        # 统计失败类型与工具
        type_counts = Counter([f.failure_type for f in failures])
        tool_counts = Counter([f.tool_name for f in failures if f.tool_name])

        # 推断类别
        category, cat_conf, reasons = self._infer_category(type_counts, tool_counts)

        # 策略推荐
        strategies = self.STRATEGY_LIBRARY.get(category, ["重试", "请求帮助"])

        return RootCause(category=category, confidence=cat_conf, reasons=reasons, strategies=strategies)

    def _infer_category(
        self,
        type_counts: Counter,
        tool_counts: Counter,
    ) -> Tuple[str, float, List[str]]:
        # 将 FailureType 映射到类别票数
        cat_votes: Counter = Counter()
        reasons: List[str] = []
        total = sum(type_counts.values()) or 1
        for ftype, cnt in type_counts.items():
            for cat, types in self.CATEGORY_MAP.items():
                if ftype in types:
                    cat_votes[cat] += cnt
                    reasons.append(f"{cat}: {ftype.value} x{cnt}")

        # 默认逻辑错误
        if not cat_votes:
            return "logic", 0.5, ["fallback: execution_error"]

        best_cat, best_cnt = cat_votes.most_common(1)[0]
        confidence = min(1.0, best_cnt / total + (0.1 if len(tool_counts) == 1 else 0.0))
        return best_cat, confidence, reasons
