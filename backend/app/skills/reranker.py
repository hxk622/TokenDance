"""
BGE Reranker - 基于 BGE-Reranker-v2 的重排序器

使用 BAAI/bge-reranker-v2-m3 模型对候选 Skill 进行重排序，
提升 Skill 匹配的准确率。

特点：
- 免费开源，本地运行
- 支持多语言（中英文效果优秀）
- 轻量高效，比 LLM rerank 更快更便宜
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """重排序结果"""
    index: int           # 原始索引
    score: float         # 相关性分数 (0-1)
    text: str            # 原始文本


class BGEReranker:
    """BGE Reranker v2 封装

    使用 FlagEmbedding 的 FlagReranker 进行文档重排序。

    使用示例：
    ```python
    reranker = BGEReranker()

    query = "我想生成一个PPT"
    candidates = [
        "PPT Generation: 自动生成演示文稿",
        "Deep Research: 深度研究某个话题",
        "Code Review: 代码审查"
    ]

    results = reranker.rerank(query, candidates, top_k=1)
    # results[0].index = 0 (PPT Generation 最相关)
    ```
    """

    # 默认模型：轻量高效，多语言支持
    DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"

    def __init__(
        self,
        model_name: str | None = None,
        use_fp16: bool = True,
        device: str | None = None,
    ):
        """初始化 BGE Reranker

        Args:
            model_name: 模型名称，默认 bge-reranker-v2-m3
            use_fp16: 是否使用 FP16 加速（GPU 时推荐开启）
            device: 运行设备，None 表示自动选择
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.use_fp16 = use_fp16
        self.device = device
        self._reranker: Any = None
        self._initialized = False

    def _lazy_init(self) -> None:
        """懒加载模型（首次使用时加载）"""
        if self._initialized:
            return

        try:
            from FlagEmbedding import FlagReranker

            logger.info(f"Loading BGE reranker model: {self.model_name}")

            # 构建参数
            kwargs: dict[str, Any] = {"use_fp16": self.use_fp16}
            if self.device:
                kwargs["device"] = self.device

            self._reranker = FlagReranker(self.model_name, **kwargs)
            self._initialized = True

            logger.info("BGE reranker loaded successfully")

        except ImportError:
            logger.error(
                "FlagEmbedding not installed. "
                "Run: pip install FlagEmbedding"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to load BGE reranker: {e}")
            raise

    def compute_score(
        self,
        query: str,
        passage: str,
        normalize: bool = True,
    ) -> float:
        """计算单个 query-passage 对的相关性分数

        Args:
            query: 查询文本
            passage: 候选文本
            normalize: 是否归一化到 0-1 范围（sigmoid）

        Returns:
            相关性分数
        """
        self._lazy_init()

        score = self._reranker.compute_score(
            [query, passage],
            normalize=normalize
        )
        return float(score)

    def compute_scores(
        self,
        query: str,
        passages: list[str],
        normalize: bool = True,
    ) -> list[float]:
        """批量计算 query 与多个 passage 的相关性分数

        Args:
            query: 查询文本
            passages: 候选文本列表
            normalize: 是否归一化到 0-1 范围

        Returns:
            相关性分数列表
        """
        if not passages:
            return []

        self._lazy_init()

        # 构建 query-passage 对
        pairs = [[query, passage] for passage in passages]

        scores = self._reranker.compute_score(pairs, normalize=normalize)

        # 确保返回列表
        if isinstance(scores, (int, float)):
            return [float(scores)]
        return [float(s) for s in scores]

    def rerank(
        self,
        query: str,
        candidates: list[str],
        top_k: int | None = None,
        threshold: float = 0.0,
    ) -> list[RerankResult]:
        """对候选文本进行重排序

        Args:
            query: 查询文本
            candidates: 候选文本列表
            top_k: 返回前 k 个结果，None 表示返回全部
            threshold: 分数阈值，低于此值的结果不返回

        Returns:
            排序后的结果列表（按分数降序）
        """
        if not candidates:
            return []

        # 计算分数
        scores = self.compute_scores(query, candidates, normalize=True)

        # 构建结果
        results = [
            RerankResult(index=i, score=score, text=text)
            for i, (score, text) in enumerate(zip(scores, candidates, strict=False))
            if score >= threshold
        ]

        # 按分数降序排序
        results.sort(key=lambda x: x.score, reverse=True)

        # 取 top_k
        if top_k is not None:
            results = results[:top_k]

        return results

    def rerank_with_metadata(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        text_key: str = "text",
        top_k: int | None = None,
        threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """对带元数据的候选进行重排序

        Args:
            query: 查询文本
            candidates: 候选列表，每个元素是包含文本的字典
            text_key: 文本字段的键名
            top_k: 返回前 k 个结果
            threshold: 分数阈值

        Returns:
            排序后的结果，每个字典增加 'rerank_score' 字段
        """
        if not candidates:
            return []

        # 提取文本
        texts = [c.get(text_key, "") for c in candidates]

        # 计算分数
        scores = self.compute_scores(query, texts, normalize=True)

        # 添加分数并过滤
        results = []
        for candidate, score in zip(candidates, scores, strict=False):
            if score >= threshold:
                result = candidate.copy()
                result["rerank_score"] = score
                results.append(result)

        # 按分数降序排序
        results.sort(key=lambda x: x["rerank_score"], reverse=True)

        # 取 top_k
        if top_k is not None:
            results = results[:top_k]

        return results


# 全局单例
_reranker: BGEReranker | None = None


def get_reranker() -> BGEReranker:
    """获取全局 BGE Reranker 单例"""
    global _reranker
    if _reranker is None:
        _reranker = BGEReranker()
    return _reranker


def set_reranker(reranker: BGEReranker) -> None:
    """设置全局 Reranker 实例"""
    global _reranker
    _reranker = reranker
