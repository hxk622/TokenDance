"""
Context Graph 统一服务

提供:
- 内存模式 (默认，无需 Neo4j)
- Neo4j 模式 (可选，高性能持久化)
- 失败信号系统
- 决策轨迹记录
"""

from .failure_observer import (
    FailureObserver,
    FailureSignal,
    FailureTaxonomy,
    RecoveryStrategy,
)
from .service import (
    ContextGraphService,
    DecisionTrace,
    get_context_graph_service,
)

__all__ = [
    # Service
    "ContextGraphService",
    "get_context_graph_service",
    "DecisionTrace",
    # Failure
    "FailureObserver",
    "FailureSignal",
    "FailureTaxonomy",
    "RecoveryStrategy",
]
