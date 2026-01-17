"""
TokenDance Skill System

Skill 系统是 TokenDance 的核心架构创新，通过三级懒加载机制节省 90%+ 的 Token 消耗。

核心组件：
- SkillRegistry: Skill 注册表，管理 L1 元数据
- SkillMatcher: Skill 意图匹配器，支持关键词/Embedding/LLM Rerank
- SkillLoader: Skill 加载器，负责 L2 指令和 L3 资源的加载
- SkillExecutor: Skill 执行器，负责执行 L3 脚本（自动化能力）

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
# Embedding
from .embedding import (
    BaseEmbedding,
    SentenceTransformerEmbedding,
    get_embedding_model,
    set_embedding_model,
)

# Executor
from .executor import (
    SkillExecutor,
    get_skill_executor,
    reset_skill_executor,
)

# Hot Reload
from .hot_reload import (
    SkillHotReloader,
    get_skill_hot_reloader,
    setup_hot_reload_for_app,
    start_skill_hot_reload,
    stop_skill_hot_reload,
)

# Loader
from .loader import (
    SkillContextBuilder,
    SkillLoader,
)

# Matcher
from .matcher import (
    SkillMatcher,
    create_skill_matcher,
    get_skill_matcher,
    reset_skill_matcher,
)

# Monitoring
from .monitoring import (
    ExecutionTimer,
    MatchTimer,
    SkillMonitor,
    get_skill_monitor,
    reset_skill_monitor,
)
from .registry import (
    SkillRegistry,
    get_skill_registry,
    init_skill_registry,
)

# Types
from .types import (
    Artifact,
    ContextIsolationMode,
    SkillChain,
    SkillChainMode,
    SkillChainStep,
    SkillContext,
    SkillMatch,
    SkillMetadata,
    SkillStatus,
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
    # Executor
    "SkillExecutor",
    "get_skill_executor",
    "reset_skill_executor",
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
    # Hot Reload
    "SkillHotReloader",
    "get_skill_hot_reloader",
    "start_skill_hot_reload",
    "stop_skill_hot_reload",
    "setup_hot_reload_for_app",
    # Monitoring
    "SkillMonitor",
    "MatchTimer",
    "ExecutionTimer",
    "get_skill_monitor",
    "reset_skill_monitor",
]
