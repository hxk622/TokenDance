# -*- coding: utf-8 -*-
"""
Research Findings Model - 研究发现数据模型

定义 Deep Research 输出的结构化数据格式，用于：
- 连接 Deep Research 和 PPT Generation
- 标准化研究成果的表示
- 支持多种导出格式（报告、PPT、思维导图）
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class FindingImportance(str, Enum):
    """发现重要性级别"""
    HIGH = "high"       # 核心发现，必须展示
    MEDIUM = "medium"   # 重要发现，建议展示
    LOW = "low"         # 补充信息，可选展示


class DataPointType(str, Enum):
    """数据点类型"""
    NUMBER = "number"           # 单一数值
    PERCENTAGE = "percentage"   # 百分比
    COMPARISON = "comparison"   # 对比数据
    TREND = "trend"             # 趋势数据
    RANKING = "ranking"         # 排名数据


@dataclass
class Source:
    """信息来源"""
    url: str
    title: str
    domain: str
    accessed_at: datetime = field(default_factory=datetime.now)
    credibility: str = "medium"  # high/medium/low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "domain": self.domain,
            "accessed_at": self.accessed_at.isoformat(),
            "credibility": self.credibility
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Source":
        return cls(
            url=data["url"],
            title=data["title"],
            domain=data.get("domain", ""),
            accessed_at=datetime.fromisoformat(data["accessed_at"]) if "accessed_at" in data else datetime.now(),
            credibility=data.get("credibility", "medium")
        )


@dataclass
class Quote:
    """可引用语句"""
    text: str
    source: Optional[Source] = None
    author: Optional[str] = None
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "source": self.source.to_dict() if self.source else None,
            "author": self.author,
            "context": self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quote":
        return cls(
            text=data["text"],
            source=Source.from_dict(data["source"]) if data.get("source") else None,
            author=data.get("author"),
            context=data.get("context")
        )


@dataclass
class DataPoint:
    """数据点 - 可图表化的数据"""
    label: str
    value: Any  # 数值、百分比、或对比数据
    type: DataPointType = DataPointType.NUMBER
    unit: Optional[str] = None
    source: Optional[Source] = None
    context: Optional[str] = None  # 数据背景说明
    
    # 对比数据专用
    comparison_base: Optional[str] = None  # 对比基准
    change_direction: Optional[str] = None  # increase/decrease/stable
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "type": self.type.value,
            "unit": self.unit,
            "source": self.source.to_dict() if self.source else None,
            "context": self.context,
            "comparison_base": self.comparison_base,
            "change_direction": self.change_direction
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataPoint":
        return cls(
            label=data["label"],
            value=data["value"],
            type=DataPointType(data.get("type", "number")),
            unit=data.get("unit"),
            source=Source.from_dict(data["source"]) if data.get("source") else None,
            context=data.get("context"),
            comparison_base=data.get("comparison_base"),
            change_direction=data.get("change_direction")
        )


@dataclass
class ResearchFinding:
    """单个研究发现"""
    title: str
    content: str
    importance: FindingImportance = FindingImportance.MEDIUM
    source_urls: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # 可选的细分要点
    sub_points: List[str] = field(default_factory=list)
    
    # 关联数据
    related_data: List[DataPoint] = field(default_factory=list)
    related_quotes: List[Quote] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "importance": self.importance.value,
            "source_urls": self.source_urls,
            "tags": self.tags,
            "sub_points": self.sub_points,
            "related_data": [d.to_dict() for d in self.related_data],
            "related_quotes": [q.to_dict() for q in self.related_quotes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchFinding":
        return cls(
            title=data["title"],
            content=data["content"],
            importance=FindingImportance(data.get("importance", "medium")),
            source_urls=data.get("source_urls", []),
            tags=data.get("tags", []),
            sub_points=data.get("sub_points", []),
            related_data=[DataPoint.from_dict(d) for d in data.get("related_data", [])],
            related_quotes=[Quote.from_dict(q) for q in data.get("related_quotes", [])]
        )


@dataclass
class ResearchFindings:
    """研究发现集合 - Deep Research 的结构化输出"""
    session_id: str
    topic: str
    summary: str  # 研究摘要（1-2段）
    
    # 核心内容
    key_findings: List[ResearchFinding] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)
    quotes: List[Quote] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    research_duration_seconds: int = 0
    total_sources_consulted: int = 0
    
    # 可选：结论和建议
    conclusions: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def get_high_importance_findings(self) -> List[ResearchFinding]:
        """获取高重要性发现"""
        return [f for f in self.key_findings if f.importance == FindingImportance.HIGH]
    
    def get_findings_by_tag(self, tag: str) -> List[ResearchFinding]:
        """按标签获取发现"""
        return [f for f in self.key_findings if tag in f.tags]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "summary": self.summary,
            "key_findings": [f.to_dict() for f in self.key_findings],
            "data_points": [d.to_dict() for d in self.data_points],
            "quotes": [q.to_dict() for q in self.quotes],
            "sources": [s.to_dict() for s in self.sources],
            "created_at": self.created_at.isoformat(),
            "research_duration_seconds": self.research_duration_seconds,
            "total_sources_consulted": self.total_sources_consulted,
            "conclusions": self.conclusions,
            "recommendations": self.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResearchFindings":
        return cls(
            session_id=data["session_id"],
            topic=data["topic"],
            summary=data["summary"],
            key_findings=[ResearchFinding.from_dict(f) for f in data.get("key_findings", [])],
            data_points=[DataPoint.from_dict(d) for d in data.get("data_points", [])],
            quotes=[Quote.from_dict(q) for q in data.get("quotes", [])],
            sources=[Source.from_dict(s) for s in data.get("sources", [])],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            research_duration_seconds=data.get("research_duration_seconds", 0),
            total_sources_consulted=data.get("total_sources_consulted", 0),
            conclusions=data.get("conclusions", []),
            recommendations=data.get("recommendations", [])
        )
    
    def to_markdown_summary(self) -> str:
        """生成 Markdown 格式的摘要"""
        lines = [
            f"# {self.topic}",
            "",
            "## 研究摘要",
            self.summary,
            "",
            "## 关键发现",
        ]
        
        for i, finding in enumerate(self.key_findings, 1):
            importance_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(finding.importance.value, "")
            lines.append(f"### {i}. {finding.title} {importance_icon}")
            lines.append(finding.content)
            if finding.sub_points:
                for point in finding.sub_points:
                    lines.append(f"  - {point}")
            lines.append("")
        
        if self.conclusions:
            lines.append("## 结论")
            for conclusion in self.conclusions:
                lines.append(f"- {conclusion}")
            lines.append("")
        
        if self.recommendations:
            lines.append("## 建议")
            for rec in self.recommendations:
                lines.append(f"- {rec}")
            lines.append("")
        
        if self.sources:
            lines.append("## 参考来源")
            for source in self.sources[:10]:  # 最多显示10个
                lines.append(f"- [{source.title}]({source.url})")
        
        return "\n".join(lines)
