"""
Research v4 API - Deep Research 下一代功能

包含:
1. 推理轨迹 (Reasoning Trace) - 展示 AI 思考过程
2. 用户偏好 (User Preference) - 学习和配置用户偏好
3. 报告迭代 (Report Iteration) - 交互式报告
4. 智能深度 (Smart Depth) - 自适应深度建议
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.reasoning_trace import (
    ReasoningTrace,
    ReasoningTraceFeedback,
    ReasoningTraceList,
)
from app.schemas.interactive_report import (
    InteractiveReport,
    QuickAction,
    QUICK_ACTIONS,
    ReportSection,
    RevisionRequest,
    RevisionResult,
    RevisionType,
    SectionType,
)
from app.services.preference_learner import PreferenceLearner, get_preference_learner
from app.services.reasoning_trace import get_reasoning_service
from app.services.report_iterator import get_report_iterator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research/v4", tags=["research-v4"])


# ==================== Schemas ====================

class PreferenceUpdateRequest(BaseModel):
    """偏好更新请求"""
    preferred_source_types: list[str] | None = None
    trusted_domains: list[str] | None = None
    blocked_domains: list[str] | None = None
    preferred_languages: list[str] | None = None
    default_depth: str | None = None  # quick | standard | deep
    default_breadth: int | None = Field(None, ge=3, le=25)
    expertise_level: str | None = None  # beginner | intermediate | expert
    expertise_domains: list[str] | None = None
    preferred_report_style: str | None = None  # concise | detailed | academic
    include_charts: bool | None = None
    include_citations: bool | None = None


class PreferenceResponse(BaseModel):
    """偏好响应"""
    user_id: str
    preferred_source_types: list[str]
    trusted_domains: list[str]
    blocked_domains: list[str]
    preferred_languages: list[str]
    default_depth: str
    default_breadth: int
    expertise_level: str
    expertise_domains: list[str]
    preferred_report_style: str
    include_charts: bool
    include_citations: bool
    interaction_count: int
    updated_at: str | None


class InteractionEvent(BaseModel):
    """用户交互事件"""
    event_type: str = Field(
        ...,
        description="事件类型: skip_source, like_finding, dislike_finding, "
                    "adjust_depth, select_source, block_domain"
    )
    context: dict = Field(default_factory=dict, description="事件上下文")


class ResearchConfigResponse(BaseModel):
    """研究配置响应"""
    max_sources: int
    preferred_source_types: list[str]
    trusted_domains: list[str]
    blocked_domains: list[str]
    preferred_languages: list[str]
    expertise_level: str
    report_style: str
    include_charts: bool
    include_citations: bool
    domain_scores: dict


# ==================== Reasoning Trace Endpoints ====================

@router.get(
    "/sessions/{session_id}/reasoning",
    response_model=ReasoningTraceList,
    summary="获取会话的推理轨迹"
)
async def get_reasoning_traces(
    session_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="返回数量限制")
):
    """获取指定会话的 AI 推理轨迹列表"""
    service = get_reasoning_service(session_id)
    traces = service.get_recent_traces(limit)
    
    return ReasoningTraceList(
        traces=traces,
        total=len(service.get_all_traces()),
        session_id=session_id
    )


@router.get(
    "/sessions/{session_id}/reasoning/{trace_id}",
    response_model=ReasoningTrace,
    summary="获取单条推理轨迹详情"
)
async def get_reasoning_trace_detail(
    session_id: str,
    trace_id: str
):
    """获取指定推理轨迹的详细信息"""
    service = get_reasoning_service(session_id)
    trace = service.get_trace_by_id(trace_id)
    
    if not trace:
        raise HTTPException(status_code=404, detail="Reasoning trace not found")
    
    return trace


@router.post(
    "/sessions/{session_id}/reasoning/feedback",
    summary="提交推理反馈"
)
async def submit_reasoning_feedback(
    session_id: str,
    feedback: ReasoningTraceFeedback
):
    """用户对某条推理的反馈 (点赞/点踩)"""
    service = get_reasoning_service(session_id)
    success = service.add_feedback(feedback)
    
    if not success:
        raise HTTPException(status_code=404, detail="Reasoning trace not found")
    
    return {"status": "ok", "message": "Feedback recorded"}


# ==================== User Preference Endpoints ====================

@router.get(
    "/users/{user_id}/preferences",
    response_model=PreferenceResponse,
    summary="获取用户研究偏好"
)
async def get_user_preferences(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """获取用户的研究偏好设置"""
    learner = await get_preference_learner(db, user_id)
    preference = await learner.get_or_create_preference()
    
    return PreferenceResponse(**preference.to_dict())


@router.put(
    "/users/{user_id}/preferences",
    response_model=PreferenceResponse,
    summary="更新用户研究偏好"
)
async def update_user_preferences(
    user_id: str,
    updates: PreferenceUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """更新用户的研究偏好设置"""
    learner = await get_preference_learner(db, user_id)
    
    # 过滤掉 None 值
    update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    preference = await learner.update_explicit_preference(update_dict)
    return PreferenceResponse(**preference.to_dict())


@router.post(
    "/users/{user_id}/preferences/learn",
    summary="记录用户交互用于学习"
)
async def learn_from_interaction(
    user_id: str,
    event: InteractionEvent,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """记录用户交互事件，用于隐式学习偏好"""
    learner = await get_preference_learner(db, user_id)
    await learner.learn_from_interaction(event.event_type, event.context)
    
    return {"status": "ok", "message": "Interaction recorded for learning"}


@router.get(
    "/users/{user_id}/research-config",
    response_model=ResearchConfigResponse,
    summary="获取研究配置"
)
async def get_research_config(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """获取基于用户偏好的研究配置参数"""
    learner = await get_preference_learner(db, user_id)
    config = await learner.get_research_config()
    
    return ResearchConfigResponse(**config)


@router.post(
    "/users/{user_id}/preferences/domains/trust",
    summary="添加信任域名"
)
async def add_trusted_domain(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    domain: str = Query(..., description="要信任的域名"),
):
    """添加域名到信任列表"""
    learner = await get_preference_learner(db, user_id)
    preference = await learner.get_or_create_preference()
    
    trusted = list(preference.trusted_domains or [])
    if domain not in trusted:
        trusted.append(domain)
        await learner.update_explicit_preference({"trusted_domains": trusted})
    
    return {"status": "ok", "trusted_domains": trusted}


@router.post(
    "/users/{user_id}/preferences/domains/block",
    summary="添加屏蔽域名"
)
async def add_blocked_domain(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    domain: str = Query(..., description="要屏蔽的域名"),
):
    """添加域名到屏蔽列表"""
    learner = await get_preference_learner(db, user_id)
    await learner.learn_from_interaction("block_domain", {"domain": domain})
    
    preference = await learner.get_or_create_preference()
    return {"status": "ok", "blocked_domains": preference.blocked_domains}


@router.delete(
    "/users/{user_id}/preferences/domains/trust",
    summary="移除信任域名"
)
async def remove_trusted_domain(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    domain: str = Query(..., description="要移除的域名"),
):
    """从信任列表移除域名"""
    learner = await get_preference_learner(db, user_id)
    preference = await learner.get_or_create_preference()
    
    trusted = list(preference.trusted_domains or [])
    if domain in trusted:
        trusted.remove(domain)
        await learner.update_explicit_preference({"trusted_domains": trusted})
    
    return {"status": "ok", "trusted_domains": trusted}


@router.delete(
    "/users/{user_id}/preferences/domains/block",
    summary="移除屏蔽域名"
)
async def remove_blocked_domain(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    domain: str = Query(..., description="要移除的域名"),
):
    """从屏蔽列表移除域名"""
    learner = await get_preference_learner(db, user_id)
    preference = await learner.get_or_create_preference()
    
    blocked = list(preference.blocked_domains or [])
    if domain in blocked:
        blocked.remove(domain)
        await learner.update_explicit_preference({"blocked_domains": blocked})
    
    return {"status": "ok", "blocked_domains": blocked}


# ==================== Interactive Report Endpoints ====================

class CreateReportRequest(BaseModel):
    """创建报告请求"""
    session_id: str
    title: str
    query: str
    sections: list[dict] = Field(default_factory=list)


class ReviseRequest(BaseModel):
    """修订请求"""
    section_id: str
    revision_type: str  # expand, simplify, evidence, rewrite
    instruction: str | None = None


class ApplyRevisionsRequest(BaseModel):
    """应用修订请求"""
    revisions: list[dict]
    user_note: str | None = None


@router.get(
    "/reports/actions",
    response_model=list[QuickAction],
    summary="获取快速操作列表"
)
async def get_quick_actions():
    """获取可用的报告快速操作"""
    return QUICK_ACTIONS


@router.post(
    "/reports",
    response_model=InteractiveReport,
    summary="创建可交互报告"
)
async def create_report(request: CreateReportRequest):
    """创建新的可交互报告"""
    iterator = get_report_iterator()
    
    sections = []
    for idx, s in enumerate(request.sections):
        section = ReportSection(
            id=s.get("id", f"section-{idx}"),
            type=SectionType(s.get("type", "analysis")),
            title=s.get("title", f"章节 {idx + 1}"),
            content=s.get("content", ""),
            sources=s.get("sources", []),
        )
        sections.append(section)
    
    report = iterator.create_report(
        session_id=request.session_id,
        title=request.title,
        query=request.query,
        sections=sections,
    )
    
    return report


@router.get(
    "/reports/{report_id}",
    response_model=InteractiveReport,
    summary="获取报告"
)
async def get_report(report_id: str):
    """获取指定报告"""
    iterator = get_report_iterator()
    report = iterator.get_report(report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.get(
    "/reports/{report_id}/sections",
    response_model=list[ReportSection],
    summary="获取报告当前版本章节"
)
async def get_report_sections(report_id: str):
    """获取报告当前版本的所有章节"""
    iterator = get_report_iterator()
    sections = iterator.get_current_sections(report_id)
    
    if not sections:
        raise HTTPException(status_code=404, detail="Report not found or has no sections")
    
    return sections


@router.post(
    "/reports/{report_id}/revise",
    response_model=RevisionResult,
    summary="修订章节"
)
async def revise_section(report_id: str, request: ReviseRequest):
    """修订报告的单个章节"""
    iterator = get_report_iterator()
    
    try:
        revision = RevisionRequest(
            section_id=request.section_id,
            revision_type=RevisionType(request.revision_type),
            instruction=request.instruction,
        )
        result = await iterator.revise_section(report_id, revision)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/reports/{report_id}/apply",
    response_model=InteractiveReport,
    summary="应用修订创建新版本"
)
async def apply_revisions(report_id: str, request: ApplyRevisionsRequest):
    """应用修订结果，创建报告新版本"""
    iterator = get_report_iterator()
    
    try:
        results = []
        for r in request.revisions:
            result = RevisionResult(
                section_id=r["section_id"],
                original_content=r.get("original_content", ""),
                revised_content=r["revised_content"],
                revision_type=RevisionType(r["revision_type"]),
                changes_summary=r.get("changes_summary", ""),
                new_sources=r.get("new_sources", []),
            )
            results.append(result)
        
        report = await iterator.apply_revisions(
            report_id, results, request.user_note
        )
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/reports/{report_id}/rollback/{version}",
    response_model=InteractiveReport,
    summary="回滚到指定版本"
)
async def rollback_report(report_id: str, version: int):
    """回滚报告到指定版本"""
    iterator = get_report_iterator()
    
    try:
        report = iterator.rollback_version(report_id, version)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/reports/{report_id}/diff",
    summary="获取版本差异"
)
async def get_version_diff(
    report_id: str,
    version_a: int = Query(..., ge=1, description="版本 A"),
    version_b: int = Query(..., ge=1, description="版本 B"),
):
    """获取两个版本之间的差异"""
    iterator = get_report_iterator()
    
    try:
        diff = iterator.get_version_diff(report_id, version_a, version_b)
        return diff
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
