"""
CustomerSupplierService - 客户/供应商分析服务

提供：
1. 主要客户分析
2. 主要供应商分析
3. 客户/供应商集中度
4. 关系稳定性评估
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RelationType(str, Enum):
    """关系类型"""
    CUSTOMER = "customer"
    SUPPLIER = "supplier"


class RelationStrength(str, Enum):
    """关系强度"""
    STRATEGIC = "strategic"   # 战略合作
    IMPORTANT = "important"   # 重要关系
    NORMAL = "normal"         # 一般关系
    OCCASIONAL = "occasional" # 偶发关系


@dataclass
class CustomerSupplierRelation:
    """客户/供应商关系"""
    symbol: str
    name: str
    relation_type: RelationType

    # 交易信息
    transaction_amount: float  # 交易金额（亿）
    revenue_pct: float         # 占收入/采购比例
    relationship_years: int    # 合作年限

    # 关系评估
    strength: RelationStrength
    is_listed: bool = False
    listed_symbol: str | None = None

    # 风险
    dependency_risk: str = "medium"  # 依赖风险

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "relation_type": self.relation_type.value,
            "transaction_amount": self.transaction_amount,
            "revenue_pct": self.revenue_pct,
            "relationship_years": self.relationship_years,
            "strength": self.strength.value,
            "is_listed": self.is_listed,
            "listed_symbol": self.listed_symbol,
            "dependency_risk": self.dependency_risk,
        }


@dataclass
class ConcentrationAnalysis:
    """集中度分析"""
    top1_pct: float
    top5_pct: float
    top10_pct: float
    herfindahl_index: float  # HHI指数
    concentration_level: str  # 高/中/低

    def to_dict(self) -> dict[str, Any]:
        return {
            "top1_pct": self.top1_pct,
            "top5_pct": self.top5_pct,
            "top10_pct": self.top10_pct,
            "herfindahl_index": self.herfindahl_index,
            "concentration_level": self.concentration_level,
        }


@dataclass
class CustomerSupplierResult:
    """客户/供应商分析结果"""
    symbol: str
    name: str
    analysis_date: datetime

    # 客户分析
    customers: list[CustomerSupplierRelation] = field(default_factory=list)
    customer_concentration: ConcentrationAnalysis | None = None

    # 供应商分析
    suppliers: list[CustomerSupplierRelation] = field(default_factory=list)
    supplier_concentration: ConcentrationAnalysis | None = None

    # 风险提示
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "analysis_date": self.analysis_date.isoformat(),
            "customers": [c.to_dict() for c in self.customers],
            "customer_concentration": self.customer_concentration.to_dict() if self.customer_concentration else None,
            "suppliers": [s.to_dict() for s in self.suppliers],
            "supplier_concentration": self.supplier_concentration.to_dict() if self.supplier_concentration else None,
            "risks": self.risks,
        }


class CustomerSupplierService:
    """客户/供应商分析服务"""

    def __init__(self):
        self._cache: dict[str, CustomerSupplierResult] = {}

    async def analyze_customer_supplier(
        self,
        symbol: str,
    ) -> CustomerSupplierResult:
        """分析客户供应商关系"""
        if symbol in self._cache:
            return self._cache[symbol]

        try:
            # 获取客户列表
            customers = await self._get_customers(symbol)
            customer_concentration = self._analyze_concentration(customers)

            # 获取供应商列表
            suppliers = await self._get_suppliers(symbol)
            supplier_concentration = self._analyze_concentration(suppliers)

            # 风险分析
            risks = self._analyze_risks(customers, suppliers, customer_concentration, supplier_concentration)

            result = CustomerSupplierResult(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                analysis_date=datetime.now(),
                customers=customers,
                customer_concentration=customer_concentration,
                suppliers=suppliers,
                supplier_concentration=supplier_concentration,
                risks=risks,
            )

            self._cache[symbol] = result
            return result

        except Exception as e:
            logger.error(f"Failed to analyze customer/supplier for {symbol}: {e}")
            return CustomerSupplierResult(
                symbol=symbol,
                name="",
                analysis_date=datetime.now(),
            )

    async def get_related_companies(
        self,
        symbol: str,
    ) -> dict[str, list[str]]:
        """获取关联公司"""
        result = await self.analyze_customer_supplier(symbol)

        return {
            "customers": [c.name for c in result.customers if c.is_listed],
            "suppliers": [s.name for s in result.suppliers if s.is_listed],
        }

    async def _get_customers(self, symbol: str) -> list[CustomerSupplierRelation]:
        """获取客户列表"""
        import random

        # Mock 数据
        customer_names = [
            ("客户A", True, "600000"),
            ("客户B", False, None),
            ("客户C", True, "000001"),
            ("客户D", False, None),
            ("客户E", True, "600519"),
        ]

        customers = []
        remaining_pct = 100.0

        for i, (name, is_listed, listed_symbol) in enumerate(customer_names):
            if remaining_pct <= 0:
                break

            pct = random.uniform(5, min(30, remaining_pct))
            remaining_pct -= pct

            customers.append(CustomerSupplierRelation(
                symbol=f"CUST_{i}",
                name=name,
                relation_type=RelationType.CUSTOMER,
                transaction_amount=round(random.uniform(1, 50), 2),
                revenue_pct=round(pct, 1),
                relationship_years=random.randint(1, 10),
                strength=random.choice(list(RelationStrength)),
                is_listed=is_listed,
                listed_symbol=listed_symbol,
                dependency_risk="high" if pct > 20 else "medium" if pct > 10 else "low",
            ))

        return sorted(customers, key=lambda x: x.revenue_pct, reverse=True)

    async def _get_suppliers(self, symbol: str) -> list[CustomerSupplierRelation]:
        """获取供应商列表"""
        import random

        supplier_names = [
            ("供应商A", True, "601398"),
            ("供应商B", False, None),
            ("供应商C", True, "000858"),
            ("供应商D", False, None),
        ]

        suppliers = []
        remaining_pct = 100.0

        for i, (name, is_listed, listed_symbol) in enumerate(supplier_names):
            if remaining_pct <= 0:
                break

            pct = random.uniform(5, min(35, remaining_pct))
            remaining_pct -= pct

            suppliers.append(CustomerSupplierRelation(
                symbol=f"SUPP_{i}",
                name=name,
                relation_type=RelationType.SUPPLIER,
                transaction_amount=round(random.uniform(0.5, 30), 2),
                revenue_pct=round(pct, 1),
                relationship_years=random.randint(1, 15),
                strength=random.choice(list(RelationStrength)),
                is_listed=is_listed,
                listed_symbol=listed_symbol,
                dependency_risk="high" if pct > 25 else "medium" if pct > 15 else "low",
            ))

        return sorted(suppliers, key=lambda x: x.revenue_pct, reverse=True)

    def _analyze_concentration(
        self,
        relations: list[CustomerSupplierRelation],
    ) -> ConcentrationAnalysis:
        """分析集中度"""
        if not relations:
            return ConcentrationAnalysis(
                top1_pct=0, top5_pct=0, top10_pct=0,
                herfindahl_index=0, concentration_level="低",
            )

        sorted_relations = sorted(relations, key=lambda x: x.revenue_pct, reverse=True)

        top1_pct = sorted_relations[0].revenue_pct if len(sorted_relations) >= 1 else 0
        top5_pct = sum(r.revenue_pct for r in sorted_relations[:5])
        top10_pct = sum(r.revenue_pct for r in sorted_relations[:10])

        # HHI指数
        hhi = sum(r.revenue_pct ** 2 for r in relations) / 10000

        # 集中度判断
        if top5_pct > 60:
            level = "高"
        elif top5_pct > 40:
            level = "中"
        else:
            level = "低"

        return ConcentrationAnalysis(
            top1_pct=round(top1_pct, 1),
            top5_pct=round(top5_pct, 1),
            top10_pct=round(top10_pct, 1),
            herfindahl_index=round(hhi, 4),
            concentration_level=level,
        )

    def _analyze_risks(
        self,
        customers: list[CustomerSupplierRelation],
        suppliers: list[CustomerSupplierRelation],
        customer_conc: ConcentrationAnalysis,
        supplier_conc: ConcentrationAnalysis,
    ) -> list[str]:
        """分析风险"""
        risks = []

        # 客户集中度风险
        if customer_conc and customer_conc.top1_pct > 25:
            risks.append(f"客户集中度高：第一大客户占比{customer_conc.top1_pct}%")

        # 供应商集中度风险
        if supplier_conc and supplier_conc.top1_pct > 30:
            risks.append(f"供应商集中度高：第一大供应商占比{supplier_conc.top1_pct}%")

        # 高依赖关系
        high_dep_customers = [c for c in customers if c.dependency_risk == "high"]
        if high_dep_customers:
            risks.append(f"存在{len(high_dep_customers)}个高依赖客户")

        high_dep_suppliers = [s for s in suppliers if s.dependency_risk == "high"]
        if high_dep_suppliers:
            risks.append(f"存在{len(high_dep_suppliers)}个高依赖供应商")

        return risks

    def _get_stock_name(self, symbol: str) -> str:
        """获取股票名称"""
        names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "600036": "招商银行",
            "000333": "美的集团",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_customer_supplier_service: CustomerSupplierService | None = None


def get_customer_supplier_service() -> CustomerSupplierService:
    """获取客户供应商服务单例"""
    global _customer_supplier_service
    if _customer_supplier_service is None:
        _customer_supplier_service = CustomerSupplierService()
    return _customer_supplier_service
