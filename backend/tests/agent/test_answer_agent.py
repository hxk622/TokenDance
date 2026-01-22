"""
Tests for AnswerAgent

验证答案组装和格式化功能
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.answer_agent import (
    Answer,
    AnswerAgent,
    AnswerStyle,
    Citation,
    TaskOutput,
    detect_answer_style,
)


class TestTaskOutput:
    """TaskOutput dataclass tests"""

    def test_create_task_output(self):
        """Test creating a TaskOutput"""
        output = TaskOutput(
            task_id="task1",
            task_title="Search for info",
            output="Found relevant information about X.",
            success=True,
        )
        assert output.task_id == "task1"
        assert output.task_title == "Search for info"
        assert output.output == "Found relevant information about X."
        assert output.success is True
        assert output.citations == []

    def test_task_output_with_citations(self):
        """Test TaskOutput with citations"""
        output = TaskOutput(
            task_id="task1",
            task_title="Research",
            output="Result",
            citations=[{"url": "https://example.com", "title": "Example"}],
        )
        assert len(output.citations) == 1
        assert output.citations[0]["url"] == "https://example.com"


class TestCitation:
    """Citation dataclass tests"""

    def test_citation_to_dict(self):
        """Test Citation.to_dict()"""
        citation = Citation(
            id=1,
            url="https://example.com/article",
            title="Example Article",
            domain="example.com",
            excerpt="This is an excerpt.",
        )
        result = citation.to_dict()
        assert result["id"] == 1
        # Check nested source structure (matches frontend interface)
        assert result["source"]["url"] == "https://example.com/article"
        assert result["source"]["title"] == "Example Article"
        assert result["source"]["domain"] == "example.com"
        assert result["source"]["credibility"] == 50
        assert result["excerpt"] == "This is an excerpt."


class TestAnswer:
    """Answer dataclass tests"""

    def test_answer_to_dict(self):
        """Test Answer.to_dict()"""
        answer = Answer(
            content="This is the answer content.",
            summary="Brief summary",
            citations=[
                Citation(id=1, url="https://a.com", title="Source A", domain="a.com"),
            ],
            suggestions=["Try this", "Consider that"],
            style=AnswerStyle.DETAILED,
        )
        result = answer.to_dict()
        assert result["content"] == "This is the answer content."
        assert result["summary"] == "Brief summary"
        assert len(result["citations"]) == 1
        assert result["citations"][0]["id"] == 1
        assert result["suggestions"] == ["Try this", "Consider that"]
        assert result["style"] == "detailed"


class TestDetectAnswerStyle:
    """detect_answer_style function tests"""

    def test_concise_style(self):
        """Test detecting concise style"""
        assert detect_answer_style("简单告诉我") == AnswerStyle.CONCISE
        assert detect_answer_style("快速回答") == AnswerStyle.CONCISE
        # "什么是" maps to "what is" which triggers concise
        assert detect_answer_style("what is Python") == AnswerStyle.CONCISE
        assert detect_answer_style("Give me a brief answer") == AnswerStyle.CONCISE

    def test_structured_style(self):
        """Test detecting structured style"""
        assert detect_answer_style("列出所有选项") == AnswerStyle.STRUCTURED
        assert detect_answer_style("完整步骤教程") == AnswerStyle.STRUCTURED
        assert detect_answer_style("对比两个方案") == AnswerStyle.STRUCTURED
        assert detect_answer_style("Compare Python and JavaScript") == AnswerStyle.STRUCTURED

    def test_narrative_style(self):
        """Test detecting narrative style"""
        assert detect_answer_style("解释一下背景") == AnswerStyle.NARRATIVE
        assert detect_answer_style("介绍这个技术") == AnswerStyle.NARRATIVE
        assert detect_answer_style("Explain how it works") == AnswerStyle.NARRATIVE

    def test_default_detailed_style(self):
        """Test default to detailed style"""
        assert detect_answer_style("分析这个问题") == AnswerStyle.DETAILED
        assert detect_answer_style("Tell me about machine learning") == AnswerStyle.DETAILED


class TestAnswerAgent:
    """AnswerAgent tests"""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM"""
        mock = MagicMock()
        mock.complete = AsyncMock()
        return mock

    @pytest.fixture
    def answer_agent(self, mock_llm):
        """Create an AnswerAgent instance"""
        return AnswerAgent(mock_llm)

    @pytest.mark.asyncio
    async def test_generate_empty_outputs(self, answer_agent):
        """Test generating answer with no outputs"""
        result = await answer_agent.generate(
            task_outputs=[],
            query="What is Python?",
        )
        assert "没有产生有效输出" in result.content
        assert result.style == AnswerStyle.DETAILED

    @pytest.mark.asyncio
    async def test_generate_single_output_no_llm(self, answer_agent):
        """Test generating answer from single output without LLM"""
        output = TaskOutput(
            task_id="task1",
            task_title="Search",
            output="## Python\nPython is a programming language.\n\n1. Easy to learn\n2. Versatile",
            success=True,
        )
        result = await answer_agent.generate(
            task_outputs=[output],
            query="What is Python?",
            use_llm=False,
        )
        # Single well-structured output should not need LLM
        assert "Python" in result.content

    @pytest.mark.asyncio
    async def test_generate_multiple_outputs_uses_template(self, answer_agent):
        """Test generating answer from multiple outputs with template"""
        outputs = [
            TaskOutput(task_id="t1", task_title="Search A", output="Info from A", success=True),
            TaskOutput(task_id="t2", task_title="Search B", output="Info from B", success=True),
        ]
        result = await answer_agent.generate(
            task_outputs=outputs,
            query="Compare A and B",
            use_llm=False,
        )
        assert "Info from A" in result.content
        assert "Info from B" in result.content

    @pytest.mark.asyncio
    async def test_generate_filters_failed_outputs(self, answer_agent):
        """Test that failed outputs are filtered out"""
        outputs = [
            TaskOutput(task_id="t1", task_title="Good", output="Valid result", success=True),
            TaskOutput(task_id="t2", task_title="Bad", output="", success=False),
        ]
        result = await answer_agent.generate(
            task_outputs=outputs,
            query="Get info",
            use_llm=False,
        )
        assert "Valid result" in result.content

    @pytest.mark.asyncio
    async def test_generate_with_llm_synthesis(self, answer_agent, mock_llm):
        """Test generating answer with LLM synthesis"""
        from app.agent.llm.base import LLMResponse

        mock_llm.complete.return_value = LLMResponse(
            content="Synthesized answer combining all task results.",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        outputs = [
            TaskOutput(task_id="t1", task_title="Part 1", output="First part info", success=True),
            TaskOutput(task_id="t2", task_title="Part 2", output="Second part info", success=True),
        ]
        result = await answer_agent.generate(
            task_outputs=outputs,
            query="Combine info",
            use_llm=True,
            generate_summary=False,
        )
        assert result.content == "Synthesized answer combining all task results."
        mock_llm.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_use_llm_auto_detect(self, answer_agent):
        """Test automatic LLM usage detection"""
        # Single well-structured output - no LLM needed
        single_output = [
            TaskOutput(
                task_id="t1",
                task_title="Info",
                output="## Result\n1. Point one\n2. Point two",
                success=True,
            )
        ]
        assert answer_agent._should_use_llm(single_output, "What is X?") is False

        # Multiple outputs - needs LLM
        multi_outputs = [
            TaskOutput(task_id="t1", task_title="A", output="Info A", success=True),
            TaskOutput(task_id="t2", task_title="B", output="Info B", success=True),
        ]
        assert answer_agent._should_use_llm(multi_outputs, "What is X?") is True

        # Complex query - needs LLM
        assert answer_agent._should_use_llm(single_output, "compare and analyze") is True

    @pytest.mark.asyncio
    async def test_collect_citations(self, answer_agent):
        """Test citation collection and deduplication"""
        outputs = [
            TaskOutput(
                task_id="t1",
                task_title="Search",
                output="Info",
                citations=[
                    {"url": "https://a.com", "title": "Source A"},
                    {"url": "https://b.com", "title": "Source B"},
                ],
            ),
            TaskOutput(
                task_id="t2",
                task_title="Search 2",
                output="More info",
                citations=[
                    {"url": "https://a.com", "title": "Source A"},  # Duplicate
                    {"url": "https://c.com", "title": "Source C"},
                ],
            ),
        ]
        citations = answer_agent._collect_citations(outputs)
        # Should deduplicate based on URL
        assert len(citations) == 3
        urls = [c.url for c in citations]
        assert "https://a.com" in urls
        assert "https://b.com" in urls
        assert "https://c.com" in urls

    def test_template_format_single(self, answer_agent):
        """Test template formatting with single output"""
        outputs = [
            TaskOutput(task_id="t1", task_title="Result", output="The answer is 42.", success=True)
        ]
        result = answer_agent._template_format(outputs, "Question", AnswerStyle.DETAILED)
        assert result == "The answer is 42."

    def test_template_format_multiple_structured(self, answer_agent):
        """Test template formatting with multiple outputs in structured style"""
        outputs = [
            TaskOutput(task_id="t1", task_title="Part A", output="Content A", success=True),
            TaskOutput(task_id="t2", task_title="Part B", output="Content B", success=True),
        ]
        result = answer_agent._template_format(outputs, "Question", AnswerStyle.STRUCTURED)
        assert "### Part A" in result
        assert "Content A" in result
        assert "### Part B" in result
        assert "Content B" in result

    def test_extract_first_paragraph(self, answer_agent):
        """Test extracting first paragraph as summary"""
        content = """# Title

This is the first meaningful paragraph with content.

This is the second paragraph."""
        result = answer_agent._extract_first_paragraph(content)
        assert "first meaningful paragraph" in result


class TestAnswerStyleEnum:
    """AnswerStyle enum tests"""

    def test_style_values(self):
        """Test style enum values"""
        assert AnswerStyle.CONCISE.value == "concise"
        assert AnswerStyle.DETAILED.value == "detailed"
        assert AnswerStyle.STRUCTURED.value == "structured"
        assert AnswerStyle.NARRATIVE.value == "narrative"
