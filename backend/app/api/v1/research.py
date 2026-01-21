"""
Research API - 深度研究 API 端点

提供深度研究功能的 REST API：
- POST /research/start - 启动研究任务
- GET /research/{task_id} - 获取研究状态
- GET /research/{task_id}/report - 获取研究报告
- POST /research/{task_id}/generate-ppt - 一键生成 PPT
- GET /research/{task_id}/findings - 获取结构化发现
"""
import logging
import uuid
from enum import Enum
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ...agent.agents.ppt import PPTStyle
from ...core.config import settings
from ...services.findings_extractor import FindingsExtractor
from ...services.object_storage import get_object_storage
from ...services.research_to_ppt import ResearchToPPTConverter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["research"])


# ==================== 请求/响应模型 ====================

class ResearchRequest(BaseModel):
    """研究请求"""
    topic: str = Field(..., description="研究主题")
    max_sources: int = Field(default=10, ge=1, le=20, description="最大来源数")
    include_screenshots: bool = Field(default=True, description="是否包含截图")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "topic": "Rust 异步编程最佳实践",
            "max_sources": 10,
            "include_screenshots": True
        }
    })


class ResearchStatus(BaseModel):
    """研究状态"""
    task_id: str
    status: str  # "pending", "searching", "reading", "synthesizing", "completed", "failed"
    progress: float  # 0.0 - 1.0
    phase: str
    sources_collected: int
    message: str | None = None


class ResearchSource(BaseModel):
    """研究来源"""
    url: str
    title: str
    snippet: str
    credibility: str
    key_findings: list[str] = []


class ResearchReport(BaseModel):
    """研究报告"""
    task_id: str
    topic: str
    report_markdown: str
    sources: list[ResearchSource]
    generated_at: str


class PPTStyleEnum(str, Enum):
    """可用的 PPT 风格"""
    BUSINESS = "business"
    TECH = "tech"
    MINIMAL = "minimal"
    ACADEMIC = "academic"
    CREATIVE = "creative"


class GeneratePPTRequest(BaseModel):
    """生成 PPT 请求"""
    style: PPTStyleEnum = Field(default=PPTStyleEnum.BUSINESS, description="PPT 风格")
    author: str | None = Field(default=None, description="作者名称")
    include_sources: bool = Field(default=True, description="是否包含来源页")
    include_qa: bool = Field(default=True, description="是否包含 Q&A 页")
    max_slides: int = Field(default=20, ge=5, le=30, description="最大幻灯片数")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "style": "business",
            "author": "运营团队",
            "include_sources": True,
            "max_slides": 15
        }
    })


class SlidePreview(BaseModel):
    """幻灯片预览"""
    index: int
    type: str
    title: str
    content_preview: str | None = None


class GeneratePPTResponse(BaseModel):
    """生成 PPT 响应"""
    task_id: str
    ppt_id: str
    title: str
    slide_count: int
    estimated_duration: str
    style: str
    slides_preview: list[SlidePreview]
    marp_markdown: str  # 完整的 Marp Markdown
    edit_url: str | None = None  # PPT 编辑页面 URL
    preview_url: str | None = None  # 预览页面 URL


class FindingsResponse(BaseModel):
    """结构化发现响应"""
    task_id: str
    topic: str
    summary: str
    key_findings: list[dict[str, Any]]
    data_points: list[dict[str, Any]]
    quotes: list[dict[str, Any]]
    sources_count: int
    research_duration_seconds: int
    can_generate_ppt: bool


class InterventionType(str, Enum):
    """干预类型"""
    ADD_FOCUS = "add_focus"        # 追加关注方向
    SKIP_SOURCE = "skip_source"   # 跳过某类来源
    CHANGE_DEPTH = "change_depth" # 调整研究深度
    ADD_QUERY = "add_query"       # 追加搜索词
    STOP_READING = "stop_reading" # 停止阅读当前来源
    CUSTOM = "custom"             # 自定义指令


class ResearchIntervention(BaseModel):
    """研究干预请求"""
    type: InterventionType = Field(..., description="干预类型")
    content: str = Field(..., description="干预内容")
    timestamp: str | None = Field(default=None, description="时间戳")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "type": "add_focus",
            "content": "更多关注技术实现细节",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    })


class InterventionResponse(BaseModel):
    """干预响应"""
    session_id: str
    intervention_id: str
    status: str  # "queued", "processing", "applied", "rejected"
    message: str


# ==================== 内存存储（开发用）====================

