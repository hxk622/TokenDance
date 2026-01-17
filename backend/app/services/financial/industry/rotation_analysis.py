"""
RotationAnalysisService - 行业轮动分析服务

提供：
1. 行业轮动规律识别
2. 经济周期与行业表现
3. 动量因子分析
4. 领先/滞后行业识别
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EconomicCycle(str, Enum):
    """经济周期阶段"""
    RECOVERY = "recovery"       # 复苏
    EXPANSION = "expansion"     # 扩张
    PEAK = "peak"               # 顶峰
    CONTRACTION = "contraction" # 收缩
    TROUGH = "trough"           # 谷底


class MomentumSignal(str, Enum):
    """动量信号"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class IndustryMomentum:
    """行业动量"""
    industry: str
    return_1w: float   # 1周收益率
    return_1m: float   # 1月收益率
    return_3m: float   # 3月收益率
    return_6m: float   # 6月收益率
    momentum_score: float  # 动量得分
    signal: MomentumSignal
    rank: int = 0  # 在所有行业中的排名

    def to_dict(self) -> dict[str, Any]:
        return {
            "industry": self.industry,
            "return_1w": self.return_1w,
            "return_1m": self.return_1m,
            "return_3m": self.return_3m,
            "return_6m": self.return_6m,
            "momentum_score": self.momentum_score,
            "signal": self.signal.value,
            "rank": self.rank,
        }


@dataclass
class RotationPattern:
    """轮动模式"""
    from_industry: str
    to_industry: str
    frequency: int        # 历史发生次数
    avg_duration_days: int  # 平均持续天数
    avg_return: float     # 平均收益
    confidence: float     # 置信度

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_industry": self.from_industry,
            "to_industry": self.to_industry,
            "frequency": self.frequency,
            "avg_duration_days": self.avg_duration_days,
            "avg_return": self.avg_return,
            "confidence": self.confidence,
        }


@dataclass
class CycleIndustryPerformance:
    """经济周期下的行业表现"""
    cycle: EconomicCycle
    top_industries: list[str]
    bottom_industries: list[str]
    recommended_sectors: list[str]
    avoid_sectors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle": self.cycle.value,
            "top_industries": self.top_industries,
            "bottom_industries": self.bottom_industries,
            "recommended_sectors": self.recommended_sectors,
            "avoid_sectors": self.avoid_sectors,
        }


@dataclass
class RotationAnalysisResult:
    """轮动分析结果"""
    analysis_date: datetime
    current_cycle: EconomicCycle
    momentum_rankings: list[IndustryMomentum] = field(default_factory=list)
    rotation_patterns: list[RotationPattern] = field(default_factory=list)
    cycle_performance: CycleIndustryPerformance | None = None
    leading_industries: list[str] = field(default_factory=list)
    lagging_industries: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "current_cycle": self.current_cycle.value,
            "momentum_rankings": [m.to_dict() for m in self.momentum_rankings],
            "rotation_patterns": [p.to_dict() for p in self.rotation_patterns],
            "cycle_performance": self.cycle_performance.to_dict() if self.cycle_performance else None,
            "leading_industries": self.leading_industries,
            "lagging_industries": self.lagging_industries,
        }


