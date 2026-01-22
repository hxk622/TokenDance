"""
Knowledge Graph Tool Tests
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.tools.builtin.knowledge_graph import (
    EDGE_TYPES,
    NODE_TYPES,
    KnowledgeGraphTool,
    create_knowledge_graph_tool,
    knowledge_graph_tool,
)


class TestKnowledgeGraphTool:
    """KnowledgeGraphTool 测试"""

    def setup_method(self):
        """设置测试环境"""
        self.tool = KnowledgeGraphTool()

    def test_tool_metadata(self):
        """测试工具元数据"""
        assert self.tool.name == "generate_knowledge_graph"
        assert "知识图谱" in self.tool.description
        assert "content" in self.tool.parameters["properties"]
        assert "graph_type" in self.tool.parameters["properties"]
        assert "content" in self.tool.parameters["required"]

    def test_node_types_defined(self):
        """测试节点类型定义"""
        assert "concept" in NODE_TYPES
        assert "source" in NODE_TYPES
        assert "finding" in NODE_TYPES
        assert "entity" in NODE_TYPES
        assert "event" in NODE_TYPES
        
        for node_type in NODE_TYPES.values():
            assert "label" in node_type
            assert "color" in node_type
            assert node_type["color"].startswith("#")

    def test_edge_types_defined(self):
        """测试边类型定义"""
        assert "relates_to" in EDGE_TYPES
        assert "cites" in EDGE_TYPES
        assert "supports" in EDGE_TYPES
        assert "contradicts" in EDGE_TYPES
        
        for edge_type in EDGE_TYPES.values():
            assert "label" in edge_type
            assert "style" in edge_type
            assert edge_type["style"] in ["solid", "dashed", "dotted"]

    def test_system_prompt_generation(self):
        """测试 system prompt 生成"""
        prompt = self.tool._get_system_prompt("concept", 30)
        
        assert "知识图谱" in prompt
        assert "nodes" in prompt
        assert "edges" in prompt
        assert "JSON" in prompt
        assert "30" in prompt  # max_nodes

    def test_system_prompt_different_types(self):
        """测试不同图谱类型的 prompt"""
        types = ["concept", "citation", "finding", "timeline", "mixed"]
        
        for graph_type in types:
            prompt = self.tool._get_system_prompt(graph_type, 20)
            assert "知识图谱" in prompt or "提取" in prompt

    def test_extract_json_from_code_block(self):
        """测试从代码块提取 JSON"""
        content = '''```json
{
  "nodes": [{"id": "a", "label": "A"}],
  "edges": []
}
```'''
        result = self.tool._extract_json(content)
        
        assert "nodes" in result
        assert len(result["nodes"]) == 1
        assert result["nodes"][0]["id"] == "a"

    def test_extract_json_direct(self):
        """测试直接提取 JSON"""
        content = '''{"nodes": [{"id": "b", "label": "B"}], "edges": []}'''
        result = self.tool._extract_json(content)
        
        assert "nodes" in result
        assert result["nodes"][0]["id"] == "b"

    def test_extract_json_with_text(self):
        """测试带有额外文本的 JSON 提取"""
        content = '''Here is the graph:
{"nodes": [{"id": "c", "label": "C"}], "edges": []}
Hope this helps!'''
        result = self.tool._extract_json(content)
        
        assert "nodes" in result

    def test_validate_graph_valid(self):
        """测试验证有效图谱"""
        data = {
            "nodes": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B"},
            ],
            "edges": [
                {"source": "a", "target": "b"},
            ],
        }
        
        is_valid, error = self.tool._validate_graph(data)
        assert is_valid
        assert error == ""

    def test_validate_graph_missing_nodes(self):
        """测试缺少 nodes 字段"""
        data = {"edges": []}
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "nodes" in error

    def test_validate_graph_missing_edges(self):
        """测试缺少 edges 字段"""
        data = {"nodes": []}
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "edges" in error

    def test_validate_graph_invalid_edge_source(self):
        """测试边的 source 不存在"""
        data = {
            "nodes": [{"id": "a", "label": "A"}],
            "edges": [{"source": "nonexistent", "target": "a"}],
        }
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "source" in error

    def test_validate_graph_invalid_edge_target(self):
        """测试边的 target 不存在"""
        data = {
            "nodes": [{"id": "a", "label": "A"}],
            "edges": [{"source": "a", "target": "nonexistent"}],
        }
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "target" in error

    def test_validate_graph_missing_node_id(self):
        """测试节点缺少 id"""
        data = {
            "nodes": [{"label": "A"}],
            "edges": [],
        }
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "id" in error

    def test_validate_graph_missing_node_label(self):
        """测试节点缺少 label"""
        data = {
            "nodes": [{"id": "a"}],
            "edges": [],
        }
        
        is_valid, error = self.tool._validate_graph(data)
        assert not is_valid
        assert "label" in error

    def test_enrich_graph_adds_colors(self):
        """测试补充节点颜色"""
        data = {
            "nodes": [
                {"id": "a", "label": "A", "type": "concept"},
                {"id": "b", "label": "B", "type": "source"},
            ],
            "edges": [],
        }
        
        result = self.tool._enrich_graph(data)
        
        assert result["nodes"][0]["color"] == NODE_TYPES["concept"]["color"]
        assert result["nodes"][1]["color"] == NODE_TYPES["source"]["color"]

    def test_enrich_graph_adds_default_importance(self):
        """测试补充默认 importance"""
        data = {
            "nodes": [{"id": "a", "label": "A"}],
            "edges": [],
        }
        
        result = self.tool._enrich_graph(data)
        
        assert result["nodes"][0]["importance"] == 5

    def test_enrich_graph_adds_edge_style(self):
        """测试补充边样式"""
        data = {
            "nodes": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B"},
            ],
            "edges": [
                {"source": "a", "target": "b", "type": "cites"},
            ],
        }
        
        result = self.tool._enrich_graph(data)
        
        assert result["edges"][0]["style"] == EDGE_TYPES["cites"]["style"]

    def test_enrich_graph_adds_default_strength(self):
        """测试补充默认 strength"""
        data = {
            "nodes": [
                {"id": "a", "label": "A"},
                {"id": "b", "label": "B"},
            ],
            "edges": [{"source": "a", "target": "b"}],
        }
        
        result = self.tool._enrich_graph(data)
        
        assert result["edges"][0]["strength"] == 5

    def test_enrich_graph_preserves_existing_values(self):
        """测试保留已有值"""
        data = {
            "nodes": [
                {"id": "a", "label": "A", "color": "#ff0000", "importance": 10},
            ],
            "edges": [],
        }
        
        result = self.tool._enrich_graph(data)
        
        assert result["nodes"][0]["color"] == "#ff0000"
        assert result["nodes"][0]["importance"] == 10

    @pytest.mark.asyncio
    async def test_execute_empty_content(self):
        """测试空内容执行"""
        result = await self.tool.execute(content="")
        
        assert "Error" in result
        assert "不能为空" in result

    @pytest.mark.asyncio
    async def test_execute_no_api_key(self):
        """测试无 API key"""
        tool = KnowledgeGraphTool()
        tool.api_key = ""
        
        result = await tool.execute(content="test content")
        
        assert "Error" in result
        assert "OPENROUTER_API_KEY" in result

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行"""
        mock_llm_response = '''```json
{
    "nodes": [
        {"id": "ai", "label": "人工智能", "type": "concept", "importance": 8},
        {"id": "ml", "label": "机器学习", "type": "concept", "importance": 7}
    ],
    "edges": [
        {"source": "ai", "target": "ml", "label": "包含", "type": "part_of", "strength": 8}
    ],
    "metadata": {
        "central_node": "ai",
        "clusters": ["AI 技术"]
    }
}
```'''
        
        with patch.object(self.tool, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response
            self.tool.api_key = "test_key"
            
            result = await self.tool.execute(
                content="人工智能和机器学习的关系",
                graph_type="concept",
                title="AI 概念图"
            )
            
            # to_text() returns summary for success
            assert "已生成知识图谱" in result
            assert "2 个节点" in result
            assert "1 条边" in result

    @pytest.mark.asyncio
    async def test_execute_with_focus_entities(self):
        """测试带 focus_entities 的执行"""
        mock_llm_response = '''{"nodes": [{"id": "a", "label": "A"}], "edges": []}'''
        
        with patch.object(self.tool, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response
            self.tool.api_key = "test_key"
            
            await self.tool.execute(
                content="test",
                focus_entities=["entity1", "entity2"]
            )
            
            # 检查 prompt 中包含 focus_entities
            call_args = mock_llm.call_args[0]
            assert "entity1" in call_args[1] or "entity2" in call_args[1]

    @pytest.mark.asyncio
    async def test_execute_json_parse_error(self):
        """测试 JSON 解析错误"""
        with patch.object(self.tool, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = "invalid json {"
            self.tool.api_key = "test_key"
            
            result = await self.tool.execute(content="test")
            
            assert "Error" in result
            assert "解析" in result or "失败" in result

    @pytest.mark.asyncio
    async def test_execute_invalid_graph(self):
        """测试无效图谱数据"""
        mock_llm_response = '''{"nodes": [], "edges": [{"source": "x", "target": "y"}]}'''
        
        with patch.object(self.tool, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = mock_llm_response
            self.tool.api_key = "test_key"
            
            result = await self.tool.execute(content="test")
            
            assert "Error" in result
            assert "无效" in result or "不存在" in result


class TestKnowledgeGraphToolFactory:
    """工厂函数和便捷访问测试"""

    def test_create_knowledge_graph_tool(self):
        """测试工厂函数"""
        tool = create_knowledge_graph_tool()
        assert isinstance(tool, KnowledgeGraphTool)
        assert tool.name == "generate_knowledge_graph"

    def test_knowledge_graph_tool_singleton(self):
        """测试便捷访问实例"""
        assert isinstance(knowledge_graph_tool, KnowledgeGraphTool)
        assert knowledge_graph_tool.name == "generate_knowledge_graph"


class TestGraphTypes:
    """测试不同图谱类型"""

    def setup_method(self):
        self.tool = KnowledgeGraphTool()

    @pytest.mark.parametrize("graph_type,expected_keyword", [
        ("concept", "概念"),
        ("citation", "引用"),
        ("finding", "发现"),
        ("timeline", "事件"),
        ("mixed", "综合"),
    ])
    def test_graph_type_prompts(self, graph_type, expected_keyword):
        """测试不同图谱类型生成的 prompt 包含相应关键词"""
        prompt = self.tool._get_system_prompt(graph_type, 30)
        assert expected_keyword in prompt or "知识图谱" in prompt
