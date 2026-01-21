"""
Research Memory Service - 研究记忆服务

支持:
- 跨会话研究延续
- 研究上下文保存
- 智能关联推荐
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型"""
    FINDING = "finding"           # 发现
    INSIGHT = "insight"           # 洞见
    QUESTION = "question"         # 问题
    HYPOTHESIS = "hypothesis"     # 假设
    CONCLUSION = "conclusion"     # 结论
    BOOKMARK = "bookmark"         # 书签
    NOTE = "note"                 # 笔记


class MemoryRelationType(str, Enum):
    """记忆关联类型"""
    SUPPORTS = "supports"         # 支持
    CONTRADICTS = "contradicts"   # 矛盾
    EXTENDS = "extends"           # 延伸
    RELATED = "related"           # 相关


@dataclass
class ResearchMemory:
    """研究记忆条目"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    source_session_id: str | None = None
    source_url: str | None = None
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    importance: float = 0.5  # 0-1
    embedding: list[float] | None = None


@dataclass
class MemoryRelation:
    """记忆关联"""
    source_id: str
    target_id: str
    relation_type: MemoryRelationType
    strength: float = 0.5  # 0-1


@dataclass
class ResearchContext:
    """研究上下文"""
    session_id: str
    query: str
    memories: list[ResearchMemory]
    key_findings: list[str]
    open_questions: list[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class ResearchMemoryService:
    """
    研究记忆服务

    管理用户的研究记忆，支持跨会话延续研究
    """

    def __init__(self):
        self._memories: dict[str, list[ResearchMemory]] = {}  # user_id -> memories
        self._relations: list[MemoryRelation] = []
        self._contexts: dict[str, ResearchContext] = {}  # session_id -> context

    def add_memory(
        self,
        user_id: str,
        memory_type: MemoryType,
        content: str,
        session_id: str | None = None,
        source_url: str | None = None,
        tags: list[str] | None = None,
        importance: float = 0.5,
    ) -> ResearchMemory:
        """
        添加研究记忆

        Args:
            user_id: 用户 ID
            memory_type: 记忆类型
            content: 内容
            session_id: 来源会话 ID
            source_url: 来源 URL
            tags: 标签
            importance: 重要性

        Returns:
            ResearchMemory: 创建的记忆
        """
        memory = ResearchMemory(
            id=str(uuid.uuid4()),
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            source_session_id=session_id,
            source_url=source_url,
            tags=tags or [],
            importance=importance,
        )

        if user_id not in self._memories:
            self._memories[user_id] = []

        self._memories[user_id].append(memory)
        return memory

    def get_memories(
        self,
        user_id: str,
        memory_type: MemoryType | None = None,
        tags: list[str] | None = None,
        limit: int = 50,
    ) -> list[ResearchMemory]:
        """
        获取用户的研究记忆

        Args:
            user_id: 用户 ID
            memory_type: 过滤类型
            tags: 过滤标签
            limit: 返回数量限制

        Returns:
            list[ResearchMemory]: 记忆列表
        """
        memories = self._memories.get(user_id, [])

        # 按类型过滤
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]

        # 按标签过滤
        if tags:
            memories = [
                m for m in memories
                if any(tag in m.tags for tag in tags)
            ]

        # 按重要性和时间排序
        memories.sort(
            key=lambda m: (m.importance, m.created_at),
            reverse=True
        )

        return memories[:limit]

    def find_related_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> list[ResearchMemory]:
        """
        根据查询找到相关记忆

        Args:
            user_id: 用户 ID
            query: 查询文本
            limit: 返回数量

        Returns:
            list[ResearchMemory]: 相关记忆列表
        """
        memories = self._memories.get(user_id, [])

        # 简单的关键词匹配（实际应使用向量搜索）
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_memories = []
        for memory in memories:
            content_lower = memory.content.lower()
            content_words = set(content_lower.split())

            # 计算词重叠率
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / len(query_words)
                scored_memories.append((memory, score))

        # 按分数排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        return [m for m, _ in scored_memories[:limit]]

    def save_context(
        self,
        session_id: str,
        query: str,
        user_id: str,
        findings: list[str],
        questions: list[str],
    ) -> ResearchContext:
        """
        保存研究上下文

        Args:
            session_id: 会话 ID
            query: 研究查询
            user_id: 用户 ID
            findings: 关键发现
            questions: 开放问题

        Returns:
            ResearchContext: 保存的上下文
        """
        # 获取相关记忆
        related_memories = self.find_related_memories(user_id, query, limit=5)

        context = ResearchContext(
            session_id=session_id,
            query=query,
            memories=related_memories,
            key_findings=findings,
            open_questions=questions,
        )

        self._contexts[session_id] = context

        # 自动将发现添加为记忆
        for finding in findings:
            self.add_memory(
                user_id=user_id,
                memory_type=MemoryType.FINDING,
                content=finding,
                session_id=session_id,
                importance=0.7,
            )

        return context

    def get_context(self, session_id: str) -> ResearchContext | None:
        """获取研究上下文"""
        return self._contexts.get(session_id)

    def get_continuation_prompt(
        self,
        user_id: str,
        new_query: str,
    ) -> dict | None:
        """
        获取研究延续提示

        检测是否与之前的研究相关，并提供延续建议

        Args:
            user_id: 用户 ID
            new_query: 新的查询

        Returns:
            dict | None: 延续提示信息
        """
        related = self.find_related_memories(user_id, new_query, limit=5)

        if not related:
            return None

        # 找到最相关的会话
        session_ids = {
            m.source_session_id for m in related
            if m.source_session_id
        }

        if not session_ids:
            return None

        # 获取相关上下文
        related_contexts = [
            self._contexts[sid] for sid in session_ids
            if sid in self._contexts
        ]

        if not related_contexts:
            return None

        # 构建延续提示
        recent_context = max(
            related_contexts,
            key=lambda c: c.created_at
        )

        return {
            "detected": True,
            "related_query": recent_context.query,
            "session_id": recent_context.session_id,
            "key_findings": recent_context.key_findings[:3],
            "open_questions": recent_context.open_questions[:2],
            "suggestion": f"这似乎与你之前关于「{recent_context.query[:30]}...」的研究相关。要继续那项研究吗？",
        }

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: MemoryRelationType,
        strength: float = 0.5,
    ) -> MemoryRelation:
        """添加记忆关联"""
        relation = MemoryRelation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=strength,
        )
        self._relations.append(relation)
        return relation

    def get_memory_graph(
        self,
        user_id: str,
        center_id: str | None = None,
        depth: int = 2,
    ) -> dict:
        """
        获取记忆图谱

        Args:
            user_id: 用户 ID
            center_id: 中心记忆 ID
            depth: 图谱深度

        Returns:
            dict: 图谱数据 (nodes, edges)
        """
        memories = self._memories.get(user_id, [])
        memory_ids = {m.id for m in memories}

        nodes = [
            {
                "id": m.id,
                "type": m.memory_type.value,
                "content": m.content[:100],
                "importance": m.importance,
            }
            for m in memories
        ]

        edges = [
            {
                "source": r.source_id,
                "target": r.target_id,
                "type": r.relation_type.value,
                "strength": r.strength,
            }
            for r in self._relations
            if r.source_id in memory_ids and r.target_id in memory_ids
        ]

        return {"nodes": nodes, "edges": edges}

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """删除记忆"""
        memories = self._memories.get(user_id, [])
        for i, m in enumerate(memories):
            if m.id == memory_id:
                memories.pop(i)
                return True
        return False

    def update_importance(
        self,
        user_id: str,
        memory_id: str,
        importance: float,
    ) -> ResearchMemory | None:
        """更新记忆重要性"""
        memories = self._memories.get(user_id, [])
        for m in memories:
            if m.id == memory_id:
                m.importance = max(0.0, min(1.0, importance))
                m.updated_at = datetime.utcnow()
                return m
        return None


# 单例
_memory_service: ResearchMemoryService | None = None


def get_research_memory_service() -> ResearchMemoryService:
    """获取研究记忆服务单例"""
    global _memory_service
    if _memory_service is None:
        _memory_service = ResearchMemoryService()
    return _memory_service
