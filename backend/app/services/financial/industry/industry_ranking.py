# -*- coding: utf-8 -*-
"""
IndustryRankingService - 行业内排名服务

提供：
1. 行业内公司排名
2. 多维度排名
3. 综合评分排名
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RankingMetric(str, Enum):
    """排名指标"""
    MARKET_CAP = "market_cap"
    PE = "pe"
    PB = "pb"
    ROE = "roe"
    REVENUE_GROWTH = "revenue_growth"
    PROFIT_GROWTH = "profit_growth"
    GROSS_MARGIN = "gross_margin"
    NET_MARGIN = "net_margin"
    COMPOSITE = "composite"


@dataclass
class RankingItem:
    """排名条目"""
    rank: int
    symbol: str
    name: str
    value: float
    percentile: float = 0.0  # 百分位
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "symbol": self.symbol,
            "name": self.name,
            "value": self.value,
            "percentile": self.percentile,
        }


@dataclass
class RankingResult:
    """排名结果"""
    industry: str
    metric: RankingMetric
    total_count: int
    rankings: List[RankingItem] = field(default_factory=list)
    
    # 目标公司排名 (如果指定)
    target_rank: Optional[RankingItem] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "metric": self.metric.value,
            "total_count": self.total_count,
            "rankings": [r.to_dict() for r in self.rankings],
            "target_rank": self.target_rank.to_dict() if self.target_rank else None,
        }


class IndustryRankingService:
    """行业排名服务"""
    
    # 行业公司列表
    INDUSTRY_STOCKS = {
        "白酒": [
            ("600519", "贵州茅台"), ("000858", "五粮液"), ("000568", "泸州老窖"),
            ("600809", "山西汾酒"), ("002304", "洋河股份"), ("000596", "古井贡酒"),
        ],
        "银行": [
            ("601398", "工商银行"), ("601939", "建设银行"), ("600036", "招商银行"),
            ("601166", "兴业银行"), ("000001", "平安银行"), ("601288", "农业银行"),
        ],
        "家电": [
            ("000333", "美的集团"), ("000651", "格力电器"), ("600690", "海尔智家"),
        ],
    }
    
    def __init__(self):
        self._cache: Dict[str, RankingResult] = {}
    
    async def get_industry_ranking(
        self,
        industry: str,
        metric: RankingMetric = RankingMetric.MARKET_CAP,
        target_symbol: Optional[str] = None,
    ) -> RankingResult:
        """
        获取行业排名
        
        Args:
            industry: 行业名称
            metric: 排名指标
            target_symbol: 关注的目标股票
        """
        cache_key = f"{industry}:{metric.value}"
        
        if cache_key in self._cache:
            result = self._cache[cache_key]
            if target_symbol:
                result.target_rank = self._find_target_rank(result.rankings, target_symbol)
            return result
        
        try:
            result = await self._compute_ranking(industry, metric)
            self._cache[cache_key] = result
            
            if target_symbol:
                result.target_rank = self._find_target_rank(result.rankings, target_symbol)
            
            return result
        except Exception as e:
            logger.error(f"Failed to get ranking: {e}")
            return RankingResult(industry=industry, metric=metric, total_count=0)
    
    async def get_top_companies(
        self,
        industry: str,
        metric: RankingMetric,
        top_n: int = 10,
    ) -> List[RankingItem]:
        """获取行业前 N 名"""
        result = await self.get_industry_ranking(industry, metric)
        return result.rankings[:top_n]
    
    async def get_composite_ranking(
        self,
        industry: str,
        weights: Optional[Dict[str, float]] = None,
    ) -> RankingResult:
        """
        综合评分排名
        
        Args:
            industry: 行业
            weights: 各指标权重，如 {"roe": 0.3, "revenue_growth": 0.2, ...}
        """
        if weights is None:
            weights = {
                "roe": 0.25,
                "revenue_growth": 0.2,
                "gross_margin": 0.2,
                "market_cap": 0.15,
                "pe": 0.1,
                "debt_ratio": 0.1,
            }
        
        stocks = self.INDUSTRY_STOCKS.get(industry, [])
        if not stocks:
            return RankingResult(industry=industry, metric=RankingMetric.COMPOSITE, total_count=0)
        
        # 计算综合得分
        scores = []
        for symbol, name in stocks:
            score = await self._calculate_composite_score(symbol, weights)
            scores.append((symbol, name, score))
        
        # 排序
        scores.sort(key=lambda x: x[2], reverse=True)
        
        rankings = []
        for i, (symbol, name, score) in enumerate(scores):
            rankings.append(RankingItem(
                rank=i + 1,
                symbol=symbol,
                name=name,
                value=round(score, 2),
                percentile=(len(scores) - i) / len(scores) * 100,
            ))
        
        return RankingResult(
            industry=industry,
            metric=RankingMetric.COMPOSITE,
            total_count=len(rankings),
            rankings=rankings,
        )
    
    async def _compute_ranking(
        self,
        industry: str,
        metric: RankingMetric,
    ) -> RankingResult:
        """计算排名"""
        stocks = self.INDUSTRY_STOCKS.get(industry, [])
        if not stocks:
            return RankingResult(industry=industry, metric=metric, total_count=0)
        
        # 获取各公司指标值
        values = []
        for symbol, name in stocks:
            value = await self._get_metric_value(symbol, metric)
            values.append((symbol, name, value))
        
        # 排序 (市值、ROE、毛利率等越高越好；PE 越低越好)
        reverse = metric not in [RankingMetric.PE, RankingMetric.PB]
        values.sort(key=lambda x: x[2] if x[2] is not None else float('-inf'), reverse=reverse)
        
        rankings = []
        for i, (symbol, name, value) in enumerate(values):
            if value is not None:
                rankings.append(RankingItem(
                    rank=i + 1,
                    symbol=symbol,
                    name=name,
                    value=round(value, 2),
                    percentile=(len(values) - i) / len(values) * 100,
                ))
        
        return RankingResult(
            industry=industry,
            metric=metric,
            total_count=len(rankings),
            rankings=rankings,
        )
    
    async def _get_metric_value(self, symbol: str, metric: RankingMetric) -> Optional[float]:
        """获取指标值"""
        import random
        
        # Mock 数据
        mock_values = {
            RankingMetric.MARKET_CAP: random.uniform(100, 20000),
            RankingMetric.PE: random.uniform(10, 80),
            RankingMetric.PB: random.uniform(1, 15),
            RankingMetric.ROE: random.uniform(5, 35),
            RankingMetric.REVENUE_GROWTH: random.uniform(-10, 40),
            RankingMetric.PROFIT_GROWTH: random.uniform(-20, 60),
            RankingMetric.GROSS_MARGIN: random.uniform(20, 70),
            RankingMetric.NET_MARGIN: random.uniform(5, 35),
        }
        
        return mock_values.get(metric, 0)
    
    async def _calculate_composite_score(
        self,
        symbol: str,
        weights: Dict[str, float],
    ) -> float:
        """计算综合得分"""
        import random
        
        # Mock 各项得分 (0-100)
        score = 0
        for metric, weight in weights.items():
            metric_score = random.uniform(40, 95)
            score += metric_score * weight
        
        return score
    
    def _find_target_rank(
        self,
        rankings: List[RankingItem],
        target_symbol: str,
    ) -> Optional[RankingItem]:
        """查找目标股票排名"""
        for item in rankings:
            if item.symbol == target_symbol:
                return item
        return None


# 全局单例
_industry_ranking_service: Optional[IndustryRankingService] = None


def get_industry_ranking_service() -> IndustryRankingService:
    """获取行业排名服务单例"""
    global _industry_ranking_service
    if _industry_ranking_service is None:
        _industry_ranking_service = IndustryRankingService()
    return _industry_ranking_service
