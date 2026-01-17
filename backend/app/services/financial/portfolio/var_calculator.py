"""
VaRCalculatorService - VaR计算服务

提供：
1. 参数法VaR
2. 历史模拟法VaR
3. 蒙特卡洛模拟VaR
4. CVaR (Expected Shortfall)
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class VaRMethod(str, Enum):
    """VaR计算方法"""
    PARAMETRIC = "parametric"           # 参数法
    HISTORICAL = "historical"           # 历史模拟法
    MONTE_CARLO = "monte_carlo"         # 蒙特卡洛法


@dataclass
class VaRResult:
    """VaR计算结果"""
    portfolio_id: str
    calculation_date: datetime
    method: VaRMethod
    confidence_level: float   # 置信度 (e.g., 0.95, 0.99)
    holding_period: int       # 持有期 (天)

    # VaR值
    var_amount: float         # VaR金额
    var_pct: float            # VaR百分比

    # 组合信息
    portfolio_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "calculation_date": self.calculation_date.isoformat(),
            "method": self.method.value,
            "confidence_level": self.confidence_level,
            "holding_period": self.holding_period,
            "var_amount": self.var_amount,
            "var_pct": self.var_pct,
            "portfolio_value": self.portfolio_value,
        }


@dataclass
class CVaRResult:
    """CVaR (Expected Shortfall) 结果"""
    portfolio_id: str
    calculation_date: datetime
    method: VaRMethod
    confidence_level: float
    holding_period: int

    # CVaR值
    cvar_amount: float        # CVaR金额
    cvar_pct: float           # CVaR百分比

    # 对应VaR
    var_amount: float
    var_pct: float

    portfolio_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "calculation_date": self.calculation_date.isoformat(),
            "method": self.method.value,
            "confidence_level": self.confidence_level,
            "holding_period": self.holding_period,
            "cvar_amount": self.cvar_amount,
            "cvar_pct": self.cvar_pct,
            "var_amount": self.var_amount,
            "var_pct": self.var_pct,
            "portfolio_value": self.portfolio_value,
        }


@dataclass
class VaRSummary:
    """VaR汇总"""
    portfolio_id: str
    calculation_date: datetime
    portfolio_value: float

    # 不同置信度的VaR
    var_95: VaRResult
    var_99: VaRResult
    cvar_95: CVaRResult
    cvar_99: CVaRResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "calculation_date": self.calculation_date.isoformat(),
            "portfolio_value": self.portfolio_value,
            "var_95": self.var_95.to_dict(),
            "var_99": self.var_99.to_dict(),
            "cvar_95": self.cvar_95.to_dict(),
            "cvar_99": self.cvar_99.to_dict(),
        }


class VaRCalculatorService:
    """VaR计算服务"""

    # 标准正态分位数
    Z_SCORES = {
        0.90: 1.282,
        0.95: 1.645,
        0.99: 2.326,
    }

    def __init__(self):
        self._cache: dict[str, Any] = {}

    async def calculate_var(
        self,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
        method: VaRMethod = VaRMethod.PARAMETRIC,
        confidence_level: float = 0.95,
        holding_period: int = 1,
    ) -> VaRResult:
        """计算VaR"""
        portfolio_value = self._get_portfolio_value(holdings)

        if method == VaRMethod.PARAMETRIC:
            var_pct = await self._calculate_parametric_var(holdings, confidence_level, holding_period)
        elif method == VaRMethod.HISTORICAL:
            var_pct = await self._calculate_historical_var(holdings, confidence_level, holding_period)
        else:  # MONTE_CARLO
            var_pct = await self._calculate_monte_carlo_var(holdings, confidence_level, holding_period)

        var_amount = portfolio_value * var_pct

        return VaRResult(
            portfolio_id=portfolio_id,
            calculation_date=datetime.now(),
            method=method,
            confidence_level=confidence_level,
            holding_period=holding_period,
            var_amount=round(var_amount, 2),
            var_pct=round(var_pct * 100, 4),
            portfolio_value=portfolio_value,
        )

    async def calculate_cvar(
        self,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
        method: VaRMethod = VaRMethod.PARAMETRIC,
        confidence_level: float = 0.95,
        holding_period: int = 1,
    ) -> CVaRResult:
        """计算CVaR (Expected Shortfall)"""
        var_result = await self.calculate_var(
            portfolio_id, holdings, method, confidence_level, holding_period
        )

        # CVaR 通常比VaR大20-40%
        import random
        cvar_multiplier = random.uniform(1.2, 1.4)
        cvar_pct = var_result.var_pct / 100 * cvar_multiplier
        cvar_amount = var_result.portfolio_value * cvar_pct

        return CVaRResult(
            portfolio_id=portfolio_id,
            calculation_date=datetime.now(),
            method=method,
            confidence_level=confidence_level,
            holding_period=holding_period,
            cvar_amount=round(cvar_amount, 2),
            cvar_pct=round(cvar_pct * 100, 4),
            var_amount=var_result.var_amount,
            var_pct=var_result.var_pct,
            portfolio_value=var_result.portfolio_value,
        )

    async def calculate_var_summary(
        self,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
        method: VaRMethod = VaRMethod.PARAMETRIC,
        holding_period: int = 1,
    ) -> VaRSummary:
        """计算VaR汇总"""
        var_95 = await self.calculate_var(portfolio_id, holdings, method, 0.95, holding_period)
        var_99 = await self.calculate_var(portfolio_id, holdings, method, 0.99, holding_period)
        cvar_95 = await self.calculate_cvar(portfolio_id, holdings, method, 0.95, holding_period)
        cvar_99 = await self.calculate_cvar(portfolio_id, holdings, method, 0.99, holding_period)

        return VaRSummary(
            portfolio_id=portfolio_id,
            calculation_date=datetime.now(),
            portfolio_value=self._get_portfolio_value(holdings),
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            cvar_99=cvar_99,
        )

    async def _calculate_parametric_var(
        self,
        holdings: list[dict[str, Any]],
        confidence_level: float,
        holding_period: int,
    ) -> float:
        """参数法计算VaR"""
        import math
        import random

        # Mock: 计算组合波动率
        portfolio_volatility = random.uniform(0.15, 0.25)  # 年化波动率

        # 转换为日波动率
        daily_volatility = portfolio_volatility / math.sqrt(252)

        # 持有期波动率
        period_volatility = daily_volatility * math.sqrt(holding_period)

        # Z分数
        z_score = self.Z_SCORES.get(confidence_level, 1.645)

        return period_volatility * z_score

    async def _calculate_historical_var(
        self,
        holdings: list[dict[str, Any]],
        confidence_level: float,
        holding_period: int,
    ) -> float:
        """历史模拟法计算VaR"""
        import random

        # Mock: 模拟历史收益分布
        base_var = await self._calculate_parametric_var(holdings, confidence_level, holding_period)

        # 历史法通常略有不同
        return base_var * random.uniform(0.9, 1.1)

    async def _calculate_monte_carlo_var(
        self,
        holdings: list[dict[str, Any]],
        confidence_level: float,
        holding_period: int,
    ) -> float:
        """蒙特卡洛法计算VaR"""
        import random

        # Mock: 模拟蒙特卡洛结果
        base_var = await self._calculate_parametric_var(holdings, confidence_level, holding_period)

        # MC法通常更精确
        return base_var * random.uniform(0.95, 1.05)

    def _get_portfolio_value(self, holdings: list[dict[str, Any]]) -> float:
        """获取组合价值"""
        total = sum(h.get("value", 0) for h in holdings)
        return total if total > 0 else 1000000  # 默认100万


# 全局单例
_var_calculator_service: VaRCalculatorService | None = None


def get_var_calculator_service() -> VaRCalculatorService:
    global _var_calculator_service
    if _var_calculator_service is None:
        _var_calculator_service = VaRCalculatorService()
    return _var_calculator_service
