"""
PeerComparisonService - 同行对比分析服务

提供：
1. 同行业公司对比
2. 关键指标横向比较
3. 竞争优势分析
4. 估值对比
5. [新增] PK 矩阵 - 带冠军标识和综合评分

使用方法：
    service = get_peer_comparison_service()
    result = await service.compare_peers("600519")
    matrix = await service.get_comparison_matrix("600519")
"""
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """指标类型 - 用于判断谁是冠军"""
    HIGHER_BETTER = "higher_better"  # 越高越好
    LOWER_BETTER = "lower_better"    # 越低越好


@dataclass
class CompanyMetrics:
    """公司指标"""
    symbol: str
    name: str

    # 市值与估值
    market_cap: float = 0.0         # 市值 (亿)
    pe_ttm: float = 0.0             # PE (TTM)
    pb: float = 0.0                 # PB
    ps: float = 0.0                 # PS

    # 盈利能力
    roe: float = 0.0                # ROE %
    roa: float = 0.0                # ROA %
    gross_margin: float = 0.0       # 毛利率 %
    net_margin: float = 0.0         # 净利率 %

    # 成长性
    revenue_growth: float = 0.0     # 营收增速 %
    profit_growth: float = 0.0      # 净利润增速 %

    # 运营效率
    asset_turnover: float = 0.0     # 资产周转率
    inventory_days: float = 0.0     # 存货周转天数
    receivable_days: float = 0.0    # 应收周转天数

    # 财务健康
    debt_ratio: float = 0.0         # 资产负债率 %
    current_ratio: float = 0.0      # 流动比率

    # 股价表现
    price_change_1m: float = 0.0    # 1月涨跌幅
    price_change_ytd: float = 0.0   # 年初至今涨跌幅

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market_cap": self.market_cap,
            "pe_ttm": self.pe_ttm,
            "pb": self.pb,
            "ps": self.ps,
            "roe": self.roe,
            "roa": self.roa,
            "gross_margin": self.gross_margin,
            "net_margin": self.net_margin,
            "revenue_growth": self.revenue_growth,
            "profit_growth": self.profit_growth,
            "asset_turnover": self.asset_turnover,
            "inventory_days": self.inventory_days,
            "receivable_days": self.receivable_days,
            "debt_ratio": self.debt_ratio,
            "current_ratio": self.current_ratio,
            "price_change_1m": self.price_change_1m,
            "price_change_ytd": self.price_change_ytd,
        }


@dataclass
class PeerComparisonResult:
    """对比结果"""
    target_symbol: str
    target_name: str
    industry: str

    # 对比公司
    peers: list[CompanyMetrics] = field(default_factory=list)

    # 目标公司指标
    target_metrics: CompanyMetrics | None = None

    # 行业平均/中位数
    industry_avg: dict[str, float] = field(default_factory=dict)
    industry_median: dict[str, float] = field(default_factory=dict)

    # 排名
    rankings: dict[str, int] = field(default_factory=dict)

    # 优劣势分析
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_symbol": self.target_symbol,
            "target_name": self.target_name,
            "industry": self.industry,
            "target_metrics": self.target_metrics.to_dict() if self.target_metrics else None,
            "peers": [p.to_dict() for p in self.peers],
            "peer_count": len(self.peers),
            "industry_avg": self.industry_avg,
            "industry_median": self.industry_median,
            "rankings": self.rankings,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


@dataclass
class PeerInfo:
    """对比公司信息"""
    symbol: str
    name: str
    market_cap: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "market_cap": self.market_cap,
        }


@dataclass
class PeerMetricComparison:
    """单指标对比"""
    metric_name: str
    metric_key: str
    metric_type: MetricType
    values: dict[str, float | None]  # symbol -> value
    winner: str | None  # 最优者 symbol
    industry_mean: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "metric_key": self.metric_key,
            "metric_type": self.metric_type.value,
            "values": self.values,
            "winner": self.winner,
            "industry_mean": self.industry_mean,
        }


@dataclass
class PeerComparisonMatrix:
    """同行对比矩阵 - 用于 PK 展示"""
    target_symbol: str
    target_name: str
    industry: str
    peers: list[PeerInfo]  # 对比公司列表
    metrics: list[PeerMetricComparison]  # 各指标对比

    # 综合评分 (0-100)
    scores: dict[str, float]  # symbol -> score

    # 洞察
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_symbol": self.target_symbol,
            "target_name": self.target_name,
            "industry": self.industry,
            "peers": [p.to_dict() for p in self.peers],
            "peer_count": len(self.peers),
            "metrics": [m.to_dict() for m in self.metrics],
            "scores": self.scores,
            "insights": self.insights,
        }


