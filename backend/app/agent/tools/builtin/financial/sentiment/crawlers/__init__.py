"""Sentiment crawlers for different financial platforms."""

from app.agent.tools.builtin.financial.sentiment.crawlers.base import BaseSentimentCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.guba import GubaCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.reddit import RedditCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.stocktwits import StocktwitsCrawler
from app.agent.tools.builtin.financial.sentiment.crawlers.xueqiu import XueqiuCrawler

__all__ = [
    "BaseSentimentCrawler",
    "XueqiuCrawler",
    "GubaCrawler",
    "RedditCrawler",
    "StocktwitsCrawler",
]
