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

from app.core.database import get_async_db
from app.schemas.reasoning_trace import (
    ReasoningTrace,
    ReasoningTraceFeedback,
    ReasoningTraceList,
)
from app.services.preference_learner import PreferenceLearner, get_preference_learner
from app.services.reasoning_trace import get_reasoning_service

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
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    domain: str = Query(..., description="要信任的域名"),
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    domain: str = Query(..., description="要屏蔽的域名"),
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    domain: str = Query(..., description="要移除的域名"),
    db: Annotated[AsyncSession, Depends(get_async_db)]
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
    domain: str = Query(..., description="要移除的域名"),
    db: Annotated[AsyncSession, Depends(get_async_db)]
):
    """从屏蔽列表移除域名"""
    learner = await get_preference_learner(db, user_id)
    preference = await learner.get_or_create_preference()
    
    blocked = list(preference.blocked_domains or [])
    if domain in blocked:
        blocked.remove(domain)
        await learner.update_explicit_preference({"blocked_domains": blocked})
    
    return {"status": "ok", "blocked_domains": blocked}
