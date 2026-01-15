# -*- coding: utf-8 -*-
"""
PPT Generation API - PPT 生成 API 端点

提供 PPT 生成相关的 REST API：
- POST /api/v1/ppt/outline - 生成 PPT 大纲
- POST /api/v1/ppt/render - 渲染为 HTML 预览
- POST /api/v1/ppt/export - 导出为 PDF/HTML/PPTX
- GET /api/v1/ppt/templates - 获取可用模板
- GET /api/v1/ppt/health - 健康检查
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ...services.ppt_renderer import (
    get_ppt_renderer,
    check_renderer_health,
    ExportFormat,
    PPTRenderConfig,
    MarpTheme
)
from ...agent.tools.builtin.ppt_ops import (
    GeneratePPTOutlineTool,
    FillPPTContentTool,
    RenderPPTTool,
    ExportPPTTool,
    get_outline,
    store_outline
)
from ...agent.agents.ppt import PPTOutline, SlideContent, SlideType, PPTStyle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ppt", tags=["PPT Generation"])


# ==================== 请求/响应模型 ====================

class GenerateOutlineRequest(BaseModel):
    """生成大纲请求"""
    content: str = Field(..., description="输入内容（研究报告、文本等）")
    title: Optional[str] = Field(None, description="演示标题")
    slide_count: int = Field(12, ge=5, le=50, description="目标幻灯片数量")
    style: str = Field("business", description="风格：business/tech/minimal/academic/creative")


class SlideInfo(BaseModel):
    """幻灯片信息"""
    index: int
    type: str
    title: str


class OutlineResponse(BaseModel):
    """大纲响应"""
    outline_id: str
    title: str
    style: str
    slide_count: int
    estimated_duration: str
    slides: List[SlideInfo]


class RenderRequest(BaseModel):
    """渲染请求"""
    outline_id: str = Field(..., description="大纲 ID")
    theme: str = Field("default", description="主题：default/gaia/uncover/business/tech/minimal")


class RenderResponse(BaseModel):
    """渲染响应"""
    success: bool
    preview_url: Optional[str] = None
    markdown: Optional[str] = None
    file_size: Optional[int] = None
    render_time: Optional[float] = None
    note: Optional[str] = None


class ExportRequest(BaseModel):
    """导出请求"""
    outline_id: str = Field(..., description="大纲 ID")
    format: str = Field("pdf", description="导出格式：pdf/html/pptx")
    filename: Optional[str] = Field(None, description="输出文件名")


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool
    download_url: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    format: Optional[str] = None
    render_time: Optional[float] = None
    markdown: Optional[str] = None
    note: Optional[str] = None
    instructions: Optional[str] = None


class TemplateInfo(BaseModel):
    """模板信息"""
    id: str
    name: str
    description: str
    style: str
    tags: List[str]


class HealthResponse(BaseModel):
    """健康检查响应"""
    service: str
    status: str
    marp_cli: bool
    workspace: str
    themes_available: List[str]


# ==================== API 端点 ====================

@router.post("/outline", response_model=OutlineResponse)
async def generate_outline(request: GenerateOutlineRequest):
    """生成 PPT 大纲
    
    从输入内容（研究报告、文本等）生成结构化的 PPT 大纲。
    
    **输入内容示例**:
    - Deep Research 生成的研究报告
    - Markdown 格式的文档
    - 普通文本内容
    - 要点列表
    
    **返回**:
    - 大纲 ID（用于后续操作）
    - 幻灯片结构预览
    - 预计演示时长
    """
    try:
        tool = GeneratePPTOutlineTool()
        result = await tool.execute(
            content=request.content,
            title=request.title,
            slide_count=request.slide_count,
            style=request.style
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        data = result.data
        return OutlineResponse(
            outline_id=data["outline_id"],
            title=data["title"],
            style=data["style"],
            slide_count=data["slide_count"],
            estimated_duration=data["estimated_duration"],
            slides=[SlideInfo(**s) for s in data["slides"]]
        )
        
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/render", response_model=RenderResponse)
async def render_preview(request: RenderRequest):
    """渲染 PPT 预览
    
    将大纲渲染为 HTML 格式，可在浏览器中预览。
    
    **主题选项**:
    - `default`: Marp 默认主题
    - `gaia`: 简约风格
    - `uncover`: 现代风格
    - `business`: 商务风格（自定义）
    - `tech`: 科技风格（自定义）
    - `minimal`: 极简风格（自定义）
    
    **返回**:
    - 预览 URL（如果 Marp CLI 可用）
    - Markdown 源码（作为后备）
    """
    try:
        tool = RenderPPTTool()
        result = await tool.execute(
            outline_id=request.outline_id,
            theme=request.theme
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        data = result.data
        return RenderResponse(
            success=True,
            preview_url=data.get("preview_url"),
            markdown=data.get("markdown"),
            file_size=data.get("file_size"),
            render_time=data.get("render_time"),
            note=data.get("note")
        )
        
    except Exception as e:
        logger.error(f"Render failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=ExportResponse)
async def export_presentation(request: ExportRequest):
    """导出 PPT 文件
    
    将演示文稿导出为可下载的文件。
    
    **支持格式**:
    - `pdf`: 最适合分享和打印
    - `html`: 交互式网页演示
    - `pptx`: PowerPoint 格式（需要 python-pptx）
    
    **返回**:
    - 下载 URL
    - 文件大小
    - 如果导出失败，返回 Markdown 源码
    """
    try:
        tool = ExportPPTTool()
        result = await tool.execute(
            outline_id=request.outline_id,
            format=request.format,
            filename=request.filename
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        data = result.data
        return ExportResponse(
            success=True,
            download_url=data.get("download_url"),
            file_path=data.get("file_path"),
            file_size=data.get("file_size"),
            format=data.get("format"),
            render_time=data.get("render_time"),
            markdown=data.get("markdown"),
            note=data.get("note"),
            instructions=data.get("instructions")
        )
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/outline/{outline_id}")
async def get_outline_details(outline_id: str):
    """获取大纲详情
    
    获取已生成大纲的完整信息。
    """
    outline = get_outline(outline_id)
    if not outline:
        raise HTTPException(status_code=404, detail=f"Outline not found: {outline_id}")
    
    return {
        "outline_id": outline.id,
        "title": outline.title,
        "style": outline.style.value,
        "theme": outline.theme,
        "slide_count": outline.get_slide_count(),
        "estimated_duration": outline.estimated_duration,
        "created_at": outline.created_at.isoformat(),
        "slides": [
            {
                "id": slide.id,
                "type": slide.type.value,
                "title": slide.title,
                "subtitle": slide.subtitle,
                "points": slide.points,
                "notes": slide.notes
            }
            for slide in outline.slides
        ]
    }


@router.get("/outline/{outline_id}/markdown")
async def get_outline_markdown(outline_id: str):
    """获取大纲的 Markdown 源码
    
    返回可直接用于 Marp 的 Markdown 内容。
    """
    outline = get_outline(outline_id)
    if not outline:
        raise HTTPException(status_code=404, detail=f"Outline not found: {outline_id}")
    
    return {
        "outline_id": outline.id,
        "title": outline.title,
        "markdown": outline.to_marp_markdown()
    }


@router.get("/templates", response_model=List[TemplateInfo])
async def list_templates():
    """获取可用模板列表
    
    返回所有可用的 PPT 模板。
    """
    templates = [
        TemplateInfo(
            id="business_proposal",
            name="商业提案",
            description="专业的商业提案或项目汇报 PPT",
            style="business",
            tags=["business", "proposal", "presentation"]
        ),
        TemplateInfo(
            id="project_report",
            name="项目汇报",
            description="项目进展或总结汇报 PPT",
            style="business",
            tags=["project", "report", "summary"]
        ),
        TemplateInfo(
            id="product_intro",
            name="产品介绍",
            description="产品功能介绍或演示 PPT",
            style="tech",
            tags=["product", "introduction", "demo"]
        ),
        TemplateInfo(
            id="training",
            name="培训课件",
            description="培训或教学用的 PPT 课件",
            style="academic",
            tags=["training", "education", "course"]
        ),
        TemplateInfo(
            id="pitch_deck",
            name="融资路演",
            description="面向投资人的融资路演 PPT",
            style="business",
            tags=["pitch", "investor", "funding"]
        )
    ]
    return templates


@router.get("/themes")
async def list_themes():
    """获取可用主题列表
    
    返回所有可用的视觉主题。
    """
    return {
        "builtin": [
            {"id": "default", "name": "Default", "description": "Marp 默认主题"},
            {"id": "gaia", "name": "Gaia", "description": "简约风格"},
            {"id": "uncover", "name": "Uncover", "description": "现代风格"}
        ],
        "custom": [
            {"id": "business", "name": "Business", "description": "商务风格 - 深蓝渐变背景"},
            {"id": "tech", "name": "Tech", "description": "科技风格 - 深色背景霓虹高亮"},
            {"id": "minimal", "name": "Minimal", "description": "极简风格 - 白色背景"}
        ]
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """PPT 服务健康检查
    
    检查 PPT 渲染服务的状态：
    - Marp CLI 是否可用
    - 工作目录是否正常
    - 可用主题列表
    """
    health = await check_renderer_health()
    
    return HealthResponse(
        service=health["service"],
        status=health["status"],
        marp_cli=health["marp_cli"],
        workspace=health["workspace"],
        themes_available=[str(t) for t in health["themes_available"]]
    )


@router.post("/cleanup")
async def cleanup_old_files(background_tasks: BackgroundTasks, max_age_hours: int = 24):
    """清理旧的 PPT 文件
    
    删除超过指定时间的临时文件。
    
    **参数**:
    - max_age_hours: 最大保留时间（小时），默认 24
    """
    renderer = get_ppt_renderer()
    
    # 在后台执行清理
    background_tasks.add_task(renderer.cleanup_old_files, max_age_hours)
    
    return {
        "status": "cleanup_scheduled",
        "max_age_hours": max_age_hours
    }
