# -*- coding: utf-8 -*-
"""
KnowledgeGraphService - 知识图谱服务

提供：
1. 实体关系图谱
2. 关联路径查询
3. 影响链分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """实体类型"""
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    INDUSTRY = "industry"
    EVENT = "event"
    LOCATION = "location"


class RelationshipType(str, Enum):
    """关系类型"""
    OWNS = "owns"                   # 持股
    CONTROLS = "controls"           # 控制
    SUPPLIES = "supplies"           # 供应
    COMPETES = "competes"           # 竞争
    COOPERATES = "cooperates"       # 合作
    MANAGES = "manages"             # 管理
    INVESTS = "invests"             # 投资
    BELONGS_TO = "belongs_to"       # 属于


@dataclass
class Entity:
    """实体"""
    entity_id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "entity_type": self.entity_type.value,
            "properties": self.properties,
        }


@dataclass
class Relationship:
    """关系"""
    source_id: str
    target_id: str
    relation_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type.value,
            "properties": self.properties,
            "weight": self.weight,
        }


@dataclass
class RelationPath:
    """关系路径"""
    source: Entity
    target: Entity
    path: List[Entity]
    relationships: List[Relationship]
    path_length: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "path": [e.to_dict() for e in self.path],
            "relationships": [r.to_dict() for r in self.relationships],
            "path_length": self.path_length,
        }


@dataclass
class KnowledgeGraphResult:
    """知识图谱结果"""
    center_entity: Entity
    analysis_date: datetime
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    
    # 统计
    entity_count: int = 0
    relationship_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "center_entity": self.center_entity.to_dict(),
            "analysis_date": self.analysis_date.isoformat(),
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "entity_count": self.entity_count,
            "relationship_count": self.relationship_count,
        }


class KnowledgeGraphService:
    """知识图谱服务"""
    
    def __init__(self):
        self._cache: Dict[str, KnowledgeGraphResult] = {}
    
    async def get_entity_graph(
        self,
        symbol: str,
        depth: int = 2,
    ) -> KnowledgeGraphResult:
        """获取实体关系图谱"""
        cache_key = f"{symbol}:{depth}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            # 中心实体
            center = Entity(
                entity_id=symbol,
                name=self._get_stock_name(symbol),
                entity_type=EntityType.COMPANY,
                properties={"symbol": symbol},
            )
            
            # 构建图谱
            entities, relationships = await self._build_graph(symbol, depth)
            
            result = KnowledgeGraphResult(
                center_entity=center,
                analysis_date=datetime.now(),
                entities=entities,
                relationships=relationships,
                entity_count=len(entities),
                relationship_count=len(relationships),
            )
            
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error(f"Failed to get entity graph for {symbol}: {e}")
            return KnowledgeGraphResult(
                center_entity=Entity(entity_id=symbol, name="", entity_type=EntityType.COMPANY),
                analysis_date=datetime.now(),
            )
    
    async def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 4,
    ) -> Optional[RelationPath]:
        """查找两个实体间的关系路径"""
        # Mock 实现
        source = Entity(
            entity_id=source_id,
            name=self._get_stock_name(source_id),
            entity_type=EntityType.COMPANY,
        )
        target = Entity(
            entity_id=target_id,
            name=self._get_stock_name(target_id),
            entity_type=EntityType.COMPANY,
        )
        
        # 模拟中间节点
        intermediate = Entity(
            entity_id="industry_consumer",
            name="消费行业",
            entity_type=EntityType.INDUSTRY,
        )
        
        return RelationPath(
            source=source,
            target=target,
            path=[source, intermediate, target],
            relationships=[
                Relationship(
                    source_id=source_id,
                    target_id="industry_consumer",
                    relation_type=RelationshipType.BELONGS_TO,
                ),
                Relationship(
                    source_id="industry_consumer",
                    target_id=target_id,
                    relation_type=RelationshipType.BELONGS_TO,
                ),
            ],
            path_length=2,
        )
    
    async def get_related_entities(
        self,
        symbol: str,
        relation_type: Optional[RelationshipType] = None,
    ) -> List[Entity]:
        """获取相关实体"""
        graph = await self.get_entity_graph(symbol, depth=1)
        
        if relation_type:
            related_ids = set()
            for rel in graph.relationships:
                if rel.relation_type == relation_type:
                    if rel.source_id == symbol:
                        related_ids.add(rel.target_id)
                    else:
                        related_ids.add(rel.source_id)
            
            return [e for e in graph.entities if e.entity_id in related_ids]
        
        return graph.entities
    
    async def _build_graph(
        self,
        symbol: str,
        depth: int,
    ) -> tuple[List[Entity], List[Relationship]]:
        """构建图谱"""
        import random
        
        entities = []
        relationships = []
        
        # 添加关联公司
        related_companies = [
            ("000858", "五粮液", RelationshipType.COMPETES),
            ("000568", "泸州老窖", RelationshipType.COMPETES),
            ("600809", "山西汾酒", RelationshipType.COMPETES),
        ]
        
        for comp_symbol, comp_name, rel_type in related_companies:
            entity = Entity(
                entity_id=comp_symbol,
                name=comp_name,
                entity_type=EntityType.COMPANY,
                properties={"symbol": comp_symbol},
            )
            entities.append(entity)
            
            relationships.append(Relationship(
                source_id=symbol,
                target_id=comp_symbol,
                relation_type=rel_type,
                weight=round(random.uniform(0.5, 1.0), 2),
            ))
        
        # 添加行业
        industry = Entity(
            entity_id="industry_baijiu",
            name="白酒行业",
            entity_type=EntityType.INDUSTRY,
        )
        entities.append(industry)
        relationships.append(Relationship(
            source_id=symbol,
            target_id="industry_baijiu",
            relation_type=RelationshipType.BELONGS_TO,
        ))
        
        # 添加管理层
        executives = [
            ("exec_1", "董事长"),
            ("exec_2", "总经理"),
            ("exec_3", "财务总监"),
        ]
        
        for exec_id, title in executives:
            entity = Entity(
                entity_id=exec_id,
                name=f"{self._get_stock_name(symbol)}{title}",
                entity_type=EntityType.PERSON,
                properties={"title": title},
            )
            entities.append(entity)
            
            relationships.append(Relationship(
                source_id=exec_id,
                target_id=symbol,
                relation_type=RelationshipType.MANAGES,
            ))
        
        # 添加股东
        shareholders = [
            ("sh_1", "控股股东", 60),
            ("sh_2", "战略投资者", 10),
        ]
        
        for sh_id, sh_name, stake in shareholders:
            entity = Entity(
                entity_id=sh_id,
                name=sh_name,
                entity_type=EntityType.COMPANY,
                properties={"stake_pct": stake},
            )
            entities.append(entity)
            
            relationships.append(Relationship(
                source_id=sh_id,
                target_id=symbol,
                relation_type=RelationshipType.OWNS,
                properties={"stake_pct": stake},
            ))
        
        return entities, relationships
    
    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000568": "泸州老窖",
            "600809": "山西汾酒",
            "600036": "招商银行",
            "000333": "美的集团",
        }
        return names.get(symbol, f"公司{symbol}")


# 全局单例
_knowledge_graph_service: Optional[KnowledgeGraphService] = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """获取知识图谱服务单例"""
    global _knowledge_graph_service
    if _knowledge_graph_service is None:
        _knowledge_graph_service = KnowledgeGraphService()
    return _knowledge_graph_service
