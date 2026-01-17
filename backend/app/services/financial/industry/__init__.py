"""
Industry 行业分析模块

提供：
1. 同行对比分析
2. 行业内排名
3. 行业轮动分析
4. 板块地图
"""
from .industry_ranking import (
    IndustryRankingService,
    RankingResult,
    get_industry_ranking_service,
)
from .peer_comparison import (
    CompanyMetrics,
    PeerComparisonResult,
    PeerComparisonService,
    get_peer_comparison_service,
)
from .rotation_analysis import (
    MomentumSignal,
    RotationAnalysisResult,
    RotationAnalysisService,
    get_rotation_analysis_service,
)
from .sector_map import (
    SectorMapService,
    SectorNode,
    get_sector_map_service,
)

__all__ = [
    # Peer Comparison
    "PeerComparisonService",
    "PeerComparisonResult",
    "CompanyMetrics",
    "get_peer_comparison_service",
    # Industry Ranking
    "IndustryRankingService",
    "RankingResult",
    "get_industry_ranking_service",
    # Rotation Analysis
    "RotationAnalysisService",
    "RotationAnalysisResult",
    "MomentumSignal",
    "get_rotation_analysis_service",
    # Sector Map
    "SectorMapService",
    "SectorNode",
    "get_sector_map_service",
]
