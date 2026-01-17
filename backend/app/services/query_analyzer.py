# -*- coding: utf-8 -*-
"""
查询分析器 (Query Analyzer)

功能:
- 分析查询复杂度
- 动态调整研究深度 (depth) 和广度 (breadth)
- 识别查询类型 (事实型/分析型/探索型)

智能深度控制:
- 简单事实查询: depth=1, breadth=3
- 中等分析查询: depth=2, breadth=5
- 复杂探索查询: depth=3, breadth=8
"""
import logging
import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """查询类型"""
    FACTUAL = "factual"           # 事实型: 什么是 X? X 的价格?
    ANALYTICAL = "analytical"     # 分析型: 为什么 X? X 的影响?
    COMPARATIVE = "comparative"   # 比较型: X vs Y? X 和 Y 的区别?
    EXPLORATORY = "exploratory"   # 探索型: X 的未来趋势? X 的可能性?
    PROCEDURAL = "procedural"     # 过程型: 如何做 X? X 的步骤?


class QueryComplexity(Enum):
    """查询复杂度"""
    SIMPLE = "simple"      # 简单: 单一概念, 直接答案
    MODERATE = "moderate"  # 中等: 多个概念, 需要整合
    COMPLEX = "complex"    # 复杂: 多维度, 需要深入分析


@dataclass
class ResearchConfig:
    """研究配置"""
    depth: int              # 搜索深度 (迭代轮数)
    breadth: int            # 搜索广度 (每轮查询数)
    max_sources: int        # 最大来源数
    max_iterations: int     # 最大迭代次数
    summarize_every: int    # 每 N 个来源后摘要
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "depth": self.depth,
            "breadth": self.breadth,
            "max_sources": self.max_sources,
            "max_iterations": self.max_iterations,
            "summarize_every": self.summarize_every
        }


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    query: str
    query_type: QueryType
    complexity: QueryComplexity
    keywords: List[str]
    entities: List[str]
    config: ResearchConfig
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "query_type": self.query_type.value,
            "complexity": self.complexity.value,
            "keywords": self.keywords,
            "entities": self.entities,
            "config": self.config.to_dict(),
            "reasoning": self.reasoning
        }


# 预设配置
PRESET_CONFIGS = {
    (QueryType.FACTUAL, QueryComplexity.SIMPLE): ResearchConfig(
        depth=1, breadth=3, max_sources=5, max_iterations=10, summarize_every=5
    ),
    (QueryType.FACTUAL, QueryComplexity.MODERATE): ResearchConfig(
        depth=2, breadth=4, max_sources=8, max_iterations=15, summarize_every=4
    ),
    (QueryType.FACTUAL, QueryComplexity.COMPLEX): ResearchConfig(
        depth=2, breadth=5, max_sources=10, max_iterations=20, summarize_every=3
    ),
    (QueryType.ANALYTICAL, QueryComplexity.SIMPLE): ResearchConfig(
        depth=2, breadth=4, max_sources=8, max_iterations=15, summarize_every=3
    ),
    (QueryType.ANALYTICAL, QueryComplexity.MODERATE): ResearchConfig(
        depth=3, breadth=5, max_sources=12, max_iterations=25, summarize_every=3
    ),
    (QueryType.ANALYTICAL, QueryComplexity.COMPLEX): ResearchConfig(
        depth=3, breadth=6, max_sources=15, max_iterations=30, summarize_every=3
    ),
    (QueryType.COMPARATIVE, QueryComplexity.SIMPLE): ResearchConfig(
        depth=2, breadth=4, max_sources=8, max_iterations=15, summarize_every=4
    ),
    (QueryType.COMPARATIVE, QueryComplexity.MODERATE): ResearchConfig(
        depth=2, breadth=6, max_sources=12, max_iterations=20, summarize_every=3
    ),
    (QueryType.COMPARATIVE, QueryComplexity.COMPLEX): ResearchConfig(
        depth=3, breadth=8, max_sources=15, max_iterations=30, summarize_every=3
    ),
    (QueryType.EXPLORATORY, QueryComplexity.SIMPLE): ResearchConfig(
        depth=2, breadth=5, max_sources=10, max_iterations=20, summarize_every=3
    ),
    (QueryType.EXPLORATORY, QueryComplexity.MODERATE): ResearchConfig(
        depth=3, breadth=6, max_sources=15, max_iterations=30, summarize_every=3
    ),
    (QueryType.EXPLORATORY, QueryComplexity.COMPLEX): ResearchConfig(
        depth=4, breadth=8, max_sources=20, max_iterations=40, summarize_every=3
    ),
    (QueryType.PROCEDURAL, QueryComplexity.SIMPLE): ResearchConfig(
        depth=1, breadth=3, max_sources=5, max_iterations=10, summarize_every=5
    ),
    (QueryType.PROCEDURAL, QueryComplexity.MODERATE): ResearchConfig(
        depth=2, breadth=4, max_sources=8, max_iterations=15, summarize_every=3
    ),
    (QueryType.PROCEDURAL, QueryComplexity.COMPLEX): ResearchConfig(
        depth=2, breadth=5, max_sources=10, max_iterations=20, summarize_every=3
    ),
}


