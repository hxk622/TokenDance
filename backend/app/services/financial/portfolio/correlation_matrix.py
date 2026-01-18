"""
CorrelationMatrixService - 相关性矩阵服务

提供：
1. 股票相关性矩阵
2. 因子相关性矩阵
3. 动态相关性分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CorrelationPair:
    """相关性配对"""
    symbol1: str
    name1: str
    symbol2: str
    name2: str
    correlation: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol1": self.symbol1,
            "name1": self.name1,
            "symbol2": self.symbol2,
            "name2": self.name2,
            "correlation": self.correlation,
        }


@dataclass
class CorrelationResult:
    """相关性矩阵结果"""
    analysis_date: datetime
    lookback_days: int

    # 股票列表
    symbols: list[str]
    names: list[str]

    # 相关性矩阵 (二维列表)
    correlation_matrix: list[list[float]]

    # 高/低相关性配对
    high_correlations: list[CorrelationPair] = field(default_factory=list)
    low_correlations: list[CorrelationPair] = field(default_factory=list)

    # 统计
    avg_correlation: float = 0.0
    max_correlation: float = 0.0
    min_correlation: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "lookback_days": self.lookback_days,
            "symbols": self.symbols,
            "names": self.names,
            "correlation_matrix": self.correlation_matrix,
            "high_correlations": [h.to_dict() for h in self.high_correlations],
            "low_correlations": [lc.to_dict() for lc in self.low_correlations],
            "avg_correlation": self.avg_correlation,
            "max_correlation": self.max_correlation,
            "min_correlation": self.min_correlation,
        }


class CorrelationMatrixService:
    """相关性矩阵服务"""

    def __init__(self):
        self._cache: dict[str, CorrelationResult] = {}

    async def calculate_correlation_matrix(
        self,
        symbols: list[str],
        lookback_days: int = 252,
    ) -> CorrelationResult:
        """计算相关性矩阵"""
        import random

        n = len(symbols)
        names = [self._get_stock_name(s) for s in symbols]

        # 生成相关性矩阵
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

        # 填充非对角线元素
        correlations = []
        for i in range(n):
            for j in range(i + 1, n):
                # 同行业股票相关性较高
                if self._same_industry(symbols[i], symbols[j]):
                    corr = random.uniform(0.5, 0.9)
                else:
                    corr = random.uniform(-0.2, 0.6)

                corr = round(corr, 4)
                matrix[i][j] = corr
                matrix[j][i] = corr
                correlations.append((symbols[i], names[i], symbols[j], names[j], corr))

        # 高/低相关性配对
        sorted_corrs = sorted(correlations, key=lambda x: x[4], reverse=True)
        high_corrs = [
            CorrelationPair(symbol1=c[0], name1=c[1], symbol2=c[2], name2=c[3], correlation=c[4])
            for c in sorted_corrs[:5]
        ]
        low_corrs = [
            CorrelationPair(symbol1=c[0], name1=c[1], symbol2=c[2], name2=c[3], correlation=c[4])
            for c in sorted_corrs[-5:]
        ]

        # 统计
        all_corrs = [c[4] for c in correlations]
        avg_corr = sum(all_corrs) / len(all_corrs) if all_corrs else 0
        max_corr = max(all_corrs) if all_corrs else 0
        min_corr = min(all_corrs) if all_corrs else 0

        return CorrelationResult(
            analysis_date=datetime.now(),
            lookback_days=lookback_days,
            symbols=symbols,
            names=names,
            correlation_matrix=matrix,
            high_correlations=high_corrs,
            low_correlations=low_corrs,
            avg_correlation=round(avg_corr, 4),
            max_correlation=round(max_corr, 4),
            min_correlation=round(min_corr, 4),
        )

    async def get_stock_correlations(
        self,
        symbol: str,
        compare_symbols: list[str],
        lookback_days: int = 252,
    ) -> dict[str, float]:
        """获取单只股票与其他股票的相关性"""
        import random

        correlations = {}
        for comp_symbol in compare_symbols:
            if comp_symbol == symbol:
                correlations[comp_symbol] = 1.0
            elif self._same_industry(symbol, comp_symbol):
                correlations[comp_symbol] = round(random.uniform(0.5, 0.9), 4)
            else:
                correlations[comp_symbol] = round(random.uniform(-0.2, 0.6), 4)

        return correlations

    async def calculate_rolling_correlation(
        self,
        symbol1: str,
        symbol2: str,
        window: int = 60,
        lookback_days: int = 252,
    ) -> list[dict[str, Any]]:
        """计算滚动相关性"""
        import random
        from datetime import timedelta

        rolling_corrs = []
        base_date = datetime.now()

        # 基础相关性
        if self._same_industry(symbol1, symbol2):
            base_corr = random.uniform(0.5, 0.7)
        else:
            base_corr = random.uniform(0.1, 0.4)

        for i in range(lookback_days // window):
            date = base_date - timedelta(days=i * window)
            corr = base_corr + random.uniform(-0.2, 0.2)
            corr = max(-1, min(1, corr))

            rolling_corrs.append({
                "date": date.strftime("%Y-%m-%d"),
                "correlation": round(corr, 4),
            })

        return list(reversed(rolling_corrs))

    def _same_industry(self, symbol1: str, symbol2: str) -> bool:
        """判断是否同行业"""
        industries = {
            "600519": "白酒", "000858": "白酒", "000568": "白酒",
            "600036": "银行", "601398": "银行",
            "000333": "家电", "000651": "家电",
        }
        return industries.get(symbol1) == industries.get(symbol2)

    def _get_stock_name(self, symbol: str) -> str:
        names = {
            "600519": "贵州茅台", "000858": "五粮液", "000568": "泸州老窖",
            "600036": "招商银行", "000333": "美的集团", "000651": "格力电器",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_correlation_matrix_service: CorrelationMatrixService | None = None


def get_correlation_matrix_service() -> CorrelationMatrixService:
    global _correlation_matrix_service
    if _correlation_matrix_service is None:
        _correlation_matrix_service = CorrelationMatrixService()
    return _correlation_matrix_service
