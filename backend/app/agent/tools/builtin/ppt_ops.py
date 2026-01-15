# -*- coding: utf-8 -*-
"""
PPT Operations Tools - PPT 操作工具

提供 PPT 生成相关的工具：
- generate_ppt_outline: 生成 PPT 大纲
- fill_ppt_content: 填充幻灯片内容
- render_ppt: 渲染预览
- export_ppt: 导出文件
"""
import uuid
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from ..base import BaseTool, ToolResult, ToolCategory, RiskLevel
from ....services.ppt_renderer import (
    PPTRendererService,
    get_ppt_renderer,
    ExportFormat,
    PPTRenderConfig,
    MarpTheme
)
from ....agent.agents.ppt import (
    PPTOutline,
    SlideContent,
    SlideType,
    PPTStyle
)

logger = logging.getLogger(__name__)


# ==================== 内存存储（用于 MVP，生产应使用 Redis/DB）====================

_outline_store: Dict[str, PPTOutline] = {}


def store_outline(outline: PPTOutline) -> str:
    """存储大纲并返回 ID"""
    _outline_store[outline.id] = outline
    return outline.id


def get_outline(outline_id: str) -> Optional[PPTOutline]:
    """获取大纲"""
    return _outline_store.get(outline_id)


# ==================== 工具实现 ====================

