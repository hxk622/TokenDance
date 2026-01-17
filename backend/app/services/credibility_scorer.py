# -*- coding: utf-8 -*-
"""
来源可信度评分器 (Credibility Scorer)

功能:
- Domain Authority 评分
- 时效性加权
- 学术/权威来源优先
- 内容质量评估

评分维度:
1. 域名权威性 (0-40 分)
2. 时效性 (0-20 分)
3. 内容质量 (0-20 分)
4. 来源类型 (0-20 分)

总分: 0-100 分
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from urllib.parse import urlparse
from enum import Enum

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """来源类型"""
    ACADEMIC = "academic"           # 学术来源 (arXiv, PubMed, IEEE)
    GOVERNMENT = "government"       # 政府来源 (.gov)
    OFFICIAL = "official"           # 官方文档 (docs.*, official)
    NEWS_MAJOR = "news_major"       # 主流媒体 (Reuters, BBC, NYT)
    NEWS_TECH = "news_tech"         # 科技媒体 (TechCrunch, Wired)
    PROFESSIONAL = "professional"   # 专业平台 (GitHub, StackOverflow)
    ENCYCLOPEDIA = "encyclopedia"   # 百科类 (Wikipedia)
    BLOG = "blog"                   # 博客
    FORUM = "forum"                 # 论坛
    UNKNOWN = "unknown"             # 未知


@dataclass
class CredibilityScore:
    """可信度评分"""
    url: str
    total_score: float          # 总分 (0-100)
    domain_score: float         # 域名分 (0-40)
    freshness_score: float      # 时效分 (0-20)
    content_score: float        # 内容分 (0-20)
    source_type_score: float    # 类型分 (0-20)
    source_type: SourceType
    domain: str
    is_trusted: bool            # 是否可信 (>60分)
    reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "total_score": round(self.total_score, 1),
            "breakdown": {
                "domain": round(self.domain_score, 1),
                "freshness": round(self.freshness_score, 1),
                "content": round(self.content_score, 1),
                "source_type": round(self.source_type_score, 1)
            },
            "source_type": self.source_type.value,
            "domain": self.domain,
            "is_trusted": self.is_trusted,
            "reasoning": self.reasoning
        }


class CredibilityScorer:
    """可信度评分器"""
    
    # 高权威域名 (40分)
    HIGH_AUTHORITY_DOMAINS = {
        # 学术
        'arxiv.org', 'pubmed.ncbi.nlm.nih.gov', 'scholar.google.com',
        'ieee.org', 'acm.org', 'nature.com', 'science.org',
        'sciencedirect.com', 'springer.com', 'wiley.com',
        # 政府/国际组织
        'nih.gov', 'cdc.gov', 'who.int', 'un.org', 'worldbank.org',
        # 官方文档
        'docs.python.org', 'docs.microsoft.com', 'developer.mozilla.org',
        'cloud.google.com', 'aws.amazon.com', 'docs.github.com',
    }
    
    # 中高权威域名 (30分)
    MEDIUM_HIGH_DOMAINS = {
        # 主流媒体
        'reuters.com', 'bbc.com', 'nytimes.com', 'theguardian.com',
        'wsj.com', 'ft.com', 'economist.com', 'bloomberg.com',
        # 科技媒体
        'techcrunch.com', 'wired.com', 'arstechnica.com', 'theverge.com',
        'venturebeat.com', 'zdnet.com',
        # 专业平台
        'github.com', 'stackoverflow.com', 'medium.com',
        # 百科
        'wikipedia.org', 'britannica.com',
    }
    
    # 中等权威域名 (20分)
    MEDIUM_DOMAINS = {
        'reddit.com', 'quora.com', 'dev.to', 'hashnode.com',
        'towardsdatascience.com', 'hackernews.com',
    }
    
    # 低可信域名 (5分)
    LOW_TRUST_PATTERNS = [
        r'\.blogspot\.', r'\.wordpress\.com', r'\.tumblr\.com',
        r'\.weebly\.com', r'\.wix\.com',
        r'forum\.', r'bbs\.', r'tieba\.baidu\.com',
    ]
    
    # 来源类型评分
    SOURCE_TYPE_SCORES = {
        SourceType.ACADEMIC: 20,
        SourceType.GOVERNMENT: 20,
        SourceType.OFFICIAL: 18,
        SourceType.NEWS_MAJOR: 15,
        SourceType.NEWS_TECH: 14,
        SourceType.PROFESSIONAL: 12,
        SourceType.ENCYCLOPEDIA: 10,
        SourceType.BLOG: 5,
        SourceType.FORUM: 3,
        SourceType.UNKNOWN: 5,
    }
    
    def __init__(self, freshness_weight: float = 1.0):
        """
        Args:
            freshness_weight: 时效性权重 (默认 1.0)
        """
        self.freshness_weight = freshness_weight
    
    def score(
        self,
        url: str,
        content: Optional[str] = None,
        publish_date: Optional[datetime] = None,
        title: Optional[str] = None
    ) -> CredibilityScore:
        """评估来源可信度
        
        Args:
            url: 来源 URL
            content: 内容 (可选，用于内容质量评估)
            publish_date: 发布日期 (可选)
            title: 标题 (可选)
            
        Returns:
            CredibilityScore: 评分结果
        """
        # 解析 URL
        parsed = urlparse(url)
        domain = parsed.netloc.lower().lstrip('www.')
        
        # 1. 域名权威性评分
        domain_score = self._score_domain(domain, url)
        
        # 2. 来源类型识别和评分
        source_type = self._identify_source_type(domain, url)
        source_type_score = self.SOURCE_TYPE_SCORES.get(source_type, 5)
        
        # 3. 时效性评分
        freshness_score = self._score_freshness(publish_date, content)
        
        # 4. 内容质量评分
        content_score = self._score_content(content, title)
        
        # 计算总分
        total_score = domain_score + source_type_score + freshness_score + content_score
        
        # 生成推理
        reasoning = self._generate_reasoning(
            domain, source_type, domain_score, freshness_score, content_score
        )
        
        score = CredibilityScore(
            url=url,
            total_score=total_score,
            domain_score=domain_score,
            freshness_score=freshness_score,
            content_score=content_score,
            source_type_score=source_type_score,
            source_type=source_type,
            domain=domain,
            is_trusted=total_score >= 60,
            reasoning=reasoning
        )
        
        logger.debug(f"Credibility score for {domain}: {total_score:.1f}")
        return score
    
    def _score_domain(self, domain: str, url: str) -> float:
        """域名权威性评分 (0-40)"""
        
        # 检查高权威域名
        for trusted in self.HIGH_AUTHORITY_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return 40
        
        # 检查中高权威域名
        for trusted in self.MEDIUM_HIGH_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return 30
        
        # 检查中等域名
        for trusted in self.MEDIUM_DOMAINS:
            if domain == trusted or domain.endswith('.' + trusted):
                return 20
        
        # 检查政府域名
        if domain.endswith('.gov') or domain.endswith('.gov.cn'):
            return 38
        
        # 检查教育域名
        if domain.endswith('.edu') or domain.endswith('.edu.cn') or domain.endswith('.ac.uk'):
            return 35
        
        # 检查低可信模式
        for pattern in self.LOW_TRUST_PATTERNS:
            if re.search(pattern, url.lower()):
                return 5
        
        # 默认分数
        return 15
    
    def _identify_source_type(self, domain: str, url: str) -> SourceType:
        """识别来源类型"""
        url_lower = url.lower()
        domain_lower = domain.lower()
        
        # 学术来源
        academic_patterns = ['arxiv', 'pubmed', 'ieee', 'acm.org', 'nature.com', 'science.org']
        if any(p in domain_lower for p in academic_patterns):
            return SourceType.ACADEMIC
        
        # 政府来源
        if '.gov' in domain_lower:
            return SourceType.GOVERNMENT
        
        # 官方文档
        if domain_lower.startswith('docs.') or 'documentation' in url_lower:
            return SourceType.OFFICIAL
        
        # 主流媒体
        major_news = ['reuters', 'bbc', 'nytimes', 'guardian', 'wsj', 'bloomberg']
        if any(n in domain_lower for n in major_news):
            return SourceType.NEWS_MAJOR
        
        # 科技媒体
        tech_news = ['techcrunch', 'wired', 'verge', 'arstechnica', 'venturebeat']
        if any(n in domain_lower for n in tech_news):
            return SourceType.NEWS_TECH
        
        # 专业平台
        professional = ['github', 'stackoverflow', 'gitlab']
        if any(p in domain_lower for p in professional):
            return SourceType.PROFESSIONAL
        
        # 百科
        if 'wikipedia' in domain_lower or 'britannica' in domain_lower:
            return SourceType.ENCYCLOPEDIA
        
        # 博客
        blog_patterns = ['blog', 'medium.com', '.blogspot.', '.wordpress.']
        if any(p in url_lower for p in blog_patterns):
            return SourceType.BLOG
        
        # 论坛
        forum_patterns = ['forum', 'reddit', 'quora', 'bbs', 'tieba']
        if any(p in url_lower for p in forum_patterns):
            return SourceType.FORUM
        
        return SourceType.UNKNOWN
    
    def _score_freshness(
        self,
        publish_date: Optional[datetime],
        content: Optional[str]
    ) -> float:
        """时效性评分 (0-20)"""
        
        # 如果没有日期，尝试从内容提取
        if publish_date is None and content:
            publish_date = self._extract_date_from_content(content)
        
        if publish_date is None:
            return 10  # 默认中等分数
        
        now = datetime.now()
        age_days = (now - publish_date).days
        
        # 时效性评分规则
        if age_days <= 30:  # 1 个月内
            return 20
        elif age_days <= 90:  # 3 个月内
            return 18
        elif age_days <= 180:  # 6 个月内
            return 15
        elif age_days <= 365:  # 1 年内
            return 12
        elif age_days <= 730:  # 2 年内
            return 8
        else:
            return 5
    
    def _extract_date_from_content(self, content: str) -> Optional[datetime]:
        """从内容提取日期"""
        # 匹配常见日期格式
        patterns = [
            r'(\d{4})-(\d{2})-(\d{2})',  # 2024-01-15
            r'(\d{4})/(\d{2})/(\d{2})',  # 2024/01/15
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',  # January 15, 2024
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    if len(match.groups()) == 3:
                        if match.group(1).isdigit():
                            return datetime(
                                int(match.group(1)),
                                int(match.group(2)),
                                int(match.group(3))
                            )
                except:
                    pass
        
        return None
    
    def _score_content(
        self,
        content: Optional[str],
        title: Optional[str]
    ) -> float:
        """内容质量评分 (0-20)"""
        if not content:
            return 10  # 默认分数
        
        score = 10  # 基础分
        
        # 长度因素 (内容充实)
        if len(content) > 5000:
            score += 3
        elif len(content) > 2000:
            score += 2
        elif len(content) < 500:
            score -= 2
        
        # 包含数据/引用 (更可靠)
        if re.search(r'\d+[%$€¥]|\d+\.\d+', content):
            score += 2
        
        if re.search(r'\[\d+\]|references|citations', content.lower()):
            score += 2
        
        # 包含代码块 (技术内容)
        if '```' in content or '<code>' in content:
            score += 1
        
        # 标题质量
        if title:
            # 避免 clickbait
            clickbait_patterns = ['you won\'t believe', 'shocking', '!!!', 'BREAKING']
            if any(p.lower() in title.lower() for p in clickbait_patterns):
                score -= 3
        
        return max(0, min(20, score))
    
    def _generate_reasoning(
        self,
        domain: str,
        source_type: SourceType,
        domain_score: float,
        freshness_score: float,
        content_score: float
    ) -> str:
        """生成评分推理"""
        parts = []
        
        # 域名评价
        if domain_score >= 35:
            parts.append(f"High authority domain ({domain})")
        elif domain_score >= 25:
            parts.append(f"Reputable domain ({domain})")
        elif domain_score >= 15:
            parts.append(f"Standard domain ({domain})")
        else:
            parts.append(f"Low authority domain ({domain})")
        
        # 类型评价
        type_desc = {
            SourceType.ACADEMIC: "Academic source",
            SourceType.GOVERNMENT: "Government source",
            SourceType.OFFICIAL: "Official documentation",
            SourceType.NEWS_MAJOR: "Major news outlet",
            SourceType.NEWS_TECH: "Tech media",
            SourceType.PROFESSIONAL: "Professional platform",
            SourceType.ENCYCLOPEDIA: "Encyclopedia",
            SourceType.BLOG: "Blog",
            SourceType.FORUM: "Forum/Community",
            SourceType.UNKNOWN: "Unknown type",
        }
        parts.append(type_desc.get(source_type, "Unknown"))
        
        # 时效性评价
        if freshness_score >= 18:
            parts.append("Very recent")
        elif freshness_score >= 12:
            parts.append("Reasonably fresh")
        else:
            parts.append("May be outdated")
        
        return ". ".join(parts) + "."
    
    def rank_sources(
        self,
        sources: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], CredibilityScore]]:
        """对来源列表进行可信度排序
        
        Args:
            sources: 来源列表 (每项包含 url, content, title 等)
            
        Returns:
            排序后的 (来源, 评分) 列表
        """
        scored = []
        for source in sources:
            score = self.score(
                url=source.get('url') or source.get('link', ''),
                content=source.get('content') or source.get('snippet', ''),
                title=source.get('title', '')
            )
            scored.append((source, score))
        
        # 按总分降序排序
        scored.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored


# 便捷函数
def score_source(url: str, content: Optional[str] = None) -> CredibilityScore:
    """评估单个来源的可信度"""
    scorer = CredibilityScorer()
    return scorer.score(url, content)


def rank_sources(sources: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], CredibilityScore]]:
    """对来源进行可信度排序"""
    scorer = CredibilityScorer()
    return scorer.rank_sources(sources)
