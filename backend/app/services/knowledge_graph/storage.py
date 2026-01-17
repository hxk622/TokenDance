"""
Neo4j 知识图谱存储服务

提供:
- Neo4j 连接管理
- 实体和关系的 CRUD 操作
- Cypher 查询接口
- 与内存图谱的同步
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from .models import (
    Entity,
    EntityType,
    Relation,
    RelationType,
    ResearchKnowledgeGraph,
)

logger = logging.getLogger(__name__)


class Neo4jStorage:
    """
    Neo4j 知识图谱存储

    特性:
    - 异步 API
    - 连接池管理
    - 事务支持
    - 批量操作优化
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str = "neo4j"
    ):
        """
        初始化 Neo4j 连接

        Args:
            uri: Neo4j URI (默认从环境变量读取)
            username: 用户名
            password: 密码
            database: 数据库名
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.username = username or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        self.database = database

        self._driver: AsyncDriver | None = None
        self._initialized = False

    async def connect(self) -> None:
        """建立数据库连接"""
        if self._driver is not None:
            return

        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
            # 验证连接
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {self.uri}")
        except AuthError as e:
            logger.error(f"Neo4j authentication failed: {e}")
            raise
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable: {e}")
            raise

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    async def initialize_schema(self) -> None:
        """
        初始化图谱 Schema

        创建约束和索引以优化查询性能
        """
        if self._initialized:
            return

        constraints = [
            # 实体唯一性约束
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
            # 来源唯一性约束
            "CREATE CONSTRAINT source_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
        ]

        indexes = [
            # 实体名称索引 (用于名称查找)
            "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)",
            # 实体类型索引
            "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)",
            # 来源 URL 索引
            "CREATE INDEX source_url IF NOT EXISTS FOR (s:Source) ON (s.url)",
        ]

        async with self._session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    # 约束可能已存在
                    logger.debug(f"Constraint creation: {e}")

            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.debug(f"Index creation: {e}")

        self._initialized = True
        logger.info("Neo4j schema initialized")

    @asynccontextmanager
    async def _session(self):
        """获取数据库会话"""
        if not self._driver:
            await self.connect()

        session = self._driver.session(database=self.database)
        try:
            yield session
        finally:
            await session.close()

    # ==================== 实体操作 ====================

    async def create_entity(self, entity: Entity) -> str:
        """
        创建实体节点

        使用 MERGE 避免重复创建
        """
        query = """
        MERGE (e:Entity {id: $id})
        SET e.name = $name,
            e.type = $type,
            e.properties = $properties,
            e.source_ids = $source_ids,
            e.confidence = $confidence,
            e.created_at = $created_at,
            e.updated_at = $updated_at
        RETURN e.id
        """

        async with self._session() as session:
            result = await session.run(
                query,
                id=entity.id,
                name=entity.name,
                type=entity.type.value,
                properties=str(entity.properties),  # Neo4j 不支持嵌套 dict，序列化为字符串
                source_ids=entity.source_ids,
                confidence=entity.confidence,
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat(),
            )
            record = await result.single()
            return record["e.id"] if record else entity.id

    async def get_entity(self, entity_id: str) -> Entity | None:
        """按 ID 获取实体"""
        query = """
        MATCH (e:Entity {id: $id})
        RETURN e
        """

        async with self._session() as session:
            result = await session.run(query, id=entity_id)
            record = await result.single()

            if not record:
                return None

            node = record["e"]
            return self._node_to_entity(node)

    async def get_entity_by_name(self, name: str) -> Entity | None:
        """按名称获取实体 (大小写不敏感)"""
        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) = toLower($name)
        RETURN e
        LIMIT 1
        """

        async with self._session() as session:
            result = await session.run(query, name=name)
            record = await result.single()

            if not record:
                return None

            return self._node_to_entity(record["e"])

    async def search_entities(
        self,
        keyword: str,
        entity_type: EntityType | None = None,
        limit: int = 10
    ) -> list[Entity]:
        """
        搜索实体

        支持名称模糊匹配和类型过滤
        """
        if entity_type:
            query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($keyword)
              AND e.type = $type
            RETURN e
            LIMIT $limit
            """
            params = {"keyword": keyword, "type": entity_type.value, "limit": limit}
        else:
            query = """
            MATCH (e:Entity)
            WHERE toLower(e.name) CONTAINS toLower($keyword)
            RETURN e
            LIMIT $limit
            """
            params = {"keyword": keyword, "limit": limit}

        async with self._session() as session:
            result = await session.run(query, **params)
            records = await result.fetch(limit)
            return [self._node_to_entity(r["e"]) for r in records]

    async def update_entity(self, entity: Entity) -> None:
        """更新实体"""
        await self.create_entity(entity)  # MERGE 会更新已存在的实体

    async def delete_entity(self, entity_id: str) -> bool:
        """
        删除实体及其所有关系
        """
        query = """
        MATCH (e:Entity {id: $id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """

        async with self._session() as session:
            result = await session.run(query, id=entity_id)
            record = await result.single()
            return record["deleted"] > 0 if record else False

    # ==================== 关系操作 ====================

    async def create_relation(self, relation: Relation) -> str:
        """
        创建关系

        注意: Neo4j 关系类型必须是标识符，不能动态设置
        使用 RELATIONSHIP 属性存储具体类型
        """
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        MERGE (source)-[r:RELATES_TO {id: $id}]->(target)
        SET r.type = $type,
            r.properties = $properties,
            r.evidence = $evidence,
            r.source_id = $doc_source_id,
            r.confidence = $confidence,
            r.created_at = $created_at
        RETURN r.id
        """

        async with self._session() as session:
            result = await session.run(
                query,
                source_id=relation.source_entity_id,
                target_id=relation.target_entity_id,
                id=relation.id,
                type=relation.type.value,
                properties=str(relation.properties),
                evidence=relation.evidence,
                doc_source_id=relation.source_id,
                confidence=relation.confidence,
                created_at=relation.created_at.isoformat(),
            )
            record = await result.single()
            return record["r.id"] if record else relation.id

    async def get_relations(
        self,
        entity_id: str,
        direction: str = "both",
        relation_type: RelationType | None = None
    ) -> list[tuple[Relation, Entity]]:
        """
        获取实体的关系

        Args:
            entity_id: 实体 ID
            direction: "outgoing", "incoming", 或 "both"
            relation_type: 可选的关系类型过滤
        """
        if direction == "outgoing":
            pattern = "(e:Entity {id: $id})-[r:RELATES_TO]->(other:Entity)"
        elif direction == "incoming":
            pattern = "(e:Entity {id: $id})<-[r:RELATES_TO]-(other:Entity)"
        else:
            pattern = "(e:Entity {id: $id})-[r:RELATES_TO]-(other:Entity)"

        if relation_type:
            query = f"""
            MATCH {pattern}
            WHERE r.type = $type
            RETURN r, other
            """
            params = {"id": entity_id, "type": relation_type.value}
        else:
            query = f"""
            MATCH {pattern}
            RETURN r, other
            """
            params = {"id": entity_id}

        async with self._session() as session:
            result = await session.run(query, **params)
            records = await result.fetch(100)

            relations = []
            for record in records:
                relation = self._edge_to_relation(record["r"])
                entity = self._node_to_entity(record["other"])
                relations.append((relation, entity))

            return relations

    async def delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        query = """
        MATCH ()-[r:RELATES_TO {id: $id}]->()
        DELETE r
        RETURN count(r) as deleted
        """

        async with self._session() as session:
            result = await session.run(query, id=relation_id)
            record = await result.single()
            return record["deleted"] > 0 if record else False

    # ==================== 图谱操作 ====================

    async def save_graph(self, graph: ResearchKnowledgeGraph) -> None:
        """
        保存整个知识图谱到 Neo4j

        使用批量操作优化性能
        """
        # 批量创建实体
        entity_query = """
        UNWIND $entities as entity
        MERGE (e:Entity {id: entity.id})
        SET e.name = entity.name,
            e.type = entity.type,
            e.properties = entity.properties,
            e.source_ids = entity.source_ids,
            e.confidence = entity.confidence,
            e.created_at = entity.created_at,
            e.updated_at = entity.updated_at
        """

        entities_data = [
            {
                "id": e.id,
                "name": e.name,
                "type": e.type.value,
                "properties": str(e.properties),
                "source_ids": e.source_ids,
                "confidence": e.confidence,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
            }
            for e in graph.entities.values()
        ]

        async with self._session() as session:
            if entities_data:
                await session.run(entity_query, entities=entities_data)

        # 批量创建关系
        relation_query = """
        UNWIND $relations as rel
        MATCH (source:Entity {id: rel.source_entity_id})
        MATCH (target:Entity {id: rel.target_entity_id})
        MERGE (source)-[r:RELATES_TO {id: rel.id}]->(target)
        SET r.type = rel.type,
            r.properties = rel.properties,
            r.evidence = rel.evidence,
            r.source_id = rel.source_id,
            r.confidence = rel.confidence,
            r.created_at = rel.created_at
        """

        relations_data = [
            {
                "id": r.id,
                "source_entity_id": r.source_entity_id,
                "target_entity_id": r.target_entity_id,
                "type": r.type.value,
                "properties": str(r.properties),
                "evidence": r.evidence,
                "source_id": r.source_id,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat(),
            }
            for r in graph.relations
        ]

        async with self._session() as session:
            if relations_data:
                await session.run(relation_query, relations=relations_data)

        # 保存来源
        source_query = """
        UNWIND $sources as source
        MERGE (s:Source {id: source.id})
        SET s.url = source.url,
            s.title = source.title,
            s.snippet = source.snippet,
            s.credibility_score = source.credibility_score,
            s.timestamp = source.timestamp
        """

        sources_data = [
            {
                "id": s.id,
                "url": s.url,
                "title": s.title,
                "snippet": s.snippet,
                "credibility_score": s.credibility_score,
                "timestamp": s.timestamp.isoformat(),
            }
            for s in graph.sources.values()
        ]

        async with self._session() as session:
            if sources_data:
                await session.run(source_query, sources=sources_data)

        logger.info(
            f"Saved graph: {len(graph.entities)} entities, "
            f"{len(graph.relations)} relations, {len(graph.sources)} sources"
        )

    async def load_graph(self, research_id: str | None = None) -> ResearchKnowledgeGraph:
        """
        从 Neo4j 加载知识图谱

        Args:
            research_id: 可选的研究 ID 过滤
        """
        graph = ResearchKnowledgeGraph()

        # 加载实体
        if research_id:
            entity_query = """
            MATCH (e:Entity)
            WHERE $research_id IN e.source_ids
            RETURN e
            """
            params = {"research_id": research_id}
        else:
            entity_query = "MATCH (e:Entity) RETURN e"
            params = {}

        async with self._session() as session:
            result = await session.run(entity_query, **params)
            async for record in result:
                entity = self._node_to_entity(record["e"])
                graph.add_entity(entity)

        # 加载关系
        relation_query = """
        MATCH (source:Entity)-[r:RELATES_TO]->(target:Entity)
        WHERE source.id IN $entity_ids AND target.id IN $entity_ids
        RETURN r, source.id as source_id, target.id as target_id
        """

        entity_ids = list(graph.entities.keys())

        async with self._session() as session:
            if entity_ids:
                result = await session.run(relation_query, entity_ids=entity_ids)
                async for record in result:
                    relation = self._edge_to_relation(
                        record["r"],
                        source_id=record["source_id"],
                        target_id=record["target_id"]
                    )
                    graph.add_relation(relation)

        logger.info(
            f"Loaded graph: {len(graph.entities)} entities, "
            f"{len(graph.relations)} relations"
        )

        return graph

    # ==================== 多跳查询 ====================

    async def find_paths(
        self,
        start_entity_id: str,
        end_entity_id: str,
        max_hops: int = 3,
        relation_types: list[RelationType] | None = None
    ) -> list[list[dict[str, Any]]]:
        """
        查找两个实体之间的路径

        使用 Neo4j 原生路径查询，高效处理多跳
        """
        if relation_types:
            type_filter = "AND ALL(r IN relationships(p) WHERE r.type IN $types)"
            params = {
                "start_id": start_entity_id,
                "end_id": end_entity_id,
                "types": [rt.value for rt in relation_types],
            }
        else:
            type_filter = ""
            params = {
                "start_id": start_entity_id,
                "end_id": end_entity_id,
            }

        query = f"""
        MATCH p = shortestPath(
            (start:Entity {{id: $start_id}})-[*1..{max_hops}]-(end:Entity {{id: $end_id}})
        )
        {type_filter}
        RETURN [n IN nodes(p) | n] as nodes,
               [r IN relationships(p) | r] as relations
        LIMIT 5
        """

        paths = []
        async with self._session() as session:
            result = await session.run(query, **params)
            async for record in result:
                path = {
                    "nodes": [self._node_to_entity(n).to_dict() for n in record["nodes"]],
                    "relations": [self._edge_to_relation(r).to_dict() for r in record["relations"]],
                }
                paths.append(path)

        return paths

    async def find_related_entities(
        self,
        entity_id: str,
        hops: int = 2,
        limit: int = 20
    ) -> list[tuple[Entity, int]]:
        """
        查找 N 跳内的相关实体

        返回: (实体, 距离) 列表，按距离排序
        """
        query = f"""
        MATCH path = (start:Entity {{id: $id}})-[*1..{hops}]-(related:Entity)
        WHERE related.id <> $id
        WITH related, min(length(path)) as distance
        RETURN related, distance
        ORDER BY distance
        LIMIT $limit
        """

        results = []
        async with self._session() as session:
            result = await session.run(query, id=entity_id, limit=limit)
            async for record in result:
                entity = self._node_to_entity(record["related"])
                distance = record["distance"]
                results.append((entity, distance))

        return results

    async def get_subgraph(
        self,
        center_entity_id: str,
        radius: int = 2
    ) -> ResearchKnowledgeGraph:
        """
        获取以某实体为中心的子图
        """
        query = f"""
        MATCH (center:Entity {{id: $id}})
        CALL apoc.path.subgraphAll(center, {{
            maxLevel: {radius}
        }})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """

        graph = ResearchKnowledgeGraph()

        async with self._session() as session:
            try:
                result = await session.run(query, id=center_entity_id)
                record = await result.single()

                if record:
                    for node in record["nodes"]:
                        if "Entity" in node.labels:
                            entity = self._node_to_entity(node)
                            graph.add_entity(entity)

                    for rel in record["relationships"]:
                        relation = self._edge_to_relation(rel)
                        if relation.source_entity_id in graph.entities and \
                           relation.target_entity_id in graph.entities:
                            graph.add_relation(relation)

            except Exception as e:
                # APOC 可能未安装，回退到基本查询
                logger.warning(f"APOC not available, using basic query: {e}")

                # 基本的多跳查询
                basic_query = f"""
                MATCH (center:Entity {{id: $id}})-[*0..{radius}]-(e:Entity)
                WITH collect(DISTINCT e) as entities
                UNWIND entities as entity
                OPTIONAL MATCH (entity)-[r:RELATES_TO]-(other:Entity)
                WHERE other IN entities
                RETURN entity, collect(DISTINCT r) as relations
                """

                result = await session.run(basic_query, id=center_entity_id)
                seen_relations = set()

                async for record in result:
                    entity = self._node_to_entity(record["entity"])
                    graph.add_entity(entity)

                    for rel in record["relations"]:
                        if rel and rel.id not in seen_relations:
                            relation = self._edge_to_relation(rel)
                            graph.add_relation(relation)
                            seen_relations.add(rel.id)

        return graph

    # ==================== 辅助方法 ====================

    def _node_to_entity(self, node) -> Entity:
        """将 Neo4j 节点转换为 Entity"""
        import ast
        from datetime import datetime

        properties = {}
        if node.get("properties"):
            try:
                properties = ast.literal_eval(node["properties"])
            except (ValueError, SyntaxError):
                properties = {}

        return Entity(
            id=node["id"],
            name=node["name"],
            type=EntityType(node["type"]),
            properties=properties,
            source_ids=list(node.get("source_ids", [])),
            confidence=node.get("confidence", 1.0),
            created_at=datetime.fromisoformat(node["created_at"]) if "created_at" in node else datetime.now(),
            updated_at=datetime.fromisoformat(node["updated_at"]) if "updated_at" in node else datetime.now(),
        )

    def _edge_to_relation(
        self,
        edge,
        source_id: str | None = None,
        target_id: str | None = None
    ) -> Relation:
        """将 Neo4j 边转换为 Relation"""
        import ast
        from datetime import datetime

        properties = {}
        if edge.get("properties"):
            try:
                properties = ast.literal_eval(edge["properties"])
            except (ValueError, SyntaxError):
                properties = {}

        return Relation(
            id=edge["id"],
            source_entity_id=source_id or edge.get("source_entity_id", ""),
            target_entity_id=target_id or edge.get("target_entity_id", ""),
            type=RelationType(edge["type"]),
            properties=properties,
            evidence=edge.get("evidence", ""),
            source_id=edge.get("source_id", ""),
            confidence=edge.get("confidence", 1.0),
            created_at=datetime.fromisoformat(edge["created_at"]) if "created_at" in edge else datetime.now(),
        )

    # ==================== 统计查询 ====================

    async def get_statistics(self) -> dict[str, Any]:
        """获取图谱统计信息"""
        query = """
        MATCH (e:Entity)
        WITH count(e) as entity_count,
             collect(e.type) as types
        MATCH ()-[r:RELATES_TO]->()
        RETURN entity_count,
               count(r) as relation_count,
               types
        """

        async with self._session() as session:
            result = await session.run(query)
            record = await result.single()

            if not record:
                return {"entities": 0, "relations": 0}

            # 统计类型分布
            type_counts = {}
            for t in record["types"]:
                type_counts[t] = type_counts.get(t, 0) + 1

            return {
                "entities": record["entity_count"],
                "relations": record["relation_count"],
                "entity_types": type_counts,
            }


# 单例实例
_storage_instance: Neo4jStorage | None = None


async def get_neo4j_storage() -> Neo4jStorage:
    """获取 Neo4j 存储单例"""
    global _storage_instance

    if _storage_instance is None:
        _storage_instance = Neo4jStorage()
        await _storage_instance.connect()
        await _storage_instance.initialize_schema()

    return _storage_instance


async def close_neo4j_storage() -> None:
    """关闭 Neo4j 连接"""
    global _storage_instance

    if _storage_instance:
        await _storage_instance.close()
        _storage_instance = None
