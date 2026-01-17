# -*- coding: utf-8 -*-
"""
SupplyChainMapService - 产业链图谱服务

提供：
1. 产业链上下游映射
2. 供应链关系图
3. 产业链价值分析
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ChainPosition(str, Enum):
    """产业链位置"""
    UPSTREAM = "upstream"       # 上游
    MIDSTREAM = "midstream"     # 中游
    DOWNSTREAM = "downstream"   # 下游


class NodeType(str, Enum):
    """节点类型"""
    COMPANY = "company"
    INDUSTRY = "industry"
    PRODUCT = "product"


@dataclass
class SupplyChainNode:
    """产业链节点"""
    node_id: str
    name: str
    node_type: NodeType
    position: ChainPosition
    symbol: Optional[str] = None  # 股票代码（如果是上市公司）
    market_share: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "node_type": self.node_type.value,
            "position": self.position.value,
            "symbol": self.symbol,
            "market_share": self.market_share,
        }


@dataclass
class SupplyChainLink:
    """产业链关系"""
    source_id: str
    target_id: str
    relation_type: str  # 供应、采购、合作等
    strength: float = 0.5  # 关系强度 0-1
    value: Optional[float] = None  # 交易金额（如有）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "strength": self.strength,
            "value": self.value,
        }


@dataclass
class ChainValueAnalysis:
    """产业链价值分析"""
    position: ChainPosition
    avg_gross_margin: float
    avg_net_margin: float
    bargaining_power: str  # 议价能力
    growth_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position.value,
            "avg_gross_margin": self.avg_gross_margin,
            "avg_net_margin": self.avg_net_margin,
            "bargaining_power": self.bargaining_power,
            "growth_rate": self.growth_rate,
        }


@dataclass
class SupplyChainMapResult:
    """产业链图谱结果"""
    industry: str
    analysis_date: datetime
    nodes: List[SupplyChainNode] = field(default_factory=list)
    links: List[SupplyChainLink] = field(default_factory=list)
    value_analysis: List[ChainValueAnalysis] = field(default_factory=list)
    
    # 关键信息
    key_players: List[str] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "analysis_date": self.analysis_date.isoformat(),
            "nodes": [n.to_dict() for n in self.nodes],
            "links": [l.to_dict() for l in self.links],
            "value_analysis": [v.to_dict() for v in self.value_analysis],
            "key_players": self.key_players,
            "bottlenecks": self.bottlenecks,
        }


class SupplyChainMapService:
    """产业链图谱服务"""
    
    # 产业链数据
    CHAIN_DATA = {
        "新能源汽车": {
            "upstream": [
                ("锂矿", ["天齐锂业", "赣锋锂业"]),
                ("钴镍", ["华友钴业", "格林美"]),
                ("正极材料", ["容百科技", "当升科技"]),
                ("负极材料", ["璞泰来", "杉杉股份"]),
            ],
            "midstream": [
                ("电池", ["宁德时代", "比亚迪", "国轩高科"]),
                ("电机", ["汇川技术", "大洋电机"]),
                ("电控", ["英威腾", "汇川技术"]),
            ],
            "downstream": [
                ("整车", ["比亚迪", "蔚来", "理想", "小鹏"]),
                ("充电桩", ["特锐德", "星星充电"]),
            ],
        },
        "半导体": {
            "upstream": [
                ("EDA工具", ["新思科技", "Cadence"]),
                ("设备", ["北方华创", "中微公司"]),
                ("材料", ["沪硅产业", "南大光电"]),
            ],
            "midstream": [
                ("制造", ["中芯国际", "华虹半导体"]),
                ("封测", ["长电科技", "通富微电"]),
            ],
            "downstream": [
                ("设计", ["韦尔股份", "卓胜微"]),
                ("应用", ["消费电子", "汽车电子"]),
            ],
        },
    }
    
    def __init__(self):
        self._cache: Dict[str, SupplyChainMapResult] = {}
    
    async def get_supply_chain_map(
        self,
        industry: str,
    ) -> SupplyChainMapResult:
        """获取产业链图谱"""
        if industry in self._cache:
            return self._cache[industry]
        
        try:
            # 构建节点和关系
            nodes, links = self._build_chain_graph(industry)
            
            # 价值分析
            value_analysis = self._analyze_chain_value(industry)
            
            # 识别关键玩家和瓶颈
            key_players = self._identify_key_players(nodes)
            bottlenecks = self._identify_bottlenecks(industry)
            
            result = SupplyChainMapResult(
                industry=industry,
                analysis_date=datetime.now(),
                nodes=nodes,
                links=links,
                value_analysis=value_analysis,
                key_players=key_players,
                bottlenecks=bottlenecks,
            )
            
            self._cache[industry] = result
            return result
            
        except Exception as e:
            logger.error(f"Failed to get supply chain map for {industry}: {e}")
            return SupplyChainMapResult(
                industry=industry,
                analysis_date=datetime.now(),
            )
    
    async def get_company_position(
        self,
        symbol: str,
    ) -> Dict[str, Any]:
        """获取公司在产业链中的位置"""
        # Mock 数据
        return {
            "symbol": symbol,
            "industry": "新能源汽车",
            "position": ChainPosition.MIDSTREAM.value,
            "segment": "电池",
            "upstream_deps": ["正极材料", "负极材料", "电解液"],
            "downstream_customers": ["整车厂", "储能"],
        }
    
    def _build_chain_graph(
        self,
        industry: str,
    ) -> tuple[List[SupplyChainNode], List[SupplyChainLink]]:
        """构建产业链图"""
        import random
        
        chain_data = self.CHAIN_DATA.get(industry, {})
        nodes = []
        links = []
        node_id_counter = 0
        
        position_map = {
            "upstream": ChainPosition.UPSTREAM,
            "midstream": ChainPosition.MIDSTREAM,
            "downstream": ChainPosition.DOWNSTREAM,
        }
        
        prev_position_nodes = []
        
        for position_key, position_enum in position_map.items():
            segments = chain_data.get(position_key, [])
            current_position_nodes = []
            
            for segment_name, companies in segments:
                # 添加行业节点
                industry_node_id = f"ind_{node_id_counter}"
                node_id_counter += 1
                nodes.append(SupplyChainNode(
                    node_id=industry_node_id,
                    name=segment_name,
                    node_type=NodeType.INDUSTRY,
                    position=position_enum,
                ))
                current_position_nodes.append(industry_node_id)
                
                # 添加公司节点
                for company in companies:
                    company_node_id = f"com_{node_id_counter}"
                    node_id_counter += 1
                    nodes.append(SupplyChainNode(
                        node_id=company_node_id,
                        name=company,
                        node_type=NodeType.COMPANY,
                        position=position_enum,
                        market_share=round(random.uniform(5, 40), 1),
                    ))
                    
                    # 公司到行业的关系
                    links.append(SupplyChainLink(
                        source_id=company_node_id,
                        target_id=industry_node_id,
                        relation_type="belongs_to",
                        strength=1.0,
                    ))
            
            # 上下游关系
            for prev_node in prev_position_nodes:
                for curr_node in current_position_nodes:
                    links.append(SupplyChainLink(
                        source_id=prev_node,
                        target_id=curr_node,
                        relation_type="supplies",
                        strength=round(random.uniform(0.3, 0.9), 2),
                    ))
            
            prev_position_nodes = current_position_nodes
        
        return nodes, links
    
    def _analyze_chain_value(self, industry: str) -> List[ChainValueAnalysis]:
        """分析产业链价值分布"""
        import random
        
        return [
            ChainValueAnalysis(
                position=ChainPosition.UPSTREAM,
                avg_gross_margin=round(random.uniform(15, 35), 1),
                avg_net_margin=round(random.uniform(5, 15), 1),
                bargaining_power="中等",
                growth_rate=round(random.uniform(10, 30), 1),
            ),
            ChainValueAnalysis(
                position=ChainPosition.MIDSTREAM,
                avg_gross_margin=round(random.uniform(20, 40), 1),
                avg_net_margin=round(random.uniform(8, 20), 1),
                bargaining_power="较强",
                growth_rate=round(random.uniform(15, 40), 1),
            ),
            ChainValueAnalysis(
                position=ChainPosition.DOWNSTREAM,
                avg_gross_margin=round(random.uniform(10, 25), 1),
                avg_net_margin=round(random.uniform(3, 12), 1),
                bargaining_power="中等偏弱",
                growth_rate=round(random.uniform(20, 50), 1),
            ),
        ]
    
    def _identify_key_players(self, nodes: List[SupplyChainNode]) -> List[str]:
        """识别关键玩家"""
        companies = [n for n in nodes if n.node_type == NodeType.COMPANY]
        companies.sort(key=lambda x: x.market_share or 0, reverse=True)
        return [c.name for c in companies[:5]]
    
    def _identify_bottlenecks(self, industry: str) -> List[str]:
        """识别产业链瓶颈"""
        bottlenecks_map = {
            "新能源汽车": ["锂资源供应", "高端芯片", "充电基础设施"],
            "半导体": ["光刻机", "EDA工具", "先进制程产能"],
        }
        return bottlenecks_map.get(industry, ["数据不足"])


# 全局单例
_supply_chain_map_service: Optional[SupplyChainMapService] = None


def get_supply_chain_map_service() -> SupplyChainMapService:
    """获取产业链图谱服务单例"""
    global _supply_chain_map_service
    if _supply_chain_map_service is None:
        _supply_chain_map_service = SupplyChainMapService()
    return _supply_chain_map_service
