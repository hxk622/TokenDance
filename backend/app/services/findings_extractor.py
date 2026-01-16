# -*- coding: utf-8 -*-
"""
Findings Extractor Service - 研究发现提取服务

从 Deep Research 的输出中提取结构化的研究发现：
- 从 Timeline 提取搜索、阅读、发现记录
- 从研究报告提取关键段落
- 识别数据点（数字、百分比、对比）
- 提取可引用语句
"""
import re
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from datetime import datetime

from .research_timeline import ResearchTimeline, TimelineEntry, ResearchTimelineService
from ..models.research_findings import (
    ResearchFindings,
    ResearchFinding,
    FindingImportance,
    DataPoint,
    DataPointType,
    Quote,
    Source,
)

logger = logging.getLogger(__name__)


class FindingsExtractor:
    """研究发现提取器
    
    从 Deep Research 的各种输出中提取结构化的研究发现，
    用于生成 PPT、报告等。
    
    使用示例:
        extractor = FindingsExtractor(session_id="research_123")
        findings = await extractor.extract_all(
            timeline=timeline,
            report_markdown=report_content
        )
    """
    
    def __init__(self, session_id: str, topic: str = ""):
        self.session_id = session_id
        self.topic = topic
    
    async def extract_all(
        self,
        timeline: Optional[ResearchTimeline] = None,
        report_markdown: Optional[str] = None,
        llm=None  # 可选：使用 LLM 增强提取
    ) -> ResearchFindings:
        """提取所有研究发现
        
        Args:
            timeline: 研究时间轴
            report_markdown: 研究报告 Markdown
            llm: 可选的 LLM 实例，用于增强提取
            
        Returns:
            ResearchFindings: 结构化的研究发现
        """
        findings = ResearchFindings(
            session_id=self.session_id,
            topic=self.topic or self._extract_topic(timeline, report_markdown),
            summary=""
        )
        
        # 从 Timeline 提取
        if timeline:
            self._extract_from_timeline(timeline, findings)
        
        # 从报告提取
        if report_markdown:
            self._extract_from_report(report_markdown, findings)
        
        # 使用 LLM 增强（如果可用）
        if llm and (timeline or report_markdown):
            await self._enhance_with_llm(findings, llm, report_markdown)
        
        # 去重和排序
        self._deduplicate_and_sort(findings)
        
        return findings
    
    def _extract_topic(
        self,
        timeline: Optional[ResearchTimeline],
        report: Optional[str]
    ) -> str:
        """提取研究主题"""
        if timeline and timeline.topic:
            return timeline.topic
        
        if report:
            # 尝试从报告标题提取
            lines = report.strip().split('\n')
            for line in lines[:5]:
                if line.startswith('# '):
                    return line[2:].strip()
        
        return "研究报告"
    
    def _extract_from_timeline(
        self,
        timeline: ResearchTimeline,
        findings: ResearchFindings
    ) -> None:
        """从时间轴提取发现"""
        for entry in timeline.entries:
            # 提取来源
            if entry.url:
                source = self._create_source_from_entry(entry)
                if source and not self._source_exists(findings.sources, source.url):
                    findings.sources.append(source)
            
            # 提取发现类型的条目
            if entry.event_type == "finding":
                finding = ResearchFinding(
                    title=entry.title.replace("Finding: ", ""),
                    content=entry.description,
                    importance=self._determine_importance(entry),
                    source_urls=[entry.url] if entry.url else []
                )
                findings.key_findings.append(finding)
            
            # 从搜索结果中提取数据点
            if entry.event_type == "search":
                metadata = entry.metadata or {}
                if "results_count" in metadata:
                    # 记录搜索统计
                    findings.total_sources_consulted += metadata.get("results_count", 0)
        
        # 计算研究时长
        if timeline.entries:
            first = timeline.entries[0].timestamp
            last = timeline.entries[-1].timestamp
            findings.research_duration_seconds = int((last - first).total_seconds())
    
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
    
    def _extract_sections(self, report: str) -> List[Dict[str, Any]]:
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
    
    def _extract_bullet_points(self, content: str) -> List[str]:
        """提取要点列表"""
        points = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                point = line[2:].strip()
                if len(point) > 5:  # 过滤太短的
                    points.append(point)
        return points[:5]  # 最多5个要点
    
    def _extract_data_points(self, report: str) -> List[DataPoint]:
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
                label=context or f"数据",
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
    
    def _extract_quotes(self, report: str) -> List[Quote]:
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
    
    def _extract_conclusions(self, report: str) -> List[str]:
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
    
    def _extract_recommendations(self, report: str) -> List[str]:
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
    
    def _create_source_from_entry(self, entry: TimelineEntry) -> Optional[Source]:
        """从时间轴条目创建来源"""
        if not entry.url:
            return None
        
        try:
            parsed = urlparse(entry.url)
            domain = parsed.netloc
            title = entry.metadata.get("title", entry.title) if entry.metadata else entry.title
            
            return Source(
                url=entry.url,
                title=title.replace("Read: ", ""),
                domain=domain,
                accessed_at=entry.timestamp
            )
        except Exception as e:
            logger.warning(f"Failed to create source: {e}")
            return None
    
    def _source_exists(self, sources: List[Source], url: str) -> bool:
        """检查来源是否已存在"""
        return any(s.url == url for s in sources)
    
    def _determine_importance(self, entry: TimelineEntry) -> FindingImportance:
        """根据条目内容判断重要性"""
        text = f"{entry.title} {entry.description}".lower()
        
        # 高重要性关键词
        high_keywords = ['关键', '重要', '核心', 'key', 'important', 'critical', '突破', '首次']
        if any(kw in text for kw in high_keywords):
            return FindingImportance.HIGH
        
        # 低重要性关键词
        low_keywords = ['补充', '参考', 'note', 'minor', '次要']
        if any(kw in text for kw in low_keywords):
            return FindingImportance.LOW
        
        return FindingImportance.MEDIUM
    
    async def _enhance_with_llm(
        self,
        findings: ResearchFindings,
        llm,
        report: Optional[str]
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
