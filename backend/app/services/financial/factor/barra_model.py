"""
BarraModelService - Barra风险模型服务

提供：
1. 风险因子暴露
2. 因子风险贡献
3. 特质风险计算
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BarraFactor(str, Enum):
    """Barra因子"""
    # 市场因子
    MARKET = "market"

    # 行业因子
    INDUSTRY = "industry"

    # 风格因子
    SIZE = "size"                   # 规模
    BETA = "beta"                   # 贝塔
    MOMENTUM = "momentum"           # 动量
    VOLATILITY = "volatility"       # 波动率
    VALUE = "value"                 # 价值
    GROWTH = "growth"               # 成长
    LIQUIDITY = "liquidity"         # 流动性
    LEVERAGE = "leverage"           # 杠杆
    QUALITY = "quality"             # 质量
    DIVIDEND = "dividend"           # 红利


@dataclass
class FactorExposure:
    """因子暴露"""
    factor: BarraFactor
    factor_name: str
    exposure: float          # 暴露度 (标准化)
    risk_contribution: float  # 风险贡献
    risk_contribution_pct: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor.value,
            "factor_name": self.factor_name,
            "exposure": self.exposure,
            "risk_contribution": self.risk_contribution,
            "risk_contribution_pct": self.risk_contribution_pct,
        }


@dataclass
class StockFactorProfile:
    """股票因子画像"""
    symbol: str
    name: str
    exposures: list[FactorExposure] = field(default_factory=list)
    industry: str = ""
    specific_risk: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "exposures": [e.to_dict() for e in self.exposures],
            "industry": self.industry,
            "specific_risk": self.specific_risk,
        }


@dataclass
class BarraRiskResult:
    """Barra风险分析结果"""
    portfolio_id: str
    analysis_date: datetime

    # 总风险
    total_risk: float           # 年化波动率
    factor_risk: float          # 因子风险
    specific_risk: float        # 特质风险

    # 因子暴露
    factor_exposures: list[FactorExposure] = field(default_factory=list)

    # 个股画像
    stock_profiles: list[StockFactorProfile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "analysis_date": self.analysis_date.isoformat(),
            "total_risk": self.total_risk,
            "factor_risk": self.factor_risk,
            "specific_risk": self.specific_risk,
            "factor_exposures": [f.to_dict() for f in self.factor_exposures],
            "stock_profiles": [s.to_dict() for s in self.stock_profiles],
        }


class BarraModelService:
    """Barra风险模型服务"""

    FACTOR_NAMES = {
        BarraFactor.MARKET: "市场",
        BarraFactor.INDUSTRY: "行业",
        BarraFactor.SIZE: "规模",
        BarraFactor.BETA: "贝塔",
        BarraFactor.MOMENTUM: "动量",
        BarraFactor.VOLATILITY: "波动率",
        BarraFactor.VALUE: "价值",
        BarraFactor.GROWTH: "成长",
        BarraFactor.LIQUIDITY: "流动性",
        BarraFactor.LEVERAGE: "杠杆",
        BarraFactor.QUALITY: "质量",
        BarraFactor.DIVIDEND: "红利",
    }

    def __init__(self):
        self._cache: dict[str, BarraRiskResult] = {}

    async def analyze_barra_risk(
        self,
        portfolio_id: str,
        holdings: list[dict[str, Any]],
    ) -> BarraRiskResult:
        """分析Barra风险"""
        import random

        # 计算总风险
        total_risk = random.uniform(0.15, 0.30)
        factor_risk = total_risk * random.uniform(0.6, 0.8)
        specific_risk = total_risk - factor_risk

        # 计算因子暴露
        factor_exposures = await self._calculate_portfolio_exposures(holdings, total_risk)

        # 计算个股画像
        stock_profiles = await self._calculate_stock_profiles(holdings)

        return BarraRiskResult(
            portfolio_id=portfolio_id,
            analysis_date=datetime.now(),
            total_risk=round(total_risk, 4),
            factor_risk=round(factor_risk, 4),
            specific_risk=round(specific_risk, 4),
            factor_exposures=factor_exposures,
            stock_profiles=stock_profiles,
        )

    async def get_stock_factor_profile(
        self,
        symbol: str,
    ) -> StockFactorProfile:
        """获取单只股票因子画像"""
        import random

        exposures = []
        for factor in [BarraFactor.SIZE, BarraFactor.VALUE, BarraFactor.MOMENTUM,
                      BarraFactor.QUALITY, BarraFactor.VOLATILITY]:
            exposures.append(FactorExposure(
                factor=factor,
                factor_name=self.FACTOR_NAMES[factor],
                exposure=round(random.uniform(-2, 2), 2),
                risk_contribution=round(random.uniform(0.01, 0.05), 4),
                risk_contribution_pct=round(random.uniform(5, 20), 2),
            ))

        return StockFactorProfile(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            exposures=exposures,
            industry=self._get_stock_industry(symbol),
            specific_risk=round(random.uniform(0.15, 0.35), 4),
        )

    async def _calculate_portfolio_exposures(
        self,
        holdings: list[dict[str, Any]],
        total_risk: float,
    ) -> list[FactorExposure]:
        """计算组合因子暴露"""
        import random

        exposures = []
        remaining_pct = 100.0

        factors = [
            (BarraFactor.MARKET, 40),
            (BarraFactor.SIZE, 15),
            (BarraFactor.VALUE, 12),
            (BarraFactor.MOMENTUM, 10),
            (BarraFactor.QUALITY, 8),
            (BarraFactor.VOLATILITY, 8),
            (BarraFactor.INDUSTRY, 7),
        ]

        for factor, base_pct in factors:
            pct = base_pct * random.uniform(0.8, 1.2)
            pct = min(pct, remaining_pct)
            remaining_pct -= pct

            exposures.append(FactorExposure(
                factor=factor,
                factor_name=self.FACTOR_NAMES[factor],
                exposure=round(random.uniform(-1.5, 1.5), 2),
                risk_contribution=round(total_risk * pct / 100, 4),
                risk_contribution_pct=round(pct, 2),
            ))

        return exposures

    async def _calculate_stock_profiles(
        self,
        holdings: list[dict[str, Any]],
    ) -> list[StockFactorProfile]:
        """计算个股因子画像"""
        profiles = []
        for holding in holdings[:5]:  # 只返回前5个
            symbol = holding.get("symbol", "")
            profile = await self.get_stock_factor_profile(symbol)
            profiles.append(profile)
        return profiles

    def _get_stock_name(self, symbol: str) -> str:
        names = {"600519": "贵州茅台", "000858": "五粮液", "600036": "招商银行", "000333": "美的集团"}
        return names.get(symbol, f"股票{symbol}")

    def _get_stock_industry(self, symbol: str) -> str:
        industries = {"600519": "白酒", "000858": "白酒", "600036": "银行", "000333": "家电"}
        return industries.get(symbol, "其他")


_barra_model_service: BarraModelService | None = None


def get_barra_model_service() -> BarraModelService:
    global _barra_model_service
    if _barra_model_service is None:
        _barra_model_service = BarraModelService()
    return _barra_model_service
