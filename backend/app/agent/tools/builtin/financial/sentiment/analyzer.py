"""
Sentiment analyzer using LLM.

Analyzes financial text sentiment using Claude API.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any

from app.agent.tools.builtin.financial.sentiment.crawlers.base import SentimentPost


@dataclass
class SentimentAnalysisResult:
    """Result of sentiment analysis."""

    overall_score: float = 0.0  # -1 (bearish) to 1 (bullish)
    overall_label: str = "neutral"  # bullish / bearish / neutral
    confidence: float = 0.0  # 0 to 1

    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0

    key_bullish_points: list[str] = field(default_factory=list)
    key_bearish_points: list[str] = field(default_factory=list)
    trending_topics: list[str] = field(default_factory=list)

    analyzed_count: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_score": self.overall_score,
            "overall_label": self.overall_label,
            "confidence": self.confidence,
            "distribution": {
                "bullish": self.bullish_count,
                "bearish": self.bearish_count,
                "neutral": self.neutral_count,
            },
            "key_bullish_points": self.key_bullish_points,
            "key_bearish_points": self.key_bearish_points,
            "trending_topics": self.trending_topics,
            "analyzed_count": self.analyzed_count,
            "error": self.error,
        }


SENTIMENT_PROMPT = """你是一个金融情绪分析专家。请分析以下来自股票论坛的帖子内容，判断整体市场情绪。

股票代码: {symbol}
帖子数量: {count}

帖子内容:
{posts}

请分析上述帖子，返回JSON格式的分析结果:
{{
    "overall_sentiment": "bullish" 或 "bearish" 或 "neutral",
    "sentiment_score": -1到1之间的数值 (负数看空，正数看多),
    "confidence": 0到1之间的置信度,
    "bullish_count": 看多帖子数量,
    "bearish_count": 看空帖子数量,
    "neutral_count": 中性帖子数量,
    "key_bullish_points": ["看多的主要观点1", "看多的主要观点2"],
    "key_bearish_points": ["看空的主要观点1", "看空的主要观点2"],
    "trending_topics": ["热门话题1", "热门话题2"],
    "individual_sentiments": [
        {{"id": "帖子ID", "sentiment": "bullish/bearish/neutral", "score": 0.5}}
    ]
}}

