"""
EventCalendarService - 统一事件日历服务

提供：
1. 聚合多种事件源（财报、分红、股权激励解锁、业绩指引、年报、股东大会）
2. 未来90天事件Timeline
3. 历史事件影响分析（事件前后股价表现）
4. 事件重要性评级
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    EARNINGS = "earnings"           # 财报发布
    DIVIDEND = "dividend"           # 分红派息
    EQUITY_UNLOCK = "equity_unlock" # 股权激励解锁
    GUIDANCE = "guidance"           # 业绩指引
    ANNUAL_REPORT = "annual_report" # 年报发布
    SHAREHOLDER_MEETING = "shareholder_meeting"  # 股东大会
    BOND_MATURITY = "bond_maturity"  # 债券到期
    ANALYST_MEETING = "analyst_meeting"  # 分析师会议
    PRODUCT_LAUNCH = "product_launch"  # 产品发布


class EventImportance(str, Enum):
    """事件重要性"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventImpactDirection(str, Enum):
    """历史事件影响方向"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class EventImpact:
    """事件历史影响分析"""
    event_type: EventType
    event_date: date

    # 股价反应
    price_change_1d: float = 0.0    # 事件后1日涨跌幅 %
    price_change_5d: float = 0.0    # 事件后5日涨跌幅 %
    price_change_20d: float = 0.0   # 事件后20日涨跌幅 %

    # 相对大盘表现
    excess_return_1d: float = 0.0   # 相对指数超额收益 %
    excess_return_5d: float = 0.0

    # 成交量变化
    volume_change_pct: float = 0.0  # 事件日成交量变化 %

    # 方向判断
    direction: EventImpactDirection = EventImpactDirection.NEUTRAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "event_date": self.event_date.isoformat(),
            "price_change_1d": self.price_change_1d,
            "price_change_5d": self.price_change_5d,
            "price_change_20d": self.price_change_20d,
            "excess_return_1d": self.excess_return_1d,
            "excess_return_5d": self.excess_return_5d,
            "volume_change_pct": self.volume_change_pct,
            "direction": self.direction.value,
        }


@dataclass
class UpcomingEvent:
    """即将发生的事件"""
    symbol: str
    name: str
    event_type: EventType
    event_date: date
    importance: EventImportance

    # 事件详情
    title: str
    description: str = ""

    # 额外信息（根据事件类型不同）
    metadata: dict[str, Any] = field(default_factory=dict)

    # 历史影响参考
    historical_impact: EventImpact | None = None

    # 距今天数
    days_until: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "event_type": self.event_type.value,
            "event_date": self.event_date.isoformat(),
            "importance": self.importance.value,
            "title": self.title,
            "description": self.description,
            "metadata": self.metadata,
            "historical_impact": self.historical_impact.to_dict() if self.historical_impact else None,
            "days_until": self.days_until,
        }


@dataclass
class EventCalendarResult:
    """事件日历查询结果"""
    symbol: str
    name: str
    query_date: datetime

    # 事件列表
    upcoming_events: list[UpcomingEvent] = field(default_factory=list)

    # 按类型分组统计
    events_by_type: dict[str, int] = field(default_factory=dict)

    # 最近重要事件
    next_critical_event: UpcomingEvent | None = None

    # 历史事件影响汇总
    historical_impacts: list[EventImpact] = field(default_factory=list)
    avg_post_event_return: float = 0.0  # 历史事件后平均收益

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "query_date": self.query_date.isoformat(),
            "upcoming_events": [e.to_dict() for e in self.upcoming_events],
            "events_by_type": self.events_by_type,
            "next_critical_event": self.next_critical_event.to_dict() if self.next_critical_event else None,
            "historical_impacts": [h.to_dict() for h in self.historical_impacts],
            "avg_post_event_return": self.avg_post_event_return,
        }


# 事件类型配置
EVENT_CONFIG: dict[EventType, dict[str, Any]] = {
    EventType.EARNINGS: {
        "icon": "TrendingUp",
        "color": "#00D9FF",  # 青色
        "default_importance": EventImportance.HIGH,
        "typical_volatility": 3.5,  # 典型波动率 %
    },
    EventType.DIVIDEND: {
        "icon": "DollarSign",
        "color": "#00FF88",  # 绿色
        "default_importance": EventImportance.MEDIUM,
        "typical_volatility": 1.0,
    },
    EventType.EQUITY_UNLOCK: {
        "icon": "Unlock",
        "color": "#FFB800",  # 琥珀色
        "default_importance": EventImportance.HIGH,
        "typical_volatility": 2.5,
    },
    EventType.GUIDANCE: {
        "icon": "Target",
        "color": "#00D9FF",
        "default_importance": EventImportance.MEDIUM,
        "typical_volatility": 2.0,
    },
    EventType.ANNUAL_REPORT: {
        "icon": "FileText",
        "color": "#6366F1",  # 靛蓝色
        "default_importance": EventImportance.MEDIUM,
        "typical_volatility": 1.5,
    },
    EventType.SHAREHOLDER_MEETING: {
        "icon": "Users",
        "color": "#8B5CF6",  # 紫色
        "default_importance": EventImportance.MEDIUM,
        "typical_volatility": 1.0,
    },
    EventType.BOND_MATURITY: {
        "icon": "Calendar",
        "color": "#F59E0B",  # 橙色
        "default_importance": EventImportance.LOW,
        "typical_volatility": 0.5,
    },
    EventType.ANALYST_MEETING: {
        "icon": "Mic",
        "color": "#10B981",  # 翠绿
        "default_importance": EventImportance.LOW,
        "typical_volatility": 1.0,
    },
    EventType.PRODUCT_LAUNCH: {
        "icon": "Rocket",
        "color": "#EC4899",  # 粉色
        "default_importance": EventImportance.MEDIUM,
        "typical_volatility": 2.0,
    },
}


class EventCalendarService:
    """统一事件日历服务"""

    def __init__(self):
        self._cache: dict[str, EventCalendarResult] = {}
        # 股票名称映射
        self._stock_names: dict[str, str] = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000568": "泸州老窖",
            "000651": "格力电器",
            "000333": "美的集团",
            "601318": "中国平安",
            "600036": "招商银行",
            "601166": "兴业银行",
        }

    async def get_upcoming_events(
        self,
        symbol: str,
        days_ahead: int = 90,
        event_types: list[EventType] | None = None,
        min_importance: EventImportance = EventImportance.LOW,
    ) -> EventCalendarResult:
        """
        获取未来事件日历

        Args:
            symbol: 股票代码
            days_ahead: 未来天数
            event_types: 筛选事件类型
            min_importance: 最低重要性
        """
        cache_key = f"{symbol}_{days_ahead}_{event_types}_{min_importance}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            # 检查缓存是否过期（1小时）
            if (datetime.now() - cached.query_date).total_seconds() < 3600:
                return cached

        try:
            # 从各数据源聚合事件
            events: list[UpcomingEvent] = []

            # 1. 财报日历
            earnings_events = await self._get_earnings_events(symbol, days_ahead)
            events.extend(earnings_events)

            # 2. 分红日历
            dividend_events = await self._get_dividend_events(symbol, days_ahead)
            events.extend(dividend_events)

            # 3. 股权激励解锁
            unlock_events = await self._get_equity_unlock_events(symbol, days_ahead)
            events.extend(unlock_events)

            # 4. 股东大会
            meeting_events = await self._get_shareholder_meeting_events(symbol, days_ahead)
            events.extend(meeting_events)

            # 5. 年报/季报发布
            report_events = await self._get_annual_report_events(symbol, days_ahead)
            events.extend(report_events)

            # 筛选
            if event_types:
                events = [e for e in events if e.event_type in event_types]

            importance_order = [EventImportance.LOW, EventImportance.MEDIUM, EventImportance.HIGH, EventImportance.CRITICAL]
            min_idx = importance_order.index(min_importance)
            events = [e for e in events if importance_order.index(e.importance) >= min_idx]

            # 按日期排序
            today = date.today()
            for event in events:
                event.days_until = (event.event_date - today).days
            events.sort(key=lambda x: x.event_date)

            # 统计
            events_by_type: dict[str, int] = {}
            for e in events:
                events_by_type[e.event_type.value] = events_by_type.get(e.event_type.value, 0) + 1

            # 找最近的重要事件
            critical_events = [e for e in events if e.importance in [EventImportance.HIGH, EventImportance.CRITICAL]]
            next_critical = critical_events[0] if critical_events else None

            # 获取历史影响
            historical_impacts = await self._get_historical_impacts(symbol)
            avg_return = sum(h.price_change_5d for h in historical_impacts) / len(historical_impacts) if historical_impacts else 0

            result = EventCalendarResult(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                query_date=datetime.now(),
                upcoming_events=events,
                events_by_type=events_by_type,
                next_critical_event=next_critical,
                historical_impacts=historical_impacts,
                avg_post_event_return=round(avg_return, 2),
            )

            self._cache[cache_key] = result
            return result

        except Exception as e:
            logger.error(f"Failed to get upcoming events for {symbol}: {e}")
            return EventCalendarResult(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                query_date=datetime.now(),
            )

    async def get_historical_event_impact(
        self,
        symbol: str,
        event_type: EventType,
        lookback_events: int = 8,
    ) -> list[EventImpact]:
        """
        获取历史事件影响分析

        Args:
            symbol: 股票代码
            event_type: 事件类型
            lookback_events: 回看事件数量
        """
        # Mock数据 - 实际应从数据库/API获取
        return await self._get_mock_historical_impacts(symbol, event_type, lookback_events)

    async def _get_earnings_events(self, symbol: str, days_ahead: int) -> list[UpcomingEvent]:
        """获取财报发布事件"""
        # Mock数据
        today = date.today()
        events = []

        # 模拟季度财报
        current_year = today.year

        # 贵州茅台的财报日期（示例）
        if symbol == "600519":
            # 假设下个季度财报在30天后
            next_earnings = today + timedelta(days=45)
            events.append(UpcomingEvent(
                symbol=symbol,
                name="贵州茅台",
                event_type=EventType.EARNINGS,
                event_date=next_earnings,
                importance=EventImportance.CRITICAL,
                title=f"{current_year}年Q3季报发布",
                description="预计披露第三季度财务数据，关注营收增速和净利润表现",
                metadata={
                    "period": f"{current_year}Q3",
                    "consensus_revenue": "330亿",
                    "consensus_profit": "165亿",
                },
                historical_impact=EventImpact(
                    event_type=EventType.EARNINGS,
                    event_date=today - timedelta(days=90),
                    price_change_1d=2.3,
                    price_change_5d=4.1,
                    price_change_20d=6.8,
                    excess_return_1d=1.8,
                    excess_return_5d=3.2,
                    volume_change_pct=85.0,
                    direction=EventImpactDirection.POSITIVE,
                ),
            ))
        elif symbol == "000858":
            next_earnings = today + timedelta(days=60)
            events.append(UpcomingEvent(
                symbol=symbol,
                name="五粮液",
                event_type=EventType.EARNINGS,
                event_date=next_earnings,
                importance=EventImportance.CRITICAL,
                title=f"{current_year}年Q3季报发布",
                description="关注高端白酒销量和价格策略",
                metadata={
                    "period": f"{current_year}Q3",
                },
                historical_impact=EventImpact(
                    event_type=EventType.EARNINGS,
                    event_date=today - timedelta(days=90),
                    price_change_1d=1.5,
                    price_change_5d=2.8,
                    price_change_20d=3.5,
                    direction=EventImpactDirection.POSITIVE,
                ),
            ))
        else:
            # 通用mock
            next_earnings = today + timedelta(days=50)
            events.append(UpcomingEvent(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                event_type=EventType.EARNINGS,
                event_date=next_earnings,
                importance=EventImportance.HIGH,
                title=f"{current_year}年Q3季报发布",
                description="季度财报披露",
                metadata={"period": f"{current_year}Q3"},
            ))

        return [e for e in events if (e.event_date - today).days <= days_ahead]

    async def _get_dividend_events(self, symbol: str, days_ahead: int) -> list[UpcomingEvent]:
        """获取分红事件"""
        today = date.today()
        events = []

        if symbol == "600519":
            # 茅台年度分红
            ex_date = today + timedelta(days=75)
            events.append(UpcomingEvent(
                symbol=symbol,
                name="贵州茅台",
                event_type=EventType.DIVIDEND,
                event_date=ex_date,
                importance=EventImportance.MEDIUM,
                title="2024年度分红派息",
                description="每10股派发现金红利275.00元（含税）",
                metadata={
                    "cash_per_share": 27.5,
                    "dividend_yield": 1.2,
                    "record_date": (ex_date - timedelta(days=1)).isoformat(),
                    "pay_date": (ex_date + timedelta(days=5)).isoformat(),
                },
            ))
        elif symbol == "601318":
            # 中国平安半年分红
            ex_date = today + timedelta(days=40)
            events.append(UpcomingEvent(
                symbol=symbol,
                name="中国平安",
                event_type=EventType.DIVIDEND,
                event_date=ex_date,
                importance=EventImportance.MEDIUM,
                title="2024年中期分红",
                description="每10股派发现金红利9.30元（含税）",
                metadata={
                    "cash_per_share": 0.93,
                    "dividend_yield": 1.8,
                },
            ))

        return [e for e in events if 0 < (e.event_date - today).days <= days_ahead]

    async def _get_equity_unlock_events(self, symbol: str, days_ahead: int) -> list[UpcomingEvent]:
        """获取股权激励解锁事件"""
        today = date.today()
        events = []

        if symbol == "600519":
            unlock_date = today + timedelta(days=120)
            events.append(UpcomingEvent(
                symbol=symbol,
                name="贵州茅台",
                event_type=EventType.EQUITY_UNLOCK,
                event_date=unlock_date,
                importance=EventImportance.HIGH,
                title="2022年股权激励第二期解锁",
                description="约500万股限制性股票解锁，占总股本0.4%",
                metadata={
                    "unlock_shares": 5000000,
                    "unlock_ratio": 0.4,
                    "grant_price": 869.0,
                    "current_price": 1500.0,
                    "potential_supply_pressure": "中等",
                },
                historical_impact=EventImpact(
                    event_type=EventType.EQUITY_UNLOCK,
                    event_date=today - timedelta(days=365),
                    price_change_1d=-1.2,
                    price_change_5d=-0.5,
                    price_change_20d=2.3,
                    volume_change_pct=45.0,
                    direction=EventImpactDirection.NEGATIVE,
                ),
            ))

        return [e for e in events if 0 < (e.event_date - today).days <= days_ahead]

    async def _get_shareholder_meeting_events(self, symbol: str, days_ahead: int) -> list[UpcomingEvent]:
        """获取股东大会事件"""
        today = date.today()
        events = []

        # 年度股东大会通常在4-5月
        meeting_date = today + timedelta(days=85)
        if symbol in self._stock_names:
            events.append(UpcomingEvent(
                symbol=symbol,
                name=self._stock_names.get(symbol, symbol),
                event_type=EventType.SHAREHOLDER_MEETING,
                event_date=meeting_date,
                importance=EventImportance.LOW,
                title="2024年度股东大会",
                description="审议年度报告、利润分配方案、董事会换届等议案",
                metadata={
                    "meeting_type": "annual",
                    "key_proposals": ["利润分配", "董事会换届", "薪酬方案"],
                },
            ))

        return [e for e in events if 0 < (e.event_date - today).days <= days_ahead]

    async def _get_annual_report_events(self, symbol: str, days_ahead: int) -> list[UpcomingEvent]:
        """获取年报/季报事件"""
        today = date.today()
        events = []
        current_year = today.year

        # 年报通常在次年1-4月披露
        if today.month <= 4:
            report_date = date(current_year, 4, 25)
            if (report_date - today).days <= days_ahead and (report_date - today).days > 0:
                events.append(UpcomingEvent(
                    symbol=symbol,
                    name=self._stock_names.get(symbol, symbol),
                    event_type=EventType.ANNUAL_REPORT,
                    event_date=report_date,
                    importance=EventImportance.HIGH,
                    title=f"{current_year-1}年年度报告发布",
                    description="全年财务数据及经营情况详细披露",
                    metadata={
                        "report_type": "annual",
                        "fiscal_year": current_year - 1,
                    },
                ))

        return events

    async def _get_historical_impacts(self, symbol: str) -> list[EventImpact]:
        """获取历史事件影响汇总"""
        impacts = []
        today = date.today()

        # Mock历史财报影响
        for i in range(4):
            impacts.append(EventImpact(
                event_type=EventType.EARNINGS,
                event_date=today - timedelta(days=90 * (i + 1)),
                price_change_1d=2.1 - i * 0.5 + (0.5 if i % 2 == 0 else -0.3),
                price_change_5d=3.5 - i * 0.3,
                price_change_20d=5.2 - i * 0.4,
                excess_return_1d=1.5,
                excess_return_5d=2.8,
                volume_change_pct=60 + i * 10,
                direction=EventImpactDirection.POSITIVE if i < 3 else EventImpactDirection.NEUTRAL,
            ))

        return impacts

    async def _get_mock_historical_impacts(
        self,
        symbol: str,
        event_type: EventType,
        lookback_events: int,
    ) -> list[EventImpact]:
        """获取Mock历史事件影响"""
        impacts = []
        today = date.today()

        # 根据事件类型生成不同的mock数据
        config = EVENT_CONFIG.get(event_type, {})
        typical_vol = config.get("typical_volatility", 2.0)

        for i in range(lookback_events):
            # 模拟不同的历史反应
            base_change = typical_vol * (1 - i * 0.1)
            is_positive = i % 3 != 2  # 2/3概率正向

            impact = EventImpact(
                event_type=event_type,
                event_date=today - timedelta(days=90 * (i + 1)),
                price_change_1d=base_change if is_positive else -base_change * 0.8,
                price_change_5d=base_change * 1.5 if is_positive else -base_change,
                price_change_20d=base_change * 2 if is_positive else -base_change * 0.5,
                excess_return_1d=base_change * 0.7 if is_positive else -base_change * 0.5,
                excess_return_5d=base_change if is_positive else -base_change * 0.3,
                volume_change_pct=50 + i * 5,
                direction=EventImpactDirection.POSITIVE if is_positive else EventImpactDirection.NEGATIVE,
            )
            impacts.append(impact)

        return impacts


# 单例
_event_calendar_service: EventCalendarService | None = None


def get_event_calendar_service() -> EventCalendarService:
    """获取事件日历服务单例"""
    global _event_calendar_service
    if _event_calendar_service is None:
        _event_calendar_service = EventCalendarService()
    return _event_calendar_service
