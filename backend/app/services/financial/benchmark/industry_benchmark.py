"""
IndustryBenchmarkService - 行业基准服务

提供：
1. 指标行业分位数计算 (TOP X%)
2. DuPont 分解分析 (ROE = 净利率 × 资产周转率 × 权益乘数)
3. 行业分布数据 (P10/P25/P50/P75/P90)

使用方法：
    service = get_industry_benchmark_service()
    benchmark = await service.get_percentile("600519", "roe")
    dupont = await service.get_dupont_decomposition("600519")
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """趋势方向"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


@dataclass
class IndustryBenchmark:
    """行业基准数据"""
    metric_name: str
    metric_key: str
    industry_code: str
    industry_name: str

    # 当前值
    current_value: float

    # 分位数 (0-100, 100 表示最优)
    percentile: float

    # 行业分布数据
    percentile_10: float = 0.0
    percentile_25: float = 0.0
    percentile_50: float = 0.0  # 中位数
    percentile_75: float = 0.0
    percentile_90: float = 0.0
    mean: float = 0.0

    # 排名信息
    rank: int = 0
    total_companies: int = 0

    # 趋势
    trend: TrendDirection = TrendDirection.STABLE
    trend_description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "metric_key": self.metric_key,
            "industry_code": self.industry_code,
            "industry_name": self.industry_name,
            "current_value": self.current_value,
            "percentile": self.percentile,
            "percentile_10": self.percentile_10,
            "percentile_25": self.percentile_25,
            "percentile_50": self.percentile_50,
            "percentile_75": self.percentile_75,
            "percentile_90": self.percentile_90,
            "mean": self.mean,
            "rank": self.rank,
            "total_companies": self.total_companies,
            "trend": self.trend.value,
            "trend_description": self.trend_description,
        }


@dataclass
class DuPontFactor:
    """DuPont 分解因子"""
    name: str
    value: float
    percentile: float  # 行业分位
    trend: TrendDirection
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "percentile": self.percentile,
            "trend": self.trend.value,
            "description": self.description,
        }


@dataclass
class DuPontDecomposition:
    """DuPont 分解结果"""
    symbol: str
    name: str
    roe: float  # ROE = 净利率 × 资产周转率 × 权益乘数

    # 三因子
    net_profit_margin: DuPontFactor  # 净利率
    asset_turnover: DuPontFactor     # 资产周转率
    equity_multiplier: DuPontFactor  # 权益乘数

    # 归因分析
    primary_driver: str  # 主要驱动因素
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "roe": self.roe,
            "net_profit_margin": self.net_profit_margin.to_dict(),
            "asset_turnover": self.asset_turnover.to_dict(),
            "equity_multiplier": self.equity_multiplier.to_dict(),
            "primary_driver": self.primary_driver,
            "insights": self.insights,
        }


# 指标配置: (中文名, 是否越高越好)
METRIC_CONFIG: dict[str, tuple[str, bool]] = {
    "roe": ("ROE", True),
    "roa": ("ROA", True),
    "gross_margin": ("毛利率", True),
    "net_margin": ("净利率", True),
    "revenue_growth": ("营收增速", True),
    "profit_growth": ("利润增速", True),
    "pe_ttm": ("PE (TTM)", False),  # 越低越好 (相对估值)
    "pb": ("PB", False),
    "ps": ("PS", False),
    "debt_ratio": ("资产负债率", False),  # 越低越好
    "current_ratio": ("流动比率", True),
    "asset_turnover": ("资产周转率", True),
}


