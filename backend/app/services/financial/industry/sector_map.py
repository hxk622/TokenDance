# -*- coding: utf-8 -*-
"""
SectorMapService - 板块地图服务

提供：
1. 板块分类体系
2. 板块层级结构
3. 板块涨跌热力图
4. 板块资金流向
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SectorLevel(str, Enum):
    """板块层级"""
    SECTOR = "sector"           # 大类板块
    INDUSTRY = "industry"       # 行业
    SUB_INDUSTRY = "sub_industry"  # 细分行业
    CONCEPT = "concept"         # 概念板块


class HeatLevel(str, Enum):
    """热度级别"""
    HOT = "hot"           # 热门 (涨幅 > 3%)
    WARM = "warm"         # 偏热 (涨幅 1-3%)
    NEUTRAL = "neutral"   # 中性 (涨幅 -1% ~ 1%)
    COOL = "cool"         # 偏冷 (跌幅 1-3%)
    COLD = "cold"         # 冷门 (跌幅 > 3%)


@dataclass
class SectorNode:
    """板块节点"""
    code: str
    name: str
    level: SectorLevel
    parent_code: Optional[str] = None
    children: List["SectorNode"] = field(default_factory=list)
    stock_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "level": self.level.value,
            "parent_code": self.parent_code,
            "children": [c.to_dict() for c in self.children],
            "stock_count": self.stock_count,
        }


@dataclass
class SectorHeatData:
    """板块热力数据"""
    code: str
    name: str
    level: SectorLevel
    change_pct: float       # 涨跌幅
    heat_level: HeatLevel
    volume: float           # 成交额 (亿)
    turnover_rate: float    # 换手率
    leading_stock: str      # 领涨股
    leading_change: float   # 领涨股涨幅
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "level": self.level.value,
            "change_pct": self.change_pct,
            "heat_level": self.heat_level.value,
            "volume": self.volume,
            "turnover_rate": self.turnover_rate,
            "leading_stock": self.leading_stock,
            "leading_change": self.leading_change,
        }


@dataclass
class SectorFlowData:
    """板块资金流向"""
    code: str
    name: str
    net_inflow: float       # 净流入 (亿)
    main_inflow: float      # 主力净流入
    retail_inflow: float    # 散户净流入
    super_large_inflow: float  # 超大单净流入
    large_inflow: float     # 大单净流入
    medium_inflow: float    # 中单净流入
    small_inflow: float     # 小单净流入
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "net_inflow": self.net_inflow,
            "main_inflow": self.main_inflow,
            "retail_inflow": self.retail_inflow,
            "super_large_inflow": self.super_large_inflow,
            "large_inflow": self.large_inflow,
            "medium_inflow": self.medium_inflow,
            "small_inflow": self.small_inflow,
        }


@dataclass
class SectorMapResult:
    """板块地图结果"""
    update_time: datetime
    sector_tree: List[SectorNode] = field(default_factory=list)
    heat_map: List[SectorHeatData] = field(default_factory=list)
    flow_ranking: List[SectorFlowData] = field(default_factory=list)
    hot_concepts: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "update_time": self.update_time.isoformat(),
            "sector_tree": [s.to_dict() for s in self.sector_tree],
            "heat_map": [h.to_dict() for h in self.heat_map],
            "flow_ranking": [f.to_dict() for f in self.flow_ranking],
            "hot_concepts": self.hot_concepts,
        }


class SectorMapService:
    """板块地图服务"""
    
    # 板块分类体系
    SECTOR_HIERARCHY = {
        "金融": ["银行", "保险", "券商", "多元金融"],
        "消费": ["白酒", "食品饮料", "家电", "汽车", "零售"],
        "科技": ["电子", "计算机", "通信", "传媒"],
        "周期": ["钢铁", "煤炭", "有色", "化工", "建材"],
        "医药": ["化学制药", "中药", "医疗器械", "医疗服务"],
        "公用": ["电力", "燃气", "环保", "交通运输"],
        "地产": ["房地产", "建筑", "建筑装饰"],
    }
    
    # 概念板块
    CONCEPT_SECTORS = [
        "人工智能", "新能源汽车", "光伏", "储能",
        "芯片", "5G", "大数据", "云计算",
        "元宇宙", "ChatGPT", "机器人", "国产替代",
    ]
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    async def get_sector_map(self) -> SectorMapResult:
        """获取完整板块地图"""
        update_time = datetime.now()
        
        # 构建板块树
        sector_tree = self._build_sector_tree()
        
        # 获取热力图数据
        heat_map = await self._get_heat_map()
        
        # 获取资金流向排名
        flow_ranking = await self._get_flow_ranking()
        
        # 获取热门概念
        hot_concepts = await self._get_hot_concepts()
        
        return SectorMapResult(
            update_time=update_time,
            sector_tree=sector_tree,
            heat_map=heat_map,
            flow_ranking=flow_ranking,
            hot_concepts=hot_concepts,
        )
    
    async def get_sector_heat(
        self,
        level: SectorLevel = SectorLevel.INDUSTRY,
        top_n: int = 20,
    ) -> List[SectorHeatData]:
        """获取板块热力数据"""
        heat_map = await self._get_heat_map()
        filtered = [h for h in heat_map if h.level == level]
        return sorted(filtered, key=lambda x: x.change_pct, reverse=True)[:top_n]
    
    async def get_sector_flow(
        self,
        level: SectorLevel = SectorLevel.INDUSTRY,
        top_n: int = 20,
    ) -> List[SectorFlowData]:
        """获取板块资金流向"""
        flow_data = await self._get_flow_ranking()
        return flow_data[:top_n]
    
    async def get_concept_sectors(self) -> List[SectorHeatData]:
        """获取概念板块行情"""
        return await self._get_concept_heat()
    
    async def find_sector_by_stock(self, symbol: str) -> Dict[str, Any]:
        """根据股票查找所属板块"""
        # Mock 数据
        return {
            "symbol": symbol,
            "sector": "消费",
            "industry": "白酒",
            "sub_industry": "高端白酒",
            "concepts": ["消费升级", "国企改革"],
        }
    
    def _build_sector_tree(self) -> List[SectorNode]:
        """构建板块树"""
        import random
        
        tree = []
        for sector_name, industries in self.SECTOR_HIERARCHY.items():
            sector_node = SectorNode(
                code=f"S_{sector_name}",
                name=sector_name,
                level=SectorLevel.SECTOR,
                stock_count=random.randint(100, 500),
            )
            
            for industry in industries:
                industry_node = SectorNode(
                    code=f"I_{industry}",
                    name=industry,
                    level=SectorLevel.INDUSTRY,
                    parent_code=sector_node.code,
                    stock_count=random.randint(20, 100),
                )
                sector_node.children.append(industry_node)
            
            tree.append(sector_node)
        
        return tree
    
    async def _get_heat_map(self) -> List[SectorHeatData]:
        """获取热力图数据"""
        import random
        
        heat_map = []
        for sector_name, industries in self.SECTOR_HIERARCHY.items():
            for industry in industries:
                change_pct = random.uniform(-5, 8)
                
                # 确定热度级别
                if change_pct > 3:
                    heat_level = HeatLevel.HOT
                elif change_pct > 1:
                    heat_level = HeatLevel.WARM
                elif change_pct > -1:
                    heat_level = HeatLevel.NEUTRAL
                elif change_pct > -3:
                    heat_level = HeatLevel.COOL
                else:
                    heat_level = HeatLevel.COLD
                
                heat_map.append(SectorHeatData(
                    code=f"I_{industry}",
                    name=industry,
                    level=SectorLevel.INDUSTRY,
                    change_pct=round(change_pct, 2),
                    heat_level=heat_level,
                    volume=round(random.uniform(50, 500), 2),
                    turnover_rate=round(random.uniform(1, 8), 2),
                    leading_stock=f"{industry}龙头",
                    leading_change=round(change_pct + random.uniform(1, 5), 2),
                ))
        
        return sorted(heat_map, key=lambda x: x.change_pct, reverse=True)
    
    async def _get_flow_ranking(self) -> List[SectorFlowData]:
        """获取资金流向排名"""
        import random
        
        flow_data = []
        all_industries = []
        for industries in self.SECTOR_HIERARCHY.values():
            all_industries.extend(industries)
        
        for industry in all_industries:
            net_inflow = random.uniform(-50, 80)
            main_ratio = random.uniform(0.4, 0.7)
            
            flow_data.append(SectorFlowData(
                code=f"I_{industry}",
                name=industry,
                net_inflow=round(net_inflow, 2),
                main_inflow=round(net_inflow * main_ratio, 2),
                retail_inflow=round(net_inflow * (1 - main_ratio), 2),
                super_large_inflow=round(net_inflow * 0.3, 2),
                large_inflow=round(net_inflow * 0.25, 2),
                medium_inflow=round(net_inflow * 0.25, 2),
                small_inflow=round(net_inflow * 0.2, 2),
            ))
        
        return sorted(flow_data, key=lambda x: x.net_inflow, reverse=True)
    
    async def _get_hot_concepts(self) -> List[str]:
        """获取热门概念"""
        import random
        
        # 随机选择几个热门概念
        return random.sample(self.CONCEPT_SECTORS, min(5, len(self.CONCEPT_SECTORS)))
    
    async def _get_concept_heat(self) -> List[SectorHeatData]:
        """获取概念板块热力数据"""
        import random
        
        concept_heat = []
        for concept in self.CONCEPT_SECTORS:
            change_pct = random.uniform(-6, 10)
            
            if change_pct > 3:
                heat_level = HeatLevel.HOT
            elif change_pct > 1:
                heat_level = HeatLevel.WARM
            elif change_pct > -1:
                heat_level = HeatLevel.NEUTRAL
            elif change_pct > -3:
                heat_level = HeatLevel.COOL
            else:
                heat_level = HeatLevel.COLD
            
            concept_heat.append(SectorHeatData(
                code=f"C_{concept}",
                name=concept,
                level=SectorLevel.CONCEPT,
                change_pct=round(change_pct, 2),
                heat_level=heat_level,
                volume=round(random.uniform(100, 800), 2),
                turnover_rate=round(random.uniform(2, 10), 2),
                leading_stock=f"{concept}龙头",
                leading_change=round(change_pct + random.uniform(2, 8), 2),
            ))
        
        return sorted(concept_heat, key=lambda x: x.change_pct, reverse=True)


# 全局单例
_sector_map_service: Optional[SectorMapService] = None


def get_sector_map_service() -> SectorMapService:
    """获取板块地图服务单例"""
    global _sector_map_service
    if _sector_map_service is None:
        _sector_map_service = SectorMapService()
    return _sector_map_service
