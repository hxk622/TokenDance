"""
Findings Extractor Service - 研究发现提取服务

从 Deep Research 的输出中提取结构化的研究发现：
- 从研究报告提取关键段落
- 识别数据点（数字、百分比、对比）
- 提取可引用语句
- 从报告中提取来源链接
"""
import logging
import re
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from ..models.research_findings import (
    DataPoint,
    DataPointType,
    FindingImportance,
    Quote,
    ResearchFinding,
    ResearchFindings,
    Source,
)

logger = logging.getLogger(__name__)


class FindingsExtractor:
    """研究发现提取器

    从 Deep Research 的报告输出中提取结构化的研究发现，
    用于生成 PPT、报告等。

    使用示例:
        extractor = FindingsExtractor(session_id="research_123")
        findings = await extractor.extract_all(
            report_markdown=report_content
        )
    """

    def __init__(self, session_id: str, topic: str = ""):
        self.session_id = session_id
        self.topic = topic

    async def extract_all(
        self,
        report_markdown: str | None = None,
        sources_list: list[dict] | None = None,
        llm=None  # 可选：使用 LLM 增强提取
    ) -> ResearchFindings:
        """提取所有研究发现

        Args:
            report_markdown: 研究报告 Markdown
            sources_list: 来源列表 [{'url': ..., 'title': ..., 'domain': ...}]
            llm: 可选的 LLM 实例，用于增强提取

        Returns:
            ResearchFindings: 结构化的研究发现
        """
        findings = ResearchFindings(
            session_id=self.session_id,
            topic=self.topic or self._extract_topic(report_markdown),
            summary=""
        )

        # 从报告提取
        if report_markdown:
            self._extract_from_report(report_markdown, findings)

        # 从来源列表提取
        if sources_list:
            self._extract_from_sources_list(sources_list, findings)

        # 使用 LLM 增强（如果可用）
        if llm and report_markdown:
            await self._enhance_with_llm(findings, llm, report_markdown)

        # 去重和排序
        self._deduplicate_and_sort(findings)

        return findings

    def _extract_topic(self, report: str | None) -> str:
        """提取研究主题"""
        if report:
            # 尝试从报告标题提取
            lines = report.strip().split('\n')
            for line in lines[:5]:
                if line.startswith('# '):
                    return line[2:].strip()

        return "研究报告"

    def _extract_from_sources_list(
        self,
        sources_list: list[dict],
        findings: ResearchFindings
    ) -> None:
        """从来源列表提取"""
        for src in sources_list:
            url = src.get('url', '')
            if not url:
                continue

            try:
                parsed = urlparse(url)
                domain = src.get('domain') or parsed.netloc
                title = src.get('title', domain)

                source = Source(
                    url=url,
                    title=title,
                    domain=domain,
                    accessed_at=datetime.now()
                )
                if not self._source_exists(findings.sources, url):
                    findings.sources.append(source)
                    findings.total_sources_consulted += 1
            except Exception as e:
                logger.warning(f"Failed to parse source: {e}")

    def _extract_from_report(
        self,
        report: str,
        findings: ResearchFindings
    ) -> None:
        """从研究报告提取结构化内容"""
        # 提取摘要（第一个主要段落）
        if not findings.summary:
            findings.summary = self._extract_summary(report)

        # 提取章节作为发现
        sections = self._extract_sections(report)
        for section in sections:
            if section["level"] == 2:  # 二级标题
                finding = ResearchFinding(
                    title=section["title"],
                    content=section["content"][:500],  # 限制长度
                    sub_points=self._extract_bullet_points(section["content"]),
                    importance=FindingImportance.MEDIUM
                )
                # 避免重复
                if not any(f.title == finding.title for f in findings.key_findings):
                    findings.key_findings.append(finding)

        # 提取数据点
        data_points = self._extract_data_points(report)
        findings.data_points.extend(data_points)

        # 提取引用
        quotes = self._extract_quotes(report)
        findings.quotes.extend(quotes)

        # 提取结论和建议
        conclusions = self._extract_conclusions(report)
        findings.conclusions.extend(conclusions)

        recommendations = self._extract_recommendations(report)
        findings.recommendations.extend(recommendations)

    def _extract_summary(self, report: str) -> str:
        """提取摘要"""
        lines = report.split('\n')
        summary_lines = []
        in_summary = False

        for line in lines:
            # 跳过标题
            if line.startswith('# '):
                continue
            # 检测摘要区域
            if '摘要' in line or 'summary' in line.lower():
                in_summary = True
                continue
            # 遇到下一个标题结束
            if line.startswith('## ') and summary_lines:
                break
            # 收集摘要内容
            if in_summary or (not line.startswith('#') and len(summary_lines) < 3):
                stripped = line.strip()
                if stripped and not stripped.startswith('-'):
                    summary_lines.append(stripped)
                    if len(summary_lines) >= 3:
                        break

        return ' '.join(summary_lines[:3]) if summary_lines else ""

    def _extract_sections(self, report: str) -> list[dict[str, Any]]:
        """提取报告章节"""
        sections = []
        current_section = None
        content_lines = []

        for line in report.split('\n'):
            # 检测标题
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                # 保存上一个章节
                if current_section:
                    current_section["content"] = '\n'.join(content_lines).strip()
                    sections.append(current_section)

                # 开始新章节
                level = len(match.group(1))
                title = match.group(2).strip()
                current_section = {"level": level, "title": title, "content": ""}
                content_lines = []
            elif current_section:
                content_lines.append(line)

        # 保存最后一个章节
        if current_section:
            current_section["content"] = '\n'.join(content_lines).strip()
            sections.append(current_section)

        return sections

    def _extract_bullet_points(self, content: str) -> list[str]:
        """提取要点列表"""
        points = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                point = line[2:].strip()
                if len(point) > 5:  # 过滤太短的
                    points.append(point)
        return points[:5]  # 最多5个要点

    def _extract_data_points(self, report: str) -> list[DataPoint]:
        """从报告中提取数据点"""
        data_points = []

        # 匹配百分比
        percent_pattern = r'(\d+(?:\.\d+)?)\s*%\s*(?:的)?([^，。\n]{2,30})'
        for match in re.finditer(percent_pattern, report):
            value = float(match.group(1))
            context = match.group(2).strip()
            data_points.append(DataPoint(
                label=context,
                value=value,
                type=DataPointType.PERCENTAGE,
                unit="%"
            ))

        # 匹配金额/数量
        number_pattern = r'(\d+(?:\.\d+)?)\s*(亿|万|千|百|美元|元|人|家|个|次)([^，。\n]{2,20})?'
        for match in re.finditer(number_pattern, report):
            value = float(match.group(1))
            unit = match.group(2)
            context = match.group(3).strip() if match.group(3) else ""
            data_points.append(DataPoint(
                label=context or "数据",
                value=value,
                type=DataPointType.NUMBER,
                unit=unit
            ))

        # 去重
        seen_labels = set()
        unique_points = []
        for dp in data_points:
            if dp.label not in seen_labels:
                seen_labels.add(dp.label)
                unique_points.append(dp)

        return unique_points[:10]  # 最多10个数据点

    def _extract_quotes(self, report: str) -> list[Quote]:
        """提取引用语句"""
        quotes = []

        # 匹配引用格式 > 或 ""
        quote_patterns = [
            r'>\s*(.{20,200})',  # Markdown 引用
            r'"([^"]{20,200})"',  # 双引号引用
            r'「([^」]{20,200})」',  # 中文引号
        ]

        for pattern in quote_patterns:
            for match in re.finditer(pattern, report):
                text = match.group(1).strip()
                if len(text) >= 20:
                    quotes.append(Quote(text=text))

        return quotes[:5]  # 最多5个引用

    def _extract_conclusions(self, report: str) -> list[str]:
        """提取结论"""
        conclusions = []
        in_conclusion = False

        for line in report.split('\n'):
            lower = line.lower()
            if '结论' in line or 'conclusion' in lower or '总结' in line:
                in_conclusion = True
                continue
            if in_conclusion:
                if line.startswith('## ') or line.startswith('# '):
                    break
                stripped = line.strip()
                if stripped.startswith('- ') or stripped.startswith('* '):
                    conclusions.append(stripped[2:])
                elif stripped and len(stripped) > 10:
                    conclusions.append(stripped)

        return conclusions[:5]

    def _extract_recommendations(self, report: str) -> list[str]:
        """提取建议"""
        recommendations = []
        in_recommendation = False

        for line in report.split('\n'):
            lower = line.lower()
            if '建议' in line or 'recommendation' in lower or '行动' in line:
                in_recommendation = True
                continue
            if in_recommendation:
                if line.startswith('## ') or line.startswith('# '):
                    break
                stripped = line.strip()
                if stripped.startswith('- ') or stripped.startswith('* '):
                    recommendations.append(stripped[2:])
                elif stripped and len(stripped) > 10:
                    recommendations.append(stripped)

        return recommendations[:5]

    def _source_exists(self, sources: list[Source], url: str) -> bool:
        """检查来源是否已存在"""
        return any(s.url == url for s in sources)

    def _extract_sources_from_report(self, report: str, findings: ResearchFindings) -> None:
        """从报告中提取来源链接"""
        # 匹配 Markdown 链接 [text](url)
        link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        for match in re.finditer(link_pattern, report):
            title = match.group(1)
            url = match.group(2)
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                source = Source(
                    url=url,
                    title=title,
                    domain=domain,
                    accessed_at=datetime.now()
                )
                if not self._source_exists(findings.sources, url):
                    findings.sources.append(source)
                    findings.total_sources_consulted += 1
            except Exception as e:
                logger.warning(f"Failed to parse link: {e}")

        # 匹配引用标记 [1], [2] 等
        # 并在报告末尾查找引用列表
        ref_pattern = r'^\[\d+\]:\s*(https?://\S+)'
        for match in re.finditer(ref_pattern, report, re.MULTILINE):
            url = match.group(1)
            try:
                parsed = urlparse(url)
                domain = parsed.netloc
                source = Source(
                    url=url,
                    title=domain,
                    domain=domain,
                    accessed_at=datetime.now()
                )
                if not self._source_exists(findings.sources, url):
                    findings.sources.append(source)
                    findings.total_sources_consulted += 1
            except Exception as e:
                logger.warning(f"Failed to parse ref: {e}")

    async def _enhance_with_llm(
        self,
        findings: ResearchFindings,
        llm,
        report: str | None
    ) -> None:
        """使用 LLM 增强提取结果"""
        # 如果没有摘要，使用 LLM 生成
        if not findings.summary and report:
            try:
                prompt = f"""请为以下研究报告生成一段简洁的摘要（100字以内）：

{report[:2000]}

只输出摘要内容，不要其他说明。"""

                response = await llm.complete(
                    messages=[{"role": "user", "content": prompt}],
                    system="你是一个专业的研究助理，擅长提炼研究报告的核心内容。"
                )
                findings.summary = response.content.strip()
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}")

        # 如果发现数量太少，尝试补充
        if len(findings.key_findings) < 3 and report:
            try:
                prompt = f"""从以下研究内容中提取3-5个关键发现：

{report[:3000]}

请以JSON数组格式返回，每个发现包含 title 和 content 字段。"""

                response = await llm.complete(
                    messages=[{"role": "user", "content": prompt}],
                    system="你是一个专业的研究分析师。请只返回JSON数组，不要其他内容。"
                )

                import json
                extracted = json.loads(response.content)
                for item in extracted:
                    if isinstance(item, dict) and "title" in item:
                        finding = ResearchFinding(
                            title=item["title"],
                            content=item.get("content", ""),
                            importance=FindingImportance.MEDIUM
                        )
                        findings.key_findings.append(finding)
            except Exception as e:
                logger.warning(f"LLM findings extraction failed: {e}")

    def _deduplicate_and_sort(self, findings: ResearchFindings) -> None:
        """去重和排序"""
        # 按重要性排序发现
        importance_order = {
            FindingImportance.HIGH: 0,
            FindingImportance.MEDIUM: 1,
            FindingImportance.LOW: 2
        }
        findings.key_findings.sort(key=lambda f: importance_order.get(f.importance, 1))

        # 去重来源
        seen_urls = set()
        unique_sources = []
        for source in findings.sources:
            if source.url not in seen_urls:
                seen_urls.add(source.url)
                unique_sources.append(source)
        findings.sources = unique_sources
