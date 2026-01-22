"""
Benchmark 行业基准模块

提供：
1. 行业分位数计算
2. DuPont 分解分析
3. 指标历史分位数
"""
from .industry_benchmark import (
    DuPontDecomposition,
    DuPontFactor,
    IndustryBenchmark,
    IndustryBenchmarkService,
    get_industry_benchmark_service,
)

__all__ = [
    "IndustryBenchmarkService",
    "IndustryBenchmark",
    "DuPontDecomposition",
    "DuPontFactor",
    "get_industry_benchmark_service",
]
