"""
KnowledgeGraphService - 知识图谱服务

提供：
1. 实体关系图谱
2. 关联路径查询
3. 影响链分析
4. 风险传导分析 (Risk Propagation)
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

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
    GUARANTEES = "guarantees"       # 担保
    DEBT_TO = "debt_to"             # 负债


class RiskType(str, Enum):
    """风险类型"""
    CREDIT = "credit"               # 信用风险
    LIQUIDITY = "liquidity"         # 流动性风险
    OPERATIONAL = "operational"     # 运营风险
    MARKET = "market"               # 市场风险
    REGULATORY = "regulatory"       # 监管风险
    CONTAGION = "contagion"         # 传导风险


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Entity:
    """实体"""
    entity_id: str
    name: str
    entity_type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
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
    path: list[Entity]
    relationships: list[Relationship]
    path_length: int

    def to_dict(self) -> dict[str, Any]:
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
    entities: list[Entity] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)

    # 统计
    entity_count: int = 0
    relationship_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "center_entity": self.center_entity.to_dict(),
            "analysis_date": self.analysis_date.isoformat(),
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "entity_count": self.entity_count,
            "relationship_count": self.relationship_count,
        }


@dataclass
class RiskNode:
    """风险节点"""
    entity: Entity
    risk_type: RiskType
    risk_level: RiskLevel
    risk_score: float               # 0-100
    is_source: bool                 # 是否为风险源
    propagation_depth: int          # 传导层级 (0=源头)
    propagation_path: list[str]    # 传导路径
    description: str = ""
    mitigation: str = ""           # 建议措施

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity": self.entity.to_dict(),
            "risk_type": self.risk_type.value,
            "risk_level": self.risk_level.value,
            "risk_score": self.risk_score,
            "is_source": self.is_source,
            "propagation_depth": self.propagation_depth,
            "propagation_path": self.propagation_path,
            "description": self.description,
            "mitigation": self.mitigation,
        }


@dataclass
class RiskPropagationResult:
    """风险传导分析结果"""
    symbol: str
    name: str
    analysis_date: datetime

    # 自身风险
    self_risks: list[RiskNode] = field(default_factory=list)

    # 传导风险 (受他人影响)
    incoming_risks: list[RiskNode] = field(default_factory=list)

    # 输出风险 (影响他人)
    outgoing_risks: list[RiskNode] = field(default_factory=list)

    # 统计
    total_risk_score: float = 0.0   # 综合风险分 0-100
    overall_risk_level: RiskLevel = RiskLevel.LOW
    high_risk_count: int = 0
    critical_risk_count: int = 0

    # 风险类型分布
    risk_by_type: dict[str, int] = field(default_factory=dict)

    # 核心洞察
    key_insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "self_risks": [r.to_dict() for r in self.self_risks],
            "incoming_risks": [r.to_dict() for r in self.incoming_risks],
            "outgoing_risks": [r.to_dict() for r in self.outgoing_risks],
            "total_risk_score": self.total_risk_score,
            "overall_risk_level": self.overall_risk_level.value,
            "high_risk_count": self.high_risk_count,
            "critical_risk_count": self.critical_risk_count,
            "risk_by_type": self.risk_by_type,
            "key_insights": self.key_insights,
        }


class KnowledgeGraphService:
    """知识图谱服务"""

    def __init__(self):
        self._cache: dict[str, KnowledgeGraphResult] = {}

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
    ) -> RelationPath | None:
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
        relation_type: RelationshipType | None = None,
    ) -> list[Entity]:
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
    ) -> tuple[list[Entity], list[Relationship]]:
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

    async def analyze_risk_propagation(
        self,
        symbol: str,
    ) -> RiskPropagationResult:
        """
        分析风险传导

        返回：
        - 自身风险 (self_risks)
        - 传导风险 (incoming_risks) - 受他人影响
        - 输出风险 (outgoing_risks) - 影响他人
        """
        try:
            # 获取图谱
            graph = await self.get_entity_graph(symbol, depth=2)

            # 生成自身风险
            self_risks = self._generate_self_risks(symbol)

            # 生成传导风险
            incoming_risks = self._generate_incoming_risks(symbol, graph)

            # 生成输出风险
            outgoing_risks = self._generate_outgoing_risks(symbol, graph)

            # 计算统计
            all_risks = self_risks + incoming_risks + outgoing_risks
            high_count = sum(1 for r in all_risks if r.risk_level == RiskLevel.HIGH)
            critical_count = sum(1 for r in all_risks if r.risk_level == RiskLevel.CRITICAL)

            # 综合风险分
            total_score = self._calculate_total_risk_score(all_risks)

            # 风险类型分布
            risk_by_type: dict[str, int] = {}
            for r in all_risks:
                risk_by_type[r.risk_type.value] = risk_by_type.get(r.risk_type.value, 0) + 1

            # 核心洞察
            insights = self._generate_risk_insights(self_risks, incoming_risks, outgoing_risks)

            return RiskPropagationResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                self_risks=self_risks,
                incoming_risks=incoming_risks,
                outgoing_risks=outgoing_risks,
                total_risk_score=round(total_score, 1),
                overall_risk_level=self._score_to_level(total_score),
                high_risk_count=high_count,
                critical_risk_count=critical_count,
                risk_by_type=risk_by_type,
                key_insights=insights,
            )

        except Exception as e:
            logger.error(f"Failed to analyze risk propagation for {symbol}: {e}")
            return RiskPropagationResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
            )

    def _generate_self_risks(self, symbol: str) -> list[RiskNode]:
        """生成自身风险 (Mock)"""
        risks = []

        # 根据股票生成不同风险
        risk_configs: dict[str, list[dict]] = {
            "600519": [
                {
                    "type": RiskType.MARKET,
                    "level": RiskLevel.MEDIUM,
                    "score": 45,
                    "desc": "白酒行业整体需求放缓，高端白酒竞争加剧",
                    "mitigation": "关注行业动态，适时调整仓位",
                },
                {
                    "type": RiskType.REGULATORY,
                    "level": RiskLevel.LOW,
                    "score": 25,
                    "desc": "酒类监管政策可能趋严",
                    "mitigation": "关注政策变化",
                },
            ],
            "601318": [
                {
                    "type": RiskType.CREDIT,
                    "level": RiskLevel.HIGH,
                    "score": 68,
                    "desc": "地产投资敢口较大，信用风险需重点关注",
                    "mitigation": "密切跟踪地产行业变化及公司资产质量",
                },
                {
                    "type": RiskType.MARKET,
                    "level": RiskLevel.MEDIUM,
                    "score": 52,
                    "desc": "利差收窄压制保险股估值",
                    "mitigation": "关注利率走势和政策变化",
                },
            ],
        }

        configs = risk_configs.get(symbol, [
            {
                "type": RiskType.OPERATIONAL,
                "level": RiskLevel.LOW,
                "score": 30,
                "desc": "常规运营风险",
                "mitigation": "保持关注",
            },
        ])

        for config in configs:
            center_entity = Entity(
                entity_id=symbol,
                name=self._get_stock_name(symbol),
                entity_type=EntityType.COMPANY,
            )
            risks.append(RiskNode(
                entity=center_entity,
                risk_type=config["type"],
                risk_level=config["level"],
                risk_score=config["score"],
                is_source=True,
                propagation_depth=0,
                propagation_path=[symbol],
                description=config["desc"],
                mitigation=config["mitigation"],
            ))

        return risks

    def _generate_incoming_risks(
        self,
        symbol: str,
        graph: KnowledgeGraphResult,
    ) -> list[RiskNode]:
        """生成传导风险 - 受他人影响 (Mock)"""
        risks = []

        # 从图谱中找股东、担保等关系
        for rel in graph.relationships:
            if rel.target_id == symbol and rel.relation_type == RelationshipType.OWNS:
                # 股东风险
                source_entity = next(
                    (e for e in graph.entities if e.entity_id == rel.source_id),
                    None,
                )
                if source_entity:
                    stake_pct = rel.properties.get("stake_pct", 0)
                    if stake_pct > 30:  # 大股东
                        risks.append(RiskNode(
                            entity=source_entity,
                            risk_type=RiskType.CONTAGION,
                            risk_level=RiskLevel.MEDIUM if stake_pct < 50 else RiskLevel.HIGH,
                            risk_score=min(80, stake_pct),
                            is_source=False,
                            propagation_depth=1,
                            propagation_path=[rel.source_id, symbol],
                            description=f"控股股东持股{stake_pct}%，股东风险可能传导",
                            mitigation="关注股东动态及资金状况",
                        ))

        # 添加行业传导风险
        industry_entity = next(
            (e for e in graph.entities if e.entity_type == EntityType.INDUSTRY),
            None,
        )
        if industry_entity:
            risks.append(RiskNode(
                entity=industry_entity,
                risk_type=RiskType.MARKET,
                risk_level=RiskLevel.MEDIUM,
                risk_score=40,
                is_source=False,
                propagation_depth=1,
                propagation_path=[industry_entity.entity_id, symbol],
                description="行业系统性风险可能影响公司表现",
                mitigation="关注行业政策和竞争格局变化",
            ))

        return risks

    def _generate_outgoing_risks(
        self,
        symbol: str,
        graph: KnowledgeGraphResult,
    ) -> list[RiskNode]:
        """生成输出风险 - 影响他人 (Mock)"""
        risks = []

        # 从图谱中找竞争、供应等关系
        for rel in graph.relationships:
            if rel.source_id == symbol and rel.relation_type == RelationshipType.COMPETES:
                target_entity = next(
                    (e for e in graph.entities if e.entity_id == rel.target_id),
                    None,
                )
                if target_entity:
                    risks.append(RiskNode(
                        entity=target_entity,
                        risk_type=RiskType.CONTAGION,
                        risk_level=RiskLevel.LOW,
                        risk_score=25,
                        is_source=False,
                        propagation_depth=1,
                        propagation_path=[symbol, rel.target_id],
                        description=f"竞争关系，可能受{self._get_stock_name(symbol)}价格策略影响",
                        mitigation="保持竞争格局关注",
                    ))

        return risks

    def _calculate_total_risk_score(self, risks: list[RiskNode]) -> float:
        """计算综合风险分"""
        if not risks:
            return 0.0

        # 加权平均，根据传导层级衰减
        total = 0.0
        weight_sum = 0.0

        for risk in risks:
            # 传导层级越深，权重越低
            weight = 1.0 / (1 + risk.propagation_depth * 0.3)
            total += risk.risk_score * weight
            weight_sum += weight

        return total / weight_sum if weight_sum > 0 else 0.0

    def _score_to_level(self, score: float) -> RiskLevel:
        """分数转换为风险等级"""
        if score >= 70:
            return RiskLevel.CRITICAL
        if score >= 50:
            return RiskLevel.HIGH
        if score >= 30:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _generate_risk_insights(
        self,
        self_risks: list[RiskNode],
        incoming_risks: list[RiskNode],
        outgoing_risks: list[RiskNode],
    ) -> list[str]:
        """生成风险洞察"""
        insights = []

        # 分析自身风险
        critical_self = [r for r in self_risks if r.risk_level == RiskLevel.CRITICAL]
        if critical_self:
            insights.append(
                f"存在 {len(critical_self)} 个严重自身风险，建议重点关注"
            )

        high_self = [r for r in self_risks if r.risk_level == RiskLevel.HIGH]
        if high_self:
            types = {r.risk_type.value for r in high_self}
            insights.append(
                f"高风险类型集中在: {', '.join(types)}"
            )

        # 分析传导风险
        if incoming_risks:
            high_incoming = [r for r in incoming_risks if r.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
            if high_incoming:
                sources = [r.entity.name for r in high_incoming[:3]]
                insights.append(
                    f"来自 {', '.join(sources)} 的传导风险需警惕"
                )

        # 分析输出风险
        if len(outgoing_risks) > 3:
            insights.append(
                f"公司风险可能影响 {len(outgoing_risks)} 个关联方"
            )

        if not insights:
            insights.append("整体风险可控，无重大风险预警")

        return insights

    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000568": "泸州老窖",
            "600809": "山西汾酒",
            "600036": "招商银行",
            "000333": "美的集团",
            "601318": "中国平安",
        }
        return names.get(symbol, f"公司{symbol}")


# 全局单例
_knowledge_graph_service: KnowledgeGraphService | None = None


def get_knowledge_graph_service() -> KnowledgeGraphService:
    """获取知识图谱服务单例"""
    global _knowledge_graph_service
    if _knowledge_graph_service is None:
        _knowledge_graph_service = KnowledgeGraphService()
    return _knowledge_graph_service
