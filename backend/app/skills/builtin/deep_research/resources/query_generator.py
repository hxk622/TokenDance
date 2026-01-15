"""
查询生成策略脚本

根据主题自动生成多角度搜索查询，确保覆盖各个维度。

用法：
    python query_generator.py "AI Agent" deep
    python query_generator.py "区块链" shallow

输出：
    JSON 格式的查询列表
"""

import json
import sys
from typing import List


def generate_queries(topic: str, depth: str = "deep", language: str = "both") -> List[str]:
    """根据主题生成多角度搜索查询
    
    Args:
        topic: 研究主题
        depth: 搜索深度 ("shallow" / "deep")
        language: 语言 ("en" / "zh" / "both")
        
    Returns:
        查询列表
    """
    queries = []
    
    if depth == "shallow":
        # 浅度搜索：只搜概述
        if language in ("en", "both"):
            queries.append(f"{topic} overview introduction")
        if language in ("zh", "both"):
            queries.append(f"{topic} 概述 介绍")
        return queries
    
    # 深度搜索：多维度拆解
    query_templates = {
        "en": [
            "{topic} overview introduction what is",
            "{topic} market size revenue 2024",
            "{topic} key players companies leaders",
            "{topic} technology architecture how it works",
            "{topic} trends predictions 2024 2025",
            "{topic} challenges problems limitations",
            "{topic} use cases applications examples",
            "{topic} vs comparison alternatives",
        ],
        "zh": [
            "{topic} 概述 是什么 介绍",
            "{topic} 市场规模 市场份额 2024",
            "{topic} 主要厂商 头部企业 公司",
            "{topic} 技术架构 原理 实现",
            "{topic} 发展趋势 前景 预测",
            "{topic} 挑战 问题 局限性",
            "{topic} 应用场景 案例 实践",
            "{topic} 对比 比较 区别",
        ],
    }
    
    if language in ("en", "both"):
        for template in query_templates["en"]:
            queries.append(template.format(topic=topic))
    
    if language in ("zh", "both"):
        for template in query_templates["zh"]:
            queries.append(template.format(topic=topic))
    
    return queries


def generate_followup_queries(topic: str, aspect: str, language: str = "both") -> List[str]:
    """根据特定方面生成深入查询
    
    Args:
        topic: 研究主题
        aspect: 特定方面 (e.g., "技术实现", "市场竞争")
        language: 语言
        
    Returns:
        查询列表
    """
    queries = []
    
    if language in ("en", "both"):
        queries.extend([
            f"{topic} {aspect} detailed analysis",
            f"{topic} {aspect} research paper",
            f"{topic} {aspect} expert opinion",
        ])
    
    if language in ("zh", "both"):
        queries.extend([
            f"{topic} {aspect} 深度分析",
            f"{topic} {aspect} 研究报告",
            f"{topic} {aspect} 专家观点",
        ])
    
    return queries


if __name__ == "__main__":
    # 命令行接口
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python query_generator.py <topic> [depth] [language]",
            "example": "python query_generator.py 'AI Agent' deep both"
        }))
        sys.exit(1)
    
    topic = sys.argv[1]
    depth = sys.argv[2] if len(sys.argv) > 2 else "deep"
    language = sys.argv[3] if len(sys.argv) > 3 else "both"
    
    queries = generate_queries(topic, depth, language)
    
    # 输出 JSON 格式
    output = {
        "topic": topic,
        "depth": depth,
        "language": language,
        "queries": queries,
        "count": len(queries)
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
