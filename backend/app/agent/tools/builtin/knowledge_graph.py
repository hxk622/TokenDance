"""
Knowledge Graph Tool - AI 知识图谱生成工具

生成结构化的知识图谱数据，用于可视化展示：
- 概念关系图 (Concept Relationships)
- 引用网络 (Citation Networks)
- 发现关联 (Finding Connections)
- 时间线网络 (Timeline Networks)

输出格式：JSON (nodes + edges)，前端用 Cytoscape.js 渲染
"""

import json
import os
from typing import Any

from ..base import BaseTool, ToolResult
from ..risk import OperationCategory, RiskLevel

# 节点类型定义
NODE_TYPES = {
    "concept": {"label": "概念", "color": "#6366f1"},      # 紫色 - 核心概念
    "source": {"label": "来源", "color": "#10b981"},       # 绿色 - 信息来源
    "finding": {"label": "发现", "color": "#f59e0b"},      # 橙色 - 研究发现
    "section": {"label": "章节", "color": "#3b82f6"},      # 蓝色 - 报告章节
    "entity": {"label": "实体", "color": "#ec4899"},       # 粉色 - 人/组织/产品
    "event": {"label": "事件", "color": "#ef4444"},        # 红色 - 时间事件
    "question": {"label": "问题", "color": "#8b5cf6"},     # 紫罗兰 - 研究问题
}

# 边类型定义
EDGE_TYPES = {
    "relates_to": {"label": "相关", "style": "solid"},
    "cites": {"label": "引用", "style": "dashed"},
    "supports": {"label": "支持", "style": "solid"},
    "contradicts": {"label": "矛盾", "style": "dotted"},
    "leads_to": {"label": "导致", "style": "solid"},
    "part_of": {"label": "属于", "style": "solid"},
    "derived_from": {"label": "来自", "style": "dashed"},
    "answers": {"label": "回答", "style": "solid"},
}


