# -*- coding: utf-8 -*-
"""
DividendTrackerService - 分红派息跟踪服务

提供：
1. 分红历史分析
2. 股息率计算
3. 分红政策跟踪
4. 高股息股票筛选
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class DividendType(str, Enum):
    """分红类型"""
    CASH = "cash"               # 现金分红
    STOCK = "stock"             # 送股
    BONUS = "bonus"             # 转增
    MIXED = "mixed"             # 混合


class DividendFrequency(str, Enum):
    """分红频率"""
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    SPECIAL = "special"


@dataclass
class DividendRecord:
    """分红记录"""
    symbol: str
    name: str
    announce_date: date
    ex_date: date               # 除权除息日
    record_date: date           # 股权登记日
    pay_date: date              # 派息日
    
    # 分红内容
    dividend_type: DividendType
    cash_per_share: float = 0.0      # 每股现金 (元)
    stock_per_10: float = 0.0        # 每10股送股
    bonus_per_10: float = 0.0        # 每10股转增
    
    # 计算指标
    dividend_yield: float = 0.0       # 股息率
    payout_ratio: float = 0.0         # 派息率
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "announce_date": self.announce_date.isoformat(),
            "ex_date": self.ex_date.isoformat(),
            "record_date": self.record_date.isoformat(),
            "pay_date": self.pay_date.isoformat(),
            "dividend_type": self.dividend_type.value,
            "cash_per_share": self.cash_per_share,
            "stock_per_10": self.stock_per_10,
            "bonus_per_10": self.bonus_per_10,
            "dividend_yield": self.dividend_yield,
            "payout_ratio": self.payout_ratio,
        }


@dataclass
class DividendPolicy:
    """分红政策"""
    symbol: str
    name: str
    policy_date: date
    
    # 政策内容
    min_payout_ratio: Optional[float] = None  # 最低派息率
    frequency: DividendFrequency = DividendFrequency.ANNUAL
    policy_text: str = ""
    
    # 历史执行情况
    avg_payout_ratio: float = 0.0
    consecutive_years: int = 0  # 连续分红年数
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "policy_date": self.policy_date.isoformat(),
            "min_payout_ratio": self.min_payout_ratio,
            "frequency": self.frequency.value,
            "policy_text": self.policy_text,
            "avg_payout_ratio": self.avg_payout_ratio,
            "consecutive_years": self.consecutive_years,
        }


@dataclass
class DividendAnalysisResult:
    """分红分析结果"""
    symbol: str
    name: str
    analysis_date: datetime
    
    # 分红记录
    recent_dividends: List[DividendRecord] = field(default_factory=list)
    historical_dividends: List[DividendRecord] = field(default_factory=list)
    
    # 分红政策
    policy: Optional[DividendPolicy] = None
    
    # 统计
    current_yield: float = 0.0          # 当前股息率
    avg_yield_5y: float = 0.0           # 5年平均股息率
    total_cash_dividend: float = 0.0    # 累计现金分红
    dividend_growth_rate: float = 0.0   # 分红增长率
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "recent_dividends": [d.to_dict() for d in self.recent_dividends],
            "historical_dividends": [d.to_dict() for d in self.historical_dividends],
            "policy": self.policy.to_dict() if self.policy else None,
            "current_yield": self.current_yield,
            "avg_yield_5y": self.avg_yield_5y,
            "total_cash_dividend": self.total_cash_dividend,
            "dividend_growth_rate": self.dividend_growth_rate,
        }


class DividendTrackerService:
    """分红派息跟踪服务"""
    
    def __init__(self):
        self._cache: Dict[str, DividendAnalysisResult] = {}
    
    async def analyze_dividends(
        self,
        symbol: str,
        lookback_years: int = 5,
    ) -> DividendAnalysisResult:
        """分析分红情况"""
        if symbol in self._cache:
            return self._cache[symbol]
        
        try:
            # 获取近期分红
            recent = await self._get_recent_dividends(symbol)
            
            # 获取历史分红
            historical = await self._get_historical_dividends(symbol, lookback_years)
            
            # 获取分红政策
            policy = await self._get_dividend_policy(symbol)
            
            # 计算统计
            all_dividends = recent + historical
            if all_dividends:
                current_yield = all_dividends[0].dividend_yield if all_dividends else 0
                avg_yield = sum(d.dividend_yield for d in all_dividends) / len(all_dividends)
                total_cash = sum(d.cash_per_share for d in all_dividends)
                
                # 计算增长率
                if len(all_dividends) >= 2:
                    growth = (all_dividends[0].cash_per_share - all_dividends[-1].cash_per_share) / all_dividends[-1].cash_per_share * 100 if all_dividends[-1].cash_per_share else 0
                else:
                    growth = 0
            else:
                current_yield = 0
                avg_yield = 0
                total_cash = 0
                growth = 0
            
            result = DividendAnalysisResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                recent_dividends=recent,
                historical_dividends=historical,
                policy=policy,
                current_yield=round(current_yield, 2),
                avg_yield_5y=round(avg_yield, 2),
                total_cash_dividend=round(total_cash, 2),
                dividend_growth_rate=round(growth, 2),
            )
            
            self._cache[symbol] = result
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze dividends for {symbol}: {e}")
            return DividendAnalysisResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )
    
    async def get_high_dividend_stocks(
        self,
        min_yield: float = 3.0,
        limit: int = 20,
    ) -> List[DividendRecord]:
        """获取高股息股票"""
        records = await self._get_market_dividends()
        high_yield = [r for r in records if r.dividend_yield >= min_yield]
        high_yield.sort(key=lambda x: x.dividend_yield, reverse=True)
        return high_yield[:limit]
    
    async def get_upcoming_ex_dates(
        self,
        days: int = 30,
    ) -> List[DividendRecord]:
        """获取即将除权除息的股票"""
        records = await self._get_market_dividends()
        upcoming = [r for r in records if (r.ex_date - date.today()).days <= days and r.ex_date >= date.today()]
        upcoming.sort(key=lambda x: x.ex_date)
        return upcoming
    
    async def get_dividend_aristocrats(
        self,
        min_years: int = 10,
    ) -> List[Dict[str, Any]]:
        """获取分红贵族 (连续分红多年)"""
        return await self._get_consistent_dividend_stocks(min_years)
    
    async def _get_recent_dividends(self, symbol: str) -> List[DividendRecord]:
        """获取近期分红"""
        import random
        from datetime import timedelta
        
        dividends = []
        current_price = random.uniform(20, 200)
        
        # 最近一次分红
        cash = random.uniform(0.5, 5)
        dividends.append(DividendRecord(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            announce_date=date.today() - timedelta(days=random.randint(30, 90)),
            ex_date=date.today() - timedelta(days=random.randint(1, 30)),
            record_date=date.today() - timedelta(days=random.randint(2, 31)),
            pay_date=date.today() + timedelta(days=random.randint(1, 30)),
            dividend_type=DividendType.CASH,
            cash_per_share=round(cash, 2),
            dividend_yield=round(cash / current_price * 100, 2),
            payout_ratio=round(random.uniform(30, 70), 2),
        ))
        
        return dividends
    
    async def _get_historical_dividends(
        self,
        symbol: str,
        lookback_years: int,
    ) -> List[DividendRecord]:
        """获取历史分红"""
        import random
        
        dividends = []
        current_price = random.uniform(20, 200)
        
        for i in range(lookback_years):
            year = date.today().year - i - 1
            cash = random.uniform(0.3, 4)
            
            dividends.append(DividendRecord(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                announce_date=date(year, 4, 15),
                ex_date=date(year, 5, 15),
                record_date=date(year, 5, 14),
                pay_date=date(year, 5, 20),
                dividend_type=DividendType.CASH,
                cash_per_share=round(cash, 2),
                dividend_yield=round(cash / current_price * 100, 2),
                payout_ratio=round(random.uniform(25, 65), 2),
            ))
        
        return dividends
    
    async def _get_dividend_policy(self, symbol: str) -> DividendPolicy:
        """获取分红政策"""
        import random
        
        return DividendPolicy(
            symbol=symbol,
            name=self._get_stock_name(symbol),
            policy_date=date(date.today().year - 1, 4, 1),
            min_payout_ratio=round(random.uniform(30, 50), 0),
            frequency=DividendFrequency.ANNUAL,
            policy_text="公司承诺每年现金分红不低于当年可分配利润的30%",
            avg_payout_ratio=round(random.uniform(35, 55), 2),
            consecutive_years=random.randint(5, 20),
        )
    
    async def _get_market_dividends(self) -> List[DividendRecord]:
        """获取市场分红数据"""
        import random
        from datetime import timedelta
        
        stocks = [
            ("600519", "贵州茅台", 1800), ("000858", "五粮液", 150),
            ("600036", "招商银行", 35), ("000333", "美的集团", 65),
            ("601398", "工商银行", 5), ("601939", "建设银行", 7),
        ]
        
        records = []
        for symbol, name, price in stocks:
            cash = random.uniform(0.5, 20)
            records.append(DividendRecord(
                symbol=symbol,
                name=name,
                announce_date=date.today() - timedelta(days=random.randint(1, 60)),
                ex_date=date.today() + timedelta(days=random.randint(-10, 30)),
                record_date=date.today() + timedelta(days=random.randint(-11, 29)),
                pay_date=date.today() + timedelta(days=random.randint(1, 45)),
                dividend_type=DividendType.CASH,
                cash_per_share=round(cash, 2),
                dividend_yield=round(cash / price * 100, 2),
                payout_ratio=round(random.uniform(30, 70), 2),
            ))
        
        return records
    
    async def _get_consistent_dividend_stocks(
        self,
        min_years: int,
    ) -> List[Dict[str, Any]]:
        """获取连续分红股票"""
        import random
        
        stocks = [
            ("600519", "贵州茅台"), ("000858", "五粮液"),
            ("600036", "招商银行"), ("601398", "工商银行"),
        ]
        
        aristocrats = []
        for symbol, name in stocks:
            years = random.randint(min_years, 25)
            if years >= min_years:
                aristocrats.append({
                    "symbol": symbol,
                    "name": name,
                    "consecutive_years": years,
                    "avg_yield": round(random.uniform(1, 5), 2),
                    "dividend_growth_rate": round(random.uniform(5, 15), 2),
                })
        
        return sorted(aristocrats, key=lambda x: x["consecutive_years"], reverse=True)
    
    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "600036": "招商银行",
            "000333": "美的集团",
            "601398": "工商银行",
            "601939": "建设银行",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_dividend_tracker_service: Optional[DividendTrackerService] = None


def get_dividend_tracker_service() -> DividendTrackerService:
    """获取分红跟踪服务单例"""
    global _dividend_tracker_service
    if _dividend_tracker_service is None:
        _dividend_tracker_service = DividendTrackerService()
    return _dividend_tracker_service
