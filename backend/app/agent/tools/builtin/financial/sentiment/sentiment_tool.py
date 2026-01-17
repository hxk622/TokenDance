"""
SentimentTool - Unified interface for sentiment analysis.

Combines crawlers and analyzer into a single tool.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from app.agent.tools.builtin.financial.compliance import get_compliance_checker
from app.agent.tools.builtin.financial.sentiment.analyzer import (
    SentimentAnalysisResult,
    SentimentAnalyzer,
)
from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    CrawlResult,
    SentimentPost,
)
from app.agent.tools.builtin.financial.sentiment.crawlers.guba import GubaCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.xueqiu import XueqiuCrawler


@dataclass
class SentimentResult:
    """Complete sentiment analysis result."""

    success: bool
    symbol: str

    # Analysis results
    analysis: SentimentAnalysisResult | None = None

    # Raw crawl results
    crawl_results: dict[str, CrawlResult] = field(default_factory=dict)

    # All posts
    posts: list[SentimentPost] = field(default_factory=list)

    # Errors
    errors: list[str] = field(default_factory=list)

    # Metadata
    sources_used: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "symbol": self.symbol,
            "analysis": self.analysis.to_dict() if self.analysis else None,
            "posts": [p.to_dict() for p in self.posts],
            "sources_used": self.sources_used,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
            "disclaimer": self.disclaimer,
        }


class SentimentTool:
    """
    Unified sentiment analysis tool.

    Crawls posts from multiple sources and analyzes sentiment.

    Usage:
        tool = SentimentTool()
        result = await tool.analyze("600519", sources=["xueqiu", "guba"])
    """

    name = "sentiment_analysis"
    description = """分析股票的市场舆情和情绪。

从多个来源采集讨论帖子，使用AI分析整体情绪倾向。

数据源:
- xueqiu: 雪球社区
- guba: 东方财富股吧

示例:
- 分析茅台舆情: symbol="600519", sources=["xueqiu", "guba"]
- 只看雪球: symbol="600519", sources=["xueqiu"]

输出:
- overall_sentiment: bullish (看多) / bearish (看空) / neutral (中性)
- sentiment_score: -1到1之间的数值
- key_points: 主要观点汇总
- posts: 原始帖子列表
"""

    # Available crawlers
    CRAWLERS = {
        "xueqiu": XueqiuCrawler,
        "guba": GubaCrawler,
    }

    def __init__(self, anthropic_api_key: str | None = None):
        """
        Initialize sentiment tool.

        Args:
            anthropic_api_key: API key for Claude. If None, uses keyword analysis.
        """
        self.analyzer = SentimentAnalyzer(api_key=anthropic_api_key)
        self.compliance = get_compliance_checker()
        self._crawlers: dict[str, Any] = {}

    def _get_crawler(self, source: str):
        """Get or create crawler instance."""
        if source not in self._crawlers:
            if source not in self.CRAWLERS:
                raise ValueError(f"Unknown source: {source}")
            self._crawlers[source] = self.CRAWLERS[source]()
        return self._crawlers[source]

    async def analyze(
        self,
        symbol: str,
        sources: list[Literal["xueqiu", "guba"]] | None = None,
        limit_per_source: int = 20,
        analyze: bool = True,
        **kwargs
    ) -> SentimentResult:
        """
        Analyze sentiment for a stock symbol.

        Args:
            symbol: Stock symbol (e.g., "600519")
            sources: Sources to crawl. Default: ["xueqiu", "guba"]
            limit_per_source: Maximum posts per source
            analyze: Whether to run sentiment analysis

        Returns:
            SentimentResult with analysis and posts
        """
        if sources is None:
            sources = ["xueqiu", "guba"]

        result = SentimentResult(
            success=False,
            symbol=symbol,
            disclaimer=self.compliance.get_disclaimer(),
        )

        all_posts: list[SentimentPost] = []

        # Crawl from each source
        for source in sources:
            try:
                crawler = self._get_crawler(source)

                crawl_result = await crawler.crawl(
                    symbol,
                    limit=limit_per_source,
                    **kwargs
                )

                result.crawl_results[source] = crawl_result

                if crawl_result.success:
                    result.sources_used.append(source)
                    all_posts.extend(crawl_result.posts)
                else:
                    result.errors.append(f"{source}: {crawl_result.error}")

            except Exception as e:
                result.errors.append(f"{source}: {str(e)}")

        # Store all posts
        result.posts = all_posts

        # Run analysis if we have posts
        if all_posts and analyze:
            try:
                analysis = await self.analyzer.analyze_posts(all_posts, symbol)
                result.analysis = analysis
                result.success = True
            except Exception as e:
                result.errors.append(f"Analysis error: {str(e)}")
        elif all_posts:
            result.success = True

        return result

    async def crawl_only(
        self,
        symbol: str,
        sources: list[str] | None = None,
        limit_per_source: int = 20,
    ) -> SentimentResult:
        """
        Only crawl posts without analysis.

        Args:
            symbol: Stock symbol
            sources: Sources to crawl
            limit_per_source: Maximum posts per source

        Returns:
            SentimentResult with posts but no analysis
        """
        return await self.analyze(
            symbol,
            sources=sources,
            limit_per_source=limit_per_source,
            analyze=False,
        )

    async def search(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 20,
    ) -> SentimentResult:
        """
        Search for posts matching query.

        Args:
            query: Search query
            sources: Sources to search
            limit: Maximum posts

        Returns:
            SentimentResult with posts
        """
        if sources is None:
            sources = ["xueqiu"]  # Guba doesn't support search

        result = SentimentResult(
            success=False,
            symbol=query,
            disclaimer=self.compliance.get_disclaimer(),
        )

        all_posts: list[SentimentPost] = []

        for source in sources:
            try:
                crawler = self._get_crawler(source)

                crawl_result = await crawler.search(query, limit=limit)

                result.crawl_results[source] = crawl_result

                if crawl_result.success:
                    result.sources_used.append(source)
                    all_posts.extend(crawl_result.posts)
                else:
                    result.errors.append(f"{source}: {crawl_result.error}")

            except Exception as e:
                result.errors.append(f"{source}: {str(e)}")

        result.posts = all_posts

        if all_posts:
            analysis = await self.analyzer.analyze_posts(all_posts, query)
            result.analysis = analysis
            result.success = True

        return result

    async def close(self) -> None:
        """Close all crawler connections."""
        for crawler in self._crawlers.values():
            if hasattr(crawler, 'close'):
                await crawler.close()
        self._crawlers.clear()

    def get_available_sources(self) -> list[str]:
        """Get list of available sources."""
        return list(self.CRAWLERS.keys())


# Singleton instance
_sentiment_tool: SentimentTool | None = None


def get_sentiment_tool() -> SentimentTool:
    """Get global sentiment tool instance."""
    global _sentiment_tool

    if _sentiment_tool is None:
        _sentiment_tool = SentimentTool()

    return _sentiment_tool
