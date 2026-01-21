"""
Report Iterator Service - 报告迭代服务

支持:
- 报告章节局部修订
- 版本管理
- 流式修订生成
"""
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime

from app.schemas.interactive_report import (
    QUICK_ACTIONS,
    InteractiveReport,
    QuickAction,
    ReportSection,
    ReportVersion,
    RevisionRequest,
    RevisionResult,
    RevisionType,
)


class ReportIterator:
    """报告迭代器 - 处理报告的局部修订"""

    # 修订类型对应的系统提示
    REVISION_PROMPTS = {
        RevisionType.EXPAND: """你需要对以下内容进行深入展开：
- 补充更多细节和背景信息
- 深入分析关键点
- 添加相关的例子或案例
- 保持原有的论点方向""",

        RevisionType.SIMPLIFY: """你需要简化以下内容：
- 使用更通俗易懂的语言
- 去除冗余和复杂的表述
- 保留核心观点
- 适当使用类比帮助理解""",

        RevisionType.ADD_EVIDENCE: """你需要为以下内容增加支持性证据：
- 引用相关数据和统计
- 添加专家观点或研究结论
- 补充案例支撑
- 注明证据来源""",

        RevisionType.REWRITE: """你需要重写以下内容：
- 重新组织段落结构
- 改进表达方式
- 保持原有的核心观点
- 提升可读性""",

        RevisionType.ADD_SECTION: """你需要新增一个章节：
- 根据用户指令确定主题
- 与现有内容保持风格一致
- 提供有价值的新信息
- 注明信息来源""",

        RevisionType.TONE_CHANGE: """你需要调整以下内容的语气：
- 根据用户指令调整正式/非正式程度
- 保持内容的准确性
- 适应目标读者
- 保持专业性""",
    }

    def __init__(self, llm_service: object | None = None):
        """
        初始化报告迭代器

        Args:
            llm_service: LLM 服务实例，用于生成修订内容
        """
        self.llm_service = llm_service
        self._reports: dict[str, InteractiveReport] = {}

    def create_report(
        self,
        session_id: str,
        title: str,
        query: str,
        sections: list[ReportSection],
    ) -> InteractiveReport:
        """
        创建新的可交互报告

        Args:
            session_id: 研究会话 ID
            title: 报告标题
            query: 原始查询
            sections: 初始章节列表

        Returns:
            InteractiveReport: 创建的报告
        """
        report_id = str(uuid.uuid4())

        initial_version = ReportVersion(
            version=1,
            sections=sections,
            created_at=datetime.utcnow(),
            revision_note="初始版本",
        )

        report = InteractiveReport(
            id=report_id,
            session_id=session_id,
            title=title,
            query=query,
            current_version=1,
            versions=[initial_version],
            created_at=datetime.utcnow(),
        )

        self._reports[report_id] = report
        return report

    def get_report(self, report_id: str) -> InteractiveReport | None:
        """获取报告"""
        return self._reports.get(report_id)

    def get_current_sections(self, report_id: str) -> list[ReportSection]:
        """获取报告当前版本的章节"""
        report = self._reports.get(report_id)
        if not report or not report.versions:
            return []

        current_version = report.versions[-1]
        return current_version.sections

    def get_quick_actions(self) -> list[QuickAction]:
        """获取可用的快速操作"""
        return QUICK_ACTIONS

    async def revise_section(
        self,
        report_id: str,
        revision: RevisionRequest,
    ) -> RevisionResult:
        """
        修订单个章节

        Args:
            report_id: 报告 ID
            revision: 修订请求

        Returns:
            RevisionResult: 修订结果
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 获取当前章节
        current_sections = self.get_current_sections(report_id)
        section = next(
            (s for s in current_sections if s.id == revision.section_id),
            None
        )

        if not section:
            raise ValueError(f"Section {revision.section_id} not found")

        # 构建修订提示
        system_prompt = self.REVISION_PROMPTS.get(
            revision.revision_type,
            "请根据用户指令修改以下内容："
        )

        user_instruction = revision.instruction or ""

        prompt = f"""{system_prompt}

原始内容:
{section.content}

{f"用户指令: {user_instruction}" if user_instruction else ""}

