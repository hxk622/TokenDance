# -*- coding: utf-8 -*-
"""
RebalanceSuggestService - 再平衡建议服务

提供：
1. 偏离度分析
2. 再平衡建议
3. 交易成本估算
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RebalanceStrategy(str, Enum):
    """再平衡策略"""
    THRESHOLD = "threshold"       # 阈值触发
    PERIODIC = "periodic"         # 定期再平衡
    OPTIMAL = "optimal"           # 最优化再平衡


class TradeDirection(str, Enum):
    """交易方向"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class PositionDeviation:
    """持仓偏离"""
    symbol: str
    name: str
    current_weight: float
    target_weight: float
    deviation: float
    deviation_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "current_weight": self.current_weight,
            "target_weight": self.target_weight,
            "deviation": self.deviation,
            "deviation_pct": self.deviation_pct,
        }


@dataclass
class RebalanceSuggestion:
    """再平衡建议"""
    symbol: str
    name: str
    direction: TradeDirection
    current_weight: float
    target_weight: float
    trade_amount: float       # 交易金额
    trade_shares: int         # 交易股数
    estimated_cost: float     # 预估交易成本
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "direction": self.direction.value,
            "current_weight": self.current_weight,
            "target_weight": self.target_weight,
            "trade_amount": self.trade_amount,
            "trade_shares": self.trade_shares,
            "estimated_cost": self.estimated_cost,
        }


@dataclass
class RebalanceResult:
    """再平衡结果"""
    portfolio_id: str
    analysis_date: datetime
    strategy: RebalanceStrategy
    
    # 当前状态
    portfolio_value: float
    total_deviation: float    # 总偏离度
    
    # 偏离分析
    deviations: List[PositionDeviation] = field(default_factory=list)
    
    # 再平衡建议
    suggestions: List[RebalanceSuggestion] = field(default_factory=list)
    
    # 交易汇总
    total_buy_amount: float = 0.0
    total_sell_amount: float = 0.0
    total_trade_cost: float = 0.0
    
    # 是否需要再平衡
    needs_rebalance: bool = False
    rebalance_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "analysis_date": self.analysis_date.isoformat(),
            "strategy": self.strategy.value,
            "portfolio_value": self.portfolio_value,
            "total_deviation": self.total_deviation,
            "deviations": [d.to_dict() for d in self.deviations],
            "suggestions": [s.to_dict() for s in self.suggestions],
            "total_buy_amount": self.total_buy_amount,
            "total_sell_amount": self.total_sell_amount,
            "total_trade_cost": self.total_trade_cost,
            "needs_rebalance": self.needs_rebalance,
            "rebalance_reason": self.rebalance_reason,
        }


class RebalanceSuggestService:
    """再平衡建议服务"""
    
    # 默认阈值
    DEFAULT_THRESHOLD = 0.05  # 5%偏离触发再平衡
    
    # 交易成本假设
    COMMISSION_RATE = 0.0003  # 佣金率
    STAMP_TAX_RATE = 0.001    # 印花税 (卖出)
    
    def __init__(self):
        self._cache: Dict[str, RebalanceResult] = {}
    
    async def analyze_rebalance(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
        target_weights: Dict[str, float],
        strategy: RebalanceStrategy = RebalanceStrategy.THRESHOLD,
        threshold: float = 0.05,
    ) -> RebalanceResult:
        """分析再平衡需求"""
        import random
        
        # 计算组合价值
        portfolio_value = sum(h.get("value", 0) for h in holdings)
        if portfolio_value == 0:
            portfolio_value = 1000000
        
        # 计算偏离
        deviations = []
        total_deviation = 0
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            current_value = holding.get("value", 0)
            current_weight = current_value / portfolio_value if portfolio_value > 0 else 0
            target_weight = target_weights.get(symbol, 0)
            
            deviation = current_weight - target_weight
            deviation_pct = abs(deviation) / target_weight * 100 if target_weight > 0 else 0
            
            deviations.append(PositionDeviation(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                current_weight=round(current_weight * 100, 2),
                target_weight=round(target_weight * 100, 2),
                deviation=round(deviation * 100, 2),
                deviation_pct=round(deviation_pct, 2),
            ))
            
            total_deviation += abs(deviation)
        
        # 判断是否需要再平衡
        needs_rebalance = total_deviation > threshold
        rebalance_reason = ""
        if needs_rebalance:
            rebalance_reason = f"总偏离度{total_deviation*100:.2f}%超过阈值{threshold*100:.0f}%"
        
        # 生成再平衡建议
        suggestions = []
        total_buy = 0
        total_sell = 0
        total_cost = 0
        
        if needs_rebalance:
            for dev in deviations:
                target_w = target_weights.get(dev.symbol.replace("股票", ""), 0)
                current_w = dev.current_weight / 100
                
                trade_value = (target_w - current_w) * portfolio_value
                
                if abs(trade_value) < 1000:  # 忽略小额交易
                    continue
                
                if trade_value > 0:
                    direction = TradeDirection.BUY
                    cost = abs(trade_value) * self.COMMISSION_RATE
                    total_buy += trade_value
                else:
                    direction = TradeDirection.SELL
                    cost = abs(trade_value) * (self.COMMISSION_RATE + self.STAMP_TAX_RATE)
                    total_sell += abs(trade_value)
                
                total_cost += cost
                
                # 估算股数 (假设股价)
                price = random.uniform(20, 200)
                shares = int(abs(trade_value) / price / 100) * 100
                
                suggestions.append(RebalanceSuggestion(
                    symbol=dev.symbol,
                    name=dev.name,
                    direction=direction,
                    current_weight=dev.current_weight,
                    target_weight=dev.target_weight,
                    trade_amount=round(abs(trade_value), 2),
                    trade_shares=shares,
                    estimated_cost=round(cost, 2),
                ))
        
        return RebalanceResult(
            portfolio_id=portfolio_id,
            analysis_date=datetime.now(),
            strategy=strategy,
            portfolio_value=portfolio_value,
            total_deviation=round(total_deviation * 100, 2),
            deviations=deviations,
            suggestions=sorted(suggestions, key=lambda x: x.trade_amount, reverse=True),
            total_buy_amount=round(total_buy, 2),
            total_sell_amount=round(total_sell, 2),
            total_trade_cost=round(total_cost, 2),
            needs_rebalance=needs_rebalance,
            rebalance_reason=rebalance_reason,
        )
    
    async def suggest_optimal_weights(
        self,
        symbols: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """建议最优权重 (简化版)"""
        import random
        
        n = len(symbols)
        weights = {}
        remaining = 1.0
        
        for i, symbol in enumerate(symbols[:-1]):
            w = random.uniform(0.05, min(0.3, remaining - 0.05 * (n - i - 1)))
            weights[symbol] = round(w, 4)
            remaining -= w
        
        weights[symbols[-1]] = round(remaining, 4)
        
        return weights
    
    def _get_stock_name(self, symbol: str) -> str:
        names = {
            "600519": "贵州茅台", "000858": "五粮液",
            "600036": "招商银行", "000333": "美的集团",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_rebalance_suggest_service: Optional[RebalanceSuggestService] = None


def get_rebalance_suggest_service() -> RebalanceSuggestService:
    global _rebalance_suggest_service
    if _rebalance_suggest_service is None:
        _rebalance_suggest_service = RebalanceSuggestService()
    return _rebalance_suggest_service
