# -*- coding: utf-8 -*-
"""
组合分析模块

包含：
- 风险归因分析
- 压力测试
- VaR计算
- 相关性矩阵
- 再平衡建议
"""
from .risk_attribution import (
    RiskAttributionService,
    get_risk_attribution_service,
    RiskSource,
    RiskContribution,
    RiskAttributionResult,
)
from .stress_test import (
    StressTestService,
    get_stress_test_service,
    ScenarioType,
    StressScenario,
    StressTestResult,
)
from .var_calculator import (
    VaRCalculatorService,
    get_var_calculator_service,
    VaRMethod,
    VaRResult,
    CVaRResult,
)
from .correlation_matrix import (
    CorrelationMatrixService,
    get_correlation_matrix_service,
    CorrelationResult,
)
from .rebalance_suggest import (
    RebalanceSuggestService,
    get_rebalance_suggest_service,
    RebalanceStrategy,
    RebalanceSuggestion,
    RebalanceResult,
)

__all__ = [
    # Risk Attribution
    "RiskAttributionService",
    "get_risk_attribution_service",
    "RiskSource",
    "RiskContribution",
    "RiskAttributionResult",
    # Stress Test
    "StressTestService",
    "get_stress_test_service",
    "ScenarioType",
    "StressScenario",
    "StressTestResult",
    # VaR Calculator
    "VaRCalculatorService",
    "get_var_calculator_service",
    "VaRMethod",
    "VaRResult",
    "CVaRResult",
    # Correlation Matrix
    "CorrelationMatrixService",
    "get_correlation_matrix_service",
    "CorrelationResult",
    # Rebalance Suggest
    "RebalanceSuggestService",
    "get_rebalance_suggest_service",
    "RebalanceStrategy",
    "RebalanceSuggestion",
    "RebalanceResult",
]
