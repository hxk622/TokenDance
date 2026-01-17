# -*- coding: utf-8 -*-
"""
Financial Services - 金融分析服务模块

提供专业的金融分析能力：
1. FinancialAnalyzer - 财务分析（盈利/成长/偿债/现金流）
2. ValuationAnalyzer - 估值分析（PE/PB/DCF/行业对比）

使用方法：
    from app.services.financial import (
        get_financial_analyzer,
        get_valuation_analyzer,
    )
    
    # 财务分析
    analyzer = get_financial_analyzer()
    result = await analyzer.analyze("AAPL")
    
    # 估值分析
    valuation = get_valuation_analyzer()
    result = await valuation.analyze("AAPL")
"""

from app.services.financial.analyzer import (
    FinancialAnalyzer,
    FinancialAnalysisResult,
    ProfitabilityMetrics,
    GrowthMetrics,
    SolvencyMetrics,
    EfficiencyMetrics,
    CashFlowMetrics,
    HealthLevel,
    get_financial_analyzer,
)

from app.services.financial.valuation import (
    ValuationAnalyzer,
    ValuationResult,
    RelativeValuation,
    HistoricalValuation,
    IndustryComparison,
    DCFValuation,
    ValuationLevel,
    get_valuation_analyzer,
)

from app.services.financial.technical import (
    TechnicalIndicators,
    TechnicalAnalysisResult,
    TrendIndicators,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
    TrendSignal,
    get_technical_indicators,
)

from app.services.financial.cache import (
    AnalysisCache,
    get_analysis_cache,
    run_parallel_analysis,
    benchmark_analysis,
    CACHE_TTL,
)

__all__ = [
    # Financial Analysis
    "FinancialAnalyzer",
    "FinancialAnalysisResult",
    "ProfitabilityMetrics",
    "GrowthMetrics",
    "SolvencyMetrics",
    "EfficiencyMetrics",
    "CashFlowMetrics",
    "HealthLevel",
    "get_financial_analyzer",
    # Valuation Analysis
    "ValuationAnalyzer",
    "ValuationResult",
    "RelativeValuation",
    "HistoricalValuation",
    "IndustryComparison",
    "DCFValuation",
    "ValuationLevel",
    "get_valuation_analyzer",
    # Technical Analysis
    "TechnicalIndicators",
    "TechnicalAnalysisResult",
    "TrendIndicators",
    "MomentumIndicators",
    "VolatilityIndicators",
    "VolumeIndicators",
    "TrendSignal",
    "get_technical_indicators",
    # Cache & Performance
    "AnalysisCache",
    "get_analysis_cache",
    "run_parallel_analysis",
    "benchmark_analysis",
    "CACHE_TTL",
]
