"""
ValuationAnalyzer - 估值分析服务

实现股票估值分析，包括：
1. 相对估值 (PE/PB/PS/EV-EBITDA)
2. 历史估值对比
3. 行业估值对比
4. DCF 简化模型
5. 估值结论生成

使用方法：
    analyzer = ValuationAnalyzer()
    result = await analyzer.analyze("AAPL")
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ValuationLevel(str, Enum):
    """估值水平"""
    SEVERELY_UNDERVALUED = "severely_undervalued"  # 严重低估 (<-30%)
    UNDERVALUED = "undervalued"                      # 低估 (-30% ~ -10%)
    FAIRLY_VALUED = "fairly_valued"                  # 合理 (-10% ~ +10%)
    OVERVALUED = "overvalued"                        # 高估 (+10% ~ +30%)
    SEVERELY_OVERVALUED = "severely_overvalued"      # 严重高估 (>+30%)


@dataclass
class RelativeValuation:
    """相对估值指标"""
    # 市盈率 (Price/Earnings)
    pe_ttm: float | None = None        # 滚动市盈率
    pe_forward: float | None = None    # 预测市盈率

    # 市净率 (Price/Book)
    pb: float | None = None

    # 市销率 (Price/Sales)
    ps: float | None = None

    # 企业价值/EBITDA
    ev_ebitda: float | None = None

    # PEG (PE / 增长率)
    peg: float | None = None

    # 股息率
    dividend_yield: float | None = None

    # 市值
    market_cap: float | None = None

    # 企业价值
    enterprise_value: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pe_ttm": self.pe_ttm,
            "pe_forward": self.pe_forward,
            "pb": self.pb,
            "ps": self.ps,
            "ev_ebitda": self.ev_ebitda,
            "peg": self.peg,
            "dividend_yield": self.dividend_yield,
            "market_cap": self.market_cap,
            "enterprise_value": self.enterprise_value,
        }


@dataclass
class HistoricalValuation:
    """历史估值数据"""
    # PE 历史区间
    pe_min_5y: float | None = None
    pe_max_5y: float | None = None
    pe_avg_5y: float | None = None
    pe_median_5y: float | None = None
    pe_percentile: float | None = None  # 当前 PE 在历史中的百分位

    # PB 历史区间
    pb_min_5y: float | None = None
    pb_max_5y: float | None = None
    pb_avg_5y: float | None = None
    pb_percentile: float | None = None

    # PS 历史区间
    ps_min_5y: float | None = None
    ps_max_5y: float | None = None
    ps_avg_5y: float | None = None
    ps_percentile: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pe": {
                "min_5y": self.pe_min_5y,
                "max_5y": self.pe_max_5y,
                "avg_5y": self.pe_avg_5y,
                "median_5y": self.pe_median_5y,
                "percentile": self.pe_percentile,
            },
            "pb": {
                "min_5y": self.pb_min_5y,
                "max_5y": self.pb_max_5y,
                "avg_5y": self.pb_avg_5y,
                "percentile": self.pb_percentile,
            },
            "ps": {
                "min_5y": self.ps_min_5y,
                "max_5y": self.ps_max_5y,
                "avg_5y": self.ps_avg_5y,
                "percentile": self.ps_percentile,
            },
        }


@dataclass
class IndustryComparison:
    """行业估值对比"""
    industry: str = ""
    sector: str = ""

    # 行业平均估值
    industry_pe_avg: float | None = None
    industry_pb_avg: float | None = None
    industry_ps_avg: float | None = None

    # 相对行业的溢价/折价
    pe_premium: float | None = None  # 正数表示溢价，负数表示折价
    pb_premium: float | None = None
    ps_premium: float | None = None

    # 行业排名
    pe_rank: int | None = None
    pe_rank_total: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "sector": self.sector,
            "industry_pe_avg": self.industry_pe_avg,
            "industry_pb_avg": self.industry_pb_avg,
            "industry_ps_avg": self.industry_ps_avg,
            "pe_premium": self.pe_premium,
            "pb_premium": self.pb_premium,
            "ps_premium": self.ps_premium,
            "pe_rank": self.pe_rank,
            "pe_rank_total": self.pe_rank_total,
        }


@dataclass
class DCFValuation:
    """DCF 估值结果"""
    # 假设参数
    growth_rate_5y: float = 0.0       # 未来5年增长率
    terminal_growth: float = 0.03     # 永续增长率
    discount_rate: float = 0.10       # 折现率 (WACC)

    # 计算结果
    intrinsic_value: float | None = None  # 每股内在价值
    current_price: float | None = None    # 当前价格
    upside_potential: float | None = None # 上涨空间 (%)

    # 敏感性分析
    sensitivity: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assumptions": {
                "growth_rate_5y": self.growth_rate_5y,
                "terminal_growth": self.terminal_growth,
                "discount_rate": self.discount_rate,
            },
            "intrinsic_value": self.intrinsic_value,
            "current_price": self.current_price,
            "upside_potential": self.upside_potential,
            "sensitivity": self.sensitivity,
        }


@dataclass
class ValuationResult:
    """估值分析结果"""
    symbol: str
    company_name: str = ""
    market: str = ""
    currency: str = "USD"
    current_price: float | None = None

    # 各维度估值
    relative: RelativeValuation = field(default_factory=RelativeValuation)
    historical: HistoricalValuation = field(default_factory=HistoricalValuation)
    industry: IndustryComparison = field(default_factory=IndustryComparison)
    dcf: DCFValuation = field(default_factory=DCFValuation)

    # 综合判断
    valuation_level: ValuationLevel = ValuationLevel.FAIRLY_VALUED
    valuation_score: float = 50.0  # 0-100, 50=合理, <50=低估, >50=高估
    target_price: float | None = None  # 目标价
    upside_potential: float | None = None  # 上涨空间

    # 结论
    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    data_source: str = ""

    # 免责声明
    disclaimer: str = "估值分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "market": self.market,
            "currency": self.currency,
            "current_price": self.current_price,
            "relative": self.relative.to_dict(),
            "historical": self.historical.to_dict(),
            "industry": self.industry.to_dict(),
            "dcf": self.dcf.to_dict(),
            "valuation_level": self.valuation_level.value,
            "valuation_score": self.valuation_score,
            "target_price": self.target_price,
            "upside_potential": self.upside_potential,
            "summary": self.summary,
            "key_points": self.key_points,
            "risks": self.risks,
            "timestamp": self.timestamp.isoformat(),
            "data_source": self.data_source,
            "disclaimer": self.disclaimer,
        }


class ValuationAnalyzer:
    """
    估值分析服务

    综合多种估值方法，判断股票的估值水平。
    """

    # 估值权重
    WEIGHTS = {
        "pe_historical": 0.25,      # PE 历史对比
        "pb_historical": 0.15,      # PB 历史对比
        "industry_comparison": 0.25, # 行业对比
        "peg": 0.20,                # PEG 估值
        "dcf": 0.15,                # DCF 估值
    }

    # 估值分位数阈值
    PERCENTILE_THRESHOLDS = {
        "severely_undervalued": 10,   # <10%
        "undervalued": 30,            # 10-30%
        "fairly_valued_low": 40,      # 30-40%
        "fairly_valued_high": 60,     # 40-60%
        "overvalued": 70,             # 60-70%
        "severely_overvalued": 90,    # >90%
    }

    def __init__(self):
        """初始化估值分析器"""
        self._financial_tool = None

    def _get_financial_tool(self):
        """懒加载金融数据工具"""
        if self._financial_tool is None:
            from app.agent.tools.builtin.financial import get_financial_tool
            self._financial_tool = get_financial_tool()
        return self._financial_tool

    async def analyze(
        self,
        symbol: str,
        market: str = "auto",
        growth_rate: float | None = None,
        discount_rate: float = 0.10,
    ) -> ValuationResult:
        """
        执行完整估值分析

        Args:
            symbol: 股票代码
            market: 市场类型
            growth_rate: 自定义增长率预测（用于 DCF）
            discount_rate: 折现率

        Returns:
            ValuationResult: 估值分析结果
        """
        logger.info(f"Starting valuation analysis for {symbol}")

        result = ValuationResult(symbol=symbol, market=market)

        try:
            tool = self._get_financial_tool()

            # 1. 获取当前估值数据
            valuation_data = await tool.get_valuation(symbol, market=market)

            # 2. 获取报价数据（获取当前价格）
            quote_data = await tool.get_quote(symbol, market=market)

            # 3. 获取财务数据（用于 DCF）
            fundamental_data = await tool.get_fundamental(symbol, market=market)

            if valuation_data.success and valuation_data.data:
                data = valuation_data.data

                # 解析相对估值
                result.relative = self._parse_relative_valuation(data)

                # 解析历史估值
                result.historical = self._analyze_historical_valuation(data)

                # 解析行业对比
                result.industry = self._analyze_industry_comparison(data)

            if quote_data.success and quote_data.data:
                result.current_price = self._get_value(
                    quote_data.data,
                    ["price", "last_price", "close", "current_price"]
                )

            # DCF 估值
            if fundamental_data.success and fundamental_data.data:
                result.dcf = self._calculate_dcf(
                    fundamental_data.data,
                    result.current_price,
                    growth_rate,
                    discount_rate,
                )

            # 综合判断
            result.valuation_score = self._calculate_valuation_score(result)
            result.valuation_level = self._get_valuation_level(result)
            result.target_price = self._estimate_target_price(result)

            if result.current_price and result.target_price:
                result.upside_potential = (
                    (result.target_price - result.current_price) /
                    result.current_price * 100
                )

            # 生成结论
            result.summary = self._generate_summary(result)
            result.key_points = self._generate_key_points(result)
            result.risks = self._identify_valuation_risks(result)

            result.data_source = valuation_data.source if valuation_data.success else ""

            logger.info(
                f"Valuation analysis completed for {symbol}, "
                f"level: {result.valuation_level.value}"
            )

        except Exception as e:
            logger.error(f"Valuation analysis failed for {symbol}: {e}")
            result.summary = f"估值分析失败: {str(e)}"

        return result

    def _parse_relative_valuation(self, data: dict[str, Any]) -> RelativeValuation:
        """解析相对估值数据"""
        return RelativeValuation(
            pe_ttm=self._get_value(data, ["pe", "pe_ttm", "pe_ratio"]),
            pe_forward=self._get_value(data, ["forward_pe", "pe_forward"]),
            pb=self._get_value(data, ["pb", "pb_ratio", "price_to_book"]),
            ps=self._get_value(data, ["ps", "ps_ratio", "price_to_sales"]),
            ev_ebitda=self._get_value(data, ["ev_ebitda", "ev_to_ebitda"]),
            peg=self._get_value(data, ["peg", "peg_ratio"]),
            dividend_yield=self._get_value(data, ["dividend_yield", "yield"]),
            market_cap=self._get_value(data, ["market_cap", "marketCap"]),
            enterprise_value=self._get_value(data, ["enterprise_value", "ev"]),
        )

    def _analyze_historical_valuation(self, data: dict[str, Any]) -> HistoricalValuation:
        """分析历史估值"""
        historical = HistoricalValuation()

        # 从数据中提取历史估值区间
        hist = data.get("historical_valuation", {})

        if hist:
            historical.pe_min_5y = hist.get("pe_min")
            historical.pe_max_5y = hist.get("pe_max")
            historical.pe_avg_5y = hist.get("pe_avg")
            historical.pe_median_5y = hist.get("pe_median")

            historical.pb_min_5y = hist.get("pb_min")
            historical.pb_max_5y = hist.get("pb_max")
            historical.pb_avg_5y = hist.get("pb_avg")

            historical.ps_min_5y = hist.get("ps_min")
            historical.ps_max_5y = hist.get("ps_max")
            historical.ps_avg_5y = hist.get("ps_avg")

        # 计算百分位
        current_pe = self._get_value(data, ["pe", "pe_ttm"])
        if current_pe and historical.pe_min_5y and historical.pe_max_5y:
            if historical.pe_max_5y > historical.pe_min_5y:
                historical.pe_percentile = (
                    (current_pe - historical.pe_min_5y) /
                    (historical.pe_max_5y - historical.pe_min_5y) * 100
                )

        current_pb = self._get_value(data, ["pb", "pb_ratio"])
        if current_pb and historical.pb_min_5y and historical.pb_max_5y:
            if historical.pb_max_5y > historical.pb_min_5y:
                historical.pb_percentile = (
                    (current_pb - historical.pb_min_5y) /
                    (historical.pb_max_5y - historical.pb_min_5y) * 100
                )

        return historical

    def _analyze_industry_comparison(self, data: dict[str, Any]) -> IndustryComparison:
        """分析行业对比"""
        comparison = IndustryComparison()

        comparison.industry = data.get("industry", "")
        comparison.sector = data.get("sector", "")

        industry_data = data.get("industry_comparison", {})

        if industry_data:
            comparison.industry_pe_avg = industry_data.get("pe_avg")
            comparison.industry_pb_avg = industry_data.get("pb_avg")
            comparison.industry_ps_avg = industry_data.get("ps_avg")
            comparison.pe_rank = industry_data.get("pe_rank")
            comparison.pe_rank_total = industry_data.get("total_companies")

        # 计算溢价/折价
        current_pe = self._get_value(data, ["pe", "pe_ttm"])
        if current_pe and comparison.industry_pe_avg:
            comparison.pe_premium = (
                (current_pe - comparison.industry_pe_avg) /
                comparison.industry_pe_avg * 100
            )

        current_pb = self._get_value(data, ["pb", "pb_ratio"])
        if current_pb and comparison.industry_pb_avg:
            comparison.pb_premium = (
                (current_pb - comparison.industry_pb_avg) /
                comparison.industry_pb_avg * 100
            )

        return comparison

    def _calculate_dcf(
        self,
        data: dict[str, Any],
        current_price: float | None,
        growth_rate: float | None,
        discount_rate: float,
    ) -> DCFValuation:
        """
        简化 DCF 估值

        使用两阶段模型：
        1. 高增长期（5年）
        2. 永续期
        """
        dcf = DCFValuation(discount_rate=discount_rate)

        try:
            # 获取基础数据
            cf = data.get("cash_flow_statement", {})
            income = data.get("income_statement", {})
            data.get("balance_sheet", {})

            # 获取自由现金流或净利润
            fcf = self._get_value(cf, ["free_cash_flow", "operating_cash_flow"])
            net_income = self._get_value(income, ["net_income", "净利润"])

            # 使用 FCF 或 净利润
            base_cash_flow = fcf or net_income

            if not base_cash_flow or base_cash_flow <= 0:
                dcf.intrinsic_value = None
                return dcf

            # 获取流通股数
            shares = self._get_value(
                data,
                ["shares_outstanding", "diluted_shares", "总股本"]
            )

            if not shares:
                # 如果没有股数，尝试从市值和价格推算
                market_cap = self._get_value(data, ["market_cap"])
                if market_cap and current_price and current_price > 0:
                    shares = market_cap / current_price

            if not shares:
                dcf.intrinsic_value = None
                return dcf

            # 估算增长率
            if growth_rate is not None:
                dcf.growth_rate_5y = growth_rate
            else:
                # 从历史数据估算
                growth_data = data.get("growth", {})
                historical_growth = growth_data.get("revenue_cagr_3y") or growth_data.get("eps_growth")
                dcf.growth_rate_5y = min(0.25, max(0.0, (historical_growth or 10) / 100))

            # 计算高增长期现金流现值
            pv_high_growth = 0.0
            cf_projection = base_cash_flow

            for year in range(1, 6):
                cf_projection *= (1 + dcf.growth_rate_5y)
                pv = cf_projection / ((1 + discount_rate) ** year)
                pv_high_growth += pv

            # 计算永续期价值
            terminal_cf = cf_projection * (1 + dcf.terminal_growth)
            terminal_value = terminal_cf / (discount_rate - dcf.terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** 5)

            # 总企业价值
            total_value = pv_high_growth + pv_terminal

            # 每股价值
            dcf.intrinsic_value = round(total_value / shares, 2)
            dcf.current_price = current_price

            if current_price and current_price > 0:
                dcf.upside_potential = round(
                    (dcf.intrinsic_value - current_price) / current_price * 100, 1
                )

            # 敏感性分析
            dcf.sensitivity = self._calculate_sensitivity(
                base_cash_flow, shares, discount_rate, dcf.growth_rate_5y
            )

        except Exception as e:
            logger.warning(f"DCF calculation error: {e}")

        return dcf

    def _calculate_sensitivity(
        self,
        base_cf: float,
        shares: float,
        discount_rate: float,
        growth_rate: float,
    ) -> dict[str, float]:
        """DCF 敏感性分析"""
        sensitivity = {}

        # 不同折现率
        for dr in [0.08, 0.10, 0.12]:
            for gr in [growth_rate * 0.8, growth_rate, growth_rate * 1.2]:
                # 简化计算
                pv = 0.0
                cf = base_cf
                for year in range(1, 6):
                    cf *= (1 + gr)
                    pv += cf / ((1 + dr) ** year)

                terminal_cf = cf * 1.03
                terminal_value = terminal_cf / (dr - 0.03)
                pv += terminal_value / ((1 + dr) ** 5)

                key = f"dr_{int(dr*100)}_gr_{int(gr*100)}"
                sensitivity[key] = round(pv / shares, 2)

        return sensitivity

    def _calculate_valuation_score(self, result: ValuationResult) -> float:
        """
        计算综合估值评分

        评分逻辑：
        - 50 分 = 合理估值
        - < 50 分 = 低估
        - > 50 分 = 高估
        """
        score = 50.0
        weight_sum = 0.0

        # 1. PE 历史对比
        if result.historical.pe_percentile is not None:
            pe_score = result.historical.pe_percentile  # 0-100
            score += (pe_score - 50) * self.WEIGHTS["pe_historical"]
            weight_sum += self.WEIGHTS["pe_historical"]

        # 2. PB 历史对比
        if result.historical.pb_percentile is not None:
            pb_score = result.historical.pb_percentile
            score += (pb_score - 50) * self.WEIGHTS["pb_historical"]
            weight_sum += self.WEIGHTS["pb_historical"]

        # 3. 行业对比
        if result.industry.pe_premium is not None:
            # 溢价 = 高估，折价 = 低估
            industry_score = 50 + result.industry.pe_premium
            industry_score = max(0, min(100, industry_score))
            score += (industry_score - 50) * self.WEIGHTS["industry_comparison"]
            weight_sum += self.WEIGHTS["industry_comparison"]

        # 4. PEG 估值
        if result.relative.peg is not None:
            if result.relative.peg < 1:
                peg_score = 30  # 低估
            elif result.relative.peg < 1.5:
                peg_score = 50  # 合理
            elif result.relative.peg < 2:
                peg_score = 65  # 略高
            else:
                peg_score = 80  # 高估
            score += (peg_score - 50) * self.WEIGHTS["peg"]
            weight_sum += self.WEIGHTS["peg"]

        # 5. DCF 估值
        if result.dcf.upside_potential is not None:
            # 上涨空间 > 0 = 低估
            dcf_score = 50 - result.dcf.upside_potential * 0.5
            dcf_score = max(0, min(100, dcf_score))
            score += (dcf_score - 50) * self.WEIGHTS["dcf"]
            weight_sum += self.WEIGHTS["dcf"]

        # 归一化
        if weight_sum > 0:
            # 已经是加权平均
            pass

        return round(max(0, min(100, score)), 1)

    def _get_valuation_level(self, result: ValuationResult) -> ValuationLevel:
        """根据评分确定估值水平"""
        score = result.valuation_score

        if score < 25:
            return ValuationLevel.SEVERELY_UNDERVALUED
        elif score < 40:
            return ValuationLevel.UNDERVALUED
        elif score < 60:
            return ValuationLevel.FAIRLY_VALUED
        elif score < 75:
            return ValuationLevel.OVERVALUED
        else:
            return ValuationLevel.SEVERELY_OVERVALUED

    def _estimate_target_price(self, result: ValuationResult) -> float | None:
        """估算目标价"""
        estimates = []

        # 从 DCF 获取
        if result.dcf.intrinsic_value:
            estimates.append(result.dcf.intrinsic_value)

        # 从历史均值估算
        if result.current_price and result.relative.pe_ttm and result.historical.pe_avg_5y:
            # 假设回归历史均值
            eps = result.current_price / result.relative.pe_ttm
            target_from_pe = eps * result.historical.pe_avg_5y
            estimates.append(target_from_pe)

        # 从行业均值估算
        if result.current_price and result.relative.pe_ttm and result.industry.industry_pe_avg:
            eps = result.current_price / result.relative.pe_ttm
            target_from_industry = eps * result.industry.industry_pe_avg
            estimates.append(target_from_industry)

        if estimates:
            return round(sum(estimates) / len(estimates), 2)

        return None

    def _generate_summary(self, result: ValuationResult) -> str:
        """生成估值总结"""
        level_text = {
            ValuationLevel.SEVERELY_UNDERVALUED: "估值严重偏低",
            ValuationLevel.UNDERVALUED: "估值偏低",
            ValuationLevel.FAIRLY_VALUED: "估值合理",
            ValuationLevel.OVERVALUED: "估值偏高",
            ValuationLevel.SEVERELY_OVERVALUED: "估值严重偏高",
        }

        summary = f"{result.symbol} 当前{level_text.get(result.valuation_level, '估值状态未知')}"

        if result.relative.pe_ttm:
            summary += f"，PE(TTM) {result.relative.pe_ttm:.1f}x"

        if result.target_price and result.current_price:
            if result.upside_potential and result.upside_potential > 0:
                summary += f"。目标价 {result.target_price:.2f}，潜在上涨空间 {result.upside_potential:.1f}%"
            elif result.upside_potential and result.upside_potential < 0:
                summary += f"。目标价 {result.target_price:.2f}，潜在下跌空间 {abs(result.upside_potential):.1f}%"

        summary += "。"

        return summary

    def _generate_key_points(self, result: ValuationResult) -> list[str]:
        """生成关键要点"""
        points = []

        # PE 分析
        if result.relative.pe_ttm:
            pe = result.relative.pe_ttm
            if result.historical.pe_avg_5y:
                diff = pe - result.historical.pe_avg_5y
                if abs(diff) > 5:
                    direction = "高于" if diff > 0 else "低于"
                    points.append(f"当前 PE {pe:.1f}x，{direction}历史均值 {result.historical.pe_avg_5y:.1f}x")

        # PEG 分析
        if result.relative.peg:
            peg = result.relative.peg
            if peg < 1:
                points.append(f"PEG {peg:.2f}，低于 1，具有成长性价值")
            elif peg > 2:
                points.append(f"PEG {peg:.2f}，高于 2，增长可能无法支撑估值")

        # 行业对比
        if result.industry.pe_premium is not None:
            premium = result.industry.pe_premium
            if abs(premium) > 20:
                direction = "溢价" if premium > 0 else "折价"
                points.append(f"相对行业{direction} {abs(premium):.0f}%")

        # DCF
        if result.dcf.upside_potential is not None:
            if result.dcf.upside_potential > 20:
                points.append(f"DCF 估值显示约 {result.dcf.upside_potential:.0f}% 上涨空间")
            elif result.dcf.upside_potential < -20:
                points.append(f"DCF 估值显示约 {abs(result.dcf.upside_potential):.0f}% 下跌风险")

        # 股息
        if result.relative.dividend_yield and result.relative.dividend_yield > 3:
            points.append(f"股息率 {result.relative.dividend_yield:.2f}%，具有分红价值")

        return points[:5]

    def _identify_valuation_risks(self, result: ValuationResult) -> list[str]:
        """识别估值风险"""
        risks = []

        # 高估风险
        if result.valuation_level in [ValuationLevel.OVERVALUED, ValuationLevel.SEVERELY_OVERVALUED]:
            risks.append("估值偏高，存在回调风险")

        # PE 风险
        if result.relative.pe_ttm and result.relative.pe_ttm > 50:
            risks.append(f"PE {result.relative.pe_ttm:.0f}x 过高，对业绩敏感")

        if result.relative.pe_ttm and result.relative.pe_ttm < 0:
            risks.append("公司处于亏损状态，PE 为负")

        # 行业风险
        if result.industry.pe_premium and result.industry.pe_premium > 50:
            risks.append("相对行业溢价过高，可能存在估值泡沫")

        # DCF 风险
        if result.dcf.upside_potential and result.dcf.upside_potential < -30:
            risks.append("DCF 估值显示显著高估")

        return risks[:4]

    def _get_value(self, data: dict[str, Any], keys: list[str]) -> float | None:
        """从字典中获取值"""
        for key in keys:
            value = data.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None


# 单例实例
_valuation_analyzer_instance: ValuationAnalyzer | None = None


def get_valuation_analyzer() -> ValuationAnalyzer:
    """获取估值分析器实例"""
    global _valuation_analyzer_instance
    if _valuation_analyzer_instance is None:
        _valuation_analyzer_instance = ValuationAnalyzer()
    return _valuation_analyzer_instance


__all__ = [
    "ValuationAnalyzer",
    "ValuationResult",
    "RelativeValuation",
    "HistoricalValuation",
    "IndustryComparison",
    "DCFValuation",
    "ValuationLevel",
    "get_valuation_analyzer",
]
