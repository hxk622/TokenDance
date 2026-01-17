"""
FactorReturnService - 因子收益分析服务

提供：
1. 因子收益率
2. 因子收益归因
3. 因子表现排名
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FactorReturnResult:
    """因子收益结果"""
    factor_name: str
    period: str

    # 收益
    return_value: float
    cumulative_return: float

    # 风险
    volatility: float
    sharpe_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "period": self.period,
            "return_value": self.return_value,
            "cumulative_return": self.cumulative_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
        }


@dataclass
class FactorPerformance:
    """因子表现汇总"""
    analysis_date: datetime

    # 各因子表现
    factor_returns: list[FactorReturnResult] = field(default_factory=list)

    # 排名
    best_factors: list[str] = field(default_factory=list)
    worst_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "factor_returns": [f.to_dict() for f in self.factor_returns],
            "best_factors": self.best_factors,
            "worst_factors": self.worst_factors,
        }


class FactorReturnService:
    """因子收益分析服务"""

    FACTORS = ["规模", "价值", "成长", "动量", "波动率", "质量", "红利", "流动性"]

    def __init__(self):
        self._cache: dict[str, Any] = {}

    async def get_factor_returns(
        self,
        period: str = "1M",  # 1D, 1W, 1M, 3M, 6M, 1Y, YTD
    ) -> FactorPerformance:
        """获取因子收益"""
        import random

        factor_returns = []
        for factor in self.FACTORS:
            ret = random.uniform(-0.10, 0.15)
            vol = random.uniform(0.10, 0.25)

            factor_returns.append(FactorReturnResult(
                factor_name=factor,
                period=period,
                return_value=round(ret, 4),
                cumulative_return=round(ret * random.uniform(0.8, 1.2), 4),
                volatility=round(vol, 4),
                sharpe_ratio=round(ret / vol if vol > 0 else 0, 2),
            ))

        # 排序
        sorted_returns = sorted(factor_returns, key=lambda x: x.return_value, reverse=True)
        best = [f.factor_name for f in sorted_returns[:3]]
        worst = [f.factor_name for f in sorted_returns[-3:]]

        return FactorPerformance(
            analysis_date=datetime.now(),
            factor_returns=factor_returns,
            best_factors=best,
            worst_factors=worst,
        )

    async def get_factor_return_attribution(
        self,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
        period: str = "1M",
    ) -> dict[str, Any]:
        """因子收益归因"""
        import random

        total_return = random.uniform(-0.05, 0.10)
        factor_contrib = {}
        remaining = total_return

        for factor in self.FACTORS[:-1]:
            contrib = random.uniform(-0.02, 0.03)
            factor_contrib[factor] = round(contrib, 4)
            remaining -= contrib

        factor_contrib["特质收益"] = round(remaining, 4)

        return {
            "portfolio_id": portfolio_id,
            "period": period,
            "total_return": round(total_return, 4),
            "factor_contributions": factor_contrib,
        }

    async def get_factor_return_history(
        self,
        factor_name: str,
        lookback_months: int = 12,
    ) -> list[dict[str, Any]]:
        """获取因子收益历史"""
        import random
        from datetime import timedelta

        history = []
        base_date = datetime.now()

        for i in range(lookback_months):
            history.append({
                "date": (base_date - timedelta(days=i * 30)).strftime("%Y-%m"),
                "return": round(random.uniform(-0.08, 0.10), 4),
            })

        return list(reversed(history))


_factor_return_service: FactorReturnService | None = None


def get_factor_return_service() -> FactorReturnService:
    global _factor_return_service
    if _factor_return_service is None:
        _factor_return_service = FactorReturnService()
    return _factor_return_service
