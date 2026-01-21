"""
Diagram Generation Tool - AI 流程图/架构图生成工具

基于 draw.io (mxGraph) 格式生成专业图表：
- 流程图 (Flowchart)
- 架构图 (Architecture Diagram)
- 时序图 (Sequence Diagram)
- ER 图 (Entity Relationship Diagram)
- 云架构图 (Cloud Architecture - AWS/GCP/Azure)

输出格式：draw.io XML，可在前端用 viewer.diagrams.net 渲染
"""

import json
import os
from typing import Any

from ..base import BaseTool, ToolResult
from ..risk import OperationCategory, RiskLevel


# draw.io XML 模板示例（用于 LLM prompt）
DRAWIO_EXAMPLES = {
    "flowchart": '''<mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="开始" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
      <mxGeometry x="340" y="40" width="120" height="40" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="处理步骤" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
      <mxGeometry x="340" y="120" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="" style="endArrow=classic;html=1;exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;" edge="1" parent="1" source="2" target="3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>''',

    "architecture": '''<mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="用户" style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;" vertex="1" parent="1">
      <mxGeometry x="80" y="200" width="30" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="3" value="Web 服务器" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;" vertex="1" parent="1">
      <mxGeometry x="200" y="200" width="120" height="60" as="geometry"/>
    </mxCell>
    <mxCell id="4" value="数据库" style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#f8cecc;strokeColor=#b85450;" vertex="1" parent="1">
      <mxGeometry x="400" y="190" width="80" height="80" as="geometry"/>
    </mxCell>
    <mxCell id="5" value="" style="endArrow=classic;html=1;" edge="1" parent="1" source="2" target="3">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
    <mxCell id="6" value="" style="endArrow=classic;startArrow=classic;html=1;" edge="1" parent="1" source="3" target="4">
      <mxGeometry relative="1" as="geometry"/>
    </mxCell>
  </root>
</mxGraphModel>''',
}

# 图表类型的中文描述
DIAGRAM_TYPES = {
    "flowchart": "流程图 - 展示步骤、决策和流程",
    "architecture": "架构图 - 展示系统组件和关系",
    "sequence": "时序图 - 展示对象间的交互顺序",
    "er": "ER图 - 展示数据库实体关系",
    "cloud": "云架构图 - AWS/GCP/Azure 架构",
    "mindmap": "思维导图 - 展示概念层级关系",
    "network": "网络拓扑图 - 展示网络结构",
}


