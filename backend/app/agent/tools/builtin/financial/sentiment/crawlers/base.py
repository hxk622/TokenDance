"""Base class for sentiment crawlers."""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agent.tools.builtin.financial.compliance import (
    ComplianceChecker,
    get_compliance_checker,
)


@dataclass
class SentimentPost:
    """A single post/comment from financial platform."""

    id: str
    content: str
    author: str = ""
    timestamp: datetime | None = None
    url: str = ""
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    source: str = ""
    symbol: str = ""

    # Sentiment analysis results (filled by analyzer)
    sentiment_score: float | None = None  # -1 (bearish) to 1 (bullish)
    sentiment_label: str | None = None    # bullish / bearish / neutral
    key_points: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "author": self.author,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "url": self.url,
            "likes": self.likes,
            "comments": self.comments,
            "reposts": self.reposts,
            "source": self.source,
            "symbol": self.symbol,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "key_points": self.key_points,
        }


@dataclass
class CrawlResult:
    """Result from a crawl operation."""

    success: bool
    posts: list[SentimentPost] = field(default_factory=list)
    error: str | None = None
    source: str = ""
    symbol: str = ""
    crawled_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "posts": [p.to_dict() for p in self.posts],
            "error": self.error,
            "source": self.source,
            "symbol": self.symbol,
            "crawled_at": self.crawled_at.isoformat(),
            "metadata": self.metadata,
        }


class RateLimiter:
    """Simple rate limiter for crawling."""

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time: float = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until rate limit allows another request."""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time

            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                await asyncio.sleep(wait_time)

            self.last_request_time = time.time()


class BaseSentimentCrawler(ABC):
    """
    Base class for sentiment crawlers.

    All crawlers must:
    - Check compliance before crawling
    - Respect rate limits
    - Handle errors gracefully
    """

    name: str = "base"
    domain: str = ""

    def __init__(self, compliance_checker: ComplianceChecker | None = None):
        """
        Initialize crawler.

        Args:
            compliance_checker: Compliance checker instance.
                              If None, uses global checker.
        """
        self.compliance = compliance_checker or get_compliance_checker()
        self._rate_limiters: dict[str, RateLimiter] = {}

    def _get_rate_limiter(self, domain: str) -> RateLimiter:
        """Get or create rate limiter for domain."""
        if domain not in self._rate_limiters:
            rate_limit = self.compliance.get_rate_limit(f"https://{domain}/")
            self._rate_limiters[domain] = RateLimiter(rate_limit)
        return self._rate_limiters[domain]

    async def _check_compliance(self, url: str) -> tuple[bool, str]:
        """
        Check if URL can be crawled.

        Args:
            url: URL to check

        Returns:
            Tuple of (can_crawl, reason)
        """
        return self.compliance.can_crawl(url)

    async def _wait_for_rate_limit(self) -> None:
        """Wait for rate limit."""
        limiter = self._get_rate_limiter(self.domain)
        await limiter.acquire()

    @abstractmethod
    async def crawl(
        self,
        symbol: str,
        limit: int = 20,
        **kwargs
    ) -> CrawlResult:
        """
        Crawl sentiment data for a symbol.

        Args:
            symbol: Stock symbol to search for
            limit: Maximum number of posts to fetch
            **kwargs: Additional arguments

        Returns:
            CrawlResult with posts
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs
    ) -> CrawlResult:
        """
        Search for posts matching query.

        Args:
            query: Search query
            limit: Maximum number of posts
            **kwargs: Additional arguments

        Returns:
            CrawlResult with posts
        """
        pass

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize stock symbol for search.

        Override in subclasses if needed.
        """
        # Remove common suffixes
        symbol = symbol.upper()
        for suffix in [".SH", ".SS", ".SZ", ".XSHG", ".XSHE"]:
            if symbol.endswith(suffix):
                symbol = symbol[:-len(suffix)]
                break
        return symbol
