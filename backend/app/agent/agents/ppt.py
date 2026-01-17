"""
PPTAgent - PPT 生成 Agent

实现 Manus 级别的 PPT 生成能力：
- 智能大纲生成 (OutlineGeneration)
- 内容填充与优化 (ContentFilling)
- 视觉建议 (VisualSuggestions)
- 模板匹配 (TemplateMatching)
- 与 Deep Research 无缝集成

设计原则：
- Template-Driven MVP: 基于 Marp Markdown 渲染
- 结构化输出: 每页幻灯片有明确的类型和内容
- 渐进式生成: 大纲 → 内容 → 样式 → 导出
"""
import logging
import re
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from ..base import BaseAgent
from ..types import ActionType, AgentAction, SSEEvent, SSEEventType

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class SlideType(str, Enum):
    """幻灯片类型"""
    TITLE = "title"              # 标题页
    TOC = "toc"                  # 目录页
    SECTION = "section"          # 章节分隔页
    CONTENT = "content"          # 内容页（要点列表）
    DATA = "data"                # 数据页（图表）
    IMAGE = "image"              # 图片页
    QUOTE = "quote"              # 引用页
    COMPARISON = "comparison"    # 对比页
    TIMELINE = "timeline"        # 时间线页
    CONCLUSION = "conclusion"    # 结论页
    QA = "qa"                    # Q&A页
    THANK_YOU = "thank_you"      # 感谢页


class PPTStyle(str, Enum):
    """PPT 风格"""
    BUSINESS = "business"        # 商务风
    TECH = "tech"                # 科技风
    MINIMAL = "minimal"          # 简约风
    ACADEMIC = "academic"        # 学术风
    CREATIVE = "creative"        # 创意风


