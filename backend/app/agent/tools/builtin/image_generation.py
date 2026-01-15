"""
Image Generation Tool - AI 图像生成工具

基于 Google Gemini Nano Banana API 实现：
- 文生图 (Text-to-Image)
- 图生图 (Image-to-Image)  
- 图像编辑 (Image Editing)

支持模型：
- gemini-2.5-flash-image (Nano Banana) - 快速生成
- gemini-3-pro-image-preview (Nano Banana Pro) - 高质量生成
"""

import base64
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import BaseTool, ToolResult
from ..risk import RiskLevel, OperationCategory


class GenerateImageTool(BaseTool):
    """文生图/图生图工具
    
    使用 Gemini Nano Banana API 生成图像。
    """
    
    name = "generate_image"
    description = """AI图像生成工具，根据文字描述生成高质量图像。
支持多种风格（写实、动漫、油画等）和尺寸（1:1, 16:9, 9:16等）。
可用于创意设计、营销素材、演示文稿配图、社交媒体内容等场景。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "图像描述（英文效果更佳）。建议格式：[主体] + [动作/姿态] + [场景/背景] + [风格] + [氛围/光线]"
            },
            "style": {
                "type": "string",
                "enum": ["realistic", "anime", "oil_painting", "watercolor", "minimal", "cinematic", "3d_rendered", "paper_cut"],
                "description": "图像风格预设",
                "default": "realistic"
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["1:1", "16:9", "9:16", "4:3", "3:4", "21:9"],
                "description": "宽高比",
                "default": "1:1"
            },
            "resolution": {
                "type": "string",
                "enum": ["1K", "2K", "4K"],
                "description": "分辨率（4K仅Nano Banana Pro支持）",
                "default": "1K"
            },
            "num_images": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4,
                "description": "生成图像数量",
                "default": 1
            },
            "reference_image": {
                "type": "string",
                "description": "参考图像路径（可选，用于图生图）"
            },
            "use_pro_model": {
                "type": "boolean",
                "description": "是否使用 Nano Banana Pro（更高质量但更慢）",
                "default": False
            }
        },
        "required": ["prompt"]
    }
    
    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.CONTENT_GENERATION]
    
    # 风格预设映射
    STYLE_PROMPTS = {
        "realistic": "photorealistic, hyperrealistic, 8K, detailed, professional photography",
        "anime": "anime style, Japanese animation, cel shading, vibrant colors",
        "oil_painting": "oil painting style, impressionist, brush strokes, artistic",
        "watercolor": "watercolor painting, soft edges, flowing colors, artistic",
        "minimal": "minimal, flat design, vector art, clean lines",
        "cinematic": "cinematic, dramatic lighting, movie poster style, epic",
        "3d_rendered": "3D rendered, octane render, realistic lighting, detailed textures",
        "paper_cut": "traditional Chinese paper cut art style, layered paper effect, folk art"
    }
    
    # 分辨率映射
    RESOLUTION_MAP = {
        "1K": {"width": 1024, "height": 1024},  # 基于 aspect_ratio 调整
        "2K": {"width": 2048, "height": 2048},
        "4K": {"width": 4096, "height": 4096}
    }
    
    # 宽高比映射
    ASPECT_RATIOS = {
        "1:1": (1, 1),
        "16:9": (16, 9),
        "9:16": (9, 16),
        "4:3": (4, 3),
        "3:4": (3, 4),
        "21:9": (21, 9)
    }
    
    def __init__(self, output_dir: str = "/tmp/tokendance/images"):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Gemini API Key (从环境变量获取)
        self.api_key = os.getenv("GEMINI_API_KEY", "")
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """增强 Prompt 添加风格词"""
        style_suffix = self.STYLE_PROMPTS.get(style, "")
        enhanced = f"{prompt}, {style_suffix}, high quality, detailed"
        return enhanced
    
    def _calculate_dimensions(self, aspect_ratio: str, resolution: str) -> tuple[int, int]:
        """计算实际尺寸"""
        base_size = self.RESOLUTION_MAP.get(resolution, self.RESOLUTION_MAP["1K"])
        ratio = self.ASPECT_RATIOS.get(aspect_ratio, (1, 1))
        
        # 计算实际尺寸，保持面积大致相同
        base_pixels = base_size["width"] * base_size["height"]
        ratio_product = ratio[0] * ratio[1]
        scale = (base_pixels / ratio_product) ** 0.5
        
        width = int(ratio[0] * scale)
        height = int(ratio[1] * scale)
        
        # 确保是64的倍数（GPU优化）
        width = (width // 64) * 64
        height = (height // 64) * 64
        
        return width, height
    
    async def execute(self, **kwargs) -> str:
        """执行图像生成
        
        Args:
            prompt: 图像描述
            style: 风格预设
            aspect_ratio: 宽高比
            resolution: 分辨率
            num_images: 生成数量
            reference_image: 参考图路径（可选）
            use_pro_model: 是否使用Pro模型
            
        Returns:
            生成结果（包含图像路径）
        """
        prompt = kwargs.get("prompt", "")
        style = kwargs.get("style", "realistic")
        aspect_ratio = kwargs.get("aspect_ratio", "1:1")
        resolution = kwargs.get("resolution", "1K")
        num_images = kwargs.get("num_images", 1)
        reference_image = kwargs.get("reference_image")
        use_pro_model = kwargs.get("use_pro_model", False)
        
        if not prompt:
            return ToolResult(
                success=False,
                error="Prompt is required"
            ).to_text()
        
        if not self.api_key:
            return ToolResult(
                success=False,
                error="GEMINI_API_KEY not configured. Please set the environment variable."
            ).to_text()
        
        # 增强 Prompt
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        # 计算尺寸
        width, height = self._calculate_dimensions(aspect_ratio, resolution)
        
        # 选择模型
        model = "gemini-3-pro-image-preview" if use_pro_model else "gemini-2.5-flash-image"
        
        try:
            # 调用 Gemini API
            generated_images = await self._call_gemini_api(
                model=model,
                prompt=enhanced_prompt,
                width=width,
                height=height,
                num_images=num_images,
                reference_image=reference_image
            )
            
            # 保存图像
            saved_paths = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, image_data in enumerate(generated_images):
                filename = f"generated_{timestamp}_{i+1}.png"
                filepath = self.output_dir / filename
                
                # 解码 base64 并保存
                image_bytes = base64.b64decode(image_data)
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
                
                saved_paths.append(str(filepath))
            
            result = ToolResult(
                success=True,
                data={
                    "images": saved_paths,
                    "prompt": enhanced_prompt,
                    "model": model,
                    "dimensions": f"{width}x{height}",
                    "style": style
                },
                summary=f"Generated {len(saved_paths)} image(s): {', '.join(saved_paths)}"
            )
            
            return result.to_text()
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Image generation failed: {str(e)}"
            ).to_text()
    
    async def _call_gemini_api(
        self,
        model: str,
        prompt: str,
        width: int,
        height: int,
        num_images: int,
        reference_image: Optional[str] = None
    ) -> List[str]:
        """调用 Gemini API 生成图像
        
        Returns:
            List[str]: Base64 编码的图像数据列表
        """
        import httpx
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        # 构建请求内容
        contents = [{"parts": [{"text": prompt}]}]
        
        # 如果有参考图，添加到请求中
        if reference_image and Path(reference_image).exists():
            with open(reference_image, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            contents[0]["parts"].append({
                "inline_data": {
                    "mime_type": "image/png",
                    "data": image_data
                }
            })
        
        # 构建生成配置
        generation_config = {
            "responseModalities": ["TEXT", "IMAGE"],
            "imageConfig": {
                "numberOfImages": num_images
            }
        }
        
        # 如果是 Pro 模型，添加分辨率配置
        if "pro" in model.lower():
            # Nano Banana Pro 支持更高分辨率
            if width >= 2048 or height >= 2048:
                generation_config["imageConfig"]["imageSize"] = "2K"
            if width >= 4096 or height >= 4096:
                generation_config["imageConfig"]["imageSize"] = "4K"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "contents": contents,
                    "generationConfig": generation_config
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Gemini API error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # 提取生成的图像
            images = []
            for candidate in result.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if "inlineData" in part:
                        images.append(part["inlineData"]["data"])
            
            if not images:
                raise Exception("No images generated")
            
            return images


class EditImageTool(BaseTool):
    """图像编辑工具
    
    使用 Gemini Nano Banana API 编辑现有图像。
    """
    
    name = "edit_image"
    description = """AI图像编辑工具，修改现有图像的特定部分。
