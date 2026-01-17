# -*- coding: utf-8 -*-
"""
StressTestService - 压力测试服务

提供：
1. 历史情景压力测试
2. 假设情景压力测试
3. 极端情景分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ScenarioType(str, Enum):
    """情景类型"""
    HISTORICAL = "historical"     # 历史情景
    HYPOTHETICAL = "hypothetical" # 假设情景
    EXTREME = "extreme"           # 极端情景


@dataclass
class StressScenario:
    """压力测试情景"""
    scenario_id: str
    name: str
    scenario_type: ScenarioType
    description: str
    
    # 因子冲击
    market_shock: float = 0.0     # 市场冲击 (%)
    industry_shocks: Dict[str, float] = field(default_factory=dict)
    factor_shocks: Dict[str, float] = field(default_factory=dict)
    
    # 历史情景参考
    reference_period: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "scenario_type": self.scenario_type.value,
            "description": self.description,
            "market_shock": self.market_shock,
            "industry_shocks": self.industry_shocks,
            "factor_shocks": self.factor_shocks,
            "reference_period": self.reference_period,
        }


@dataclass
class PositionImpact:
    """持仓影响"""
    symbol: str
    name: str
    weight: float
    expected_loss: float
    expected_loss_pct: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "weight": self.weight,
            "expected_loss": self.expected_loss,
            "expected_loss_pct": self.expected_loss_pct,
        }


@dataclass
class StressTestResult:
    """压力测试结果"""
    portfolio_id: str
    scenario: StressScenario
    test_date: datetime
    
    # 组合影响
    portfolio_loss: float         # 预期损失金额
    portfolio_loss_pct: float     # 预期损失百分比
    
    # 持仓影响
    position_impacts: List[PositionImpact] = field(default_factory=list)
    
    # 风险指标变化
    var_change: float = 0.0       # VaR变化
    volatility_change: float = 0.0  # 波动率变化
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "portfolio_id": self.portfolio_id,
            "scenario": self.scenario.to_dict(),
            "test_date": self.test_date.isoformat(),
            "portfolio_loss": self.portfolio_loss,
            "portfolio_loss_pct": self.portfolio_loss_pct,
            "position_impacts": [p.to_dict() for p in self.position_impacts],
            "var_change": self.var_change,
            "volatility_change": self.volatility_change,
        }


class StressTestService:
    """压力测试服务"""
    
    # 预定义情景
    PREDEFINED_SCENARIOS = {
        "2008_financial_crisis": StressScenario(
            scenario_id="2008_financial_crisis",
            name="2008年金融危机",
            scenario_type=ScenarioType.HISTORICAL,
            description="模拟2008年全球金融危机对组合的影响",
            market_shock=-40,
            industry_shocks={"金融": -50, "房地产": -45, "消费": -30},
            reference_period="2008-09 to 2009-03",
        ),
        "2015_stock_crash": StressScenario(
            scenario_id="2015_stock_crash",
            name="2015年A股股灾",
            scenario_type=ScenarioType.HISTORICAL,
            description="模拟2015年A股股灾对组合的影响",
            market_shock=-45,
            industry_shocks={"科技": -55, "金融": -40},
            reference_period="2015-06 to 2015-09",
        ),
        "covid_crash": StressScenario(
            scenario_id="covid_crash",
            name="2020年新冠疫情冲击",
            scenario_type=ScenarioType.HISTORICAL,
            description="模拟2020年新冠疫情初期对组合的影响",
            market_shock=-15,
            industry_shocks={"旅游": -50, "航空": -45, "医药": 20},
            reference_period="2020-01 to 2020-03",
        ),
        "interest_rate_shock": StressScenario(
            scenario_id="interest_rate_shock",
            name="利率大幅上升",
            scenario_type=ScenarioType.HYPOTHETICAL,
            description="假设利率上升200bp对组合的影响",
            market_shock=-10,
            industry_shocks={"房地产": -20, "银行": 5},
            factor_shocks={"利率因子": 200},
        ),
        "extreme_bear": StressScenario(
            scenario_id="extreme_bear",
            name="极端熊市",
            scenario_type=ScenarioType.EXTREME,
            description="市场下跌50%的极端情景",
            market_shock=-50,
        ),
    }
    
    def __init__(self):
        self._cache: Dict[str, StressTestResult] = {}
    
    async def run_stress_test(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
        scenario_id: str,
    ) -> StressTestResult:
        """运行压力测试"""
        scenario = self.PREDEFINED_SCENARIOS.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        return await self._run_test(portfolio_id, holdings, scenario)
    
    async def run_custom_stress_test(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
        scenario: StressScenario,
    ) -> StressTestResult:
        """运行自定义压力测试"""
        return await self._run_test(portfolio_id, holdings, scenario)
    
    async def run_all_scenarios(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
    ) -> List[StressTestResult]:
        """运行所有预定义情景"""
        results = []
        for scenario in self.PREDEFINED_SCENARIOS.values():
            result = await self._run_test(portfolio_id, holdings, scenario)
            results.append(result)
        return results
    
    def get_available_scenarios(self) -> List[Dict[str, Any]]:
        """获取可用情景列表"""
        return [s.to_dict() for s in self.PREDEFINED_SCENARIOS.values()]
    
    async def _run_test(
        self,
        portfolio_id: str,
        holdings: List[Dict[str, Any]],
        scenario: StressScenario,
    ) -> StressTestResult:
        """执行压力测试"""
        import random
        
        # 计算组合价值
        portfolio_value = sum(h.get("value", 0) for h in holdings)
        if portfolio_value == 0:
            portfolio_value = 1000000  # 默认100万
        
        # 计算各持仓影响
        position_impacts = []
        total_loss = 0
        
        for holding in holdings:
            symbol = holding.get("symbol", "")
            weight = holding.get("weight", 0)
            value = holding.get("value", portfolio_value * weight)
            
            # 基于行业和市场冲击计算损失
            industry = self._get_stock_industry(symbol)
            industry_shock = scenario.industry_shocks.get(industry, 0)
            position_shock = scenario.market_shock + industry_shock * 0.3
            position_shock *= random.uniform(0.8, 1.2)  # 增加一些随机性
            
            expected_loss = value * position_shock / 100
            
            position_impacts.append(PositionImpact(
                symbol=symbol,
                name=self._get_stock_name(symbol),
                weight=round(weight * 100, 2),
                expected_loss=round(expected_loss, 2),
                expected_loss_pct=round(position_shock, 2),
            ))
            
            total_loss += expected_loss
        
        portfolio_loss_pct = total_loss / portfolio_value * 100 if portfolio_value > 0 else 0
        
        return StressTestResult(
            portfolio_id=portfolio_id,
            scenario=scenario,
            test_date=datetime.now(),
            portfolio_loss=round(total_loss, 2),
            portfolio_loss_pct=round(portfolio_loss_pct, 2),
            position_impacts=sorted(position_impacts, key=lambda x: x.expected_loss),
            var_change=round(abs(scenario.market_shock) * 0.5, 2),
            volatility_change=round(abs(scenario.market_shock) * 0.3, 2),
        )
    
    def _get_stock_industry(self, symbol: str) -> str:
        industries = {
            "600519": "消费", "000858": "消费",
            "600036": "金融", "000333": "消费",
        }
        return industries.get(symbol, "其他")
    
    def _get_stock_name(self, symbol: str) -> str:
        names = {
            "600519": "贵州茅台", "000858": "五粮液",
            "600036": "招商银行", "000333": "美的集团",
        }
        return names.get(symbol, f"股票{symbol}")


# 全局单例
_stress_test_service: Optional[StressTestService] = None


def get_stress_test_service() -> StressTestService:
    global _stress_test_service
    if _stress_test_service is None:
        _stress_test_service = StressTestService()
    return _stress_test_service
