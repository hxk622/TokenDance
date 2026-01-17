"""
CompetitorAnalysisService - 竞争对手分析服务

提供：
1. 竞争对手识别
2. 竞争格局分析
3. 市场份额对比
4. 竞争优势分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CompetitionLevel(str, Enum):
    """竞争程度"""
    DIRECT = "direct"           # 直接竞争
    INDIRECT = "indirect"       # 间接竞争
    POTENTIAL = "potential"     # 潜在竞争
    SUBSTITUTE = "substitute"   # 替代品竞争


@dataclass
class CompetitiveMetrics:
    """竞争力指标"""
    market_share: float
    revenue_growth: float
    profit_margin: float
    rd_intensity: float  # 研发强度
    brand_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "market_share": self.market_share,
            "revenue_growth": self.revenue_growth,
            "profit_margin": self.profit_margin,
            "rd_intensity": self.rd_intensity,
            "brand_value": self.brand_value,
        }


@dataclass
class Competitor:
    """竞争对手"""
    symbol: str
    name: str
    competition_level: CompetitionLevel
    metrics: CompetitiveMetrics

    # 竞争分析
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    threat_level: str = "medium"  # low/medium/high

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "competition_level": self.competition_level.value,
            "metrics": self.metrics.to_dict(),
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "threat_level": self.threat_level,
        }


@dataclass
class MarketLandscape:
    """市场格局"""
    total_market_size: float  # 市场规模（亿）
    growth_rate: float
    concentration: str  # 集中度：高/中/低
    top_players_share: float  # 前几名市占率
    entry_barriers: str  # 进入壁垒

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_market_size": self.total_market_size,
            "growth_rate": self.growth_rate,
            "concentration": self.concentration,
            "top_players_share": self.top_players_share,
            "entry_barriers": self.entry_barriers,
        }


@dataclass
class CompetitorAnalysisResult:
    """竞争分析结果"""
    symbol: str
    name: str
    analysis_date: datetime
    industry: str

    # 自身指标
    own_metrics: CompetitiveMetrics | None = None

    # 竞争对手
    competitors: list[Competitor] = field(default_factory=list)

    # 市场格局
    market_landscape: MarketLandscape | None = None

    # 竞争优势
    competitive_advantages: list[str] = field(default_factory=list)
    competitive_risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "industry": self.industry,
            "own_metrics": self.own_metrics.to_dict() if self.own_metrics else None,
            "competitors": [c.to_dict() for c in self.competitors],
            "market_landscape": self.market_landscape.to_dict() if self.market_landscape else None,
            "competitive_advantages": self.competitive_advantages,
            "competitive_risks": self.competitive_risks,
        }


class CompetitorAnalysisService:
    """竞争对手分析服务"""

    # 竞争对手映射
    COMPETITOR_MAP = {
        "600519": {  # 贵州茅台
            "industry": "白酒",
            "competitors": [
                ("000858", "五粮液", CompetitionLevel.DIRECT),
                ("000568", "泸州老窖", CompetitionLevel.DIRECT),
                ("600809", "山西汾酒", CompetitionLevel.DIRECT),
            ],
        },
        "000333": {  # 美的集团
            "industry": "家电",
            "competitors": [
                ("000651", "格力电器", CompetitionLevel.DIRECT),
                ("600690", "海尔智家", CompetitionLevel.DIRECT),
            ],
        },
        "300750": {  # 宁德时代
            "industry": "动力电池",
            "competitors": [
                ("002594", "比亚迪", CompetitionLevel.DIRECT),
                ("002074", "国轩高科", CompetitionLevel.DIRECT),
            ],
        },
    }

    def __init__(self):
        self._cache: dict[str, CompetitorAnalysisResult] = {}

    async def analyze_competitors(
        self,
        symbol: str,
    ) -> CompetitorAnalysisResult:
        """分析竞争对手"""
        if symbol in self._cache:
            return self._cache[symbol]

        try:
            # 获取竞争对手信息
            comp_info = self.COMPETITOR_MAP.get(symbol, {})
            industry = comp_info.get("industry", "未知")

            # 自身指标
            own_metrics = await self._get_competitive_metrics(symbol)

            # 竞争对手列表
            competitors = []
            for comp_symbol, comp_name, comp_level in comp_info.get("competitors", []):
                comp_metrics = await self._get_competitive_metrics(comp_symbol)
                competitor = await self._analyze_single_competitor(
                    comp_symbol, comp_name, comp_level, comp_metrics, own_metrics
                )
                competitors.append(competitor)

            # 市场格局
            market_landscape = await self._analyze_market_landscape(industry)

            # 竞争优势/风险
            advantages, risks = self._analyze_competitive_position(own_metrics, competitors)

            result = CompetitorAnalysisResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                industry=industry,
                own_metrics=own_metrics,
                competitors=competitors,
                market_landscape=market_landscape,
                competitive_advantages=advantages,
                competitive_risks=risks,
            )

            self._cache[symbol] = result
            return result

        except Exception as e:
            logger.error(f"Failed to analyze competitors for {symbol}: {e}")
            return CompetitorAnalysisResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
                industry="",
            )

    async def compare_competitors(
        self,
        symbols: list[str],
    ) -> dict[str, Any]:
        """多公司竞争力对比"""
        metrics = {}
        for symbol in symbols:
            m = await self._get_competitive_metrics(symbol)
            metrics[symbol] = {
                "name": self._get_stock_name(symbol),
                "metrics": m.to_dict(),
            }

        return {
            "comparison_date": datetime.now().isoformat(),
            "companies": metrics,
        }

    async def _get_competitive_metrics(self, symbol: str) -> CompetitiveMetrics:
        """获取竞争力指标"""
        import random

        return CompetitiveMetrics(
            market_share=round(random.uniform(5, 40), 1),
            revenue_growth=round(random.uniform(-5, 30), 1),
            profit_margin=round(random.uniform(5, 35), 1),
            rd_intensity=round(random.uniform(1, 15), 1),
            brand_value=round(random.uniform(50, 100), 0),
        )

    async def _analyze_single_competitor(
        self,
        symbol: str,
        name: str,
        level: CompetitionLevel,
        metrics: CompetitiveMetrics,
        own_metrics: CompetitiveMetrics,
    ) -> Competitor:
        """分析单个竞争对手"""
        # 确定威胁程度
        if metrics.market_share > own_metrics.market_share:
            threat_level = "high"
        elif metrics.market_share > own_metrics.market_share * 0.7:
            threat_level = "medium"
        else:
            threat_level = "low"

        # 分析优劣势
        strengths = []
        weaknesses = []

        if metrics.market_share > own_metrics.market_share:
            strengths.append("市场份额领先")
        else:
            weaknesses.append("市场份额较小")

        if metrics.revenue_growth > own_metrics.revenue_growth:
            strengths.append("增长势头强劲")
        else:
            weaknesses.append("增长动力不足")

        if metrics.rd_intensity > own_metrics.rd_intensity:
            strengths.append("研发投入高")
        else:
            weaknesses.append("研发投入相对较低")

        return Competitor(
            symbol=symbol,
            name=name,
            competition_level=level,
            metrics=metrics,
            strengths=strengths,
            weaknesses=weaknesses,
            threat_level=threat_level,
        )

    async def _analyze_market_landscape(self, industry: str) -> MarketLandscape:
        """分析市场格局"""
        import random

        landscapes = {
            "白酒": MarketLandscape(
                total_market_size=round(random.uniform(5000, 8000), 0),
                growth_rate=round(random.uniform(5, 15), 1),
                concentration="高",
                top_players_share=round(random.uniform(60, 80), 1),
                entry_barriers="高（品牌、渠道、产能）",
            ),
            "家电": MarketLandscape(
                total_market_size=round(random.uniform(8000, 12000), 0),
                growth_rate=round(random.uniform(3, 10), 1),
                concentration="高",
                top_players_share=round(random.uniform(55, 75), 1),
                entry_barriers="中（规模、品牌）",
            ),
            "动力电池": MarketLandscape(
                total_market_size=round(random.uniform(3000, 5000), 0),
                growth_rate=round(random.uniform(20, 40), 1),
                concentration="高",
                top_players_share=round(random.uniform(70, 85), 1),
                entry_barriers="高（技术、资金、客户）",
            ),
        }

        return landscapes.get(industry, MarketLandscape(
            total_market_size=1000,
            growth_rate=10,
            concentration="中",
            top_players_share=50,
            entry_barriers="中",
        ))

    def _analyze_competitive_position(
        self,
        own_metrics: CompetitiveMetrics,
        competitors: list[Competitor],
    ) -> tuple[list[str], list[str]]:
        """分析竞争地位"""
        advantages = []
        risks = []

        # 计算相对位置
        avg_market_share = sum(c.metrics.market_share for c in competitors) / len(competitors) if competitors else 0

        if own_metrics.market_share > avg_market_share:
            advantages.append("市场份额领先于主要竞争对手")
        else:
            risks.append("市场份额低于竞争对手平均水平")

        if own_metrics.profit_margin > 20:
            advantages.append("盈利能力强")

        if own_metrics.rd_intensity > 5:
            advantages.append("研发投入较高，技术竞争力强")

        # 检查威胁
        high_threat = [c for c in competitors if c.threat_level == "high"]
        if high_threat:
            risks.append(f"面临{len(high_threat)}个高威胁竞争对手")

        return advantages, risks

    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000568": "泸州老窖",
            "600809": "山西汾酒",
            "000333": "美的集团",
            "000651": "格力电器",
            "600690": "海尔智家",
            "300750": "宁德时代",
            "002594": "比亚迪",
            "002074": "国轩高科",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_competitor_analysis_service: CompetitorAnalysisService | None = None


def get_competitor_analysis_service() -> CompetitorAnalysisService:
    """获取竞争分析服务单例"""
    global _competitor_analysis_service
    if _competitor_analysis_service is None:
        _competitor_analysis_service = CompetitorAnalysisService()
    return _competitor_analysis_service