class RotationAnalysisService:
    """行业轮动分析服务"""

    # 行业列表
    INDUSTRIES = [
        "银行", "保险", "券商", "房地产",
        "白酒", "医药", "家电", "汽车",
        "电子", "计算机", "通信", "传媒",
        "钢铁", "煤炭", "有色", "化工",
        "电力", "公用事业", "交通运输", "建筑",
    ]

    # 经济周期对应的优势行业
    CYCLE_INDUSTRIES = {
        EconomicCycle.RECOVERY: {
            "top": ["券商", "房地产", "建筑", "有色"],
            "bottom": ["公用事业", "电力"],
        },
        EconomicCycle.EXPANSION: {
            "top": ["白酒", "家电", "汽车", "电子"],
            "bottom": ["银行", "保险"],
        },
        EconomicCycle.PEAK: {
            "top": ["煤炭", "钢铁", "化工", "交通运输"],
            "bottom": ["房地产", "汽车"],
        },
        EconomicCycle.CONTRACTION: {
            "top": ["医药", "公用事业", "电力"],
            "bottom": ["有色", "钢铁", "化工"],
        },
        EconomicCycle.TROUGH: {
            "top": ["银行", "保险", "公用事业"],
            "bottom": ["券商", "计算机"],
        },
    }

    def __init__(self):
        self._cache: dict[str, Any] = {}

    async def analyze_rotation(
        self,
        lookback_months: int = 6,
    ) -> RotationAnalysisResult:
        """
        行业轮动分析

        Args:
            lookback_months: 回看月数
        """
        analysis_date = datetime.now()

        # 判断当前经济周期
        current_cycle = await self._detect_economic_cycle()

        # 计算各行业动量
        momentum_list = await self._calculate_industry_momentum()

        # 发现轮动规律
        rotation_patterns = await self._discover_rotation_patterns(lookback_months)

        # 获取周期行业表现
        cycle_performance = self._get_cycle_performance(current_cycle)

        # 识别领先/滞后行业
        leading = [m.industry for m in momentum_list[:5]]
        lagging = [m.industry for m in momentum_list[-5:]]

        return RotationAnalysisResult(
            analysis_date=analysis_date,
            current_cycle=current_cycle,
            momentum_rankings=momentum_list,
            rotation_patterns=rotation_patterns,
            cycle_performance=cycle_performance,
            leading_industries=leading,
            lagging_industries=lagging,
        )

    async def get_industry_momentum(self, industry: str) -> IndustryMomentum | None:
        """获取单个行业动量"""
        momentum_list = await self._calculate_industry_momentum()
        for m in momentum_list:
            if m.industry == industry:
                return m
        return None

    async def get_current_cycle(self) -> EconomicCycle:
        """获取当前经济周期判断"""
        return await self._detect_economic_cycle()

    async def get_rotation_suggestion(self) -> dict[str, Any]:
        """获取轮动建议"""
        result = await self.analyze_rotation()

        return {
            "current_cycle": result.current_cycle.value,
            "recommended_industries": result.leading_industries[:3],
            "avoid_industries": result.lagging_industries[:3],
            "rotation_patterns": [p.to_dict() for p in result.rotation_patterns[:3]],
            "analysis_date": result.analysis_date.isoformat(),
        }

    async def _detect_economic_cycle(self) -> EconomicCycle:
        """检测当前经济周期"""
        import random

        # Mock: 随机返回一个周期阶段
        # 实际应基于 PMI、GDP、利率等宏观指标判断
        return random.choice(list(EconomicCycle))

    async def _calculate_industry_momentum(self) -> list[IndustryMomentum]:
        """计算各行业动量"""
        import random

        momentum_list = []
        for industry in self.INDUSTRIES:
            # Mock 数据
            return_1w = random.uniform(-5, 8)
            return_1m = random.uniform(-10, 15)
            return_3m = random.uniform(-15, 25)
            return_6m = random.uniform(-20, 40)

            # 动量得分 = 加权平均
            momentum_score = (
                return_1w * 0.1 +
                return_1m * 0.2 +
                return_3m * 0.3 +
                return_6m * 0.4
            )

            # 信号判断
            if momentum_score > 15:
                signal = MomentumSignal.STRONG_BUY
            elif momentum_score > 5:
                signal = MomentumSignal.BUY
            elif momentum_score > -5:
                signal = MomentumSignal.NEUTRAL
            elif momentum_score > -15:
                signal = MomentumSignal.SELL
            else:
                signal = MomentumSignal.STRONG_SELL

            momentum_list.append(IndustryMomentum(
                industry=industry,
                return_1w=round(return_1w, 2),
                return_1m=round(return_1m, 2),
                return_3m=round(return_3m, 2),
                return_6m=round(return_6m, 2),
                momentum_score=round(momentum_score, 2),
                signal=signal,
            ))

        # 按动量得分排序
        momentum_list.sort(key=lambda x: x.momentum_score, reverse=True)

        # 设置排名
        for i, m in enumerate(momentum_list):
            m.rank = i + 1

        return momentum_list

    async def _discover_rotation_patterns(
        self,
        lookback_months: int,
    ) -> list[RotationPattern]:
        """发现历史轮动规律"""
        import random

        # Mock 常见轮动模式
        patterns = [
            RotationPattern(
                from_industry="券商",
                to_industry="房地产",
                frequency=random.randint(5, 15),
                avg_duration_days=random.randint(30, 90),
                avg_return=random.uniform(10, 30),
                confidence=random.uniform(0.6, 0.85),
            ),
            RotationPattern(
                from_industry="有色",
                to_industry="煤炭",
                frequency=random.randint(5, 15),
                avg_duration_days=random.randint(20, 60),
                avg_return=random.uniform(8, 25),
                confidence=random.uniform(0.55, 0.8),
            ),
            RotationPattern(
                from_industry="银行",
                to_industry="保险",
                frequency=random.randint(8, 20),
                avg_duration_days=random.randint(15, 45),
                avg_return=random.uniform(5, 15),
                confidence=random.uniform(0.65, 0.9),
            ),
            RotationPattern(
                from_industry="电子",
                to_industry="计算机",
                frequency=random.randint(10, 25),
                avg_duration_days=random.randint(20, 50),
                avg_return=random.uniform(8, 20),
                confidence=random.uniform(0.6, 0.85),
            ),
        ]

        return sorted(patterns, key=lambda x: x.confidence, reverse=True)

    def _get_cycle_performance(self, cycle: EconomicCycle) -> CycleIndustryPerformance:
        """获取周期行业表现"""
        cycle_data = self.CYCLE_INDUSTRIES.get(cycle, {"top": [], "bottom": []})

        return CycleIndustryPerformance(
            cycle=cycle,
            top_industries=cycle_data["top"],
            bottom_industries=cycle_data["bottom"],
            recommended_sectors=cycle_data["top"][:2],
            avoid_sectors=cycle_data["bottom"][:2],
        )


# 全局单例
_rotation_analysis_service: RotationAnalysisService | None = None


def get_rotation_analysis_service() -> RotationAnalysisService:
    """获取行业轮动分析服务单例"""
    global _rotation_analysis_service
    if _rotation_analysis_service is None:
        _rotation_analysis_service = RotationAnalysisService()
    return _rotation_analysis_service
