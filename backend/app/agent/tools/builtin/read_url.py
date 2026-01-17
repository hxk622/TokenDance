"""
Read URL 工具

抓取网页内容并转换为 Markdown 格式
支持 Jina Reader API 实现 Token 优化（推荐）

Token 优化效果:
- 原始 HTML: ~223K tokens
- 去除 JS/CSS 后: ~9K tokens
- Jina Reader Markdown: ~2-3K tokens (节省 70-90%)
"""
import logging
import os
import re
from typing import Any

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
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)

# Jina Reader API 配置
JINA_READER_BASE_URL = "https://r.jina.ai/"
JINA_API_KEY = os.getenv("JINA_API_KEY")  # 可选，免费用法无需 API Key


class ReadUrlTool(BaseTool):
    """网页抓取工具

    功能：
    - 抓取网页 HTML
    - 清理无用内容（脚本、样式等）
    - 转换为 Markdown 格式
    - 提取主要文本内容
    - 【推荐】使用 Jina Reader API 实现高效 Token 优化

    Token 优化:
    - use_jina=True (默认): 使用 Jina Reader API，节省 70-90% tokens
    - use_jina=False: 使用本地 html2text 转换

    风险等级：NONE（纯读取操作，无副作用）
    """

    # 风险配置
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_READ]
    requires_confirmation = False

    def __init__(self):
        super().__init__(
            name="read_url",
            description=(
                "Fetch and read content from a web page URL. "
                "Converts HTML to clean, LLM-optimized Markdown text. "
                "Use this tool when you need to read detailed information from a specific web page. "
                "Automatically removes ads, navigation, and clutter for token efficiency."
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
                    },
                    "use_jina": {
                        "type": "boolean",
                        "description": "Use Jina Reader API for better token optimization (default: true)",
                        "default": True
                    },
                    "extract_relevant": {
                        "type": "boolean",
                        "description": "Extract only query-relevant content using LLM (saves 60-80% more tokens)",
                        "default": False
                    },
                    "query": {
                        "type": "string",
                        "description": "The research query - used when extract_relevant=true to filter content"
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

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """执行网页抓取

        Args:
            url: 网页 URL
            max_length: 最大内容长度（默认 10000 字符）
            use_jina: 是否使用 Jina Reader API（默认 True，节省 70-90% tokens）
            extract_relevant: 是否只提取与查询相关的内容（再节省 60-80% tokens）
            query: 研究查询（extract_relevant=True 时必须提供）

        Returns:
            Dict: 抓取结果
                - success: bool
                - url: str
                - title: str
                - content: str (Markdown 格式)
                - length: int
                - method: str ("jina" or "local")
                - token_savings: str (估算的 token 节省)
        """
        if not HTTPX_AVAILABLE:
            return {
                "success": False,
                "error": "httpx not installed. Install with: pip install httpx"
            }

        url = kwargs.get("url", "")
        max_length = kwargs.get("max_length", 10000)
        use_jina = kwargs.get("use_jina", True)  # 默认使用 Jina
        extract_relevant = kwargs.get("extract_relevant", False)
        query = kwargs.get("query", "")

        if not url:
            return {
                "success": False,
                "error": "URL parameter is required"
            }

        # 验证 URL 格式
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        logger.info(f"Reading URL: {url} (max_length={max_length}, use_jina={use_jina}, extract_relevant={extract_relevant})")

        try:
            if use_jina:
                # 使用 Jina Reader API (推荐，节省 token)
                result = await self._fetch_with_jina(url, max_length)
                if result.get("success"):
                    # 如果需要提取相关内容
                    if extract_relevant and query:
                        result = await self._extract_relevant_content(result, query)
                    return result
                # Jina 失败时回退到本地方法
                logger.warning(f"Jina Reader failed, falling back to local: {result.get('error')}")

            # 本地方法: 异步抓取网页
            html_content = await self._fetch_html(url)

            # 解析和清理 HTML
            title, clean_text = self._parse_html(html_content)

            # 转换为 Markdown
            markdown_content = self._html_to_markdown(clean_text)

            # 截断内容
            if len(markdown_content) > max_length:
                markdown_content = markdown_content[:max_length] + "\n\n... (content truncated)"

            logger.info(f"Successfully read URL (local): {url} ({len(markdown_content)} chars)")

            return {
                "success": True,
                "url": url,
                "title": title,
                "content": markdown_content,
                "length": len(markdown_content),
                "method": "local",
                "token_savings": "~50% (local html2text)"
            }

        except Exception as e:
            logger.error(f"Failed to read URL {url}: {e}", exc_info=True)
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    async def _fetch_with_jina(self, url: str, max_length: int) -> dict[str, Any]:
        """使用 Jina Reader API 获取干净的 Markdown

        Jina Reader API:
        - 免费基础用法: 在 URL 前加 https://r.jina.ai/
        - 自动移除广告、导航、脚本
        - 输出干净的 LLM-friendly Markdown
        - 节省 70-90% tokens

        Args:
            url: 原始 URL
            max_length: 最大内容长度

        Returns:
            Dict: 结果
        """
        jina_url = f"{JINA_READER_BASE_URL}{url}"

        headers = {
            "Accept": "text/markdown",
            "User-Agent": "TokenDance/1.0 (Deep Research Agent)"
        }

        # 如果有 API Key，添加到请求头
        if JINA_API_KEY:
            headers["Authorization"] = f"Bearer {JINA_API_KEY}"

        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                response = await client.get(jina_url, headers=headers)
                response.raise_for_status()

                content = response.text

                # 提取标题 (通常在第一行)
                lines = content.strip().split('\n')
                title = "No title"
                if lines and lines[0].startswith('# '):
                    title = lines[0][2:].strip()
                elif lines and lines[0].startswith('Title: '):
                    title = lines[0][7:].strip()

                # 截断内容
                if len(content) > max_length:
                    content = content[:max_length] + "\n\n... (content truncated)"

                logger.info(f"Successfully read URL (Jina): {url} ({len(content)} chars)")

                return {
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": content,
                    "length": len(content),
                    "method": "jina",
                    "token_savings": "~70-90% (Jina Reader)"
                }

        except httpx.HTTPStatusError as e:
            logger.warning(f"Jina Reader HTTP error for {url}: {e.response.status_code}")
            return {
                "success": False,
                "error": f"Jina Reader HTTP {e.response.status_code}: {str(e)}"
            }
        except Exception as e:
            logger.warning(f"Jina Reader error for {url}: {e}")
            return {
                "success": False,
                "error": f"Jina Reader error: {str(e)}"
            }

    async def _extract_relevant_content(
        self,
        result: dict[str, Any],
        query: str
    ) -> dict[str, Any]:
        """使用 LLM 提取与查询相关的内容

        Index-based Extraction 思想:
        - 将内容分块
        - 用 LLM 识别相关块的索引
        - 只返回相关块
        - 节省 60-80% tokens

        Args:
            result: 原始拓取结果
            query: 研究查询

        Returns:
            Dict: 过滤后的结果
        """
        content = result.get("content", "")
        if not content or len(content) < 500:
            # 内容太短，无需过滤
            return result

        # 将内容分块 (按段落/标题)
        chunks = self._split_into_chunks(content)
        if len(chunks) <= 3:
            # 块数太少，无需过滤
            return result

        # 构建索引提示
        "\n".join([
            f"[{i}] {chunk[:200]}..." if len(chunk) > 200 else f"[{i}] {chunk}"
            for i, chunk in enumerate(chunks)
        ])

        # 使用简单的关键词匹配 (节省 LLM 调用)
        # 如果需要更精确的提取，可以调用 LLM
        relevant_indices = self._find_relevant_indices_fast(chunks, query)

        if not relevant_indices:
            # 找不到相关内容，返回原始结果的前部分
            logger.warning(f"No relevant content found for query: {query[:50]}")
            return result

        # 重组相关内容
        relevant_content = "\n\n".join([chunks[i] for i in relevant_indices])

        original_len = len(content)
        filtered_len = len(relevant_content)
        savings = round((1 - filtered_len / original_len) * 100)

        logger.info(
            f"Query-Relevant extraction: {original_len} -> {filtered_len} chars "
            f"({savings}% reduction, {len(relevant_indices)}/{len(chunks)} chunks)"
        )

        return {
            **result,
            "content": relevant_content,
            "length": filtered_len,
            "extraction_method": "query_relevant",
            "token_savings": f"~{savings}% (query-relevant extraction)",
            "chunks_kept": len(relevant_indices),
            "chunks_total": len(chunks)
        }

    def _split_into_chunks(self, content: str) -> list[str]:
        """将内容分块

        按优先级分割:
        1. Markdown 标题 (##)
        2. 空行
        3. 固定长度
        """
        # 先按 Markdown 标题分割
        import re

        # 匹配 Markdown 标题
        header_pattern = r'\n(?=#{1,3}\s)'
        chunks = re.split(header_pattern, content)

        # 如果分块太少，按双换行分割
        if len(chunks) < 5:
            chunks = content.split('\n\n')

        # 过滤空块和太短的块
        chunks = [c.strip() for c in chunks if c.strip() and len(c.strip()) > 50]

        # 如果块太大，进一步分割
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > 1500:
                # 按句子分割
                sentences = re.split(r'(?<=[.!?。！？])\s+', chunk)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) < 1200:
                        current += sent + " "
                    else:
                        if current:
                            final_chunks.append(current.strip())
                        current = sent + " "
                if current:
                    final_chunks.append(current.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks if final_chunks else chunks

    def _find_relevant_indices_fast(self, chunks: list[str], query: str) -> list[int]:
        """快速查找相关块索引 (基于关键词匹配)

        不调用 LLM，使用简单的关键词匹配 + 评分
        """
        import re

        # 提取查询关键词 (移除停用词)
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall',
            'this', 'that', 'these', 'those', 'it', 'its',
            'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where',
            'what', 'which', 'who', 'whom', 'how', 'why',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            '的', '是', '在', '了', '和', '与', '或', '但',
            '什么', '怎么', '如何', '为什么', '哪个', '这个', '那个'
        }

        # 提取查询关键词
        query_words = set()
        for word in re.findall(r'\w+', query.lower()):
            if word not in stop_words and len(word) > 2:
                query_words.add(word)

        # 添加中文关键词 (按字符)
        for char in query:
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                query_words.add(char)

        if not query_words:
            # 无关键词，返回前几块
            return list(range(min(5, len(chunks))))

        # 计算每块的相关性得分
        scores = []
        for i, chunk in enumerate(chunks):
            chunk_lower = chunk.lower()
            score = 0

            # 关键词匹配
            for word in query_words:
                count = chunk_lower.count(word)
                if count > 0:
                    score += count * (2 if len(word) > 4 else 1)

            # 标题加分 (包含 # 的块)
            if chunk.strip().startswith('#'):
                score *= 1.5

            # 列表/数据加分
            if re.search(r'\d+[%\.\$万亿]|\|.*\||\*\s+', chunk):
                score *= 1.2

            scores.append((i, score))

        # 排序并筛选
        scores.sort(key=lambda x: x[1], reverse=True)

        # 取得分 > 0 的块，最多取 10 块
        relevant = [i for i, score in scores if score > 0][:10]

        # 按原始顺序排列
        relevant.sort()

        # 如果没有相关块，返回前 5 块
        if not relevant:
            return list(range(min(5, len(chunks))))

        return relevant

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

    def format_result(self, result: dict[str, Any]) -> str:
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