只返回JSON，不要其他内容。"""


class SentimentAnalyzer:
    """
    Sentiment analyzer using OpenRouter API.

    Analyzes batches of posts to determine overall market sentiment.
    统一使用 OpenRouter 免费模型。
    """

    def __init__(self, model: str = "xiaomi/mimo-v2-flash:free"):
        """
        Initialize analyzer.

        Args:
            model: OpenRouter model to use. Default: xiaomi/mimo-v2-flash:free (fast & free)
        """
        self.model = model
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")

    async def analyze_posts(
        self,
        posts: list[SentimentPost],
        symbol: str = "",
    ) -> SentimentAnalysisResult:
        """
        Analyze sentiment of multiple posts.

        Args:
            posts: List of posts to analyze
            symbol: Stock symbol for context

        Returns:
            SentimentAnalysisResult
        """
        if not posts:
            return SentimentAnalysisResult(
                error="No posts to analyze",
                analyzed_count=0,
            )

        if not self.api_key:
            # Fallback to keyword-based analysis
            return self._keyword_analysis(posts, symbol)

        try:
            # Format posts for prompt
            posts_text = self._format_posts(posts)

            prompt = SENTIMENT_PROMPT.format(
                symbol=symbol or "未知",
                count=len(posts),
                posts=posts_text,
            )

            # Call OpenRouter API
            import httpx
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://tokendance.ai",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 2000,
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Parse response
            response_text = data["choices"][0]["message"]["content"]

            # Extract JSON from response
            result = self._parse_llm_response(response_text, posts)
            result.analyzed_count = len(posts)

            return result

        except Exception as e:
            # Fallback to keyword analysis
            result = self._keyword_analysis(posts, symbol)
            result.error = f"LLM analysis failed: {str(e)}, using keyword fallback"
            return result

    def _format_posts(self, posts: list[SentimentPost], max_chars: int = 8000) -> str:
        """Format posts for LLM prompt."""
        lines = []
        total_chars = 0

        for _i, post in enumerate(posts):
            # Truncate long posts
            content = post.content[:500] if len(post.content) > 500 else post.content

            line = f"[{post.id}] {content}"
            if post.likes > 0:
                line += f" (👍{post.likes})"

            if total_chars + len(line) > max_chars:
                break

            lines.append(line)
            total_chars += len(line)

        return "\n".join(lines)

    def _parse_llm_response(
        self,
        response: str,
        posts: list[SentimentPost]
    ) -> SentimentAnalysisResult:
        """Parse LLM response and update posts."""
        try:
            # Try to parse JSON
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            data = json.loads(response.strip())

            result = SentimentAnalysisResult(
                overall_score=float(data.get("sentiment_score", 0)),
                overall_label=data.get("overall_sentiment", "neutral"),
                confidence=float(data.get("confidence", 0.5)),
                bullish_count=int(data.get("bullish_count", 0)),
                bearish_count=int(data.get("bearish_count", 0)),
                neutral_count=int(data.get("neutral_count", 0)),
                key_bullish_points=data.get("key_bullish_points", []),
                key_bearish_points=data.get("key_bearish_points", []),
                trending_topics=data.get("trending_topics", []),
            )

            # Update individual posts
            individual = data.get("individual_sentiments", [])
            sentiment_map = {str(item.get("id", "")): item for item in individual}

            for post in posts:
                if post.id in sentiment_map:
                    item = sentiment_map[post.id]
                    post.sentiment_label = item.get("sentiment", "neutral")
                    post.sentiment_score = float(item.get("score", 0))

            return result

        except json.JSONDecodeError:
            # Parse failed, use keyword fallback
            return self._keyword_analysis(posts, "")

    def _keyword_analysis(
        self,
        posts: list[SentimentPost],
        symbol: str
    ) -> SentimentAnalysisResult:
        """
        Fallback keyword-based sentiment analysis.

        Used when LLM is not available.
        """
        # Bullish keywords
        bullish_words = [
            "利好", "突破", "放量", "主力", "龙头", "翻倍", "涨停", "拉升",
            "低估", "价值洼地", "长期看好", "逢低买入", "买入", "加仓", "看多",
            "牛市", "反弹", "起飞", "爆发", "暴涨", "机会", "底部",
        ]

        # Bearish keywords
        bearish_words = [
            "利空", "暴跌", "出货", "割肉", "套牢", "爆雷", "跌停", "崩盘",
            "高估", "泡沫", "风险", "减仓", "清仓", "看空", "卖出",
            "熊市", "跳水", "砸盘", "出逃", "危险", "顶部",
        ]

        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        for post in posts:
            text = post.content

            bull_score = sum(1 for w in bullish_words if w in text)
            bear_score = sum(1 for w in bearish_words if w in text)

            if bull_score > bear_score:
                post.sentiment_label = "bullish"
                post.sentiment_score = min(1.0, bull_score * 0.2)
                bullish_count += 1
            elif bear_score > bull_score:
                post.sentiment_label = "bearish"
                post.sentiment_score = max(-1.0, -bear_score * 0.2)
                bearish_count += 1
            else:
                post.sentiment_label = "neutral"
                post.sentiment_score = 0
                neutral_count += 1

        total = len(posts)
        if total == 0:
            return SentimentAnalysisResult(error="No posts")

        # Calculate overall score
        overall_score = (bullish_count - bearish_count) / total

        if overall_score > 0.2:
            overall_label = "bullish"
        elif overall_score < -0.2:
            overall_label = "bearish"
        else:
            overall_label = "neutral"

        return SentimentAnalysisResult(
            overall_score=overall_score,
            overall_label=overall_label,
            confidence=0.5,  # Lower confidence for keyword analysis
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=neutral_count,
            analyzed_count=total,
        )

    async def analyze_single(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment of a single text.

        Returns:
            Dict with sentiment_label, sentiment_score
        """
        post = SentimentPost(id="single", content=text)
        result = await self.analyze_posts([post])

        return {
            "sentiment_label": post.sentiment_label or "neutral",
            "sentiment_score": post.sentiment_score or 0,
            "overall": result.overall_label,
        }
