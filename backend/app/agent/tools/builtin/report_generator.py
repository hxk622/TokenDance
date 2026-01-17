"""
Report Generator Tool - 研究报告生成工具

生成结构化的研究报告，支持：
- Markdown 报告模板
- 自动引用管理
- 摘要生成
- 关键发现提取
"""
import logging
from datetime import datetime
from typing import Any

from ..base import BaseTool
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)


class ReportGeneratorTool(BaseTool):
    """研究报告生成工具

    根据收集的来源和发现生成结构化报告。

    功能：
    - 自动生成 Executive Summary
    - 组织 Key Findings 并添加引用
    - 识别并呈现冲突观点
    - 生成参考文献列表

    风险等级：NONE（纯生成操作）
    """

    name = "generate_report"
    description = (
        "Generate a structured research report from collected sources and findings. "
        "The report includes an executive summary, key findings with citations, "
        "analysis, conflicting viewpoints, and references."
    )
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Report title"
            },
            "sources": {
                "type": "array",
                "description": "List of source objects with url, title, snippet, and key_findings",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "title": {"type": "string"},
                        "snippet": {"type": "string"},
                        "key_findings": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            },
            "findings": {
                "type": "array",
                "description": "List of key findings to include",
                "items": {"type": "string"}
            },
            "conflicts": {
                "type": "array",
                "description": "List of conflicting viewpoints",
                "items": {"type": "string"}
            },
            "limitations": {
                "type": "array",
                "description": "List of research limitations",
                "items": {"type": "string"}
            }
        },
        "required": ["title", "sources"]
    }

    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.DOCUMENT_CREATE]
    requires_confirmation = False

    async def execute(self, **kwargs: Any) -> str:
        """生成研究报告

        Args:
            title: 报告标题
            sources: 来源列表
            findings: 关键发现
            conflicts: 冲突观点
            limitations: 研究限制

        Returns:
            str: Markdown 格式的研究报告
        """
        title = kwargs.get("title", "Research Report")
        sources = kwargs.get("sources", [])
        findings = kwargs.get("findings", [])
        conflicts = kwargs.get("conflicts", [])
        limitations = kwargs.get("limitations", [])

        logger.info(f"Generating report: {title} with {len(sources)} sources")

        report = self._generate_report(
            title=title,
            sources=sources,
            findings=findings,
            conflicts=conflicts,
            limitations=limitations
        )

        return report

    def _generate_report(
        self,
        title: str,
        sources: list[dict],
        findings: list[str],
        conflicts: list[str],
        limitations: list[str]
    ) -> str:
        """生成报告内容"""

        date_str = datetime.now().strftime("%Y-%m-%d")

        # 构建报告
        report = f"# {title}\n\n"
        report += f"**Generated**: {date_str}  \n"
        report += f"**Sources**: {len(sources)}\n\n"
        report += "---\n\n"

        # Executive Summary
        report += "## Executive Summary\n\n"
        if findings:
            summary = f"This research analyzes {len(sources)} sources to explore {title.lower()}. "
            summary += f"Key findings include: {findings[0][:100]}..."
            report += summary + "\n\n"
        else:
            report += "_Summary to be generated based on findings._\n\n"

        # Key Findings
        report += "## Key Findings\n\n"
        if findings:
            for i, finding in enumerate(findings, 1):
                # 尝试匹配引用
                citation = self._get_citation_for_finding(finding, sources)
                report += f"{i}. {finding}"
                if citation:
                    report += f" [{citation}]"
                report += "\n"
        else:
            report += "- _No specific findings recorded yet._\n"
        report += "\n"

        # Source Analysis
        report += "## Source Analysis\n\n"
        for i, source in enumerate(sources, 1):
            url = source.get("url", "")
            src_title = source.get("title", "Unknown")
            snippet = source.get("snippet", "")[:200]
            src_findings = source.get("key_findings", [])

            report += f"### [{i}] {src_title}\n\n"
            report += f"**URL**: {url}\n\n"
            if snippet:
                report += f"> {snippet}...\n\n"
            if src_findings:
                report += "**Key Points**:\n"
                for finding in src_findings[:3]:
                    report += f"- {finding}\n"
                report += "\n"

        # Conflicting Viewpoints
        if conflicts:
            report += "## Conflicting Viewpoints\n\n"
            for conflict in conflicts:
                report += f"- {conflict}\n"
            report += "\n"

        # Limitations
        report += "## Limitations & Gaps\n\n"
        if limitations:
            for limitation in limitations:
                report += f"- {limitation}\n"
        else:
            report += "- Research scope limited to available online sources\n"
            report += "- Time constraints may have affected depth of analysis\n"
        report += "\n"

        # References
        report += "## References\n\n"
        for i, source in enumerate(sources, 1):
            url = source.get("url", "")
            src_title = source.get("title", "Unknown")
            report += f"[{i}] {src_title}. {url}. Accessed: {date_str}\n"

        return report

    def _get_citation_for_finding(self, finding: str, sources: list[dict]) -> int | None:
        """尝试为发现匹配引用"""
        finding_lower = finding.lower()

        for i, source in enumerate(sources, 1):
            # 检查来源的关键发现
            src_findings = source.get("key_findings", [])
            for src_finding in src_findings:
                if src_finding.lower() in finding_lower or finding_lower in src_finding.lower():
                    return i

            # 检查来源的摘要
            snippet = source.get("snippet", "").lower()
            if len(snippet) > 20:
                # 简单的关键词匹配
                words = finding_lower.split()[:5]
                match_count = sum(1 for w in words if w in snippet)
                if match_count >= 2:
                    return i

        return None


def create_report_generator_tool() -> ReportGeneratorTool:
    """创建报告生成器工具"""
    return ReportGeneratorTool()
