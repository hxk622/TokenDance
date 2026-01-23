"""
SkillMatcher - Skill意图匹配器

职责：
1. 根据用户消息匹配最相关的Skill
2. 支持多种匹配策略：关键词、Embedding、BGE Rerank
3. 可配置匹配阈值

匹配流程：
1. 关键词匹配（快速初筛）- 包含中文别名支持
2. Embedding匹配（语义理解）
3. BGE Rerank（精确重排序）- 替代 LLM Rerank，更快更准
"""

import logging
import re
from typing import Protocol

from typing import Any

from .registry import SkillRegistry
from .types import SkillMatch, SkillMetadata

logger = logging.getLogger(__name__)


# ============================================================================
# 中文 Skill 别名映射
# ============================================================================

# Skill 名称到中文别名的映射（支持多语言匹配）
SKILL_CHINESE_ALIASES: dict[str, list[str]] = {
    # 研究类
    "deep_research": ["深度研究", "调研", "研究报告", "分析报告", "研究"],
    "financial_research": ["金融研究", "投研", "股票分析", "财务分析", "行业分析"],
    "market_research": ["市场研究", "市场调研", "市场分析", "竞品分析"],

    # 生成类
    "ppt": ["PPT", "幻灯片", "演示文稿", "做PPT", "生成PPT"],
    "ppt_generation": ["PPT生成", "幻灯片生成", "演示文稿生成"],
    "image_generation": ["图片生成", "生成图片", "画图", "AI绘画"],

    # 代码类
    "code_review": ["代码审查", "代码评审", "Review代码", "审查代码"],
    "systematic_debugging": ["调试", "Debug", "排查问题", "修Bug"],

    # 文档类
    "scientific_writing": ["学术写作", "论文写作", "科学写作"],
    "literature_review": ["文献综述", "文献回顾", "综述"],
    "peer_review": ["同行评审", "论文评审"],

    # 数据类
    "exploratory_data_analysis": ["数据分析", "探索性分析", "EDA"],
    "statistical_analysis": ["统计分析", "统计"],

    # 工具类
    "perplexity_search": ["搜索", "联网搜索", "网络搜索"],
}


class EmbeddingModel(Protocol):
    """Embedding模型接口"""

    def encode(self, text: str) -> list[float]:
        """将文本编码为向量"""
        ...


class LLMClient(Protocol):
    """LLM客户端接口"""

    async def complete(self, prompt: str) -> str:
        """完成文本生成"""
        ...


