"""
Reddit crawler for stock sentiment.

Reddit is a major social platform with active financial communities.
Target subreddits:
- r/wallstreetbets - Retail investor discussions
- r/investing - General investing
- r/stocks - Stock market discussions

URL patterns:
- Subreddit: https://www.reddit.com/r/{subreddit}/
- Search: https://www.reddit.com/r/{subreddit}/search?q={query}

Note: This crawler uses Reddit's public JSON API (append .json to URLs).
No authentication required for public data, but rate limited.
"""

import re
from datetime import datetime
from typing import Any, Literal

import httpx

from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    BaseSentimentCrawler,
    CrawlResult,
    SentimentPost,
)


class RedditCrawler(BaseSentimentCrawler):
    """
    Crawler for Reddit financial subreddits.

    Fetches posts from the public JSON API.
    """

    name = "reddit"
    domain = "reddit.com"

    # Target subreddits for financial discussions
    FINANCIAL_SUBREDDITS = [
        "wallstreetbets",
        "investing",
        "stocks",
        "stockmarket",
        "options",
    ]

    # API endpoints (public JSON)
    BASE_URL = "https://www.reddit.com"
    SUBREDDIT_URL = "https://www.reddit.com/r/{subreddit}/{sort}.json"
    SEARCH_URL = "https://www.reddit.com/r/{subreddit}/search.json"
    MULTI_SEARCH_URL = "https://www.reddit.com/search.json"

    # Headers - Reddit requires a proper User-Agent
    DEFAULT_HEADERS = {
        "User-Agent": "TokenDance/1.0 (Financial Sentiment Analysis; https://github.com/TokenDance)",
        "Accept": "application/json",
    }

    def __init__(self, subreddits: list[str] | None = None, **kwargs: Any) -> None:
        """
        Initialize Reddit crawler.

        Args:
            subreddits: List of subreddits to crawl. Default: financial subreddits.
        """
        super().__init__(**kwargs)
        self.subreddits = subreddits or self.FINANCIAL_SUBREDDITS
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
        Format symbol for Reddit search.

        Reddit users often use $SYMBOL format.
        """
        # Remove common suffixes
        upper = symbol.upper()
        for suffix in [".US", ".NYSE", ".NASDAQ", ".AMEX"]:
            if upper.endswith(suffix):
                upper = upper[:-len(suffix)]
                break

        # Add $ prefix for search (common Reddit convention)
        if not upper.startswith("$"):
            upper = f"${upper}"

        return upper

    def _parse_timestamp(self, ts: float | None) -> datetime | None:
        """Parse Unix timestamp from API response."""
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts)
        except Exception:
            return None

    def _clean_text(self, text: str) -> str:
        """Clean text content."""
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove markdown links but keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        return text.strip()

    def _parse_post(self, item: dict[str, Any], symbol: str = "") -> SentimentPost | None:
        """Parse a post from API response."""
        try:
            data = item.get("data", {})
            if not data:
                return None

            post_id = data.get("id", "")
            if not post_id:
                return None

            # Get title and selftext
            title = data.get("title", "")
            selftext = data.get("selftext", "")

            # Combine title and selftext for content
            content = title
            if selftext and selftext != "[removed]" and selftext != "[deleted]":
                content = f"{title}\n\n{selftext[:500]}"  # Limit selftext length

            content = self._clean_text(content)
            if not content or len(content) < 5:
                return None

            # Skip removed/deleted posts
            if "[removed]" in content or "[deleted]" in content:
                return None

            # Get engagement metrics
            score = data.get("score", 0) or 0
            num_comments = data.get("num_comments", 0) or 0

            # Build URL
            permalink = data.get("permalink", "")
            url = f"https://www.reddit.com{permalink}" if permalink else ""

            # Get author
            author = data.get("author", "")
            if author in ["[deleted]", "[removed]"]:
                author = ""

            # Get subreddit
            subreddit = data.get("subreddit", "")

            return SentimentPost(
                id=f"reddit_{post_id}",
                content=content,
                author=author,
                timestamp=self._parse_timestamp(data.get("created_utc")),
                url=url,
                likes=score,
                comments=num_comments,
                reposts=0,  # Reddit doesn't have native reposts
                source=f"{self.name}/{subreddit}" if subreddit else self.name,
                symbol=symbol,
            )
        except Exception:
            return None

    async def _fetch_subreddit(
        self,
        subreddit: str,
        sort: Literal["hot", "new", "top", "rising"] = "hot",
        limit: int = 25,
        query: str | None = None,
    ) -> list[SentimentPost]:
        """
        Fetch posts from a single subreddit.

        Args:
            subreddit: Subreddit name
            sort: Sort order
            limit: Maximum posts
            query: Optional search query

        Returns:
            List of posts
        """
        try:
            client = await self._get_client()

            if query:
                # Search within subreddit
                url = self.SEARCH_URL.format(subreddit=subreddit)
                params: dict[str, str | int] = {
                    "q": query,
                    "restrict_sr": "1",  # Restrict to subreddit
                    "sort": "relevance",
                    "limit": min(limit, 100),
                    "t": "week",  # Time filter: week
                }
            else:
                # Get posts by sort order
                url = self.SUBREDDIT_URL.format(subreddit=subreddit, sort=sort)
                params = {"limit": min(limit, 100)}

            response = await client.get(url, params=params)

            if response.status_code != 200:
                return []

            data = response.json()
            children = data.get("data", {}).get("children", [])

            posts = []
            for item in children:
                post = self._parse_post(item, query or "")
                if post:
                    posts.append(post)

            return posts

        except Exception:
            return []

    async def crawl(
        self,
        symbol: str,
        limit: int = 20,
        subreddits: list[str] | None = None,
        **kwargs: Any
    ) -> CrawlResult:
        """
        Crawl posts mentioning a stock symbol.

        Searches across financial subreddits for the symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "TSLA")
            limit: Maximum number of posts total
            subreddits: Override subreddits to search

        Returns:
            CrawlResult with posts
        """
        # Check compliance
        can_crawl, reason = await self._check_compliance(f"https://{self.domain}/")
        if not can_crawl:
            return CrawlResult(
                success=False,
                error=f"Compliance check failed: {reason}",
                source=self.name,
                symbol=symbol,
            )

        formatted_symbol = self._format_symbol(symbol)
        target_subreddits = subreddits or self.subreddits

        all_posts: list[SentimentPost] = []
        errors: list[str] = []

        # Fetch from each subreddit (sequential to respect rate limits)
        posts_per_sub = max(5, limit // len(target_subreddits))

        for subreddit in target_subreddits:
            # Wait for rate limit before each request
            await self._wait_for_rate_limit()

            try:
                posts = await self._fetch_subreddit(
                    subreddit=subreddit,
                    query=formatted_symbol,
                    limit=posts_per_sub,
                )
                all_posts.extend(posts)
            except Exception as e:
                errors.append(f"{subreddit}: {str(e)}")

            if len(all_posts) >= limit:
                break

        # Trim to limit
        all_posts = all_posts[:limit]

        if not all_posts and errors:
            return CrawlResult(
                success=False,
                error="; ".join(errors),
                source=self.name,
                symbol=symbol,
            )

        return CrawlResult(
            success=True,
            posts=all_posts,
            source=self.name,
            symbol=symbol,
            metadata={
                "search_query": formatted_symbol,
                "subreddits_searched": target_subreddits,
                "parsed_count": len(all_posts),
                "errors": errors if errors else None,
            },
        )

    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs: Any
    ) -> CrawlResult:
        """
        Search for posts matching query across Reddit.

        Args:
            query: Search query
            limit: Maximum number of posts

        Returns:
            CrawlResult with posts
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

            # Search across all of Reddit but focus on financial terms
            params: dict[str, str | int] = {
                "q": f"{query} (stocks OR investing OR market)",
                "sort": "relevance",
                "limit": min(limit, 100),
                "t": "week",
            }

            response = await client.get(self.MULTI_SEARCH_URL, params=params)

            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"Search returned status {response.status_code}",
                    source=self.name,
                    symbol=query,
                )

            data = response.json()
            children = data.get("data", {}).get("children", [])

            posts = []
            for item in children:
                post = self._parse_post(item, query)
                if post:
                    posts.append(post)
                    if len(posts) >= limit:
                        break

            return CrawlResult(
                success=True,
                posts=posts,
                source=self.name,
                symbol=query,
                metadata={
                    "search_query": query,
                    "total_results": len(children),
                    "parsed_count": len(posts),
                },
            )

        except Exception as e:
            return CrawlResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=query,
            )

    async def get_hot(
        self,
        subreddit: str = "wallstreetbets",
        limit: int = 20
    ) -> CrawlResult:
        """
        Get hot posts from a subreddit.

        Args:
            subreddit: Subreddit name
            limit: Maximum number of posts

        Returns:
            CrawlResult with hot posts
        """
        # Check compliance
        can_crawl, reason = await self._check_compliance(f"https://{self.domain}/")
        if not can_crawl:
            return CrawlResult(
                success=False,
                error=f"Compliance check failed: {reason}",
                source=self.name,
                symbol=subreddit,
            )

        # Wait for rate limit
        await self._wait_for_rate_limit()

        try:
            posts = await self._fetch_subreddit(
                subreddit=subreddit,
                sort="hot",
                limit=limit,
            )

            return CrawlResult(
                success=True,
                posts=posts,
                source=f"{self.name}/{subreddit}",
                symbol=subreddit,
                metadata={
                    "subreddit": subreddit,
                    "sort": "hot",
                    "parsed_count": len(posts),
                },
            )

        except Exception as e:
            return CrawlResult(
                success=False,
                error=str(e),
                source=self.name,
                symbol=subreddit,
            )
