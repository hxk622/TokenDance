# -*- coding: utf-8 -*-
"""
PeerComparisonService - 同行对比分析服务

提供：
1. 同行业公司对比
2. 关键指标横向比较
3. 竞争优势分析
4. 估值对比

使用方法：
    service = PeerComparisonService()
    result = await service.compare_peers("600519")
"""
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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
    
    def to_dict(self) -> Dict[str, Any]:
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
    peers: List[CompanyMetrics] = field(default_factory=list)
    
    # 目标公司指标
    target_metrics: Optional[CompanyMetrics] = None
    
    # 行业平均/中位数
    industry_avg: Dict[str, float] = field(default_factory=dict)
    industry_median: Dict[str, float] = field(default_factory=dict)
    
    # 排名
    rankings: Dict[str, int] = field(default_factory=dict)
    
    # 优劣势分析
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
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


class PeerComparisonService:
    """
    同行对比服务
    
    提供同行业公司的横向对比分析。
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
        self._cache: Dict[str, PeerComparisonResult] = {}
    
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
    
    async def get_industry_peers(self, symbol: str) -> List[str]:
        """获取同行业公司列表"""
        info = self.INDUSTRY_MAPPING.get(symbol)
        if not info:
            return []
        
        industry = info[1]
        
        peers = []
        for sym, (name, ind) in self.INDUSTRY_MAPPING.items():
            if ind == industry and sym != symbol:
                peers.append(sym)
        
        return peers
    
    async def compare_specific_metrics(
        self, 
        symbols: List[str],
        metrics: List[str],
    ) -> Dict[str, Dict[str, float]]:
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
    
    async def _fetch_company_metrics(self, symbol: str) -> Optional[CompanyMetrics]:
        """获取公司指标"""
        try:
            return await self._fetch_from_akshare(symbol)
        except Exception as e:
            logger.debug(f"AKShare fetch failed: {e}")
        
        return self._generate_mock_metrics(symbol)
    
    async def _fetch_from_akshare(self, symbol: str) -> Optional[CompanyMetrics]:
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
        companies: List[CompanyMetrics],
    ) -> tuple[Dict[str, float], Dict[str, float]]:
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
        peers: List[CompanyMetrics],
    ) -> Dict[str, int]:
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
        avg: Dict[str, float],
        median: Dict[str, float],
    ) -> tuple[List[str], List[str]]:
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
_peer_comparison_service: Optional[PeerComparisonService] = None


def get_peer_comparison_service() -> PeerComparisonService:
    """获取同行对比服务单例"""
    global _peer_comparison_service
    if _peer_comparison_service is None:
        _peer_comparison_service = PeerComparisonService()
    return _peer_comparison_service
