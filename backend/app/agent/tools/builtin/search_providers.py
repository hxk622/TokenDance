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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SearchProviderType(Enum):
    """搜索提供者类型"""
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"
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
    """DuckDuckGo 搜索提供者"""

    provider_type = SearchProviderType.DUCKDUCKGO

    def __init__(self):
        try:
            from duckduckgo_search import DDGS
            self._ddgs_class = DDGS
            self._available = True
        except ImportError:
            self._ddgs_class = None
            self._available = False
            logger.warning("duckduckgo-search not installed")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("DuckDuckGo provider not available")

        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            self._search_sync,
            query,
            max_results
        )
        return results

    def _search_sync(self, query: str, max_results: int) -> list[SearchResult]:
        with self._ddgs_class() as ddgs:
            raw_results = ddgs.text(
                keywords=query,
                region="wt-wt",
                safesearch="moderate",
                max_results=max_results
            )

            return [
                SearchResult(
                    title=r.get("title", ""),
                    link=r.get("href", ""),
                    snippet=r.get("body", ""),
                    source=self.provider_type
                )
                for r in raw_results
            ]


class BraveSearchProvider(BaseSearchProvider):
    """Brave Search 提供者"""

    provider_type = SearchProviderType.BRAVE

    def __init__(self):
        self.api_key = os.getenv("BRAVE_SEARCH_API_KEY")
        self._available = bool(self.api_key)

        if not self._available:
            logger.debug("Brave Search API key not configured")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("Brave Search provider not available")

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={
                    "q": query,
                    "count": max_results
                },
                headers={
                    "Accept": "application/json",
                    "X-Subscription-Token": self.api_key
                }
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("web", {}).get("results", [])[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    link=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source=self.provider_type
                ))

            return results


class SerperProvider(BaseSearchProvider):
    """Serper (Google) 搜索提供者"""

    provider_type = SearchProviderType.SERPER

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        self._available = bool(self.api_key)

        if not self._available:
            logger.debug("Serper API key not configured")

    def is_available(self) -> bool:
        return self._available

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        if not self._available:
            raise RuntimeError("Serper provider not available")

        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
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
            providers = [
                DuckDuckGoProvider(),
                BraveSearchProvider(),
                SerperProvider()
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
