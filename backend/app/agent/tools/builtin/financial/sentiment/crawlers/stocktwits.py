"""
Stocktwits crawler for stock sentiment.

Stocktwits is a social media platform for investors and traders.
URL patterns:
- Symbol stream: https://stocktwits.com/symbol/{SYMBOL}
- API: https://api.stocktwits.com/api/2/streams/symbol/{SYMBOL}.json

Note: This crawler uses the public API which doesn't require authentication.
"""

from datetime import datetime
from typing import Any

import httpx

from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    BaseSentimentCrawler,
    CrawlResult,
    SentimentPost,
)


class StocktwitsCrawler(BaseSentimentCrawler):
    """
    Crawler for Stocktwits stock discussions.

    Fetches messages from the public API endpoints.
    Stocktwits messages often include sentiment labels (bullish/bearish).
    """

    name = "stocktwits"
    domain = "stocktwits.com"

    # API endpoints
    BASE_URL = "https://stocktwits.com"
    SYMBOL_API = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
    SEARCH_API = "https://api.stocktwits.com/api/2/search/symbols.json"
    TRENDING_API = "https://api.stocktwits.com/api/2/streams/trending.json"

    # Headers
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    def __init__(self, **kwargs):
        """Initialize Stocktwits crawler."""
        super().__init__(**kwargs)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _format_symbol(self, symbol: str) -> str:
        """
        Format symbol for Stocktwits API.

        Stocktwits uses uppercase symbols without exchange suffix.
        """
        # Remove common suffixes
        upper = symbol.upper()
        for suffix in [".US", ".NYSE", ".NASDAQ", ".AMEX"]:
            if upper.endswith(suffix):
                upper = upper[:-len(suffix)]
                break

        # Remove $ prefix if present
        if upper.startswith("$"):
            upper = upper[1:]

        return upper

    def _parse_timestamp(self, ts_str: str | None) -> datetime | None:
        """Parse timestamp from API response."""
        if not ts_str:
            return None
        try:
            # Stocktwits uses ISO 8601 format: 2024-01-15T10:30:00Z
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            return None

    def _parse_message(self, item: dict[str, Any], symbol: str = "") -> SentimentPost | None:
        """Parse a message from API response."""
        try:
            msg_id = str(item.get("id", ""))
            if not msg_id:
                return None

            # Get message body
            body = item.get("body", "")
            if not body or len(body) < 3:
                return None

            # Get user info
            user = item.get("user", {}) or {}
            author = user.get("username", "") or user.get("name", "")

            # Get sentiment if available (Stocktwits specific feature!)
            entities = item.get("entities", {}) or {}
            sentiment_data = entities.get("sentiment", {}) or {}
            native_sentiment = sentiment_data.get("basic") if sentiment_data else None

            # Map Stocktwits sentiment to our format
            sentiment_score = None
            sentiment_label = None
            if native_sentiment == "Bullish":
                sentiment_score = 0.8
                sentiment_label = "bullish"
            elif native_sentiment == "Bearish":
                sentiment_score = -0.8
                sentiment_label = "bearish"

            # Get engagement
            likes = item.get("likes", {})
            like_count = likes.get("total", 0) if isinstance(likes, dict) else 0

            # Build URL
            url = f"https://stocktwits.com/{author}/message/{msg_id}" if author else ""

            # Get symbols mentioned
            symbols = item.get("symbols", []) or []
            symbol_str = symbol or (symbols[0].get("symbol", "") if symbols else "")

            return SentimentPost(
                id=msg_id,
                content=body,
                author=author,
                timestamp=self._parse_timestamp(item.get("created_at")),
                url=url,
                likes=like_count,
                comments=item.get("conversation", {}).get("replies", 0) if item.get("conversation") else 0,
                reposts=item.get("reshares", {}).get("reshared_count", 0) if item.get("reshares") else 0,
                source=self.name,
                symbol=symbol_str,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
            )
        except Exception:
            return None

    async def crawl(
        self,
        symbol: str,
        limit: int = 20,
        **kwargs
    ) -> CrawlResult:
        """
        Crawl messages for a specific stock symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "TSLA")
            limit: Maximum number of messages

        Returns:
            CrawlResult with messages
        """
        formatted_symbol = self._format_symbol(symbol)
        url = self.SYMBOL_API.format(symbol=formatted_symbol)

        # Check compliance
        can_crawl, reason = await self._check_compliance(f"https://{self.domain}/")
        if not can_crawl:
            return CrawlResult(
                success=False,
                error=f"Compliance check failed: {reason}",
                source=self.name,
                symbol=symbol,
            )

        # Wait for rate limit
        await self._wait_for_rate_limit()

        try:
            client = await self._get_client()

            response = await client.get(url)

            if response.status_code == 404:
                return CrawlResult(
                    success=False,
                    error=f"Symbol not found: {formatted_symbol}",
                    source=self.name,
                    symbol=symbol,
                )

            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"API returned status {response.status_code}",
                    source=self.name,
                    symbol=symbol,
                )

            data = response.json()

            # Check for API response status
            response_status = data.get("response", {}).get("status")
            if response_status != 200:
                return CrawlResult(
                    success=False,
                    error=f"API error: {data.get('errors', 'Unknown error')}",
                    source=self.name,
                    symbol=symbol,
                )

            messages = data.get("messages", []) or []

            posts = []
            for item in messages:
                post = self._parse_message(item, formatted_symbol)
                if post:
                    posts.append(post)
                    if len(posts) >= limit:
                        break

            # Get symbol info if available
            symbol_info = data.get("symbol", {}) or {}

            return CrawlResult(
                success=True,
                posts=posts,
                source=self.name,
                symbol=symbol,
                metadata={
                    "formatted_symbol": formatted_symbol,
                    "symbol_title": symbol_info.get("title", ""),
                    "total_fetched": len(messages),
                    "parsed_count": len(posts),
                    "cursor_max": data.get("cursor", {}).get("max"),
                },
            )

        except httpx.TimeoutException:
            return CrawlResult(
                success=False,
                error="Request timeout",
                source=self.name,
                symbol=symbol,
            )
        except Exception as e:
            return CrawlResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=symbol,
            )

    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs
    ) -> CrawlResult:
        """
        Search for symbols matching query.

        Note: Stocktwits search API finds symbols, not messages.
        For message search, use crawl() with the found symbol.

        Args:
            query: Search query (stock name or symbol)
            limit: Maximum number of results

        Returns:
            CrawlResult (will crawl the first matching symbol)
        """
        # Check compliance
        can_crawl, reason = await self._check_compliance(f"https://{self.domain}/")
        if not can_crawl:
            return CrawlResult(
                success=False,
                error=f"Compliance check failed: {reason}",
                source=self.name,
                symbol=query,
            )

        # Wait for rate limit
        await self._wait_for_rate_limit()

        try:
            client = await self._get_client()

            # First search for matching symbols
            params = {"q": query}
            response = await client.get(self.SEARCH_API, params=params)

            if response.status_code != 200:
                # If search fails, try treating query as a symbol directly
                return await self.crawl(query, limit=limit)

            data = response.json()
            results = data.get("results", []) or []

            if not results:
                # No symbols found, try as direct symbol
                return await self.crawl(query, limit=limit)

            # Get the first matching symbol and crawl it
            first_symbol = results[0].get("symbol", query)
            return await self.crawl(first_symbol, limit=limit)

        except Exception as e:
            return CrawlResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=query,
            )

    async def get_trending(self, limit: int = 10) -> CrawlResult:
        """
        Get trending stocks on Stocktwits.

        Args:
            limit: Maximum number of posts

        Returns:
            CrawlResult with trending messages
        """
        # Check compliance
        can_crawl, reason = await self._check_compliance(f"https://{self.domain}/")
        if not can_crawl:
            return CrawlResult(
                success=False,
                error=f"Compliance check failed: {reason}",
                source=self.name,
                symbol="trending",
            )

        # Wait for rate limit
        await self._wait_for_rate_limit()

        try:
            client = await self._get_client()
            response = await client.get(self.TRENDING_API)

            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"API returned status {response.status_code}",
                    source=self.name,
                    symbol="trending",
                )

            data = response.json()
            messages = data.get("messages", []) or []

            posts = []
            for item in messages:
                post = self._parse_message(item, "trending")
                if post:
                    posts.append(post)
                    if len(posts) >= limit:
                        break

            return CrawlResult(
                success=True,
                posts=posts,
                source=self.name,
                symbol="trending",
                metadata={
                    "total_fetched": len(messages),
                    "parsed_count": len(posts),
                },
            )

        except Exception as e:
            return CrawlResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol="trending",
            )