class GeneratePPTOutlineTool(BaseTool):
    """生成 PPT 大纲工具"""
    
    name = "generate_ppt_outline"
    description = """Generate a structured PPT outline from content.
    
Use this to create the initial presentation structure including:
- Title and metadata
- Slide types and order
- Section divisions
- Content points for each slide

Input content can be:
- A research report
- Plain text description
- Bullet points
- Any structured content"""
    
    category = ToolCategory.CONTENT_GENERATION
    risk_level = RiskLevel.LOW
    
    parameters = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The source content to transform into a presentation (research report, text, etc.)"
            },
            "title": {
                "type": "string",
                "description": "Optional presentation title. If not provided, will be extracted from content."
            },
            "slide_count": {
                "type": "integer",
                "description": "Target number of slides (default: 12)",
                "default": 12
            },
            "style": {
                "type": "string",
                "enum": ["business", "tech", "minimal", "academic", "creative"],
                "description": "Visual style preference",
                "default": "business"
            }
        },
        "required": ["content"]
    }
    
    async def execute(
        self,
        content: str,
        title: Optional[str] = None,
        slide_count: int = 12,
        style: str = "business"
    ) -> ToolResult:
        """执行大纲生成"""
        try:
            # 解析风格
            ppt_style = PPTStyle(style) if style in PPTStyle.__members__.values() else PPTStyle.BUSINESS
            
            # 创建大纲
            outline = PPTOutline(
                title=title or self._extract_title(content),
                style=ppt_style,
                source_content=content
            )
            
            # 生成幻灯片结构
            slides = self._generate_slides(content, slide_count)
            outline.slides = slides
            outline.estimated_duration = outline.estimate_duration()
            
            # 存储大纲
            outline_id = store_outline(outline)
            
            # 构建返回结果
            result = {
                "outline_id": outline_id,
                "title": outline.title,
                "style": outline.style.value,
                "slide_count": len(outline.slides),
                "estimated_duration": outline.estimated_duration,
                "slides": [
                    {
                        "index": i,
                        "type": slide.type.value,
                        "title": slide.title
                    }
                    for i, slide in enumerate(outline.slides)
                ]
            }
            
            return ToolResult(
                success=True,
                data=result,
                message=f"Generated outline with {len(outline.slides)} slides"
            )
            
        except Exception as e:
            logger.error(f"Outline generation failed: {e}")
            return ToolResult(success=False, error=str(e))
    
    def _extract_title(self, content: str) -> str:
        """从内容提取标题"""
        lines = content.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line and len(line) < 100 and not line.startswith(('#', '-', '*', '>')):
                return line
        return "Presentation"
    
    def _generate_slides(self, content: str, target_count: int) -> List[SlideContent]:
        """生成幻灯片列表"""
        slides = []
        
        # 1. 标题页
        title = self._extract_title(content)
        slides.append(SlideContent(
            type=SlideType.TITLE,
            title=title,
            subtitle="Generated by TokenDance"
        ))
        
        # 2. 解析内容章节
        sections = self._parse_sections(content)
        
        # 3. 目录页（如果有多个章节）
        if len(sections) > 2:
            slides.append(SlideContent(
                type=SlideType.TOC,
                title="目录",
                points=[s.get("title", f"Section {i+1}") for i, s in enumerate(sections[:6])]
            ))
        
        # 4. 内容页
        remaining_slots = target_count - 3  # 留出标题、目录、结论
        slots_per_section = max(1, remaining_slots // len(sections)) if sections else 2
        
        for section in sections:
            # 章节标题
            if section.get("title"):
                slides.append(SlideContent(
                    type=SlideType.SECTION,
                    title=section["title"]
                ))
            
            # 内容页
            points = section.get("points", [])
            for i in range(0, len(points), 4):
                if len(slides) >= target_count - 2:
                    break
                chunk = points[i:i+4]
                slides.append(SlideContent(
                    type=SlideType.CONTENT,
                    title=section.get("title", "Content"),
                    points=chunk
                ))
        
        # 5. 结论页
        conclusions = self._extract_conclusions(content)
        slides.append(SlideContent(
            type=SlideType.CONCLUSION,
            title="结论",
            points=conclusions
        ))
        
        # 6. 感谢页
        slides.append(SlideContent(
            type=SlideType.THANK_YOU,
            title="Thank You",
            subtitle="Questions?"
        ))
        
        return slides
    
    def _parse_sections(self, content: str) -> List[Dict[str, Any]]:
        """解析内容章节"""
        import re
        
        sections = []
        current = {"title": "", "points": []}
        
        for line in content.split('\n'):
            line = line.strip()
            
            if line.startswith('## '):
                if current["title"] or current["points"]:
                    sections.append(current)
                current = {"title": line[3:].strip(), "points": []}
            
            elif line.startswith(('- ', '* ', '• ')):
                point = line[2:].strip()
                if point and len(point) < 200:
                    current["points"].append(point)
            
            elif re.match(r'^\d+[\.\)]\s+', line):
                point = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                if point and len(point) < 200:
                    current["points"].append(point)
        
        if current["title"] or current["points"]:
            sections.append(current)
        
        if not sections:
            # 如果没有检测到章节，创建单个默认章节
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            sections = [{"title": "Overview", "points": lines[:10]}]
        
        return sections
    
    def _extract_conclusions(self, content: str) -> List[str]:
        """提取结论"""
        import re
        
        conclusions = []
        
        patterns = [
            r'(?:结论|Conclusion|Summary)[：:]\s*\n([\s\S]*?)(?=\n##|\Z)',
            r'(?:建议|Recommendation)[：:]\s*\n([\s\S]*?)(?=\n##|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                for line in match.group(1).split('\n'):
                    line = line.strip()
                    if line.startswith(('- ', '* ')):
                        conclusions.append(line[2:].strip())
        
        if not conclusions:
            conclusions = ["关键发现", "下一步行动", "感谢聆听"]
        
        return conclusions[:5]


class FillPPTContentTool(BaseTool):
    """填充 PPT 内容工具"""
    
    name = "fill_ppt_content"
    description = """Fill detailed content for slides in an outline.
    
Use this after generating an outline to:
- Add detailed bullet points
- Enhance slide content
- Add speaker notes
- Suggest visualizations"""
    
    category = ToolCategory.CONTENT_GENERATION
    risk_level = RiskLevel.LOW
    
    parameters = {
        "type": "object",
        "properties": {
            "outline_id": {
                "type": "string",
                "description": "The outline ID returned from generate_ppt_outline"
            },
            "slide_index": {
                "type": "integer",
                "description": "Optional: specific slide index to fill. If not provided, fills all slides."
            },
            "additional_context": {
                "type": "string",
                "description": "Optional: additional context or instructions for content generation"
            }
        },
        "required": ["outline_id"]
    }
    
    async def execute(
        self,
        outline_id: str,
        slide_index: Optional[int] = None,
        additional_context: Optional[str] = None
    ) -> ToolResult:
        """执行内容填充"""
        try:
            outline = get_outline(outline_id)
            if not outline:
                return ToolResult(success=False, error=f"Outline not found: {outline_id}")
            
            # 如果指定了具体幻灯片
            if slide_index is not None:
                if 0 <= slide_index < len(outline.slides):
                    slide = outline.slides[slide_index]
                    # 简单的内容增强（实际应用中可以用 LLM）
                    if not slide.notes:
                        slide.notes = f"Key talking point for: {slide.title}"
                    
                    return ToolResult(
                        success=True,
                        data={
                            "slide_index": slide_index,
                            "type": slide.type.value,
                            "title": slide.title,
                            "points": slide.points,
                            "notes": slide.notes
                        },
                        message=f"Filled content for slide {slide_index}"
                    )
                else:
                    return ToolResult(success=False, error=f"Invalid slide index: {slide_index}")
            
            # 填充所有幻灯片
            filled = []
            for i, slide in enumerate(outline.slides):
                if not slide.notes and slide.type in [SlideType.CONTENT, SlideType.DATA]:
                    slide.notes = f"Elaborate on: {slide.title}"
                filled.append({
                    "index": i,
                    "type": slide.type.value,
                    "title": slide.title,
                    "filled": True
                })
            
            # 更新存储
            store_outline(outline)
            
            return ToolResult(
                success=True,
                data={
                    "outline_id": outline_id,
                    "slides_filled": len(filled),
                    "slides": filled
                },
                message=f"Filled content for {len(filled)} slides"
            )
            
        except Exception as e:
            logger.error(f"Content filling failed: {e}")
            return ToolResult(success=False, error=str(e))


class RenderPPTTool(BaseTool):
    """渲染 PPT 预览工具"""
    
    name = "render_ppt"
    description = """Render the presentation to HTML for preview.
    
Use this to:
- Preview the presentation in browser
- Check visual appearance
- Verify content layout"""
    
    category = ToolCategory.CONTENT_GENERATION
    risk_level = RiskLevel.LOW
    
    parameters = {
        "type": "object",
        "properties": {
            "outline_id": {
                "type": "string",
                "description": "The outline ID to render"
            },
            "theme": {
                "type": "string",
                "enum": ["default", "gaia", "uncover", "business", "tech", "minimal"],
                "description": "Visual theme to apply",
                "default": "default"
            }
        },
        "required": ["outline_id"]
    }
    
    async def execute(
        self,
        outline_id: str,
        theme: str = "default"
    ) -> ToolResult:
        """执行渲染"""
        try:
            outline = get_outline(outline_id)
            if not outline:
                return ToolResult(success=False, error=f"Outline not found: {outline_id}")
            
            # 生成 Marp Markdown
            markdown_content = outline.to_marp_markdown()
            
            # 获取渲染器
            renderer = get_ppt_renderer()
            
            # 配置
            config = PPTRenderConfig()
            if theme in MarpTheme.__members__.values():
                config.theme = MarpTheme(theme)
            
            # 渲染
            result = await renderer.render_to_html(
                markdown_content,
                config=config,
                output_name=outline_id[:8]
            )
            
            if result.success:
                return ToolResult(
                    success=True,
                    data={
                        "preview_url": result.preview_url,
                        "markdown_preview": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content,
                        "file_size": result.file_size,
                        "render_time": result.render_time
                    },
                    message="Presentation rendered successfully"
                )
            else:
                # 如果 Marp 不可用，返回 Markdown
                return ToolResult(
                    success=True,
                    data={
                        "markdown": markdown_content,
                        "note": "Marp CLI not available. Here's the Markdown source."
                    },
                    message="Generated Markdown (Marp not available for HTML rendering)"
                )
                
        except Exception as e:
            logger.error(f"Render failed: {e}")
            return ToolResult(success=False, error=str(e))


class ExportPPTTool(BaseTool):
    """导出 PPT 文件工具"""
    
    name = "export_ppt"
    description = """Export the presentation to a downloadable file.
    
Supported formats:
- pdf: Best for sharing and printing
- html: Interactive web presentation
- pptx: PowerPoint format (requires python-pptx)"""
    
    category = ToolCategory.FILE_MANAGEMENT
    risk_level = RiskLevel.LOW
    
    parameters = {
        "type": "object",
        "properties": {
            "outline_id": {
                "type": "string",
                "description": "The outline ID to export"
            },
            "format": {
                "type": "string",
                "enum": ["pdf", "html", "pptx"],
                "description": "Export format",
                "default": "pdf"
            },
            "filename": {
                "type": "string",
                "description": "Optional output filename (without extension)"
            }
        },
        "required": ["outline_id"]
    }
    
    async def execute(
        self,
        outline_id: str,
        format: str = "pdf",
        filename: Optional[str] = None
    ) -> ToolResult:
        """执行导出"""
        try:
            outline = get_outline(outline_id)
            if not outline:
                return ToolResult(success=False, error=f"Outline not found: {outline_id}")
            
            # 生成 Markdown
            markdown_content = outline.to_marp_markdown()
            
            # 获取渲染器
            renderer = get_ppt_renderer()
            
            # 解析格式
            export_format = ExportFormat(format) if format in ExportFormat.__members__.values() else ExportFormat.PDF
            
            # 输出文件名
            output_name = filename or f"{outline.title[:30].replace(' ', '_')}_{outline_id[:6]}"
            
            # 导出
            result = await renderer.export(
                markdown_content,
                format=export_format,
                output_name=output_name
            )
            
            if result.success:
                return ToolResult(
                    success=True,
                    data={
                        "download_url": result.download_url,
                        "file_path": result.output_path,
                        "file_size": result.file_size,
                        "format": format,
                        "render_time": result.render_time
                    },
                    message=f"Exported to {format.upper()} successfully"
                )
            else:
                # 如果导出失败，返回 Markdown 作为后备
                return ToolResult(
                    success=True,
                    data={
                        "markdown": markdown_content,
                        "note": f"Export to {format} failed: {result.error}. Here's the Markdown source.",
                        "instructions": "Save as .md file and use: marp slides.md --pdf"
                    },
                    message="Export failed, returning Markdown source"
                )
                
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return ToolResult(success=False, error=str(e))


# ==================== 工具注册 ====================

def get_ppt_tools() -> List[BaseTool]:
    """获取所有 PPT 工具"""
    return [
        GeneratePPTOutlineTool(),
        FillPPTContentTool(),
        RenderPPTTool(),
        ExportPPTTool()
    ]
