"""
Browser Automation API

浏览器自动化相关的 API 端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.services.browser_automation import (
    check_browser_health,
    get_session_manager,
    init_session_manager,
    shutdown_session_manager,
)

router = APIRouter(prefix="/browser", tags=["browser"])


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str  # healthy | degraded | unhealthy
    agent_browser_available: bool
    playwright_available: bool
    active_sessions: int


class SessionInfo(BaseModel):
    """会话信息"""
    task_id: str
    implementation: str
    created_at: str
    last_activity: str


class SessionStatsResponse(BaseModel):
    """会话统计响应"""
    active_sessions: int
    max_sessions: int
    agent_browser_available: Optional[bool]
    sessions: List[SessionInfo]


@router.get("/health", response_model=HealthResponse)
async def browser_health():
    """
    浏览器服务健康检查
    
    返回浏览器自动化服务的可用性状态：
    - healthy: agent-browser 和 Playwright 都可用
    - degraded: 只有 Playwright 可用（降级模式）
    - unhealthy: 没有可用的浏览器服务
    """
    result = await check_browser_health()
    return HealthResponse(**result)


@router.get("/sessions", response_model=SessionStatsResponse)
async def session_stats():
    """
    获取浏览器会话统计
    
    返回当前活跃的浏览器会话信息
    """
    manager = get_session_manager()
    stats = manager.get_stats()
    
    return SessionStatsResponse(
        active_sessions=stats["active_sessions"],
        max_sessions=stats["max_sessions"],
        agent_browser_available=stats["agent_browser_available"],
        sessions=[
            SessionInfo(**s) for s in stats["sessions"]
        ]
    )


@router.post("/sessions/{task_id}/close")
async def close_session(task_id: str):
    """
    关闭指定任务的浏览器会话
    
    Args:
        task_id: 任务 ID
    """
    manager = get_session_manager()
    await manager.close_session(task_id)
    return {"status": "closed", "task_id": task_id}


@router.post("/sessions/cleanup")
async def cleanup_sessions():
    """
    清理所有超时的浏览器会话
    """
    manager = get_session_manager()
    await manager._cleanup_expired_sessions()
    return {"status": "cleaned"}


# 生命周期事件处理
async def startup_browser_service():
    """应用启动时初始化浏览器服务"""
    await init_session_manager()


async def shutdown_browser_service():
    """应用关闭时清理浏览器服务"""
    await shutdown_session_manager()
