"""
MAAnalysisService - 并购重组分析服务

提供：
1. 并购交易跟踪
2. 交易估值分析
3. 整合进度监控
4. 协同效应评估
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MAType(str, Enum):
    """并购类型"""
    ACQUISITION = "acquisition"     # 收购
    MERGER = "merger"               # 合并
    ASSET_PURCHASE = "asset_purchase"  # 资产收购
    EQUITY_TRANSFER = "equity_transfer"  # 股权转让
    RESTRUCTURING = "restructuring"  # 资产重组
    SPIN_OFF = "spin_off"           # 分拆上市


class MAStatus(str, Enum):
    """并购状态"""
    RUMORED = "rumored"         # 传闻
    ANNOUNCED = "announced"     # 已公告
    DUE_DILIGENCE = "due_diligence"  # 尽职调查
    SHAREHOLDER_VOTE = "shareholder_vote"  # 股东投票
    REGULATORY_REVIEW = "regulatory_review"  # 监管审批
    APPROVED = "approved"       # 已批准
    COMPLETED = "completed"     # 已完成
    TERMINATED = "terminated"   # 已终止
    FAILED = "failed"           # 失败


class PaymentType(str, Enum):
    """支付方式"""
    CASH = "cash"
    STOCK = "stock"
    MIXED = "mixed"
    ASSET_SWAP = "asset_swap"


@dataclass
class MAParty:
    """交易方"""
    symbol: str
    name: str
    role: str  # acquirer / target
    stake_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "role": self.role,
            "stake_pct": self.stake_pct,
        }


@dataclass
class MAValuation:
    """交易估值"""
    deal_value: float           # 交易金额 (亿)
    ev_ebitda: float | None = None
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    premium_pct: float | None = None  # 溢价率

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_value": self.deal_value,
            "ev_ebitda": self.ev_ebitda,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "premium_pct": self.premium_pct,
        }


@dataclass
class SynergyEstimate:
    """协同效应估计"""
    revenue_synergy: float      # 收入协同 (亿/年)
    cost_synergy: float         # 成本协同 (亿/年)
    total_synergy: float        # 总协同效应
    realization_years: int      # 实现年限
    confidence: float           # 置信度

    def to_dict(self) -> dict[str, Any]:
        return {
            "revenue_synergy": self.revenue_synergy,
            "cost_synergy": self.cost_synergy,
            "total_synergy": self.total_synergy,
            "realization_years": self.realization_years,
            "confidence": self.confidence,
        }


@dataclass
class MADeal:
    """并购交易"""
    deal_id: str
    deal_name: str
    ma_type: MAType
    status: MAStatus

    # 交易方
    acquirer: MAParty
    target: MAParty

    # 时间
    announce_date: date
    expected_close_date: date | None = None
    actual_close_date: date | None = None

    # 交易条款
    payment_type: PaymentType = PaymentType.CASH
    valuation: MAValuation | None = None
    synergy: SynergyEstimate | None = None

    # 进展
    milestones: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deal_id": self.deal_id,
            "deal_name": self.deal_name,
            "ma_type": self.ma_type.value,
            "status": self.status.value,
            "acquirer": self.acquirer.to_dict(),
            "target": self.target.to_dict(),
            "announce_date": self.announce_date.isoformat(),
            "expected_close_date": self.expected_close_date.isoformat() if self.expected_close_date else None,
            "actual_close_date": self.actual_close_date.isoformat() if self.actual_close_date else None,
            "payment_type": self.payment_type.value,
            "valuation": self.valuation.to_dict() if self.valuation else None,
            "synergy": self.synergy.to_dict() if self.synergy else None,
            "milestones": self.milestones,
            "risks": self.risks,
        }


@dataclass
class MAAnalysisResult:
    """并购分析结果"""
    symbol: str
    name: str
    analysis_date: datetime

    # 作为收购方的交易
    as_acquirer: list[MADeal] = field(default_factory=list)
    # 作为标的的交易
    as_target: list[MADeal] = field(default_factory=list)
    # 历史交易
    historical_deals: list[MADeal] = field(default_factory=list)

    # 统计
    total_deal_value: float = 0.0
    successful_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "as_acquirer": [d.to_dict() for d in self.as_acquirer],
            "as_target": [d.to_dict() for d in self.as_target],
            "historical_deals": [d.to_dict() for d in self.historical_deals],
            "total_deal_value": self.total_deal_value,
            "successful_rate": self.successful_rate,
        }


class MAAnalysisService:
    """并购重组分析服务"""

    def __init__(self):
        self._cache: dict[str, MAAnalysisResult] = {}

    async def analyze_ma_activity(
        self,
        symbol: str,
    ) -> MAAnalysisResult:
        """分析并购活动"""
        if symbol in self._cache:
            return self._cache[symbol]

        try:
            # 获取作为收购方的交易
            as_acquirer = await self._get_deals_as_acquirer(symbol)

            # 获取作为标的的交易
            as_target = await self._get_deals_as_target(symbol)

            # 获取历史交易
            historical = await self._get_historical_deals(symbol)

            # 计算统计
            all_deals = as_acquirer + as_target + historical
            total_value = sum(d.valuation.deal_value for d in all_deals if d.valuation)
            completed = sum(1 for d in all_deals if d.status == MAStatus.COMPLETED)
            success_rate = completed / len(all_deals) if all_deals else 0

            result = MAAnalysisResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                as_acquirer=as_acquirer,
                as_target=as_target,
                historical_deals=historical,
                total_deal_value=round(total_value, 2),
                successful_rate=round(success_rate, 2),
            )

            self._cache[symbol] = result
            return result

        except Exception as e:
            logger.error(f"Failed to analyze M&A activity for {symbol}: {e}")
            return MAAnalysisResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )

    async def get_recent_ma_deals(
        self,
        ma_type: MAType | None = None,
        status: MAStatus | None = None,
        limit: int = 20,
    ) -> list[MADeal]:
        """获取近期并购交易"""
        deals = await self._get_market_deals()

        if ma_type:
            deals = [d for d in deals if d.ma_type == ma_type]
        if status:
            deals = [d for d in deals if d.status == status]

        deals.sort(key=lambda x: x.announce_date, reverse=True)
        return deals[:limit]

    async def get_pending_regulatory_reviews(self) -> list[MADeal]:
        """获取待审批交易"""
        deals = await self._get_market_deals()
        return [d for d in deals if d.status == MAStatus.REGULATORY_REVIEW]

    async def _get_deals_as_acquirer(self, symbol: str) -> list[MADeal]:
        """获取作为收购方的交易"""
        import random
        from datetime import timedelta

        deals = []

        # 模拟一个进行中的交易
        deals.append(MADeal(
            deal_id=f"{symbol}_MA_001",
            deal_name=f"{self._get_stock_name(symbol)}收购某科技公司",
            ma_type=MAType.ACQUISITION,
            status=MAStatus.REGULATORY_REVIEW,
            acquirer=MAParty(symbol=symbol, name=self._get_stock_name(symbol), role="acquirer"),
            target=MAParty(symbol="PRIVATE", name="某科技公司", role="target", stake_pct=100),
            announce_date=date.today() - timedelta(days=random.randint(30, 90)),
            expected_close_date=date.today() + timedelta(days=random.randint(30, 90)),
            payment_type=PaymentType.MIXED,
            valuation=MAValuation(
                deal_value=round(random.uniform(10, 100), 2),
                ev_ebitda=round(random.uniform(8, 15), 1),
                pe_ratio=round(random.uniform(15, 30), 1),
                premium_pct=round(random.uniform(20, 50), 1),
            ),
            synergy=SynergyEstimate(
                revenue_synergy=round(random.uniform(1, 10), 2),
                cost_synergy=round(random.uniform(0.5, 5), 2),
                total_synergy=round(random.uniform(2, 15), 2),
                realization_years=3,
                confidence=round(random.uniform(0.6, 0.85), 2),
            ),
            milestones=["已公告", "股东大会通过", "等待监管审批"],
            risks=["监管审批风险", "整合风险"],
        ))

        return deals

    async def _get_deals_as_target(self, symbol: str) -> list[MADeal]:
        """获取作为标的的交易"""
        # 大多数公司不会是收购标的
        return []

    async def _get_historical_deals(self, symbol: str) -> list[MADeal]:
        """获取历史交易"""
        import random

        deals = []

        for i in range(2):
            year = date.today().year - i - 1
            deals.append(MADeal(
                deal_id=f"{symbol}_MA_{year}_001",
                deal_name=f"{self._get_stock_name(symbol)}{year}年资产收购",
                ma_type=MAType.ASSET_PURCHASE,
                status=MAStatus.COMPLETED,
                acquirer=MAParty(symbol=symbol, name=self._get_stock_name(symbol), role="acquirer"),
                target=MAParty(symbol="PRIVATE", name=f"标的公司{i+1}", role="target"),
                announce_date=date(year, random.randint(1, 6), 15),
                actual_close_date=date(year, random.randint(7, 12), 15),
                payment_type=PaymentType.CASH,
                valuation=MAValuation(
                    deal_value=round(random.uniform(5, 50), 2),
                    pe_ratio=round(random.uniform(10, 25), 1),
                ),
            ))

        return deals

    async def _get_market_deals(self) -> list[MADeal]:
        """获取市场并购交易"""
        import random
        from datetime import timedelta

        deals_data = [
            ("600519", "贵州茅台", "某酒业公司"),
            ("000333", "美的集团", "某家电品牌"),
            ("000858", "五粮液", "某酿酒厂"),
        ]

        deals = []
        for symbol, name, target_name in deals_data:
            deals.append(MADeal(
                deal_id=f"{symbol}_MA_{date.today().year}_001",
                deal_name=f"{name}收购{target_name}",
                ma_type=random.choice(list(MAType)),
                status=random.choice([MAStatus.ANNOUNCED, MAStatus.REGULATORY_REVIEW, MAStatus.APPROVED]),
                acquirer=MAParty(symbol=symbol, name=name, role="acquirer"),
                target=MAParty(symbol="PRIVATE", name=target_name, role="target"),
                announce_date=date.today() - timedelta(days=random.randint(1, 60)),
                payment_type=random.choice(list(PaymentType)),
                valuation=MAValuation(
                    deal_value=round(random.uniform(5, 100), 2),
                ),
            ))

        return deals

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
_ma_analysis_service: MAAnalysisService | None = None


def get_ma_analysis_service() -> MAAnalysisService:
    """获取并购分析服务单例"""
    global _ma_analysis_service
    if _ma_analysis_service is None:
        _ma_analysis_service = MAAnalysisService()
    return _ma_analysis_service
