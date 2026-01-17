# -*- coding: utf-8 -*-
"""
关联分析模块

包含：
- 产业链图谱
- 竞争对手分析
- 客户/供应商分析
- 知识图谱
"""
from .supply_chain_map import (
    SupplyChainMapService,
    get_supply_chain_map_service,
    ChainPosition,
    SupplyChainNode,
    SupplyChainLink,
    SupplyChainMapResult,
)
from .competitor_analysis import (
    CompetitorAnalysisService,
    get_competitor_analysis_service,
    CompetitionLevel,
    Competitor,
    CompetitorAnalysisResult,
)
from .customer_supplier import (
    CustomerSupplierService,
    get_customer_supplier_service,
    RelationType,
    CustomerSupplierRelation,
    CustomerSupplierResult,
)
from .knowledge_graph import (
    KnowledgeGraphService,
    get_knowledge_graph_service,
    EntityType,
    RelationshipType,
    Entity,
    Relationship,
    KnowledgeGraphResult,
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
]
