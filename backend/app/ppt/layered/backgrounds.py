"""
Background Generator - 程序化背景生成

支持的背景类型：
- Gradient: 线性/径向渐变
- Geometric: 几何图案（圆形、六边形、网格）
- Wave: 波浪/曲线
- Mesh: 网格渐变
- Abstract: 抽象图形组合
"""

import io
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class BackgroundStyle(str, Enum):
    """背景样式枚举"""
    
    # 渐变类
    LINEAR_GRADIENT = "linear_gradient"
    RADIAL_GRADIENT = "radial_gradient"
    DIAGONAL_GRADIENT = "diagonal_gradient"
    MESH_GRADIENT = "mesh_gradient"
    
    # 几何类
    CIRCLES = "circles"
    HEXAGONS = "hexagons"
    GRID = "grid"
    DOTS = "dots"
    
    # 曲线类
    WAVE = "wave"
    BLOB = "blob"
    
    # 抽象类
    ABSTRACT_SHAPES = "abstract_shapes"
    PARTICLES = "particles"
    
    # 纯色
    SOLID = "solid"


@dataclass
class GradientConfig:
    """渐变配置"""
    
    colors: List[str] = field(default_factory=lambda: ["#1a1a2e", "#4a90e2"])
    angle: float = 45.0  # 渐变角度（线性渐变用）
    center: Tuple[float, float] = (0.5, 0.5)  # 中心点（径向渐变用）
    
    def get_color_stops(self) -> List[Tuple[float, Tuple[int, int, int]]]:
        """获取颜色停止点"""
        stops = []
        n = len(self.colors)
        for i, color in enumerate(self.colors):
            pos = i / (n - 1) if n > 1 else 0
            rgb = hex_to_rgb(color)
            stops.append((pos, rgb))
        return stops


@dataclass
class GeometricConfig:
    """几何图案配置"""
    
    primary_color: str = "#4a90e2"
    secondary_color: str = "#1a1a2e"
    size: int = 50  # 基础图形大小
    opacity: float = 0.3
    spacing: float = 1.2  # 间距倍数
    rotation: float = 0.0
    randomize: bool = True  # 是否随机化


@dataclass
class WaveConfig:
    """波浪配置"""
    
    colors: List[str] = field(default_factory=lambda: ["#4a90e2", "#60a5fa"])
    amplitude: float = 50.0  # 振幅
    frequency: float = 2.0  # 频率
    layers: int = 3  # 波浪层数
    opacity: float = 0.5


@dataclass
class ParticleConfig:
    """粒子配置"""
    
    colors: List[str] = field(default_factory=lambda: ["#4a90e2", "#60a5fa", "#93c5fd"])
    count: int = 50
    min_size: int = 5
    max_size: int = 30
    opacity_range: Tuple[float, float] = (0.1, 0.5)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Hex 转 RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """RGB 转 Hex"""
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def interpolate_color(
    color1: Tuple[int, int, int],
    color2: Tuple[int, int, int],
    t: float
) -> Tuple[int, int, int]:
    """颜色插值"""
    return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))