class DiagramTool(BaseTool):
    """AI 图表生成工具

    使用 LLM 生成 draw.io XML 格式的专业图表。
    """

    name = "generate_diagram"
    description = """生成专业图表工具，根据描述生成 draw.io 格式的图表。
支持类型：流程图、架构图、时序图、ER图、云架构图、思维导图、网络拓扑图。
输出可直接在 draw.io 中打开编辑，也可嵌入到报告中展示。"""

    parameters = {
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "图表的详细描述，包括要展示的内容、节点、关系等"
            },
            "diagram_type": {
                "type": "string",
                "enum": list(DIAGRAM_TYPES.keys()),
                "description": f"图表类型: {', '.join(DIAGRAM_TYPES.keys())}",
                "default": "flowchart"
            },
            "title": {
                "type": "string",
                "description": "图表标题（可选）"
            },
            "style": {
                "type": "string",
                "enum": ["default", "modern", "minimal", "colorful"],
                "description": "图表风格",
                "default": "modern"
            }
        },
        "required": ["description"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.CONTENT_GENERATION]

    # 风格配色方案
    STYLE_COLORS = {
        "default": {
            "primary": "#dae8fc",
            "secondary": "#d5e8d4",
            "accent": "#fff2cc",
            "border": "#6c8ebf"
        },
        "modern": {
            "primary": "#e1d5e7",
            "secondary": "#b1ddf0",
            "accent": "#ffe6cc",
            "border": "#9673a6"
        },
        "minimal": {
            "primary": "#f5f5f5",
            "secondary": "#ffffff",
            "accent": "#e6e6e6",
            "border": "#666666"
        },
        "colorful": {
            "primary": "#ffcccc",
            "secondary": "#ccffcc",
            "accent": "#ccccff",
            "border": "#333333"
        }
    }

    def __init__(self, llm_client: Any | None = None):
        super().__init__()
        self.llm_client = llm_client
        # OpenRouter API Key
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")

    def _get_system_prompt(self, diagram_type: str, style: str) -> str:
        """生成 LLM system prompt"""
        colors = self.STYLE_COLORS.get(style, self.STYLE_COLORS["modern"])
        example = DRAWIO_EXAMPLES.get(diagram_type, DRAWIO_EXAMPLES["flowchart"])

        return f"""你是一个专业的图表设计师，擅长生成 draw.io (mxGraph) 格式的 XML 图表。

## 任务
根据用户描述生成 {DIAGRAM_TYPES.get(diagram_type, '流程图')}。

## 输出格式
必须输出完整的 mxGraphModel XML，格式如下：
```xml
<mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- 节点和边 -->
  </root>
</mxGraphModel>
```

## 风格配色
- 主色: {colors['primary']}
- 辅助色: {colors['secondary']}
- 强调色: {colors['accent']}
- 边框色: {colors['border']}

## 常用节点样式
- 矩形: style="rounded=0;whiteSpace=wrap;html=1;fillColor={colors['primary']};strokeColor={colors['border']};"
- 圆角矩形: style="rounded=1;whiteSpace=wrap;html=1;fillColor={colors['secondary']};strokeColor=#82b366;"
- 菱形(决策): style="rhombus;whiteSpace=wrap;html=1;fillColor={colors['accent']};strokeColor=#d6b656;"
- 圆柱(数据库): style="shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;"
- 人物: style="shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;"
- 云: style="ellipse;shape=cloud;whiteSpace=wrap;html=1;"

## 连接线样式
- 实线箭头: style="endArrow=classic;html=1;"
- 虚线箭头: style="endArrow=classic;html=1;dashed=1;"
- 双向箭头: style="endArrow=classic;startArrow=classic;html=1;"

## 示例
{example}

## 要求
1. 只输出 XML，不要有任何其他文字
2. 确保所有 id 唯一
3. 合理布局，节点不要重叠
4. 包含必要的连接线
5. 使用中文标签"""

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 生成图表 XML"""
        import httpx

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://tokendance.app",
                    "X-Title": "TokenDance Diagram Generator"
                },
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 8000,
                    "temperature": 0.3
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _extract_xml(self, content: str) -> str:
        """从 LLM 输出中提取 XML"""
        # 尝试提取 ```xml ``` 包裹的内容
        import re
        xml_match = re.search(r'```xml\s*(.*?)\s*```', content, re.DOTALL)
        if xml_match:
            return xml_match.group(1).strip()

        # 尝试直接找 <mxGraphModel
        mx_match = re.search(r'(<mxGraphModel.*?</mxGraphModel>)', content, re.DOTALL)
        if mx_match:
            return mx_match.group(1).strip()

        # 返回原内容
        return content.strip()

    def _validate_xml(self, xml: str) -> bool:
        """验证 XML 格式"""
        return (
            xml.startswith("<mxGraphModel") and
            xml.endswith("</mxGraphModel>") and
            "<root>" in xml and
            "</root>" in xml
        )

    async def execute(self, **kwargs: Any) -> str:
        """执行图表生成

        Args:
            description: 图表描述
            diagram_type: 图表类型
            title: 图表标题
            style: 图表风格

        Returns:
            JSON 格式的结果，包含 draw.io XML
        """
        description = kwargs.get("description", "")
        diagram_type = kwargs.get("diagram_type", "flowchart")
        title = kwargs.get("title", "")
        style = kwargs.get("style", "modern")

        if not description:
            return ToolResult(
                success=False,
                error="图表描述不能为空"
            ).to_text()

        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENROUTER_API_KEY not configured"
            ).to_text()

        try:
            # 构建 prompts
            system_prompt = self._get_system_prompt(diagram_type, style)
            user_prompt = f"请生成图表：{description}"
            if title:
                user_prompt = f"标题：{title}\n\n{user_prompt}"

            # 调用 LLM
            raw_output = await self._call_llm(system_prompt, user_prompt)

            # 提取 XML
            xml = self._extract_xml(raw_output)

            # 验证 XML
            if not self._validate_xml(xml):
                return ToolResult(
                    success=False,
                    error="生成的图表格式无效，请重试",
                    data={"raw_output": raw_output[:500]}
                ).to_text()

            # 返回成功结果
            result = ToolResult(
                success=True,
                data={
                    "type": "drawio",
                    "diagram_type": diagram_type,
                    "title": title or "Untitled",
                    "xml": xml,
                    "style": style
                },
                summary=f"已生成{DIAGRAM_TYPES.get(diagram_type, '图表')}: {title or description[:50]}"
            )
            return result.to_text()

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"生成图表失败: {e!s}"
            ).to_text()


def create_diagram_tool() -> DiagramTool:
    """创建图表生成工具实例"""
    return DiagramTool()


# 便捷访问
diagram_tool = DiagramTool()
