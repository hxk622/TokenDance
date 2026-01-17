# -*- coding: utf-8 -*-
"""
GraphQueryEngine 测试
"""

import pytest

from app.services.knowledge_graph.models import (
    Entity, Relation, EntityType, RelationType,
    ResearchKnowledgeGraph,
)
from app.services.knowledge_graph.query_engine import (
    GraphQueryEngine, QueryContext, extract_keywords_from_question
)


class TestGraphQueryEngine:
    """GraphQueryEngine 测试"""
    
    @pytest.fixture
    def sample_graph(self) -> ResearchKnowledgeGraph:
        """创建示例图谱用于测试"""
        graph = ResearchKnowledgeGraph()
        
        # 创建实体
        openai = Entity.create("OpenAI", EntityType.ORGANIZATION)
        sam = Entity.create("Sam Altman", EntityType.PERSON)
        elon = Entity.create("Elon Musk", EntityType.PERSON)
        gpt4 = Entity.create("GPT-4", EntityType.PRODUCT)
        ai = Entity.create("Artificial Intelligence", EntityType.CONCEPT)
        
        graph.add_entity(openai)
        graph.add_entity(sam)
        graph.add_entity(elon)
        graph.add_entity(gpt4)
        graph.add_entity(ai)
        
        # 创建关系
        # Sam Altman -> leads -> OpenAI
        graph.add_relation(Relation.create(
            sam.id, openai.id, RelationType.LEADS,
            evidence="Sam Altman is the CEO of OpenAI"
        ))
        
        # Elon Musk -> founded -> OpenAI
        graph.add_relation(Relation.create(
            elon.id, openai.id, RelationType.FOUNDED,
            evidence="Elon Musk co-founded OpenAI in 2015"
        ))
        
        # OpenAI -> authored -> GPT-4
        graph.add_relation(Relation.create(
            openai.id, gpt4.id, RelationType.AUTHORED,
            evidence="OpenAI developed GPT-4"
        ))
        
        # GPT-4 -> is_a -> AI
        graph.add_relation(Relation.create(
            gpt4.id, ai.id, RelationType.IS_A,
            evidence="GPT-4 is an AI model"
        ))
        
        return graph
    
    @pytest.fixture
    def engine(self, sample_graph) -> GraphQueryEngine:
        """创建查询引擎"""
        return GraphQueryEngine(graph=sample_graph)
    
    def test_find_entities_by_keywords(self, engine):
        """测试关键词查找实体"""
        results = engine.find_entities_by_keywords(["OpenAI"])
        assert len(results) >= 1
        assert any(e.name == "OpenAI" for e in results)
        
        results = engine.find_entities_by_keywords(["Sam", "Altman"])
        assert len(results) >= 1
        assert any("Sam" in e.name for e in results)
    
    def test_find_paths_bfs(self, engine, sample_graph):
        """测试 BFS 路径查找"""
        sam = sample_graph.get_entity_by_name("Sam Altman")
        gpt4 = sample_graph.get_entity_by_name("GPT-4")
        
        paths = engine.find_paths_bfs(sam.id, gpt4.id, max_hops=3)
        
        # 应该找到路径: Sam -> OpenAI -> GPT-4
        assert len(paths) >= 1
        
        # 验证路径
        path = paths[0]
        assert len(path.entities) == 3
        assert path.entities[0].name == "Sam Altman"
        assert path.entities[-1].name == "GPT-4"
    
    def test_find_paths_dfs(self, engine, sample_graph):
        """测试 DFS 路径查找"""
        elon = sample_graph.get_entity_by_name("Elon Musk")
        ai = sample_graph.get_entity_by_name("Artificial Intelligence")
        
        paths = engine.find_paths_dfs(elon.id, ai.id, max_hops=3)
        
        # 应该找到路径: Elon -> OpenAI -> GPT-4 -> AI
        assert len(paths) >= 1
        
        path = paths[0]
        assert path.entities[0].name == "Elon Musk"
        assert path.entities[-1].name == "Artificial Intelligence"
    
    def test_find_paths_same_entity(self, engine, sample_graph):
        """测试查找到自身的路径"""
        openai = sample_graph.get_entity_by_name("OpenAI")
        
        paths = engine.find_paths_bfs(openai.id, openai.id)
        
        # 应该返回单节点路径
        assert len(paths) == 1
        assert len(paths[0].entities) == 1
    
    def test_find_paths_no_path(self, engine, sample_graph):
        """测试无路径情况"""
        # 添加一个孤立节点
        isolated = Entity.create("Isolated", EntityType.CONCEPT)
        sample_graph.add_entity(isolated)
        
        openai = sample_graph.get_entity_by_name("OpenAI")
        paths = engine.find_paths_bfs(openai.id, isolated.id)
        
        assert len(paths) == 0
    
    def test_multi_hop_query(self, engine):
        """测试多跳查询"""
        context = QueryContext(
            question="Who leads OpenAI?",
            keywords=["OpenAI", "leads"],
            max_hops=2,
            max_paths=3,
        )
        
        result = engine.multi_hop_query(context)
        
        assert result.answer is not None
        assert len(result.paths) > 0
        assert result.confidence > 0
    
    def test_path_score_calculation(self, engine, sample_graph):
        """测试路径分数计算"""
        sam = sample_graph.get_entity_by_name("Sam Altman")
        openai = sample_graph.get_entity_by_name("OpenAI")
        
        paths = engine.find_paths_bfs(sam.id, openai.id)
        
        assert len(paths) >= 1
        # 路径应该有分数
        assert paths[0].score > 0
        # 短路径应该分数更高
        assert paths[0].score > 0.5


class TestExtractKeywords:
    """关键词提取测试"""
    
    def test_extract_english_keywords(self):
        """测试英文关键词提取"""
        question = "What is the relationship between OpenAI and GPT-4?"
        keywords = extract_keywords_from_question(question)
        
        assert "relationship" in keywords
        assert "OpenAI" in keywords
        assert "GPT-4" in keywords
        # 停用词不应出现
        assert "what" not in [k.lower() for k in keywords]
        assert "the" not in [k.lower() for k in keywords]
    
    def test_extract_chinese_keywords(self):
        """测试中文关键词提取"""
        question = "OpenAI 和 GPT-4 之间有什么关系？"
        keywords = extract_keywords_from_question(question)
        
        assert "OpenAI" in keywords
        assert "GPT-4" in keywords
        # 停用词不应出现
        assert "的" not in keywords
        assert "什么" not in keywords
    
    def test_extract_empty_question(self):
        """测试空问题"""
        keywords = extract_keywords_from_question("")
        assert keywords == []


class TestQueryContext:
    """QueryContext 测试"""
    
    def test_default_weights(self):
        """测试默认关系权重"""
        context = QueryContext(
            question="Test",
            keywords=["test"],
        )
        
        assert context.relation_weights is not None
        assert RelationType.SUPPORTS in context.relation_weights
        assert context.relation_weights[RelationType.SUPPORTS] == 1.0
    
    def test_custom_weights(self):
        """测试自定义权重"""
        custom_weights = {
            RelationType.SUPPORTS: 0.5,
        }
        
        context = QueryContext(
            question="Test",
            keywords=["test"],
            relation_weights=custom_weights,
        )
        
        assert context.relation_weights[RelationType.SUPPORTS] == 0.5