class ChartType(str, Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    RADAR = "radar"
    SCATTER = "scatter"


@dataclass
class SlideContent:
    """单页幻灯片内容"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: SlideType = SlideType.CONTENT
    title: str = ""
    subtitle: str | None = None
    points: list[str] = field(default_factory=list)
    content: str | None = None  # Markdown 内容
    notes: str | None = None    # 演讲者备注

    # 数据图表相关
    chart_type: ChartType | None = None
    chart_data: dict[str, Any] | None = None

    # Mermaid 图表
    mermaid_code: str | None = None

    # 图片相关
    image_url: str | None = None
    image_caption: str | None = None

    # 布局相关
    layout: str = "default"  # default, two-column, centered, etc.

    def to_markdown(self) -> str:
        """转换为 Marp Markdown 格式"""
        lines = []

        if self.type == SlideType.TITLE:
            lines.append(f"# {self.title}")
            if self.subtitle:
                lines.append(f"\n{self.subtitle}")

        elif self.type == SlideType.TOC:
            lines.append(f"## {self.title or '目录'}")
            lines.append("")
            for i, point in enumerate(self.points, 1):
                lines.append(f"{i}. {point}")

        elif self.type == SlideType.SECTION:
            lines.append("<!-- _class: lead -->")
            lines.append(f"# {self.title}")
            if self.subtitle:
                lines.append(f"\n### {self.subtitle}")

        elif self.type == SlideType.CONTENT:
            lines.append(f"## {self.title}")
            if self.subtitle:
                lines.append(f"### {self.subtitle}")
            lines.append("")
            for point in self.points:
                lines.append(f"- {point}")

        elif self.type == SlideType.DATA:
            lines.append(f"## {self.title}")
            lines.append("")
            if self.mermaid_code:
                lines.append("```mermaid")
                lines.append(self.mermaid_code)
                lines.append("```")
            elif self.chart_data:
                # 简化的表格展示
                lines.append(self._render_chart_as_table())

        elif self.type == SlideType.QUOTE:
            lines.append(f"## {self.title}")
            lines.append("")
            if self.content:
                lines.append(f"> {self.content}")
            if self.subtitle:
                lines.append(f"\n— {self.subtitle}")

        elif self.type == SlideType.COMPARISON:
            lines.append(f"## {self.title}")
            lines.append("")
            lines.append("<!-- _class: comparison -->")
            if len(self.points) >= 2:
                # 两栏对比
                lines.append(f"| {self.points[0]} | {self.points[1]} |")
                lines.append("|---|---|")
                # 如果有更多点，作为对比内容
                for i in range(2, len(self.points), 2):
                    left = self.points[i] if i < len(self.points) else ""
                    right = self.points[i+1] if i+1 < len(self.points) else ""
                    lines.append(f"| {left} | {right} |")

        elif self.type == SlideType.CONCLUSION:
            lines.append(f"## {self.title or '结论'}")
            lines.append("")
            for i, point in enumerate(self.points, 1):
                lines.append(f"**{i}.** {point}")
                lines.append("")

        elif self.type == SlideType.THANK_YOU:
            lines.append("<!-- _class: lead -->")
            lines.append(f"# {self.title or 'Thank You'}")
            if self.subtitle:
                lines.append(f"\n{self.subtitle}")

        elif self.type == SlideType.QA:
            lines.append("<!-- _class: lead -->")
            lines.append(f"# {self.title or 'Q&A'}")
            lines.append("\n欢迎提问")

        else:
            # 默认内容页
            if self.title:
                lines.append(f"## {self.title}")
            if self.content:
                lines.append("")
                lines.append(self.content)

        # 添加备注
        if self.notes:
            lines.append("")
            lines.append("<!--")
            lines.append(f"Speaker notes: {self.notes}")
            lines.append("-->")

        return "\n".join(lines)

    def _render_chart_as_table(self) -> str:
        """将图表数据渲染为 Markdown 表格"""
        if not self.chart_data:
            return ""

        labels = self.chart_data.get("labels", [])
        datasets = self.chart_data.get("datasets", [])

        if not labels or not datasets:
            return ""

        # 简单的表格
        header = "| 项目 | " + " | ".join(d.get("label", f"数据{i}") for i, d in enumerate(datasets)) + " |"
        separator = "|" + "---|" * (len(datasets) + 1)

        rows = []
        for i, label in enumerate(labels):
            values = [str(d.get("data", [])[i]) if i < len(d.get("data", [])) else "-" for d in datasets]
            rows.append(f"| {label} | " + " | ".join(values) + " |")

        return "\n".join([header, separator] + rows)


@dataclass
class PPTOutline:
    """PPT 大纲"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    subtitle: str | None = None
    author: str | None = None
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    style: PPTStyle = PPTStyle.BUSINESS
    theme: str = "default"  # Marp theme
    slides: list[SlideContent] = field(default_factory=list)

    # 元数据
    source_content: str | None = None  # 原始内容（如研究报告）
    estimated_duration: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_marp_markdown(self) -> str:
        """转换为完整的 Marp Markdown 文档"""
        lines = []

        # Frontmatter
        lines.append("---")
        lines.append("marp: true")
        lines.append(f"theme: {self.theme}")
        lines.append("paginate: true")
        lines.append(f"title: {self.title}")
        if self.author:
            lines.append(f"author: {self.author}")
        lines.append("---")
        lines.append("")

        # 幻灯片内容
        for i, slide in enumerate(self.slides):
            if i > 0:
                lines.append("")
                lines.append("---")
                lines.append("")
            lines.append(slide.to_markdown())

        return "\n".join(lines)

    def get_slide_count(self) -> int:
        """获取幻灯片数量"""
        return len(self.slides)

    def estimate_duration(self) -> str:
        """估算演示时长"""
        count = self.get_slide_count()
        if count <= 10:
            return "5-8 分钟"
        elif count <= 15:
            return "10-15 分钟"
        elif count <= 25:
            return "20-30 分钟"
        else:
            return "30+ 分钟"


@dataclass
class PPTState:
    """PPT 生成状态"""
    outline: PPTOutline | None = None
    phase: str = "init"  # init -> analyzing -> outlining -> filling -> styling -> exporting
    current_slide_index: int = 0
    filled_count: int = 0
    style_applied: bool = False


# ==================== 核心 Agent ====================

class PPTAgent(BaseAgent):
    """PPT 生成 Agent

    工作流：
    1. 分析输入内容 → 提取关键信息
    2. 生成大纲 → 确定幻灯片结构
    3. 填充内容 → 每页详细内容
    4. 应用样式 → 模板和视觉效果
    5. 渲染导出 → PDF/HTML/PPTX
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ppt_state: PPTState | None = None

    async def _think(self) -> AsyncGenerator[SSEEvent, None]:
        """思考过程 - PPT Agent 版本"""
        logger.debug("PPTAgent thinking...")

        phase = self.ppt_state.phase if self.ppt_state else "init"

        thinking_prompts = {
            "init": "📊 Analyzing input content and identifying key themes...",
            "analyzing": "🔍 Extracting structure, data, and key points...",
            "outlining": "📝 Generating presentation outline...",
            "filling": "✍️ Filling slide content with details...",
            "styling": "🎨 Applying visual styles and themes...",
            "exporting": "📤 Preparing for export..."
        }

        yield SSEEvent(
            type=SSEEventType.THINKING,
            data={'content': thinking_prompts.get(phase, "Thinking...") + "\n"}
        )

        system_prompt = self._get_thinking_prompt(phase)

        thinking_content = ""
        async for chunk in self.llm.stream(
            messages=self.context.messages,
            system=system_prompt
        ):
            thinking_content += chunk
            yield SSEEvent(
                type=SSEEventType.THINKING,
                data={'content': chunk}
            )

        self.context.append_thinking(thinking_content)
        logger.debug(f"PPT thinking complete, phase: {phase}")

    def _get_thinking_prompt(self, phase: str) -> str:
        """获取阶段性思考提示"""
        base = """You are a professional presentation designer creating PPT slides.

Current State:
"""
        if self.ppt_state and self.ppt_state.outline:
            base += f"""- Title: {self.ppt_state.outline.title}
- Phase: {phase}
- Slides: {self.ppt_state.outline.get_slide_count()}
- Style: {self.ppt_state.outline.style.value}
"""

        phase_prompts = {
            "init": """
Analyze the user's request:
1. What is the main topic/theme?
2. Who is the target audience?
3. What is the desired length? (默认 12 页)
4. What style fits best? (business/tech/minimal/academic)

Identify if there's existing content (like a research report) to transform.""",

            "analyzing": """
For the input content, identify:
1. Main title and subtitle
2. Key sections/chapters
3. Important data points (for charts)
4. Quotable statements
5. Conclusions and recommendations

Structure this into a presentation flow.""",

            "outlining": """
Create a slide-by-slide outline:
1. Title slide
2. Table of contents (if > 10 slides)
3. Section dividers
4. Content slides (3-5 points each)
5. Data visualization slides
6. Conclusion slide
7. Q&A / Thank you slide

Each slide should have a clear purpose.""",

            "filling": """
For the current slide:
1. Write a clear, concise title
2. Develop 3-5 bullet points
3. Add speaker notes if helpful
4. Suggest any charts or visuals

Keep text minimal - presentations should be visual.""",

            "styling": """
Apply visual design:
1. Select appropriate theme
2. Ensure consistent formatting
3. Add visual hierarchy
4. Check readability

Follow presentation best practices."""
        }

        return base + phase_prompts.get(phase, "Continue with the presentation.")

    async def _decide(self) -> AgentAction:
        """决策 - PPT Agent 版本"""
        logger.debug(f"PPTAgent deciding, phase: {self.ppt_state.phase if self.ppt_state else 'init'}")

        # 初始化状态
        if not self.ppt_state:
            self.ppt_state = PPTState()

        # 获取工具
        tool_definitions = self.tools.get_llm_tool_definitions()

        if not tool_definitions:
            logger.warning("No tools available")
            return await self._generate_ppt_directly()

        system_prompt = self._get_decision_prompt()

        response = await self.llm.complete(
            messages=self.context.messages,
            system=system_prompt,
            tools=tool_definitions
        )

        if response.tool_calls:
            tool_call = response.tool_calls[0]
            self._update_phase_from_tool(tool_call["name"])

            return AgentAction(
                type=ActionType.TOOL_CALL,
                tool_name=tool_call["name"],
                tool_input=tool_call["input"],
                tool_call_id=tool_call["id"]
            )

        # 检查是否应该生成 PPT
        if self._should_generate_ppt():
            return await self._generate_ppt_directly()

        answer = response.content.strip()
        return AgentAction(
            type=ActionType.ANSWER,
            answer=answer
        )

    def _get_decision_prompt(self) -> str:
        """获取决策提示"""
        phase = self.ppt_state.phase if self.ppt_state else "init"

        base = """You are creating a professional presentation. Based on the conversation:

Available tools:
- generate_ppt_outline: Generate presentation structure
- fill_ppt_content: Fill detailed content for slides
- render_ppt: Render to HTML preview
- export_ppt: Export to PDF/HTML

Current state:
"""
        if self.ppt_state and self.ppt_state.outline:
            base += f"""- Title: {self.ppt_state.outline.title}
- Phase: {phase}
- Slides created: {self.ppt_state.outline.get_slide_count()}
"""

        phase_instructions = {
            "init": """
First, understand what the user wants:
1. If they have content to transform (research report, text), use generate_ppt_outline
2. If they want a new presentation on a topic, also use generate_ppt_outline
3. Ask clarifying questions if the request is unclear

Start by generating an outline.""",

            "outlining": """
The outline is being created. Once complete:
1. Review the slide structure
2. Use fill_ppt_content to add detailed content
3. Ensure logical flow between slides""",

            "filling": """
Content is being filled. For each slide:
1. Keep titles short and impactful
2. Limit to 3-5 bullet points
3. Add speaker notes for complex topics
4. Suggest visuals where appropriate

Once all slides are filled, proceed to render_ppt.""",

            "styling": """
Apply final touches:
1. Use render_ppt to preview
2. Adjust theme if needed
3. When ready, use export_ppt for final output""",

            "exporting": """
Generate the final presentation.
Use export_ppt with the desired format (pdf/html).
Provide the download link to the user."""
        }

        return base + phase_instructions.get(phase, "Continue building the presentation.")

    def _update_phase_from_tool(self, tool_name: str) -> None:
        """根据工具调用更新阶段"""
        if not self.ppt_state:
            return

        if tool_name == "generate_ppt_outline":
            self.ppt_state.phase = "outlining"
        elif tool_name == "fill_ppt_content":
            self.ppt_state.phase = "filling"
        elif tool_name == "render_ppt":
            self.ppt_state.phase = "styling"
        elif tool_name == "export_ppt":
            self.ppt_state.phase = "exporting"

    def _should_generate_ppt(self) -> bool:
        """判断是否应该直接生成 PPT"""
        if not self.ppt_state:
            return False

        if self.ppt_state.phase in ["styling", "exporting"]:
            return True

        if self.ppt_state.outline and self.ppt_state.outline.get_slide_count() >= 5:
            if self.ppt_state.filled_count >= self.ppt_state.outline.get_slide_count():
                return True

        return False

    async def _generate_ppt_directly(self) -> AgentAction:
        """直接生成 PPT（当没有工具时的后备方案）"""
        logger.info("Generating PPT directly...")

        system_prompt = """Generate a complete Marp Markdown presentation based on the conversation.

Include:
1. Frontmatter (marp: true, theme, paginate)
2. Title slide
3. Table of contents (if applicable)
4. Content slides (3-5 per topic)
5. Conclusion
6. Thank you slide

Use --- to separate slides.
Keep each slide concise with 3-5 bullet points max.
Use headers (##) for slide titles.
Include Mermaid diagrams for processes or relationships.

Output ONLY the Markdown content."""

        response = await self.llm.complete(
            messages=self.context.messages,
            system=system_prompt
        )

        markdown_content = response.content.strip()

        # 确保有正确的 frontmatter
        if not markdown_content.startswith("---"):
            markdown_content = """---
marp: true
theme: default
paginate: true
---

""" + markdown_content

        return AgentAction(
            type=ActionType.ANSWER,
            answer=f"Here's your presentation:\n\n```markdown\n{markdown_content}\n```\n\nYou can:\n1. Copy this to a `.md` file\n2. Use Marp CLI to convert: `marp slides.md --pdf`\n3. Or use the Marp VS Code extension for preview"
        )

    # ==================== 大纲生成方法 ====================

    def generate_outline_from_content(
        self,
        content: str,
        title: str | None = None,
        style: PPTStyle = PPTStyle.BUSINESS,
        target_slides: int = 12
    ) -> PPTOutline:
        """从内容生成大纲

        Args:
            content: 输入内容（研究报告、文本等）
            title: 演示标题（可选，自动提取）
            style: 演示风格
            target_slides: 目标幻灯片数量

        Returns:
            PPTOutline: 生成的大纲
        """
        outline = PPTOutline(
            title=title or self._extract_title(content),
            style=style,
            source_content=content
        )

        # 分析内容结构
        sections = self._parse_content_sections(content)

        # 1. 标题页
        outline.slides.append(SlideContent(
            type=SlideType.TITLE,
            title=outline.title,
            subtitle=outline.date
        ))

        # 2. 目录页（如果有多个章节）
        if len(sections) > 3:
            outline.slides.append(SlideContent(
                type=SlideType.TOC,
                title="目录",
                points=[s.get("title", f"章节 {i+1}") for i, s in enumerate(sections[:6])]
            ))

        # 3. 内容页
        max(1, (target_slides - 4) // len(sections)) if sections else 2

        for section in sections:
            # 章节分隔页
            outline.slides.append(SlideContent(
                type=SlideType.SECTION,
                title=section.get("title", ""),
                subtitle=section.get("subtitle")
            ))

            # 内容页
            points = section.get("points", [])
            for i in range(0, len(points), 4):
                chunk = points[i:i+4]
                outline.slides.append(SlideContent(
                    type=SlideType.CONTENT,
                    title=section.get("title", ""),
                    points=chunk
                ))

                if len(outline.slides) >= target_slides - 2:
                    break

        # 4. 结论页
        outline.slides.append(SlideContent(
            type=SlideType.CONCLUSION,
            title="结论",
            points=self._extract_conclusions(content)
        ))

        # 5. 感谢页
        outline.slides.append(SlideContent(
            type=SlideType.THANK_YOU,
            title="Thank You",
            subtitle="欢迎提问"
        ))

        outline.estimated_duration = outline.estimate_duration()

        return outline

    def _extract_title(self, content: str) -> str:
        """从内容提取标题"""
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line and len(line) < 100 and not line.startswith(('#', '-', '*', '>')):
                return line
        return "Presentation"

    def _parse_content_sections(self, content: str) -> list[dict[str, Any]]:
        """解析内容章节"""
        sections = []
        current_section = {"title": "", "points": []}

        lines = content.split('\n')
        for line in lines:
            line = line.strip()

            # 检测标题
            if line.startswith('## '):
                if current_section["title"] or current_section["points"]:
                    sections.append(current_section)
                current_section = {"title": line[3:].strip(), "points": []}

            elif line.startswith('### '):
                current_section["subtitle"] = line[4:].strip()

            # 检测要点
            elif line.startswith(('- ', '* ', '• ')):
                point = line[2:].strip()
                if point and len(point) < 200:
                    current_section["points"].append(point)

            elif re.match(r'^\d+[\.\)]\s+', line):
                point = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                if point and len(point) < 200:
                    current_section["points"].append(point)

        if current_section["title"] or current_section["points"]:
            sections.append(current_section)

        # 如果没有检测到章节，创建默认章节
        if not sections:
            sections = [{"title": "Overview", "points": content.split('\n')[:5]}]

        return sections

    def _extract_conclusions(self, content: str) -> list[str]:
        """提取结论要点"""
        conclusions = []

        # 查找结论部分
        patterns = [
            r'(?:结论|Conclusion|Summary|总结)[：:]\s*\n([\s\S]*?)(?=\n##|\n---|\Z)',
            r'(?:建议|Recommendation)[：:]\s*\n([\s\S]*?)(?=\n##|\n---|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                section = match.group(1)
                for line in section.split('\n'):
                    line = line.strip()
                    if line.startswith(('- ', '* ', '• ')):
                        conclusions.append(line[2:].strip())
                    elif re.match(r'^\d+[\.\)]\s+', line):
                        conclusions.append(re.sub(r'^\d+[\.\)]\s+', '', line).strip())

        if not conclusions:
            conclusions = ["关键发现总结", "下一步行动计划", "感谢聆听"]

        return conclusions[:5]


# ==================== 工厂函数 ====================

async def create_ppt_agent(
    context,
    llm,
    tools,
    memory,
    db,
    max_iterations: int = 15
) -> PPTAgent:
    """创建 PPTAgent 实例

    Args:
        context: AgentContext
        llm: BaseLLM
        tools: ToolRegistry
        memory: WorkingMemory
        db: AsyncSession
        max_iterations: 最大迭代次数

    Returns:
        PPTAgent: Agent 实例
    """
    agent = PPTAgent(
        context=context,
        llm=llm,
        tools=tools,
        memory=memory,
        db=db,
        max_iterations=max_iterations
    )

    logger.info(f"PPTAgent created with max_iterations={max_iterations}")
    return agent
