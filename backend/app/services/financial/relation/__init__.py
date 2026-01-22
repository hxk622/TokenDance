"""
关联分析模块

包含：
- 产业链图谱
- 竞争对手分析
- 客户/供应商分析
- 知识图谱
"""
from .competitor_analysis import (
    CompetitionLevel,
    Competitor,
    CompetitorAnalysisResult,
    CompetitorAnalysisService,
    get_competitor_analysis_service,
)
from .customer_supplier import (
    CustomerSupplierRelation,
    CustomerSupplierResult,
    CustomerSupplierService,
    RelationType,
    get_customer_supplier_service,
)
from .knowledge_graph import (
    Entity,
    EntityType,
    KnowledgeGraphResult,
    KnowledgeGraphService,
    Relationship,
    RelationshipType,
    RiskLevel,
    RiskNode,
    RiskPropagationResult,
    RiskType,
    get_knowledge_graph_service,
)
from .supply_chain_map import (
    ChainPosition,
    SupplyChainLink,
    SupplyChainMapResult,
    SupplyChainMapService,
    SupplyChainNode,
    get_supply_chain_map_service,
)

__all__ = [
    # Supply Chain Map
    "SupplyChainMapService",
    "get_supply_chain_map_service",
    "ChainPosition",
    "SupplyChainNode",
    "SupplyChainLink",
    "SupplyChainMapResult",
    # Competitor Analysis
    "CompetitorAnalysisService",
    "get_competitor_analysis_service",
    "CompetitionLevel",
    "Competitor",
    "CompetitorAnalysisResult",
    # Customer Supplier
    "CustomerSupplierService",
    "get_customer_supplier_service",
    "RelationType",
    "CustomerSupplierRelation",
    "CustomerSupplierResult",
    # Knowledge Graph
    "KnowledgeGraphService",
    "get_knowledge_graph_service",
    "EntityType",
    "RelationshipType",
    "Entity",
    "Relationship",
    "KnowledgeGraphResult",
    # Risk Propagation
    "RiskType",
    "RiskLevel",
    "RiskNode",
    "RiskPropagationResult",
]
