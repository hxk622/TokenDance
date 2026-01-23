"""
WeChat Search Tool - 微信公众号文章搜索

功能：
- 使用 Serper (Google) 搜索微信公众号文章
- 自动添加 site:mp.weixin.qq.com 过滤
- 支持与 wechat_article 工具联动提取文章内容

使用场景：
- 用户想搜索某个话题的微信公众号文章
- 用户想找特定公众号的历史文章
- 深度研究时需要微信生态内的信息

注意事项：
- 依赖 Serper API Key (SERPER_API_KEY)
- Google 对微信文章的收录有延迟，新文章可能搜不到
- 小公众号的文章收录率较低

风险等级：NONE（纯读取操作，无副作用）
"""
import logging
from typing import Any

from ..base import BaseTool
from ..risk import OperationCategory, RiskLevel

logger = logging.getLogger(__name__)


class WeChatSearchTool(BaseTool):
    """微信公众号文章搜索工具

    使用 Google (via Serper) 搜索微信公众号文章，
    自动添加 site:mp.weixin.qq.com 限定。

    特点：
    - 复用现有的 web_search 基础设施
    - 自动过滤非微信结果
    - 返回标准化的搜索结果

    使用示例：
    - 搜索 AI Agent 相关文章: query="AI Agent"
    - 搜索特定公众号文章: query="公众号名称 关键词"
    - 搜索特定时间范围: query="关键词 2024" (借助 Google 时间识别)

    风险等级：NONE（纯读取操作，无副作用）
    """

    # 工具定义
    name = "wechat_search"
    description = (
        "Search for WeChat Official Account (微信公众号) articles by keywords. "
        "Returns a list of article titles and links from mp.weixin.qq.com. "
        "Use this tool when you need to find WeChat articles about specific topics, "
        "research opinions from Chinese content creators, or gather information "
        "from the WeChat ecosystem. "
        "For reading the full content of a found article, use the 'wechat_article' tool."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Search keywords (Chinese or English). "
                    "Be specific to get better results. "
                    "Example: 'AI Agent 应用场景', '大模型 RAG'"
                )
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 10)",
                "default": 10,
                "minimum": 1,
                "maximum": 20
            },
            "account_name": {
                "type": "string",
                "description": (
                    "Optional: Filter by WeChat Official Account name. "
                    "Example: '36氪', '量子位'"
                ),
                "default": ""
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
        self._searcher = None

    def _get_searcher(self):
        """懒加载搜索器"""
        if self._searcher is None:
            from .search_providers import get_multi_source_searcher
            self._searcher = get_multi_source_searcher()
        return self._searcher

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """执行微信公众号文章搜索

        Args:
            query: 搜索关键词
            max_results: 最大结果数（默认 10）
            account_name: 可选，公众号名称过滤

        Returns:
            Dict: 搜索结果
                - success: bool
                - query: str (原始查询)
                - wechat_query: str (实际发送的查询)
                - count: int
                - results: List[Dict]
                    - title: str
                    - link: str
                    - snippet: str
                - provider: str (使用的搜索引擎)
                - hint: str (使用提示)
        """
        query = kwargs.get("query", "").strip()
        max_results = kwargs.get("max_results", 10)
        account_name = kwargs.get("account_name", "").strip()

        if not query:
            return {
                "success": False,
                "error": "Query parameter is required",
                "results": []
            }

        # 构造微信专用搜索查询
        # 使用 site: 操作符限定搜索范围
        wechat_query = f"{query} site:mp.weixin.qq.com"

        # 如果指定了公众号名称，添加到查询中
        if account_name:
            wechat_query = f"{account_name} {wechat_query}"

        logger.info(f"WeChat search: '{query}' -> '{wechat_query}' (max_results={max_results})")

        try:
            # 使用多源搜索器执行搜索
            searcher = self._get_searcher()

            # 请求更多结果以应对过滤损失
            raw_max = min(max_results * 2, 20)
            result = await searcher.search(wechat_query, raw_max)

            if not result.get("success"):
                logger.warning(f"WeChat search failed: {result.get('errors')}")
                return {
                    "success": False,
                    "error": "Search failed",
                    "errors": result.get("errors", []),
                    "query": query,
                    "results": []
                }

            # 过滤结果，只保留微信公众号链接
            raw_results = result.get("results", [])
            filtered_results = []

            for r in raw_results:
                link = r.get("link", "")
                # 严格匹配微信公众号域名
                if "mp.weixin.qq.com" in link:
                    filtered_results.append({
                        "title": r.get("title", ""),
                        "link": link,
                        "snippet": r.get("snippet", ""),
                    })

                    if len(filtered_results) >= max_results:
                        break

            logger.info(
                f"WeChat search found {len(filtered_results)} articles "
                f"(from {len(raw_results)} raw results) via {result.get('provider')}"
            )

            return {
                "success": True,
                "query": query,
                "wechat_query": wechat_query,
                "count": len(filtered_results),
                "results": filtered_results,
                "provider": result.get("provider"),
                "hint": (
                    "To read the full content of any article, use the 'wechat_article' tool "
                    "with the article link."
                )
            }

        except Exception as e:
            logger.error(f"WeChat search error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "query": query,
                "results": []
            }


# 全局实例
wechat_search_tool = WeChatSearchTool()


def create_wechat_search_tool() -> WeChatSearchTool:
    """创建微信搜索工具实例"""
    return WeChatSearchTool()