# PK 矩阵指标配置
MATRIX_METRICS: list[tuple[str, str, MetricType]] = [
    ("ROE", "roe", MetricType.HIGHER_BETTER),
    ("PE (TTM)", "pe_ttm", MetricType.LOWER_BETTER),
    ("营收增速", "revenue_growth", MetricType.HIGHER_BETTER),
    ("净利率", "net_margin", MetricType.HIGHER_BETTER),
    ("毛利率", "gross_margin", MetricType.HIGHER_BETTER),
    ("资产负债率", "debt_ratio", MetricType.LOWER_BETTER),
]

# 评分权重
SCORE_WEIGHTS: dict[str, float] = {
    "roe": 0.20,
    "pe_ttm": 0.15,
    "revenue_growth": 0.15,
    "net_margin": 0.15,
    "gross_margin": 0.15,
    "debt_ratio": 0.10,
    "profit_growth": 0.10,
}


class PeerComparisonService:
    """
    同行对比服务

    提供同行业公司的横向对比分析和 PK 矩阵。
    """

    # 申万行业分类 (简化版)
    INDUSTRY_MAPPING = {
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

    def __init__(self):
        """初始化服务"""
        self._cache: dict[str, PeerComparisonResult] = {}

    async def compare_peers(
        self,
        symbol: str,
        top_n: int = 10,
    ) -> PeerComparisonResult:
        """
        同行对比分析

        Args:
            symbol: 目标股票代码
            top_n: 对比公司数量

        Returns:
            PeerComparisonResult
        """
        cache_key = f"{symbol}:{top_n}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self._perform_comparison(symbol, top_n)
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Failed to compare peers: {e}")
            return PeerComparisonResult(
                target_symbol=symbol,
                target_name="",
                industry="",
            )

    async def get_industry_peers(self, symbol: str) -> list[str]:
        """获取同行业公司列表"""
        info = self.INDUSTRY_MAPPING.get(symbol)
        if not info:
            return []

        industry = info[1]

        peers = []
        for sym, (_name, ind) in self.INDUSTRY_MAPPING.items():
            if ind == industry and sym != symbol:
                peers.append(sym)

        return peers

    async def compare_specific_metrics(
        self,
        symbols: list[str],
        metrics: list[str],
    ) -> dict[str, dict[str, float]]:
        """
        比较指定指标

        Args:
            symbols: 股票代码列表
            metrics: 指标列表 (如 ["pe_ttm", "roe", "revenue_growth"])

        Returns:
            {symbol: {metric: value}}
        """
        result = {}

        for symbol in symbols:
            company_metrics = await self._fetch_company_metrics(symbol)
            if company_metrics:
                result[symbol] = {}
                for metric in metrics:
                    result[symbol][metric] = getattr(company_metrics, metric, 0)

        return result

    async def get_comparison_matrix(
        self,
        symbol: str,
        peer_count: int = 3,
        auto_select: bool = True,
        custom_peers: list[str] | None = None,
    ) -> PeerComparisonMatrix:
        """
        获取同行对比矩阵 (PK 矩阵)

        Args:
            symbol: 目标股票代码
            peer_count: 对比公司数量
            auto_select: 是否自动选择对比公司
            custom_peers: 自定义对比公司列表

        Returns:
            PeerComparisonMatrix 包含各指标对比和综合评分
        """
        cache_key = f"matrix:{symbol}:{peer_count}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            result = await self._build_comparison_matrix(
                symbol, peer_count, auto_select, custom_peers
            )
            self._cache[cache_key] = result
            return result
        except Exception as e:
            logger.error(f"Failed to build comparison matrix: {e}")
            return self._get_empty_matrix(symbol)

    async def _build_comparison_matrix(
        self,
        symbol: str,
        peer_count: int,
        auto_select: bool,
        custom_peers: list[str] | None,
    ) -> PeerComparisonMatrix:
        """构建对比矩阵"""
        # 获取目标公司信息
        info = self.INDUSTRY_MAPPING.get(symbol)
        if info:
            target_name, industry = info
        else:
            target_name = f"Stock {symbol}"
            industry = "其他"

        # 获取对比公司
        if custom_peers:
            peer_symbols = custom_peers[:peer_count]
        else:
            peer_symbols = await self.get_industry_peers(symbol)
            peer_symbols = peer_symbols[:peer_count]

        # 所有公司 (包括目标)
        all_symbols = [symbol] + peer_symbols

        # 获取所有公司指标
        all_metrics: dict[str, CompanyMetrics] = {}
        peers_info: list[PeerInfo] = []

        for sym in all_symbols:
            company_metrics = await self._fetch_company_metrics(sym)
            if company_metrics:
                all_metrics[sym] = company_metrics
                peers_info.append(PeerInfo(
                    symbol=sym,
                    name=company_metrics.name,
                    market_cap=company_metrics.market_cap,
                ))

        # 构建各指标对比
        metric_comparisons: list[PeerMetricComparison] = []

        for metric_name, metric_key, metric_type in MATRIX_METRICS:
            values: dict[str, float | None] = {}
            valid_values: list[tuple[str, float]] = []

            for sym in all_symbols:
                if sym in all_metrics:
                    val = getattr(all_metrics[sym], metric_key, None)
                    values[sym] = val
                    if val is not None and val != 0:
                        valid_values.append((sym, val))
                else:
                    values[sym] = None

            # 确定冠军
            winner = None
            if valid_values:
                if metric_type == MetricType.HIGHER_BETTER:
                    winner = max(valid_values, key=lambda x: x[1])[0]
                else:
                    winner = min(valid_values, key=lambda x: x[1])[0]

            # 计算行业均值
            industry_mean = None
            if valid_values:
                industry_mean = sum(v for _, v in valid_values) / len(valid_values)

            metric_comparisons.append(PeerMetricComparison(
                metric_name=metric_name,
                metric_key=metric_key,
                metric_type=metric_type,
                values=values,
                winner=winner,
                industry_mean=industry_mean,
            ))

        # 计算综合评分
        scores = self._calculate_composite_scores(all_symbols, all_metrics, metric_comparisons)

        # 生成洞察
        insights = self._generate_matrix_insights(symbol, all_metrics, scores)

        return PeerComparisonMatrix(
            target_symbol=symbol,
            target_name=target_name,
            industry=industry,
            peers=peers_info,
            metrics=metric_comparisons,
            scores=scores,
            insights=insights,
        )

    def _calculate_composite_scores(
        self,
        symbols: list[str],
        all_metrics: dict[str, CompanyMetrics],
        comparisons: list[PeerMetricComparison],
    ) -> dict[str, float]:
        """计算综合评分"""
        scores: dict[str, float] = {}

        for sym in symbols:
            if sym not in all_metrics:
                scores[sym] = 0.0
                continue

            total_score = 0.0
            total_weight = 0.0

            for comp in comparisons:
                metric_key = comp.metric_key
                weight = SCORE_WEIGHTS.get(metric_key, 0.1)

                value = comp.values.get(sym)
                if value is None:
                    continue

                # 收集所有有效值
                valid_values = [v for v in comp.values.values() if v is not None]
                if not valid_values:
                    continue

                min_val = min(valid_values)
                max_val = max(valid_values)

                if max_val == min_val:
                    normalized = 50.0
                else:
                    if comp.metric_type == MetricType.HIGHER_BETTER:
                        normalized = ((value - min_val) / (max_val - min_val)) * 100
                    else:
                        normalized = ((max_val - value) / (max_val - min_val)) * 100

                total_score += normalized * weight
                total_weight += weight

            if total_weight > 0:
                scores[sym] = round(total_score / total_weight, 1)
            else:
                scores[sym] = 50.0

        return scores

    def _generate_matrix_insights(
        self,
        target_symbol: str,
        all_metrics: dict[str, CompanyMetrics],
        scores: dict[str, float],
    ) -> list[str]:
        """生成矩阵洞察"""
        insights = []

        if target_symbol not in all_metrics:
            return ["数据不足，无法生成洞察"]

        target = all_metrics[target_symbol]
        target_score = scores.get(target_symbol, 0)

        # 排名
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        rank = next((i + 1 for i, (sym, _) in enumerate(sorted_scores) if sym == target_symbol), 0)

        if rank == 1:
            insights.append(f"{target.name}综合评分{target_score:.0f}分，位列同行第一")
        elif rank <= 3:
            insights.append(f"{target.name}综合评分{target_score:.0f}分，位列同行前三")
        else:
            insights.append(f"{target.name}综合评分{target_score:.0f}分，排名第{rank}")

        # 优势指标
        if target.roe > 20:
            insights.append(f"ROE {target.roe:.1f}% 表现优秀，盈利能力强")

        if target.net_margin > 30:
            insights.append(f"净利率 {target.net_margin:.1f}% 显著领先，定价能力强")

        # 劣势
        if target.debt_ratio > 60:
            insights.append(f"资产负债率 {target.debt_ratio:.1f}% 偏高，关注财务风险")

        return insights if insights else ["各项指标表现均衡"]

    def _get_empty_matrix(self, symbol: str) -> PeerComparisonMatrix:
        """返回空矩阵"""
        return PeerComparisonMatrix(
            target_symbol=symbol,
            target_name="",
            industry="",
            peers=[],
            metrics=[],
            scores={},
            insights=["数据不可用"],
        )

    async def _perform_comparison(
        self,
        symbol: str,
        top_n: int,
    ) -> PeerComparisonResult:
        """执行对比分析"""
        # 获取目标公司信息
        info = self.INDUSTRY_MAPPING.get(symbol)
        if info:
            target_name, industry = info
        else:
            target_name = f"Stock {symbol}"
            industry = "其他"

        # 获取目标公司指标
        target_metrics = await self._fetch_company_metrics(symbol)

        # 获取同行
        peer_symbols = await self.get_industry_peers(symbol)

        # 获取同行指标
        peers = []
        for peer_symbol in peer_symbols[:top_n]:
            peer_metrics = await self._fetch_company_metrics(peer_symbol)
            if peer_metrics:
                peers.append(peer_metrics)

        # 计算行业平均/中位数
        industry_avg, industry_median = self._calculate_industry_stats(peers + ([target_metrics] if target_metrics else []))

        # 计算排名
        rankings = self._calculate_rankings(target_metrics, peers) if target_metrics else {}

        # 分析优劣势
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            target_metrics, industry_avg, industry_median
        ) if target_metrics else ([], [])

        return PeerComparisonResult(
            target_symbol=symbol,
            target_name=target_name,
            industry=industry,
            target_metrics=target_metrics,
            peers=peers,
            industry_avg=industry_avg,
            industry_median=industry_median,
            rankings=rankings,
            strengths=strengths,
            weaknesses=weaknesses,
        )

    async def _fetch_company_metrics(self, symbol: str) -> CompanyMetrics | None:
        """获取公司指标"""
        try:
            result = await self._fetch_from_akshare(symbol)
            if result is not None:
                return result
        except Exception as e:
            logger.debug(f"AKShare fetch failed: {e}")

        # Fallback to mock data
        return self._generate_mock_metrics(symbol)

    async def _fetch_from_akshare(self, symbol: str) -> CompanyMetrics | None:
        """从 AKShare 获取"""
        try:
            import akshare as ak

            # 获取实时行情
            df = ak.stock_zh_a_spot_em()
            row = df[df['代码'] == symbol]

            if row.empty:
                return None

            row = row.iloc[0]

            info = self.INDUSTRY_MAPPING.get(symbol, (f"Stock {symbol}", "其他"))

            return CompanyMetrics(
                symbol=symbol,
                name=info[0],
                market_cap=float(row.get('总市值', 0)) / 1e8,
                pe_ttm=float(row.get('市盈率-动态', 0) or 0),
                pb=float(row.get('市净率', 0) or 0),
            )

        except Exception as e:
            logger.error(f"AKShare fetch error: {e}")
            return None

    def _generate_mock_metrics(self, symbol: str) -> CompanyMetrics:
        """生成 Mock 指标"""
        import random

        info = self.INDUSTRY_MAPPING.get(symbol, (f"Stock {symbol}", "其他"))

        return CompanyMetrics(
            symbol=symbol,
            name=info[0],
            market_cap=random.uniform(100, 10000),
            pe_ttm=random.uniform(10, 50),
            pb=random.uniform(1, 10),
            ps=random.uniform(1, 20),
            roe=random.uniform(5, 30),
            roa=random.uniform(2, 15),
            gross_margin=random.uniform(20, 60),
            net_margin=random.uniform(5, 30),
            revenue_growth=random.uniform(-10, 30),
            profit_growth=random.uniform(-20, 50),
            asset_turnover=random.uniform(0.3, 1.5),
            inventory_days=random.uniform(30, 180),
            receivable_days=random.uniform(30, 120),
            debt_ratio=random.uniform(20, 70),
            current_ratio=random.uniform(1, 3),
            price_change_1m=random.uniform(-10, 10),
            price_change_ytd=random.uniform(-20, 30),
        )

    def _calculate_industry_stats(
        self,
        companies: list[CompanyMetrics],
    ) -> tuple[dict[str, float], dict[str, float]]:
        """计算行业统计"""
        if not companies:
            return {}, {}

        metrics = [
            "pe_ttm", "pb", "roe", "gross_margin", "net_margin",
            "revenue_growth", "profit_growth", "debt_ratio",
        ]

        avg = {}
        median = {}

        for metric in metrics:
            values = [getattr(c, metric, 0) for c in companies if getattr(c, metric, 0) != 0]
            if values:
                avg[metric] = sum(values) / len(values)
                sorted_values = sorted(values)
                n = len(sorted_values)
                median[metric] = sorted_values[n // 2] if n % 2 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

        return avg, median

    def _calculate_rankings(
        self,
        target: CompanyMetrics,
        peers: list[CompanyMetrics],
    ) -> dict[str, int]:
        """计算排名"""
        all_companies = [target] + peers
        rankings = {}

        # 越高越好的指标
        higher_better = ["roe", "gross_margin", "net_margin", "revenue_growth", "profit_growth", "current_ratio"]
        # 越低越好的指标
        lower_better = ["pe_ttm", "debt_ratio", "inventory_days", "receivable_days"]

        for metric in higher_better:
            sorted_list = sorted(all_companies, key=lambda x: getattr(x, metric, 0), reverse=True)
            for i, c in enumerate(sorted_list):
                if c.symbol == target.symbol:
                    rankings[metric] = i + 1
                    break

        for metric in lower_better:
            sorted_list = sorted(all_companies, key=lambda x: getattr(x, metric, float('inf')))
            for i, c in enumerate(sorted_list):
                if c.symbol == target.symbol:
                    rankings[metric] = i + 1
                    break

        return rankings

    def _analyze_strengths_weaknesses(
        self,
        target: CompanyMetrics,
        avg: dict[str, float],
        median: dict[str, float],
    ) -> tuple[list[str], list[str]]:
        """分析优劣势"""
        strengths = []
        weaknesses = []

        # ROE
        if target.roe > avg.get("roe", 0) * 1.2:
            strengths.append(f"ROE ({target.roe:.1f}%) 显著高于行业平均 ({avg.get('roe', 0):.1f}%)")
        elif target.roe < avg.get("roe", 0) * 0.8:
            weaknesses.append(f"ROE ({target.roe:.1f}%) 低于行业平均 ({avg.get('roe', 0):.1f}%)")

        # 毛利率
        if target.gross_margin > avg.get("gross_margin", 0) * 1.1:
            strengths.append(f"毛利率 ({target.gross_margin:.1f}%) 高于行业平均")
        elif target.gross_margin < avg.get("gross_margin", 0) * 0.9:
            weaknesses.append(f"毛利率 ({target.gross_margin:.1f}%) 低于行业平均")

        # 增速
        if target.revenue_growth > avg.get("revenue_growth", 0) + 10:
            strengths.append(f"营收增速 ({target.revenue_growth:.1f}%) 领先行业")
        elif target.revenue_growth < avg.get("revenue_growth", 0) - 10:
            weaknesses.append(f"营收增速 ({target.revenue_growth:.1f}%) 落后行业")

        # 负债率
        if target.debt_ratio < avg.get("debt_ratio", 50) * 0.8:
            strengths.append(f"负债率 ({target.debt_ratio:.1f}%) 低于行业平均，财务稳健")
        elif target.debt_ratio > avg.get("debt_ratio", 50) * 1.2:
            weaknesses.append(f"负债率 ({target.debt_ratio:.1f}%) 高于行业平均，财务风险较高")

        return strengths, weaknesses


# 全局单例
_peer_comparison_service: PeerComparisonService | None = None


def get_peer_comparison_service() -> PeerComparisonService:
    """获取同行对比服务单例"""
    global _peer_comparison_service
    if _peer_comparison_service is None:
        _peer_comparison_service = PeerComparisonService()
    return _peer_comparison_service
