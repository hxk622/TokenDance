# -*- coding: utf-8 -*-
"""
WeChat Article Tool - 微信公众号文章提取

功能：
- 提取微信公众号文章内容
- 支持 Markdown/HTML 输出格式
- 使用 mptext.top 免费 API

API: https://down.mptext.top/api/public/v1/download
- 无需 API Key
- 免费使用
- 支持多种输出格式

风险等级：NONE（纯读取操作，无副作用）
"""
import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from ..base import BaseTool
from ..risk import RiskLevel, OperationCategory

logger = logging.getLogger(__name__)

# mptext.top API 配置
MPTEXT_API_URL = "https://down.mptext.top/api/public/v1/download"
DEFAULT_TIMEOUT = 30.0


class WeChatArticleTool(BaseTool):
    """微信公众号文章提取工具

    功能：
    - 提取微信公众号文章内容
    - 支持 Markdown 和 HTML 格式输出
    - 自动验证链接格式

    风险等级：NONE（纯读取操作，无副作用）
    """

    # 类属性配置
    name = "wechat_article"
    description = (
        "Extract content from WeChat Official Account (微信公众号) articles. "
        "Converts article to clean Markdown or HTML format. "
        "Use this tool when you need to read content from WeChat article links (mp.weixin.qq.com). "
        "This tool is specifically designed for WeChat articles and provides better results than generic read_url."
    )
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The WeChat article URL (must be from mp.weixin.qq.com)"
            },
            "format": {
                "type": "string",
                "description": "Output format: 'markdown' (default) or 'html'",
                "enum": ["markdown", "html"],
                "default": "markdown"
            },
            "include_images": {
                "type": "boolean",
                "description": "Whether to include image references in output (default: true)",
                "default": True
            }
        },
        "required": ["url"]
    }

    # 风险配置
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    requires_confirmation = False

    def __init__(self):
        super().__init__()
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not installed. WeChat article extraction will not work.")

    def _validate_wechat_url(self, url: str) -> tuple[bool, str]:
        """验证是否为有效的微信公众号链接

        Args:
            url: 待验证的 URL

        Returns:
            (is_valid, error_message)
        """
        if not url:
            return False, "URL cannot be empty"

        # 添加协议头
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            parsed = urlparse(url)
        except Exception:
            return False, "Invalid URL format"

        # 检查是否为微信公众号域名
        valid_domains = ["mp.weixin.qq.com", "weixin.qq.com"]
        if parsed.netloc not in valid_domains:
            return False, f"Not a WeChat article URL. Expected domain: mp.weixin.qq.com, got: {parsed.netloc}"

        return True, ""

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行微信公众号文章提取

        Args:
            url: 微信公众号文章链接
            format: 输出格式 (markdown/html)
            include_images: 是否包含图片引用

        Returns:
            Dict: 提取结果
                - success: bool
                - url: str
                - title: str
                - content: str
                - author: str (如果有)
                - publish_time: str (如果有)
                - format: str
        """
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "error": "httpx not installed. Install with: pip install httpx"
            }

        url = kwargs.get("url", "")
        output_format = kwargs.get("format", "markdown")
        include_images = kwargs.get("include_images", True)

        # 验证 URL
        is_valid, error_msg = self._validate_wechat_url(url)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "hint": "Please provide a valid WeChat article URL (e.g., https://mp.weixin.qq.com/s/xxx)"
            }

        # 确保 URL 有协议头
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        logger.info(f"Extracting WeChat article: {url} (format={output_format})")

        try:
            # 调用 mptext.top API
            result = await self._fetch_article(url, output_format, include_images)
            return result

        except httpx.TimeoutException:
            logger.error(f"Timeout extracting WeChat article: {url}")
            return {
                "success": False,
                "error": "Request timeout. The article may be too long or the service is slow.",
                "url": url
            }
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error extracting WeChat article: {e}")
            return {
                "success": False,
                "error": f"HTTP error: {e.response.status_code}",
                "url": url
            }
        except Exception as e:
            logger.error(f"Error extracting WeChat article: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to extract article: {str(e)}",
                "url": url
            }

    async def _fetch_article(
        self,
        url: str,
        output_format: str,
        include_images: bool
    ) -> Dict[str, Any]:
        """调用 mptext.top API 获取文章内容

        Args:
            url: 微信文章链接
            output_format: 输出格式
            include_images: 是否包含图片

        Returns:
            提取结果字典
        """
        # 构建请求参数
        # API 文档: https://down.mptext.top/dashboard/api
        params = {
            "url": url,
            "type": output_format,  # markdown 或 html
        }

        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(MPTEXT_API_URL, params=params)
            response.raise_for_status()

            data = response.json()

            # 解析响应
            if data.get("code") != 0 and data.get("code") != 200:
                error_msg = data.get("msg") or data.get("message") or "Unknown error"
                return {
                    "success": False,
                    "error": f"API error: {error_msg}",
                    "url": url
                }

            # 提取内容
            content = data.get("data", {}).get("content") or data.get("content", "")
            title = data.get("data", {}).get("title") or data.get("title", "Untitled")
            author = data.get("data", {}).get("author") or data.get("author", "")
            publish_time = data.get("data", {}).get("publish_time") or data.get("publish_time", "")

            # 如果不包含图片，移除图片标记
            if not include_images and output_format == "markdown":
                content = self._remove_images_from_markdown(content)

            # 计算内容长度
            content_length = len(content)

            logger.info(f"Successfully extracted WeChat article: {title} ({content_length} chars)")

            return {
                "success": True,
                "url": url,
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "content": content,
                "format": output_format,
                "length": content_length
            }

    def _remove_images_from_markdown(self, content: str) -> str:
        """从 Markdown 内容中移除图片引用

        Args:
            content: Markdown 内容

        Returns:
            移除图片后的内容
        """
        # 移除 Markdown 图片语法: ![alt](url)
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)
        # 移除连续空行
        content = re.sub(r'\n{3,}', '\n\n', content)
        return content.strip()


# 全局实例
wechat_article_tool = WeChatArticleTool()
