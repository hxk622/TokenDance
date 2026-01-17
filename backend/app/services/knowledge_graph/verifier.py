"""
交叉验证服务

提供:
- 声明验证
- 支持/矛盾来源识别
- 可信度计算
- 冲突检测
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import (
    ClaimVerification,
    Entity,
    EntityType,
    RelationType,
    ResearchKnowledgeGraph,
)
from .query_engine import GraphQueryEngine

logger = logging.getLogger(__name__)


class VerificationVerdict(Enum):
    """验证判定"""
    CONFIRMED = "confirmed"       # 多来源确认
    CONTRADICTED = "contradicted" # 存在矛盾
    PARTIALLY_SUPPORTED = "partially_supported"  # 部分支持
    UNCERTAIN = "uncertain"       # 无法确定
    NO_EVIDENCE = "no_evidence"   # 无相关证据


@dataclass
class SourceCredibility:
    """来源可信度评估"""
    source_id: str
    url: str
    score: float  # 0.0 - 1.0
    factors: dict[str, float]  # 各因素得分


class CrossSourceVerifier:
    """
    交叉来源验证器

    通过比较多个来源的信息来验证声明的可靠性
    """

    def __init__(
        self,
        graph: ResearchKnowledgeGraph | None = None,
        query_engine: GraphQueryEngine | None = None,
        llm_client: Any = None,
        model: str = "gpt-4o-mini"
    ):
        """
        初始化验证器

        Args:
            graph: 知识图谱
            query_engine: 图查询引擎
            llm_client: LLM 客户端 (用于语义比较)
            model: LLM 模型
        """
        self.graph = graph or ResearchKnowledgeGraph()
        self.query_engine = query_engine or GraphQueryEngine(graph=self.graph)
        self.llm_client = llm_client
        self.model = model

        # 来源可信度缓存
        self._credibility_cache: dict[str, float] = {}

    def set_graph(self, graph: ResearchKnowledgeGraph) -> None:
        """设置知识图谱"""
        self.graph = graph
        self.query_engine.set_graph(graph)

    # ==================== 声明验证 ====================

    async def verify_claim(
        self,
        claim: str,
        related_entities: list[str] | None = None
    ) -> ClaimVerification:
        """
        验证声明

        1. 在图谱中查找相关实体
        2. 收集支持和矛盾证据
        3. 计算可信度并做出判定
        """
        # 1. 查找相关实体
        if related_entities:
            entities = [
                self.graph.get_entity_by_name(name)
                for name in related_entities
            ]
            entities = [e for e in entities if e is not None]
        else:
            # 从声明中提取关键词
            from .query_engine import extract_keywords_from_question
            keywords = extract_keywords_from_question(claim)
            entities = self.query_engine.find_entities_by_keywords(keywords)

        if not entities:
            return ClaimVerification(
                claim=claim,
                verdict=VerificationVerdict.NO_EVIDENCE.value,
                confidence=0.0,
                explanation="未找到与声明相关的实体",
            )

        # 2. 收集证据
        supporting_evidence = []
        contradicting_evidence = []

        for entity in entities:
            # 查找与该实体相关的所有关系
            neighbors = self.graph.get_neighbors(entity.id)

            for relation, neighbor in neighbors:
                evidence_text = relation.evidence or neighbor.name
                source_url = self._get_source_url(relation.source_id)

                if relation.type == RelationType.SUPPORTS:
                    supporting_evidence.append((source_url, evidence_text))
                elif relation.type == RelationType.CONTRADICTS:
                    contradicting_evidence.append((source_url, evidence_text))
                elif relation.type in [RelationType.RELATED_TO, RelationType.IS_A, RelationType.PART_OF]:
                    # 使用 LLM 判断是支持还是矛盾
                    if self.llm_client:
                        stance = await self._determine_stance(claim, evidence_text)
                        if stance == "support":
                            supporting_evidence.append((source_url, evidence_text))
                        elif stance == "contradict":
                            contradicting_evidence.append((source_url, evidence_text))

        # 3. 计算可信度和判定
        verdict, confidence, explanation = self._make_verdict(
            claim,
            supporting_evidence,
            contradicting_evidence
        )

        return ClaimVerification(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            explanation=explanation,
        )

    def verify_claim_sync(
        self,
        claim: str,
        related_entities: list[str] | None = None
    ) -> ClaimVerification:
        """
        同步版本的声明验证 (不使用 LLM)
        """
        # 查找相关实体
        if related_entities:
            entities = [
                self.graph.get_entity_by_name(name)
                for name in related_entities
            ]
            entities = [e for e in entities if e is not None]
        else:
            from .query_engine import extract_keywords_from_question
            keywords = extract_keywords_from_question(claim)
            entities = self.query_engine.find_entities_by_keywords(keywords)

        if not entities:
            return ClaimVerification(
                claim=claim,
                verdict=VerificationVerdict.NO_EVIDENCE.value,
                confidence=0.0,
                explanation="未找到与声明相关的实体",
            )

        # 收集证据
        supporting_evidence = []
        contradicting_evidence = []

        for entity in entities:
            neighbors = self.graph.get_neighbors(entity.id)

            for relation, neighbor in neighbors:
                evidence_text = relation.evidence or neighbor.name
                source_url = self._get_source_url(relation.source_id)

                if relation.type == RelationType.SUPPORTS:
                    supporting_evidence.append((source_url, evidence_text))
                elif relation.type == RelationType.CONTRADICTS:
                    contradicting_evidence.append((source_url, evidence_text))

        # 判定
        verdict, confidence, explanation = self._make_verdict(
            claim,
            supporting_evidence,
            contradicting_evidence
        )

        return ClaimVerification(
            claim=claim,
            verdict=verdict,
            confidence=confidence,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            explanation=explanation,
        )

    # ==================== 来源可信度评估 ====================

    def evaluate_source_credibility(self, source_id: str) -> float:
        """
        评估来源可信度

        基于:
        - 域名权威性
        - 被引用次数
        - 与其他来源的一致性
        """
        if source_id in self._credibility_cache:
            return self._credibility_cache[source_id]

        source = self.graph.sources.get(source_id)
        if not source:
            return 0.5  # 默认中等可信度

        score = 0.5

        # 1. 域名评分
        domain_score = self._evaluate_domain(source.url)

        # 2. 引用次数评分 (在图谱中被引用的次数)
        citation_count = self._count_citations(source_id)
        citation_score = min(1.0, citation_count / 10)  # 10 次引用达到满分

        # 3. 一致性评分 (与其他来源的信息是否一致)
        consistency_score = self._evaluate_consistency(source_id)

        # 加权平均
        score = (
            domain_score * 0.4 +
            citation_score * 0.3 +
            consistency_score * 0.3
        )

        self._credibility_cache[source_id] = score
        return score

    def get_source_credibility_details(self, source_id: str) -> SourceCredibility:
        """获取来源可信度详情"""
        source = self.graph.sources.get(source_id)
        url = source.url if source else ""

        domain_score = self._evaluate_domain(url) if url else 0.5
        citation_count = self._count_citations(source_id)
        citation_score = min(1.0, citation_count / 10)
        consistency_score = self._evaluate_consistency(source_id)

        overall_score = (
            domain_score * 0.4 +
            citation_score * 0.3 +
            consistency_score * 0.3
        )

        return SourceCredibility(
            source_id=source_id,
            url=url,
            score=overall_score,
            factors={
                "domain_authority": domain_score,
                "citation_count": citation_score,
                "consistency": consistency_score,
            }
        )

    # ==================== 冲突检测 ====================

    def detect_conflicts(self) -> list[tuple[Entity, Entity, str]]:
        """
        检测图谱中的冲突

        返回: (实体1, 实体2, 冲突描述) 列表
        """
        conflicts = []

        # 查找所有 CONTRADICTS 关系
        for relation in self.graph.relations:
            if relation.type == RelationType.CONTRADICTS:
                source_entity = self.graph.entities.get(relation.source_entity_id)
                target_entity = self.graph.entities.get(relation.target_entity_id)

                if source_entity and target_entity:
                    description = f"'{source_entity.name}' 与 '{target_entity.name}' 存在矛盾"
                    if relation.evidence:
                        description += f": {relation.evidence}"

                    conflicts.append((source_entity, target_entity, description))

        return conflicts

    def find_conflicting_sources(
        self,
        entity_id: str
    ) -> list[tuple[str, str, str]]:
        """
        查找关于某实体的冲突来源

        返回: (来源1 URL, 来源2 URL, 冲突描述) 列表
        """
        conflicts = []

        # 获取所有涉及该实体的关系
        entity_relations = [
            r for r in self.graph.relations
            if r.source_entity_id == entity_id or r.target_entity_id == entity_id
        ]

        # 查找同类型但来自不同来源的关系
        # 如果证据内容明显不同，可能存在冲突
        seen_pairs = set()

        for i, r1 in enumerate(entity_relations):
            for r2 in entity_relations[i+1:]:
                if r1.source_id == r2.source_id:
                    continue

                # 检查是否可能冲突 (同一类型的关系，不同的目标)
                if r1.type == r2.type:
                    other1 = r1.target_entity_id if r1.source_entity_id == entity_id else r1.source_entity_id
                    other2 = r2.target_entity_id if r2.source_entity_id == entity_id else r2.source_entity_id

                    if other1 != other2:
                        pair_key = tuple(sorted([r1.source_id, r2.source_id]))
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)

                            url1 = self._get_source_url(r1.source_id)
                            url2 = self._get_source_url(r2.source_id)

                            e1 = self.graph.entities.get(other1)
                            e2 = self.graph.entities.get(other2)

                            if e1 and e2:
                                conflicts.append((
                                    url1,
                                    url2,
                                    f"关于 {r1.type.value} 关系存在分歧: {e1.name} vs {e2.name}"
                                ))

        return conflicts

    # ==================== 批量验证 ====================

    async def verify_all_claims(self) -> list[ClaimVerification]:
        """验证图谱中的所有声明"""
        results = []

        # 找到所有声明实体
        claim_entities = [
            e for e in self.graph.entities.values()
            if e.type == EntityType.CLAIM
        ]

        for claim_entity in claim_entities:
            full_claim = claim_entity.properties.get("full_claim", claim_entity.name)
            verification = await self.verify_claim(full_claim)
            results.append(verification)

        return results

    def get_verification_summary(
        self,
        verifications: list[ClaimVerification]
    ) -> dict[str, Any]:
        """获取验证摘要"""
        if not verifications:
            return {
                "total": 0,
                "confirmed": 0,
                "contradicted": 0,
                "uncertain": 0,
                "average_confidence": 0.0,
            }

        confirmed = sum(1 for v in verifications if v.verdict == VerificationVerdict.CONFIRMED.value)
        contradicted = sum(1 for v in verifications if v.verdict == VerificationVerdict.CONTRADICTED.value)
        uncertain = sum(1 for v in verifications if v.verdict in [
            VerificationVerdict.UNCERTAIN.value,
            VerificationVerdict.NO_EVIDENCE.value
        ])

        avg_confidence = sum(v.confidence for v in verifications) / len(verifications)

        return {
            "total": len(verifications),
            "confirmed": confirmed,
            "contradicted": contradicted,
            "uncertain": uncertain,
            "average_confidence": avg_confidence,
            "conflicts_found": sum(1 for v in verifications if v.has_conflict),
        }

    # ==================== 私有方法 ====================

    async def _determine_stance(
        self,
        claim: str,
        evidence: str
    ) -> str:
        """使用 LLM 判断证据对声明的立场"""
        if not self.llm_client:
            return "neutral"

        prompt = f"""判断以下证据对声明的立场。

