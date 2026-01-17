"""
Knowledge Graph 数据模型测试
"""


import pytest

from app.services.knowledge_graph.models import (
    ClaimVerification,
    Entity,
    EntityType,
    ReasoningPath,
    Relation,
    RelationType,
    ResearchKnowledgeGraph,
)


class TestEntity:
    """Entity 数据类测试"""

    def test_create_entity(self):
        """测试实体创建"""
        entity = Entity.create(
            name="OpenAI",
            entity_type=EntityType.ORGANIZATION,
            source_id="source-123",
            description="AI research company"
        )

        assert entity.name == "OpenAI"
        assert entity.type == EntityType.ORGANIZATION
        assert "source-123" in entity.source_ids
        assert entity.properties.get("description") == "AI research company"
        assert entity.confidence == 1.0

    def test_entity_merge(self):
        """测试实体合并"""
        entity1 = Entity.create(
            name="OpenAI",
            entity_type=EntityType.ORGANIZATION,
            source_id="source-1",
        )
        entity1.confidence = 0.8  # 设置较低初始置信度

        entity2 = Entity.create(
            name="OpenAI",
            entity_type=EntityType.ORGANIZATION,
            source_id="source-2",
            description="Founded in 2015"
        )

        entity1.merge_with(entity2)

        assert "source-1" in entity1.source_ids
        assert "source-2" in entity1.source_ids
        assert entity1.properties.get("description") == "Founded in 2015"
        assert entity1.confidence == 0.9  # 置信度提升 0.1 (capped at 1.0)

    def test_entity_serialization(self):
        """测试实体序列化/反序列化"""
        entity = Entity.create(
            name="GPT-4",
            entity_type=EntityType.PRODUCT,
        )

        data = entity.to_dict()
        restored = Entity.from_dict(data)

        assert restored.name == entity.name
        assert restored.type == entity.type
        assert restored.id == entity.id


class TestRelation:
    """Relation 数据类测试"""

    def test_create_relation(self):
        """测试关系创建"""
        relation = Relation.create(
            source_id="entity-1",
            target_id="entity-2",
            relation_type=RelationType.WORKS_FOR,
            evidence="Sam Altman works for OpenAI",
            doc_source_id="doc-123"
        )

        assert relation.source_entity_id == "entity-1"
        assert relation.target_entity_id == "entity-2"
        assert relation.type == RelationType.WORKS_FOR
        assert relation.evidence == "Sam Altman works for OpenAI"

    def test_relation_serialization(self):
        """测试关系序列化/反序列化"""
        relation = Relation.create(
            source_id="e1",
            target_id="e2",
            relation_type=RelationType.SUPPORTS,
        )

        data = relation.to_dict()
        restored = Relation.from_dict(data)

        assert restored.id == relation.id
        assert restored.type == relation.type


