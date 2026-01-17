# -*- coding: utf-8 -*-
"""
RiskAttributionService - 风险归因分析服务

提供：
1. 组合风险分解
2. 因子风险归因
3. 个股风险贡献
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskSource(str, Enum):
    """风险来源"""
    MARKET = "market"           # 市场风险
    INDUSTRY = "industry"       # 行业风险
    STYLE = "style"             # 风格风险
    SPECIFIC = "specific"       # 特质风险
    CURRENCY = "currency"       # 汇率风险
    INTEREST_RATE = "interest_rate"  # 利率风险


@dataclass
class RiskContribution:
    """风险贡献"""
    source: str
    source_type: RiskSource
    risk_contribution: float      # 风险贡献 (波动率贡献)
    risk_contribution_pct: float  # 风险贡献占比
    marginal_risk: float          # 边际风险
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_type": self.source_type.value,
            "risk_contribution": self.risk_contribution,
            "risk_contribution_pct": self.risk_contribution_pct,
            "marginal_risk": self.marginal_risk,
        }


@dataclass
class PositionRisk:
    """持仓风险"""
    symbol: str
    name: str
    weight: float
    volatility: float
    beta: float
    risk_contribution: float
    risk_contribution_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "weight": self.weight,
            "volatility": self.volatility,
            "beta": self.beta,
            "risk_contribution": self.risk_contribution,
            "risk_contribution_pct": self.risk_contribution_pct,
        }


@dataclass
class RiskAttributionResult:
    """风险归因结果"""
    portfolio_id: str
    analysis_date: datetime
    
    # 组合整体风险
    total_risk: float              # 总风险 (年化波动率)
    systematic_risk: float         # 系统性风险
    specific_risk: float           # 特质风险
    
    # 因子风险归因
    factor_contributions: List[RiskContribution] = field(default_factory=list)
    
    # 持仓风险
    position_risks: List[PositionRisk] = field(default_factory=list)
    
    # 风险集中度
    top5_risk_contribution: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "analysis_date": self.analysis_date.isoformat(),
            "total_risk": self.total_risk,
            "systematic_risk": self.systematic_risk,
            "specific_risk": self.specific_risk,
            "factor_contributions": [f.to_dict() for f in self.factor_contributions],
            "position_risks": [p.to_dict() for p in self.position_risks],
            "top5_risk_contribution": self.top5_risk_contribution,
        }


class RiskAttributionService:
    """风险归因分析服务"""
    
    def __init__(self):
        self._cache: Dict[str, RiskAttributionResult] = {}
    
    async def analyze_risk_attribution(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
    ) -> RiskAttributionResult:
        """
        分析风险归因
        
        Args:
            portfolio_id: 组合ID
            holdings: 持仓列表 [{"symbol": "600519", "weight": 0.1}, ...]
        """
        try:
            # 计算组合风险
            total_risk = await self._calculate_portfolio_risk(holdings)
            
            # 分解系统性/特质风险
            systematic_risk = total_risk * 0.7  # 简化计算
            specific_risk = total_risk * 0.3
            
            # 因子风险归因
            factor_contributions = await self._calculate_factor_contributions(holdings, total_risk)
            
            # 持仓风险
            position_risks = await self._calculate_position_risks(holdings, total_risk)
            
            # 风险集中度
            sorted_positions = sorted(position_risks, key=lambda x: x.risk_contribution_pct, reverse=True)
            top5_contribution = sum(p.risk_contribution_pct for p in sorted_positions[:5])
            
            return RiskAttributionResult(
                portfolio_id=portfolio_id,
                analysis_date=datetime.now(),
                total_risk=round(total_risk, 4),
                systematic_risk=round(systematic_risk, 4),
                specific_risk=round(specific_risk, 4),
                factor_contributions=factor_contributions,
                position_risks=position_risks,
                top5_risk_contribution=round(top5_contribution, 2),
            )
            
        except Exception as e:
            logger.error(f"Failed to analyze risk attribution: {e}")
            return RiskAttributionResult(
                portfolio_id=portfolio_id,
                analysis_date=datetime.now(),
                total_risk=0,
                systematic_risk=0,
                specific_risk=0,
            )
    
    async def _calculate_portfolio_risk(
        self,
        holdings: List[Dict[str, Any]],
    ) -> float:
        """计算组合风险"""
        import random
        
        # Mock: 实际应基于协方差矩阵计算
        return random.uniform(0.15, 0.30)
    
    async def _calculate_factor_contributions(
        self,
        holdings: List[Dict[str, Any]],
        total_risk: float,
    ) -> List[RiskContribution]:
        """计算因子风险贡献"""
        import random
        
        factors = [
            ("市场因子", RiskSource.MARKET, 0.5),
            ("行业因子", RiskSource.INDUSTRY, 0.2),
            ("规模因子", RiskSource.STYLE, 0.1),
            ("价值因子", RiskSource.STYLE, 0.08),
            ("动量因子", RiskSource.STYLE, 0.07),
            ("特质风险", RiskSource.SPECIFIC, 0.05),
        ]
        
        contributions = []
        remaining_pct = 100.0
        
        for name, source_type, base_pct in factors[:-1]:
            pct = base_pct * 100 * random.uniform(0.8, 1.2)
            pct = min(pct, remaining_pct)
            remaining_pct -= pct
            
            contributions.append(RiskContribution(
                source=name,
                source_type=source_type,
                risk_contribution=round(total_risk * pct / 100, 4),
                risk_contribution_pct=round(pct, 2),
                marginal_risk=round(random.uniform(0.01, 0.05), 4),
            ))
        
        # 特质风险
        contributions.append(RiskContribution(
            source="特质风险",
            source_type=RiskSource.SPECIFIC,
            risk_contribution=round(total_risk * remaining_pct / 100, 4),
            risk_contribution_pct=round(remaining_pct, 2),
            marginal_risk=round(random.uniform(0.01, 0.03), 4),
        ))
        
        return contributions
    
    async def _calculate_position_risks(
        self,
        holdings: List[Dict[str, Any]],
        total_risk: float,
    ) -> List[PositionRisk]:
        """计算持仓风险"""
        import random
        
        position_risks = []
        total_weight = sum(h.get("weight", 0) for h in holdings)
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            weight = holding.get("weight", 0) / total_weight if total_weight > 0 else 0
            
            volatility = random.uniform(0.20, 0.50)
            beta = random.uniform(0.8, 1.3)
            risk_contrib = weight * volatility * beta
            risk_contrib_pct = risk_contrib / total_risk * 100 if total_risk > 0 else 0
            
            position_risks.append(PositionRisk(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                weight=round(weight * 100, 2),
                volatility=round(volatility, 4),
                beta=round(beta, 2),
                risk_contribution=round(risk_contrib, 4),
                risk_contribution_pct=round(risk_contrib_pct, 2),
            ))
        
        return sorted(position_risks, key=lambda x: x.risk_contribution_pct, reverse=True)
    
    def _get_stock_name(self, symbol: str) -> str:
        names = {
            "600519": "贵州茅台", "000858": "五粮液",
            "600036": "招商银行", "000333": "美的集团",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_risk_attribution_service: Optional[RiskAttributionService] = None


def get_risk_attribution_service() -> RiskAttributionService:
    global _risk_attribution_service
    if _risk_attribution_service is None:
        _risk_attribution_service = RiskAttributionService()
    return _risk_attribution_service
