"""
组合分析模块

包含：
- 风险归因分析
- 压力测试
- VaR计算
- 相关性矩阵
- 再平衡建议
"""
from .correlation_matrix import (
    CorrelationMatrixService,
    CorrelationResult,
    get_correlation_matrix_service,
)
from .rebalance_suggest import (
    RebalanceResult,
    RebalanceStrategy,
    RebalanceSuggestion,
    RebalanceSuggestService,
    get_rebalance_suggest_service,
)
from .risk_attribution import (
    RiskAttributionResult,
    RiskAttributionService,
    RiskContribution,
    RiskSource,
    get_risk_attribution_service,
)
from .stress_test import (
    ScenarioType,
    StressScenario,
    StressTestResult,
    StressTestService,
    get_stress_test_service,
)
from .var_calculator import (
    CVaRResult,
    VaRCalculatorService,
    VaRMethod,
    VaRResult,
    get_var_calculator_service,
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
