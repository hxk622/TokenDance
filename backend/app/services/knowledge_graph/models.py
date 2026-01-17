"""
Knowledge Graph 数据模型

定义知识图谱的核心数据结构:
- Entity: 实体节点 (人物、组织、概念等)
- Relation: 关系边 (支持、矛盾、引用等)
- ResearchKnowledgeGraph: 知识图谱容器
- ReasoningPath: 推理路径
- MultiHopResult: 多跳查询结果
- ClaimVerification: 声明验证结果
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EntityType(Enum):
    """实体类型"""
    PERSON = "person"           # 人物
    ORGANIZATION = "org"        # 组织/公司
    CONCEPT = "concept"         # 概念/术语
    EVENT = "event"             # 事件
    PRODUCT = "product"         # 产品/技术
    LOCATION = "location"       # 地点
    DOCUMENT = "document"       # 文档/来源
    CLAIM = "claim"             # 声明/论断
    DATA_POINT = "data_point"   # 数据点/统计


class RelationType(Enum):
    """关系类型"""
    # 人物关系
    WORKS_FOR = "works_for"         # A works for B
    FOUNDED = "founded"             # A founded B
    AUTHORED = "authored"           # A authored B
    LEADS = "leads"                 # A leads B

    # 概念关系
    IS_A = "is_a"                   # A is a type of B
    PART_OF = "part_of"             # A is part of B
    RELATED_TO = "related_to"       # A is related to B
    COMPARED_TO = "compared_to"     # A compared to B
    DEPENDS_ON = "depends_on"       # A depends on B

    # 时间关系
    PRECEDED_BY = "preceded_by"     # A preceded by B
    FOLLOWED_BY = "followed_by"     # A followed by B
    CONCURRENT_WITH = "concurrent_with"  # A concurrent with B

    # 来源关系
    CITED_IN = "cited_in"           # A is cited in B
    EXTRACTED_FROM = "extracted_from"  # A extracted from B

    # 证据关系 (用于交叉验证)
    SUPPORTS = "supports"           # A supports claim B
    CONTRADICTS = "contradicts"     # A contradicts B
    REFINES = "refines"             # A refines/extends B
    NEUTRAL = "neutral"             # A neither supports nor contradicts B


class ConfidenceLevel(Enum):
    """可信度等级"""
    HIGH = "high"           # 多来源一致确认
    MEDIUM = "medium"       # 部分来源支持
    LOW = "low"             # 单一来源或存在矛盾
    UNCERTAIN = "uncertain" # 无法确定


@dataclass
class Entity:
    """
    知识图谱实体

    Attributes:
        id: 唯一标识符
        name: 实体名称
        type: 实体类型
        properties: 附加属性 (如: description, aliases, url)
        embedding: 向量表示 (用于语义相似度)
        source_ids: 来源文档 ID 列表 (溯源)
        confidence: 置信度 (0.0 - 1.0)
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: str
    name: str
    type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    source_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        name: str,
        entity_type: EntityType,
        source_id: str | None = None,
        **properties
    ) -> "Entity":
        """工厂方法: 创建新实体"""
        return cls(
            id=str(uuid.uuid4()),
            name=name,
            type=entity_type,
            properties=properties,
            source_ids=[source_id] if source_id else [],
        )

    def merge_with(self, other: "Entity") -> None:
        """合并另一个实体的信息 (实体消歧后)"""
        # 合并来源
        for sid in other.source_ids:
            if sid not in self.source_ids:
                self.source_ids.append(sid)

        # 合并属性 (新属性优先)
        for key, value in other.properties.items():
            if key not in self.properties:
                self.properties[key] = value

        # 更新置信度 (更多来源 = 更高置信度)
        self.confidence = min(1.0, self.confidence + 0.1)
        self.updated_at = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (用于序列化)"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "properties": self.properties,
            "source_ids": self.source_ids,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entity":
        """从字典创建实体"""
        return cls(
            id=data["id"],
            name=data["name"],
            type=EntityType(data["type"]),
            properties=data.get("properties", {}),
            source_ids=data.get("source_ids", []),
            confidence=data.get("confidence", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )


@dataclass
class Relation:
    """
    知识图谱关系

    Attributes:
        id: 唯一标识符
        source_entity_id: 源实体 ID
        target_entity_id: 目标实体 ID
        type: 关系类型
        properties: 附加属性
        evidence: 支持证据 (原文摘录)
        source_id: 来源文档 ID
        confidence: 置信度
        created_at: 创建时间
    """
    id: str
    source_entity_id: str
    target_entity_id: str
    type: RelationType
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: str = ""
    source_id: str = ""
    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(
        cls,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        evidence: str = "",
        doc_source_id: str = "",
        **properties
    ) -> "Relation":
        """工厂方法: 创建新关系"""
        return cls(
            id=str(uuid.uuid4()),
            source_entity_id=source_id,
            target_entity_id=target_id,
            type=relation_type,
            properties=properties,
            evidence=evidence,
            source_id=doc_source_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "source_entity_id": self.source_entity_id,
            "target_entity_id": self.target_entity_id,
            "type": self.type.value,
            "properties": self.properties,
            "evidence": self.evidence,
            "source_id": self.source_id,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relation":
        """从字典创建关系"""
        return cls(
            id=data["id"],
            source_entity_id=data["source_entity_id"],
            target_entity_id=data["target_entity_id"],
            type=RelationType(data["type"]),
            properties=data.get("properties", {}),
            evidence=data.get("evidence", ""),
            source_id=data.get("source_id", ""),
            confidence=data.get("confidence", 1.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
        )


@dataclass
class ResearchSource:
    """研究来源 (与 deep_research.py 中的定义兼容)"""
    id: str
    url: str
    title: str
    snippet: str
    content: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    credibility_score: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "credibility_score": self.credibility_score,
        }


@dataclass
class ResearchKnowledgeGraph:
    """
    研究知识图谱

    包含实体、关系和来源的完整图谱结构
    支持内存操作和 Neo4j 持久化
    """
    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)
    sources: dict[str, ResearchSource] = field(default_factory=dict)

    # 索引结构 (加速查询)
    _name_to_entity: dict[str, str] = field(default_factory=dict)  # name -> entity_id
    _adjacency: dict[str, list[tuple[str, str]]] = field(default_factory=dict)  # entity_id -> [(relation_id, target_id)]

    def add_entity(self, entity: Entity) -> str:
        """添加实体"""
        self.entities[entity.id] = entity

        # 更新名称索引
        name_key = entity.name.lower().strip()
        self._name_to_entity[name_key] = entity.id

        # 初始化邻接表
        if entity.id not in self._adjacency:
            self._adjacency[entity.id] = []

        return entity.id

    def add_relation(self, relation: Relation) -> str:
        """添加关系"""
        self.relations.append(relation)

        # 更新邻接表 (双向)
        if relation.source_entity_id not in self._adjacency:
            self._adjacency[relation.source_entity_id] = []
        self._adjacency[relation.source_entity_id].append(
            (relation.id, relation.target_entity_id)
        )

        # 反向边 (用于双向遍历)
        if relation.target_entity_id not in self._adjacency:
            self._adjacency[relation.target_entity_id] = []
        self._adjacency[relation.target_entity_id].append(
            (relation.id, relation.source_entity_id)
        )

        return relation.id

    def add_source(self, source: ResearchSource) -> str:
        """添加来源"""
        self.sources[source.id] = source
        return source.id

    def get_entity_by_name(self, name: str) -> Entity | None:
        """按名称查找实体"""
        name_key = name.lower().strip()
        entity_id = self._name_to_entity.get(name_key)
        return self.entities.get(entity_id) if entity_id else None

    def get_neighbors(self, entity_id: str) -> list[tuple[Relation, Entity]]:
        """获取实体的所有邻居"""
        neighbors = []
        for relation_id, neighbor_id in self._adjacency.get(entity_id, []):
            # 找到关系
            relation = next((r for r in self.relations if r.id == relation_id), None)
            neighbor = self.entities.get(neighbor_id)
            if relation and neighbor:
                neighbors.append((relation, neighbor))
        return neighbors

    def find_similar_entity(self, name: str, threshold: float = 0.8) -> Entity | None:
        """
        查找相似实体 (用于实体消歧)
        使用简单的字符串匹配，可扩展为向量相似度
        """
        name_lower = name.lower().strip()

        # 精确匹配
        if name_lower in self._name_to_entity:
            return self.entities[self._name_to_entity[name_lower]]

        # 模糊匹配 (Jaccard 相似度)
        name_tokens = set(name_lower.split())
        best_match = None
        best_score = 0.0

        for existing_name, entity_id in self._name_to_entity.items():
            existing_tokens = set(existing_name.split())
            if not existing_tokens:
                continue

            intersection = len(name_tokens & existing_tokens)
            union = len(name_tokens | existing_tokens)
            score = intersection / union if union > 0 else 0

            if score > best_score and score >= threshold:
                best_score = score
                best_match = self.entities[entity_id]

        return best_match

    def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        entity_types = {}
        for entity in self.entities.values():
            entity_types[entity.type.value] = entity_types.get(entity.type.value, 0) + 1

        relation_types = {}
        for relation in self.relations:
            relation_types[relation.type.value] = relation_types.get(relation.type.value, 0) + 1

        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "total_sources": len(self.sources),
            "entity_types": entity_types,
            "relation_types": relation_types,
        }

    def to_dict(self) -> dict[str, Any]:
        """序列化为字典"""
        return {
            "entities": {eid: e.to_dict() for eid, e in self.entities.items()},
            "relations": [r.to_dict() for r in self.relations],
            "sources": {sid: s.to_dict() for sid, s in self.sources.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchKnowledgeGraph":
        """从字典反序列化"""
        graph = cls()

        for entity_data in data.get("entities", {}).values():
            entity = Entity.from_dict(entity_data)
            graph.add_entity(entity)

        for relation_data in data.get("relations", []):
            relation = Relation.from_dict(relation_data)
            graph.relations.append(relation)
            # 重建邻接表
            if relation.source_entity_id in graph.entities:
                graph._adjacency.setdefault(relation.source_entity_id, []).append(
                    (relation.id, relation.target_entity_id)
                )
            if relation.target_entity_id in graph.entities:
                graph._adjacency.setdefault(relation.target_entity_id, []).append(
                    (relation.id, relation.source_entity_id)
                )

        return graph


@dataclass
class ReasoningPath:
    """
    推理路径

    记录从起始实体到目标实体的推理链
    """
    entities: list[Entity]
    relations: list[Relation]
    score: float = 0.0  # 路径质量评分

    def __str__(self) -> str:
        """可读的路径表示"""
        if not self.entities:
            return "(empty path)"

        parts = [self.entities[0].name]
        for i, relation in enumerate(self.relations):
            if i + 1 < len(self.entities):
                parts.append(f" --[{relation.type.value}]--> ")
                parts.append(self.entities[i + 1].name)

        return "".join(parts)

    def get_evidence(self) -> list[str]:
        """获取路径上的所有证据"""
        return [r.evidence for r in self.relations if r.evidence]


@dataclass
class MultiHopResult:
    """
    多跳查询结果
    """
    answer: str                           # 综合答案
    paths: list[ReasoningPath]            # 推理路径
    confidence: float                     # 整体置信度
    entities_involved: list[Entity] = field(default_factory=list)  # 涉及的实体
    sources_used: list[str] = field(default_factory=list)          # 使用的来源

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "paths": [str(p) for p in self.paths],
            "confidence": self.confidence,
            "entities_involved": [e.name for e in self.entities_involved],
            "sources_used": self.sources_used,
        }


@dataclass
class ClaimVerification:
    """
    声明验证结果
    """
    claim: str                                    # 原始声明
    verdict: str                                  # 判定: confirmed, contradicted, uncertain
    confidence: float                             # 置信度
    supporting_evidence: list[tuple[str, str]] = field(default_factory=list)    # (来源, 证据)
    contradicting_evidence: list[tuple[str, str]] = field(default_factory=list) # (来源, 证据)
    explanation: str = ""                         # 解释

    @property
    def has_conflict(self) -> bool:
        """是否存在矛盾"""
        return len(self.supporting_evidence) > 0 and len(self.contradicting_evidence) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "verdict": self.verdict,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "contradicting_evidence": self.contradicting_evidence,
            "has_conflict": self.has_conflict,
            "explanation": self.explanation,
        }
