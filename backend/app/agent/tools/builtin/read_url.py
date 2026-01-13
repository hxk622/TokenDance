# -*- coding: utf-8 -*-
"""
Read URL 工具

抓取网页内容并转换为 Markdown 格式
"""
import logging
from typing import Any, Dict
import asyncio
import re

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False

from ..base import BaseTool

logger = logging.getLogger(__name__)


class ReadUrlTool(BaseTool):
    """网页抓取工具
    
    功能：
    - 抓取网页 HTML
    - 清理无用内容（脚本、样式等）
    - 转换为 Markdown 格式
    - 提取主要文本内容
    """
    
    def __init__(self):
        super().__init__(
            name="read_url",
            description=(
                "Fetch and read content from a web page URL. "
                "Converts HTML to clean Markdown text. "
                "Use this tool when you need to read detailed information from a specific web page."
            ),
            parameters_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the web page to fetch and read"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum content length in characters (default: 10000)",
                        "default": 10000,
                        "minimum": 1000,
                        "maximum": 50000
                    }
                },
                "required": ["url"]
            },
            requires_confirmation=False
        )
        
        if not HTTPX_AVAILABLE:
            logger.warning("httpx not installed. URL reading will not work.")
        if not BS4_AVAILABLE:
            logger.warning("beautifulsoup4 not installed. HTML parsing will be limited.")
        if not HTML2TEXT_AVAILABLE:
            logger.warning("html2text not installed. Markdown conversion will be limited.")
    
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """执行网页抓取
        
        Args:
            url: 网页 URL
            max_length: 最大内容长度（默认 10000 字符）
            
        Returns:
            Dict: 抓取结果
                - success: bool
                - url: str
                - title: str
                - content: str (Markdown 格式)
                - length: int
        """
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "error": "httpx not installed. Install with: pip install httpx"
            }
        
        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 10000)
        
        if not url:
            return {
                "success": False,
                "error": "URL parameter is required"
            }
        
        # 验证 URL 格式
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        logger.info(f"Reading URL: {url} (max_length={max_length})")
        
        try:
            # 异步抓取网页
            html_content = await self._fetch_html(url)
            
            # 解析和清理 HTML
            title, clean_text = self._parse_html(html_content)
            
            # 转换为 Markdown
            markdown_content = self._html_to_markdown(clean_text)
            
            # 截断内容
            if len(markdown_content) > max_length:
                markdown_content = markdown_content[:max_length] + "\n\n... (content truncated)"
            
            logger.info(f"Successfully read URL: {url} ({len(markdown_content)} chars)")
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": markdown_content,
                "length": len(markdown_content)
            }
        
        except Exception as e:
            logger.error(f"Failed to read URL {url}: {e}", exc_info=True)
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    async def _fetch_html(self, url: str) -> str:
        """异步抓取网页 HTML
        
        Args:
            url: 网页 URL
            
        Returns:
            str: HTML 内容
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
            )
            response.raise_for_status()
            return response.text
    
    def _parse_html(self, html: str) -> tuple[str, str]:
        """解析和清理 HTML
        
        Args:
            html: 原始 HTML
            
        Returns:
            tuple: (title, clean_text)
        """
        if not BS4_AVAILABLE:
            # 简单的文本提取（无 BeautifulSoup）
            title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            title = title.group(1) if title else "No title"
            
            # 移除脚本和样式
            text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)  # 移除所有标签
            
            return title, text
        
        # 使用 BeautifulSoup 解析
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取标题
        title = soup.title.string if soup.title else "No title"
        
        # 移除无用元素
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            element.decompose()
        
        # 提取主要内容区域
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', class_=re.compile('content|main|article', re.I)) or
            soup.body or
            soup
        )
        
        # 获取清理后的 HTML
        clean_html = str(main_content)
        
        return title.strip(), clean_html
    
    def _html_to_markdown(self, html: str) -> str:
        """转换 HTML 为 Markdown
        
        Args:
            html: HTML 内容
            
        Returns:
            str: Markdown 文本
        """
        if not HTML2TEXT_AVAILABLE:
            # 简单的纯文本提取
            text = re.sub(r'<[^>]+>', '', html)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()
        
        # 使用 html2text 转换
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # 不换行
        
        markdown = h.handle(html)
        
        # 清理多余空行
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        return markdown.strip()
    
    def format_result(self, result: Dict[str, Any]) -> str:
        """格式化网页内容为可读文本
        
        Args:
            result: execute() 返回的结果
            
        Returns:
            str: 格式化的文本
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            url = result.get("url", "")
            return f"❌ Failed to read URL: {url}\nError: {error}"
        
        url = result.get("url", "")
        title = result.get("title", "No title")
        content = result.get("content", "")
        length = result.get("length", 0)
        
        formatted = f"📄 **{title}**\n"
        formatted += f"🔗 {url}\n"
        formatted += f"📏 {length} characters\n\n"
        formatted += "---\n\n"
        formatted += content
        
        return formatted


# 便捷函数
def create_read_url_tool() -> ReadUrlTool:
    """创建 read_url 工具实例
    
    Returns:
        ReadUrlTool: URL 读取工具实例
    """
    return ReadUrlTool()
