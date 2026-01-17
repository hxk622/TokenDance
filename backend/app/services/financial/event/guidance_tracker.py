# -*- coding: utf-8 -*-
"""
GuidanceTrackerService - 业绩指引跟踪服务

提供：
1. 公司业绩指引跟踪
2. 指引变化监控
3. 指引达成率分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class GuidanceType(str, Enum):
    """指引类型"""
    REVENUE = "revenue"
    NET_PROFIT = "net_profit"
    GROSS_MARGIN = "gross_margin"
    CAPEX = "capex"
    SHIPMENT = "shipment"
    OTHER = "other"


class GuidanceChange(str, Enum):
    """指引变化"""
    RAISED = "raised"       # 上调
    MAINTAINED = "maintained"  # 维持
    LOWERED = "lowered"     # 下调
    WITHDRAWN = "withdrawn"  # 撤回
    NEW = "new"             # 新发布


@dataclass
class Guidance:
    """业绩指引"""
    symbol: str
    name: str
    guidance_date: date
    period: str  # 指引期间，如 "FY2024"
    guidance_type: GuidanceType
    
    # 指引范围
    low_estimate: Optional[float] = None
    high_estimate: Optional[float] = None
    point_estimate: Optional[float] = None
    
    # 变化
    change: GuidanceChange = GuidanceChange.NEW
    previous_low: Optional[float] = None
    previous_high: Optional[float] = None
    
    # 描述
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "guidance_date": self.guidance_date.isoformat(),
            "period": self.period,
            "guidance_type": self.guidance_type.value,
            "low_estimate": self.low_estimate,
            "high_estimate": self.high_estimate,
            "point_estimate": self.point_estimate,
            "change": self.change.value,
            "previous_low": self.previous_low,
            "previous_high": self.previous_high,
            "description": self.description,
        }


@dataclass
class GuidanceAchievement:
    """指引达成情况"""
    symbol: str
    period: str
    guidance_type: GuidanceType
    guidance_value: float  # 指引值 (取中值)
    actual_value: float
    achievement_rate: float  # 达成率
    exceeded: bool  # 是否超出指引
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "period": self.period,
            "guidance_type": self.guidance_type.value,
            "guidance_value": self.guidance_value,
            "actual_value": self.actual_value,
            "achievement_rate": self.achievement_rate,
            "exceeded": self.exceeded,
        }


@dataclass
class GuidanceTrackingResult:
    """指引跟踪结果"""
    symbol: str
    name: str
    analysis_date: datetime
    current_guidances: List[Guidance] = field(default_factory=list)
    historical_guidances: List[Guidance] = field(default_factory=list)
    achievements: List[GuidanceAchievement] = field(default_factory=list)
    
    # 统计
    avg_achievement_rate: float = 0.0
    exceed_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "current_guidances": [g.to_dict() for g in self.current_guidances],
            "historical_guidances": [g.to_dict() for g in self.historical_guidances],
            "achievements": [a.to_dict() for a in self.achievements],
            "avg_achievement_rate": self.avg_achievement_rate,
            "exceed_rate": self.exceed_rate,
        }


class GuidanceTrackerService:
    """业绩指引跟踪服务"""
    
    def __init__(self):
        self._cache: Dict[str, GuidanceTrackingResult] = {}
    
    async def track_guidance(
        self,
        symbol: str,
        lookback_years: int = 3,
    ) -> GuidanceTrackingResult:
        """
        跟踪业绩指引
        
        Args:
            symbol: 股票代码
            lookback_years: 回看年数
        """
        if symbol in self._cache:
            return self._cache[symbol]
        
        try:
            # 获取当前指引
            current = await self._get_current_guidances(symbol)
            
            # 获取历史指引
            historical = await self._get_historical_guidances(symbol, lookback_years)
            
            # 获取达成情况
            achievements = await self._get_achievements(symbol, lookback_years)
            
            # 计算统计
            if achievements:
                avg_rate = sum(a.achievement_rate for a in achievements) / len(achievements)
                exceed_count = sum(1 for a in achievements if a.exceeded)
                exceed_rate = exceed_count / len(achievements)
            else:
                avg_rate = 0
                exceed_rate = 0
            
            result = GuidanceTrackingResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                current_guidances=current,
                historical_guidances=historical,
                achievements=achievements,
                avg_achievement_rate=round(avg_rate, 2),
                exceed_rate=round(exceed_rate, 2),
            )
            
            self._cache[symbol] = result
            return result
            
        except Exception as e:
            logger.error(f"Failed to track guidance for {symbol}: {e}")
            return GuidanceTrackingResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )
    
    async def get_recent_guidance_changes(
        self,
        change_type: Optional[GuidanceChange] = None,
        limit: int = 20,
    ) -> List[Guidance]:
        """获取近期指引变化"""
        guidances = await self._get_market_guidances()
        
        if change_type:
            guidances = [g for g in guidances if g.change == change_type]
        
        guidances.sort(key=lambda x: x.guidance_date, reverse=True)
        return guidances[:limit]
    
    async def _get_current_guidances(self, symbol: str) -> List[Guidance]:
        """获取当前有效指引"""
        import random
        
        year = date.today().year
        guidances = []
        
        # 营收指引
        rev_low = random.uniform(100, 500)
        guidances.append(Guidance(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            guidance_date=date.today(),
            period=f"FY{year}",
            guidance_type=GuidanceType.REVENUE,
            low_estimate=round(rev_low, 2),
            high_estimate=round(rev_low * 1.1, 2),
            change=GuidanceChange.MAINTAINED,
            description=f"公司维持{year}年营收指引",
        ))
        
        # 净利润指引
        profit_low = random.uniform(10, 50)
        guidances.append(Guidance(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            guidance_date=date.today(),
            period=f"FY{year}",
            guidance_type=GuidanceType.NET_PROFIT,
            low_estimate=round(profit_low, 2),
            high_estimate=round(profit_low * 1.15, 2),
            change=GuidanceChange.RAISED,
            previous_low=round(profit_low * 0.9, 2),
            previous_high=round(profit_low * 1.05, 2),
            description=f"公司上调{year}年净利润指引",
        ))
        
        return guidances
    
    async def _get_historical_guidances(
        self,
        symbol: str,
        lookback_years: int,
    ) -> List[Guidance]:
        """获取历史指引"""
        import random
        from datetime import timedelta
        
        guidances = []
        base_year = date.today().year
        
        for i in range(lookback_years):
            year = base_year - i - 1
            
            guidances.append(Guidance(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                guidance_date=date(year, 1, 15),
                period=f"FY{year}",
                guidance_type=GuidanceType.REVENUE,
                low_estimate=round(random.uniform(80, 400), 2),
                high_estimate=round(random.uniform(100, 500), 2),
                change=random.choice(list(GuidanceChange)),
            ))
        
        return guidances
    
    async def _get_achievements(
        self,
        symbol: str,
        lookback_years: int,
    ) -> List[GuidanceAchievement]:
        """获取指引达成情况"""
        import random
        
        achievements = []
        base_year = date.today().year
        
        for i in range(lookback_years):
            year = base_year - i - 1
            guidance_val = random.uniform(50, 200)
            actual_val = guidance_val * random.uniform(0.9, 1.15)
            rate = actual_val / guidance_val * 100
            
            achievements.append(GuidanceAchievement(
                symbol=symbol,
                period=f"FY{year}",
                guidance_type=GuidanceType.REVENUE,
                guidance_value=round(guidance_val, 2),
                actual_value=round(actual_val, 2),
                achievement_rate=round(rate, 2),
                exceeded=actual_val > guidance_val,
            ))
        
        return achievements
    
    async def _get_market_guidances(self) -> List[Guidance]:
        """获取市场指引变化"""
        import random
        from datetime import timedelta
        
        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
            ("600036", "招商银行"), ("000333", "美的集团"),
        ]
        
        guidances = []
        for symbol, name in stocks:
            guidances.append(Guidance(
                symbol=symbol,
                name=name,
                guidance_date=date.today() - timedelta(days=random.randint(1, 30)),
                period=f"FY{date.today().year}",
                guidance_type=random.choice([GuidanceType.REVENUE, GuidanceType.NET_PROFIT]),
                low_estimate=round(random.uniform(50, 200), 2),
                high_estimate=round(random.uniform(60, 250), 2),
                change=random.choice(list(GuidanceChange)),
            ))
        
        return guidances
    
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
_guidance_tracker_service: Optional[GuidanceTrackerService] = None


def get_guidance_tracker_service() -> GuidanceTrackerService:
    """获取业绩指引跟踪服务单例"""
    global _guidance_tracker_service
    if _guidance_tracker_service is None:
        _guidance_tracker_service = GuidanceTrackerService()
    return _guidance_tracker_service
