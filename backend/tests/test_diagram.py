"""
Tests for DiagramTool - AI 图表生成工具

测试内容：
- 工具初始化
- 参数验证
- XML 提取
- XML 验证
"""
import pytest

from app.agent.tools.builtin.diagram import (
    DIAGRAM_TYPES,
    DRAWIO_EXAMPLES,
    DiagramTool,
    create_diagram_tool,
)


class TestDiagramToolBasics:
    """测试 DiagramTool 基本功能"""

    def test_tool_creation(self):
        """测试工具创建"""
        tool = DiagramTool()
        assert tool.name == "generate_diagram"
        assert "流程图" in tool.description
        assert "架构图" in tool.description

    def test_create_diagram_tool_factory(self):
        """测试工厂函数"""
        tool = create_diagram_tool()
        assert isinstance(tool, DiagramTool)
        assert tool.name == "generate_diagram"

    def test_tool_parameters_schema(self):
        """测试参数 schema"""
        tool = DiagramTool()
        params = tool.parameters

        assert params["type"] == "object"
        assert "description" in params["properties"]
        assert "diagram_type" in params["properties"]
        assert "title" in params["properties"]
        assert "style" in params["properties"]
        assert "description" in params["required"]

    def test_diagram_types_defined(self):
        """测试图表类型定义"""
        expected_types = [
            "flowchart", "architecture", "sequence",
            "er", "cloud", "mindmap", "network"
        ]
        for t in expected_types:
            assert t in DIAGRAM_TYPES

    def test_drawio_examples_exist(self):
        """测试 draw.io 示例"""
        assert "flowchart" in DRAWIO_EXAMPLES
        assert "architecture" in DRAWIO_EXAMPLES
        # 验证示例是有效的 mxGraphModel XML
        for example in DRAWIO_EXAMPLES.values():
            assert "<mxGraphModel" in example
            assert "</mxGraphModel>" in example


class TestDiagramToolXmlHandling:
    """测试 XML 处理功能"""

    def setup_method(self):
        """测试前准备"""
        self.tool = DiagramTool()

    def test_extract_xml_from_markdown(self):
        """测试从 markdown 代码块中提取 XML"""
        content = '''Here is the diagram:

```xml
<mxGraphModel dx="1422" dy="794">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>
```

This is a flowchart.'''

        xml = self.tool._extract_xml(content)
        assert xml.startswith("<mxGraphModel")
        assert xml.endswith("</mxGraphModel>")

    def test_extract_xml_direct(self):
        """测试直接提取 XML"""
        content = '<mxGraphModel dx="1422" dy="794"><root><mxCell id="0"/></root></mxGraphModel>'
        xml = self.tool._extract_xml(content)
        assert xml == content

    def test_validate_valid_xml(self):
        """测试有效 XML 验证"""
        valid_xml = '''<mxGraphModel dx="1422" dy="794">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
  </root>
</mxGraphModel>'''
        assert self.tool._validate_xml(valid_xml) is True

    def test_validate_invalid_xml_no_root(self):
        """测试无效 XML - 缺少 root"""
        invalid_xml = '<mxGraphModel dx="1422"></mxGraphModel>'
        assert self.tool._validate_xml(invalid_xml) is False

    def test_validate_invalid_xml_wrong_tag(self):
        """测试无效 XML - 错误标签"""
        invalid_xml = '<svg><rect/></svg>'
        assert self.tool._validate_xml(invalid_xml) is False


class TestDiagramToolSystemPrompt:
    """测试系统 prompt 生成"""

    def setup_method(self):
        """测试前准备"""
        self.tool = DiagramTool()

    def test_system_prompt_contains_style_colors(self):
        """测试系统 prompt 包含风格配色"""
        prompt = self.tool._get_system_prompt("flowchart", "modern")
        assert "#e1d5e7" in prompt  # modern primary color
        assert "#9673a6" in prompt  # modern border color

    def test_system_prompt_contains_example(self):
        """测试系统 prompt 包含示例"""
        prompt = self.tool._get_system_prompt("architecture", "default")
        assert "<mxGraphModel" in prompt
        assert "Web 服务器" in prompt  # architecture example content

    def test_system_prompt_contains_requirements(self):
        """测试系统 prompt 包含要求"""
        prompt = self.tool._get_system_prompt("flowchart", "minimal")
        assert "只输出 XML" in prompt
        assert "确保所有 id 唯一" in prompt


class TestDiagramToolExecution:
    """测试工具执行 (需要 mock LLM)"""

    def setup_method(self):
        """测试前准备"""
        self.tool = DiagramTool()

    @pytest.mark.asyncio
    async def test_execute_missing_description(self):
        """测试缺少描述时的错误处理"""
        result = await self.tool.execute(description="")
        assert "Error" in result
        assert "图表描述不能为空" in result

    @pytest.mark.asyncio
    async def test_execute_missing_api_key(self):
        """测试缺少 API key 时的错误处理"""
        # 确保 API key 为空
        self.tool.api_key = ""
        result = await self.tool.execute(
            description="用户登录流程",
            diagram_type="flowchart"
        )
        assert "Error" in result
        assert "OPENROUTER_API_KEY" in result