可以添加/删除元素、修改背景、调整风格等。"""
    
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "要编辑的图像路径"
            },
            "prompt": {
                "type": "string",
                "description": "编辑指令（如：'将背景改为夜景'、'添加红色灯笼'）"
            },
            "preserve_subject": {
                "type": "boolean",
                "description": "是否保持主体不变",
                "default": True
            }
        },
        "required": ["image_path", "prompt"]
    }
    
    risk_level = RiskLevel.LOW
    operation_categories = [OperationCategory.CONTENT_GENERATION]
    
    def __init__(self, output_dir: str = "/tmp/tokendance/images"):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = os.getenv("GEMINI_API_KEY", "")
    
    async def execute(self, **kwargs) -> str:
        """执行图像编辑"""
        image_path = kwargs.get("image_path", "")
        prompt = kwargs.get("prompt", "")
        preserve_subject = kwargs.get("preserve_subject", True)
        
        if not image_path or not Path(image_path).exists():
            return ToolResult(
                success=False,
                error=f"Image not found: {image_path}"
            ).to_text()
        
        if not prompt:
            return ToolResult(
                success=False,
                error="Edit prompt is required"
            ).to_text()
        
        if not self.api_key:
            return ToolResult(
                success=False,
                error="GEMINI_API_KEY not configured"
            ).to_text()
        
        # 构建编辑 Prompt
        edit_prompt = prompt
        if preserve_subject:
            edit_prompt = f"{prompt}. Keep the main subject unchanged."
        
        try:
            import httpx
            
            # 读取原图
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # 确定 MIME 类型
            suffix = Path(image_path).suffix.lower()
            mime_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".webp": "image/webp"
            }.get(suffix, "image/png")
            
            # 调用 API
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"
            
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "x-goog-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "contents": [{
                            "parts": [
                                {"text": edit_prompt},
                                {
                                    "inline_data": {
                                        "mime_type": mime_type,
                                        "data": image_data
                                    }
                                }
                            ]
                        }],
                        "generationConfig": {
                            "responseModalities": ["TEXT", "IMAGE"]
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code}")
                
                result = response.json()
                
                # 提取编辑后的图像
                for candidate in result.get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            # 保存编辑后的图像
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            output_path = self.output_dir / f"edited_{timestamp}.png"
                            
                            edited_data = base64.b64decode(part["inlineData"]["data"])
                            with open(output_path, "wb") as f:
                                f.write(edited_data)
                            
                            return ToolResult(
                                success=True,
                                data={
                                    "original": image_path,
                                    "edited": str(output_path),
                                    "edit_prompt": edit_prompt
                                },
                                summary=f"Image edited successfully: {output_path}"
                            ).to_text()
                
                raise Exception("No edited image returned")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Image editing failed: {str(e)}"
            ).to_text()


def create_image_generation_tools(output_dir: str = "/tmp/tokendance/images") -> List[BaseTool]:
    """创建图像生成工具集
    
    Args:
        output_dir: 图像输出目录
        
    Returns:
        List[BaseTool]: 图像生成工具列表
    """
    return [
        GenerateImageTool(output_dir=output_dir),
        EditImageTool(output_dir=output_dir)
    ]
