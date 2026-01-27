"""
Web Search 工具

支持多搜索源自动降级:
1. Serper (Google 结果, 需 API Key, 最稳定)
2. Brave Search (需 API Key)
3. DuckDuckGo (免费, 无需 API Key)
4. httpx 备选 (解决 SSL 问题)
"""
import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote_plus

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# 导入多源搜索器
try:
    from .search_providers import get_multi_source_searcher
    MULTI_SOURCE_AVAILABLE = True
except ImportError:
    MULTI_SOURCE_AVAILABLE = False

from ..base import BaseTool
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """网页搜索工具

    使用 DuckDuckGo 搜索引擎进行网页搜索。
    免费、无需 API Key、支持中英文。

    功能：
    - 关键词搜索
    - 返回标题、链接、摘要
    - 可配置结果数量

    风险等级：NONE（纯读取操作，无副作用）
    """

    # 工具定义（类属性）
    name = "web_search"
    description = (
        "Search the web for information using DuckDuckGo. "
        "Returns a list of search results with titles, links, and snippets. "
        "Use this tool when you need to find current information, "
        "research a topic, or verify facts from the internet."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string. Be specific and concise."
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5,
                "minimum": 1,
                "maximum": 10
            },
            "region": {
                "type": "string",
                "description": "Region code for search results (e.g., 'cn-zh' for China, 'us-en' for US)",
                "default": "wt-wt"
            }
        },
        "required": ["query"]
    }

    # 风险配置
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_SEARCH]
    requires_confirmation = False

    def __init__(self):
        super().__init__()
        if not DDGS_AVAILABLE:
            logger.warning("duckduckgo-search not installed. Web search will not work.")

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """执行网页搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数（默认 5）
            region: 地区代码（默认 'wt-wt' 全球）

        Returns:
            Dict: 搜索结果
                - success: bool
                - results: List[Dict]
                    - title: str
                    - link: str
                    - snippet: str
                - query: str
                - count: int
        """
        if not DDGS_AVAILABLE:
            return {
                "success": False,
                "error": "duckduckgo-search not installed. Install with: pip install duckduckgo-search",
                "results": []
            }

        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)
        region = kwargs.get("region", "wt-wt")

        if not query:
            return {
                "success": False,
                "error": "Query parameter is required",
                "results": []
            }

        logger.info(f"Searching web: '{query}' (max_results={max_results}, region={region})")

        # 优先使用多源搜索器 (Serper/Brave/DuckDuckGo 自动降级)
        if MULTI_SOURCE_AVAILABLE:
            try:
                searcher = get_multi_source_searcher()
                result = await searcher.search(query, max_results)

                if result.get("success"):
                    logger.info(
                        f"Found {len(result.get('results', []))} results via {result.get('provider')} "
                        f"(fallback: {result.get('fallback_used')})"
                    )
                    return {
                        "success": True,
                        "query": query,
                        "count": len(result.get("results", [])),
                        "results": result.get("results", []),
                        "provider": result.get("provider")
                    }
                else:
                    logger.warning(f"MultiSourceSearcher failed: {result.get('errors')}")
            except Exception as e:
                logger.warning(f"MultiSourceSearcher error: {e}")

        # 备选: 直接使用 DuckDuckGo 或 httpx
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._search_sync,
                query,
                max_results,
                region
            )

            logger.info(f"Found {len(results)} results for query: '{query}'")

            return {
                "success": True,
                "query": query,
                "count": len(results),
                "results": results
            }

        except Exception as e:
            logger.error(f"Web search failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }

    def _search_sync(self, query: str, max_results: int, region: str) -> list:
        """同步搜索方法（在线程池中调用）

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            region: 地区代码

        Returns:
            List[Dict]: 搜索结果列表
        """
        # 尝试使用 DDGS
        if DDGS_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    raw_results = ddgs.text(
                        keywords=query,
                        region=region,
                        safesearch='moderate',
                        max_results=max_results
                    )

                    formatted_results = []
                    for result in raw_results:
                        formatted_results.append({
                            "title": result.get("title", ""),
                            "link": result.get("href", ""),
                            "snippet": result.get("body", "")
                        })

                    return formatted_results

            except Exception as e:
                logger.warning(f"DDGS search failed, trying httpx fallback: {e}")

        # 备选: 使用 httpx 直接请求 DuckDuckGo HTML API
        if HTTPX_AVAILABLE:
            return self._search_with_httpx(query, max_results)

        raise RuntimeError("No search backend available. Install duckduckgo-search or httpx.")

    def _search_with_httpx(self, query: str, max_results: int) -> list:
        """使用 httpx 搜索 DuckDuckGo HTML API

        这是 DDGS 失败时的备选方案，绕过 primp 的 SSL 问题
        """
        try:
            # DuckDuckGo HTML 搜索 URL
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            # 禁用 SSL 验证以解决某些环境的证书问题 (开发环境)
            # 增加超时时间以处理慢速网络
            timeout = httpx.Timeout(60.0, connect=30.0, read=60.0)
            with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()
                html = response.text

            # 解析 HTML 结果
            results = []

            # 匹配搜索结果块
            result_pattern = re.compile(
                r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
                r'.*?<a[^>]+class="result__snippet"[^>]*>([^<]*)</a>',
                re.DOTALL
            )


            # 尝试主模式
            for match in result_pattern.finditer(html):
                if len(results) >= max_results:
                    break
                link, title, snippet = match.groups()
                # 清理 HTML 实体
                title = re.sub(r'<[^>]+>', '', title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippet).strip()
                if link and title:
                    results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet
                    })

            # 如果主模式没有结果，尝试备用模式
            if not results:
                # 更简单的模式: 提取所有链接
                link_pattern = re.compile(
                    r'<a[^>]+class="[^"]*result__url[^"]*"[^>]+href="([^"]+)"[^>]*>',
                    re.IGNORECASE
                )
                title_pattern = re.compile(
                    r'<a[^>]+class="[^"]*result__a[^"]*"[^>]*>([^<]+)</a>',
                    re.IGNORECASE
                )
                snippet_pattern = re.compile(
                    r'<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>([^<]+)</a>',
                    re.IGNORECASE
                )

                links = link_pattern.findall(html)
                titles = title_pattern.findall(html)
                snippets = snippet_pattern.findall(html)

                for i in range(min(len(titles), max_results)):
                    results.append({
                        "title": titles[i] if i < len(titles) else "",
                        "link": links[i] if i < len(links) else "",
                        "snippet": snippets[i] if i < len(snippets) else ""
                    })

            logger.info(f"httpx fallback found {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"httpx search failed: {e}")
            raise

    def format_result(self, result: dict[str, Any]) -> str:
        """格式化搜索结果为可读文本

        Args:
            result: execute() 返回的结果

        Returns:
            str: 格式化的文本
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"❌ Search failed: {error}"

        results = result.get("results", [])
        query = result.get("query", "")
        count = result.get("count", 0)

        if count == 0:
            return f"🔍 No results found for: '{query}'"

        # 格式化每个结果
        formatted = f"🔍 Found {count} results for: '{query}'\n\n"

        for i, item in enumerate(results, 1):
            title = item.get("title", "No title")
            link = item.get("link", "")
            snippet = item.get("snippet", "No snippet")

            formatted += f"{i}. **{title}**\n"
            formatted += f"   {link}\n"
            formatted += f"   {snippet[:200]}{'...' if len(snippet) > 200 else ''}\n\n"

        return formatted.strip()


# 便捷函数
def create_web_search_tool() -> WebSearchTool:
    """创建 web_search 工具实例

    Returns:
        WebSearchTool: 搜索工具实例
    """
    return WebSearchTool()
