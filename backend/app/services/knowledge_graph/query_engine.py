"""
多跳查询引擎

提供:
- BFS/DFS 图遍历
- 推理路径查找
- 路径评分
- 答案综合
"""

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any

from .models import (
    Entity,
    MultiHopResult,
    ReasoningPath,
    Relation,
    RelationType,
    ResearchKnowledgeGraph,
)
from .storage import Neo4jStorage

logger = logging.getLogger(__name__)


@dataclass
class QueryContext:
    """查询上下文"""
    question: str
    keywords: list[str]
    max_hops: int = 3
    max_paths: int = 5
    relation_weights: dict[RelationType, float] = None

    def __post_init__(self):
        if self.relation_weights is None:
            # 默认关系权重 (用于路径评分)
            self.relation_weights = {
                RelationType.SUPPORTS: 1.0,
                RelationType.IS_A: 0.9,
                RelationType.PART_OF: 0.85,
                RelationType.RELATED_TO: 0.7,
                RelationType.CONTRADICTS: 0.5,  # 矛盾关系得分较低
            }


class GraphQueryEngine:
    """
    图查询引擎

    支持:
    - 基于内存图谱的查询
    - 基于 Neo4j 的查询 (用于大规模图谱)
    - 多跳推理
    - 路径发现
    """

    def __init__(
        self,
        graph: ResearchKnowledgeGraph | None = None,
        neo4j_storage: Neo4jStorage | None = None
    ):
        """
        初始化查询引擎

        Args:
            graph: 内存图谱 (小规模查询)
            neo4j_storage: Neo4j 存储 (大规模查询)
        """
        self.graph = graph or ResearchKnowledgeGraph()
        self.neo4j_storage = neo4j_storage

    def set_graph(self, graph: ResearchKnowledgeGraph) -> None:
        """设置内存图谱"""
        self.graph = graph

    # ==================== 实体查询 ====================

    def find_entities_by_keywords(
        self,
        keywords: list[str],
        limit: int = 10
    ) -> list[Entity]:
        """
        按关键词查找实体

        使用简单的字符串匹配
        """
        results = []

        for entity in self.graph.entities.values():
            name_lower = entity.name.lower()
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    results.append(entity)
                    break

        # 按相关度排序 (名称越短越相关)
        results.sort(key=lambda e: len(e.name))

        return results[:limit]

    async def find_entities_by_keywords_neo4j(
        self,
        keywords: list[str],
        limit: int = 10
    ) -> list[Entity]:
        """使用 Neo4j 按关键词查找实体"""
        if not self.neo4j_storage:
            return self.find_entities_by_keywords(keywords, limit)

        results = []
        for keyword in keywords:
            entities = await self.neo4j_storage.search_entities(keyword, limit=limit)
            results.extend(entities)

        # 去重
        seen = set()
        unique = []
        for entity in results:
            if entity.id not in seen:
                seen.add(entity.id)
                unique.append(entity)

        return unique[:limit]

    # ==================== 路径查找 ====================

    def find_paths_bfs(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 3
    ) -> list[ReasoningPath]:
        """
        BFS 查找最短路径

        适用于找到最直接的连接
        """
        if start_entity_id not in self.graph.entities:
            return []
        if end_entity_id not in self.graph.entities:
            return []
        if start_entity_id == end_entity_id:
            return [ReasoningPath(
                entities=[self.graph.entities[start_entity_id]],
                relations=[],
                score=1.0
            )]

        # BFS 状态: (当前实体 ID, 路径实体列表, 路径关系列表)
        queue = deque([(start_entity_id, [start_entity_id], [])])
        visited = {start_entity_id}
        paths = []

        while queue and len(paths) < 5:  # 最多找 5 条路径
            current_id, entity_path, relation_path = queue.popleft()

            if len(entity_path) > max_hops + 1:
                continue

            # 获取邻居
            neighbors = self.graph.get_neighbors(current_id)

            for relation, neighbor in neighbors:
                if neighbor.id == end_entity_id:
                    # 找到目标
                    full_entity_path = entity_path + [neighbor.id]
                    full_relation_path = relation_path + [relation]

                    path = ReasoningPath(
                        entities=[self.graph.entities[eid] for eid in full_entity_path],
                        relations=full_relation_path,
                    )
                    path.score = self._calculate_path_score(path)
                    paths.append(path)

                elif neighbor.id not in visited and len(entity_path) < max_hops:
                    visited.add(neighbor.id)
                    queue.append((
                        neighbor.id,
                        entity_path + [neighbor.id],
                        relation_path + [relation]
                    ))

        # 按分数排序
        paths.sort(key=lambda p: p.score, reverse=True)

        return paths

    def find_paths_dfs(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 3
    ) -> list[ReasoningPath]:
        """
        DFS 查找所有路径

        适用于探索多种可能的连接方式
        """
        if start_entity_id not in self.graph.entities:
            return []
        if end_entity_id not in self.graph.entities:
            return []

        paths = []
        visited = set()

        def dfs(current_id: str, entity_path: list[str], relation_path: list[Relation]):
            if len(entity_path) > max_hops + 1:
                return

            if current_id == end_entity_id:
                path = ReasoningPath(
                    entities=[self.graph.entities[eid] for eid in entity_path],
                    relations=relation_path.copy(),
                )
                path.score = self._calculate_path_score(path)
                paths.append(path)
                return

            visited.add(current_id)

            for relation, neighbor in self.graph.get_neighbors(current_id):
                if neighbor.id not in visited:
                    dfs(
                        neighbor.id,
                        entity_path + [neighbor.id],
                        relation_path + [relation]
                    )

            visited.remove(current_id)

        dfs(start_entity_id, [start_entity_id], [])

        # 按分数排序
        paths.sort(key=lambda p: p.score, reverse=True)

        return paths[:10]  # 限制返回数量

    async def find_paths_neo4j(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 3
    ) -> list[ReasoningPath]:
        """使用 Neo4j 查找路径"""
        if not self.neo4j_storage:
            return self.find_paths_bfs(start_entity_id, end_entity_id, max_hops)

        raw_paths = await self.neo4j_storage.find_paths(
            start_entity_id, end_entity_id, max_hops
        )

        paths = []
        for raw_path in raw_paths:
            entities = [Entity.from_dict(n) for n in raw_path["nodes"]]
            relations = [Relation.from_dict(r) for r in raw_path["relations"]]

            path = ReasoningPath(entities=entities, relations=relations)
            path.score = self._calculate_path_score(path)
            paths.append(path)

        paths.sort(key=lambda p: p.score, reverse=True)
        return paths

    # ==================== 多跳查询 ====================

    def multi_hop_query(
        self,
        context: QueryContext,
        llm_client: Any = None
    ) -> MultiHopResult:
        """
        多跳查询 (内存图谱)

        1. 从关键词找到起始实体
        2. 探索相关路径
        3. 综合答案
        """
        # 1. 找到相关实体
        seed_entities = self.find_entities_by_keywords(context.keywords)

        if not seed_entities:
            return MultiHopResult(
                answer="未找到与查询相关的实体",
                paths=[],
                confidence=0.0,
            )

        # 2. 从种子实体出发，探索图谱
        all_paths = []
        entities_involved = set()

        for entity in seed_entities[:3]:  # 限制起始实体数量
            # 获取 N 跳内的所有路径
            related = self._explore_from_entity(
                entity.id,
                max_hops=context.max_hops
            )

            for path in related:
                all_paths.append(path)
                for e in path.entities:
                    entities_involved.add(e.id)

        # 3. 路径去重和排序
        unique_paths = self._deduplicate_paths(all_paths)
        unique_paths.sort(key=lambda p: p.score, reverse=True)
        top_paths = unique_paths[:context.max_paths]

        # 4. 收集来源
        sources_used = set()
        for path in top_paths:
            for relation in path.relations:
                if relation.source_id:
                    sources_used.add(relation.source_id)

        # 5. 综合答案
        answer = self._synthesize_answer(context.question, top_paths, llm_client)

        # 6. 计算整体置信度
        if top_paths:
            confidence = sum(p.score for p in top_paths) / len(top_paths)
        else:
            confidence = 0.0

        return MultiHopResult(
            answer=answer,
            paths=top_paths,
            confidence=confidence,
            entities_involved=[self.graph.entities[eid] for eid in entities_involved if eid in self.graph.entities],
            sources_used=list(sources_used),
        )

    async def multi_hop_query_async(
        self,
        context: QueryContext,
        llm_client: Any = None
    ) -> MultiHopResult:
        """
        异步多跳查询 (支持 Neo4j)
        """
        # 使用 Neo4j 查找实体
        if self.neo4j_storage:
            seed_entities = await self.find_entities_by_keywords_neo4j(context.keywords)
        else:
            seed_entities = self.find_entities_by_keywords(context.keywords)

        if not seed_entities:
            return MultiHopResult(
                answer="未找到与查询相关的实体",
                paths=[],
                confidence=0.0,
            )

        # 探索路径
        all_paths = []
        entities_involved = set()

        for entity in seed_entities[:3]:
            if self.neo4j_storage:
                # 使用 Neo4j 获取子图
                subgraph = await self.neo4j_storage.get_subgraph(
                    entity.id,
                    radius=context.max_hops
                )
                # 在子图中探索
                sub_engine = GraphQueryEngine(graph=subgraph)
                related = sub_engine._explore_from_entity(entity.id, context.max_hops)
            else:
                related = self._explore_from_entity(entity.id, context.max_hops)

            for path in related:
                all_paths.append(path)
                for e in path.entities:
                    entities_involved.add(e.id)

        # 后续处理与同步版本相同
        unique_paths = self._deduplicate_paths(all_paths)
        unique_paths.sort(key=lambda p: p.score, reverse=True)
        top_paths = unique_paths[:context.max_paths]

        sources_used = set()
        for path in top_paths:
            for relation in path.relations:
                if relation.source_id:
                    sources_used.add(relation.source_id)

        answer = self._synthesize_answer(context.question, top_paths, llm_client)

        confidence = sum(p.score for p in top_paths) / len(top_paths) if top_paths else 0.0

        return MultiHopResult(
            answer=answer,
            paths=top_paths,
            confidence=confidence,
            entities_involved=[self.graph.entities.get(eid) for eid in entities_involved if eid in self.graph.entities],
            sources_used=list(sources_used),
        )

    # ==================== 关系查询 ====================

    def find_supporting_evidence(
        self,
        claim_entity_id: str
    ) -> list[tuple[Entity, Relation]]:
        """查找支持某声明的证据"""
        results = []

        for relation, neighbor in self.graph.get_neighbors(claim_entity_id):
            if relation.type == RelationType.SUPPORTS:
                results.append((neighbor, relation))

        return results

    def find_contradicting_evidence(
        self,
        claim_entity_id: str
    ) -> list[tuple[Entity, Relation]]:
        """查找与某声明矛盾的证据"""
        results = []

        for relation, neighbor in self.graph.get_neighbors(claim_entity_id):
            if relation.type == RelationType.CONTRADICTS:
                results.append((neighbor, relation))

        return results

    def find_related_claims(
        self,
        entity_id: str,
        relation_types: list[RelationType] | None = None
    ) -> list[Entity]:
        """查找与实体相关的声明"""
        claims = []

        for relation, neighbor in self.graph.get_neighbors(entity_id):
            if neighbor.type.value == "claim":
                if relation_types is None or relation.type in relation_types:
                    claims.append(neighbor)

        return claims

    # ==================== 私有方法 ====================

    def _explore_from_entity(
        self,
        entity_id: str,
        max_hops: int
    ) -> list[ReasoningPath]:
        """
        从实体出发探索图谱

        收集可达的所有路径
        """
        paths = []

        def explore(current_id: str, path_entities: list[str], path_relations: list[Relation], depth: int):
            if depth > max_hops:
                return

            # 当前路径也是一个有效路径
            if len(path_entities) > 1:
                path = ReasoningPath(
                    entities=[self.graph.entities[eid] for eid in path_entities if eid in self.graph.entities],
                    relations=path_relations.copy(),
                )
                path.score = self._calculate_path_score(path)
                paths.append(path)

            # 继续探索
            for relation, neighbor in self.graph.get_neighbors(current_id):
                if neighbor.id not in path_entities:  # 避免环
                    explore(
                        neighbor.id,
                        path_entities + [neighbor.id],
                        path_relations + [relation],
                        depth + 1
                    )

        explore(entity_id, [entity_id], [], 0)

        return paths

    def _calculate_path_score(self, path: ReasoningPath) -> float:
        """
        计算路径分数

        基于:
        - 路径长度 (越短越好)
        - 关系类型权重
        - 实体置信度
        """
        if not path.entities:
            return 0.0

        # 长度惩罚
        length_score = 1.0 / (1 + len(path.relations) * 0.1)

        # 关系权重
        if path.relations:
            relation_score = sum(
                self._get_relation_weight(r.type) for r in path.relations
            ) / len(path.relations)
        else:
            relation_score = 1.0

        # 实体置信度
        entity_score = sum(e.confidence for e in path.entities) / len(path.entities)

        return length_score * relation_score * entity_score

    def _get_relation_weight(self, relation_type: RelationType) -> float:
        """获取关系类型权重"""
        weights = {
            RelationType.SUPPORTS: 1.0,
            RelationType.IS_A: 0.95,
            RelationType.PART_OF: 0.9,
            RelationType.AUTHORED: 0.85,
            RelationType.WORKS_FOR: 0.85,
            RelationType.LEADS: 0.85,
            RelationType.FOUNDED: 0.85,
            RelationType.RELATED_TO: 0.7,
            RelationType.COMPARED_TO: 0.7,
            RelationType.DEPENDS_ON: 0.8,
            RelationType.CITED_IN: 0.75,
            RelationType.EXTRACTED_FROM: 0.75,
            RelationType.REFINES: 0.8,
            RelationType.CONTRADICTS: 0.5,
            RelationType.NEUTRAL: 0.6,
            RelationType.PRECEDED_BY: 0.7,
            RelationType.FOLLOWED_BY: 0.7,
            RelationType.CONCURRENT_WITH: 0.7,
        }
        return weights.get(relation_type, 0.5)

    def _deduplicate_paths(self, paths: list[ReasoningPath]) -> list[ReasoningPath]:
        """路径去重"""
        seen = set()
        unique = []

        for path in paths:
            # 使用实体 ID 序列作为路径标识
            path_key = tuple(e.id for e in path.entities)
            if path_key not in seen:
                seen.add(path_key)
                unique.append(path)

        return unique

    def _synthesize_answer(
        self,
        question: str,
        paths: list[ReasoningPath],
        llm_client: Any = None
    ) -> str:
        """
        综合答案

        如果有 LLM 客户端，使用 LLM 综合
        否则使用模板生成
        """
        if not paths:
            return "未找到相关信息"

        # 收集路径信息
        path_descriptions = []
        for i, path in enumerate(paths, 1):
            path_descriptions.append(f"{i}. {str(path)}")

        # 收集证据
        all_evidence = []
        for path in paths:
            evidence = path.get_evidence()
            all_evidence.extend(evidence)

        # 简单模板答案 (无 LLM 时)
        if not llm_client:
            answer_parts = [
                "基于知识图谱的多跳推理，找到以下相关路径:",
                "",
            ]
            answer_parts.extend(path_descriptions)

            if all_evidence:
                answer_parts.extend([
                    "",
                    "支持证据:",
                ])
                for ev in all_evidence[:3]:  # 最多 3 条证据
                    answer_parts.append(f"- {ev[:200]}...")

            return "\n".join(answer_parts)

        # TODO: 使用 LLM 综合答案
        # 这里可以调用 LLM 生成更自然的答案
        return "\n".join([
            "基于知识图谱的多跳推理，找到以下相关路径:",
            "",
        ] + path_descriptions)


# ==================== 辅助函数 ====================

def extract_keywords_from_question(question: str) -> list[str]:
    """
    从问题中提取关键词

    简单实现: 移除停用词，返回名词/动词
    """
    # 中文停用词
    chinese_stopwords = {
        "的", "是", "在", "了", "有", "和", "与", "或", "等",
        "这", "那", "什么", "怎么", "为什么", "如何", "哪些",
        "吗", "呢", "吧", "啊", "呀", "哦", "嗯",
    }

    # 英文停用词
    english_stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "what", "how",
        "why", "when", "where", "who", "which", "this", "that",
        "these", "those", "and", "or", "but", "if", "then",
    }

    stopwords = chinese_stopwords | english_stopwords

    # 简单分词 (按空格和标点)
    import re
    tokens = re.split(r'[\s,，。！？!?\n]+', question)

    # 过滤停用词和短词
    keywords = [
        t.strip() for t in tokens
        if t.strip() and t.lower() not in stopwords and len(t) > 1
    ]

    return keywords