请直接输出修订后的内容，不要包含任何解释或前缀。"""

        # 模拟 LLM 响应（实际应调用 LLM 服务）
        revised_content = await self._generate_revision(prompt, section)

        # 生成变更摘要
        changes_summary = self._generate_changes_summary(
            revision.revision_type,
            section.content,
            revised_content,
        )

        return RevisionResult(
            section_id=revision.section_id,
            original_content=section.content,
            revised_content=revised_content,
            revision_type=revision.revision_type,
            changes_summary=changes_summary,
            new_sources=[],  # 实际应从 LLM 输出中提取
        )

    async def apply_revisions(
        self,
        report_id: str,
        results: list[RevisionResult],
        user_note: str | None = None,
    ) -> InteractiveReport:
        """
        应用修订结果，创建新版本

        Args:
            report_id: 报告 ID
            results: 修订结果列表
            user_note: 用户备注

        Returns:
            InteractiveReport: 更新后的报告
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 复制当前章节
        current_sections = self.get_current_sections(report_id)
        new_sections = []

        for section in current_sections:
            # 查找是否有对应的修订
            revision = next(
                (r for r in results if r.section_id == section.id),
                None
            )

            if revision:
                # 创建修订后的章节
                new_section = ReportSection(
                    id=section.id,
                    type=section.type,
                    title=section.title,
                    content=revision.revised_content,
                    sources=list(set(section.sources + revision.new_sources)),
                    created_at=section.created_at,
                    updated_at=datetime.utcnow(),
                    version=section.version + 1,
                )
            else:
                new_section = section

            new_sections.append(new_section)

        # 创建新版本
        new_version = ReportVersion(
            version=report.current_version + 1,
            sections=new_sections,
            created_at=datetime.utcnow(),
            revision_note=user_note or f"版本 {report.current_version + 1}",
        )

        # 更新报告
        report.versions.append(new_version)
        report.current_version += 1
        report.updated_at = datetime.utcnow()

        return report

    async def stream_revision(
        self,
        report_id: str,
        revision: RevisionRequest,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成修订内容

        Args:
            report_id: 报告 ID
            revision: 修订请求

        Yields:
            str: 修订内容片段
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # 获取当前章节
        current_sections = self.get_current_sections(report_id)
        section = next(
            (s for s in current_sections if s.id == revision.section_id),
            None
        )

        if not section:
            raise ValueError(f"Section {revision.section_id} not found")

        # 构建提示（与 revise_section 相同）
        self.REVISION_PROMPTS.get(
            revision.revision_type,
            "请根据用户指令修改以下内容："
        )

        # 模拟流式输出
        # 实际应使用 LLM 的流式 API
        sample_response = f"[修订后的内容 - {revision.revision_type.value}]\n\n{section.content[:100]}... (已根据 {revision.revision_type.value} 要求修订)"

        for char in sample_response:
            yield char

    def rollback_version(
        self,
        report_id: str,
        target_version: int,
    ) -> InteractiveReport:
        """
        回滚到指定版本

        Args:
            report_id: 报告 ID
            target_version: 目标版本号

        Returns:
            InteractiveReport: 更新后的报告
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        if target_version < 1 or target_version > len(report.versions):
            raise ValueError(f"Invalid version: {target_version}")

        # 获取目标版本的章节
        target_version_obj = report.versions[target_version - 1]

        # 创建回滚版本
        rollback_version = ReportVersion(
            version=report.current_version + 1,
            sections=target_version_obj.sections,
            created_at=datetime.utcnow(),
            revision_note=f"回滚至版本 {target_version}",
        )

        report.versions.append(rollback_version)
        report.current_version += 1
        report.updated_at = datetime.utcnow()

        return report

    def get_version_diff(
        self,
        report_id: str,
        version_a: int,
        version_b: int,
    ) -> dict:
        """
        获取两个版本之间的差异

        Args:
            report_id: 报告 ID
            version_a: 版本 A
            version_b: 版本 B

        Returns:
            dict: 差异信息
        """
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        if version_a < 1 or version_a > len(report.versions):
            raise ValueError(f"Invalid version: {version_a}")
        if version_b < 1 or version_b > len(report.versions):
            raise ValueError(f"Invalid version: {version_b}")

        sections_a = report.versions[version_a - 1].sections
        sections_b = report.versions[version_b - 1].sections

        diffs = []
        sections_a_map = {s.id: s for s in sections_a}
        sections_b_map = {s.id: s for s in sections_b}

        # 找出修改和删除
        for section_id, section_a in sections_a_map.items():
            section_b = sections_b_map.get(section_id)
            if section_b is None:
                diffs.append({
                    "type": "deleted",
                    "section_id": section_id,
                    "title": section_a.title,
                })
            elif section_a.content != section_b.content:
                diffs.append({
                    "type": "modified",
                    "section_id": section_id,
                    "title": section_a.title,
                    "content_a": section_a.content,
                    "content_b": section_b.content,
                })

        # 找出新增
        for section_id, section_b in sections_b_map.items():
            if section_id not in sections_a_map:
                diffs.append({
                    "type": "added",
                    "section_id": section_id,
                    "title": section_b.title,
                })

        return {
            "version_a": version_a,
            "version_b": version_b,
            "diffs": diffs,
        }

    async def _generate_revision(
        self,
        prompt: str,
        section: ReportSection,
    ) -> str:
        """
        生成修订内容（模拟）

        实际实现应调用 LLM 服务
        """
        # 模拟修订
        return f"{section.content}\n\n[已根据要求进行修订]"

    def _generate_changes_summary(
        self,
        revision_type: RevisionType,
        original: str,
        revised: str,
    ) -> str:
        """生成变更摘要"""
        original_len = len(original)
        revised_len = len(revised)

        change_desc = {
            RevisionType.EXPAND: "深入展开了内容",
            RevisionType.SIMPLIFY: "简化了表述",
            RevisionType.ADD_EVIDENCE: "增加了支持性证据",
            RevisionType.REWRITE: "重写了段落",
            RevisionType.ADD_SECTION: "新增了章节",
            RevisionType.DELETE_SECTION: "删除了章节",
            RevisionType.TONE_CHANGE: "调整了语气",
        }

        desc = change_desc.get(revision_type, "修订了内容")

        if revised_len > original_len:
            change_pct = ((revised_len - original_len) / original_len) * 100
            return f"{desc}，内容增加了 {change_pct:.0f}%"
        elif revised_len < original_len:
            change_pct = ((original_len - revised_len) / original_len) * 100
            return f"{desc}，内容精简了 {change_pct:.0f}%"
        else:
            return desc


# 单例实例
_report_iterator: ReportIterator | None = None


def get_report_iterator() -> ReportIterator:
    """获取 ReportIterator 单例"""
    global _report_iterator
    if _report_iterator is None:
        _report_iterator = ReportIterator()
    return _report_iterator
