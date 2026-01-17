#!/usr/bin/env python3
"""
图像生成 Skill 的 L3 执行脚本

负责：
1. 解析用户描述，优化 Prompt
2. 调用图像生成 API（支持多种后端）
3. 处理生成结果
4. 返回图像 URL 或 Base64
"""

import json
import logging
import os
import sys
import uuid
from typing import Any

# 配置日志输出到 stderr（不污染 stdout）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


# 支持的图像生成后端
SUPPORTED_BACKENDS = {
    "openai": "DALL-E 3",
    "stability": "Stable Diffusion",
    "midjourney": "Midjourney (via API)",
    "replicate": "Replicate Models",
}

# 默认图像参数
DEFAULT_CONFIG = {
    "size": "1024x1024",
    "quality": "standard",
    "style": "vivid",
    "n": 1,
}


def check_dependencies() -> tuple[bool, str | None]:
    """检查脚本依赖"""
    missing = []
    try:
        import httpx  # noqa: F401
    except ImportError:
        missing.append("httpx")
    
    if missing:
        return False, f"Missing dependencies: {', '.join(missing)}"
    return True, None


def optimize_prompt(
    user_prompt: str,
    style: str | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """优化用户 Prompt
    
    Args:
        user_prompt: 用户原始描述
        style: 风格偏好
        context: 上下文信息
        
    Returns:
        优化后的 Prompt
    """
    # TODO: 使用 LLM 优化 Prompt
    # 目前做基本的增强
    prompt_parts = [user_prompt]
    
    # 添加风格修饰
    if style:
        style_modifiers = {
            "realistic": "photorealistic, highly detailed, 8k resolution",
            "artistic": "artistic, painterly style, vibrant colors",
            "minimal": "minimalist design, clean lines, simple composition",
            "vintage": "vintage aesthetic, retro style, film grain",
            "futuristic": "futuristic, sci-fi, cyberpunk aesthetic",
            "cartoon": "cartoon style, animated, colorful",
        }
        if style.lower() in style_modifiers:
            prompt_parts.append(style_modifiers[style.lower()])
    
    # 添加质量修饰
    prompt_parts.append("high quality, professional")
    
    optimized = ", ".join(prompt_parts)
    logger.info(f"Optimized prompt: {optimized[:100]}...")
    return optimized


def generate_with_openai(
    prompt: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """使用 OpenAI DALL-E 生成图像
    
    Args:
        prompt: 优化后的 Prompt
        config: 生成配置
        
    Returns:
        生成结果
    """
    # TODO: 实际调用 OpenAI API
    # 需要 OPENAI_API_KEY 环境变量
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "OPENAI_API_KEY not configured",
        }
    
    # 模拟返回结果（实际实现时替换）
    image_id = str(uuid.uuid4())[:8]
    return {
        "success": True,
        "images": [
            {
                "id": image_id,
                "url": f"https://example.com/generated/{image_id}.png",
                "prompt": prompt,
                "size": config.get("size", "1024x1024"),
                "backend": "openai",
            }
        ],
        "revised_prompt": prompt,
    }


def generate_with_stability(
    prompt: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """使用 Stability AI 生成图像
    
    Args:
        prompt: 优化后的 Prompt
        config: 生成配置
        
    Returns:
        生成结果
    """
    # TODO: 实际调用 Stability API
    api_key = os.environ.get("STABILITY_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "STABILITY_API_KEY not configured",
        }
    
    image_id = str(uuid.uuid4())[:8]
    return {
        "success": True,
        "images": [
            {
                "id": image_id,
                "url": f"https://example.com/stability/{image_id}.png",
                "prompt": prompt,
                "size": config.get("size", "1024x1024"),
                "backend": "stability",
            }
        ],
    }


def generate_image(
    prompt: str,
    backend: str = "openai",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """生成图像
    
    Args:
        prompt: 优化后的 Prompt
        backend: 生成后端
        config: 生成配置
        
    Returns:
        生成结果
    """
    config = {**DEFAULT_CONFIG, **(config or {})}
    
    logger.info(f"Generating image with {backend}, config: {config}")
    
    if backend == "openai":
        return generate_with_openai(prompt, config)
    elif backend == "stability":
        return generate_with_stability(prompt, config)
    else:
        return {
            "success": False,
            "error": f"Unsupported backend: {backend}. Supported: {list(SUPPORTED_BACKENDS.keys())}",
        }


def execute_image_generation(
    query: str,
    context: dict[str, Any],
    parameters: dict[str, Any],
) -> dict[str, Any]:
    """执行图像生成
    
    Args:
        query: 用户描述
        context: 执行上下文
        parameters: 额外参数
        
    Returns:
        生成结果
    """
    logger.info(f"Starting image generation for: {query[:50]}...")
    
    # 1. 提取参数
    style = parameters.get("style")
    backend = parameters.get("backend", "openai")
    size = parameters.get("size", "1024x1024")
    quality = parameters.get("quality", "standard")
    n = parameters.get("n", 1)
    
    # 2. 优化 Prompt
    optimized_prompt = optimize_prompt(query, style, context)
    
    # 3. 生成配置
    config = {
        "size": size,
        "quality": quality,
        "n": n,
    }
    
    # 4. 执行生成
    result = generate_image(optimized_prompt, backend, config)
    
    if not result.get("success"):
        return {
            "success": False,
            "error": result.get("error", "Generation failed"),
            "original_prompt": query,
            "optimized_prompt": optimized_prompt,
        }
    
    # 5. 构建结果
    return {
        "success": True,
        "original_prompt": query,
        "optimized_prompt": optimized_prompt,
        "images": result.get("images", []),
        "backend": backend,
        "config": config,
    }


def main(input_data: dict[str, Any]) -> dict[str, Any]:
    """主函数
    
    Args:
        input_data: 从 stdin 接收的 JSON 数据
        
    Returns:
        执行结果 JSON
    """
    # 检查依赖
    ok, error = check_dependencies()
    if not ok:
        return {
            "status": "failed",
            "error": error,
            "tokens_used": 0,
        }
    
    try:
        query = input_data.get("query", "")
        context = input_data.get("context", {})
        parameters = input_data.get("parameters", {})
        
        if not query:
            return {
                "status": "failed",
                "error": "Query (image description) is required",
                "tokens_used": 0,
            }
        
        # 执行图像生成
        result = execute_image_generation(query, context, parameters)
        
        if not result.get("success"):
            return {
                "status": "failed",
                "error": result.get("error", "Image generation failed"),
                "data": {
                    "original_prompt": result.get("original_prompt"),
                    "optimized_prompt": result.get("optimized_prompt"),
                },
                "tokens_used": 100,  # Prompt 优化消耗的 Token
            }
        
        return {
            "status": "success",
            "data": {
                "original_prompt": result["original_prompt"],
                "optimized_prompt": result["optimized_prompt"],
                "images": result["images"],
                "backend": result["backend"],
                "generation_config": result["config"],
            },
            "tokens_used": 500,  # 预估 Token 消耗（Prompt 优化 + API 调用）
        }
    
    except Exception as e:
        logger.exception("Image generation failed")
        return {
            "status": "failed",
            "error": str(e),
            "tokens_used": 0,
        }


if __name__ == "__main__":
    # 从 stdin 读取输入
    input_json = sys.stdin.read()
    input_data = json.loads(input_json)
    
    # 执行
    result = main(input_data)
    
    # 输出结果到 stdout
    print(json.dumps(result, ensure_ascii=False, indent=2))
