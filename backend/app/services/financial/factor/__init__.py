"""
多因子模型模块

包含：
- Barra风险模型
- Alpha因子挖掘
- 因子暴露分析
- 因子收益分析
"""
from .alpha_mining import (
    AlphaBacktestResult,
    AlphaFactor,
    AlphaMiningResult,
    AlphaMiningService,
    get_alpha_mining_service,
)
from .barra_model import (
    BarraFactor,
    BarraModelService,
    BarraRiskResult,
    FactorExposure,
    get_barra_model_service,
)
from .factor_exposure import (
    ExposureResult,
    FactorExposureService,
    get_factor_exposure_service,
)
from .factor_return import (
    FactorPerformance,
    FactorReturnResult,
    FactorReturnService,
    get_factor_return_service,
)

__all__ = [
    # Barra Model
    "BarraModelService",
    "get_barra_model_service",
    "BarraFactor",
    "FactorExposure",
    "BarraRiskResult",
    # Alpha Mining
    "AlphaMiningService",
    "get_alpha_mining_service",
    "AlphaFactor",
    "AlphaBacktestResult",
    "AlphaMiningResult",
    # Factor Exposure
    "FactorExposureService",
    "get_factor_exposure_service",
    "ExposureResult",
    # Factor Return
    "FactorReturnService",
    "get_factor_return_service",
    "FactorReturnResult",
    "FactorPerformance",
]