class TestResearchKnowledgeGraph:
    """ResearchKnowledgeGraph 测试"""

    @pytest.fixture
    def sample_graph(self) -> ResearchKnowledgeGraph:
        """创建示例图谱"""
        graph = ResearchKnowledgeGraph()

        # 添加实体
        openai = Entity.create("OpenAI", EntityType.ORGANIZATION)
        sam = Entity.create("Sam Altman", EntityType.PERSON)
        gpt4 = Entity.create("GPT-4", EntityType.PRODUCT)

        graph.add_entity(openai)
        graph.add_entity(sam)
        graph.add_entity(gpt4)

        # 添加关系
        r1 = Relation.create(
            source_id=sam.id,
            target_id=openai.id,
            relation_type=RelationType.LEADS,
        )
        r2 = Relation.create(
            source_id=openai.id,
            target_id=gpt4.id,
            relation_type=RelationType.AUTHORED,
        )

        graph.add_relation(r1)
        graph.add_relation(r2)

        return graph

    def test_add_entity(self, sample_graph):
        """测试添加实体"""
        assert len(sample_graph.entities) == 3
        assert sample_graph.get_entity_by_name("OpenAI") is not None
        assert sample_graph.get_entity_by_name("openai") is not None  # 大小写不敏感

    def test_add_relation(self, sample_graph):
        """测试添加关系"""
        assert len(sample_graph.relations) == 2

    def test_get_neighbors(self, sample_graph):
        """测试获取邻居"""
        openai = sample_graph.get_entity_by_name("OpenAI")
        neighbors = sample_graph.get_neighbors(openai.id)

        assert len(neighbors) == 2  # Sam Altman 和 GPT-4
        neighbor_names = [n[1].name for n in neighbors]
        assert "Sam Altman" in neighbor_names
        assert "GPT-4" in neighbor_names

    def test_find_similar_entity(self, sample_graph):
        """测试相似实体查找"""
        # 精确匹配
        entity = sample_graph.find_similar_entity("OpenAI")
        assert entity is not None
        assert entity.name == "OpenAI"

        # 模糊匹配
        entity = sample_graph.find_similar_entity("Sam", threshold=0.5)
        assert entity is not None
        assert "Sam" in entity.name

    def test_statistics(self, sample_graph):
        """测试统计信息"""
        stats = sample_graph.get_statistics()

        assert stats["total_entities"] == 3
        assert stats["total_relations"] == 2
        assert "org" in stats["entity_types"]

    def test_serialization(self, sample_graph):
        """测试图谱序列化/反序列化"""
        data = sample_graph.to_dict()
        restored = ResearchKnowledgeGraph.from_dict(data)

        assert len(restored.entities) == len(sample_graph.entities)
        assert len(restored.relations) == len(sample_graph.relations)


class TestReasoningPath:
    """ReasoningPath 测试"""

    def test_path_str(self):
        """测试路径字符串表示"""
        e1 = Entity.create("A", EntityType.CONCEPT)
        e2 = Entity.create("B", EntityType.CONCEPT)
        e3 = Entity.create("C", EntityType.CONCEPT)

        r1 = Relation.create(e1.id, e2.id, RelationType.RELATED_TO)
        r2 = Relation.create(e2.id, e3.id, RelationType.RELATED_TO)

        path = ReasoningPath(
            entities=[e1, e2, e3],
            relations=[r1, r2],
            score=0.9
        )

        path_str = str(path)
        assert "A" in path_str
        assert "B" in path_str
        assert "C" in path_str
        assert "related_to" in path_str

    def test_get_evidence(self):
        """测试获取证据"""
        e1 = Entity.create("A", EntityType.CONCEPT)
        e2 = Entity.create("B", EntityType.CONCEPT)

        r1 = Relation.create(
            e1.id, e2.id, RelationType.SUPPORTS,
            evidence="A supports B according to study X"
        )

        path = ReasoningPath(
            entities=[e1, e2],
            relations=[r1],
        )

        evidence = path.get_evidence()
        assert len(evidence) == 1
        assert "study X" in evidence[0]


class TestClaimVerification:
    """ClaimVerification 测试"""

    def test_has_conflict(self):
        """测试冲突检测"""
        # 无冲突
        v1 = ClaimVerification(
            claim="Test claim",
            verdict="confirmed",
            confidence=0.9,
            supporting_evidence=[("url1", "evidence1")],
            contradicting_evidence=[],
        )
        assert not v1.has_conflict

        # 有冲突
        v2 = ClaimVerification(
            claim="Test claim",
            verdict="uncertain",
            confidence=0.5,
            supporting_evidence=[("url1", "evidence1")],
            contradicting_evidence=[("url2", "evidence2")],
        )
        assert v2.has_conflict

    def test_to_dict(self):
        """测试序列化"""
        v = ClaimVerification(
            claim="Test",
            verdict="confirmed",
            confidence=0.9,
        )

        data = v.to_dict()
        assert data["claim"] == "Test"
        assert data["verdict"] == "confirmed"
        assert data["has_conflict"] is False