_research_tasks = {}
_research_interventions: dict[str, list[dict]] = {}  # session_id -> interventions queue


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
        "sources": []  # 来源列表
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


@router.get("/{task_id}/findings", response_model=FindingsResponse)
async def get_research_findings(task_id: str):
    """获取结构化的研究发现

    从研究报告和时间轴中提取结构化的发现，
    用于展示和生成 PPT。
    """
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    task = _research_tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed. Current status: {task['status']}"
        )

    # 提取结构化发现
    extractor = FindingsExtractor(
        session_id=task_id,
        topic=task["topic"]
    )

    # 获取报告内容
    report_markdown = None
    if task.get("report"):
        report_markdown = task["report"].report_markdown

    # 提取结构化发现
    findings = await extractor.extract_all(
        report_markdown=report_markdown
    )

    # 缓存发现
    task["findings"] = findings

    # 异步上传 findings.json（容错）
    try:
        storage = get_object_storage()
        if storage:
            bucket = settings.MINIO_BUCKET_REPORTS
            prefix = f"{task_id}"
            storage.ensure_bucket(bucket)
            storage.put_json(bucket, f"{prefix}/findings.json", findings.to_dict())
    except Exception as e:
        logger.warning(f"Upload findings.json failed: {e}")

    return FindingsResponse(
        task_id=task_id,
        topic=findings.topic,
        summary=findings.summary,
        key_findings=[f.to_dict() for f in findings.key_findings],
        data_points=[d.to_dict() for d in findings.data_points],
        quotes=[q.to_dict() for q in findings.quotes],
        sources_count=len(findings.sources),
        research_duration_seconds=findings.research_duration_seconds,
        can_generate_ppt=len(findings.key_findings) > 0
    )


@router.post("/{task_id}/generate-ppt", response_model=GeneratePPTResponse)
async def generate_ppt_from_research(task_id: str, request: GeneratePPTRequest):
    """一键生成汇报 PPT

    将研究发现转换为结构化的 PPT 大纲。
    这是 Deep Research → PPT Generation 连续体验的核心 API。

    流程：
    1. 从研究任务中提取结构化发现 (ResearchFindings)
    2. 使用 ResearchToPPTConverter 转换为 PPT 大纲
    3. 返回预览和编辑入口
    """
    if task_id not in _research_tasks:
        raise HTTPException(status_code=404, detail="Research task not found")

    task = _research_tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Research not completed. Current status: {task['status']}"
        )

    logger.info(f"Generating PPT from research: {task_id}")

    # 1. 获取或提取结构化发现
    findings = task.get("findings")
    if not findings:
        extractor = FindingsExtractor(
            session_id=task_id,
            topic=task["topic"]
        )

        report_markdown = None
        if task.get("report"):
            report_markdown = task["report"].report_markdown

        findings = await extractor.extract_all(
            report_markdown=report_markdown
        )
        task["findings"] = findings

    # 2. 转换为 PPT 大纲
    style_map = {
        PPTStyleEnum.BUSINESS: PPTStyle.BUSINESS,
        PPTStyleEnum.TECH: PPTStyle.TECH,
        PPTStyleEnum.MINIMAL: PPTStyle.MINIMAL,
        PPTStyleEnum.ACADEMIC: PPTStyle.ACADEMIC,
        PPTStyleEnum.CREATIVE: PPTStyle.CREATIVE,
    }

    converter = ResearchToPPTConverter(
        style=style_map.get(request.style, PPTStyle.BUSINESS),
        max_slides=request.max_slides
    )

    outline = converter.convert(
        findings=findings,
        author=request.author,
        include_sources=request.include_sources,
        include_qa=request.include_qa
    )

    # 3. 生成 Marp Markdown
    marp_markdown = outline.to_marp_markdown()

    # 4. 缓存 PPT 大纲
    ppt_id = str(uuid.uuid4())
    task["ppt_outline"] = outline
    task["ppt_id"] = ppt_id

    # 5. 生成预览
    slides_preview = [
        SlidePreview(
            index=i,
            type=slide.type.value,
            title=slide.title,
            content_preview=slide.points[0][:100] if slide.points else None
        )
        for i, slide in enumerate(outline.slides[:10])  # 最多预览10页
    ]

    logger.info(f"PPT generated: {ppt_id} with {len(outline.slides)} slides")

    return GeneratePPTResponse(
        task_id=task_id,
        ppt_id=ppt_id,
        title=outline.title,
        slide_count=len(outline.slides),
        estimated_duration=outline.estimated_duration or "10分钟",
        style=request.style.value,
        slides_preview=slides_preview,
        marp_markdown=marp_markdown,
        edit_url=f"/ppt/edit/{ppt_id}",
        preview_url=f"/ppt/preview/{ppt_id}"
    )


