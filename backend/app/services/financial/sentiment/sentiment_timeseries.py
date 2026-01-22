"""
SentimentTimeSeriesService - 情绪时序分析服务

提供：
1. 7天情绪趋势数据
2. 热门话题词云
3. 看多/看空观点Top N
4. 情绪分布变化
5. 社交媒体热度指数
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SentimentLevel(str, Enum):
    """情绪级别"""
    VERY_BEARISH = "very_bearish"   # 极度悲观 < -0.6
    BEARISH = "bearish"             # 悲观 -0.6 ~ -0.2
    NEUTRAL = "neutral"             # 中性 -0.2 ~ 0.2
    BULLISH = "bullish"             # 乐观 0.2 ~ 0.6
    VERY_BULLISH = "very_bullish"   # 极度乐观 > 0.6


@dataclass
class DailyMoodPoint:
    """每日情绪数据点"""
    date: date
    score: float                    # -1 to 1
    level: SentimentLevel
    post_count: int                 # 当日帖子数
    bullish_ratio: float            # 看多比例 0-1
    bearish_ratio: float            # 看空比例 0-1
    volume_change: float            # 成交量变化 %

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "score": self.score,
            "level": self.level.value,
            "post_count": self.post_count,
            "bullish_ratio": self.bullish_ratio,
            "bearish_ratio": self.bearish_ratio,
            "volume_change": self.volume_change,
        }


@dataclass
class TrendingTopic:
    """热门话题"""
    topic: str
    count: int                      # 出现次数
    sentiment_score: float          # 话题相关情绪
    trend: str                      # 趋势: up / down / stable
    examples: list[str] = field(default_factory=list)  # 示例帖子

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "count": self.count,
            "sentiment_score": self.sentiment_score,
            "trend": self.trend,
            "examples": self.examples[:3],  # 最多3个示例
        }


@dataclass
class KeyOpinion:
    """关键观点"""
    content: str
    source: str                     # 来源: xueqiu / guba
    author: str
    likes: int
    sentiment: str                  # bullish / bearish
    published_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "content": self.content[:200],  # 截断
            "source": self.source,
            "author": self.author,
            "likes": self.likes,
            "sentiment": self.sentiment,
            "published_at": self.published_at.isoformat(),
        }


@dataclass
class SentimentPulseResult:
    """情绪脉冲分析结果"""
    symbol: str
    name: str
    analysis_date: datetime

    # 当前情绪
    current_score: float            # -1 to 1
    current_level: SentimentLevel
    score_change_24h: float         # 24小时变化
    confidence: float               # 置信度 0-1

    # 时序数据
    daily_moods: list[DailyMoodPoint] = field(default_factory=list)

    # 热门话题
    trending_topics: list[TrendingTopic] = field(default_factory=list)

    # 关键观点
    top_bullish_opinions: list[KeyOpinion] = field(default_factory=list)
    top_bearish_opinions: list[KeyOpinion] = field(default_factory=list)

    # 统计
    total_posts_7d: int = 0
    avg_daily_posts: float = 0.0
    heat_index: float = 0.0         # 热度指数 0-100

    # 来源分布
    source_distribution: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "current_score": self.current_score,
            "current_level": self.current_level.value,
            "score_change_24h": self.score_change_24h,
            "confidence": self.confidence,
            "daily_moods": [m.to_dict() for m in self.daily_moods],
            "trending_topics": [t.to_dict() for t in self.trending_topics],
            "top_bullish_opinions": [o.to_dict() for o in self.top_bullish_opinions],
            "top_bearish_opinions": [o.to_dict() for o in self.top_bearish_opinions],
            "total_posts_7d": self.total_posts_7d,
            "avg_daily_posts": self.avg_daily_posts,
            "heat_index": self.heat_index,
            "source_distribution": self.source_distribution,
        }


class SentimentTimeSeriesService:
    """情绪时序分析服务"""

    def __init__(self):
        self._cache: dict[str, SentimentPulseResult] = {}
        # 股票名称映射
        self._stock_names: dict[str, str] = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000568": "泸州老窖",
            "000651": "格力电器",
            "000333": "美的集团",
            "601318": "中国平安",
            "600036": "招商银行",
            "601166": "兴业银行",
        }

    async def get_sentiment_pulse(
        self,
        symbol: str,
        days: int = 7,
    ) -> SentimentPulseResult:
        """
        获取情绪脉冲数据

        Args:
            symbol: 股票代码
            days: 分析天数 (默认7天)
        """
        cache_key = f"{symbol}_{days}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # 检查缓存是否过期（30分钟）
            if (datetime.now() - cached.analysis_date).total_seconds() < 1800:
                return cached

        try:
            # 生成时序数据
            daily_moods = self._generate_daily_moods(symbol, days)

            # 计算当前情绪
            current_mood = daily_moods[-1] if daily_moods else None
            prev_mood = daily_moods[-2] if len(daily_moods) >= 2 else None

            current_score = current_mood.score if current_mood else 0.0
            score_change = (current_score - prev_mood.score) if prev_mood else 0.0

            # 生成热门话题
            trending_topics = self._generate_trending_topics(symbol)

            # 生成关键观点
            bullish_opinions = self._generate_opinions(symbol, "bullish")
            bearish_opinions = self._generate_opinions(symbol, "bearish")

            # 统计
            total_posts = sum(m.post_count for m in daily_moods)
            avg_posts = total_posts / days if days > 0 else 0

            # 热度指数计算
            heat_index = self._calculate_heat_index(
                total_posts,
                avg_posts,
                current_score,
            )

            result = SentimentPulseResult(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                analysis_date=datetime.now(),
                current_score=round(current_score, 2),
                current_level=self._score_to_level(current_score),
                score_change_24h=round(score_change, 2),
                confidence=0.75,  # Mock置信度
                daily_moods=daily_moods,
                trending_topics=trending_topics,
                top_bullish_opinions=bullish_opinions,
                top_bearish_opinions=bearish_opinions,
                total_posts_7d=total_posts,
                avg_daily_posts=round(avg_posts, 1),
                heat_index=round(heat_index, 1),
                source_distribution={
                    "xueqiu": int(total_posts * 0.6),
                    "guba": int(total_posts * 0.4),
                },
            )

            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Failed to get sentiment pulse for {symbol}: {e}")
            return SentimentPulseResult(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                analysis_date=datetime.now(),
                current_score=0.0,
                current_level=SentimentLevel.NEUTRAL,
                score_change_24h=0.0,
                confidence=0.0,
            )

    def _generate_daily_moods(self, symbol: str, days: int) -> list[DailyMoodPoint]:
        """生成每日情绪数据 (Mock)"""
        import random

        moods = []
        today = date.today()

        # 基于股票代码生成不同的情绪模式
        base_score = 0.0
        if symbol == "600519":  # 茅台
            base_score = 0.3  # 偏乐观
        elif symbol == "000858":  # 五粮液
            base_score = 0.15
        elif symbol == "601318":  # 平安
            base_score = -0.1  # 稍微偏悲观

        for i in range(days):
            day = today - timedelta(days=days - 1 - i)

            # 生成波动的情绪分数
            random.seed(hash(f"{symbol}_{day}"))
            noise = random.uniform(-0.3, 0.3)
            trend = 0.02 * i  # 轻微上升趋势
            score = max(-1, min(1, base_score + noise + trend))

            # 根据分数计算看多/看空比例
            bullish_ratio = (score + 1) / 2  # 转换到 0-1
            bearish_ratio = 1 - bullish_ratio

            # 帖子数量随机
            post_count = random.randint(50, 200)

            moods.append(DailyMoodPoint(
                date=day,
                score=round(score, 2),
                level=self._score_to_level(score),
                post_count=post_count,
                bullish_ratio=round(bullish_ratio, 2),
                bearish_ratio=round(bearish_ratio, 2),
                volume_change=round(random.uniform(-20, 30), 1),
            ))

        return moods

    def _generate_trending_topics(self, symbol: str) -> list[TrendingTopic]:
        """生成热门话题 (Mock)"""
        topics_map: dict[str, list[dict[str, Any]]] = {
            "600519": [
                {"topic": "提价预期", "count": 156, "score": 0.6, "trend": "up"},
                {"topic": "渠道库存", "count": 98, "score": 0.2, "trend": "stable"},
                {"topic": "电商放量", "count": 87, "score": 0.4, "trend": "up"},
                {"topic": "业绩增速", "count": 76, "score": 0.5, "trend": "stable"},
                {"topic": "估值修复", "count": 65, "score": 0.3, "trend": "down"},
            ],
            "000858": [
                {"topic": "高端酒", "count": 120, "score": 0.4, "trend": "up"},
                {"topic": "渠道改革", "count": 89, "score": 0.2, "trend": "stable"},
                {"topic": "经典五粮液", "count": 67, "score": 0.5, "trend": "up"},
            ],
            "601318": [
                {"topic": "寿险改革", "count": 145, "score": 0.1, "trend": "stable"},
                {"topic": "NBV增速", "count": 98, "score": -0.2, "trend": "down"},
                {"topic": "分红预期", "count": 87, "score": 0.4, "trend": "up"},
                {"topic": "地产敞口", "count": 76, "score": -0.5, "trend": "down"},
            ],
        }

        topics_data = topics_map.get(symbol, [
            {"topic": "业绩预期", "count": 100, "score": 0.3, "trend": "stable"},
            {"topic": "估值水平", "count": 80, "score": 0.1, "trend": "stable"},
        ])

        return [
            TrendingTopic(
                topic=t["topic"],
                count=t["count"],
                sentiment_score=t["score"],
                trend=t["trend"],
                examples=[
                    f"关于{t['topic']}的讨论内容示例1",
                    f"关于{t['topic']}的讨论内容示例2",
                ],
            )
            for t in topics_data
        ]

    def _generate_opinions(
        self,
        symbol: str,
        sentiment: str,
        top_n: int = 5,
    ) -> list[KeyOpinion]:
        """生成关键观点 (Mock)"""
        bullish_opinions: dict[str, list[dict[str, Any]]] = {
            "600519": [
                {"content": "茅台提价预期强烈，明年业绩增速有望超预期", "likes": 523, "author": "价值投资者"},
                {"content": "渠道库存处于历史低位，春节旺季可期", "likes": 412, "author": "行业研究员"},
                {"content": "批价持续上涨，需求韧性超预期", "likes": 389, "author": "白酒老司机"},
                {"content": "茅台是确定性最高的消费龙头", "likes": 356, "author": "长期持有者"},
                {"content": "外资持续加仓，估值仍有修复空间", "likes": 298, "author": "量化分析师"},
            ],
            "601318": [
                {"content": "寿险改革见效，NBV拐点已现", "likes": 234, "author": "保险分析师"},
                {"content": "分红率提升预期，高股息策略首选", "likes": 198, "author": "稳健投资者"},
            ],
        }

        bearish_opinions: dict[str, list[dict[str, Any]]] = {
            "600519": [
                {"content": "消费降级趋势下，高端白酒承压", "likes": 187, "author": "宏观分析师"},
                {"content": "估值过高，需要消化泡沫", "likes": 156, "author": "空头大师"},
                {"content": "年轻人不喝白酒，长期逻辑存疑", "likes": 134, "author": "趋势观察者"},
            ],
            "601318": [
                {"content": "地产敞口仍然是最大风险点", "likes": 312, "author": "风控专家"},
                {"content": "利差收窄压制保险股估值", "likes": 267, "author": "宏观分析师"},
                {"content": "行业增速放缓是不争事实", "likes": 223, "author": "行业研究员"},
            ],
        }

        opinions_source = bullish_opinions if sentiment == "bullish" else bearish_opinions
        opinions_data = opinions_source.get(symbol, [
            {"content": f"关于该股票的{sentiment}观点", "likes": 100, "author": "分析师"},
        ])

        return [
            KeyOpinion(
                content=o["content"],
                source="xueqiu" if i % 2 == 0 else "guba",
                author=o["author"],
                likes=o["likes"],
                sentiment=sentiment,
                published_at=datetime.now() - timedelta(hours=i * 6),
            )
            for i, o in enumerate(opinions_data[:top_n])
        ]

    def _score_to_level(self, score: float) -> SentimentLevel:
        """将分数转换为情绪级别"""
        if score < -0.6:
            return SentimentLevel.VERY_BEARISH
        if score < -0.2:
            return SentimentLevel.BEARISH
        if score < 0.2:
            return SentimentLevel.NEUTRAL
        if score < 0.6:
            return SentimentLevel.BULLISH
        return SentimentLevel.VERY_BULLISH

    def _calculate_heat_index(
        self,
        total_posts: int,
        avg_posts: float,
        sentiment_score: float,
    ) -> float:
        """
        计算热度指数 (0-100)

        基于：
        - 帖子数量
        - 情绪极端程度
        - 趋势变化
        """
        # 基于帖子数量的基础热度
        base_heat = min(50, total_posts / 10)

        # 情绪极端程度加成
        sentiment_boost = abs(sentiment_score) * 30

        # 活跃度加成
        activity_boost = min(20, avg_posts / 5)

        return min(100, base_heat + sentiment_boost + activity_boost)


# 单例
_sentiment_timeseries_service: SentimentTimeSeriesService | None = None


def get_sentiment_timeseries_service() -> SentimentTimeSeriesService:
    """获取情绪时序服务单例"""
    global _sentiment_timeseries_service
    if _sentiment_timeseries_service is None:
        _sentiment_timeseries_service = SentimentTimeSeriesService()
    return _sentiment_timeseries_service
