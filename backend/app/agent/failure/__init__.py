"""
Failure Module - 失败信号系统

实现铁律四：智能来自失败，不来自理解

核心组件：
- FailureSignal: 失败信号数据结构
- FailureObserver: 失败观察者
- FailureSummary: 失败摘要（用于 Plan Recitation）
"""

from .observer import (
    FailureCallback,
    FailureObserver,
    FailureReporter,
)
from .pattern_kb import FailurePattern, FailurePatternKB
from .root_cause import RootCause, RootCauseAnalyzer
from .signal import (
    ExitCode,
    FailureSignal,
    FailureSource,
    FailureSummary,
    FailureType,
)

__all__ = [
    # Signal
    "FailureSignal",
    "FailureSummary",
    "FailureSource",
    "FailureType",
    "ExitCode",
    # Observer
    "FailureObserver",
    "FailureReporter",
    "FailureCallback",
    # Root cause & pattern KB (Phase 2)
    "RootCauseAnalyzer",
    "RootCause",
    "FailurePatternKB",
    "FailurePattern",
]