class SkillMatcher:
    """Skill意图匹配器

    使用三级匹配策略：
    1. 关键词匹配（快速初筛）- 包含中文别名
    2. Embedding匹配（语义理解）
    3. BGE Rerank（精确重排序）- 替代 LLM，更快更准
    """

    def __init__(
        self,
        registry: SkillRegistry,
        embedding_model: EmbeddingModel | None = None,
        llm_client: LLMClient | None = None,
        enable_embedding: bool = True,
        enable_llm_rerank: bool = False,
        enable_bge_rerank: bool = True,
    ):
        """初始化匹配器

        Args:
            registry: Skill注册表
            embedding_model: Embedding模型（可选）
            llm_client: LLM客户端（可选，用于Rerank，已废弃）
            enable_embedding: 是否启用Embedding匹配
            enable_llm_rerank: 是否启用LLM Rerank（已废弃，使用 BGE）
            enable_bge_rerank: 是否启用 BGE Rerank（默认启用）
        """
        self.registry = registry
        self.embedding_model = embedding_model
        self.llm_client = llm_client
        self.enable_embedding = enable_embedding and embedding_model is not None
        self.enable_llm_rerank = enable_llm_rerank and llm_client is not None
        self.enable_bge_rerank = enable_bge_rerank

        # BGE Reranker（懒加载）
        self._bge_reranker: Any = None

        # Skill描述的Embedding缓存
        self._skill_embeddings: dict[str, list[float]] = {}

        # 如果有Embedding模型，预计算所有Skill的Embedding
        if self.enable_embedding:
            self._precompute_embeddings()

    def _precompute_embeddings(self) -> None:
        """预计算所有Skill描述的Embedding"""
        if not self.embedding_model:
            return

        logger.info("Precomputing skill embeddings...")

        for skill in self.registry.get_all():
            # 组合显示名和描述
            text = f"{skill.display_name}: {skill.description}"
            try:
                embedding = self.embedding_model.encode(text)
                self._skill_embeddings[skill.name] = embedding
            except Exception as e:
                logger.error(f"Failed to compute embedding for {skill.name}: {e}")

        logger.info(f"Computed embeddings for {len(self._skill_embeddings)} skills")

    async def match(
        self,
        user_message: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> SkillMatch | None:
        """匹配最相关的Skill

        Args:
            user_message: 用户消息
            top_k: 返回前k个候选
            min_score: 最低分数阈值

        Returns:
            最佳匹配结果或None
        """
        if not self.registry.get_all():
            logger.warning("No skills registered")
            return None

        # 1. 关键词匹配（快速初筛）
        keyword_candidates = self._keyword_match(user_message, top_k=5)
        logger.debug(f"Keyword match candidates: {keyword_candidates}")

        if not keyword_candidates:
            # 如果关键词没有匹配到，使用所有Skill作为候选
            keyword_candidates = [s.name for s in self.registry.get_all()]

        # 2. Embedding匹配（语义理解）
        if self.enable_embedding:
            embedding_candidates = self._embedding_match(
                user_message,
                keyword_candidates,
                top_k=top_k
            )
        else:
            # 不启用Embedding时，基于关键词结果构建候选
            embedding_candidates = [
                SkillMatch(
                    skill_id=sid,
                    score=0.5,  # 默认分数
                    reason="Keyword match",
                    metadata=self.registry.get(sid)
                )
                for sid in keyword_candidates[:top_k]
            ]

        if not embedding_candidates:
            return None

        # 3. BGE Rerank（优先）或 LLM Rerank
        if self.enable_bge_rerank and len(embedding_candidates) > 1:
            final = self._bge_rerank(user_message, embedding_candidates)
        elif self.enable_llm_rerank and len(embedding_candidates) > 1:
            final = await self._llm_rerank(user_message, embedding_candidates)
        else:
            final = embedding_candidates[0] if embedding_candidates else None

        # 应用阈值过滤
        if final:
            # 使用Skill自定义阈值或默认阈值
            threshold = min_score
            if final.metadata:
                threshold = max(threshold, final.metadata.match_threshold)

            if final.score >= threshold:
                logger.info(f"Matched skill: {final.skill_id} (score={final.score:.2f})")
                return final
            else:
                logger.info(
                    f"Best match {final.skill_id} below threshold "
                    f"(score={final.score:.2f} < {threshold})"
                )

        return None

    async def match_multiple(
        self,
        user_message: str,
        top_k: int = 3,
        min_score: float = 0.5,
    ) -> list[SkillMatch]:
        """匹配多个相关的Skill（用于多Skill协同场景）

        Args:
            user_message: 用户消息
            top_k: 返回前k个
            min_score: 最低分数阈值

        Returns:
            匹配结果列表
        """
        if not self.registry.get_all():
            return []

        # 使用所有Skill作为候选
        all_skill_ids = self.registry.get_skill_ids()

        if self.enable_embedding:
            candidates = self._embedding_match(user_message, all_skill_ids, top_k=top_k)
        else:
            candidates = [
                SkillMatch(
                    skill_id=sid,
                    score=self._calculate_keyword_score(user_message, sid),
                    reason="Keyword match",
                    metadata=self.registry.get(sid)
                )
                for sid in all_skill_ids
            ]
            candidates.sort(key=lambda x: -x.score)
            candidates = candidates[:top_k]

        # 过滤低分候选
        return [c for c in candidates if c.score >= min_score]

    def _keyword_match(self, message: str, top_k: int = 5) -> list[str]:
        """关键词匹配

        基于标签和显示名进行快速匹配。

        Args:
            message: 用户消息
            top_k: 返回前k个

        Returns:
            候选Skill ID列表
        """
        candidates: list[tuple] = []  # (skill_id, score)
        message_lower = message.lower()

        for skill in self.registry.get_all():
            score = self._calculate_keyword_score(message_lower, skill)
            if score > 0:
                candidates.append((skill.name, score))

        # 按分数排序
        candidates.sort(key=lambda x: -x[1])

        return [c[0] for c in candidates[:top_k]]

    def _calculate_keyword_score(
        self,
        message: str,
        skill: SkillMetadata | str
    ) -> float:
        """计算关键词匹配分数

        Args:
            message: 用户消息（小写）
            skill: Skill元数据或ID

        Returns:
            匹配分数 (0-1)
        """
        if isinstance(skill, str):
            skill_meta = self.registry.get(skill)
            if not skill_meta:
                return 0.0
            skill = skill_meta

        message_lower = message.lower() if message != message.lower() else message
        score = 0.0

        # 1. 检查标签匹配 (权重: 0.3)
        for tag in skill.tags:
            if tag.lower() in message_lower:
                score += 0.3
                break

        # 2. 检查显示名匹配 (权重: 0.4)
        if skill.display_name.lower() in message_lower:
            score += 0.4

        # 3. 检查name匹配 (权重: 0.2)
        # 处理下划线分隔的name
        name_parts = skill.name.replace("_", " ").lower()
        if name_parts in message_lower:
            score += 0.2

        # 4. 检查描述中的关键词 (权重: 0.1)
        # 提取描述中的关键词（长度>2的词）
        description_words = re.findall(r'\b\w{3,}\b', skill.description.lower())
        matched_words = sum(1 for w in description_words if w in message_lower)
        if matched_words > 0:
            score += min(0.1, matched_words * 0.02)

        # 5. 检查中文别名匹配 (权重: 0.5)
        chinese_aliases = SKILL_CHINESE_ALIASES.get(skill.name, [])
        for alias in chinese_aliases:
            if alias.lower() in message_lower:
                score += 0.5
                break

        return min(score, 1.0)

    def _embedding_match(
        self,
        message: str,
        candidates: list[str],
        top_k: int = 3,
    ) -> list[SkillMatch]:
        """Embedding语义匹配

        Args:
            message: 用户消息
            candidates: 候选Skill ID列表
            top_k: 返回前k个

        Returns:
            匹配结果列表
        """
        if not self.embedding_model:
            return []

        try:
            message_embedding = self.embedding_model.encode(message)
        except Exception as e:
            logger.error(f"Failed to encode message: {e}")
            return []

        scores: list[tuple] = []  # (skill_id, similarity)

        for skill_id in candidates:
            if skill_id not in self._skill_embeddings:
                continue

            skill_embedding = self._skill_embeddings[skill_id]
            similarity = self._cosine_similarity(message_embedding, skill_embedding)
            scores.append((skill_id, similarity))

        # 按相似度排序
        scores.sort(key=lambda x: -x[1])

        # 构建匹配结果
        results = []
        for skill_id, similarity in scores[:top_k]:
            results.append(SkillMatch(
                skill_id=skill_id,
                score=similarity,
                reason="Semantic similarity",
                metadata=self.registry.get(skill_id)
            ))

        return results

    def _bge_rerank(
        self,
        message: str,
        candidates: list[SkillMatch],
    ) -> SkillMatch | None:
        """使用 BGE Reranker 重排序候选

        相比 LLM Rerank：
        - 更快：本地模型，无网络延迟
        - 更便宜：免费开源
        - 更稳定：专门训练的重排序模型

        Args:
            message: 用户消息
            candidates: 候选匹配列表

        Returns:
            最佳匹配
        """
        if not candidates:
            return None

        # 懒加载 BGE Reranker
        if self._bge_reranker is None:
            try:
                from .reranker import get_reranker
                self._bge_reranker = get_reranker()
            except Exception as e:
                logger.warning(f"Failed to load BGE reranker, falling back: {e}")
                return candidates[0]

        try:
            # 构建候选文本（包含显示名和描述）
            candidate_texts = []
            for c in candidates:
                skill = self.registry.get(c.skill_id)
                if skill:
                    # 包含中文别名以提升中文查询的匹配效果
                    aliases = SKILL_CHINESE_ALIASES.get(c.skill_id, [])
                    alias_text = f" ({', '.join(aliases[:2])})" if aliases else ""
                    text = f"{skill.display_name}{alias_text}: {skill.description}"
                    candidate_texts.append(text)
                else:
                    candidate_texts.append(c.skill_id)

            # 使用 BGE Reranker 重排序
            rerank_results = self._bge_reranker.rerank(
                query=message,
                candidates=candidate_texts,
                top_k=1,
                threshold=0.1,
            )

            if rerank_results:
                best = rerank_results[0]
                result = candidates[best.index]
                # 使用 rerank 分数，但要融合原始分数
                result.score = (result.score + best.score) / 2
                result.reason = f"BGE rerank (score={best.score:.3f})"
                logger.debug(f"BGE rerank selected: {result.skill_id} (score={result.score:.3f})")
                return result

        except Exception as e:
            logger.error(f"BGE rerank failed: {e}")

        return candidates[0] if candidates else None

    async def _llm_rerank(
        self,
        message: str,
        candidates: list[SkillMatch],
    ) -> SkillMatch | None:
        """使用LLM重排序候选（已废弃，保留兼容性）

        推荐使用 BGE Rerank 替代。

        Args:
            message: 用户消息
            candidates: 候选匹配列表

        Returns:
            最佳匹配
        """
        if not self.llm_client or not candidates:
            return candidates[0] if candidates else None

        # 构建候选列表
        skill_list = "\n".join([
            f"{i+1}. {self.registry.get(c.skill_id).display_name}: "
            f"{self.registry.get(c.skill_id).description}"
            for i, c in enumerate(candidates)
            if self.registry.get(c.skill_id)
        ])

        prompt = f"""User message: "{message}"

Available skills:
{skill_list}

Which skill is most relevant to handle the user's request?
Respond with just the number (1-{len(candidates)}).
If none are relevant, respond with 0."""

        try:
            response = await self.llm_client.complete(prompt)
            # 解析响应
            idx_str = response.strip()
            # 提取数字
            match = re.search(r'\d+', idx_str)
            if match:
                idx = int(match.group()) - 1
                if 0 <= idx < len(candidates):
                    result = candidates[idx]
                    # 提升LLM选中的候选分数
                    result.score = max(result.score, 0.85)
                    result.reason = "LLM rerank"
                    return result
        except Exception as e:
            logger.error(f"LLM rerank failed: {e}")

        return candidates[0] if candidates else None

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """计算余弦相似度

        Args:
            a: 向量a
            b: 向量b

        Returns:
            相似度 (-1 到 1)
        """
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=False))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def refresh_embeddings(self) -> None:
        """刷新Skill Embedding缓存"""
        self._skill_embeddings.clear()
        self._precompute_embeddings()


