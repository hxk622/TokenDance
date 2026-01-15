# -*- coding: utf-8 -*-
"""
Research Timeline API endpoints.

提供研究时光长廊的 API 接口。
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from app.services.research_timeline import (
    ResearchTimelineService,
    create_research_timeline_service,
    DEFAULT_STORAGE_PATH,
)

router = APIRouter()


# ==================== Response Models ====================

class TimelineEntryResponse(BaseModel):
    """时间轴条目响应"""
    timestamp: str
    event_type: str
    title: str
    description: str
    url: Optional[str] = None
    screenshot_path: Optional[str] = None
    metadata: dict = {}


class TimelineResponse(BaseModel):
    """时间轴响应"""
    session_id: str
    topic: str
    created_at: str
    entries: list[TimelineEntryResponse]
    total_entries: int


class ScreenshotInfo(BaseModel):
    """截图信息"""
    timestamp: str
    name: str
    path: str
    url: Optional[str] = None


# ==================== API Endpoints ====================

@router.get("/sessions/{session_id}/timeline")
async def get_research_timeline(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500, description="Max entries to return"),
) -> TimelineResponse:
    """
    获取研究会话的时间轴。
    
    Args:
        session_id: 研究会话 ID
        event_type: 按事件类型过滤 (search, read, screenshot, finding, milestone)
        limit: 返回条目数限制
        
    Returns:
        TimelineResponse: 时间轴数据
    """
    storage_path = Path(DEFAULT_STORAGE_PATH) / session_id
    timeline_file = storage_path / "timeline.json"
    
    if not timeline_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Timeline not found for session: {session_id}"
        )
    
    try:
        service = ResearchTimelineService(session_id=session_id)
        timeline = service.get_timeline()
        
        # Filter by event type if specified
        entries = timeline.entries
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        
        # Apply limit
        entries = entries[-limit:]
        
        return TimelineResponse(
            session_id=timeline.session_id,
            topic=timeline.topic,
            created_at=timeline.created_at.isoformat(),
            entries=[
                TimelineEntryResponse(
                    timestamp=e.timestamp.isoformat(),
                    event_type=e.event_type,
                    title=e.title,
                    description=e.description,
                    url=e.url,
                    screenshot_path=e.screenshot_path,
                    metadata=e.metadata,
                )
                for e in entries
            ],
            total_entries=len(timeline.entries),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/timeline/screenshots")
async def list_screenshots(session_id: str) -> list[ScreenshotInfo]:
    """
    列出研究会话的所有截图。
    
    Args:
        session_id: 研究会话 ID
        
    Returns:
        list[ScreenshotInfo]: 截图列表
    """
    storage_path = Path(DEFAULT_STORAGE_PATH) / session_id
    
    if not storage_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Timeline not found for session: {session_id}"
        )
    
    try:
        service = ResearchTimelineService(session_id=session_id)
        screenshots = service.list_screenshots()
        
        return [
            ScreenshotInfo(
                timestamp=s["timestamp"],
                name=s["name"],
                path=s["path"],
                url=s.get("url"),
            )
            for s in screenshots
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/timeline/screenshots/{index}")
async def get_screenshot(session_id: str, index: int) -> FileResponse:
    """
    获取指定索引的截图文件。
    
    Args:
        session_id: 研究会话 ID
        index: 截图索引 (0-based)
        
    Returns:
        FileResponse: 截图文件
    """
    storage_path = Path(DEFAULT_STORAGE_PATH) / session_id
    
    if not storage_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Timeline not found for session: {session_id}"
        )
    
    try:
        service = ResearchTimelineService(session_id=session_id)
        screenshot_path = service.get_screenshot_path(index)
        
        if not screenshot_path or not Path(screenshot_path).exists():
            raise HTTPException(
                status_code=404,
                detail=f"Screenshot not found at index: {index}"
            )
        
        return FileResponse(
            screenshot_path,
            media_type="image/png",
            filename=Path(screenshot_path).name,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/timeline/markdown")
async def export_timeline_markdown(session_id: str) -> dict:
    """
    导出时间轴为 Markdown 格式。
    
    Args:
        session_id: 研究会话 ID
        
    Returns:
        dict: 包含 markdown 内容
    """
    storage_path = Path(DEFAULT_STORAGE_PATH) / session_id
    
    if not storage_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Timeline not found for session: {session_id}"
        )
    
    try:
        service = ResearchTimelineService(session_id=session_id)
        markdown = service.to_markdown()
        
        return {"markdown": markdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