class BackgroundGenerator:
    """背景生成器
    
    生成各种程序化背景图像。
    
    使用示例：
        generator = BackgroundGenerator(1920, 1080)
        
        # 渐变背景
        bg = generator.generate_gradient(
            GradientConfig(colors=["#1a1a2e", "#4a90e2"])
        )
        
        # 几何背景
        bg = generator.generate_geometric(
            BackgroundStyle.CIRCLES,
            GeometricConfig()
        )
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """初始化
        
        Args:
            width: 图像宽度
            height: 图像高度
        """
        self.width = width
        self.height = height
    
    def generate(
        self,
        style: BackgroundStyle,
        base_color: str = "#1a1a2e",
        accent_color: str = "#4a90e2",
        **kwargs
    ) -> Image.Image:
        """生成背景
        
        Args:
            style: 背景样式
            base_color: 基础颜色
            accent_color: 强调色
            **kwargs: 额外配置
            
        Returns:
            Image.Image: 生成的背景图像
        """
        if style == BackgroundStyle.LINEAR_GRADIENT:
            config = GradientConfig(colors=[base_color, accent_color], angle=kwargs.get("angle", 45))
            return self.generate_linear_gradient(config)
        
        elif style == BackgroundStyle.RADIAL_GRADIENT:
            config = GradientConfig(colors=[accent_color, base_color])
            return self.generate_radial_gradient(config)
        
        elif style == BackgroundStyle.DIAGONAL_GRADIENT:
            config = GradientConfig(colors=[base_color, accent_color], angle=135)
            return self.generate_linear_gradient(config)
        
        elif style == BackgroundStyle.MESH_GRADIENT:
            return self.generate_mesh_gradient([base_color, accent_color])
        
        elif style == BackgroundStyle.CIRCLES:
            config = GeometricConfig(primary_color=accent_color, secondary_color=base_color)
            return self.generate_circles(config)
        
        elif style == BackgroundStyle.HEXAGONS:
            config = GeometricConfig(primary_color=accent_color, secondary_color=base_color)
            return self.generate_hexagons(config)
        
        elif style == BackgroundStyle.GRID:
            config = GeometricConfig(primary_color=accent_color, secondary_color=base_color)
            return self.generate_grid(config)
        
        elif style == BackgroundStyle.DOTS:
            config = GeometricConfig(primary_color=accent_color, secondary_color=base_color)
            return self.generate_dots(config)
        
        elif style == BackgroundStyle.WAVE:
            config = WaveConfig(colors=[accent_color, base_color])
            return self.generate_wave(config, base_color)
        
        elif style == BackgroundStyle.BLOB:
            return self.generate_blob([base_color, accent_color])
        
        elif style == BackgroundStyle.ABSTRACT_SHAPES:
            return self.generate_abstract_shapes([base_color, accent_color])
        
        elif style == BackgroundStyle.PARTICLES:
            config = ParticleConfig(colors=[accent_color])
            return self.generate_particles(config, base_color)
        
        else:  # SOLID
            return self.generate_solid(base_color)
    
    def generate_solid(self, color: str) -> Image.Image:
        """生成纯色背景"""
        return Image.new("RGB", (self.width, self.height), hex_to_rgb(color))
    
    def generate_linear_gradient(self, config: GradientConfig) -> Image.Image:
        """生成线性渐变背景"""
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        stops = config.get_color_stops()
        angle_rad = math.radians(config.angle)
        
        # 计算渐变方向
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # 计算渐变长度
        diag = math.sqrt(self.width ** 2 + self.height ** 2)
        
        for y in range(self.height):
            for x in range(self.width):
                # 计算当前点在渐变方向上的位置
                px = (x - self.width / 2) * cos_a + (y - self.height / 2) * sin_a
                t = (px / diag) + 0.5
                t = max(0, min(1, t))
                
                # 找到对应的颜色
                color = self._get_gradient_color(stops, t)
                draw.point((x, y), fill=color)
        
        return img
    
    def generate_radial_gradient(self, config: GradientConfig) -> Image.Image:
        """生成径向渐变背景"""
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        stops = config.get_color_stops()
        cx = self.width * config.center[0]
        cy = self.height * config.center[1]
        max_dist = math.sqrt((self.width / 2) ** 2 + (self.height / 2) ** 2)
        
        for y in range(self.height):
            for x in range(self.width):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                t = min(1, dist / max_dist)
                color = self._get_gradient_color(stops, t)
                draw.point((x, y), fill=color)
        
        return img
    
    def generate_mesh_gradient(self, colors: List[str]) -> Image.Image:
        """生成网格渐变背景（简化版）"""
        img = Image.new("RGB", (self.width, self.height))
        draw = ImageDraw.Draw(img)
        
        # 创建 4 个角的颜色点
        corners = [
            (0, 0, hex_to_rgb(colors[0])),
            (self.width, 0, hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])),
            (0, self.height, hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])),
            (self.width, self.height, hex_to_rgb(colors[0])),
        ]
        
        for y in range(self.height):
            for x in range(self.width):
                # 双线性插值
                tx = x / self.width
                ty = y / self.height
                
                top = interpolate_color(corners[0][2], corners[1][2], tx)
                bottom = interpolate_color(corners[2][2], corners[3][2], tx)
                color = interpolate_color(top, bottom, ty)
                
                draw.point((x, y), fill=color)
        
        return img
    
    def generate_circles(self, config: GeometricConfig) -> Image.Image:
        """生成圆形图案背景"""
        base = self.generate_solid(config.secondary_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        color_rgb = hex_to_rgb(config.primary_color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)
        
        spacing = int(config.size * config.spacing)
        
        for y in range(-config.size, self.height + config.size, spacing):
            for x in range(-config.size, self.width + config.size, spacing):
                offset_x = 0
                offset_y = 0
                size = config.size
                
                if config.randomize:
                    offset_x = random.randint(-10, 10)
                    offset_y = random.randint(-10, 10)
                    size = config.size + random.randint(-5, 5)
                
                cx = x + offset_x
                cy = y + offset_y
                
                draw.ellipse(
                    [cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2],
                    fill=color
                )
        
        return base.convert("RGB")
    
    def generate_hexagons(self, config: GeometricConfig) -> Image.Image:
        """生成六边形图案背景"""
        base = self.generate_solid(config.secondary_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        color_rgb = hex_to_rgb(config.primary_color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)
        
        size = config.size
        h_spacing = size * 1.5
        v_spacing = size * math.sqrt(3)
        
        row = 0
        for y in range(-size, self.height + size, int(v_spacing)):
            offset = (row % 2) * h_spacing / 2
            for x in range(-size, self.width + size, int(h_spacing)):
                cx = x + offset
                cy = y
                
                # 绘制六边形
                points = []
                for i in range(6):
                    angle = math.pi / 3 * i + math.pi / 6
                    px = cx + size * math.cos(angle)
                    py = cy + size * math.sin(angle)
                    points.append((px, py))
                
                draw.polygon(points, outline=color)
            row += 1
        
        return base.convert("RGB")
    
    def generate_grid(self, config: GeometricConfig) -> Image.Image:
        """生成网格背景"""
        base = self.generate_solid(config.secondary_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        color_rgb = hex_to_rgb(config.primary_color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)
        
        spacing = config.size
        
        # 垂直线
        for x in range(0, self.width, spacing):
            draw.line([(x, 0), (x, self.height)], fill=color, width=1)
        
        # 水平线
        for y in range(0, self.height, spacing):
            draw.line([(0, y), (self.width, y)], fill=color, width=1)
        
        return base.convert("RGB")
    
    def generate_dots(self, config: GeometricConfig) -> Image.Image:
        """生成点阵背景"""
        base = self.generate_solid(config.secondary_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        color_rgb = hex_to_rgb(config.primary_color)
        alpha = int(config.opacity * 255)
        color = (*color_rgb, alpha)
        
        spacing = int(config.size * config.spacing)
        dot_size = max(2, config.size // 10)
        
        for y in range(0, self.height, spacing):
            for x in range(0, self.width, spacing):
                draw.ellipse(
                    [x - dot_size, y - dot_size, x + dot_size, y + dot_size],
                    fill=color
                )
        
        return base.convert("RGB")
    
    def generate_wave(self, config: WaveConfig, base_color: str) -> Image.Image:
        """生成波浪背景"""
        base = self.generate_solid(base_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        for layer in range(config.layers):
            color_idx = layer % len(config.colors)
            color_rgb = hex_to_rgb(config.colors[color_idx])
            alpha = int(config.opacity * 255 * (1 - layer * 0.2))
            color = (*color_rgb, alpha)
            
            # 绘制波浪
            points = []
            y_offset = self.height * (0.6 + layer * 0.1)
            amplitude = config.amplitude * (1 - layer * 0.2)
            frequency = config.frequency + layer * 0.5
            
            for x in range(self.width + 1):
                y = y_offset + amplitude * math.sin(
                    2 * math.pi * frequency * x / self.width + layer
                )
                points.append((x, y))
            
            # 闭合路径
            points.append((self.width, self.height))
            points.append((0, self.height))
            
            draw.polygon(points, fill=color)
        
        return base.convert("RGB")
    
    def generate_blob(self, colors: List[str]) -> Image.Image:
        """生成 Blob 形状背景"""
        base = self.generate_solid(colors[0])
        draw = ImageDraw.Draw(base, "RGBA")
        
        accent = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])
        
        # 绘制多个 blob
        for _ in range(3):
            cx = random.randint(0, self.width)
            cy = random.randint(0, self.height)
            size = random.randint(200, 500)
            alpha = random.randint(30, 80)
            
            # 创建不规则圆形
            points = []
            num_points = 8
            for i in range(num_points):
                angle = 2 * math.pi * i / num_points
                r = size + random.randint(-50, 50)
                px = cx + r * math.cos(angle)
                py = cy + r * math.sin(angle)
                points.append((px, py))
            
            draw.polygon(points, fill=(*accent, alpha))
        
        # 添加模糊效果
        base = base.filter(ImageFilter.GaussianBlur(radius=50))
        
        return base.convert("RGB")
    
    def generate_abstract_shapes(self, colors: List[str]) -> Image.Image:
        """生成抽象形状背景"""
        base = self.generate_solid(colors[0])
        draw = ImageDraw.Draw(base, "RGBA")
        
        accent = hex_to_rgb(colors[1] if len(colors) > 1 else colors[0])
        
        # 添加各种形状
        for _ in range(10):
            shape_type = random.choice(["circle", "rectangle", "line"])
            alpha = random.randint(20, 60)
            
            if shape_type == "circle":
                cx = random.randint(0, self.width)
                cy = random.randint(0, self.height)
                r = random.randint(50, 200)
                draw.ellipse(
                    [cx - r, cy - r, cx + r, cy + r],
                    fill=(*accent, alpha)
                )
            elif shape_type == "rectangle":
                x1 = random.randint(0, self.width)
                y1 = random.randint(0, self.height)
                x2 = x1 + random.randint(100, 400)
                y2 = y1 + random.randint(100, 400)
                draw.rectangle([x1, y1, x2, y2], fill=(*accent, alpha))
            else:
                x1 = random.randint(0, self.width)
                y1 = random.randint(0, self.height)
                x2 = random.randint(0, self.width)
                y2 = random.randint(0, self.height)
                draw.line([(x1, y1), (x2, y2)], fill=(*accent, alpha), width=5)
        
        return base.convert("RGB")
    
    def generate_particles(self, config: ParticleConfig, base_color: str) -> Image.Image:
        """生成粒子效果背景"""
        base = self.generate_solid(base_color)
        draw = ImageDraw.Draw(base, "RGBA")
        
        for _ in range(config.count):
            color = random.choice(config.colors)
            color_rgb = hex_to_rgb(color)
            opacity = random.uniform(*config.opacity_range)
            alpha = int(opacity * 255)
            
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(config.min_size, config.max_size)
            
            draw.ellipse(
                [x - size, y - size, x + size, y + size],
                fill=(*color_rgb, alpha)
            )
        
        # 轻微模糊
        base = base.filter(ImageFilter.GaussianBlur(radius=2))
        
        return base.convert("RGB")
    
    def _get_gradient_color(
        self,
        stops: List[Tuple[float, Tuple[int, int, int]]],
        t: float
    ) -> Tuple[int, int, int]:
        """获取渐变位置的颜色"""
        if t <= stops[0][0]:
            return stops[0][1]
        if t >= stops[-1][0]:
            return stops[-1][1]
        
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                local_t = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                return interpolate_color(stops[i][1], stops[i + 1][1], local_t)
        
        return stops[-1][1]
    
    def save(self, image: Image.Image, path: Union[str, Path]) -> str:
        """保存背景图像
        
        Args:
            image: 图像
            path: 保存路径
            
        Returns:
            str: 保存路径
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path), quality=95)
        return str(path)
    
    def to_bytes(self, image: Image.Image, format: str = "PNG") -> bytes:
        """将图像转换为字节
        
        Args:
            image: 图像
            format: 格式（PNG/JPEG）
            
        Returns:
            bytes: 图像字节数据
        """
        buffer = io.BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