class SimpleEmbeddingModel:
    """简单的Embedding模型实现（基于TF-IDF）

    用于测试和没有外部Embedding服务时的降级方案。
    """

    def __init__(self):
        self.vocabulary: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self._fitted = False

    def fit(self, texts: list[str]) -> None:
        """拟合词汇表"""
        import math

        # 构建词汇表
        doc_freq: dict[str, int] = {}

        for text in texts:
            words = set(self._tokenize(text))
            for word in words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = len(self.vocabulary)
                doc_freq[word] = doc_freq.get(word, 0) + 1

        # 计算IDF
        n_docs = len(texts)
        for word, freq in doc_freq.items():
            self.idf[word] = math.log(n_docs / (freq + 1)) + 1

        self._fitted = True

    def encode(self, text: str) -> list[float]:
        """编码文本为向量"""
        if not self._fitted:
            # 自动拟合
            self.fit([text])

        words = self._tokenize(text)
        word_freq: dict[str, int] = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # 构建TF-IDF向量
        vector = [0.0] * len(self.vocabulary)

        for word, freq in word_freq.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                tf = freq / len(words) if words else 0
                idf = self.idf.get(word, 1.0)
                vector[idx] = tf * idf

        # L2归一化
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def _tokenize(self, text: str) -> list[str]:
        """分词"""
        # 简单的分词：按非字母数字字符分割，转小写
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        # 过滤太短的词
        return [w for w in words if len(w) > 2]


