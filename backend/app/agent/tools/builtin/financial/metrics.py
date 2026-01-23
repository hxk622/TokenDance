"""
Financial Metrics Calculator - 财务指标计算模块

提供基于财务报表数据计算关键投资指标的功能：
- 盈利能力指标: ROE, ROA, 毛利率, 净利率
- 运营效率指标: 存货周转率, 应收账款周转率, 总资产周转率
- 偿债能力指标: 流动比率, 速动比率, 资产负债率
- 成长能力指标: 营收增长率, 利润增长率
- 杜邦分析

注意：所有指标仅供参考，不构成投资建议
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class MetricResult:
    """指标计算结果"""

    name: str                    # 指标名称
    name_en: str                 # 英文名称
    value: float | None          # 计算值
    unit: str = "%"             # 单位
    description: str = ""        # 说明
    benchmark: str = ""          # 参考基准
    error: str | None = None     # 错误信息

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "name_en": self.name_en,
            "value": round(self.value, 2) if self.value is not None else None,
            "unit": self.unit,
            "description": self.description,
            "benchmark": self.benchmark,
            "error": self.error,
        }


class FinancialMetricsCalculator:
    """财务指标计算器

    输入格式约定：
    - income_statement: 利润表数据
    - balance_sheet: 资产负债表数据
    - cash_flow: 现金流量表数据

    中文财报字段名对应关系见各方法内部
    """

    def __init__(
        self,
        income_statement: dict[str, Any] | None = None,
        balance_sheet: dict[str, Any] | None = None,
        cash_flow: dict[str, Any] | None = None,
        prev_income: dict[str, Any] | None = None,
        prev_balance: dict[str, Any] | None = None,
    ):
        """
        Args:
            income_statement: 当期利润表
            balance_sheet: 当期资产负债表
            cash_flow: 当期现金流量表
            prev_income: 上期利润表（用于计算增长率）
            prev_balance: 上期资产负债表（用于计算平均值）
        """
        self.income = income_statement or {}
        self.balance = balance_sheet or {}
        self.cash_flow = cash_flow or {}
        self.prev_income = prev_income or {}
        self.prev_balance = prev_balance or {}

    def _safe_div(self, numerator: float | None, denominator: float | None) -> float | None:
        """安全除法，避免除零"""
        if numerator is None or denominator is None or denominator == 0:
            return None
        return numerator / denominator

    def _get_value(self, data: dict, *keys: str) -> float | None:
        """从字典中获取值，支持多个可能的key"""
        for key in keys:
            if key in data and data[key] is not None:
                try:
                    return float(data[key])
                except (ValueError, TypeError):
                    continue
        return None

    def _average(self, current: float | None, previous: float | None) -> float | None:
        """计算平均值"""
        if current is None:
            return previous
        if previous is None:
            return current
        return (current + previous) / 2

    # ========== 盈利能力指标 ==========

    def calc_roe(self) -> MetricResult:
        """净资产收益率 (Return on Equity)

        公式: 净利润 / 平均股东权益 × 100%
        基准: 通常 > 15% 为优秀
        """
        net_profit = self._get_value(
            self.income, "净利润", "归属于母公司所有者的净利润", "net_profit"
        )

        equity = self._get_value(
            self.balance, "股东权益合计", "归属于母公司股东权益合计",
            "所有者权益", "shareholders_equity"
        )
        prev_equity = self._get_value(
            self.prev_balance, "股东权益合计", "归属于母公司股东权益合计",
            "所有者权益", "shareholders_equity"
        )

        avg_equity = self._average(equity, prev_equity)
        roe = self._safe_div(net_profit, avg_equity)

        return MetricResult(
            name="净资产收益率",
            name_en="ROE",
            value=roe * 100 if roe is not None else None,
            description="衡量股东投入资本的回报效率",
            benchmark="> 15% 优秀，10-15% 良好，< 10% 一般",
        )

    def calc_roa(self) -> MetricResult:
        """总资产收益率 (Return on Assets)

        公式: 净利润 / 平均总资产 × 100%
        基准: 通常 > 5% 为良好
        """
        net_profit = self._get_value(self.income, "净利润", "net_profit")

        total_assets = self._get_value(self.balance, "资产总计", "total_assets")
        prev_total_assets = self._get_value(self.prev_balance, "资产总计", "total_assets")

        avg_assets = self._average(total_assets, prev_total_assets)
        roa = self._safe_div(net_profit, avg_assets)

        return MetricResult(
            name="总资产收益率",
            name_en="ROA",
            value=roa * 100 if roa is not None else None,
            description="衡量公司运用全部资产获利的能力",
            benchmark="> 5% 良好，行业差异较大",
        )

    def calc_gross_margin(self) -> MetricResult:
        """毛利率 (Gross Profit Margin)

        公式: (营业收入 - 营业成本) / 营业收入 × 100%
        """
        revenue = self._get_value(self.income, "营业收入", "营业总收入", "revenue")
        cost = self._get_value(self.income, "营业成本", "营业总成本", "cost_of_revenue")

        if revenue is not None and cost is not None:
            gross_profit = revenue - cost
            margin = self._safe_div(gross_profit, revenue)
        else:
            margin = None

        return MetricResult(
            name="毛利率",
            name_en="Gross Margin",
            value=margin * 100 if margin is not None else None,
            description="反映产品/服务的基本盈利能力",
            benchmark="行业差异大，需与同行比较",
        )

    def calc_net_margin(self) -> MetricResult:
        """净利率 (Net Profit Margin)

        公式: 净利润 / 营业收入 × 100%
        """
        net_profit = self._get_value(self.income, "净利润", "net_profit")
        revenue = self._get_value(self.income, "营业收入", "营业总收入", "revenue")

        margin = self._safe_div(net_profit, revenue)

        return MetricResult(
            name="净利率",
            name_en="Net Margin",
            value=margin * 100 if margin is not None else None,
            description="反映最终盈利水平",
            benchmark="> 10% 良好，行业差异较大",
        )

    def calc_operating_margin(self) -> MetricResult:
        """营业利润率 (Operating Margin)

        公式: 营业利润 / 营业收入 × 100%
        """
        operating_profit = self._get_value(
            self.income, "营业利润", "operating_profit"
        )
        revenue = self._get_value(self.income, "营业收入", "营业总收入", "revenue")

        margin = self._safe_div(operating_profit, revenue)

        return MetricResult(
            name="营业利润率",
            name_en="Operating Margin",
            value=margin * 100 if margin is not None else None,
            description="反映主营业务的盈利能力",
            benchmark="行业差异大，需与同行比较",
        )

    # ========== 偿债能力指标 ==========

    def calc_current_ratio(self) -> MetricResult:
        """流动比率 (Current Ratio)

        公式: 流动资产 / 流动负债
        基准: 通常 1.5-2.0 为健康
        """
        current_assets = self._get_value(
            self.balance, "流动资产合计", "current_assets"
        )
        current_liabilities = self._get_value(
            self.balance, "流动负债合计", "current_liabilities"
        )

        ratio = self._safe_div(current_assets, current_liabilities)

        return MetricResult(
            name="流动比率",
            name_en="Current Ratio",
            value=ratio,
            unit="倍",
            description="衡量短期偿债能力",
            benchmark="1.5-2.0 为健康，< 1 可能有风险",
        )

    def calc_quick_ratio(self) -> MetricResult:
        """速动比率 (Quick Ratio / Acid Test)

        公式: (流动资产 - 存货) / 流动负债
        基准: 通常 > 1 为健康
        """
        current_assets = self._get_value(
            self.balance, "流动资产合计", "current_assets"
        )
        inventory = self._get_value(self.balance, "存货", "inventory") or 0
        current_liabilities = self._get_value(
            self.balance, "流动负债合计", "current_liabilities"
        )

        if current_assets is not None:
            quick_assets = current_assets - inventory
            ratio = self._safe_div(quick_assets, current_liabilities)
        else:
            ratio = None

        return MetricResult(
            name="速动比率",
            name_en="Quick Ratio",
            value=ratio,
            unit="倍",
            description="衡量不依赖存货的短期偿债能力",
            benchmark="> 1 为健康",
        )

    def calc_debt_to_equity(self) -> MetricResult:
        """资产负债率 (Debt to Equity Ratio)

        公式: 负债总计 / 资产总计 × 100%
        基准: 通常 40-60% 为健康
        """
        total_liabilities = self._get_value(
            self.balance, "负债合计", "total_liabilities"
        )
        total_assets = self._get_value(self.balance, "资产总计", "total_assets")

        ratio = self._safe_div(total_liabilities, total_assets)

        return MetricResult(
            name="资产负债率",
            name_en="Debt to Assets",
            value=ratio * 100 if ratio is not None else None,
            description="衡量财务杠杆和偿债压力",
            benchmark="40-60% 一般，> 70% 需关注",
        )

    # ========== 运营效率指标 ==========

    def calc_inventory_turnover(self) -> MetricResult:
        """存货周转率 (Inventory Turnover)

        公式: 营业成本 / 平均存货
        """
        cost = self._get_value(self.income, "营业成本", "cost_of_revenue")
        inventory = self._get_value(self.balance, "存货", "inventory")
        prev_inventory = self._get_value(self.prev_balance, "存货", "inventory")

        avg_inventory = self._average(inventory, prev_inventory)
        turnover = self._safe_div(cost, avg_inventory)

        return MetricResult(
            name="存货周转率",
            name_en="Inventory Turnover",
            value=turnover,
            unit="次/年",
            description="衡量存货周转效率",
            benchmark="越高越好，行业差异大",
        )

    def calc_receivables_turnover(self) -> MetricResult:
        """应收账款周转率 (Receivables Turnover)

        公式: 营业收入 / 平均应收账款
        """
        revenue = self._get_value(self.income, "营业收入", "revenue")
        receivables = self._get_value(
            self.balance, "应收账款", "accounts_receivable"
        )
        prev_receivables = self._get_value(
            self.prev_balance, "应收账款", "accounts_receivable"
        )

        avg_receivables = self._average(receivables, prev_receivables)
        turnover = self._safe_div(revenue, avg_receivables)

        return MetricResult(
            name="应收账款周转率",
            name_en="Receivables Turnover",
            value=turnover,
            unit="次/年",
            description="衡量应收账款收回效率",
            benchmark="越高越好，表示回款快",
        )

    def calc_asset_turnover(self) -> MetricResult:
        """总资产周转率 (Asset Turnover)

        公式: 营业收入 / 平均总资产
        """
        revenue = self._get_value(self.income, "营业收入", "revenue")
        total_assets = self._get_value(self.balance, "资产总计", "total_assets")
        prev_total_assets = self._get_value(
            self.prev_balance, "资产总计", "total_assets"
        )

        avg_assets = self._average(total_assets, prev_total_assets)
        turnover = self._safe_div(revenue, avg_assets)

        return MetricResult(
            name="总资产周转率",
            name_en="Asset Turnover",
            value=turnover,
            unit="次/年",
            description="衡量资产利用效率",
            benchmark="越高越好，反映运营效率",
        )

    # ========== 成长能力指标 ==========

    def calc_revenue_growth(self) -> MetricResult:
        """营收增长率 (Revenue Growth)

        公式: (本期营收 - 上期营收) / 上期营收 × 100%
        """
        revenue = self._get_value(self.income, "营业收入", "revenue")
        prev_revenue = self._get_value(self.prev_income, "营业收入", "revenue")

        if revenue is not None and prev_revenue is not None and prev_revenue != 0:
            growth = (revenue - prev_revenue) / abs(prev_revenue)
        else:
            growth = None

        return MetricResult(
            name="营收增长率",
            name_en="Revenue Growth",
            value=growth * 100 if growth is not None else None,
            description="衡量收入增长速度",
            benchmark="> 15% 高增长，5-15% 稳健",
        )

    def calc_profit_growth(self) -> MetricResult:
        """净利润增长率 (Net Profit Growth)

        公式: (本期净利 - 上期净利) / 上期净利 × 100%
        """
        profit = self._get_value(self.income, "净利润", "net_profit")
        prev_profit = self._get_value(self.prev_income, "净利润", "net_profit")

        if profit is not None and prev_profit is not None and prev_profit != 0:
            growth = (profit - prev_profit) / abs(prev_profit)
        else:
            growth = None

        return MetricResult(
            name="净利润增长率",
            name_en="Profit Growth",
            value=growth * 100 if growth is not None else None,
            description="衡量盈利增长速度",
            benchmark="关注是否与营收增长匹配",
        )

    # ========== 杜邦分析 ==========

    def dupont_analysis(self) -> dict[str, MetricResult]:
        """杜邦分析 (DuPont Analysis)

        ROE = 净利率 × 资产周转率 × 权益乘数

        分解 ROE 的驱动因素：
        - 净利率：盈利能力
        - 资产周转率：运营效率
        - 权益乘数：财务杠杆
        """
        # 计算各组成部分
        net_margin = self.calc_net_margin()
        asset_turnover = self.calc_asset_turnover()

        # 权益乘数 = 总资产 / 股东权益
        total_assets = self._get_value(self.balance, "资产总计", "total_assets")
        equity = self._get_value(
            self.balance, "股东权益合计", "所有者权益", "shareholders_equity"
        )
        equity_multiplier = self._safe_div(total_assets, equity)

        # 理论 ROE = 净利率 × 资产周转率 × 权益乘数
        theoretical_roe = None
        if all([
            net_margin.value is not None,
            asset_turnover.value is not None,
            equity_multiplier is not None
        ]):
            theoretical_roe = (
                (net_margin.value / 100) *
                asset_turnover.value *
                equity_multiplier * 100
            )

        return {
            "net_margin": net_margin,
            "asset_turnover": asset_turnover,
            "equity_multiplier": MetricResult(
                name="权益乘数",
                name_en="Equity Multiplier",
                value=equity_multiplier,
                unit="倍",
                description="反映财务杠杆程度",
                benchmark="越高杠杆越大，风险与收益并存",
            ),
            "theoretical_roe": MetricResult(
                name="理论ROE",
                name_en="Theoretical ROE",
                value=theoretical_roe,
                description="通过杜邦分析计算的 ROE",
                benchmark="应与实际 ROE 接近",
            ),
        }

    # ========== 批量计算 ==========

    def calc_all(self) -> dict[str, MetricResult]:
        """计算所有指标"""
        results = {
            # 盈利能力
            "roe": self.calc_roe(),
            "roa": self.calc_roa(),
            "gross_margin": self.calc_gross_margin(),
            "net_margin": self.calc_net_margin(),
            "operating_margin": self.calc_operating_margin(),

            # 偿债能力
            "current_ratio": self.calc_current_ratio(),
            "quick_ratio": self.calc_quick_ratio(),
            "debt_to_equity": self.calc_debt_to_equity(),

            # 运营效率
            "inventory_turnover": self.calc_inventory_turnover(),
            "receivables_turnover": self.calc_receivables_turnover(),
            "asset_turnover": self.calc_asset_turnover(),

            # 成长能力
            "revenue_growth": self.calc_revenue_growth(),
            "profit_growth": self.calc_profit_growth(),
        }

        # 添加杜邦分析
        results.update(self.dupont_analysis())

        return results

    def calc_summary(self) -> dict[str, Any]:
        """计算摘要，只返回有效值"""
        all_metrics = self.calc_all()

        summary = {
            "profitability": {},
            "solvency": {},
            "efficiency": {},
            "growth": {},
            "dupont": {},
        }

        category_mapping = {
            "roe": "profitability",
            "roa": "profitability",
            "gross_margin": "profitability",
            "net_margin": "profitability",
            "operating_margin": "profitability",
            "current_ratio": "solvency",
            "quick_ratio": "solvency",
            "debt_to_equity": "solvency",
            "inventory_turnover": "efficiency",
            "receivables_turnover": "efficiency",
            "asset_turnover": "efficiency",
            "revenue_growth": "growth",
            "profit_growth": "growth",
            "equity_multiplier": "dupont",
            "theoretical_roe": "dupont",
        }

        for key, metric in all_metrics.items():
            if metric.value is not None:
                category = category_mapping.get(key, "other")
                if category in summary:
                    summary[category][key] = metric.to_dict()

        return summary
