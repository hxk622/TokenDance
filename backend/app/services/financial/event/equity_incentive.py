# -*- coding: utf-8 -*-
"""
EquityIncentiveService - 股权激励分析服务

提供：
1. 股权激励计划跟踪
2. 激励条件分析
3. 行权价与市价对比
4. 解锁进度跟踪
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class IncentiveType(str, Enum):
    """激励类型"""
    STOCK_OPTION = "stock_option"       # 股票期权
    RESTRICTED_STOCK = "restricted_stock"  # 限制性股票
    ESOP = "esop"                        # 员工持股计划
    PHANTOM_STOCK = "phantom_stock"      # 虚拟股票


class IncentiveStatus(str, Enum):
    """激励状态"""
    ANNOUNCED = "announced"     # 已公告
    APPROVED = "approved"       # 已获批
    GRANTED = "granted"         # 已授予
    VESTING = "vesting"         # 等待期
    VESTED = "vested"           # 已归属
    EXERCISED = "exercised"     # 已行权
    EXPIRED = "expired"         # 已过期
    CANCELLED = "cancelled"     # 已取消


@dataclass
class VestingCondition:
    """解锁条件"""
    condition_type: str  # 业绩条件类型
    target_metric: str   # 目标指标
    target_value: float  # 目标值
    current_value: Optional[float] = None
    achievement_pct: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "condition_type": self.condition_type,
            "target_metric": self.target_metric,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "achievement_pct": self.achievement_pct,
        }


@dataclass
class VestingSchedule:
    """解锁计划"""
    tranche: int         # 期数
    vesting_date: date   # 解锁日期
    shares: int          # 解锁股数
    exercise_price: float  # 行权价
    conditions: List[VestingCondition] = field(default_factory=list)
    status: IncentiveStatus = IncentiveStatus.VESTING
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tranche": self.tranche,
            "vesting_date": self.vesting_date.isoformat(),
            "shares": self.shares,
            "exercise_price": self.exercise_price,
            "conditions": [c.to_dict() for c in self.conditions],
            "status": self.status.value,
        }


@dataclass
class EquityIncentivePlan:
    """股权激励计划"""
    symbol: str
    name: str
    plan_id: str
    plan_name: str
    incentive_type: IncentiveType
    status: IncentiveStatus
    
    # 计划信息
    announce_date: date
    grant_date: Optional[date] = None
    total_shares: int = 0
    exercise_price: float = 0.0
    current_price: float = 0.0
    
    # 参与者
    total_participants: int = 0
    executive_participants: int = 0
    
    # 解锁计划
    vesting_schedules: List[VestingSchedule] = field(default_factory=list)
    
    # 分析
    price_premium: float = 0.0  # 当前价格相对行权价溢价
    dilution_pct: float = 0.0   # 稀释比例
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "plan_id": self.plan_id,
            "plan_name": self.plan_name,
            "incentive_type": self.incentive_type.value,
            "status": self.status.value,
            "announce_date": self.announce_date.isoformat(),
            "grant_date": self.grant_date.isoformat() if self.grant_date else None,
            "total_shares": self.total_shares,
            "exercise_price": self.exercise_price,
            "current_price": self.current_price,
            "total_participants": self.total_participants,
            "executive_participants": self.executive_participants,
            "vesting_schedules": [v.to_dict() for v in self.vesting_schedules],
            "price_premium": self.price_premium,
            "dilution_pct": self.dilution_pct,
        }


@dataclass
class IncentiveAnalysisResult:
    """股权激励分析结果"""
    symbol: str
    name: str
    analysis_date: datetime
    active_plans: List[EquityIncentivePlan] = field(default_factory=list)
    historical_plans: List[EquityIncentivePlan] = field(default_factory=list)
    
    # 统计
    total_active_shares: int = 0
    total_dilution_pct: float = 0.0
    upcoming_vestings: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "active_plans": [p.to_dict() for p in self.active_plans],
            "historical_plans": [p.to_dict() for p in self.historical_plans],
            "total_active_shares": self.total_active_shares,
            "total_dilution_pct": self.total_dilution_pct,
            "upcoming_vestings": self.upcoming_vestings,
        }


class EquityIncentiveService:
    """股权激励分析服务"""
    
    def __init__(self):
        self._cache: Dict[str, IncentiveAnalysisResult] = {}
    
    async def analyze_incentive_plans(
        self,
        symbol: str,
    ) -> IncentiveAnalysisResult:
        """分析股权激励计划"""
        if symbol in self._cache:
            return self._cache[symbol]
        
        try:
            # 获取活跃计划
            active = await self._get_active_plans(symbol)
            
            # 获取历史计划
            historical = await self._get_historical_plans(symbol)
            
            # 计算统计
            total_shares = sum(p.total_shares for p in active)
            total_dilution = sum(p.dilution_pct for p in active)
            
            # 计算即将解锁
            upcoming = 0
            for plan in active:
                for schedule in plan.vesting_schedules:
                    if schedule.status == IncentiveStatus.VESTING:
                        if (schedule.vesting_date - date.today()).days <= 90:
                            upcoming += 1
            
            result = IncentiveAnalysisResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                active_plans=active,
                historical_plans=historical,
                total_active_shares=total_shares,
                total_dilution_pct=round(total_dilution, 2),
                upcoming_vestings=upcoming,
            )
            
            self._cache[symbol] = result
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze incentive plans for {symbol}: {e}")
            return IncentiveAnalysisResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )
    
    async def get_recent_incentive_announcements(
        self,
        incentive_type: Optional[IncentiveType] = None,
        limit: int = 20,
    ) -> List[EquityIncentivePlan]:
        """获取近期股权激励公告"""
        plans = await self._get_market_plans()
        
        if incentive_type:
            plans = [p for p in plans if p.incentive_type == incentive_type]
        
        plans.sort(key=lambda x: x.announce_date, reverse=True)
        return plans[:limit]
    
    async def get_upcoming_vestings(
        self,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """获取即将解锁的股权激励"""
        return await self._get_vesting_calendar(days)
    
    async def _get_active_plans(self, symbol: str) -> List[EquityIncentivePlan]:
        """获取活跃激励计划"""
        import random
        from datetime import timedelta
        
        plans = []
        current_price = random.uniform(20, 200)
        
        # 模拟一个活跃计划
        exercise_price = current_price * random.uniform(0.6, 0.9)
        total_shares = random.randint(1000000, 10000000)
        
        vesting_schedules = []
        for i in range(3):
            vesting_schedules.append(VestingSchedule(
                tranche=i + 1,
                vesting_date=date.today() + timedelta(days=365 * (i + 1)),
                shares=total_shares // 3,
                exercise_price=exercise_price,
                conditions=[
                    VestingCondition(
                        condition_type="业绩条件",
                        target_metric="净利润增长率",
                        target_value=15 + i * 5,
                        current_value=random.uniform(10, 25),
                        achievement_pct=random.uniform(60, 120),
                    )
                ],
                status=IncentiveStatus.VESTING,
            ))
        
        plans.append(EquityIncentivePlan(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            plan_id=f"{symbol}_2024_01",
            plan_name=f"2024年股票期权激励计划",
            incentive_type=IncentiveType.STOCK_OPTION,
            status=IncentiveStatus.GRANTED,
            announce_date=date.today() - timedelta(days=random.randint(30, 180)),
            grant_date=date.today() - timedelta(days=random.randint(1, 30)),
            total_shares=total_shares,
            exercise_price=round(exercise_price, 2),
            current_price=round(current_price, 2),
            total_participants=random.randint(50, 500),
            executive_participants=random.randint(5, 20),
            vesting_schedules=vesting_schedules,
            price_premium=round((current_price - exercise_price) / exercise_price * 100, 2),
            dilution_pct=round(random.uniform(0.5, 3), 2),
        ))
        
        return plans
    
    async def _get_historical_plans(self, symbol: str) -> List[EquityIncentivePlan]:
        """获取历史激励计划"""
        import random
        from datetime import timedelta
        
        plans = []
        
        for i in range(2):
            year = date.today().year - i - 1
            plans.append(EquityIncentivePlan(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                plan_id=f"{symbol}_{year}_01",
                plan_name=f"{year}年限制性股票激励计划",
                incentive_type=IncentiveType.RESTRICTED_STOCK,
                status=IncentiveStatus.VESTED,
                announce_date=date(year, 3, 15),
                grant_date=date(year, 4, 1),
                total_shares=random.randint(500000, 5000000),
                exercise_price=round(random.uniform(15, 100), 2),
                current_price=round(random.uniform(20, 150), 2),
                total_participants=random.randint(30, 300),
                executive_participants=random.randint(3, 15),
            ))
        
        return plans
    
    async def _get_market_plans(self) -> List[EquityIncentivePlan]:
        """获取市场股权激励公告"""
        import random
        from datetime import timedelta
        
        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
            ("600036", "招商银行"), ("000333", "美的集团"),
        ]
        
        plans = []
        for symbol, name in stocks:
            current_price = random.uniform(20, 200)
            exercise_price = current_price * random.uniform(0.6, 0.9)
            
            plans.append(EquityIncentivePlan(
                symbol=symbol,
                name=name,
                plan_id=f"{symbol}_{date.today().year}_01",
                plan_name=f"{date.today().year}年股权激励计划",
                incentive_type=random.choice(list(IncentiveType)),
                status=random.choice([IncentiveStatus.ANNOUNCED, IncentiveStatus.APPROVED, IncentiveStatus.GRANTED]),
                announce_date=date.today() - timedelta(days=random.randint(1, 60)),
                total_shares=random.randint(1000000, 10000000),
                exercise_price=round(exercise_price, 2),
                current_price=round(current_price, 2),
            ))
        
        return plans
    
    async def _get_vesting_calendar(self, days: int) -> List[Dict[str, Any]]:
        """获取解锁日历"""
        import random
        from datetime import timedelta
        
        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
        ]
        
        calendar = []
        for symbol, name in stocks:
            calendar.append({
                "symbol": symbol,
                "name": name,
                "vesting_date": (date.today() + timedelta(days=random.randint(1, days))).isoformat(),
                "shares": random.randint(100000, 1000000),
                "exercise_price": round(random.uniform(20, 100), 2),
                "plan_name": f"{date.today().year - 1}年股票期权激励计划",
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
_equity_incentive_service: Optional[EquityIncentiveService] = None


def get_equity_incentive_service() -> EquityIncentiveService:
    """获取股权激励服务单例"""
    global _equity_incentive_service
    if _equity_incentive_service is None:
        _equity_incentive_service = EquityIncentiveService()
    return _equity_incentive_service
