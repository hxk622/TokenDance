# -*- coding: utf-8 -*-
"""
事件驱动分析模块

包含：
- 业绩超预期/不及预期分析
- 业绩指引跟踪
- 股权激励分析
- 并购重组分析
- 分红派息跟踪
"""
from .earnings_surprise import (
    EarningsSurpriseService,
    get_earnings_surprise_service,
    SurpriseType,
    EarningsSurprise,
    EarningsSurpriseResult,
)
from .guidance_tracker import (
    GuidanceTrackerService,
    get_guidance_tracker_service,
    GuidanceType,
    Guidance,
    GuidanceTrackingResult,
)
from .equity_incentive import (
    EquityIncentiveService,
    get_equity_incentive_service,
    IncentiveType,
    IncentiveStatus,
    EquityIncentivePlan,
    IncentiveAnalysisResult,
)
from .ma_analysis import (
    MAAnalysisService,
    get_ma_analysis_service,
    MAType,
    MAStatus,
    MADeal,
    MAAnalysisResult,
)
from .dividend_tracker import (
    DividendTrackerService,
    get_dividend_tracker_service,
    DividendType,
    DividendRecord,
    DividendAnalysisResult,
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
]
