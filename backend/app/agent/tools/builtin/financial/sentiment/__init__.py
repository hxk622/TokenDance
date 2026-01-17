"""
Sentiment Analysis Tools for TokenDance.

This module provides tools for:
- Crawling financial sentiment from whitelisted sources
- Analyzing text sentiment using LLM
- Aggregating sentiment data

Usage:
    from app.agent.tools.builtin.financial.sentiment import SentimentTool

    tool = SentimentTool()
    result = await tool.analyze("600519", sources=["xueqiu", "guba"])
"""

from app.agent.tools.builtin.financial.sentiment.analyzer import (
    SentimentAnalysisResult,
    SentimentAnalyzer,
)
from app.agent.tools.builtin.financial.sentiment.crawlers.base import (
    BaseSentimentCrawler,
    CrawlResult,
    SentimentPost,
)
from app.agent.tools.builtin.financial.sentiment.crawlers.guba import GubaCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.xueqiu import XueqiuCrawler
from app.agent.tools.builtin.financial.sentiment.sentiment_tool import (
    SentimentResult,
    SentimentTool,
    get_sentiment_tool,
)

__all__ = [
    "SentimentTool",
    "SentimentResult",
    "get_sentiment_tool",
    "SentimentAnalyzer",
    "SentimentAnalysisResult",
    "BaseSentimentCrawler",
    "SentimentPost",
    "CrawlResult",
    "XueqiuCrawler",
    "GubaCrawler",
]
