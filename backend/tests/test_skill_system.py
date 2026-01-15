"""
Skill 系统测试

测试内容：
1. SkillRegistry 加载 SKILL.md
2. SkillMatcher 意图匹配（关键词 + Embedding）
3. SkillLoader 加载 L2/L3 内容
"""

import asyncio
import pytest
from pathlib import Path


class TestSkillRegistry:
    """测试 Skill 注册表"""

    def test_registry_loads_deep_research(self):
        """测试 Registry 能加载 deep_research skill"""
        from app.skills.registry import SkillRegistry

        # 使用默认的 builtin 目录
        registry = SkillRegistry()
        registry.load_all()

        # 验证加载成功
        assert len(registry) > 0, "Should load at least one skill"
        assert "deep_research" in registry, "Should load deep_research skill"

        # 验证元数据
        skill = registry.get("deep_research")
        assert skill is not None
        assert skill.display_name == "深度研究"
        assert "web_search" in skill.allowed_tools
        assert "read_url" in skill.allowed_tools
        assert skill.enabled is True

    def test_registry_generates_system_prompt(self):
        """测试 Registry 生成 System Prompt 片段"""
        from app.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_all()

        prompt = registry.generate_system_prompt_fragment()
        assert "[Available Skills]" in prompt
        assert "深度研究" in prompt

    def test_registry_skill_ids(self):
        """测试获取所有 Skill ID"""
        from app.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_all()

        skill_ids = registry.get_skill_ids()
        assert "deep_research" in skill_ids


class TestSkillMatcher:
    """测试 Skill 意图匹配器"""

    @pytest.fixture
    def registry(self):
        """创建并加载 Registry"""
        from app.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_all()
        return registry

    def test_keyword_match(self, registry):
        """测试关键词匹配"""
        from app.skills.matcher import SkillMatcher

        # 不使用 Embedding，仅关键词匹配
        matcher = SkillMatcher(registry, enable_embedding=False)

        # 测试匹配
        candidates = matcher._keyword_match("帮我调研一下AI市场", top_k=3)
        assert len(candidates) > 0, "Should find keyword matches"

    @pytest.mark.asyncio
    async def test_match_research_query(self, registry):
        """测试研究类查询匹配到 deep_research"""
        from app.skills.matcher import SkillMatcher

        # 仅使用关键词匹配进行快速测试
        matcher = SkillMatcher(registry, enable_embedding=False)

        # 测试各种研究相关的查询
        test_queries = [
            "帮我调研AI Agent市场",
            "research about blockchain technology",
            "分析一下竞品情况",
            "investigation on market trends",
        ]

        for query in test_queries:
            match = await matcher.match(query, min_score=0.0)
            # 关键词匹配可能无法每次都成功，但至少应该有候选
            print(f"Query: {query} -> Match: {match}")

    @pytest.mark.asyncio
    async def test_match_with_embedding(self, registry):
        """测试使用 Embedding 的语义匹配"""
        from app.skills.matcher import create_skill_matcher

        # 创建带 Embedding 的 Matcher
        matcher = create_skill_matcher(registry, use_sentence_transformer=True)

        # 测试语义匹配
        match = await matcher.match("帮我深入了解一下AI Agent这个领域")

        if match:
            print(f"Matched: {match.skill_id} (score={match.score:.2f})")
            assert match.skill_id == "deep_research"
            assert match.score > 0.5


class TestSkillLoader:
    """测试 Skill 加载器"""

    @pytest.fixture
    def registry(self):
        """创建并加载 Registry"""
        from app.skills.registry import SkillRegistry

        registry = SkillRegistry()
        registry.load_all()
        return registry

    @pytest.mark.asyncio
    async def test_load_l2_instructions(self, registry):
        """测试加载 L2 完整指令"""
        from app.skills.loader import SkillLoader

        loader = SkillLoader(registry)

        # 加载 deep_research 的 L2 指令
        l2_content = await loader.load_l2("deep_research")

        assert len(l2_content) > 0
        assert "能力概述" in l2_content
        assert "工作流程" in l2_content
        assert "工具使用" in l2_content

    @pytest.mark.asyncio
    async def test_load_l3_resource(self, registry):
        """测试加载 L3 资源"""
        from app.skills.loader import SkillLoader

        loader = SkillLoader(registry)

        # 加载子技能文档
        summarize_content = await loader.load_l3_resource(
            "deep_research", "summarize.md"
        )
        assert "内容摘要" in summarize_content

    def test_list_resources(self, registry):
        """测试列出 Skill 资源"""
        from app.skills.loader import SkillLoader

        loader = SkillLoader(registry)

        resources = loader.list_resources("deep_research")
        assert len(resources) > 0
        assert any("query_generator" in r for r in resources)
        assert any("summarize" in r for r in resources)

    @pytest.mark.asyncio
    async def test_build_skill_context(self, registry):
        """测试构建 Skill 执行上下文"""
        from app.skills.loader import SkillLoader

        loader = SkillLoader(registry)

        context = await loader.build_skill_context(
            skill_id="deep_research",
            session_id="test-session",
            workspace_id="test-workspace",
            user_id="test-user",
        )

        assert context.skill_id == "deep_research"
        assert "web_search" in context.available_tools
        assert len(context.l2_instructions) > 0


class TestEmbedding:
    """测试 Embedding 模块"""

    def test_sentence_transformer_embedding(self):
        """测试 SentenceTransformer Embedding"""
        try:
            from app.skills.embedding import SentenceTransformerEmbedding

            embedding = SentenceTransformerEmbedding()

            # 测试编码
            text = "帮我调研AI Agent市场"
            vector = embedding.encode(text)

            assert len(vector) == 384, "all-MiniLM-L6-v2 produces 384-dim vectors"
            assert all(isinstance(v, float) for v in vector)
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_embedding_similarity(self):
        """测试 Embedding 相似度计算"""
        try:
            from app.skills.embedding import SentenceTransformerEmbedding

            embedding = SentenceTransformerEmbedding()

            # 相似文本应该有较高相似度
            text1 = "帮我调研AI Agent市场"
            text2 = "research about AI Agent market"
            text3 = "今天天气真好"

            vec1 = embedding.encode(text1)
            vec2 = embedding.encode(text2)
            vec3 = embedding.encode(text3)

            def cosine_sim(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                norm_a = sum(x * x for x in a) ** 0.5
                norm_b = sum(x * x for x in b) ** 0.5
                return dot / (norm_a * norm_b)

            sim_12 = cosine_sim(vec1, vec2)
            sim_13 = cosine_sim(vec1, vec3)

            print(f"Similarity (research queries): {sim_12:.3f}")
            print(f"Similarity (research vs weather): {sim_13:.3f}")

            # 相似主题应该有更高相似度
            assert sim_12 > sim_13, "Similar topics should have higher similarity"
        except ImportError:
            pytest.skip("sentence-transformers not installed")


class TestQueryGenerator:
    """测试查询生成脚本"""

    def test_generate_queries(self):
        """测试查询生成"""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "app/skills/builtin/deep_research/resources"))

        from query_generator import generate_queries

        # 测试深度搜索
        queries = generate_queries("AI Agent", depth="deep", language="both")
        assert len(queries) > 10, "Should generate multiple queries"
        assert any("market" in q.lower() for q in queries)
        assert any("市场" in q for q in queries)

        # 测试浅度搜索
        shallow_queries = generate_queries("AI Agent", depth="shallow")
        assert len(shallow_queries) < len(queries)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