class KnowledgeGraphTool(BaseTool):
    """AI 知识图谱生成工具

    使用 LLM 从文本中提取实体和关系，生成知识图谱数据。
    """

    name = "generate_knowledge_graph"
    description = """生成知识图谱工具，从研究内容中提取实体和关系，生成可视化知识图谱。
支持：概念关系图、引用网络、发现关联、时间线网络等。
输出可在报告中嵌入展示，支持交互式探索。"""

    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要分析的文本内容（研究报告、文章摘要等）"
            },
            "graph_type": {
                "type": "string",
                "enum": ["concept", "citation", "finding", "timeline", "mixed"],
                "description": "图谱类型: concept(概念图)、citation(引用网络)、finding(发现关联)、timeline(时间线)、mixed(混合)",
                "default": "concept"
            },
            "title": {
                "type": "string",
                "description": "图谱标题（可选）"
            },
            "focus_entities": {
                "type": "array",
                "items": {"type": "string"},
                "description": "重点关注的实体列表（可选，用于过滤）"
            },
            "max_nodes": {
                "type": "integer",
                "description": "最大节点数（默认30，避免过于复杂）",
                "default": 30
            },
            "include_weights": {
                "type": "boolean",
                "description": "是否包含关系权重",
                "default": True
            }
        },
        "required": ["content"]
    }

    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.CONTENT_GENERATION]

    def __init__(self, llm_client: Any | None = None):
        super().__init__()
        self.llm_client = llm_client
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")

    def _get_system_prompt(self, graph_type: str, max_nodes: int) -> str:
        """生成 LLM system prompt"""
        type_descriptions = {
            "concept": "提取核心概念及其关系，展示知识结构",
            "citation": "提取引用来源及其被引用关系",
            "finding": "提取研究发现及其支持/矛盾关系",
            "timeline": "提取事件及其时间顺序和因果关系",
            "mixed": "综合提取概念、来源、发现等多种实体"
        }

        return f"""你是一个专业的知识图谱构建专家，擅长从文本中提取实体和关系。

## 任务
从给定文本中提取实体和关系，构建{type_descriptions.get(graph_type, '知识图谱')}。

## 输出格式
必须输出严格的 JSON 格式：
```json
{{
  "nodes": [
    {{
      "id": "unique_id_1",
      "label": "节点显示名称",
      "type": "concept|source|finding|section|entity|event|question",
      "importance": 1-10,
      "description": "简短描述（可选）"
    }}
  ],
  "edges": [
    {{
      "source": "source_node_id",
      "target": "target_node_id",
      "label": "关系名称",
      "type": "relates_to|cites|supports|contradicts|leads_to|part_of|derived_from|answers",
      "strength": 1-10
    }}
  ],
  "metadata": {{
    "central_node": "最核心节点的id",
    "clusters": ["主题1", "主题2"]
  }}
}}
```

## 节点类型说明
- concept: 核心概念、术语、理论
- source: 引用来源、参考文献
- finding: 研究发现、结论
- section: 报告/文章章节
- entity: 人物、组织、产品、地点
- event: 事件、里程碑
- question: 研究问题、待解决问题

## 边类型说明
- relates_to: 一般关联关系
- cites: 引用关系
- supports: 支持/证实关系
- contradicts: 矛盾/反对关系
- leads_to: 因果/导致关系
- part_of: 包含/隶属关系
- derived_from: 派生/来源关系
- answers: 回答问题关系

## 要求
1. 只输出 JSON，不要有任何其他文字
2. 节点 id 必须唯一，使用英文下划线命名
3. label 使用中文
4. 最多生成 {max_nodes} 个节点
5. importance 和 strength 在 1-10 之间
6. 确保所有边的 source 和 target 都是存在的节点 id
7. 识别最核心的节点作为 central_node"""

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 生成知识图谱数据"""
        import httpx

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://tokendance.app",
                    "X-Title": "TokenDance Knowledge Graph Generator"
                },
                json={
                    "model": "anthropic/claude-sonnet-4",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "max_tokens": 8000,
                    "temperature": 0.2  # 低温度确保结构化输出
                }
            )
            response.raise_for_status()
            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            return content

    def _extract_json(self, content: str) -> dict[str, Any]:
        """从 LLM 输出中提取 JSON"""
        import re

        # 尝试提取 ```json ``` 包裹的内容
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # 尝试直接解析
            json_str = content.strip()

        # 尝试找到 JSON 对象
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        if start != -1 and end > start:
            json_str = json_str[start:end]

        result: dict[str, Any] = json.loads(json_str)
        return result

    def _validate_graph(self, data: dict[str, Any]) -> tuple[bool, str]:
        """验证图谱数据结构"""
        if "nodes" not in data or "edges" not in data:
            return False, "缺少 nodes 或 edges 字段"

        if not isinstance(data["nodes"], list):
            return False, "nodes 必须是数组"

        if not isinstance(data["edges"], list):
            return False, "edges 必须是数组"

        # 收集所有节点 id
        node_ids = set()
        for node in data["nodes"]:
            if "id" not in node or "label" not in node:
                return False, "节点缺少 id 或 label 字段"
            node_ids.add(node["id"])

        # 验证边的 source 和 target
        for edge in data["edges"]:
            if "source" not in edge or "target" not in edge:
                return False, "边缺少 source 或 target 字段"
            if edge["source"] not in node_ids:
                return False, f"边的 source '{edge['source']}' 不存在"
            if edge["target"] not in node_ids:
                return False, f"边的 target '{edge['target']}' 不存在"

        return True, ""

    def _enrich_graph(self, data: dict[str, Any]) -> dict[str, Any]:
        """补充图谱的默认值和颜色"""
        # 为节点添加颜色
        for node in data["nodes"]:
            node_type = node.get("type", "concept")
            if node_type in NODE_TYPES:
                node["color"] = node.get("color") or NODE_TYPES[node_type]["color"]
            else:
                node["color"] = NODE_TYPES["concept"]["color"]

            # 默认 importance
            if "importance" not in node:
                node["importance"] = 5

        # 为边添加样式
        for edge in data["edges"]:
            edge_type = edge.get("type", "relates_to")
            if edge_type in EDGE_TYPES:
                edge["style"] = edge.get("style") or EDGE_TYPES[edge_type]["style"]
            else:
                edge["style"] = "solid"

            # 默认 strength
            if "strength" not in edge:
                edge["strength"] = 5

        return data

    async def execute(self, **kwargs: Any) -> str:
        """执行知识图谱生成

        Args:
            content: 要分析的文本内容
            graph_type: 图谱类型
            title: 图谱标题
            focus_entities: 重点关注的实体
            max_nodes: 最大节点数
            include_weights: 是否包含权重

        Returns:
            JSON 格式的结果，包含知识图谱数据
        """
        content = kwargs.get("content", "")
        graph_type = kwargs.get("graph_type", "concept")
        title = kwargs.get("title", "")
        focus_entities = kwargs.get("focus_entities", [])
        max_nodes = kwargs.get("max_nodes", 30)
        # Note: include_weights is accepted but currently always True
        _ = kwargs.get("include_weights", True)

        if not content:
            return ToolResult(
                success=False,
                error="分析内容不能为空"
            ).to_text()

        if not self.api_key:
            return ToolResult(
                success=False,
                error="OPENROUTER_API_KEY not configured"
            ).to_text()

        try:
            # 构建 prompts
            system_prompt = self._get_system_prompt(graph_type, max_nodes)
            user_prompt = f"请从以下内容中提取知识图谱：\n\n{content}"

            if focus_entities:
                user_prompt += f"\n\n重点关注以下实体：{', '.join(focus_entities)}"

            if title:
                user_prompt = f"图谱主题：{title}\n\n{user_prompt}"

            # 调用 LLM
            raw_output = await self._call_llm(system_prompt, user_prompt)

            # 提取 JSON
            graph_data = self._extract_json(raw_output)

            # 验证数据
            is_valid, error_msg = self._validate_graph(graph_data)
            if not is_valid:
                return ToolResult(
                    success=False,
                    error=f"生成的图谱数据无效: {error_msg}",
                    data={"raw_output": raw_output[:500]}
                ).to_text()

            # 补充默认值
            graph_data = self._enrich_graph(graph_data)

            # 添加元信息
            if "metadata" not in graph_data:
                graph_data["metadata"] = {}

            graph_data["metadata"]["graph_type"] = graph_type
            graph_data["metadata"]["title"] = title or "Knowledge Graph"
            graph_data["metadata"]["node_count"] = len(graph_data["nodes"])
            graph_data["metadata"]["edge_count"] = len(graph_data["edges"])

            # 返回成功结果
            result = ToolResult(
                success=True,
                data={
                    "type": "knowledge_graph",
                    "graph_type": graph_type,
                    "title": title or "Knowledge Graph",
                    "graph": graph_data,
                },
                summary=f"已生成知识图谱: {len(graph_data['nodes'])} 个节点, {len(graph_data['edges'])} 条边"
            )
            return result.to_text()

        except json.JSONDecodeError as e:
            return ToolResult(
                success=False,
                error=f"解析图谱数据失败: {e!s}"
            ).to_text()
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"生成知识图谱失败: {e!s}"
            ).to_text()


def create_knowledge_graph_tool() -> KnowledgeGraphTool:
    """创建知识图谱生成工具实例"""
    return KnowledgeGraphTool()


# 便捷访问
knowledge_graph_tool = KnowledgeGraphTool()