# ============================================================================
# 工厂函数
# ============================================================================

_global_matcher: SkillMatcher | None = None


def create_skill_matcher(
    registry: SkillRegistry,
    use_sentence_transformer: bool = True,
    llm_client: LLMClient | None = None,
) -> SkillMatcher:
    """创建 SkillMatcher 实例

    Args:
        registry: Skill 注册表
        use_sentence_transformer: 是否使用 SentenceTransformer（默认 True）
        llm_client: LLM 客户端（可选，用于 Rerank）

    Returns:
        SkillMatcher 实例
    """
    embedding_model = None

    if use_sentence_transformer:
        try:
            from .embedding import SentenceTransformerEmbedding
            embedding_model = SentenceTransformerEmbedding()
            logger.info("Using SentenceTransformer for skill matching")
        except ImportError:
            logger.warning(
                "sentence-transformers not available, falling back to keyword matching"
            )

    return SkillMatcher(
        registry=registry,
        embedding_model=embedding_model,
        llm_client=llm_client,
        enable_embedding=embedding_model is not None,
        enable_llm_rerank=llm_client is not None,
    )


def get_skill_matcher(registry: SkillRegistry | None = None) -> SkillMatcher:
    """获取全局 SkillMatcher 单例

    Args:
        registry: Skill 注册表（首次调用时必须提供）

    Returns:
        SkillMatcher 单例
    """
    global _global_matcher

    if _global_matcher is None:
        if registry is None:
            from .registry import get_skill_registry
            registry = get_skill_registry()
        _global_matcher = create_skill_matcher(registry)

    return _global_matcher


def reset_skill_matcher() -> None:
    """重置全局 SkillMatcher 单例"""
    global _global_matcher
    _global_matcher = None
