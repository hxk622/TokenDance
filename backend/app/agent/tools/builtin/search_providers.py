"""
多搜索源提供者 (Search Providers)

支持多个搜索引擎，实现自动降级:
1. DuckDuckGo (免费，无需 API Key)
2. Brave Search (需要 API Key，质量高)
3. Serper (Google 结果，需要 API Key)

降级策略:
- 主源失败 -> 自动切换备用源
- 所有源失败 -> 返回空结果 + 错误信息
"""
import asyncio
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import quote_plus, unquote, parse_qs, urlparse

logger = logging.getLogger(__name__)


def get_proxy_url() -> str | None:
    """获取搜索代理 URL

    优先级: SEARCH_HTTP_PROXY > HTTPS_PROXY > HTTP_PROXY > 默认值

    使用专用的 SEARCH_HTTP_PROXY 避免和 Shell 环境变量冲突
    （如 Warp 终端的 HTTP_PROXY=7667）
    """
    # 专用搜索代理变量（最高优先级）
    proxy = os.getenv("SEARCH_HTTP_PROXY")
    if proxy:
        return proxy

    # 默认使用 ClashX 端口 (7890)
    # 不使用通用 HTTP_PROXY，因为可能被 Warp 终端设置为 7667
    return "http://127.0.0.1:7890"


class SearchProviderType(Enum):
    """搜索提供者类型"""
    DUCKDUCKGO = "duckduckgo"
    TAVILY = "tavily"
    SERPER = "serper"
    BING = "bing"


@dataclass
class SearchResult:
    """统一的搜索结果"""
    title: str
    link: str
    snippet: str
    source: SearchProviderType

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "link": self.link,
            "snippet": self.snippet,
            "source": self.source.value
        }


