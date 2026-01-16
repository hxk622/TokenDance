"""
Xueqiu (雪球) crawler for stock sentiment.

Xueqiu is one of the largest investor communities in China.
URL patterns:
- Stock page: https://xueqiu.com/S/{SYMBOL}
- Search: https://xueqiu.com/k?q={QUERY}

Note: This crawler uses HTTP requests to fetch public API data.
"""

import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import Any

import httpx

from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    BaseSentimentCrawler,
    CrawlResult,
    SentimentPost,
)


class XueqiuCrawler(BaseSentimentCrawler):
    """
    Crawler for Xueqiu (雪球) stock discussions.
    
    Fetches posts from the public API endpoints.
    """
    
    name = "xueqiu"
    domain = "xueqiu.com"
    
    # API endpoints
    BASE_URL = "https://xueqiu.com"
    STOCK_POSTS_API = "https://xueqiu.com/query/v1/symbol/search/status"
    SEARCH_API = "https://xueqiu.com/query/v1/search/status"
    
    # Headers to mimic browser
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://xueqiu.com/",
        "Origin": "https://xueqiu.com",
    }
    
    def __init__(self, **kwargs):
        """Initialize Xueqiu crawler."""
        super().__init__(**kwargs)
        self._cookies: dict[str, str] = {}
        self._client: httpx.AsyncClient | None = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with cookies."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self.DEFAULT_HEADERS,
                timeout=30.0,
                follow_redirects=True,
            )
            
            # Get initial cookies by visiting homepage
            try:
                response = await self._client.get(self.BASE_URL)
                # Cookies are automatically stored in client
            except Exception:
                pass
        
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _format_symbol(self, symbol: str) -> str:
        """
        Format symbol for Xueqiu API.
        
        Xueqiu uses format: SH600519, SZ000001
        """
        symbol = self._normalize_symbol(symbol)
        
        # Determine exchange prefix
        if symbol.startswith(('60', '68', '5')):
            return f"SH{symbol}"
        elif symbol.startswith(('00', '30', '1', '2')):
            return f"SZ{symbol}"
        else:
            # Try both
            return f"SH{symbol}"
    
    def _parse_timestamp(self, ts: int | str | None) -> datetime | None:
        """Parse timestamp from API response."""
        if ts is None:
            return None
        try:
            if isinstance(ts, str):
                ts = int(ts)
            # Xueqiu uses millisecond timestamps
            return datetime.fromtimestamp(ts / 1000)
        except Exception:
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        if not text:
            return ""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Remove multiple spaces
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _parse_post(self, item: dict[str, Any], symbol: str = "") -> SentimentPost | None:
        """Parse a post from API response."""
        try:
            post_id = str(item.get("id", ""))
            if not post_id:
                return None
            
            # Get text content
            text = item.get("text", "") or item.get("description", "")
            text = self._clean_html(text)
            
            if not text or len(text) < 5:
                return None
            
            # Get author info
            user = item.get("user", {}) or {}
            author = user.get("screen_name", "") or user.get("name", "")
            
            # Get engagement metrics
            like_count = item.get("like_count", 0) or 0
            reply_count = item.get("reply_count", 0) or 0
            retweet_count = item.get("retweet_count", 0) or 0
            
            # Build URL
            user_id = user.get("id", "")
            url = f"https://xueqiu.com/{user_id}/{post_id}" if user_id else ""
            
            return SentimentPost(
                id=post_id,
                content=text,
                author=author,
                timestamp=self._parse_timestamp(item.get("created_at")),
                url=url,
                likes=like_count,
                comments=reply_count,
                reposts=retweet_count,
                source=self.name,
                symbol=symbol,
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
        Crawl posts for a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., "600519", "SH600519")
            limit: Maximum number of posts
            
        Returns:
            CrawlResult with posts
        """
        # Check compliance
        url = f"https://{self.domain}/S/{symbol}"
        can_crawl, reason = await self._check_compliance(url)
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
            formatted_symbol = self._format_symbol(symbol)
            
            params = {
                "symbol": formatted_symbol,
                "count": min(limit, 50),  # API limit
                "comment": 0,
                "page": 1,
            }
            
            response = await client.get(
                self.STOCK_POSTS_API,
                params=params,
            )
            
            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"API returned status {response.status_code}",
                    source=self.name,
                    symbol=symbol,
                )
            
            data = response.json()
            items = data.get("list", []) or []
            
            posts = []
            for item in items:
                post = self._parse_post(item, symbol)
                if post:
                    posts.append(post)
                    if len(posts) >= limit:
                        break
            
            return CrawlResult(
                success=True,
                posts=posts,
                source=self.name,
                symbol=symbol,
                metadata={
                    "formatted_symbol": formatted_symbol,
                    "total_fetched": len(items),
                    "parsed_count": len(posts),
                },
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
        Search for posts matching query.
        
        Args:
            query: Search query (stock name, topic, etc.)
            limit: Maximum number of posts
            
        Returns:
            CrawlResult with posts
        """
        # Check compliance
        url = f"https://{self.domain}/k?q={query}"
        can_crawl, reason = await self._check_compliance(url)
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
            
            params = {
                "q": query,
                "count": min(limit, 50),
                "page": 1,
            }
            
            response = await client.get(
                self.SEARCH_API,
                params=params,
            )
            
            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"API returned status {response.status_code}",
                    source=self.name,
                    symbol=query,
                )
            
            data = response.json()
            items = data.get("list", []) or []
            
            posts = []
            for item in items:
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
                    "query": query,
                    "total_fetched": len(items),
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