class QueryAnalyzer:
    """查询分析器"""
    
    # 查询类型关键词
    FACTUAL_PATTERNS = [
        r'\b(what is|what are|who is|who are|when|where)\b',
        r'\b(定义|是什么|什么是|谁是|何时|哪里)\b',
        r'\b(price|cost|number|amount|date)\b',
        r'\b(价格|成本|数量|日期)\b',
    ]
    
    ANALYTICAL_PATTERNS = [
        r'\b(why|how come|reason|cause|effect|impact|influence)\b',
        r'\b(为什么|原因|影响|作用|效果)\b',
        r'\b(analyze|analysis|explain|understand)\b',
        r'\b(分析|解释|理解|探究)\b',
    ]
    
    COMPARATIVE_PATTERNS = [
        r'\b(vs|versus|compare|comparison|difference|better|worse)\b',
        r'\b(对比|比较|区别|差异|哪个更好)\b',
        r'\b(A or B|which one|pros and cons)\b',
        r'\b(优缺点|利弊)\b',
    ]
    
    EXPLORATORY_PATTERNS = [
        r'\b(future|trend|prediction|forecast|potential|possibility)\b',
        r'\b(未来|趋势|预测|预期|潜力|可能性)\b',
        r'\b(what if|imagine|scenario|opportunity)\b',
        r'\b(假设|情景|机会)\b',
    ]
    
    PROCEDURAL_PATTERNS = [
        r'\b(how to|steps|guide|tutorial|instructions)\b',
        r'\b(如何|怎么|步骤|指南|教程)\b',
        r'\b(process|method|approach|way to)\b',
        r'\b(过程|方法|方式|途径)\b',
    ]
    
    def __init__(self, llm=None):
        """
        Args:
            llm: LLM 实例 (可选，用于更精确的分析)
        """
        self.llm = llm
    
    def analyze(self, query: str) -> QueryAnalysis:
        """分析查询
        
        Args:
            query: 用户查询
            
        Returns:
            QueryAnalysis: 分析结果
        """
        # 1. 识别查询类型
        query_type = self._identify_query_type(query)
        
        # 2. 评估复杂度
        complexity = self._evaluate_complexity(query)
        
        # 3. 提取关键词和实体
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        
        # 4. 获取配置
        config = self._get_config(query_type, complexity)
        
        # 5. 生成推理说明
        reasoning = self._generate_reasoning(query_type, complexity, keywords)
        
        analysis = QueryAnalysis(
            query=query,
            query_type=query_type,
            complexity=complexity,
            keywords=keywords,
            entities=entities,
            config=config,
            reasoning=reasoning
        )
        
        logger.info(
            f"Query analyzed: type={query_type.value}, "
            f"complexity={complexity.value}, "
            f"config=depth={config.depth}/breadth={config.breadth}"
        )
        
        return analysis
    
    def _identify_query_type(self, query: str) -> QueryType:
        """识别查询类型"""
        query_lower = query.lower()
        
        scores = {
            QueryType.FACTUAL: 0,
            QueryType.ANALYTICAL: 0,
            QueryType.COMPARATIVE: 0,
            QueryType.EXPLORATORY: 0,
            QueryType.PROCEDURAL: 0,
        }
        
        # 匹配模式
        for pattern in self.FACTUAL_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[QueryType.FACTUAL] += 1
        
        for pattern in self.ANALYTICAL_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[QueryType.ANALYTICAL] += 1
        
        for pattern in self.COMPARATIVE_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[QueryType.COMPARATIVE] += 1
        
        for pattern in self.EXPLORATORY_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[QueryType.EXPLORATORY] += 1
        
        for pattern in self.PROCEDURAL_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                scores[QueryType.PROCEDURAL] += 1
        
        # 返回得分最高的类型
        max_type = max(scores, key=scores.get)
        
        # 如果没有明显匹配，默认为事实型
        if scores[max_type] == 0:
            return QueryType.FACTUAL
        
        return max_type
    
    def _evaluate_complexity(self, query: str) -> QueryComplexity:
        """评估查询复杂度"""
        score = 0
        
        # 长度因素
        word_count = len(query.split())
        if word_count > 20:
            score += 2
        elif word_count > 10:
            score += 1
        
        # 多个问题
        question_marks = query.count('?') + query.count('？')
        if question_marks > 1:
            score += 2
        
        # 多个关键概念
        keywords = self._extract_keywords(query)
        if len(keywords) > 5:
            score += 2
        elif len(keywords) > 3:
            score += 1
        
        # 包含限定条件
        if re.search(r'\b(and|or|but|while|although)\b', query.lower()):
            score += 1
        if re.search(r'\b(在.*条件下|考虑.*因素|包括|不包括)\b', query):
            score += 1
        
        # 时间范围
        if re.search(r'\b(2020|2021|2022|2023|2024|2025|2026|过去|近年|最近)\b', query):
            score += 1
        
        # 判断复杂度
        if score >= 5:
            return QueryComplexity.COMPLEX
        elif score >= 2:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 移除停用词
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'what', 'which', 'who', 'how', 'why', 'when', 'where',
            'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
            'and', 'or', 'but', 'if', 'then', 'this', 'that',
            '的', '是', '在', '了', '和', '与', '或', '但', '什么', '如何',
            '这个', '那个', '哪个', '为什么', '怎么'
        }
        
        words = re.findall(r'\w+', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return list(dict.fromkeys(keywords))[:10]  # 去重，最多10个
    
    def _extract_entities(self, query: str) -> List[str]:
        """提取实体 (简单规则)"""
        entities = []
        
        # 大写开头的词 (英文)
        entities.extend(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query))
        
        # 引号中的内容
        entities.extend(re.findall(r'["\']([^"\']+)["\']', query))
        entities.extend(re.findall(r'[「」『』]([^「」『』]+)[「」『』]', query))
        
        # 专有名词模式 (如: OpenAI, GPT-4)
        entities.extend(re.findall(r'\b[A-Z][a-zA-Z]*-?\d*\b', query))
        
        return list(dict.fromkeys(entities))[:5]
    
    def _get_config(self, query_type: QueryType, complexity: QueryComplexity) -> ResearchConfig:
        """获取配置"""
        key = (query_type, complexity)
        
        if key in PRESET_CONFIGS:
            return PRESET_CONFIGS[key]
        
        # 默认配置
        return ResearchConfig(
            depth=2,
            breadth=5,
            max_sources=10,
            max_iterations=20,
            summarize_every=3
        )
    
    def _generate_reasoning(
        self,
        query_type: QueryType,
        complexity: QueryComplexity,
        keywords: List[str]
    ) -> str:
        """生成推理说明"""
        type_desc = {
            QueryType.FACTUAL: "factual query requiring direct answers",
            QueryType.ANALYTICAL: "analytical query requiring deeper investigation",
            QueryType.COMPARATIVE: "comparative query requiring multiple perspectives",
            QueryType.EXPLORATORY: "exploratory query requiring broad research",
            QueryType.PROCEDURAL: "procedural query requiring step-by-step information",
        }
        
        complexity_desc = {
            QueryComplexity.SIMPLE: "simple (single concept)",
            QueryComplexity.MODERATE: "moderate (multiple concepts)",
            QueryComplexity.COMPLEX: "complex (multi-dimensional)",
        }
        
        return (
            f"Identified as {type_desc[query_type]}. "
            f"Complexity assessed as {complexity_desc[complexity]}. "
            f"Key concepts: {', '.join(keywords[:5])}."
        )


# 便捷函数
def analyze_query(query: str) -> QueryAnalysis:
    """分析查询并返回配置"""
    analyzer = QueryAnalyzer()
    return analyzer.analyze(query)


def get_adaptive_config(query: str) -> ResearchConfig:
    """获取自适应研究配置"""
    analysis = analyze_query(query)
    return analysis.config
