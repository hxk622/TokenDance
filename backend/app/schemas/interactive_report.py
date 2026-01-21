"""
Interactive Report Schema - 可交互报告迭代数据结构

支持:
- 报告版本管理
- 局部修订请求
- 修订历史追踪
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RevisionType(str, Enum):
    """修订类型"""
    EXPAND = "expand"           # 深入展开
    SIMPLIFY = "simplify"       # 简化说明
    ADD_EVIDENCE = "evidence"   # 增加论据
    REWRITE = "rewrite"         # 重写段落
    ADD_SECTION = "add"         # 新增章节
    DELETE_SECTION = "delete"   # 删除章节
    TONE_CHANGE = "tone"        # 调整语气


class SectionType(str, Enum):
    """报告章节类型"""
    SUMMARY = "summary"
    BACKGROUND = "background"
    ANALYSIS = "analysis"
    DATA = "data"
    CONCLUSION = "conclusion"
    RECOMMENDATION = "recommendation"


class ReportSection(BaseModel):
    """报告章节"""
    id: str
    type: SectionType
    title: str
    content: str
    sources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    version: int = 1


class RevisionRequest(BaseModel):
    """修订请求"""
    section_id: str
    revision_type: RevisionType
    instruction: str | None = None  # 用户自定义指令


class RevisionResult(BaseModel):
    """修订结果"""
    section_id: str
    original_content: str
    revised_content: str
    revision_type: RevisionType
    changes_summary: str
    new_sources: list[str] = Field(default_factory=list)


class ReportVersion(BaseModel):
    """报告版本"""
    version: int
    sections: list[ReportSection]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revision_note: str | None = None


class InteractiveReport(BaseModel):
    """可交互报告"""
    id: str
    session_id: str
    title: str
    query: str
    current_version: int = 1
    versions: list[ReportVersion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None


class QuickAction(BaseModel):
    """快速操作定义"""
    id: str
    label: str
    icon: str
    revision_type: RevisionType
    default_instruction: str | None = None


# 预定义的快速操作
QUICK_ACTIONS = [
    QuickAction(
        id="expand",
        label="深入展开",
        icon="zoom-in",
        revision_type=RevisionType.EXPAND,
        default_instruction="请对这部分内容进行更深入的分析和展开"
    ),
    QuickAction(
        id="simplify",
        label="简化说明",
        icon="minimize",
        revision_type=RevisionType.SIMPLIFY,
        default_instruction="请用更简洁易懂的语言重新表述"
    ),
    QuickAction(
        id="evidence",
        label="增加论据",
        icon="file-plus",
        revision_type=RevisionType.ADD_EVIDENCE,
        default_instruction="请为这部分论述增加更多支持性证据"
    ),
    QuickAction(
        id="rewrite",
        label="重写段落",
        icon="edit",
        revision_type=RevisionType.REWRITE,
        default_instruction="请重新组织和表述这部分内容"
    ),
]


class ReportIterationRequest(BaseModel):
    """报告迭代请求 API"""
    report_id: str
    revisions: list[RevisionRequest]
    user_note: str | None = None


class ReportIterationResponse(BaseModel):
    """报告迭代响应"""
    report_id: str
    new_version: int
    results: list[RevisionResult]
    updated_report: InteractiveReport
