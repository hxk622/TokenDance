"""
Research to PPT Converter - 研究发现转 PPT 服务

将 Deep Research 的结构化发现转换为 PPT 大纲，
实现「研究 → 汇报」一键体验。

转换逻辑：
1. 标题页 - 研究主题
2. 目录页 - 关键发现概览
3. 内容页 - 每个发现一页或多页
4. 数据页 - 可视化数据点
5. 引用页 - 关键引用语句
6. 结论页 - 总结和建议
7. 来源页 - 参考资料
8. Q&A页 - 提问环节
"""
import logging
from datetime import datetime

from ..agent.agents.ppt import (
    ChartType,
    PPTOutline,
    PPTStyle,
    SlideContent,
    SlideType,
)
from ..models.research_findings import (
    DataPointType,
    FindingImportance,
    ResearchFinding,
    ResearchFindings,
)

logger = logging.getLogger(__name__)


class ResearchToPPTConverter:
    """研究发现转 PPT 转换器

    使用示例:
        converter = ResearchToPPTConverter()
        outline = converter.convert(findings, style=PPTStyle.BUSINESS)
        marp_markdown = outline.to_marp_markdown()
    """

    # 默认配置
    MAX_SLIDES = 20  # 最大幻灯片数
    MAX_POINTS_PER_SLIDE = 5  # 每页最多要点数
    MIN_FINDINGS_FOR_TOC = 4  # 超过此数量才显示目录

    def __init__(
        self,
        style: PPTStyle = PPTStyle.BUSINESS,
        max_slides: int = 20
    ):
        self.style = style
        self.max_slides = max_slides

    def convert(
        self,
        findings: ResearchFindings,
        style: PPTStyle | None = None,
        author: str | None = None,
        include_sources: bool = True,
        include_qa: bool = True
    ) -> PPTOutline:
        """将研究发现转换为 PPT 大纲

        Args:
            findings: 研究发现
            style: PPT 风格（覆盖默认）
            author: 作者名称
            include_sources: 是否包含来源页
            include_qa: 是否包含 Q&A 页

        Returns:
            PPTOutline: PPT 大纲
        """
        style = style or self.style
        slides: list[SlideContent] = []

        # 1. 标题页
        slides.append(self._create_title_slide(findings, author))

        # 2. 目录页（如果发现数量足够多）
        if len(findings.key_findings) >= self.MIN_FINDINGS_FOR_TOC:
            slides.append(self._create_toc_slide(findings))

        # 3. 摘要页（如果有摘要）
        if findings.summary:
            slides.append(self._create_summary_slide(findings))

        # 4. 内容页 - 关键发现
        content_slides = self._create_content_slides(findings)
        slides.extend(content_slides)

        # 5. 数据页（如果有数据点）
        if findings.data_points:
            data_slides = self._create_data_slides(findings)
            slides.extend(data_slides)

        # 6. 引用页（如果有引用）
        if findings.quotes:
            slides.append(self._create_quote_slide(findings))

        # 7. 结论页
        if findings.conclusions or findings.recommendations:
            slides.append(self._create_conclusion_slide(findings))

        # 8. 来源页
        if include_sources and findings.sources:
            slides.append(self._create_sources_slide(findings))

        # 9. Q&A 页
        if include_qa:
            slides.append(self._create_qa_slide())

        # 10. 感谢页
        slides.append(self._create_thank_you_slide(author))

        # 限制幻灯片数量
        if len(slides) > self.max_slides:
            slides = self._trim_slides(slides, self.max_slides)

        # 创建大纲
        outline = PPTOutline(
            title=findings.topic,
            subtitle=self._generate_subtitle(findings),
            author=author,
            style=style,
            theme=self._get_theme_for_style(style),
            slides=slides,
            source_content=findings.summary,
            estimated_duration=self._estimate_duration(len(slides))
        )

        logger.info(f"Generated PPT outline: {len(slides)} slides for '{findings.topic}'")
        return outline

    def _create_title_slide(
        self,
        findings: ResearchFindings,
        author: str | None
    ) -> SlideContent:
        """创建标题页"""
        subtitle_parts = []
        if findings.summary:
            # 取摘要的第一句作为副标题
            first_sentence = findings.summary.split('。')[0]
            if len(first_sentence) <= 50:
                subtitle_parts.append(first_sentence)

        if author:
            subtitle_parts.append(author)

        subtitle_parts.append(datetime.now().strftime("%Y年%m月%d日"))

        return SlideContent(
            type=SlideType.TITLE,
            title=findings.topic,
            subtitle=" | ".join(subtitle_parts) if subtitle_parts else None,
            notes=f"研究时长: {findings.research_duration_seconds // 60}分钟，参考来源: {len(findings.sources)}个"
        )

    def _create_toc_slide(self, findings: ResearchFindings) -> SlideContent:
        """创建目录页"""
        toc_items = []

        for _i, finding in enumerate(findings.key_findings[:7], 1):  # 最多7项
            toc_items.append(finding.title)

        return SlideContent(
            type=SlideType.TOC,
            title="目录",
            points=toc_items,
            notes="本次研究的主要内容概览"
        )

    def _create_summary_slide(self, findings: ResearchFindings) -> SlideContent:
        """创建摘要页"""
        # 将摘要分成几个要点
        summary = findings.summary
        points = []

        # 尝试按句号分割
        sentences = [s.strip() for s in summary.split('。') if s.strip()]
        for sentence in sentences[:4]:
            if len(sentence) > 10:
                points.append(sentence + ('。' if not sentence.endswith('。') else ''))

        return SlideContent(
            type=SlideType.CONTENT,
            title="研究概述",
            points=points if points else [summary[:200]],
            notes="研究的整体概述"
        )

    def _create_content_slides(
        self,
        findings: ResearchFindings
    ) -> list[SlideContent]:
        """创建内容页（关键发现）"""
        slides = []

        for _i, finding in enumerate(findings.key_findings):
            # 高重要性发现可以有更多篇幅
            is_important = finding.importance == FindingImportance.HIGH

            # 准备要点
            points = []

            # 主要内容
            if finding.content:
                # 分句处理
                content_sentences = [s.strip() for s in finding.content.split('。') if s.strip()]
                for sentence in content_sentences[:3]:
                    if len(sentence) > 10:
                        points.append(sentence + ('。' if not sentence.endswith('。') else ''))

            # 子要点
            if finding.sub_points:
                points.extend(finding.sub_points[:self.MAX_POINTS_PER_SLIDE - len(points)])

            # 确保至少有一个要点
            if not points and finding.content:
                points = [finding.content[:200]]

            # 创建幻灯片
            slide = SlideContent(
                type=SlideType.CONTENT,
                title=finding.title,
                subtitle="核心发现" if is_important else None,
                points=points[:self.MAX_POINTS_PER_SLIDE],
                notes=f"重要性: {finding.importance.value}"
            )

            # 添加来源备注
            if finding.source_urls:
                slide.notes += f"\n来源: {finding.source_urls[0]}"

            slides.append(slide)

            # 如果发现有关联数据，创建数据幻灯片
            if finding.related_data and len(finding.related_data) >= 2:
                data_slide = self._create_finding_data_slide(finding)
                if data_slide:
                    slides.append(data_slide)

        return slides

    def _create_finding_data_slide(
        self,
        finding: ResearchFinding
    ) -> SlideContent | None:
        """为单个发现创建数据幻灯片"""
        if not finding.related_data:
            return None

        # 尝试创建图表数据
        labels = []
        values = []

        for dp in finding.related_data[:6]:
            labels.append(dp.label)
            values.append(dp.value)

        return SlideContent(
            type=SlideType.DATA,
            title=f"{finding.title} - 数据",
            chart_type=ChartType.BAR,
            chart_data={
                "labels": labels,
                "datasets": [{"label": "数值", "data": values}]
            },
            notes="相关数据可视化"
        )

    def _create_data_slides(
        self,
        findings: ResearchFindings
    ) -> list[SlideContent]:
        """创建数据页"""
        slides = []

        # 分组数据点
        percentage_data = [d for d in findings.data_points if d.type == DataPointType.PERCENTAGE]
        number_data = [d for d in findings.data_points if d.type == DataPointType.NUMBER]

        # 百分比数据页
        if percentage_data:
            labels = [d.label[:20] for d in percentage_data[:6]]
            values = [d.value for d in percentage_data[:6]]

            slides.append(SlideContent(
                type=SlideType.DATA,
                title="关键数据 - 占比分析",
                chart_type=ChartType.PIE,
                chart_data={
                    "labels": labels,
                    "datasets": [{"label": "占比", "data": values}]
                },
                notes="研究中发现的关键百分比数据"
            ))

        # 数值数据页
        if number_data and len(number_data) >= 3:
            labels = [d.label[:20] for d in number_data[:6]]
            values = [d.value for d in number_data[:6]]
            units = [d.unit for d in number_data[:6]]

            # 使用表格展示
            points = [f"{lbl}: {val}{unt or ''}" for lbl, val, unt in zip(labels, values, units, strict=False)]

            slides.append(SlideContent(
                type=SlideType.CONTENT,
                title="关键数据 - 数值统计",
                points=points,
                notes="研究中发现的关键数值数据"
            ))

        return slides

    def _create_quote_slide(self, findings: ResearchFindings) -> SlideContent:
        """创建引用页"""
        # 选择最有价值的引用
        best_quote = findings.quotes[0] if findings.quotes else None

        if not best_quote:
            return SlideContent(
                type=SlideType.CONTENT,
                title="专家观点",
                points=["暂无收录的专家观点"],
                notes="引用页"
            )

        return SlideContent(
            type=SlideType.QUOTE,
            title="专家观点",
            content=best_quote.text,
            subtitle=best_quote.author or (best_quote.source.title if best_quote.source else None),
            notes="研究中发现的重要引用"
        )

    def _create_conclusion_slide(self, findings: ResearchFindings) -> SlideContent:
        """创建结论页"""
        points = []

        # 添加结论
        for conclusion in findings.conclusions[:3]:
            points.append(f"✓ {conclusion}")

        # 添加建议
        for rec in findings.recommendations[:2]:
            points.append(f"→ {rec}")

        # 如果没有结论和建议，从高重要性发现生成
        if not points:
            high_findings = findings.get_high_importance_findings()
            for f in high_findings[:3]:
                points.append(f"✓ {f.title}")

        return SlideContent(
            type=SlideType.CONCLUSION,
            title="结论与建议",
            points=points[:5],
            notes="研究的核心结论和行动建议"
        )

    def _create_sources_slide(self, findings: ResearchFindings) -> SlideContent:
        """创建来源页"""
        points = []

        # 按可信度排序
        sorted_sources = sorted(
            findings.sources,
            key=lambda s: {"high": 0, "medium": 1, "low": 2}.get(s.credibility, 1)
        )

        for source in sorted_sources[:8]:
            # 简化显示
            domain = source.domain or "未知来源"
            title = source.title[:40] + ("..." if len(source.title) > 40 else "")
            points.append(f"[{domain}] {title}")

        return SlideContent(
            type=SlideType.CONTENT,
            title="参考来源",
            points=points,
            notes=f"本研究共参考 {len(findings.sources)} 个来源"
        )

    def _create_qa_slide(self) -> SlideContent:
        """创建 Q&A 页"""
        return SlideContent(
            type=SlideType.QA,
            title="Q&A",
            subtitle="欢迎提问与讨论",
            notes="问答环节"
        )

    def _create_thank_you_slide(self, author: str | None) -> SlideContent:
        """创建感谢页"""
        subtitle = None
        if author:
            subtitle = f"{author} | {datetime.now().strftime('%Y年%m月')}"

        return SlideContent(
            type=SlideType.THANK_YOU,
            title="谢谢",
            subtitle=subtitle or "TokenDance AI Research",
            notes="感谢观看"
        )

    def _generate_subtitle(self, findings: ResearchFindings) -> str:
        """生成副标题"""
        parts = []

        if findings.key_findings:
            parts.append(f"{len(findings.key_findings)}个关键发现")

        if findings.sources:
            parts.append(f"{len(findings.sources)}个信息来源")

        return " | ".join(parts) if parts else "深度研究报告"

    def _get_theme_for_style(self, style: PPTStyle) -> str:
        """根据风格获取 Marp 主题"""
        theme_map = {
            PPTStyle.BUSINESS: "default",
            PPTStyle.TECH: "gaia",
            PPTStyle.MINIMAL: "uncover",
            PPTStyle.ACADEMIC: "default",
            PPTStyle.CREATIVE: "gaia",
        }
        return theme_map.get(style, "default")

    def _estimate_duration(self, slide_count: int) -> str:
        """估算演示时长"""
        # 假设每页平均1.5分钟
        minutes = int(slide_count * 1.5)

        if minutes <= 5:
            return "5分钟"
        elif minutes <= 10:
            return "10分钟"
        elif minutes <= 15:
            return "15分钟"
        elif minutes <= 20:
            return "20分钟"
        else:
            return f"{minutes}分钟"

    def _trim_slides(
        self,
        slides: list[SlideContent],
        max_count: int
    ) -> list[SlideContent]:
        """裁剪幻灯片数量"""
        if len(slides) <= max_count:
            return slides

        # 保留必要的幻灯片
        essential_types = {SlideType.TITLE, SlideType.CONCLUSION, SlideType.THANK_YOU}
        essential = [s for s in slides if s.type in essential_types]

        # 其他幻灯片
        others = [s for s in slides if s.type not in essential_types]

        # 计算可保留的数量
        available = max_count - len(essential)

        # 保留前面的内容幻灯片
        trimmed = essential[:1] + others[:available] + essential[1:]

        return trimmed[:max_count]
