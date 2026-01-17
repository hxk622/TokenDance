"""
Web Search 工具

使用 DuckDuckGo 进行网页搜索（免费、无需 API Key）
"""
import asyncio
import logging
from typing import Any

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

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

    # 风险配置
    risk_level = RiskLevel.NONE
    operation_categories = [OperationCategory.WEB_SEARCH]
    requires_confirmation = False

    def __init__(self):
        super().__init__(
            name="web_search",
            description=(
                "Search the web for information using DuckDuckGo. "
                "Returns a list of search results with titles, links, and snippets. "
                "Use this tool when you need to find current information, "
                "research a topic, or verify facts from the internet."
            ),
            parameters_schema={
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
            },
            requires_confirmation=False  # 搜索不需要确认
        )

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

        try:
            # DuckDuckGo 搜索（同步调用，需要在线程池中运行）
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
        try:
            with DDGS() as ddgs:
                # 执行搜索
                raw_results = ddgs.text(
                    keywords=query,
                    region=region,
                    safesearch='moderate',
                    max_results=max_results
                )

                # 格式化结果
                formatted_results = []
                for result in raw_results:
                    formatted_results.append({
                        "title": result.get("title", ""),
                        "link": result.get("href", ""),
                        "snippet": result.get("body", "")
                    })

                return formatted_results

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
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
