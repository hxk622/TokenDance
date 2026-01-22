"""
AnswerAgent - 答案组装与格式化模块

职责：
1. 收集和组装多个 Task 的输出
2. 去重和合并相似内容
3. 格式化为用户友好的格式
4. 聚合引用来源
5. 根据用户语言适配

设计原则：
- 简单任务使用模板输出（快速、低成本）
- 复杂任务使用 LLM 综合（高质量）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agent.llm.base import BaseLLM, LLMMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


# ========== 数据结构 ==========


class AnswerStyle(str, Enum):
    """答案风格"""
    CONCISE = "concise"       # 简洁：直接回答
    DETAILED = "detailed"     # 详细：完整解释
    STRUCTURED = "structured" # 结构化：分点列出
    NARRATIVE = "narrative"   # 叙述：流畅文章


@dataclass
class TaskOutput:
    """单个 Task 的输出"""
    task_id: str
    task_title: str
    output: str
    success: bool = True
    citations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Citation:
    """引用来源"""
    id: int
    url: str
    title: str
    domain: str = ""
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict matching frontend Citation interface"""
        return {
            "id": self.id,
            "source": {
                "url": self.url,
                "title": self.title,
                "domain": self.domain,
                "credibility": 50,  # Default credibility
                "credibilityLevel": "moderate",
            },
            "excerpt": self.excerpt,
        }


@dataclass
class Answer:
    """最终答案"""
    content: str                              # 主要答案内容
    summary: str = ""                         # 简短摘要
    citations: list[Citation] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)  # 后续建议
    style: AnswerStyle = AnswerStyle.DETAILED

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content,
            "summary": self.summary,
            "citations": [c.to_dict() for c in self.citations],
            "suggestions": self.suggestions,
            "style": self.style.value,
        }


# ========== Prompts ==========


SYNTHESIS_PROMPT = """You are an expert at synthesizing information into clear, well-organized answers.

## User's Question
{question}

## Task Results
{task_results}

## Instructions
1. Synthesize the task results into a coherent, comprehensive answer
2. Organize information logically with clear structure
3. Use markdown formatting (headers, lists, code blocks as appropriate)
4. Highlight key insights and findings
5. Be concise but complete - don't pad with unnecessary content
6. If there are conflicting information, acknowledge it
7. Write in the same language as the user's question

## Output Format
Provide your answer directly, without any wrapper tags. Use markdown for formatting.
"""

SUMMARY_PROMPT = """Summarize the following answer in 1-2 sentences. Be concise and capture the key point.

Answer:
{answer}

Summary (1-2 sentences):"""

SUGGESTIONS_PROMPT = """Based on the user's question and the answer provided, suggest 2-3 follow-up questions or next steps the user might find helpful.

Question: {question}

Answer Summary: {summary}

Provide 2-3 brief suggestions (one per line, no numbering):"""


# ========== AnswerAgent ==========


