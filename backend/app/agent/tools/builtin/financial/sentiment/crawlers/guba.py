"""
Guba (东方财富股吧) crawler for stock sentiment.

Guba is the largest stock discussion forum in China.
URL patterns:
- Stock forum: https://guba.eastmoney.com/list,{SYMBOL}.html
- Post detail: https://guba.eastmoney.com/news,{SYMBOL},{POST_ID}.html

Note: This crawler uses HTTP requests to fetch public data.
"""

import asyncio
import re
from datetime import datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    BaseSentimentCrawler,
    CrawlResult,
    SentimentPost,
)


class GubaCrawler(BaseSentimentCrawler):
    """
    Crawler for Guba (东方财富股吧) stock discussions.
    
    Fetches posts from the stock discussion forum.
    """
    
    name = "guba"
    domain = "guba.eastmoney.com"
    
    # URL templates
    BASE_URL = "https://guba.eastmoney.com"
    LIST_URL = "https://guba.eastmoney.com/list,{symbol}.html"
    LIST_API = "https://guba.eastmoney.com/interface/GetData.aspx"
    
    # Headers
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://guba.eastmoney.com/",
    }
    
    def __init__(self, **kwargs):
        """Initialize Guba crawler."""
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
        Format symbol for Guba.
        
        Guba uses plain 6-digit codes.
        """
        # Remove SH/SZ prefix if present
        upper = symbol.upper()
        if upper.startswith(('SH', 'SZ')):
            symbol = upper[2:]
        
        symbol = self._normalize_symbol(symbol)
        return symbol
    
    def _parse_time(self, time_str: str) -> datetime | None:
        """Parse time string from Guba."""
        if not time_str:
            return None
        
        try:
            time_str = time_str.strip()
            now = datetime.now()
            
            # Handle relative time
            if "分钟前" in time_str:
                minutes = int(re.search(r'(\d+)', time_str).group(1))
                from datetime import timedelta
                return now - timedelta(minutes=minutes)
            elif "小时前" in time_str:
                hours = int(re.search(r'(\d+)', time_str).group(1))
                from datetime import timedelta
                return now - timedelta(hours=hours)
            elif "天前" in time_str:
                days = int(re.search(r'(\d+)', time_str).group(1))
                from datetime import timedelta
                return now - timedelta(days=days)
            
            # Handle date formats
            if "-" in time_str:
                # Format: MM-DD HH:MM or YYYY-MM-DD
                if len(time_str) <= 11:  # MM-DD HH:MM
                    return datetime.strptime(f"{now.year}-{time_str}", "%Y-%m-%d %H:%M")
                else:
                    return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
            
            return None
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
            symbol: Stock symbol (e.g., "600519")
            limit: Maximum number of posts
            
        Returns:
            CrawlResult with posts
        """
        formatted_symbol = self._format_symbol(symbol)
        url = self.LIST_URL.format(symbol=formatted_symbol)
        
        # Check compliance
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
            
            response = await client.get(url)
            
            if response.status_code != 200:
                return CrawlResult(
                    success=False,
                    error=f"HTTP status {response.status_code}",
                    source=self.name,
                    symbol=symbol,
                )
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            posts = []
            
            # Find post list
            # Guba uses different structures, try multiple selectors
            post_items = soup.select('.listitem, .articleh, .normal_post')
            
            for item in post_items:
                if len(posts) >= limit:
                    break
                
                post = self._parse_html_post(item, symbol)
                if post:
                    posts.append(post)
            
            # If no posts found with selectors, try parsing table rows
            if not posts:
                rows = soup.select('table tbody tr, #articlelistnew div')
                for row in rows:
                    if len(posts) >= limit:
                        break
                    post = self._parse_table_row(row, symbol)
                    if post:
                        posts.append(post)
            
            return CrawlResult(
                success=True,
                posts=posts,
                source=self.name,
                symbol=symbol,
                metadata={
                    "url": url,
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
    
    def _parse_html_post(self, item: Any, symbol: str) -> SentimentPost | None:
        """Parse a post from HTML element."""
        try:
            # Try to find title/content
            title_elem = item.select_one('.title, .l3 a, .l3')
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title or len(title) < 3:
                return None
            
            # Get URL
            href = ""
            if title_elem.name == 'a':
                href = title_elem.get('href', '')
            else:
                link = title_elem.select_one('a')
                if link:
                    href = link.get('href', '')
            
            if href and not href.startswith('http'):
                href = f"{self.BASE_URL}{href}"
            
            # Try to get post ID from URL
            post_id = ""
            if href:
                match = re.search(r'/news,\w+,(\d+)', href)
                if match:
                    post_id = match.group(1)
                else:
                    post_id = href.split('/')[-1].replace('.html', '')
            
            if not post_id:
                import hashlib
                post_id = hashlib.md5(title.encode()).hexdigest()[:12]
            
            # Get author
            author_elem = item.select_one('.l4 a, .author, .zz')
            author = author_elem.get_text(strip=True) if author_elem else ""
            
            # Get time
            time_elem = item.select_one('.l5, .time, .update')
            time_str = time_elem.get_text(strip=True) if time_elem else ""
            timestamp = self._parse_time(time_str)
            
            # Get engagement
            read_elem = item.select_one('.l1, .read')
            reply_elem = item.select_one('.l2, .reply')
            
            read_count = 0
            reply_count = 0
            
            if read_elem:
                try:
                    read_count = int(re.sub(r'\D', '', read_elem.get_text()) or 0)
                except:
                    pass
            
            if reply_elem:
                try:
                    reply_count = int(re.sub(r'\D', '', reply_elem.get_text()) or 0)
                except:
                    pass
            
            return SentimentPost(
                id=post_id,
                content=title,
                author=author,
                timestamp=timestamp,
                url=href,
                likes=read_count,  # Using read count as proxy
                comments=reply_count,
                source=self.name,
                symbol=symbol,
            )
            
        except Exception:
            return None
    
    def _parse_table_row(self, row: Any, symbol: str) -> SentimentPost | None:
        """Parse a post from table row."""
        try:
            # Get all text and links
            text = row.get_text(strip=True)
            if not text or len(text) < 5:
                return None
            
            # Skip header rows
            if '阅读' in text and '评论' in text and '标题' in text:
                return None
            
            link = row.select_one('a')
            href = link.get('href', '') if link else ""
            title = link.get_text(strip=True) if link else text[:100]
            
            if href and not href.startswith('http'):
                href = f"{self.BASE_URL}{href}"
            
            # Generate ID
            import hashlib
            post_id = hashlib.md5(title.encode()).hexdigest()[:12]
            
            return SentimentPost(
                id=post_id,
                content=title,
                author="",
                timestamp=None,
                url=href,
                source=self.name,
                symbol=symbol,
            )
            
        except Exception:
            return None
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs
    ) -> CrawlResult:
        """
        Search for posts matching query.
        
        Note: Guba doesn't have a public search API,
        so this falls back to crawling the stock forum.
        """
        # Check if query looks like a stock code
        if query.isdigit() and len(query) == 6:
            return await self.crawl(query, limit, **kwargs)
        
        # For non-code queries, return not supported
        return CrawlResult(
            success=False,
            error="Guba search only supports stock codes. Use crawl() instead.",
            source=self.name,
            symbol=query,
        )
