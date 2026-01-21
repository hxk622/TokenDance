"""
UserResearchPreference - 用户研究偏好模型

存储用户的研究偏好设置，支持：
1. 显式设置 (用户手动配置)
2. 隐式学习 (从用户行为中学习)
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExpertiseLevel(str, PyEnum):
    """专业水平"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class ResearchDepth(str, PyEnum):
    """研究深度"""
    QUICK = "quick"       # 快速 (3-5 来源)
    STANDARD = "standard" # 标准 (8-10 来源)
    DEEP = "deep"         # 深度 (15-20 来源)


class ReportStyle(str, PyEnum):
    """报告风格"""
    CONCISE = "concise"   # 简洁
    DETAILED = "detailed" # 详细
    ACADEMIC = "academic" # 学术


class UserResearchPreference(Base):
    """用户研究偏好"""
    __tablename__ = "user_research_preferences"
    
    # 主键
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    
    # ==================== 来源偏好 ====================
    # 偏好的来源类型 ['academic', 'official', 'news', 'blog']
    preferred_source_types: Mapped[list] = mapped_column(
        JSON, 
        default=["academic", "official", "news"]
    )
    
    # 信任的域名列表
    trusted_domains: Mapped[list] = mapped_column(
        JSON,
        default=[]
    )
    
    # 屏蔽的域名列表
    blocked_domains: Mapped[list] = mapped_column(
        JSON,
        default=[]
    )
    
    # 偏好语言 ['zh', 'en', 'ja', ...]
    preferred_languages: Mapped[list] = mapped_column(
        JSON,
        default=["zh", "en"]
    )
    
    # ==================== 深度偏好 ====================
    default_depth: Mapped[ResearchDepth] = mapped_column(
        Enum(ResearchDepth, values_callable=lambda x: [e.value for e in x]),
        default=ResearchDepth.STANDARD
    )
    
    # 默认来源数量
    default_breadth: Mapped[int] = mapped_column(
        Integer,
        default=8
    )
    
    # ==================== 专业背景 ====================
    expertise_level: Mapped[ExpertiseLevel] = mapped_column(
        Enum(ExpertiseLevel, values_callable=lambda x: [e.value for e in x]),
        default=ExpertiseLevel.INTERMEDIATE
    )
    
    # 专业领域 ['AI', 'Finance', 'Healthcare', ...]
    expertise_domains: Mapped[list] = mapped_column(
        JSON,
        default=[]
    )
    
    # ==================== 输出偏好 ====================
    preferred_report_style: Mapped[ReportStyle] = mapped_column(
        Enum(ReportStyle, values_callable=lambda x: [e.value for e in x]),
        default=ReportStyle.DETAILED
    )
    
    include_charts: Mapped[bool] = mapped_column(default=True)
    include_citations: Mapped[bool] = mapped_column(default=True)
    
    # ==================== 学习数据 ====================
    # 域名分数 {"domain": score} 正数表示偏好，负数表示不喜欢
    domain_scores: Mapped[dict] = mapped_column(
        JSON,
        default={}
    )
    
    # 来源类型分数 {"type": score}
    source_type_scores: Mapped[dict] = mapped_column(
        JSON,
        default={}
    )
    
    # 深度调整历史 (用于学习默认深度)
    depth_adjustments: Mapped[list] = mapped_column(
        JSON,
        default=[]
    )
    
    # 交互历史统计
    interaction_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # ==================== 时间戳 ====================
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "preferred_source_types": self.preferred_source_types,
            "trusted_domains": self.trusted_domains,
            "blocked_domains": self.blocked_domains,
            "preferred_languages": self.preferred_languages,
            "default_depth": self.default_depth.value,
            "default_breadth": self.default_breadth,
            "expertise_level": self.expertise_level.value,
            "expertise_domains": self.expertise_domains,
            "preferred_report_style": self.preferred_report_style.value,
            "include_charts": self.include_charts,
            "include_citations": self.include_citations,
            "interaction_count": self.interaction_count,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
