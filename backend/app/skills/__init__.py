"""
TokenDance Skill System

Skill 系统是 TokenDance 的核心架构创新，通过三级懒加载机制节省 90%+ 的 Token 消耗。

核心组件：
- SkillRegistry: Skill 注册表，管理 L1 元数据
- SkillMatcher: Skill 意图匹配器，支持关键词/Embedding/LLM Rerank
- SkillLoader: Skill 加载器，负责 L2 指令和 L3 资源的加载

使用示例：
    >>> from app.skills import get_skill_registry, get_skill_matcher
    >>> 
    >>> # 获取注册表
    >>> registry = get_skill_registry()
    >>> print(f"Loaded {len(registry)} skills")
    >>> 
    >>> # 匹配 Skill
    >>> matcher = get_skill_matcher()
    >>> match = await matcher.match("帮我调研 AI Agent 市场")
    >>> if match:
    ...     print(f"Matched: {match.skill_id} (score={match.score:.2f})")
"""

# Registry
from .registry import (
    SkillRegistry,
    get_skill_registry,
    init_skill_registry,
)

# Matcher
from .matcher import (
    SkillMatcher,
    create_skill_matcher,
    get_skill_matcher,
    reset_skill_matcher,
)

# Loader
from .loader import (
    SkillLoader,
    SkillContextBuilder,
)

# Types
from .types import (
    SkillMetadata,
    SkillMatch,
    SkillChain,
    SkillChainStep,
    SkillChainMode,
    SkillContext,
    SkillStatus,
    ContextIsolationMode,
    Artifact,
)

# Embedding
from .embedding import (
    BaseEmbedding,
    SentenceTransformerEmbedding,
    get_embedding_model,
    set_embedding_model,
)

__all__ = [
    # Registry
    "SkillRegistry",
    "get_skill_registry",
    "init_skill_registry",
    # Matcher
    "SkillMatcher",
    "create_skill_matcher",
    "get_skill_matcher",
    "reset_skill_matcher",
    # Loader
    "SkillLoader",
    "SkillContextBuilder",
    # Types
    "SkillMetadata",
    "SkillMatch",
    "SkillChain",
    "SkillChainStep",
    "SkillChainMode",
    "SkillContext",
    "SkillStatus",
    "ContextIsolationMode",
    "Artifact",
    # Embedding
    "BaseEmbedding",
    "SentenceTransformerEmbedding",
    "get_embedding_model",
    "set_embedding_model",
]
