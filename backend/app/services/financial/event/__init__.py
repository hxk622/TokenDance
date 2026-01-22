"""
事件驱动分析模块

包含：
- 业绩超预期/不及预期分析
- 业绩指引跟踪
- 股权激励分析
- 并购重组分析
- 分红派息跟踪
- 统一事件日历 (Event Calendar)
"""
from .dividend_tracker import (
    DividendAnalysisResult,
    DividendRecord,
    DividendTrackerService,
    DividendType,
    get_dividend_tracker_service,
)
from .earnings_surprise import (
    EarningsSurprise,
    EarningsSurpriseResult,
    EarningsSurpriseService,
    SurpriseType,
    get_earnings_surprise_service,
)
from .equity_incentive import (
    EquityIncentivePlan,
    EquityIncentiveService,
    IncentiveAnalysisResult,
    IncentiveStatus,
    IncentiveType,
    get_equity_incentive_service,
)
from .event_calendar import (
    EVENT_CONFIG,
    EventCalendarResult,
    EventCalendarService,
    EventImpact,
    EventImpactDirection,
    EventImportance,
    EventType,
    UpcomingEvent,
    get_event_calendar_service,
)
from .guidance_tracker import (
    Guidance,
    GuidanceTrackerService,
    GuidanceTrackingResult,
    GuidanceType,
    get_guidance_tracker_service,
)
from .ma_analysis import (
    MAAnalysisResult,
    MAAnalysisService,
    MADeal,
    MAStatus,
    MAType,
    get_ma_analysis_service,
)

__all__ = [
    # Earnings Surprise
    "EarningsSurpriseService",
    "get_earnings_surprise_service",
    "SurpriseType",
    "EarningsSurprise",
    "EarningsSurpriseResult",
    # Guidance Tracker
    "GuidanceTrackerService",
    "get_guidance_tracker_service",
    "GuidanceType",
    "Guidance",
    "GuidanceTrackingResult",
    # Equity Incentive
    "EquityIncentiveService",
    "get_equity_incentive_service",
    "IncentiveType",
    "IncentiveStatus",
    "EquityIncentivePlan",
    "IncentiveAnalysisResult",
    # M&A Analysis
    "MAAnalysisService",
    "get_ma_analysis_service",
    "MAType",
    "MAStatus",
    "MADeal",
    "MAAnalysisResult",
    # Dividend Tracker
    "DividendTrackerService",
    "get_dividend_tracker_service",
    "DividendType",
    "DividendRecord",
    "DividendAnalysisResult",
    # Event Calendar
    "EventCalendarService",
    "get_event_calendar_service",
    "EventType",
    "EventImportance",
    "EventImpactDirection",
    "EventImpact",
    "UpcomingEvent",
    "EventCalendarResult",
    "EVENT_CONFIG",
]