声明: {claim}

证据: {evidence}

请只返回以下之一:
- support: 证据支持声明
- contradict: 证据与声明矛盾
- neutral: 证据与声明无明显关系

只返回一个词，不要解释。"""

        try:
            response = await self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=10,
            )

            result = response.choices[0].message.content.strip().lower()
            if result in ["support", "contradict", "neutral"]:
                return result
            return "neutral"

        except Exception as e:
            logger.error(f"Stance determination failed: {e}")
            return "neutral"

    def _make_verdict(
        self,
        claim: str,
        supporting: list[tuple[str, str]],
        contradicting: list[tuple[str, str]]
    ) -> tuple[str, float, str]:
        """
        做出验证判定

        返回: (判定结果, 置信度, 解释)
        """
        num_support = len(supporting)
        num_contradict = len(contradicting)

        # 收集唯一来源
        support_sources = {s[0] for s in supporting if s[0]}
        contradict_sources = {s[0] for s in contradicting if s[0]}

        if num_support == 0 and num_contradict == 0:
            return (
                VerificationVerdict.NO_EVIDENCE.value,
                0.0,
                "未找到相关证据"
            )

        if num_contradict == 0 and num_support > 0:
            # 只有支持，没有矛盾
            if len(support_sources) >= 3:
                confidence = min(0.95, 0.7 + len(support_sources) * 0.05)
                return (
                    VerificationVerdict.CONFIRMED.value,
                    confidence,
                    f"被 {len(support_sources)} 个独立来源确认"
                )
            elif len(support_sources) >= 1:
                confidence = 0.5 + len(support_sources) * 0.1
                return (
                    VerificationVerdict.PARTIALLY_SUPPORTED.value,
                    confidence,
                    f"被 {len(support_sources)} 个来源支持，但缺乏更多独立验证"
                )

        if num_support == 0 and num_contradict > 0:
            # 只有矛盾，没有支持
            confidence = min(0.9, 0.6 + len(contradict_sources) * 0.1)
            return (
                VerificationVerdict.CONTRADICTED.value,
                confidence,
                f"被 {len(contradict_sources)} 个来源反驳"
            )

        # 既有支持也有矛盾
        if num_support > num_contradict * 2:
            # 支持明显多于矛盾
            confidence = 0.6
            return (
                VerificationVerdict.PARTIALLY_SUPPORTED.value,
                confidence,
                f"多数来源 ({num_support}) 支持，但存在 {num_contradict} 个矛盾证据"
            )
        elif num_contradict > num_support * 2:
            # 矛盾明显多于支持
            confidence = 0.6
            return (
                VerificationVerdict.CONTRADICTED.value,
                confidence,
                f"多数来源 ({num_contradict}) 反驳，仅有 {num_support} 个支持证据"
            )
        else:
            # 势均力敌
            confidence = 0.4
            return (
                VerificationVerdict.UNCERTAIN.value,
                confidence,
                f"证据存在分歧: {num_support} 支持 vs {num_contradict} 反驳"
            )

    def _get_source_url(self, source_id: str) -> str:
        """获取来源 URL"""
        if not source_id:
            return ""
        source = self.graph.sources.get(source_id)
        return source.url if source else ""

    def _evaluate_domain(self, url: str) -> float:
        """评估域名权威性"""
        if not url:
            return 0.5

        # 权威域名列表 (简化版)
        high_authority = {
            "wikipedia.org": 0.85,
            "nature.com": 0.95,
            "science.org": 0.95,
            "sciencedirect.com": 0.9,
            "ieee.org": 0.9,
            "acm.org": 0.9,
            "arxiv.org": 0.85,
            "gov": 0.9,  # 政府网站
            "edu": 0.85,  # 教育机构
            "reuters.com": 0.85,
            "bbc.com": 0.8,
            "nytimes.com": 0.8,
        }

        url_lower = url.lower()

        for domain, score in high_authority.items():
            if domain in url_lower:
                return score

        # 默认中等可信度
        return 0.5

    def _count_citations(self, source_id: str) -> int:
        """计算来源被引用次数"""
        count = 0
        for relation in self.graph.relations:
            if relation.source_id == source_id:
                count += 1

        for entity in self.graph.entities.values():
            if source_id in entity.source_ids:
                count += 1

        return count

    def _evaluate_consistency(self, source_id: str) -> float:
        """评估来源与其他来源的一致性"""
        # 简化实现: 检查该来源提供的信息是否与其他来源矛盾
        contradictions = 0
        agreements = 0

        # 获取该来源相关的所有实体
        source_entities = [
            e for e in self.graph.entities.values()
            if source_id in e.source_ids
        ]

        for entity in source_entities:
            # 检查是否有其他来源也提到这个实体
            other_sources = [s for s in entity.source_ids if s != source_id]
            if other_sources:
                agreements += len(other_sources)

        # 检查矛盾关系
        for relation in self.graph.relations:
            if relation.source_id == source_id and relation.type == RelationType.CONTRADICTS:
                contradictions += 1

        if agreements == 0 and contradictions == 0:
            return 0.5

        # 一致性分数
        total = agreements + contradictions
        return agreements / total if total > 0 else 0.5
