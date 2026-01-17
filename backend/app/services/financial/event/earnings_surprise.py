"""
EarningsSurpriseService - 业绩超预期/不及预期分析服务

提供：
1. 业绩超预期/不及预期识别
2. 历史业绩偏离分析
3. 市场预期跟踪
4. 超预期后股价反应分析
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SurpriseType(str, Enum):
    """预期偏离类型"""
    BEAT = "beat"           # 超预期
    MEET = "meet"           # 符合预期
    MISS = "miss"           # 不及预期
    STRONG_BEAT = "strong_beat"   # 大幅超预期
    STRONG_MISS = "strong_miss"   # 大幅不及预期


class MetricType(str, Enum):
    """指标类型"""
    REVENUE = "revenue"
    NET_PROFIT = "net_profit"
    EPS = "eps"
    GROSS_MARGIN = "gross_margin"
    OPERATING_PROFIT = "operating_profit"


@dataclass
class EarningsSurprise:
    """业绩预期偏离"""
    symbol: str
    name: str
    report_date: date
    period: str  # 报告期，如 "2024Q3"
    metric: MetricType
    actual_value: float
    consensus_estimate: float
    surprise_pct: float  # 偏离百分比
    surprise_type: SurpriseType

    # 股价反应
    price_change_1d: float | None = None  # 发布后1日涨跌幅
    price_change_5d: float | None = None  # 发布后5日涨跌幅

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "report_date": self.report_date.isoformat(),
            "period": self.period,
            "metric": self.metric.value,
            "actual_value": self.actual_value,
            "consensus_estimate": self.consensus_estimate,
            "surprise_pct": self.surprise_pct,
            "surprise_type": self.surprise_type.value,
            "price_change_1d": self.price_change_1d,
            "price_change_5d": self.price_change_5d,
        }


@dataclass
class ConsensusEstimate:
    """市场一致预期"""
    symbol: str
    period: str
    metric: MetricType
    mean_estimate: float
    median_estimate: float
    high_estimate: float
    low_estimate: float
    num_analysts: int
    estimate_date: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "period": self.period,
            "metric": self.metric.value,
            "mean_estimate": self.mean_estimate,
            "median_estimate": self.median_estimate,
            "high_estimate": self.high_estimate,
            "low_estimate": self.low_estimate,
            "num_analysts": self.num_analysts,
            "estimate_date": self.estimate_date.isoformat(),
        }


@dataclass
class EarningsSurpriseResult:
    """业绩超预期分析结果"""
    symbol: str
    name: str
    analysis_date: datetime
    surprises: list[EarningsSurprise] = field(default_factory=list)
    current_estimates: list[ConsensusEstimate] = field(default_factory=list)

    # 统计
    beat_rate: float = 0.0  # 历史超预期比率
    avg_surprise_pct: float = 0.0  # 平均超预期幅度

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "surprises": [s.to_dict() for s in self.surprises],
            "current_estimates": [e.to_dict() for e in self.current_estimates],
            "beat_rate": self.beat_rate,
            "avg_surprise_pct": self.avg_surprise_pct,
        }


class EarningsSurpriseService:
    """业绩超预期分析服务"""

    def __init__(self):
        self._cache: dict[str, EarningsSurpriseResult] = {}

    async def analyze_earnings_surprise(
        self,
        symbol: str,
        lookback_periods: int = 8,
    ) -> EarningsSurpriseResult:
        """
        分析业绩超预期情况

        Args:
            symbol: 股票代码
            lookback_periods: 回看期数 (季度)
        """
        if symbol in self._cache:
            return self._cache[symbol]

        try:
            # 获取历史业绩偏离
            surprises = await self._get_historical_surprises(symbol, lookback_periods)

            # 获取当前市场预期
            estimates = await self._get_current_estimates(symbol)

            # 计算统计
            beat_count = sum(1 for s in surprises if s.surprise_type in [SurpriseType.BEAT, SurpriseType.STRONG_BEAT])
            beat_rate = beat_count / len(surprises) if surprises else 0
            avg_surprise = sum(s.surprise_pct for s in surprises) / len(surprises) if surprises else 0

            result = EarningsSurpriseResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                surprises=surprises,
                current_estimates=estimates,
                beat_rate=round(beat_rate, 2),
                avg_surprise_pct=round(avg_surprise, 2),
            )

            self._cache[symbol] = result
            return result

        except Exception as e:
            logger.error(f"Failed to analyze earnings surprise for {symbol}: {e}")
            return EarningsSurpriseResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )

    async def get_recent_surprises(
        self,
        surprise_type: SurpriseType | None = None,
        limit: int = 20,
    ) -> list[EarningsSurprise]:
        """获取近期业绩超预期/不及预期股票"""
        surprises = await self._get_market_surprises()

        if surprise_type:
            surprises = [s for s in surprises if s.surprise_type == surprise_type]

        # 按报告日期排序
        surprises.sort(key=lambda x: x.report_date, reverse=True)
        return surprises[:limit]

    async def get_upcoming_earnings(self, days: int = 30) -> list[dict[str, Any]]:
        """获取即将发布业绩的公司"""
        return await self._get_earnings_calendar(days)

    async def _get_historical_surprises(
        self,
        symbol: str,
        lookback_periods: int,
    ) -> list[EarningsSurprise]:
        """获取历史业绩偏离"""
        import random
        from datetime import timedelta

        surprises = []
        base_date = date.today()

        for i in range(lookback_periods):
            # 生成季度报告期
            quarter = (base_date.month - 1) // 3
            year = base_date.year - (i // 4)
            q = (quarter - i % 4) % 4 + 1
            if q > quarter + 1:
                year -= 1
            period = f"{year}Q{q}"

            # Mock 数据
            actual = random.uniform(1, 10)
            estimate = actual * random.uniform(0.85, 1.15)
            surprise_pct = (actual - estimate) / estimate * 100

            # 判断类型
            if surprise_pct > 15:
                surprise_type = SurpriseType.STRONG_BEAT
            elif surprise_pct > 3:
                surprise_type = SurpriseType.BEAT
            elif surprise_pct > -3:
                surprise_type = SurpriseType.MEET
            elif surprise_pct > -15:
                surprise_type = SurpriseType.MISS
            else:
                surprise_type = SurpriseType.STRONG_MISS

            surprises.append(EarningsSurprise(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                report_date=base_date - timedelta(days=i * 90),
                period=period,
                metric=MetricType.NET_PROFIT,
                actual_value=round(actual, 2),
                consensus_estimate=round(estimate, 2),
                surprise_pct=round(surprise_pct, 2),
                surprise_type=surprise_type,
                price_change_1d=round(random.uniform(-5, 8), 2),
                price_change_5d=round(random.uniform(-8, 12), 2),
            ))

        return surprises

    async def _get_current_estimates(self, symbol: str) -> list[ConsensusEstimate]:
        """获取当前市场预期"""
        import random

        estimates = []
        year = date.today().year

        for q in range(1, 5):
            period = f"{year}Q{q}"
            mean_est = random.uniform(1, 10)

            estimates.append(ConsensusEstimate(
                symbol=symbol,
                period=period,
                metric=MetricType.NET_PROFIT,
                mean_estimate=round(mean_est, 2),
                median_estimate=round(mean_est * random.uniform(0.98, 1.02), 2),
                high_estimate=round(mean_est * 1.2, 2),
                low_estimate=round(mean_est * 0.8, 2),
                num_analysts=random.randint(5, 30),
                estimate_date=date.today(),
            ))

        return estimates

    async def _get_market_surprises(self) -> list[EarningsSurprise]:
        """获取市场最新业绩偏离"""
        import random
        from datetime import timedelta

        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
            ("600036", "招商银行"), ("000333", "美的集团"),
        ]

        surprises = []
        for symbol, name in stocks:
            actual = random.uniform(1, 10)
            estimate = actual * random.uniform(0.85, 1.15)
            surprise_pct = (actual - estimate) / estimate * 100

            if surprise_pct > 15:
                surprise_type = SurpriseType.STRONG_BEAT
            elif surprise_pct > 3:
                surprise_type = SurpriseType.BEAT
            elif surprise_pct > -3:
                surprise_type = SurpriseType.MEET
            elif surprise_pct > -15:
                surprise_type = SurpriseType.MISS
            else:
                surprise_type = SurpriseType.STRONG_MISS

            surprises.append(EarningsSurprise(
                symbol=symbol,
                name=name,
                report_date=date.today() - timedelta(days=random.randint(1, 30)),
                period=f"{date.today().year}Q3",
                metric=MetricType.NET_PROFIT,
                actual_value=round(actual, 2),
                consensus_estimate=round(estimate, 2),
                surprise_pct=round(surprise_pct, 2),
                surprise_type=surprise_type,
            ))

        return surprises

    async def _get_earnings_calendar(self, days: int) -> list[dict[str, Any]]:
        """获取业绩日历"""
        import random
        from datetime import timedelta

        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
            ("600036", "招商银行"), ("601318", "中国平安"),
        ]

        calendar = []
        for symbol, name in stocks:
            calendar.append({
                "symbol": symbol,
                "name": name,
                "expected_date": (date.today() + timedelta(days=random.randint(1, days))).isoformat(),
                "period": f"{date.today().year}Q4",
                "estimated_eps": round(random.uniform(1, 5), 2),
            })

        return calendar

    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "600036": "招商银行",
            "000333": "美的集团",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_earnings_surprise_service: EarningsSurpriseService | None = None


def get_earnings_surprise_service() -> EarningsSurpriseService:
    """获取业绩超预期服务单例"""
    global _earnings_surprise_service
    if _earnings_surprise_service is None:
        _earnings_surprise_service = EarningsSurpriseService()
    return _earnings_surprise_service
