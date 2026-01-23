"""
Tests for social media sentiment crawlers (Reddit, Stocktwits).

These tests verify:
- Crawler initialization and configuration
- Symbol formatting
- API response parsing
- Error handling
- Integration with SentimentTool
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.tools.builtin.financial.sentiment.crawlers.reddit import RedditCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.stocktwits import StocktwitsCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    CrawlResult,
    SentimentPost,
)
from app.agent.tools.builtin.financial.sentiment.sentiment_tool import SentimentTool


# =============================================================================
# Stocktwits Crawler Tests
# =============================================================================


class TestStocktwitsCrawler:
    """Tests for StocktwitsCrawler."""

    def test_init(self):
        """Test crawler initialization."""
        crawler = StocktwitsCrawler()
        assert crawler.name == "stocktwits"
        assert crawler.domain == "stocktwits.com"

    def test_format_symbol(self):
        """Test symbol formatting."""
        crawler = StocktwitsCrawler()

        # Basic symbol
        assert crawler._format_symbol("AAPL") == "AAPL"
        assert crawler._format_symbol("aapl") == "AAPL"

        # With $ prefix
        assert crawler._format_symbol("$AAPL") == "AAPL"

        # With exchange suffix
        assert crawler._format_symbol("AAPL.US") == "AAPL"
        assert crawler._format_symbol("TSLA.NASDAQ") == "TSLA"

    def test_parse_timestamp(self):
        """Test timestamp parsing."""
        crawler = StocktwitsCrawler()

        # Valid ISO timestamp
        ts = crawler._parse_timestamp("2024-01-15T10:30:00Z")
        assert ts is not None
        assert ts.year == 2024
        assert ts.month == 1
        assert ts.day == 15

        # Invalid timestamp
        assert crawler._parse_timestamp(None) is None
        assert crawler._parse_timestamp("invalid") is None

    def test_parse_message_basic(self):
        """Test basic message parsing."""
        crawler = StocktwitsCrawler()

        # Sample API response
        item = {
            "id": 12345,
            "body": "I'm bullish on $AAPL! Great earnings!",
            "created_at": "2024-01-15T10:30:00Z",
            "user": {
                "id": 100,
                "username": "trader123",
            },
            "entities": {
                "sentiment": {
                    "basic": "Bullish"
                }
            },
            "likes": {"total": 10},
            "symbols": [{"symbol": "AAPL"}],
        }

        post = crawler._parse_message(item, "AAPL")
        assert post is not None
        assert post.id == "12345"
        assert "bullish" in post.content.lower()
        assert post.author == "trader123"
        assert post.source == "stocktwits"
        assert post.sentiment_label == "bullish"
        assert post.sentiment_score == 0.8

    def test_parse_message_bearish(self):
        """Test parsing bearish message."""
        crawler = StocktwitsCrawler()

        item = {
            "id": 67890,
            "body": "Selling all my shares...",
            "user": {"username": "bear_trader"},
            "entities": {
                "sentiment": {"basic": "Bearish"}
            },
        }

        post = crawler._parse_message(item, "TSLA")
        assert post is not None
        assert post.sentiment_label == "bearish"
        assert post.sentiment_score == -0.8

    def test_parse_message_no_sentiment(self):
        """Test parsing message without sentiment."""
        crawler = StocktwitsCrawler()

        item = {
            "id": 11111,
            "body": "Just some news about the market.",
            "user": {"username": "news_bot"},
            "entities": {},
        }

        post = crawler._parse_message(item, "SPY")
        assert post is not None
        assert post.sentiment_label is None
        assert post.sentiment_score is None

    def test_parse_message_invalid(self):
        """Test parsing invalid messages."""
        crawler = StocktwitsCrawler()

        # Empty ID
        assert crawler._parse_message({"body": "test"}, "AAPL") is None

        # Empty body
        assert crawler._parse_message({"id": 123, "body": ""}, "AAPL") is None

        # Too short body
        assert crawler._parse_message({"id": 123, "body": "ab"}, "AAPL") is None

    @pytest.mark.asyncio
    async def test_crawl_mock(self):
        """Test crawl with mocked HTTP response."""
        crawler = StocktwitsCrawler()

        mock_response = {
            "response": {"status": 200},
            "messages": [
                {
                    "id": 1,
                    "body": "Bullish on $AAPL",
                    "user": {"username": "user1"},
                    "entities": {"sentiment": {"basic": "Bullish"}},
                },
                {
                    "id": 2,
                    "body": "Bearish on $AAPL",
                    "user": {"username": "user2"},
                    "entities": {"sentiment": {"basic": "Bearish"}},
                },
            ],
            "symbol": {"symbol": "AAPL", "title": "Apple Inc."},
        }

        with patch.object(crawler, '_check_compliance', return_value=(True, "OK")):
            with patch.object(crawler, '_wait_for_rate_limit', new_callable=AsyncMock):
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response
                ))
                crawler._client = mock_client

                result = await crawler.crawl("AAPL", limit=10)

                assert result.success is True
                assert len(result.posts) == 2
                assert result.source == "stocktwits"

    @pytest.mark.asyncio
    async def test_crawl_not_found(self):
        """Test crawl with 404 response."""
        crawler = StocktwitsCrawler()

        with patch.object(crawler, '_check_compliance', return_value=(True, "OK")):
            with patch.object(crawler, '_wait_for_rate_limit', new_callable=AsyncMock):
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=MagicMock(status_code=404))
                crawler._client = mock_client

                result = await crawler.crawl("INVALIDXYZ")

                assert result.success is False
                assert "not found" in result.error.lower()


# =============================================================================
# Reddit Crawler Tests
# =============================================================================


class TestRedditCrawler:
    """Tests for RedditCrawler."""

    def test_init(self):
        """Test crawler initialization."""
        crawler = RedditCrawler()
        assert crawler.name == "reddit"
        assert crawler.domain == "reddit.com"
        assert "wallstreetbets" in crawler.subreddits

    def test_init_custom_subreddits(self):
        """Test initialization with custom subreddits."""
        crawler = RedditCrawler(subreddits=["stocks", "investing"])
        assert crawler.subreddits == ["stocks", "investing"]

    def test_format_symbol(self):
        """Test symbol formatting for Reddit."""
        crawler = RedditCrawler()

        # Basic symbol - should add $
        assert crawler._format_symbol("AAPL") == "$AAPL"
        assert crawler._format_symbol("aapl") == "$AAPL"

        # Already has $
        assert crawler._format_symbol("$AAPL") == "$AAPL"

        # With exchange suffix
        assert crawler._format_symbol("AAPL.US") == "$AAPL"

    def test_parse_timestamp(self):
        """Test Unix timestamp parsing."""
        crawler = RedditCrawler()

        # Valid timestamp
        ts = crawler._parse_timestamp(1705312200.0)  # 2024-01-15 10:30:00 UTC
        assert ts is not None
        assert ts.year == 2024

        # Invalid
        assert crawler._parse_timestamp(None) is None

    def test_clean_text(self):
        """Test text cleaning."""
        crawler = RedditCrawler()

        # Normal text
        assert crawler._clean_text("Hello world") == "Hello world"

        # With excessive whitespace
        assert crawler._clean_text("Hello   world\n\ntest") == "Hello world test"

        # With markdown links
        result = crawler._clean_text("Check [this link](https://example.com) out!")
        assert result == "Check this link out!"

    def test_parse_post_basic(self):
        """Test basic post parsing."""
        crawler = RedditCrawler()

        item = {
            "data": {
                "id": "abc123",
                "title": "Why I'm bullish on AAPL",
                "selftext": "Here are my reasons...",
                "author": "redditor123",
                "created_utc": 1705312200.0,
                "score": 100,
                "num_comments": 50,
                "permalink": "/r/wallstreetbets/comments/abc123/",
                "subreddit": "wallstreetbets",
            }
        }

        post = crawler._parse_post(item, "AAPL")
        assert post is not None
        assert post.id == "reddit_abc123"
        assert "bullish" in post.content.lower()
        assert post.author == "redditor123"
        assert post.likes == 100
        assert post.comments == 50
        assert "wallstreetbets" in post.source

    def test_parse_post_removed(self):
        """Test parsing removed/deleted posts."""
        crawler = RedditCrawler()

        # Removed post
        item = {
            "data": {
                "id": "xyz789",
                "title": "[removed]",
                "selftext": "[removed]",
                "author": "[deleted]",
            }
        }

        post = crawler._parse_post(item, "GME")
        assert post is None

    def test_parse_post_no_data(self):
        """Test parsing post with no data."""
        crawler = RedditCrawler()

        assert crawler._parse_post({}, "AAPL") is None
        assert crawler._parse_post({"data": {}}, "AAPL") is None

    @pytest.mark.asyncio
    async def test_crawl_mock(self):
        """Test crawl with mocked HTTP response."""
        crawler = RedditCrawler(subreddits=["wallstreetbets"])

        mock_response = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "post1",
                            "title": "AAPL to the moon!",
                            "author": "user1",
                            "score": 500,
                            "num_comments": 100,
                            "permalink": "/r/wallstreetbets/comments/post1/",
                            "subreddit": "wallstreetbets",
                        }
                    },
                    {
                        "data": {
                            "id": "post2",
                            "title": "Why AAPL will crash",
                            "author": "user2",
                            "score": 200,
                            "num_comments": 50,
                            "permalink": "/r/wallstreetbets/comments/post2/",
                            "subreddit": "wallstreetbets",
                        }
                    },
                ]
            }
        }

        with patch.object(crawler, '_check_compliance', return_value=(True, "OK")):
            with patch.object(crawler, '_wait_for_rate_limit', new_callable=AsyncMock):
                mock_client = AsyncMock()
                mock_client.get = AsyncMock(return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response
                ))
                crawler._client = mock_client

                result = await crawler.crawl("AAPL", limit=10)

                assert result.success is True
                assert len(result.posts) == 2
                assert result.source == "reddit"


# =============================================================================
# Integration Tests
# =============================================================================


class TestSentimentToolIntegration:
    """Tests for SentimentTool integration with new crawlers."""

    def test_crawlers_registered(self):
        """Test that new crawlers are registered."""
        tool = SentimentTool()

        assert "stocktwits" in tool.CRAWLERS
        assert "reddit" in tool.CRAWLERS
        assert "xueqiu" in tool.CRAWLERS
        assert "guba" in tool.CRAWLERS

    def test_get_available_sources(self):
        """Test getting available sources."""
        tool = SentimentTool()
        sources = tool.get_available_sources()

        assert "stocktwits" in sources
        assert "reddit" in sources
        assert len(sources) == 4

    def test_get_crawler_instance(self):
        """Test getting crawler instances."""
        tool = SentimentTool()

        stocktwits = tool._get_crawler("stocktwits")
        assert isinstance(stocktwits, StocktwitsCrawler)

        reddit = tool._get_crawler("reddit")
        assert isinstance(reddit, RedditCrawler)

    def test_get_crawler_unknown(self):
        """Test getting unknown crawler."""
        tool = SentimentTool()

        with pytest.raises(ValueError, match="Unknown source"):
            tool._get_crawler("unknown_source")


# =============================================================================
# Module Import Tests
# =============================================================================


class TestModuleImports:
    """Tests for module imports."""

    def test_import_from_crawlers_package(self):
        """Test importing from crawlers package."""
        from app.agent.tools.builtin.financial.sentiment.crawlers import (
            RedditCrawler,
            StocktwitsCrawler,
            BaseSentimentCrawler,
        )

        assert RedditCrawler is not None
        assert StocktwitsCrawler is not None
        assert BaseSentimentCrawler is not None

    def test_crawler_inheritance(self):
        """Test crawler class inheritance."""
        from app.agent.tools.builtin.financial.sentiment.crawlers import (
            RedditCrawler,
            StocktwitsCrawler,
            BaseSentimentCrawler,
        )

        assert issubclass(RedditCrawler, BaseSentimentCrawler)
        assert issubclass(StocktwitsCrawler, BaseSentimentCrawler)