class BaseSearchProvider(ABC):
    """搜索提供者基类"""

    provider_type: SearchProviderType

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """执行搜索"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass


class DuckDuckGoProvider(BaseSearchProvider):
    """DuckDuckGo 搜索提供者 - 免费

    优点:
    - 完全免费，无需 API Key
    - 隐私友好

    注意:
    - 需要代理才能访问（国内网络）
    - 使用 httpx 直接请求 HTML API，避免 duckduckgo-search 库的 SSL 问题
    """

    provider_type = SearchProviderType.DUCKDUCKGO

    def __init__(self):
        # 使用 httpx 实现，不依赖 duckduckgo-search 库
        try:
            import httpx
            self._httpx_available = True
        except ImportError:
            self._httpx_available = False
            logger.warning("httpx not installed, DuckDuckGo provider unavailable")

        self._available = self._httpx_available
        self._proxy_url = get_proxy_url()

        if self._available:
            logger.info(f"DuckDuckGo provider enabled (proxy: {self._proxy_url})")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("DuckDuckGo provider not available")

        import httpx

        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # 使用配置的代理
        async with httpx.AsyncClient(
            timeout=30.0,
            proxy=self._proxy_url,
            verify=False,
            follow_redirects=True
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

        # 解析 HTML 结果
        results = self._parse_html_results(html, max_results)
        logger.info(f"DuckDuckGo found {len(results)} results for: {query}")
        return results

    def _parse_html_results(self, html: str, max_results: int) -> list[SearchResult]:
        """Parse DuckDuckGo HTML search results"""
        results = []

        # 匹配搜索结果块
        # DuckDuckGo HTML 结果格式: <a class="result__a" href="...">title</a>
        link_pattern = re.compile(
            r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.+?)</a>',
            re.IGNORECASE | re.DOTALL
        )
        # BUG FIX: 使用 .+? 而不是 [^<]*，因为 snippet 可能包含 <b> 等高亮标签
        snippet_pattern = re.compile(
            r'<a[^>]+class="result__snippet"[^>]*>(.+?)</a>',
            re.IGNORECASE | re.DOTALL
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (link, title) in enumerate(links[:max_results]):
            snippet = snippets[i] if i < len(snippets) else ""
            # 清理 HTML 标签
            title = re.sub(r'<[^>]+>', '', title).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet).strip()

            # 提取真实 URL (DuckDuckGo 使用跳转链接)
            real_url = self._extract_real_url(link)

            if real_url and title:
                results.append(SearchResult(
                    title=title,
                    link=real_url,
                    snippet=snippet,
                    source=self.provider_type
                ))

        return results

    def _extract_real_url(self, ddg_url: str) -> str:
        """Extract real URL from DuckDuckGo redirect link

        DuckDuckGo links look like: //duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&rut=...
        """
        if not ddg_url:
            return ""

        # 如果已经是直接 URL
        if ddg_url.startswith("http"):
            return ddg_url

        # 解析 DuckDuckGo 跳转链接
        try:
            # 添加 https: 如果缺少
            if ddg_url.startswith("//"):
                ddg_url = "https:" + ddg_url

            parsed = urlparse(ddg_url)
            query_params = parse_qs(parsed.query)

            # 提取 uddg 参数（真实 URL）
            if "uddg" in query_params:
                real_url = unquote(query_params["uddg"][0])
                return real_url
        except Exception:
            pass

        return ddg_url


class TavilyProvider(BaseSearchProvider):
    """Tavily 搜索提供者 - 专为 AI 设计

    优点:
    - 专为 AI/LLM 应用设计，结果质量高
    - 提供摘要和答案提取
    - 免费额度 1000 次/月
    """

    provider_type = SearchProviderType.TAVILY

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self._available = bool(self.api_key)

        if self._available:
            logger.info("Tavily provider enabled (TAVILY_API_KEY configured)")
        else:
            logger.debug("Tavily API key not configured")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("Tavily provider not available")

        import httpx

        # 使用系统代理 (trust_env=True), 开发环境禁用 SSL 验证
        async with httpx.AsyncClient(timeout=30.0, trust_env=True, verify=False) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("content", ""),
                    source=self.provider_type
                ))

            return results


class SerperProvider(BaseSearchProvider):
    """Serper (Google) 搜索提供者 - 推荐首选

    优点:
    - 使用 Google 搜索结果，质量最高
    - API 服务稳定，不受网络限制
    - 免费额度 2500 次/月
    """

    provider_type = SearchProviderType.SERPER

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self._available = bool(self.api_key)

        if self._available:
            logger.info("Serper provider enabled (SERPER_API_KEY configured)")
        else:
            logger.debug("Serper API key not configured")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("Serper provider not available")

        import httpx

        # 使用系统代理 (trust_env=True), 开发环境禁用 SSL 验证
        async with httpx.AsyncClient(timeout=30.0, trust_env=True, verify=False) as client:
            response = await client.post(
                "https://google.serper.dev/search",
                json={
                    "q": query,
                    "num": max_results
                },
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("organic", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                    source=self.provider_type
                ))

            return results


class MultiSourceSearcher:
    """多源搜索器

    特性:
    - 自动降级
    - 并行搜索 (可选)
    - 结果合并去重
    """

    def __init__(
        self,
        providers: list[BaseSearchProvider] | None = None,
        parallel: bool = False
    ):
        """
        Args:
            providers: 搜索提供者列表 (按优先级排序)
            parallel: 是否并行搜索所有源
        """
        if providers is None:
            # 优先级: DuckDuckGo (免费) > Serper (Google) > Tavily (AI专用)
            providers = [
                DuckDuckGoProvider(),   # 1st: 免费，通过代理访问
                SerperProvider(),       # 2nd: Google 结果，API 服务稳定
                TavilyProvider()        # 3rd: 专为 AI 设计，质量高
            ]

        self.providers = [p for p in providers if p.is_available()]
        self.parallel = parallel

        logger.info(f"MultiSourceSearcher initialized with {len(self.providers)} providers")

    async def search(
        self,
        query: str,
        max_results: int = 5
    ) -> dict[str, Any]:
        """执行搜索

        Args:
            query: 搜索查询
            max_results: 每个源的最大结果数

        Returns:
            Dict: {
                "success": bool,
                "results": List[Dict],
                "provider": str,
                "fallback_used": bool,
                "errors": List[str]
            }
        """
        if not self.providers:
            return {
                "success": False,
                "results": [],
                "provider": None,
                "fallback_used": False,
                "errors": ["No search providers available"]
            }

        if self.parallel:
            return await self._search_parallel(query, max_results)
        else:
            return await self._search_with_fallback(query, max_results)

    async def _search_with_fallback(
        self,
        query: str,
        max_results: int
    ) -> dict[str, Any]:
        """带降级的顺序搜索"""
        errors = []
        fallback_used = False

        for i, provider in enumerate(self.providers):
            try:
                results = await provider.search(query, max_results)

                return {
                    "success": True,
                    "results": [r.to_dict() for r in results],
                    "provider": provider.provider_type.value,
                    "fallback_used": i > 0,
                    "errors": errors
                }

            except Exception as e:
                error_msg = f"{provider.provider_type.value}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Search provider failed: {error_msg}")
                fallback_used = True
                continue

        # 所有源都失败
        return {
            "success": False,
            "results": [],
            "provider": None,
            "fallback_used": fallback_used,
            "errors": errors
        }

    async def _search_parallel(
        self,
        query: str,
        max_results: int
    ) -> dict[str, Any]:
        """并行搜索所有源"""
        tasks = [
            self._safe_search(provider, query, max_results)
            for provider in self.providers
        ]

        results_list = await asyncio.gather(*tasks)

        # 合并去重
        all_results = []
        seen_urls = set()
        errors = []
        successful_provider = None

        for provider, results, error in results_list:
            if error:
                errors.append(f"{provider.provider_type.value}: {error}")
            elif results:
                if successful_provider is None:
                    successful_provider = provider.provider_type.value

                for r in results:
                    if r.link not in seen_urls:
                        seen_urls.add(r.link)
                        all_results.append(r.to_dict())

        return {
            "success": len(all_results) > 0,
            "results": all_results[:max_results * 2],  # 返回更多结果
            "provider": successful_provider,
            "fallback_used": len(errors) > 0,
            "errors": errors
        }

    async def _safe_search(
        self,
        provider: BaseSearchProvider,
        query: str,
        max_results: int
    ) -> tuple:
        """安全搜索 (捕获异常)"""
        try:
            results = await provider.search(query, max_results)
            return (provider, results, None)
        except Exception as e:
            return (provider, [], str(e))


# 便捷函数
_global_searcher: MultiSourceSearcher | None = None


def get_multi_source_searcher() -> MultiSourceSearcher:
    """获取全局多源搜索器"""
    global _global_searcher
    if _global_searcher is None:
        _global_searcher = MultiSourceSearcher()
    return _global_searcher


def create_multi_source_searcher(
    parallel: bool = False
) -> MultiSourceSearcher:
    """创建多源搜索器"""
    return MultiSourceSearcher(parallel=parallel)
