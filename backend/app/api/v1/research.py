# -*- coding: utf-8 -*-
"""
Research API - 深度研究 API 端点

提供深度研究功能的 REST API：
- POST /research/start - 启动研究任务
- GET /research/{task_id} - 获取研究状态
- GET /research/{task_id}/report - 获取研究报告
- GET /research/{task_id}/timeline - 获取研究时间轴
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


# ==================== 请求/响应模型 ====================

class ResearchRequest(BaseModel):
    """研究请求"""
    topic: str = Field(..., description="研究主题")
    max_sources: int = Field(default=10, ge=1, le=20, description="最大来源数")
    include_screenshots: bool = Field(default=True, description="是否包含截图")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Rust 异步编程最佳实践",
                "max_sources": 10,
                "include_screenshots": True
            }
        }


class ResearchStatus(BaseModel):
    """研究状态"""
    task_id: str
    status: str  # "pending", "searching", "reading", "synthesizing", "completed", "failed"
    progress: float  # 0.0 - 1.0
    phase: str
    sources_collected: int
    message: Optional[str] = None


class ResearchSource(BaseModel):
    """研究来源"""
    url: str
    title: str
    snippet: str
    credibility: str
    key_findings: List[str] = []


class ResearchReport(BaseModel):
    """研究报告"""
    task_id: str
    topic: str
    report_markdown: str
    sources: List[ResearchSource]
    generated_at: str


class TimelineEntry(BaseModel):
    """时间轴条目"""
    timestamp: str
    event_type: str
    title: str
    description: str
    url: Optional[str] = None
    screenshot_path: Optional[str] = None


class ResearchTimeline(BaseModel):
    """研究时间轴"""
    task_id: str
    topic: str
    entries: List[TimelineEntry]


# ==================== 内存存储（开发用）====================

_research_tasks = {}


# ==================== API 端点 ====================

@router.post("/start", response_model=ResearchStatus)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """启动研究任务
    
    创建一个新的深度研究任务并在后台执行。
    返回任务 ID 用于后续查询。
    """
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    _research_tasks[task_id] = {
        "task_id": task_id,
        "topic": request.topic,
        "status": "pending",
        "progress": 0.0,
        "phase": "init",
        "sources_collected": 0,
        "max_sources": request.max_sources,
        "include_screenshots": request.include_screenshots,
        "report": None,
        "timeline": []
    }
    
    # 启动后台任务
    background_tasks.add_task(
        _execute_research,
        task_id,
        request.topic,
        request.max_sources
    )
    
    logger.info(f"Research task started: {task_id} - {request.topic}")
    
    return ResearchStatus(
        task_id=task_id,
        status="pending",
        progress=0.0,
        phase="init",
        sources_collected=0,
        message="Research task created"
    )


@router.get("/{task_id}", response_model=ResearchStatus)
async def get_research_status(task_id: str):
    """获取研究任务状态"""
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")
    
    task = _research_tasks[task_id]
    
    return ResearchStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        phase=task["phase"],
        sources_collected=task["sources_collected"],
        message=task.get("message")
    )


@router.get("/{task_id}/report", response_model=ResearchReport)
async def get_research_report(task_id: str):
    """获取研究报告
    
    只有当研究任务完成后才能获取报告。
    """
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")
    
    task = _research_tasks[task_id]
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed. Current status: {task['status']}"
        )
    
    if not task.get("report"):
        raise HTTPException(status_code=404, detail="Report not generated")
    
    return task["report"]


@router.get("/{task_id}/timeline", response_model=ResearchTimeline)
async def get_research_timeline(task_id: str):
    """获取研究时间轴"""
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")
    
    task = _research_tasks[task_id]
    
    return ResearchTimeline(
        task_id=task_id,
        topic=task["topic"],
        entries=[
            TimelineEntry(**entry) for entry in task.get("timeline", [])
        ]
    )


@router.delete("/{task_id}")
async def cancel_research(task_id: str):
    """取消研究任务"""
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")
    
    task = _research_tasks[task_id]
    
    if task["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel completed task")
    
    task["status"] = "cancelled"
    task["message"] = "Task cancelled by user"
    
    logger.info(f"Research task cancelled: {task_id}")
    
    return {"message": "Research task cancelled", "task_id": task_id}


@router.get("/", response_model=List[ResearchStatus])
async def list_research_tasks(
    status: Optional[str] = None,
    limit: int = 10
):
    """列出研究任务"""
    tasks = list(_research_tasks.values())
    
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    
    # 按创建时间倒序
    tasks = sorted(tasks, key=lambda x: x.get("created_at", ""), reverse=True)
    
    return [
        ResearchStatus(
            task_id=t["task_id"],
            status=t["status"],
            progress=t["progress"],
            phase=t["phase"],
            sources_collected=t["sources_collected"]
        )
        for t in tasks[:limit]
    ]


# ==================== 后台任务 ====================

async def _execute_research(task_id: str, topic: str, max_sources: int):
    """执行研究任务（后台）
    
    这是一个简化的实现，实际应该使用 DeepResearchAgent。
    """
    import asyncio
    from datetime import datetime
    
    task = _research_tasks.get(task_id)
    if not task:
        return
    
    try:
        # 模拟研究过程
        phases = [
            ("searching", 0.2, "Searching for sources..."),
            ("reading", 0.5, "Reading and analyzing sources..."),
            ("synthesizing", 0.8, "Synthesizing information..."),
            ("reporting", 0.95, "Generating report...")
        ]
        
        for phase, progress, message in phases:
            if task["status"] == "cancelled":
                return
            
            task["status"] = phase
            task["phase"] = phase
            task["progress"] = progress
            task["message"] = message
            
            # 添加时间轴条目
            task["timeline"].append({
                "timestamp": datetime.now().isoformat(),
                "event_type": "milestone",
                "title": f"Phase: {phase}",
                "description": message
            })
            
            await asyncio.sleep(2)  # 模拟处理时间
        
        # 生成报告
        task["report"] = ResearchReport(
            task_id=task_id,
            topic=topic,
            report_markdown=f"""# Research Report: {topic}

## Executive Summary
This is a placeholder research report for the topic: {topic}

## Key Findings
1. Finding 1
2. Finding 2
3. Finding 3

## References
[1] Source 1
[2] Source 2
""",
            sources=[],
            generated_at=datetime.now().isoformat()
        )
        
        task["status"] = "completed"
        task["progress"] = 1.0
        task["message"] = "Research completed"
        
        logger.info(f"Research task completed: {task_id}")
        
    except Exception as e:
        task["status"] = "failed"
        task["message"] = str(e)
        logger.error(f"Research task failed: {task_id} - {e}")
