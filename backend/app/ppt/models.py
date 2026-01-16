"""
PPT Data Models - PPT 数据模型定义

包含：
- SlideType: 幻灯片类型枚举
- SlideContent: 单页内容模型
- PresentationSpec: 完整演示文稿规格
- BrandKit: 品牌配置
- TemplateConfig: 模板配置
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class SlideType(str, Enum):
    """幻灯片类型枚举"""
    
    # 基础类型
    TITLE = "title"              # 标题页
    SECTION = "section"          # 章节分隔页
    BULLET = "bullet"            # 要点列表页
    TWO_COLUMN = "two_column"    # 双栏布局
    THREE_COLUMN = "three_column"  # 三栏布局
    
    # 内容类型
    CONTENT = "content"          # 通用内容页
    IMAGE = "image"              # 图片页
    IMAGE_TEXT = "image_text"    # 图文混排
    QUOTE = "quote"              # 引用页
    
    # 数据类型
    CHART = "chart"              # 图表页
    TABLE = "table"              # 表格页
    COMPARISON = "comparison"    # 对比页
    TIMELINE = "timeline"        # 时间线
    
    # 特殊类型
    THANK_YOU = "thank_you"      # 结束感谢页
    BLANK = "blank"              # 空白页


class ChartType(str, Enum):
    """图表类型"""
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"


class BrandKit(BaseModel):
    """品牌配置
    
    定义演示文稿的视觉风格，包括颜色、字体等。
    """
    
    # 主色调
    primary_color: str = Field(
        default="#1a1a2e",
        description="主色（标题、强调）"
    )
    secondary_color: str = Field(
        default="#4a90e2",
        description="辅助色（图标、链接）"
    )
    accent_color: str = Field(
        default="#e94560",
        description="强调色（CTA、重点）"
    )
    
    # 背景色
    background_color: str = Field(
        default="#ffffff",
        description="背景色"
    )
    surface_color: str = Field(
        default="#f8f9fa",
        description="表面色（卡片、区块）"
    )
    
    # 文字颜色
    text_primary: str = Field(
        default="#1f2937",
        description="主文字颜色"
    )
    text_secondary: str = Field(
        default="#6b7280",
        description="次要文字颜色"
    )
    
    # 字体
    title_font: str = Field(
        default="Microsoft YaHei",
        description="标题字体"
    )
    body_font: str = Field(
        default="Microsoft YaHei",
        description="正文字体"
    )
    
    # Logo
    logo_path: Optional[str] = Field(
        default=None,
        description="Logo 图片路径"
    )
    
    @classmethod
    def default_dark(cls) -> "BrandKit":
        """深色主题"""
        return cls(
            primary_color="#ffffff",
            secondary_color="#60a5fa",
            accent_color="#f472b6",
            background_color="#1a1a2e",
            surface_color="#2d2d44",
            text_primary="#f3f4f6",
            text_secondary="#9ca3af",
        )
    
    @classmethod
    def default_light(cls) -> "BrandKit":
        """浅色主题（默认）"""
        return cls()


class ChartData(BaseModel):
    """图表数据"""
    
    chart_type: ChartType = Field(
        default=ChartType.BAR,
        description="图表类型"
    )
    title: Optional[str] = Field(
        default=None,
        description="图表标题"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="分类标签（X轴）"
    )
    series: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="数据系列，格式: [{'name': '系列名', 'values': [1,2,3]}]"
    )


class TableData(BaseModel):
    """表格数据"""
    
    headers: List[str] = Field(
        default_factory=list,
        description="表头"
    )
    rows: List[List[str]] = Field(
        default_factory=list,
        description="数据行"
    )
    has_header_row: bool = Field(
        default=True,
        description="是否有表头行"
    )


class SlideContent(BaseModel):
    """单页幻灯片内容
    
    包含幻灯片的所有内容数据，模板引擎根据 type 选择合适的模板渲染。
    """
    
    # 类型
    type: SlideType = Field(
        default=SlideType.CONTENT,
        description="幻灯片类型"
    )
    
    # 通用字段
    title: Optional[str] = Field(
        default=None,
        description="标题"
    )
    subtitle: Optional[str] = Field(
        default=None,
        description="副标题"
    )
    body: Optional[str] = Field(
        default=None,
        description="正文内容"
    )
    
    # 列表内容
    bullets: Optional[List[str]] = Field(
        default=None,
        description="要点列表"
    )
    
    # 多栏内容
    columns: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="多栏内容，格式: [{'title': '栏目1', 'content': '内容'}]"
    )
    
    # 图片
    image_path: Optional[str] = Field(
        default=None,
        description="图片路径"
    )
    image_caption: Optional[str] = Field(
        default=None,
        description="图片说明"
    )
    image_position: str = Field(
        default="right",
        description="图片位置: left, right, center, background"
    )
    
    # 引用
    quote: Optional[str] = Field(
        default=None,
        description="引用文字"
    )
    quote_author: Optional[str] = Field(
        default=None,
        description="引用来源/作者"
    )
    
    # 图表
    chart: Optional[ChartData] = Field(
        default=None,
        description="图表数据"
    )
    
    # 表格
    table: Optional[TableData] = Field(
        default=None,
        description="表格数据"
    )
    
    # 对比
    comparison: Optional[Dict[str, Any]] = Field(
        default=None,
        description="对比数据，格式: {'left': {...}, 'right': {...}}"
    )
    
    # 时间线
    timeline: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="时间线数据，格式: [{'date': '2024', 'event': '事件'}]"
    )
    
    # 备注
    speaker_notes: Optional[str] = Field(
        default=None,
        description="演讲者备注"
    )
    
    # 元数据
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="额外元数据"
    )

    model_config = ConfigDict(use_enum_values=True)


class TemplateConfig(BaseModel):
    """模板配置
    
    控制模板渲染行为的配置项。
    """
    
    # 尺寸
    width: int = Field(
        default=13333200,  # 16:9 默认宽度 (EMU)
        description="幻灯片宽度 (EMU)"
    )
    height: int = Field(
        default=7500000,   # 16:9 默认高度 (EMU)
        description="幻灯片高度 (EMU)"
    )
    
    # 边距
    margin_left: int = Field(
        default=457200,    # 0.5 inch in EMU
        description="左边距 (EMU)"
    )
    margin_right: int = Field(
        default=457200,
        description="右边距 (EMU)"
    )
    margin_top: int = Field(
        default=457200,
        description="上边距 (EMU)"
    )
    margin_bottom: int = Field(
        default=457200,
        description="下边距 (EMU)"
    )
    
    # 字号 (磅)
    title_font_size: int = Field(
        default=44,
        description="标题字号"
    )
    subtitle_font_size: int = Field(
        default=24,
        description="副标题字号"
    )
    body_font_size: int = Field(
        default=18,
        description="正文字号"
    )
    bullet_font_size: int = Field(
        default=20,
        description="要点字号"
    )
    
    # 行间距
    line_spacing: float = Field(
        default=1.5,
        description="行间距倍数"
    )
    
    # 动画（预留）
    enable_animations: bool = Field(
        default=False,
        description="是否启用动画"
    )


class PresentationSpec(BaseModel):
    """完整演示文稿规格
    
    定义一个完整 PPT 的所有内容和配置。
    """
    
    # 基本信息
    title: str = Field(
        description="演示文稿标题"
    )
    author: Optional[str] = Field(
        default=None,
        description="作者"
    )
    subject: Optional[str] = Field(
        default=None,
        description="主题"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="关键词"
    )
    
    # 幻灯片内容
    slides: List[SlideContent] = Field(
        default_factory=list,
        description="幻灯片列表"
    )
    
    # 品牌配置
    brand: BrandKit = Field(
        default_factory=BrandKit,
        description="品牌配置"
    )
    
    # 模板配置
    template_config: TemplateConfig = Field(
        default_factory=TemplateConfig,
        description="模板配置"
    )
    
    # 元数据
    language: str = Field(
        default="zh-CN",
        description="语言"
    )
    
    def add_slide(self, slide: SlideContent) -> None:
        """添加幻灯片"""
        self.slides.append(slide)
    
    def add_title_slide(
        self,
        title: str,
        subtitle: Optional[str] = None
    ) -> None:
        """快捷方法：添加标题页"""
        self.add_slide(SlideContent(
            type=SlideType.TITLE,
            title=title,
            subtitle=subtitle
        ))
    
    def add_bullet_slide(
        self,
        title: str,
        bullets: List[str]
    ) -> None:
        """快捷方法：添加要点页"""
        self.add_slide(SlideContent(
            type=SlideType.BULLET,
            title=title,
            bullets=bullets
        ))
    
    def add_section_slide(self, title: str) -> None:
        """快捷方法：添加章节页"""
        self.add_slide(SlideContent(
            type=SlideType.SECTION,
            title=title
        ))
