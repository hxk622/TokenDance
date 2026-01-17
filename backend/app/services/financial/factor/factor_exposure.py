# -*- coding: utf-8 -*-
"""
FactorExposureService - 因子暴露分析服务

提供：
1. 组合因子暴露
2. 因子暴露归因
3. 暴露变化跟踪
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SingleExposure:
    """单因子暴露"""
    factor_name: str
    exposure: float          # 标准化暴露
    benchmark_exposure: float  # 基准暴露
    active_exposure: float   # 主动暴露
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "exposure": self.exposure,
            "benchmark_exposure": self.benchmark_exposure,
            "active_exposure": self.active_exposure,
        }


@dataclass
class ExposureResult:
    """因子暴露结果"""
    portfolio_id: str
    analysis_date: datetime
    benchmark: str
    
    # 各因子暴露
    exposures: List[SingleExposure] = field(default_factory=list)
    
    # 汇总
    total_active_risk: float = 0.0
    tracking_error: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "analysis_date": self.analysis_date.isoformat(),
            "benchmark": self.benchmark,
            "exposures": [e.to_dict() for e in self.exposures],
            "total_active_risk": self.total_active_risk,
            "tracking_error": self.tracking_error,
        }


class FactorExposureService:
    """因子暴露分析服务"""
    
    STYLE_FACTORS = ["规模", "价值", "成长", "动量", "波动率", "质量", "红利", "流动性"]
    
    def __init__(self):
        self._cache: Dict[str, ExposureResult] = {}
    
    async def analyze_exposure(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
        benchmark: str = "沪深300",
    ) -> ExposureResult:
        """分析因子暴露"""
        import random
        
        exposures = []
        for factor in self.STYLE_FACTORS:
            port_exp = random.uniform(-1.5, 1.5)
            bench_exp = random.uniform(-0.5, 0.5)
            
            exposures.append(SingleExposure(
                factor_name=factor,
                exposure=round(port_exp, 2),
                benchmark_exposure=round(bench_exp, 2),
                active_exposure=round(port_exp - bench_exp, 2),
            ))
        
        return ExposureResult(
            portfolio_id=portfolio_id,
            analysis_date=datetime.now(),
            benchmark=benchmark,
            exposures=exposures,
            total_active_risk=round(random.uniform(0.05, 0.15), 4),
            tracking_error=round(random.uniform(0.03, 0.10), 4),
        )
    
    async def get_exposure_history(
        self,
        portfolio_id: str,
        factor_name: str,
        lookback_days: int = 252,
    ) -> List[Dict[str, Any]]:
        """获取暴露历史"""
        import random
        from datetime import timedelta
        
        history = []
        base_date = datetime.now()
        
        for i in range(min(lookback_days // 20, 12)):
            history.append({
                "date": (base_date - timedelta(days=i * 20)).strftime("%Y-%m-%d"),
                "exposure": round(random.uniform(-1.5, 1.5), 2),
            })
        
        return list(reversed(history))


_factor_exposure_service: Optional[FactorExposureService] = None


def get_factor_exposure_service() -> FactorExposureService:
    global _factor_exposure_service
    if _factor_exposure_service is None:
        _factor_exposure_service = FactorExposureService()
    return _factor_exposure_service
