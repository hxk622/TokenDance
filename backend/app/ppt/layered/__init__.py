"""
Layered Slide Generation - 分层幻灯片生成

实现 Layered Image-Driven 方案：
- 程序化背景生成（渐变、几何图案、波浪等）
- 装饰元素生成（形状、线条、粒子）
- 图层合成（背景 + 装饰 + 文本）
- 保持文本可编辑

核心组件：
- BackgroundGenerator: 背景生成器
- DecorationGenerator: 装饰元素生成器
- LayerCompositor: 图层合成器
- LayeredSlideGenerator: 分层幻灯片协调器
"""

from .backgrounds import (
    BackgroundGenerator,
    BackgroundStyle,
    GradientConfig,
    GeometricConfig,
    WaveConfig,
    ParticleConfig,
)
from .decorations import (
    DecorationGenerator,
    DecorationStyle,
    DecorationConfig,
    ShapeDecoration,
)
from .compositor import (
    LayerCompositor,
    CompositeSpec,
    CompositePresets,
    LayerSpec,
    TextZone,
)
from .generator import (
    LayeredSlideGenerator,
    LayeredSlideStyle,
    LayeredSlideContent,
)

__all__ = [
    # Backgrounds
    "BackgroundGenerator",
    "BackgroundStyle",
    "GradientConfig",
    "GeometricConfig",
    "WaveConfig",
    "ParticleConfig",
    # Decorations
    "DecorationGenerator",
    "DecorationStyle",
    "DecorationConfig",
    "ShapeDecoration",
    # Compositor
    "LayerCompositor",
    "CompositeSpec",
    "CompositePresets",
    "LayerSpec",
    "TextZone",
    # Generator
    "LayeredSlideGenerator",
    "LayeredSlideStyle",
    "LayeredSlideContent",
]