@router.get("/", response_model=list[ResearchStatus])
async def list_research_tasks(
    status: str | None = None,
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


# ==================== 研究干预 API ====================

@router.post("/sessions/{session_id}/intervene", response_model=InterventionResponse)
async def intervene_research(
    session_id: str,
    intervention: ResearchIntervention
):
    """发送研究干预指令

    在深度研究进行中，用户可以发送干预指令来：
    - 追加关注方向
    - 跳过某类来源
    - 调整研究深度
    - 追加搜索词
    - 发送自定义指令

    干预会被加入队列，Agent 会在下一个检查点处理。
    """
    from datetime import datetime

    # 初始化干预队列
    if session_id not in _research_interventions:
        _research_interventions[session_id] = []

    # 创建干预记录
    intervention_id = f"int_{uuid.uuid4().hex[:8]}"
    intervention_record = {
        "id": intervention_id,
        "type": intervention.type.value,
        "content": intervention.content,
        "timestamp": intervention.timestamp or datetime.now().isoformat(),
        "status": "queued",
    }

    # 加入队列
    _research_interventions[session_id].append(intervention_record)

    logger.info(f"Research intervention queued: {session_id} - {intervention.type.value}: {intervention.content[:50]}")

    return InterventionResponse(
        session_id=session_id,
        intervention_id=intervention_id,
        status="queued",
        message="干预指令已加入队列，将在下一个检查点处理"
    )


@router.get("/sessions/{session_id}/interventions")
async def get_pending_interventions(session_id: str):
    """获取待处理的干预指令（供 Agent 内部调用）"""
    interventions = _research_interventions.get(session_id, [])
    pending = [i for i in interventions if i["status"] == "queued"]
    return {"session_id": session_id, "pending": pending}


@router.post("/sessions/{session_id}/interventions/{intervention_id}/ack")
async def acknowledge_intervention(
    session_id: str,
    intervention_id: str,
    status: str = "applied"  # "applied" or "rejected"
):
    """确认干预已处理（供 Agent 内部调用）"""
    interventions = _research_interventions.get(session_id, [])
    for i in interventions:
        if i["id"] == intervention_id:
            i["status"] = status
            logger.info(f"Intervention {intervention_id} marked as {status}")
            return {"status": "ok", "intervention_id": intervention_id}

    raise HTTPException(status_code=404, detail="Intervention not found")


def get_interventions_for_session(session_id: str) -> list[dict]:
    """获取 session 的待处理干预（供 DeepResearchAgent 调用）"""
    interventions = _research_interventions.get(session_id, [])
    return [i for i in interventions if i["status"] == "queued"]


def mark_intervention_processed(session_id: str, intervention_id: str, status: str = "applied"):
    """标记干预已处理（供 DeepResearchAgent 调用）"""
    interventions = _research_interventions.get(session_id, [])
    for i in interventions:
        if i["id"] == intervention_id:
            i["status"] = status
            return True
    return False


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

        # 上传到对象存储（容错）
        try:
            storage = get_object_storage()
            if storage:
                bucket = settings.MINIO_BUCKET_REPORTS
                prefix = f"{task_id}"
                storage.ensure_bucket(bucket)
                # report.md
                storage.put_text(
                    bucket,
                    f"{prefix}/report.md",
                    task["report"].report_markdown,
                    content_type="text/markdown; charset=utf-8",
                )
                # metadata.json
                metadata = {
                    "task_id": task_id,
                    "topic": topic,
                    "generated_at": task["report"].generated_at,
                    "sources_collected": task.get("sources_collected", 0),
                }
                storage.put_json(bucket, f"{prefix}/metadata.json", metadata)
                # timeline.json
                storage.put_json(
                    bucket,
                    f"{prefix}/timeline.json",
                    {"task_id": task_id, "topic": topic, "entries": task.get("timeline", [])},
                )
                # record key for traceability
                task["report_object_key"] = f"{prefix}/report.md"
        except Exception as e:
            logger.warning(f"Upload to object storage failed: {e}")

        task["status"] = "completed"
        task["progress"] = 1.0
        task["message"] = "Research completed"

        logger.info(f"Research task completed: {task_id}")

    except Exception as e:
        task["status"] = "failed"
        task["message"] = str(e)
        logger.error(f"Research task failed: {task_id} - {e}")
