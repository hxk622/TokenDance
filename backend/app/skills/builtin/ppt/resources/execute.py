#!/usr/bin/env python3
"""
PPT 生成 Skill 的 L3 执行脚本

负责：
1. 解析输入内容/主题
2. 生成 PPT 大纲
3. 填充每页内容
4. 渲染为 Marp Markdown 格式
5. 支持导出预览
"""

import json
import logging
import sys
import tempfile
import uuid
from typing import Any

# 配置日志输出到 stderr（不污染 stdout）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# PPT 模板类型
SLIDE_TYPES = {
    "title": "标题页",
    "toc": "目录页",
    "content": "内容页",
    "two_column": "双栏页",
    "image": "图片页",
    "quote": "引用页",
    "conclusion": "结论页",
    "thank_you": "感谢页",
}


class PPTGenerator:
    """PPT 生成器"""

    def __init__(
        self,
        query: str,
        context: dict[str, Any],
        parameters: dict[str, Any],
    ):
        self.query = query
        self.context = context
        self.parameters = parameters
        self.slides: list[dict[str, Any]] = []
        self.outline_id = str(uuid.uuid4())[:8]

    def analyze_content(self) -> dict[str, Any]:
        """分析输入内容，提取主题和要点

        Returns:
            分析结果
        """
        # TODO: 使用 LLM 分析内容
        return {
            "main_topic": self.query[:50] if len(self.query) > 50 else self.query,
            "key_points": [
                "要点 1",
                "要点 2",
                "要点 3",
            ],
            "suggested_slides": 8,
        }

    def generate_outline(self) -> list[dict[str, Any]]:
        """生成 PPT 大纲

        Returns:
            幻灯片大纲列表
        """
        analysis = self.analyze_content()
        main_topic = analysis["main_topic"]

        # 生成标准大纲结构
        outline = [
            {
                "type": "title",
                "title": main_topic,
                "subtitle": "演示文稿",
                "author": self.context.get("user_name", "演讲者"),
            },
            {
                "type": "toc",
                "title": "目录",
                "items": ["背景介绍", "核心内容", "案例分析", "总结与展望"],
            },
            {
                "type": "content",
                "title": "背景介绍",
                "points": [
                    f"关于 {main_topic} 的背景",
                    "当前现状分析",
                    "为什么这个主题很重要",
                ],
            },
            {
                "type": "content",
                "title": "核心内容",
                "points": analysis["key_points"],
            },
            {
                "type": "two_column",
                "title": "对比分析",
                "left_title": "优势",
                "left_points": ["优势 1", "优势 2"],
                "right_title": "挑战",
                "right_points": ["挑战 1", "挑战 2"],
            },
            {
                "type": "content",
                "title": "案例分析",
                "points": [
                    "案例 1: 成功实践",
                    "案例 2: 经验教训",
                    "启示与借鉴",
                ],
            },
            {
                "type": "conclusion",
                "title": "总结与展望",
                "points": [
                    "核心要点回顾",
                    "未来发展方向",
                    "行动建议",
                ],
            },
            {
                "type": "thank_you",
                "title": "感谢聆听",
                "subtitle": "欢迎提问与交流",
                "contact": self.context.get("user_email", ""),
            },
        ]

        self.slides = outline
        return outline

    def render_slide(self, slide: dict[str, Any]) -> str:
        """渲染单个幻灯片为 Marp Markdown

        Args:
            slide: 幻灯片数据

        Returns:
            Markdown 文本
        """
        slide_type = slide.get("type", "content")
        lines = []

        if slide_type == "title":
            lines.append(f"# {slide['title']}")
            if slide.get("subtitle"):
                lines.append(f"\n## {slide['subtitle']}")
            if slide.get("author"):
                lines.append(f"\n**{slide['author']}**")

        elif slide_type == "toc":
            lines.append(f"# {slide['title']}")
            lines.append("")
            for i, item in enumerate(slide.get("items", []), 1):
                lines.append(f"{i}. {item}")

        elif slide_type == "content":
            lines.append(f"# {slide['title']}")
            lines.append("")
            for point in slide.get("points", []):
                lines.append(f"- {point}")

        elif slide_type == "two_column":
            lines.append(f"# {slide['title']}")
            lines.append("")
            lines.append('<div class="columns">')
            lines.append('<div class="column">')
            lines.append(f"\n### {slide.get('left_title', '左栏')}")
            for point in slide.get("left_points", []):
                lines.append(f"- {point}")
            lines.append("</div>")
            lines.append('<div class="column">')
            lines.append(f"\n### {slide.get('right_title', '右栏')}")
            for point in slide.get("right_points", []):
                lines.append(f"- {point}")
            lines.append("</div>")
            lines.append("</div>")

        elif slide_type == "quote":
            lines.append(f"# {slide['title']}")
            lines.append("")
            lines.append(f"> {slide.get('quote', '')}")
            if slide.get("author"):
                lines.append(f"\n— {slide['author']}")

        elif slide_type == "conclusion":
            lines.append(f"# {slide['title']}")
            lines.append("")
            for point in slide.get("points", []):
                lines.append(f"✓ {point}")

        elif slide_type == "thank_you":
            lines.append(f"# {slide['title']}")
            if slide.get("subtitle"):
                lines.append(f"\n{slide['subtitle']}")
            if slide.get("contact"):
                lines.append(f"\n📧 {slide['contact']}")

        else:
            lines.append(f"# {slide.get('title', 'Slide')}")

        return "\n".join(lines)

    def render_to_marp(self) -> str:
        """渲染为完整的 Marp Markdown

        Returns:
            Marp Markdown 文本
        """
        # Marp 前置配置
        header = """---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
---

"""

        # 渲染所有幻灯片
        slides_md = []
        for slide in self.slides:
            slides_md.append(self.render_slide(slide))

        # 用分页符连接
        content = header + "\n\n---\n\n".join(slides_md)
        return content

    def save_markdown(self, content: str) -> str:
        """保存 Markdown 到临时文件

        Args:
            content: Markdown 内容

        Returns:
            文件路径
        """
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".md",
            prefix=f"ppt_{self.outline_id}_",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(content)
            return f.name

    def generate(self) -> dict[str, Any]:
        """完整生成流程

        Returns:
            生成结果
        """
        logger.info(f"Starting PPT generation for: {self.query[:50]}...")

        # 1. 生成大纲
        outline = self.generate_outline()
        logger.info(f"Generated outline with {len(outline)} slides")

        # 2. 渲染为 Marp Markdown
        markdown = self.render_to_marp()
        logger.info("Rendered to Marp Markdown")

        # 3. 保存到文件
        file_path = self.save_markdown(markdown)
        logger.info(f"Saved to: {file_path}")

        return {
            "outline_id": self.outline_id,
            "slides_count": len(self.slides),
            "slides": [
                {
                    "index": i,
                    "type": s["type"],
                    "title": s.get("title", ""),
                }
                for i, s in enumerate(self.slides)
            ],
            "markdown_file": file_path,
            "markdown_preview": markdown[:500] + "..." if len(markdown) > 500 else markdown,
            "preview_url": f"/api/v1/skills/ppt/preview/{self.outline_id}",
        }


def main(input_data: dict[str, Any]) -> dict[str, Any]:
    """主函数

    Args:
        input_data: 从 stdin 接收的 JSON 数据

    Returns:
        执行结果 JSON
    """
    try:
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        parameters = input_data.get("parameters", {})

        if not query:
            return {
                "status": "failed",
                "error": "Query (content/topic) is required",
                "tokens_used": 0,
            }

        # 生成 PPT
        generator = PPTGenerator(query, context, parameters)
        result = generator.generate()

        return {
            "status": "success",
            "data": result,
            "tokens_used": 2000,  # 预估 Token 消耗
        }

    except Exception as e:
        logger.exception("PPT generation failed")
        return {
            "status": "failed",
            "error": str(e),
            "tokens_used": 0,
        }


if __name__ == "__main__":
    # 从 stdin 读取输入
    input_json = sys.stdin.read()
    input_data = json.loads(input_json)

    # 执行
    result = main(input_data)

    # 输出结果到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))