class AnswerAgent:
    """
    答案组装与格式化 Agent

    使用示例:
    ```python
    agent = AnswerAgent(llm)

    # 简单模式：模板组装
    answer = await agent.generate(
        task_outputs=outputs,
        query="What is Python?",
        use_llm=False
    )

    # 复杂模式：LLM 综合
    answer = await agent.generate(
        task_outputs=outputs,
        query="Compare Python and JavaScript for web development",
        use_llm=True
    )
    ```
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化 AnswerAgent

        Args:
            llm: LLM 客户端（用于复杂综合）
        """
        self.llm = llm

    async def generate(
        self,
        task_outputs: list[TaskOutput],
        query: str,
        use_llm: bool | None = None,
        style: AnswerStyle = AnswerStyle.DETAILED,
        generate_summary: bool = True,
        generate_suggestions: bool = False,
    ) -> Answer:
        """
        生成最终答案

        Args:
            task_outputs: 各 Task 的输出
            query: 用户原始问题
            use_llm: 是否使用 LLM 综合（None=自动判断）
            style: 答案风格
            generate_summary: 是否生成摘要
            generate_suggestions: 是否生成建议

        Returns:
            Answer: 格式化后的最终答案
        """
        logger.info(f"AnswerAgent generating answer for {len(task_outputs)} task outputs")

        # 过滤成功的输出
        successful_outputs = [o for o in task_outputs if o.success and o.output.strip()]

        if not successful_outputs:
            return Answer(
                content="抱歉，任务执行过程中没有产生有效输出。",
                summary="任务执行失败",
                style=style,
            )

        # 自动判断是否使用 LLM
        if use_llm is None:
            use_llm = self._should_use_llm(successful_outputs, query)

        # 收集引用
        citations = self._collect_citations(successful_outputs)

        # 生成答案内容
        if use_llm:
            content = await self._llm_synthesize(successful_outputs, query, style)
        else:
            content = self._template_format(successful_outputs, query, style)

        # 生成摘要
        summary = ""
        if generate_summary and use_llm:
            summary = await self._generate_summary(content)
        elif generate_summary:
            summary = self._extract_first_paragraph(content)

        # 生成建议
        suggestions = []
        if generate_suggestions and use_llm:
            suggestions = await self._generate_suggestions(query, summary or content[:500])

        return Answer(
            content=content,
            summary=summary,
            citations=citations,
            suggestions=suggestions,
            style=style,
        )

    def _should_use_llm(self, outputs: list[TaskOutput], query: str) -> bool:
        """
        判断是否应该使用 LLM 综合

        规则：
        - 单个输出且内容完整 → 不需要
        - 多个输出需要合并 → 需要
        - 查询复杂（对比、分析）→ 需要
        """
        # 单个输出，内容已经完整
        if len(outputs) == 1:
            output = outputs[0].output
            # 如果输出已经很结构化，不需要再综合
            if len(output) > 100 and ("##" in output or "1." in output):
                return False

        # 多个输出需要合并
        if len(outputs) > 1:
            return True

        # 复杂查询关键词
        complex_keywords = [
            "对比", "比较", "分析", "总结", "评估",
            "compare", "analyze", "summarize", "evaluate", "versus", "vs"
        ]
        query_lower = query.lower()
        if any(kw in query_lower for kw in complex_keywords):
            return True

        return False

    def _collect_citations(self, outputs: list[TaskOutput]) -> list[Citation]:
        """收集并去重所有引用"""
        seen_urls: set[str] = set()
        citations: list[Citation] = []
        citation_id = 1

        for output in outputs:
            for cite_data in output.citations:
                url = cite_data.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    citations.append(Citation(
                        id=citation_id,
                        url=url,
                        title=cite_data.get("title", ""),
                        domain=cite_data.get("domain", ""),
                        excerpt=cite_data.get("excerpt", ""),
                    ))
                    citation_id += 1

        return citations

    def _template_format(
        self,
        outputs: list[TaskOutput],
        query: str,
        style: AnswerStyle,
    ) -> str:
        """模板方式格式化（快速、低成本）"""
        if len(outputs) == 1:
            # 单个输出，直接返回
            return outputs[0].output

        # 多个输出，按任务组织
        parts = []

        for output in outputs:
            if style == AnswerStyle.STRUCTURED:
                parts.append(f"### {output.task_title}\n\n{output.output}")
            else:
                parts.append(output.output)

        if style == AnswerStyle.STRUCTURED:
            return "\n\n".join(parts)
        else:
            # 用分隔符连接
            return "\n\n---\n\n".join(parts)

    async def _llm_synthesize(
        self,
        outputs: list[TaskOutput],
        query: str,
        style: AnswerStyle,
    ) -> str:
        """LLM 综合（高质量）"""
        # 构建任务结果文本
        task_results_parts = []
        for i, output in enumerate(outputs, 1):
            task_results_parts.append(
                f"### Task {i}: {output.task_title}\n{output.output}"
            )
        task_results = "\n\n".join(task_results_parts)

        prompt = SYNTHESIS_PROMPT.format(
            question=query,
            task_results=task_results,
        )

        # 根据风格调整 system prompt
        style_instructions = {
            AnswerStyle.CONCISE: "Be very concise and direct. Avoid unnecessary elaboration.",
            AnswerStyle.DETAILED: "Provide comprehensive detail while remaining organized.",
            AnswerStyle.STRUCTURED: "Use clear headings, bullet points, and numbered lists.",
            AnswerStyle.NARRATIVE: "Write in a flowing, narrative style like an article.",
        }

        system = f"You are a helpful assistant. {style_instructions.get(style, '')}"

        try:
            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system=system,
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            # 回退到模板格式
            return self._template_format(outputs, query, style)

    async def _generate_summary(self, content: str) -> str:
        """生成摘要"""
        if len(content) < 200:
            return content

        prompt = SUMMARY_PROMPT.format(answer=content[:2000])

        try:
            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system="You are concise and precise.",
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._extract_first_paragraph(content)

    async def _generate_suggestions(self, query: str, summary: str) -> list[str]:
        """生成后续建议"""
        prompt = SUGGESTIONS_PROMPT.format(
            question=query,
            summary=summary,
        )

        try:
            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system="Provide brief, actionable suggestions.",
            )

            # 解析建议（每行一个）
            lines = response.content.strip().split("\n")
            suggestions = [
                line.strip().lstrip("•-123456789.").strip()
                for line in lines
                if line.strip() and len(line.strip()) > 5
            ]
            return suggestions[:3]  # 最多 3 个

        except Exception as e:
            logger.error(f"Suggestions generation failed: {e}")
            return []

    def _extract_first_paragraph(self, content: str) -> str:
        """提取第一段作为摘要"""
        # 跳过标题
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 20:
                # 截断到第一句或 200 字符
                if "。" in line:
                    return line.split("。")[0] + "。"
                if ". " in line:
                    return line.split(". ")[0] + "."
                return line[:200] + "..." if len(line) > 200 else line
        return content[:200] + "..." if len(content) > 200 else content


# ========== 辅助函数 ==========


def detect_answer_style(query: str) -> AnswerStyle:
    """
    根据查询自动检测答案风格

    Args:
        query: 用户查询

    Returns:
        AnswerStyle: 推荐的答案风格
    """
    query_lower = query.lower()

    # 简洁风格关键词
    concise_keywords = [
        "简单", "快速", "一句话", "是什么",
        "brief", "quick", "short", "what is"
    ]
    if any(kw in query_lower for kw in concise_keywords):
        return AnswerStyle.CONCISE

    # 结构化风格关键词
    structured_keywords = [
        "列出", "步骤", "清单", "对比", "比较",
        "list", "steps", "checklist", "compare", "versus"
    ]
    if any(kw in query_lower for kw in structured_keywords):
        return AnswerStyle.STRUCTURED

    # 叙述风格关键词
    narrative_keywords = [
        "解释", "介绍", "讲述", "故事",
        "explain", "introduce", "describe", "story"
    ]
    if any(kw in query_lower for kw in narrative_keywords):
        return AnswerStyle.NARRATIVE

    # 默认详细风格
    return AnswerStyle.DETAILED
