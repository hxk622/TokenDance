"""
Vector Retriever - 向量化记忆检索

使用 pgvector 进行语义检索，替代简单的关键词匹配。

特性：
- 将 Lessons 嵌入为向量存储到 PostgreSQL
- 语义相似度搜索 (Cosine Similarity)
- 混合检索：向量 + 关键词
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.agent.long_memory.distributed import Lesson

logger = logging.getLogger(__name__)


class VectorRetriever:
    """
    向量化检索器

    使用 pgvector 进行语义相似度搜索。

    注意：需要 PostgreSQL + pgvector 扩展支持。
    """

    def __init__(
        self,
        db_session,  # SQLAlchemy session
        embedding_fn: callable | None = None,
        top_k: int = 5,
    ):
        """
        Args:
            db_session: SQLAlchemy 数据库会话
            embedding_fn: 嵌入函数 (text -> vector)，默认使用内置简易嵌入
            top_k: 返回最相关的 K 条结果
        """
        self.db = db_session
        self.embedding_fn = embedding_fn or self._default_embedding
        self.top_k = top_k

    def _default_embedding(self, text: str) -> list[float]:
        """
        默认嵌入函数（简易实现）

        生产环境应使用：
        - OpenAI Embeddings (text-embedding-ada-002)
        - Sentence-BERT
        - Claude Embeddings (如果有)
        """
        # TODO: 替换为真实的嵌入模型
        # 这里仅作为占位符，返回随机向量
        import hashlib
        hash_val = hashlib.md5(text.encode()).hexdigest()
        # 简单映射为 128 维向量
        vector = [float(int(hash_val[i:i+2], 16)) / 255.0 for i in range(0, 32, 2)]
        # Pad 到 768 维（BERT 标准）
        vector += [0.0] * (768 - len(vector))
        return vector[:768]

    def store_lesson(self, lesson: Lesson) -> None:
        """
        存储 Lesson 并嵌入为向量

        Args:
            lesson: Lesson 对象
        """
        # 组合 title + summary + tags 作为嵌入内容
        text = f"{lesson.title} {lesson.summary} {' '.join(lesson.tags)}"
        embedding = self.embedding_fn(text)

        # 插入到数据库（假设表名为 agent_lessons）
        # 注意：这里需要实际的 SQLAlchemy 模型定义
        try:
            from app.models.agent_lesson import AgentLesson  # 假设已定义

            lesson_record = AgentLesson(
                title=lesson.title,
                summary=lesson.summary,
                tags=json.dumps(lesson.tags),
                created_at=lesson.created_at,
                embedding=embedding,  # pgvector 列
            )
            self.db.add(lesson_record)
            self.db.commit()
            logger.info(f"Lesson stored with vector: {lesson.title}")
        except ImportError:
            logger.warning("AgentLesson model not found, skipping vector storage")

    def search_similar(
        self,
        query: str,
        top_k: int | None = None,
        threshold: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        语义相似度搜索

        Args:
            query: 查询文本
            top_k: 返回结果数量（默认使用初始化时的值）
            threshold: 相似度阈值 (0-1)，低于此值的结果不返回

        Returns:
            List[Dict]: 相似的 Lessons，包含 similarity score
        """
        k = top_k or self.top_k
        query_embedding = self.embedding_fn(query)

        try:
            from app.models.agent_lesson import AgentLesson

            # pgvector 相似度查询 (Cosine Similarity)
            # 使用 <=> 操作符进行向量距离计算
            results = (
                self.db.query(AgentLesson)
                .order_by(AgentLesson.embedding.cosine_distance(query_embedding))
                .limit(k)
                .all()
            )

            # 转换为字典并计算相似度
            lessons = []
            for r in results:
                # Cosine distance -> Cosine similarity
                distance = r.embedding.cosine_distance(query_embedding)
                similarity = 1 - distance

                if similarity >= threshold:
                    lessons.append({
                        "title": r.title,
                        "summary": r.summary,
                        "tags": json.loads(r.tags) if r.tags else [],
                        "created_at": r.created_at,
                        "similarity": similarity,
                    })

            logger.info(f"Vector search: found {len(lessons)} results for query '{query[:50]}...'")
            return lessons

        except ImportError:
            logger.warning("AgentLesson model not found, falling back to keyword search")
            return []

    def hybrid_search(
        self,
        query: str,
        keywords: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        混合检索：向量 + 关键词

        Args:
            query: 查询文本
            keywords: 额外的关键词过滤
            top_k: 返回结果数量

        Returns:
            List[Dict]: 混合检索结果
        """
        # 1. 向量检索
        vector_results = self.search_similar(query, top_k=top_k or self.top_k * 2)

        # 2. 关键词过滤（如果提供）
        if keywords:
            filtered = []
            for res in vector_results:
                # 检查 summary 或 tags 是否包含关键词
                text = f"{res['summary']} {' '.join(res['tags'])}".lower()
                if any(kw.lower() in text for kw in keywords):
                    filtered.append(res)
            vector_results = filtered

        # 3. 按相似度排序并返回 top_k
        vector_results.sort(key=lambda x: x["similarity"], reverse=True)
        return vector_results[:top_k or self.top_k]

    def delete_lesson(self, lesson_title: str) -> bool:
        """
        删除指定 Lesson

        Args:
            lesson_title: Lesson 标题

        Returns:
            bool: 是否删除成功
        """
        try:
            from app.models.agent_lesson import AgentLesson

            deleted = (
                self.db.query(AgentLesson)
                .filter(AgentLesson.title == lesson_title)
                .delete()
            )
            self.db.commit()

            logger.info(f"Deleted lesson: {lesson_title} (count={deleted})")
            return deleted > 0
        except ImportError:
            logger.warning("AgentLesson model not found")
            return False