class IndustryBenchmarkService:
    """
    行业基准服务

    提供指标在行业中的分位数排名和 DuPont 分解分析。
    """

    # 行业数据 (mock，实际应从 AkShare/数据库获取)
    INDUSTRY_DATA: dict[str, dict[str, list[float]]] = {
        "白酒": {
            "roe": [8.5, 12.3, 15.8, 18.2, 20.5, 22.3, 24.1, 26.5, 28.2, 30.5],
            "net_margin": [15.0, 20.5, 25.8, 28.2, 30.5, 32.3, 35.1, 38.5, 42.2, 48.5],
            "gross_margin": [55.0, 60.5, 65.8, 70.2, 72.5, 75.3, 78.1, 80.5, 85.2, 90.5],
            "revenue_growth": [-5.0, 2.5, 5.8, 8.2, 10.5, 12.3, 15.1, 18.5, 22.2, 28.5],
            "asset_turnover": [0.25, 0.32, 0.38, 0.42, 0.48, 0.52, 0.58, 0.65, 0.72, 0.85],
            "debt_ratio": [15.0, 18.5, 22.8, 25.2, 28.5, 32.3, 35.1, 40.5, 45.2, 55.5],
            "pe_ttm": [15.0, 18.5, 22.8, 25.2, 28.5, 32.3, 35.1, 40.5, 45.2, 55.5],
            "equity_multiplier": [1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.5, 1.6, 1.8],
        },
        "家电": {
            "roe": [5.5, 8.3, 10.8, 12.2, 14.5, 16.3, 18.1, 20.5, 22.2, 25.5],
            "net_margin": [3.0, 4.5, 5.8, 6.2, 7.5, 8.3, 9.1, 10.5, 12.2, 15.5],
            "gross_margin": [20.0, 22.5, 25.8, 28.2, 30.5, 32.3, 35.1, 38.5, 42.2, 48.5],
            "revenue_growth": [-8.0, -2.5, 2.8, 5.2, 8.5, 10.3, 12.1, 15.5, 18.2, 25.5],
            "asset_turnover": [0.8, 0.92, 1.05, 1.12, 1.25, 1.35, 1.48, 1.65, 1.82, 2.15],
            "debt_ratio": [35.0, 40.5, 45.8, 50.2, 55.5, 60.3, 65.1, 70.5, 75.2, 82.5],
            "pe_ttm": [8.0, 10.5, 12.8, 15.2, 18.5, 22.3, 25.1, 30.5, 35.2, 45.5],
            "equity_multiplier": [1.5, 1.65, 1.8, 1.95, 2.1, 2.25, 2.4, 2.6, 2.8, 3.2],
        },
        "银行": {
            "roe": [8.0, 9.3, 10.8, 11.2, 11.8, 12.3, 13.1, 14.5, 15.2, 16.5],
            "net_margin": [25.0, 28.5, 32.8, 35.2, 38.5, 40.3, 42.1, 45.5, 48.2, 52.5],
            "revenue_growth": [-2.0, 1.5, 3.8, 5.2, 6.5, 8.3, 10.1, 12.5, 15.2, 18.5],
            "debt_ratio": [88.0, 89.5, 90.8, 91.2, 91.8, 92.3, 93.1, 93.5, 94.2, 95.5],
            "pe_ttm": [4.0, 4.5, 5.2, 5.8, 6.5, 7.3, 8.1, 9.5, 10.2, 12.5],
        },
        "保险": {
            "roe": [5.0, 7.3, 9.8, 11.2, 12.5, 14.3, 16.1, 18.5, 20.2, 23.5],
            "net_margin": [5.0, 8.5, 10.8, 12.2, 14.5, 16.3, 18.1, 20.5, 22.2, 25.5],
            "revenue_growth": [-5.0, 0.5, 3.8, 6.2, 8.5, 12.3, 15.1, 18.5, 22.2, 28.5],
            "pe_ttm": [8.0, 10.5, 12.8, 15.2, 18.5, 22.3, 25.1, 30.5, 35.2, 45.5],
        },
    }

    # 公司-行业映射
    COMPANY_INDUSTRY: dict[str, tuple[str, str]] = {
        "600519": ("贵州茅台", "白酒"),
        "000858": ("五粮液", "白酒"),
        "000568": ("泸州老窖", "白酒"),
        "600809": ("山西汾酒", "白酒"),
        "002304": ("洋河股份", "白酒"),
        "000333": ("美的集团", "家电"),
        "000651": ("格力电器", "家电"),
        "600690": ("海尔智家", "家电"),
        "601318": ("中国平安", "保险"),
        "601628": ("中国人寿", "保险"),
        "600036": ("招商银行", "银行"),
        "601166": ("兴业银行", "银行"),
    }

    # Mock 公司指标数据
    COMPANY_METRICS: dict[str, dict[str, float]] = {
        "600519": {
            "roe": 28.5,
            "roa": 22.3,
            "net_margin": 48.2,
            "gross_margin": 91.5,
            "revenue_growth": 15.8,
            "profit_growth": 18.2,
            "asset_turnover": 0.52,
            "debt_ratio": 20.5,
            "current_ratio": 3.2,
            "pe_ttm": 28.5,
            "pb": 8.2,
            "equity_multiplier": 1.25,
        },
        "000858": {
            "roe": 22.3,
            "roa": 16.8,
            "net_margin": 35.5,
            "gross_margin": 75.2,
            "revenue_growth": 12.5,
            "profit_growth": 15.8,
            "asset_turnover": 0.58,
            "debt_ratio": 28.2,
            "current_ratio": 2.5,
            "pe_ttm": 22.5,
            "pb": 5.2,
            "equity_multiplier": 1.35,
        },
        "000568": {
            "roe": 25.8,
            "roa": 19.5,
            "net_margin": 38.2,
            "gross_margin": 82.5,
            "revenue_growth": 18.2,
            "profit_growth": 22.5,
            "asset_turnover": 0.62,
            "debt_ratio": 22.8,
            "current_ratio": 2.8,
            "pe_ttm": 25.2,
            "pb": 6.5,
            "equity_multiplier": 1.28,
        },
        "000333": {
            "roe": 20.5,
            "roa": 8.2,
            "net_margin": 9.5,
            "gross_margin": 25.8,
            "revenue_growth": 8.5,
            "profit_growth": 12.2,
            "asset_turnover": 1.35,
            "debt_ratio": 62.5,
            "current_ratio": 1.2,
            "pe_ttm": 12.5,
            "pb": 2.8,
            "equity_multiplier": 2.5,
        },
        "000651": {
            "roe": 18.2,
            "roa": 7.5,
            "net_margin": 8.2,
            "gross_margin": 28.5,
            "revenue_growth": 5.2,
            "profit_growth": 8.5,
            "asset_turnover": 1.25,
            "debt_ratio": 58.5,
            "current_ratio": 1.5,
            "pe_ttm": 8.5,
            "pb": 1.8,
            "equity_multiplier": 2.35,
        },
    }

    def __init__(self) -> None:
        """初始化服务"""
        self._cache: dict[str, Any] = {}

    async def get_percentile(
        self,
        symbol: str,
        metric: str,
        industry_code: str | None = None,
    ) -> IndustryBenchmark:
        """
        获取指标在行业中的分位数

        Args:
            symbol: 股票代码
            metric: 指标名 (roe, pe_ttm, gross_margin 等)
            industry_code: 行业代码 (可选，默认自动获取)

        Returns:
            IndustryBenchmark 包含分位数和分布数据
        """
        cache_key = f"percentile:{symbol}:{metric}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self._calculate_percentile(symbol, metric, industry_code)
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Failed to get percentile: {e}")
            return self._get_empty_benchmark(symbol, metric)

    async def get_multiple_percentiles(
        self,
        symbol: str,
        metrics: list[str] | None = None,
    ) -> list[IndustryBenchmark]:
        """
        批量获取多个指标的分位数

        Args:
            symbol: 股票代码
            metrics: 指标列表 (默认: roe, net_margin, revenue_growth, pe_ttm, debt_ratio)

        Returns:
            IndustryBenchmark 列表
        """
        if metrics is None:
            metrics = ["roe", "net_margin", "revenue_growth", "pe_ttm", "debt_ratio"]

        results = []
        for metric in metrics:
            benchmark = await self.get_percentile(symbol, metric)
            results.append(benchmark)

        return results

    async def get_dupont_decomposition(
        self,
        symbol: str,
    ) -> DuPontDecomposition:
        """
        获取 ROE 的 DuPont 分解

        ROE = 净利率 × 资产周转率 × 权益乘数

        Args:
            symbol: 股票代码

        Returns:
            DuPontDecomposition 包含三因子分解和归因分析
        """
        cache_key = f"dupont:{symbol}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self._calculate_dupont(symbol)
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Failed to get dupont decomposition: {e}")
            return self._get_empty_dupont(symbol)

    async def _calculate_percentile(
        self,
        symbol: str,
        metric: str,
        industry_code: str | None,
    ) -> IndustryBenchmark:
        """计算分位数"""
        # 获取公司信息和行业
        company_info = self.COMPANY_INDUSTRY.get(symbol)
        if company_info:
            _, industry = company_info
        else:
            industry = "其他"

        if industry_code:
            industry = industry_code

        # 获取公司指标值
        company_metrics = self.COMPANY_METRICS.get(symbol, {})
        current_value = company_metrics.get(metric, 0.0)

        # 获取行业数据
        industry_data = self.INDUSTRY_DATA.get(industry, {})
        metric_distribution = industry_data.get(metric, [])

        if not metric_distribution:
            # 生成默认分布
            metric_distribution = self._generate_default_distribution(metric)

        # 计算分位数
        metric_config = METRIC_CONFIG.get(metric, (metric, True))
        metric_name, higher_is_better = metric_config

        percentile = self._calculate_percentile_value(
            current_value, metric_distribution, higher_is_better
        )

        # 计算分布统计
        sorted_dist = sorted(metric_distribution)
        n = len(sorted_dist)

        return IndustryBenchmark(
            metric_name=metric_name,
            metric_key=metric,
            industry_code=industry,
            industry_name=industry,
            current_value=current_value,
            percentile=percentile,
            percentile_10=sorted_dist[int(n * 0.1)] if n >= 10 else sorted_dist[0],
            percentile_25=sorted_dist[int(n * 0.25)] if n >= 4 else sorted_dist[0],
            percentile_50=sorted_dist[n // 2],
            percentile_75=sorted_dist[int(n * 0.75)] if n >= 4 else sorted_dist[-1],
            percentile_90=sorted_dist[int(n * 0.9)] if n >= 10 else sorted_dist[-1],
            mean=sum(sorted_dist) / n,
            rank=self._calculate_rank(current_value, sorted_dist, higher_is_better),
            total_companies=n,
            trend=self._determine_trend(current_value, sorted_dist),
            trend_description=self._get_trend_description(percentile, metric_name),
        )

    def _calculate_percentile_value(
        self,
        value: float,
        distribution: list[float],
        higher_is_better: bool,
    ) -> float:
        """计算分位数值 (0-100)"""
        if not distribution:
            return 50.0

        sorted_dist = sorted(distribution)
        n = len(sorted_dist)

        # 计算有多少值小于等于当前值
        count_below = sum(1 for v in sorted_dist if v <= value)

        if higher_is_better:
            # 越高越好：TOP X% = 100 - 百分位
            raw_percentile = (count_below / n) * 100
            return round(100 - raw_percentile, 1)
        else:
            # 越低越好：直接使用百分位
            count_above = sum(1 for v in sorted_dist if v >= value)
            return round((count_above / n) * 100, 1)

    def _calculate_rank(
        self,
        value: float,
        sorted_dist: list[float],
        higher_is_better: bool,
    ) -> int:
        """计算排名"""
        n = len(sorted_dist)

        if higher_is_better:
            # 越高排名越前
            rank = sum(1 for v in sorted_dist if v > value) + 1
        else:
            # 越低排名越前
            rank = sum(1 for v in sorted_dist if v < value) + 1

        return min(rank, n)

    def _determine_trend(self, value: float, distribution: list[float]) -> TrendDirection:
        """判断趋势"""
        if not distribution:
            return TrendDirection.STABLE

        median = sorted(distribution)[len(distribution) // 2]

        if value > median * 1.1:
            return TrendDirection.UP
        elif value < median * 0.9:
            return TrendDirection.DOWN
        return TrendDirection.STABLE

    def _get_trend_description(self, percentile: float, metric_name: str) -> str:
        """获取趋势描述"""
        if percentile <= 10:
            return f"{metric_name}位于行业前10%，表现卓越"
        elif percentile <= 25:
            return f"{metric_name}位于行业前25%，表现优秀"
        elif percentile <= 50:
            return f"{metric_name}位于行业中上水平"
        elif percentile <= 75:
            return f"{metric_name}位于行业中等水平"
        else:
            return f"{metric_name}低于行业中位数"

    async def _calculate_dupont(self, symbol: str) -> DuPontDecomposition:
        """计算 DuPont 分解"""
        company_info = self.COMPANY_INDUSTRY.get(symbol)
        company_name = company_info[0] if company_info else f"Stock {symbol}"
        industry = company_info[1] if company_info else "其他"

        metrics = self.COMPANY_METRICS.get(symbol, {})

        # 获取三因子
        net_margin = metrics.get("net_margin", 0.0)
        asset_turnover = metrics.get("asset_turnover", 0.0)
        equity_multiplier = metrics.get("equity_multiplier", 1.0)
        roe = metrics.get("roe", 0.0)

        # 获取行业数据计算分位
        industry_data = self.INDUSTRY_DATA.get(industry, {})

        # 净利率因子
        net_margin_dist = industry_data.get("net_margin", [20, 25, 30, 35, 40])
        net_margin_percentile = self._calculate_percentile_value(
            net_margin, net_margin_dist, True
        )

        # 资产周转因子
        turnover_dist = industry_data.get("asset_turnover", [0.3, 0.4, 0.5, 0.6, 0.7])
        turnover_percentile = self._calculate_percentile_value(
            asset_turnover, turnover_dist, True
        )

        # 权益乘数因子 (适中最好，过高表示杠杆风险)
        multiplier_dist = industry_data.get("equity_multiplier", [1.2, 1.3, 1.4, 1.5, 1.6])
        multiplier_percentile = self._calculate_percentile_value(
            equity_multiplier, multiplier_dist, False
        )

        # 确定主要驱动因素
        primary_driver = self._determine_primary_driver(
            net_margin, net_margin_percentile,
            asset_turnover, turnover_percentile,
            equity_multiplier, multiplier_percentile,
        )

        # 生成洞察
        insights = self._generate_dupont_insights(
            net_margin, net_margin_percentile,
            asset_turnover, turnover_percentile,
            equity_multiplier, multiplier_percentile,
        )

        return DuPontDecomposition(
            symbol=symbol,
            name=company_name,
            roe=roe,
            net_profit_margin=DuPontFactor(
                name="净利率",
                value=net_margin,
                percentile=net_margin_percentile,
                trend=self._get_factor_trend(net_margin_percentile),
                description=self._get_factor_description("净利率", net_margin_percentile),
            ),
            asset_turnover=DuPontFactor(
                name="资产周转率",
                value=asset_turnover,
                percentile=turnover_percentile,
                trend=self._get_factor_trend(turnover_percentile),
                description=self._get_factor_description("资产周转率", turnover_percentile),
            ),
            equity_multiplier=DuPontFactor(
                name="权益乘数",
                value=equity_multiplier,
                percentile=multiplier_percentile,
                trend=self._get_factor_trend(multiplier_percentile),
                description=self._get_multiplier_description(equity_multiplier, multiplier_percentile),
            ),
            primary_driver=primary_driver,
            insights=insights,
        )

    def _get_factor_trend(self, percentile: float) -> TrendDirection:
        """根据分位确定趋势"""
        if percentile <= 30:
            return TrendDirection.UP
        elif percentile >= 70:
            return TrendDirection.DOWN
        return TrendDirection.STABLE

    def _get_factor_description(self, factor_name: str, percentile: float) -> str:
        """获取因子描述"""
        if percentile <= 10:
            return f"{factor_name}行业领先"
        elif percentile <= 30:
            return f"{factor_name}表现优秀"
        elif percentile <= 70:
            return f"{factor_name}行业中等"
        else:
            return f"{factor_name}有待提升"

    def _get_multiplier_description(self, value: float, percentile: float) -> str:
        """获取权益乘数描述"""
        if value < 1.3:
            return "杠杆较低，财务稳健"
        elif value < 1.8:
            return "杠杆适中"
        else:
            return "杠杆较高，注意财务风险"

    def _determine_primary_driver(
        self,
        net_margin: float,
        margin_percentile: float,
        turnover: float,
        turnover_percentile: float,
        multiplier: float,
        multiplier_percentile: float,
    ) -> str:
        """确定主要驱动因素"""
        # 分位数越低表示越好
        factors = [
            ("净利率", margin_percentile),
            ("资产周转率", turnover_percentile),
            ("财务杠杆", multiplier_percentile),
        ]

        # 找到分位数最低（最好）的因子
        best_factor = min(factors, key=lambda x: x[1])
        return best_factor[0]

    def _generate_dupont_insights(
        self,
        net_margin: float,
        margin_percentile: float,
        turnover: float,
        turnover_percentile: float,
        multiplier: float,
        multiplier_percentile: float,
    ) -> list[str]:
        """生成 DuPont 分析洞察"""
        insights = []

        # 净利率洞察
        if margin_percentile <= 10:
            insights.append(f"净利率 {net_margin:.1f}% 显著领先行业，具有强定价权")
        elif margin_percentile >= 70:
            insights.append(f"净利率 {net_margin:.1f}% 低于行业平均，需关注成本控制")

        # 资产周转洞察
        if turnover_percentile <= 10:
            insights.append(f"资产周转率 {turnover:.2f}x 行业领先，运营效率高")
        elif turnover_percentile >= 70:
            insights.append(f"资产周转率 {turnover:.2f}x 偏低，可能存在库存或产能利用问题")

        # 权益乘数洞察
        if multiplier > 2.0:
            insights.append(f"权益乘数 {multiplier:.2f}x 较高，财务杠杆风险需关注")
        elif multiplier < 1.3:
            insights.append(f"权益乘数 {multiplier:.2f}x 较低，财务结构保守稳健")

        return insights if insights else ["各项因子表现均衡"]

    def _generate_default_distribution(self, metric: str) -> list[float]:
        """生成默认分布"""
        defaults: dict[str, list[float]] = {
            "roe": [5, 8, 10, 12, 15, 18, 20, 22, 25, 30],
            "net_margin": [3, 5, 8, 10, 12, 15, 18, 22, 28, 35],
            "gross_margin": [15, 20, 25, 30, 35, 40, 50, 60, 70, 80],
            "revenue_growth": [-10, -5, 0, 5, 10, 15, 20, 25, 30, 40],
            "pe_ttm": [5, 10, 15, 20, 25, 30, 40, 50, 60, 80],
            "debt_ratio": [20, 30, 40, 50, 55, 60, 65, 70, 75, 85],
        }
        return defaults.get(metric, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

    def _get_empty_benchmark(self, symbol: str, metric: str) -> IndustryBenchmark:
        """返回空的 Benchmark"""
        metric_config = METRIC_CONFIG.get(metric, (metric, True))
        return IndustryBenchmark(
            metric_name=metric_config[0],
            metric_key=metric,
            industry_code="unknown",
            industry_name="未知",
            current_value=0.0,
            percentile=50.0,
        )

    def _get_empty_dupont(self, symbol: str) -> DuPontDecomposition:
        """返回空的 DuPont 分解"""
        empty_factor = DuPontFactor(
            name="",
            value=0.0,
            percentile=50.0,
            trend=TrendDirection.STABLE,
            description="数据不可用",
        )
        return DuPontDecomposition(
            symbol=symbol,
            name="",
            roe=0.0,
            net_profit_margin=empty_factor,
            asset_turnover=empty_factor,
            equity_multiplier=empty_factor,
            primary_driver="",
            insights=["数据不可用"],
        )


# 全局单例
_industry_benchmark_service: IndustryBenchmarkService | None = None


def get_industry_benchmark_service() -> IndustryBenchmarkService:
    """获取行业基准服务单例"""
    global _industry_benchmark_service
    if _industry_benchmark_service is None:
        _industry_benchmark_service = IndustryBenchmarkService()
    return _industry_benchmark_service
