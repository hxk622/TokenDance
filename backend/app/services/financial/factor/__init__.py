# -*- coding: utf-8 -*-
"""
多因子模型模块

包含：
- Barra风险模型
- Alpha因子挖掘
- 因子暴露分析
- 因子收益分析
"""
from .barra_model import (
    BarraModelService,
    get_barra_model_service,
    BarraFactor,
    FactorExposure,
    BarraRiskResult,
)
from .alpha_mining import (
    AlphaMiningService,
    get_alpha_mining_service,
    AlphaFactor,
    AlphaBacktestResult,
    AlphaMiningResult,
)
from .factor_exposure import (
    FactorExposureService,
    get_factor_exposure_service,
    ExposureResult,
)
from .factor_return import (
    FactorReturnService,
    get_factor_return_service,
    FactorReturnResult,
    FactorPerformance,
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
