"""
FinancialAnalyzer - 财务分析服务

实现上市公司财务分析，包括：
1. 盈利能力分析 (Profitability)
2. 成长能力分析 (Growth)
3. 偿债能力分析 (Solvency)
4. 运营效率分析 (Efficiency)
5. 现金流分析 (Cash Flow)
6. 财务健康度评分 (Health Score)

使用方法：
    analyzer = FinancialAnalyzer()
    result = await analyzer.analyze("AAPL")
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthLevel(str, Enum):
    """财务健康等级"""
    EXCELLENT = "excellent"    # 优秀 (80-100)
    GOOD = "good"              # 良好 (60-80)
    FAIR = "fair"              # 一般 (40-60)
    POOR = "poor"              # 较差 (20-40)
    CRITICAL = "critical"      # 危险 (<20)


@dataclass
class ProfitabilityMetrics:
    """盈利能力指标"""
    # 毛利率 = (营业收入 - 营业成本) / 营业收入
    gross_margin: float | None = None
    # 净利率 = 净利润 / 营业收入
    net_margin: float | None = None
    # ROE = 净利润 / 股东权益
    roe: float | None = None
    # ROA = 净利润 / 总资产
    roa: float | None = None
    # ROIC = 税后营业利润 / 投入资本
    roic: float | None = None
    # 毛利 (绝对值)
    gross_profit: float | None = None
    # 营业利润
    operating_income: float | None = None
    # 净利润
    net_income: float | None = None

    # 评分 (0-100)
    score: float = 0.0
    # 评级
    grade: str = ""
    # 分析说明
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gross_margin": self.gross_margin,
            "net_margin": self.net_margin,
            "roe": self.roe,
            "roa": self.roa,
            "roic": self.roic,
            "gross_profit": self.gross_profit,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "score": self.score,
            "grade": self.grade,
            "analysis": self.analysis,
        }


@dataclass
class GrowthMetrics:
    """成长能力指标"""
    # 营收增长率 (YoY)
    revenue_growth: float | None = None
    # 净利润增长率 (YoY)
    net_income_growth: float | None = None
    # EPS 增长率 (YoY)
    eps_growth: float | None = None
    # 营收 CAGR (3年)
    revenue_cagr_3y: float | None = None
    # 净利润 CAGR (3年)
    net_income_cagr_3y: float | None = None
    # 研发费用增长率
    rd_growth: float | None = None

    # 评分和评级
    score: float = 0.0
    grade: str = ""
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "revenue_growth": self.revenue_growth,
            "net_income_growth": self.net_income_growth,
            "eps_growth": self.eps_growth,
            "revenue_cagr_3y": self.revenue_cagr_3y,
            "net_income_cagr_3y": self.net_income_cagr_3y,
            "rd_growth": self.rd_growth,
            "score": self.score,
            "grade": self.grade,
            "analysis": self.analysis,
        }


@dataclass
class SolvencyMetrics:
    """偿债能力指标"""
    # 流动比率 = 流动资产 / 流动负债 (理想 > 2)
    current_ratio: float | None = None
    # 速动比率 = (流动资产 - 存货) / 流动负债 (理想 > 1)
    quick_ratio: float | None = None
    # 资产负债率 = 总负债 / 总资产 (理想 < 60%)
    debt_to_assets: float | None = None
    # 产权比率 = 总负债 / 股东权益
    debt_to_equity: float | None = None
    # 利息保障倍数 = EBIT / 利息费用 (理想 > 3)
    interest_coverage: float | None = None
    # 现金比率 = 现金 / 流动负债
    cash_ratio: float | None = None

    # 评分和评级
    score: float = 0.0
    grade: str = ""
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_ratio": self.current_ratio,
            "quick_ratio": self.quick_ratio,
            "debt_to_assets": self.debt_to_assets,
            "debt_to_equity": self.debt_to_equity,
            "interest_coverage": self.interest_coverage,
            "cash_ratio": self.cash_ratio,
            "score": self.score,
            "grade": self.grade,
            "analysis": self.analysis,
        }


@dataclass
class EfficiencyMetrics:
    """运营效率指标"""
    # 存货周转率 = 营业成本 / 平均存货
    inventory_turnover: float | None = None
    # 存货周转天数
    inventory_days: float | None = None
    # 应收账款周转率 = 营业收入 / 平均应收账款
    receivables_turnover: float | None = None
    # 应收账款周转天数
    receivables_days: float | None = None
    # 总资产周转率 = 营业收入 / 平均总资产
    asset_turnover: float | None = None
    # 固定资产周转率
    fixed_asset_turnover: float | None = None

    # 评分和评级
    score: float = 0.0
    grade: str = ""
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_turnover": self.inventory_turnover,
            "inventory_days": self.inventory_days,
            "receivables_turnover": self.receivables_turnover,
            "receivables_days": self.receivables_days,
            "asset_turnover": self.asset_turnover,
            "fixed_asset_turnover": self.fixed_asset_turnover,
            "score": self.score,
            "grade": self.grade,
            "analysis": self.analysis,
        }


@dataclass
class CashFlowMetrics:
    """现金流指标"""
    # 经营现金流
    operating_cash_flow: float | None = None
    # 投资现金流
    investing_cash_flow: float | None = None
    # 筹资现金流
    financing_cash_flow: float | None = None
    # 自由现金流 = 经营现金流 - 资本支出
    free_cash_flow: float | None = None
    # 经营现金流/净利润 (理想 > 1)
    ocf_to_net_income: float | None = None
    # 经营现金流/营业收入
    ocf_to_revenue: float | None = None
    # 现金流量充足率
    cash_flow_adequacy: float | None = None

    # 评分和评级
    score: float = 0.0
    grade: str = ""
    analysis: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "operating_cash_flow": self.operating_cash_flow,
            "investing_cash_flow": self.investing_cash_flow,
            "financing_cash_flow": self.financing_cash_flow,
            "free_cash_flow": self.free_cash_flow,
            "ocf_to_net_income": self.ocf_to_net_income,
            "ocf_to_revenue": self.ocf_to_revenue,
            "cash_flow_adequacy": self.cash_flow_adequacy,
            "score": self.score,
            "grade": self.grade,
            "analysis": self.analysis,
        }


@dataclass
class FinancialAnalysisResult:
    """财务分析结果"""
    symbol: str
    company_name: str = ""
    market: str = ""
    currency: str = "USD"
    report_date: str = ""  # 财报日期

    # 各维度分析
    profitability: ProfitabilityMetrics = field(default_factory=ProfitabilityMetrics)
    growth: GrowthMetrics = field(default_factory=GrowthMetrics)
    solvency: SolvencyMetrics = field(default_factory=SolvencyMetrics)
    efficiency: EfficiencyMetrics = field(default_factory=EfficiencyMetrics)
    cash_flow: CashFlowMetrics = field(default_factory=CashFlowMetrics)

    # 综合评估
    overall_score: float = 0.0  # 0-100
    health_level: HealthLevel = HealthLevel.FAIR
    summary: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    key_risks: list[str] = field(default_factory=list)

    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    data_source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "company_name": self.company_name,
            "market": self.market,
            "currency": self.currency,
            "report_date": self.report_date,
            "profitability": self.profitability.to_dict(),
            "growth": self.growth.to_dict(),
            "solvency": self.solvency.to_dict(),
            "efficiency": self.efficiency.to_dict(),
            "cash_flow": self.cash_flow.to_dict(),
            "overall_score": self.overall_score,
            "health_level": self.health_level.value,
            "summary": self.summary,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "key_risks": self.key_risks,
            "timestamp": self.timestamp.isoformat(),
            "data_source": self.data_source,
        }


class FinancialAnalyzer:
    """
    财务分析服务

    分析上市公司的财务健康状况，生成多维度评估报告。
    """

    # 评分权重
    WEIGHTS = {
        "profitability": 0.30,  # 盈利能力 30%
        "growth": 0.25,         # 成长能力 25%
        "solvency": 0.20,       # 偿债能力 20%
        "efficiency": 0.15,     # 运营效率 15%
        "cash_flow": 0.10,      # 现金流 10%
    }

    def __init__(self):
        """初始化财务分析器"""
        # 延迟导入金融数据工具
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
        include_historical: bool = True,
    ) -> FinancialAnalysisResult:
        """
        执行完整财务分析

        Args:
            symbol: 股票代码
            market: 市场类型 (auto/us/cn/hk)
            include_historical: 是否包含历史数据对比

        Returns:
            FinancialAnalysisResult: 分析结果
        """
        logger.info(f"Starting financial analysis for {symbol}")

        result = FinancialAnalysisResult(symbol=symbol, market=market)

        try:
            # 获取财务数据
            tool = self._get_financial_tool()

            # 1. 获取财务报表
            fundamental_result = await tool.get_fundamental(symbol, market=market)

            # 2. 获取估值数据（包含部分财务指标）
            await tool.get_valuation(symbol, market=market)

            # 3. 解析并计算各维度指标
            if fundamental_result.success and fundamental_result.data:
                data = fundamental_result.data

                # 盈利能力分析
                result.profitability = self._analyze_profitability(data)

                # 成长能力分析
                result.growth = self._analyze_growth(data)

                # 偿债能力分析
                result.solvency = self._analyze_solvency(data)

                # 运营效率分析
                result.efficiency = self._analyze_efficiency(data)

                # 现金流分析
                result.cash_flow = self._analyze_cash_flow(data)

                # 计算综合评分
                result.overall_score = self._calculate_overall_score(result)
                result.health_level = self._get_health_level(result.overall_score)

                # 生成总结
                result.summary = self._generate_summary(result)
                result.strengths = self._identify_strengths(result)
                result.weaknesses = self._identify_weaknesses(result)
                result.key_risks = self._identify_risks(result)

                result.data_source = fundamental_result.source

            logger.info(f"Financial analysis completed for {symbol}, score: {result.overall_score}")

        except Exception as e:
            logger.error(f"Financial analysis failed for {symbol}: {e}")
            result.summary = f"分析失败: {str(e)}"

        return result

    def _analyze_profitability(self, data: dict[str, Any]) -> ProfitabilityMetrics:
        """分析盈利能力"""
        metrics = ProfitabilityMetrics()

        try:
            # 从财报数据中提取指标
            income = data.get("income_statement", {})
            balance = data.get("balance_sheet", {})

            # 提取数值（兼容不同数据源的字段名）
            revenue = self._get_value(income, ["revenue", "total_revenue", "营业收入"])
            cost = self._get_value(income, ["cost_of_revenue", "cost_of_goods_sold", "营业成本"])
            gross_profit = self._get_value(income, ["gross_profit", "毛利润"])
            operating_income = self._get_value(income, ["operating_income", "营业利润"])
            net_income = self._get_value(income, ["net_income", "净利润"])

            total_equity = self._get_value(balance, ["total_equity", "stockholders_equity", "股东权益"])
            total_assets = self._get_value(balance, ["total_assets", "总资产"])

            # 计算指标
            if revenue and cost:
                metrics.gross_margin = (revenue - cost) / revenue * 100
            if gross_profit:
                metrics.gross_profit = gross_profit
            if revenue and net_income:
                metrics.net_margin = net_income / revenue * 100
            if net_income and total_equity and total_equity != 0:
                metrics.roe = net_income / total_equity * 100
            if net_income and total_assets and total_assets != 0:
                metrics.roa = net_income / total_assets * 100
            if operating_income:
                metrics.operating_income = operating_income
            if net_income:
                metrics.net_income = net_income

            # 评分
            metrics.score = self._score_profitability(metrics)
            metrics.grade = self._get_grade(metrics.score)
            metrics.analysis = self._analyze_profitability_text(metrics)

        except Exception as e:
            logger.warning(f"Profitability analysis error: {e}")
            metrics.analysis = "数据不足，无法完成盈利能力分析"

        return metrics

    def _analyze_growth(self, data: dict[str, Any]) -> GrowthMetrics:
        """分析成长能力"""
        metrics = GrowthMetrics()

        try:
            # 如果有历史数据，计算增长率
            historical = data.get("historical", [])

            if len(historical) >= 2:
                current = historical[0]
                previous = historical[1]

                current_revenue = self._get_value(current, ["revenue", "total_revenue"])
                previous_revenue = self._get_value(previous, ["revenue", "total_revenue"])

                if current_revenue and previous_revenue and previous_revenue != 0:
                    metrics.revenue_growth = (current_revenue - previous_revenue) / previous_revenue * 100

                current_net_income = self._get_value(current, ["net_income"])
                previous_net_income = self._get_value(previous, ["net_income"])

                if current_net_income and previous_net_income and previous_net_income != 0:
                    metrics.net_income_growth = (current_net_income - previous_net_income) / previous_net_income * 100

            # 从其他来源获取增长数据
            growth_data = data.get("growth", {})
            if growth_data:
                metrics.revenue_growth = metrics.revenue_growth or growth_data.get("revenue_growth")
                metrics.eps_growth = growth_data.get("eps_growth")
                metrics.revenue_cagr_3y = growth_data.get("revenue_cagr_3y")

            # 评分
            metrics.score = self._score_growth(metrics)
            metrics.grade = self._get_grade(metrics.score)
            metrics.analysis = self._analyze_growth_text(metrics)

        except Exception as e:
            logger.warning(f"Growth analysis error: {e}")
            metrics.analysis = "数据不足，无法完成成长能力分析"

        return metrics

    def _analyze_solvency(self, data: dict[str, Any]) -> SolvencyMetrics:
        """分析偿债能力"""
        metrics = SolvencyMetrics()

        try:
            balance = data.get("balance_sheet", {})
            income = data.get("income_statement", {})

            # 提取数值
            current_assets = self._get_value(balance, ["current_assets", "流动资产"])
            current_liabilities = self._get_value(balance, ["current_liabilities", "流动负债"])
            inventory = self._get_value(balance, ["inventory", "存货"])
            cash = self._get_value(balance, ["cash", "cash_and_equivalents", "货币资金"])
            total_debt = self._get_value(balance, ["total_debt", "total_liabilities", "总负债"])
            total_assets = self._get_value(balance, ["total_assets", "总资产"])
            total_equity = self._get_value(balance, ["total_equity", "股东权益"])
            interest_expense = self._get_value(income, ["interest_expense", "利息费用"])
            ebit = self._get_value(income, ["ebit", "operating_income", "营业利润"])

            # 计算指标
            if current_assets and current_liabilities and current_liabilities != 0:
                metrics.current_ratio = current_assets / current_liabilities

                if inventory:
                    metrics.quick_ratio = (current_assets - inventory) / current_liabilities

                if cash:
                    metrics.cash_ratio = cash / current_liabilities

            if total_debt and total_assets and total_assets != 0:
                metrics.debt_to_assets = total_debt / total_assets * 100

            if total_debt and total_equity and total_equity != 0:
                metrics.debt_to_equity = total_debt / total_equity

            if ebit and interest_expense and interest_expense != 0:
                metrics.interest_coverage = ebit / interest_expense

            # 评分
            metrics.score = self._score_solvency(metrics)
            metrics.grade = self._get_grade(metrics.score)
            metrics.analysis = self._analyze_solvency_text(metrics)

        except Exception as e:
            logger.warning(f"Solvency analysis error: {e}")
            metrics.analysis = "数据不足，无法完成偿债能力分析"

        return metrics

    def _analyze_efficiency(self, data: dict[str, Any]) -> EfficiencyMetrics:
        """分析运营效率"""
        metrics = EfficiencyMetrics()

        try:
            balance = data.get("balance_sheet", {})
            income = data.get("income_statement", {})

            revenue = self._get_value(income, ["revenue", "total_revenue", "营业收入"])
            cost = self._get_value(income, ["cost_of_revenue", "营业成本"])
            inventory = self._get_value(balance, ["inventory", "存货"])
            receivables = self._get_value(balance, ["accounts_receivable", "应收账款"])
            total_assets = self._get_value(balance, ["total_assets", "总资产"])
            fixed_assets = self._get_value(balance, ["property_plant_equipment", "固定资产"])

            # 计算周转率
            if cost and inventory and inventory != 0:
                metrics.inventory_turnover = cost / inventory
                metrics.inventory_days = 365 / metrics.inventory_turnover

            if revenue and receivables and receivables != 0:
                metrics.receivables_turnover = revenue / receivables
                metrics.receivables_days = 365 / metrics.receivables_turnover

            if revenue and total_assets and total_assets != 0:
                metrics.asset_turnover = revenue / total_assets

            if revenue and fixed_assets and fixed_assets != 0:
                metrics.fixed_asset_turnover = revenue / fixed_assets

            # 评分
            metrics.score = self._score_efficiency(metrics)
            metrics.grade = self._get_grade(metrics.score)
            metrics.analysis = self._analyze_efficiency_text(metrics)

        except Exception as e:
            logger.warning(f"Efficiency analysis error: {e}")
            metrics.analysis = "数据不足，无法完成运营效率分析"

        return metrics

    def _analyze_cash_flow(self, data: dict[str, Any]) -> CashFlowMetrics:
        """分析现金流"""
        metrics = CashFlowMetrics()

        try:
            cf = data.get("cash_flow_statement", {})
            income = data.get("income_statement", {})

            ocf = self._get_value(cf, ["operating_cash_flow", "经营活动现金流"])
            icf = self._get_value(cf, ["investing_cash_flow", "投资活动现金流"])
            fcf_val = self._get_value(cf, ["financing_cash_flow", "筹资活动现金流"])
            capex = self._get_value(cf, ["capital_expenditure", "资本支出"])
            net_income = self._get_value(income, ["net_income", "净利润"])
            revenue = self._get_value(income, ["revenue", "营业收入"])

            if ocf:
                metrics.operating_cash_flow = ocf
            if icf:
                metrics.investing_cash_flow = icf
            if fcf_val:
                metrics.financing_cash_flow = fcf_val

            # 自由现金流
            if ocf and capex:
                metrics.free_cash_flow = ocf - abs(capex)
            elif ocf:
                metrics.free_cash_flow = ocf

            # 现金流质量
            if ocf and net_income and net_income != 0:
                metrics.ocf_to_net_income = ocf / net_income

            if ocf and revenue and revenue != 0:
                metrics.ocf_to_revenue = ocf / revenue

            # 评分
            metrics.score = self._score_cash_flow(metrics)
            metrics.grade = self._get_grade(metrics.score)
            metrics.analysis = self._analyze_cash_flow_text(metrics)

        except Exception as e:
            logger.warning(f"Cash flow analysis error: {e}")
            metrics.analysis = "数据不足，无法完成现金流分析"

        return metrics

    # ==================== 评分方法 ====================

    def _score_profitability(self, metrics: ProfitabilityMetrics) -> float:
        """盈利能力评分"""
        score = 50.0  # 基准分

        # ROE 评分 (权重 30%)
        if metrics.roe is not None:
            if metrics.roe >= 20:
                score += 15
            elif metrics.roe >= 15:
                score += 10
            elif metrics.roe >= 10:
                score += 5
            elif metrics.roe < 0:
                score -= 15

        # 毛利率评分 (权重 25%)
        if metrics.gross_margin is not None:
            if metrics.gross_margin >= 50:
                score += 12
            elif metrics.gross_margin >= 30:
                score += 8
            elif metrics.gross_margin >= 20:
                score += 4
            elif metrics.gross_margin < 10:
                score -= 10

        # 净利率评分 (权重 25%)
        if metrics.net_margin is not None:
            if metrics.net_margin >= 20:
                score += 12
            elif metrics.net_margin >= 10:
                score += 8
            elif metrics.net_margin >= 5:
                score += 4
            elif metrics.net_margin < 0:
                score -= 15

        # ROA 评分 (权重 20%)
        if metrics.roa is not None:
            if metrics.roa >= 10:
                score += 10
            elif metrics.roa >= 5:
                score += 6
            elif metrics.roa >= 2:
                score += 3

        return max(0, min(100, score))

    def _score_growth(self, metrics: GrowthMetrics) -> float:
        """成长能力评分"""
        score = 50.0

        # 营收增长评分
        if metrics.revenue_growth is not None:
            if metrics.revenue_growth >= 30:
                score += 20
            elif metrics.revenue_growth >= 15:
                score += 12
            elif metrics.revenue_growth >= 5:
                score += 5
            elif metrics.revenue_growth < 0:
                score -= 15

        # 净利润增长评分
        if metrics.net_income_growth is not None:
            if metrics.net_income_growth >= 30:
                score += 15
            elif metrics.net_income_growth >= 15:
                score += 10
            elif metrics.net_income_growth >= 5:
                score += 5
            elif metrics.net_income_growth < -20:
                score -= 20

        # EPS 增长评分
        if metrics.eps_growth is not None:
            if metrics.eps_growth >= 20:
                score += 10
            elif metrics.eps_growth >= 10:
                score += 5

        return max(0, min(100, score))

    def _score_solvency(self, metrics: SolvencyMetrics) -> float:
        """偿债能力评分"""
        score = 50.0

        # 流动比率评分
        if metrics.current_ratio is not None:
            if metrics.current_ratio >= 2:
                score += 15
            elif metrics.current_ratio >= 1.5:
                score += 10
            elif metrics.current_ratio >= 1:
                score += 5
            elif metrics.current_ratio < 0.8:
                score -= 15

        # 速动比率评分
        if metrics.quick_ratio is not None:
            if metrics.quick_ratio >= 1.5:
                score += 10
            elif metrics.quick_ratio >= 1:
                score += 5
            elif metrics.quick_ratio < 0.5:
                score -= 10

        # 资产负债率评分
        if metrics.debt_to_assets is not None:
            if metrics.debt_to_assets <= 40:
                score += 15
            elif metrics.debt_to_assets <= 60:
                score += 8
            elif metrics.debt_to_assets > 80:
                score -= 20

        # 利息保障倍数评分
        if metrics.interest_coverage is not None:
            if metrics.interest_coverage >= 5:
                score += 10
            elif metrics.interest_coverage >= 3:
                score += 5
            elif metrics.interest_coverage < 1:
                score -= 15

        return max(0, min(100, score))

    def _score_efficiency(self, metrics: EfficiencyMetrics) -> float:
        """运营效率评分"""
        score = 50.0

        # 存货周转天数评分
        if metrics.inventory_days is not None:
            if metrics.inventory_days <= 30:
                score += 15
            elif metrics.inventory_days <= 60:
                score += 10
            elif metrics.inventory_days <= 90:
                score += 5
            elif metrics.inventory_days > 180:
                score -= 10

        # 应收账款周转天数评分
        if metrics.receivables_days is not None:
            if metrics.receivables_days <= 30:
                score += 15
            elif metrics.receivables_days <= 60:
                score += 10
            elif metrics.receivables_days <= 90:
                score += 5
            elif metrics.receivables_days > 180:
                score -= 10

        # 总资产周转率评分
        if metrics.asset_turnover is not None:
            if metrics.asset_turnover >= 1.5:
                score += 15
            elif metrics.asset_turnover >= 1:
                score += 10
            elif metrics.asset_turnover >= 0.5:
                score += 5

        return max(0, min(100, score))

    def _score_cash_flow(self, metrics: CashFlowMetrics) -> float:
        """现金流评分"""
        score = 50.0

        # 经营现金流为正
        if metrics.operating_cash_flow is not None:
            if metrics.operating_cash_flow > 0:
                score += 15
            else:
                score -= 20

        # 自由现金流为正
        if metrics.free_cash_flow is not None:
            if metrics.free_cash_flow > 0:
                score += 15
            else:
                score -= 10

        # 经营现金流/净利润
        if metrics.ocf_to_net_income is not None:
            if metrics.ocf_to_net_income >= 1.2:
                score += 15
            elif metrics.ocf_to_net_income >= 1:
                score += 10
            elif metrics.ocf_to_net_income >= 0.8:
                score += 5
            elif metrics.ocf_to_net_income < 0.5:
                score -= 10

        return max(0, min(100, score))

    def _calculate_overall_score(self, result: FinancialAnalysisResult) -> float:
        """计算综合评分"""
        score = (
            result.profitability.score * self.WEIGHTS["profitability"] +
            result.growth.score * self.WEIGHTS["growth"] +
            result.solvency.score * self.WEIGHTS["solvency"] +
            result.efficiency.score * self.WEIGHTS["efficiency"] +
            result.cash_flow.score * self.WEIGHTS["cash_flow"]
        )
        return round(score, 1)

    def _get_health_level(self, score: float) -> HealthLevel:
        """根据评分获取健康等级"""
        if score >= 80:
            return HealthLevel.EXCELLENT
        elif score >= 60:
            return HealthLevel.GOOD
        elif score >= 40:
            return HealthLevel.FAIR
        elif score >= 20:
            return HealthLevel.POOR
        else:
            return HealthLevel.CRITICAL

    def _get_grade(self, score: float) -> str:
        """获取等级标签"""
        if score >= 80:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        elif score >= 20:
            return "D"
        else:
            return "F"

    # ==================== 文本分析方法 ====================

    def _analyze_profitability_text(self, metrics: ProfitabilityMetrics) -> str:
        """生成盈利能力分析文本"""
        parts = []

        if metrics.roe is not None:
            if metrics.roe >= 15:
                parts.append(f"ROE {metrics.roe:.1f}%，股东回报优秀")
            elif metrics.roe >= 10:
                parts.append(f"ROE {metrics.roe:.1f}%，股东回报良好")
            else:
                parts.append(f"ROE {metrics.roe:.1f}%，股东回报一般")

        if metrics.gross_margin is not None:
            if metrics.gross_margin >= 40:
                parts.append(f"毛利率 {metrics.gross_margin:.1f}%，具有较强定价权")
            elif metrics.gross_margin < 20:
                parts.append(f"毛利率 {metrics.gross_margin:.1f}%，盈利空间有限")

        return "；".join(parts) if parts else "数据不足"

    def _analyze_growth_text(self, metrics: GrowthMetrics) -> str:
        """生成成长能力分析文本"""
        parts = []

        if metrics.revenue_growth is not None:
            if metrics.revenue_growth >= 20:
                parts.append(f"营收增长 {metrics.revenue_growth:.1f}%，高速成长")
            elif metrics.revenue_growth >= 10:
                parts.append(f"营收增长 {metrics.revenue_growth:.1f}%，稳健增长")
            elif metrics.revenue_growth < 0:
                parts.append(f"营收下滑 {metrics.revenue_growth:.1f}%，需关注")

        if metrics.net_income_growth is not None:
            if metrics.net_income_growth >= 20:
                parts.append(f"利润增长 {metrics.net_income_growth:.1f}%")
            elif metrics.net_income_growth < -10:
                parts.append(f"利润下滑 {metrics.net_income_growth:.1f}%，盈利承压")

        return "；".join(parts) if parts else "数据不足"

    def _analyze_solvency_text(self, metrics: SolvencyMetrics) -> str:
        """生成偿债能力分析文本"""
        parts = []

        if metrics.current_ratio is not None:
            if metrics.current_ratio >= 2:
                parts.append(f"流动比率 {metrics.current_ratio:.2f}，短期偿债能力强")
            elif metrics.current_ratio < 1:
                parts.append(f"流动比率 {metrics.current_ratio:.2f}，短期偿债压力大")

        if metrics.debt_to_assets is not None:
            if metrics.debt_to_assets <= 50:
                parts.append(f"资产负债率 {metrics.debt_to_assets:.1f}%，杠杆适中")
            elif metrics.debt_to_assets > 70:
                parts.append(f"资产负债率 {metrics.debt_to_assets:.1f}%，杠杆较高")

        return "；".join(parts) if parts else "数据不足"

    def _analyze_efficiency_text(self, metrics: EfficiencyMetrics) -> str:
        """生成运营效率分析文本"""
        parts = []

        if metrics.inventory_days is not None:
            if metrics.inventory_days <= 60:
                parts.append(f"存货周转 {metrics.inventory_days:.0f} 天，存货管理效率高")
            elif metrics.inventory_days > 120:
                parts.append(f"存货周转 {metrics.inventory_days:.0f} 天，存货积压风险")

        if metrics.receivables_days is not None:
            if metrics.receivables_days <= 45:
                parts.append(f"应收周转 {metrics.receivables_days:.0f} 天，回款较快")
            elif metrics.receivables_days > 90:
                parts.append(f"应收周转 {metrics.receivables_days:.0f} 天，坏账风险增加")

        return "；".join(parts) if parts else "数据不足"

    def _analyze_cash_flow_text(self, metrics: CashFlowMetrics) -> str:
        """生成现金流分析文本"""
        parts = []

        if metrics.operating_cash_flow is not None:
            if metrics.operating_cash_flow > 0:
                parts.append("经营现金流为正，造血能力正常")
            else:
                parts.append("经营现金流为负，造血能力不足")

        if metrics.free_cash_flow is not None:
            if metrics.free_cash_flow > 0:
                parts.append("自由现金流为正，有能力分红或再投资")
            else:
                parts.append("自由现金流为负，依赖外部融资")

        if metrics.ocf_to_net_income is not None:
            if metrics.ocf_to_net_income >= 1:
                parts.append("现金流质量好，盈利含金量高")
            elif metrics.ocf_to_net_income < 0.7:
                parts.append("现金流质量差，利润可能含水分")

        return "；".join(parts) if parts else "数据不足"

    def _generate_summary(self, result: FinancialAnalysisResult) -> str:
        """生成综合总结"""
        level_text = {
            HealthLevel.EXCELLENT: "财务状况优秀",
            HealthLevel.GOOD: "财务状况良好",
            HealthLevel.FAIR: "财务状况一般",
            HealthLevel.POOR: "财务状况较差",
            HealthLevel.CRITICAL: "财务状况危险",
        }

        return (
            f"{result.symbol} 综合财务评分 {result.overall_score} 分，"
            f"{level_text.get(result.health_level, '未知')}。"
            f"盈利能力{result.profitability.grade}级，"
            f"成长能力{result.growth.grade}级，"
            f"偿债能力{result.solvency.grade}级。"
        )

    def _identify_strengths(self, result: FinancialAnalysisResult) -> list[str]:
        """识别财务优势"""
        strengths = []

        if result.profitability.score >= 70:
            strengths.append("盈利能力强")
        if result.profitability.roe and result.profitability.roe >= 15:
            strengths.append(f"ROE 优秀 ({result.profitability.roe:.1f}%)")
        if result.growth.score >= 70:
            strengths.append("成长性好")
        if result.solvency.score >= 70:
            strengths.append("财务稳健，偿债能力强")
        if result.cash_flow.free_cash_flow and result.cash_flow.free_cash_flow > 0:
            strengths.append("自由现金流充裕")

        return strengths[:5]  # 最多返回5个

    def _identify_weaknesses(self, result: FinancialAnalysisResult) -> list[str]:
        """识别财务劣势"""
        weaknesses = []

        if result.profitability.score < 40:
            weaknesses.append("盈利能力不足")
        if result.profitability.net_margin and result.profitability.net_margin < 5:
            weaknesses.append(f"净利率偏低 ({result.profitability.net_margin:.1f}%)")
        if result.growth.score < 40:
            weaknesses.append("成长乏力")
        if result.solvency.debt_to_assets and result.solvency.debt_to_assets > 70:
            weaknesses.append(f"负债率较高 ({result.solvency.debt_to_assets:.1f}%)")
        if result.cash_flow.operating_cash_flow and result.cash_flow.operating_cash_flow < 0:
            weaknesses.append("经营现金流为负")

        return weaknesses[:5]

    def _identify_risks(self, result: FinancialAnalysisResult) -> list[str]:
        """识别关键风险"""
        risks = []

        # 偿债风险
        if result.solvency.current_ratio and result.solvency.current_ratio < 1:
            risks.append("短期偿债压力大，流动性风险")
        if result.solvency.interest_coverage and result.solvency.interest_coverage < 2:
            risks.append("利息保障不足，债务风险")

        # 盈利风险
        if result.profitability.net_margin and result.profitability.net_margin < 0:
            risks.append("持续亏损，可能需要融资")
        if result.growth.revenue_growth and result.growth.revenue_growth < -10:
            risks.append("营收大幅下滑，业务萎缩")

        # 现金流风险
        if result.cash_flow.operating_cash_flow and result.cash_flow.operating_cash_flow < 0:
            risks.append("经营现金流为负，依赖外部融资")
        if result.cash_flow.ocf_to_net_income and result.cash_flow.ocf_to_net_income < 0.5:
            risks.append("利润含金量低，可能存在应收账款问题")

        return risks[:5]

    # ==================== 工具方法 ====================

    def _get_value(self, data: dict[str, Any], keys: list[str]) -> float | None:
        """从字典中获取值，支持多个备选键名"""
        for key in keys:
            value = data.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None


# 单例实例
_analyzer_instance: FinancialAnalyzer | None = None


def get_financial_analyzer() -> FinancialAnalyzer:
    """获取财务分析器实例（单例）"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FinancialAnalyzer()
    return _analyzer_instance


__all__ = [
    "FinancialAnalyzer",
    "FinancialAnalysisResult",
    "ProfitabilityMetrics",
    "GrowthMetrics",
    "SolvencyMetrics",
    "EfficiencyMetrics",
    "CashFlowMetrics",
    "HealthLevel",
    "get_financial_analyzer",
]
