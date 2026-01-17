"""
Knowledge Graph 服务模块

用于 Deep Research v3.0 的 Graph RAG 实现:
- 知识图谱数据模型
- Neo4j 存储服务
- 图谱构建 (实体/关系抽取)
- 多跳查询引擎
- 交叉验证服务
"""

from .builder import (
    KnowledgeGraphBuilder,
    create_source_from_search_result,
)
from .models import (
    ClaimVerification,
    ConfidenceLevel,
    Entity,
    EntityType,
    MultiHopResult,
    ReasoningPath,
    Relation,
    RelationType,
    ResearchKnowledgeGraph,
    ResearchSource,
)
from .query_engine import (
    GraphQueryEngine,
    QueryContext,
    extract_keywords_from_question,
)
from .storage import (
    Neo4jStorage,
    close_neo4j_storage,
    get_neo4j_storage,
)
from .verifier import (
    CrossSourceVerifier,
    SourceCredibility,
    VerificationVerdict,
)

__all__ = [
    # Models
    "EntityType",
    "RelationType",
    "ConfidenceLevel",
    "Entity",
    "Relation",
    "ResearchSource",
    "ResearchKnowledgeGraph",
    "ReasoningPath",
    "MultiHopResult",
    "ClaimVerification",
    # Storage
    "Neo4jStorage",
    "get_neo4j_storage",
    "close_neo4j_storage",
    # Builder
    "KnowledgeGraphBuilder",
    "create_source_from_search_result",
    # Query Engine
    "GraphQueryEngine",
    "QueryContext",
    "extract_keywords_from_question",
    # Verifier
    "CrossSourceVerifier",
    "SourceCredibility",
    "VerificationVerdict",
]
