# Memory设计文档

> **核心更新 (2026-01-09)**: 集成 FileSystem 模块，实现记忆的双写策略
> - 文件系统（Source of Truth）+ 数据库（Index）
> - memory.md/learnings.md 人类可读可编辑
> - 参考：[FileSystem 模块设计](./FileSystem.md)

## 1. 核心问题

**Agent的健忘症**：
- 对话重启后丢失之前的上下文
- 无法记住用户偏好和历史决策
- 重复询问已知信息
- 无法跨Session学习和积累经验

**记忆爆炸**：
- 用户使用100个Session，每个10轮对话
- 总共1000轮历史 = 1M+ tokens
- 无法全部加载到Context

## 2. 设计原则

### 2.1 分层记忆架构

```
Layer 1: Episodic Memory (情景记忆)
- 短期工作记忆
- 来自Context-Management的摘要
- 当前Session的上下文
- 存储：PostgreSQL messages表
- 生命周期：当前Session

Layer 2: Semantic Memory (语义记忆)
- 长期结构化知识
- 用户偏好、事实、决策模式
- 跨Session持久化
- 存储：**workspace/context/memory.md（Source of Truth）** + PostgreSQL + pgvector（Index）⭐
- 生命周期：永久（可更新）

Layer 3: Procedural Memory (程序性记忆)
- 成功的Skill和工具调用模式
- 错误处理经验
- 最佳实践
- 存储：**workspace/context/learnings.md（Source of Truth）** + Skills表 + Context Graph⭐
- 生命周期：永久（可演化）
```

### 2.2 自动压缩原则

```python
# 记忆随时间自动压缩，避免爆炸

时间 t=0:   10条原始事实
时间 t=30天: 压缩为3条核心知识
时间 t=90天: 进一步压缩为1条模式

压缩策略：
- 高频访问的记忆 → 保留
- 低频且过时的记忆 → 压缩/删除
- 冲突的记忆 → 保留最新
```

### 2.3 相关性检索原则

```python
# 不加载全部记忆，根据当前任务检索相关记忆

当前任务: "帮我生成一份市场分析PPT"

检索逻辑:
1. 向量检索：embedding(query) → 相关记忆Top-K
2. 过滤：时间衰减 + 重要性权重
3. 返回：最相关的5-10条记忆

结果:
- "用户偏好蓝色配色方案"
- "用户之前做过类似的竞品分析"
- "用户的公司是科技行业"
```

## 3. 数据模型

### 3.1 核心表结构

```sql
-- 用户记忆表（Semantic Memory）
CREATE TABLE user_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 记忆类型
    memory_type TEXT NOT NULL,  -- preference/fact/pattern/skill
    
    -- 记忆内容
    content TEXT NOT NULL,  -- 自然语言描述
    structured_data JSONB,  -- 结构化数据
    
    -- 向量嵌入（用于检索）
    embedding vector(1536),
    
    -- 元数据
    source_session_id UUID,  -- 来源Session
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 重要性和时间衰减
    importance_score FLOAT DEFAULT 0.5,  -- 0-1
    access_count INT DEFAULT 0,  -- 访问次数
    last_accessed_at TIMESTAMPTZ,
    
    -- 状态
    is_active BOOLEAN DEFAULT TRUE,
    confidence FLOAT DEFAULT 1.0,  -- 置信度
    
    -- 索引
    INDEX idx_memories_user (user_id),
    INDEX idx_memories_type (memory_type),
    INDEX idx_memories_active (is_active, importance_score DESC)
);

-- 向量索引
CREATE INDEX idx_memories_embedding ON user_memories 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 记忆关系表（用于关联多个记忆）
CREATE TABLE memory_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_memory_id UUID NOT NULL REFERENCES user_memories(id),
    target_memory_id UUID NOT NULL REFERENCES user_memories(id),
    relation_type TEXT NOT NULL,  -- supports/contradicts/refines
    strength FLOAT DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_relations_source (source_memory_id),
    INDEX idx_relations_target (target_memory_id)
);
```

### 3.2 记忆类型定义

```python
# packages/core/memory/types.py

from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MemoryType(str, Enum):
    """记忆类型"""
    PREFERENCE = "preference"  # 用户偏好
    FACT = "fact"              # 事实性知识
    PATTERN = "pattern"        # 行为模式
    SKILL = "skill"            # 技能/最佳实践

class Memory(BaseModel):
    """记忆对象"""
    id: str
    user_id: str
    memory_type: MemoryType
    content: str
    structured_data: Optional[Dict[str, Any]] = None
    embedding: Optional[list[float]] = None
    
    # 元数据
    source_session_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 重要性
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None
    
    # 状态
    is_active: bool = True
    confidence: float = 1.0

# 记忆示例
MEMORY_EXAMPLES = {
    "preference": Memory(
        memory_type=MemoryType.PREFERENCE,
        content="用户偏好使用蓝色配色方案",
        structured_data={
            "category": "design",
            "key": "color_scheme",
            "value": "blue"
        }
    ),
    "fact": Memory(
        memory_type=MemoryType.FACT,
        content="用户的公司名称是'TechCorp'，主营AI产品",
        structured_data={
            "entity": "company",
            "name": "TechCorp",
            "industry": "AI"
        }
    ),
    "pattern": Memory(
        memory_type=MemoryType.PATTERN,
        content="用户通常在周一上午9-11点使用Agent做周报",
        structured_data={
            "activity": "weekly_report",
            "time_pattern": {
                "day_of_week": "monday",
                "hours": [9, 10, 11]
            }
        }
    ),
    "skill": Memory(
        memory_type=MemoryType.SKILL,
        content="Deep Research任务：先web_search → read_url → summarize",
        structured_data={
            "skill_name": "deep_research",
            "workflow": [
                {"step": 1, "tool": "web_search"},
                {"step": 2, "tool": "read_url"},
                {"step": 3, "tool": "summarize"}
            ]
        }
    )
}
```

## 4. 核心组件

### 4.1 MemoryManager

```python
# packages/core/memory/manager.py

from typing import List, Optional
import numpy as np

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, user_id: str, db, vector_db, llm, file_manager):
        self.user_id = user_id
        self.db = db
        self.vector_db = vector_db
        self.llm = llm
        self.file_manager = file_manager  # FileManager 实例（参考 FileSystem.md）
    
    # ===== 记忆提取 =====
    
    async def extract_from_conversation(
        self, 
        session_id: str
    ) -> List[Memory]:
        """
        从对话中提取记忆
        
        触发时机：
        1. Session结束时
        2. Context摘要生成时
        3. 用户显式保存时
        """
        # 1. 获取Session摘要
        summary = await self.db.get_latest_summary(session_id)
        if not summary:
            return []
        
        # 2. 调用LLM提取记忆
        memories = await self._llm_extract_memories(summary)
        
        # 3. 保存到数据库
        saved_memories = []
        for mem in memories:
            saved = await self.save_memory(mem)
            saved_memories.append(saved)
        
        return saved_memories
    
    async def _llm_extract_memories(
        self, 
        summary
    ) -> List[Memory]:
        """使用LLM从摘要中提取记忆"""
        
        prompt = f"""
从以下对话摘要中提取用户的长期记忆。

摘要：
{summary.summary_text}

提取以下类型的记忆：
1. preference: 用户偏好（颜色、风格、工具等）
2. fact: 事实性知识（公司名称、项目信息等）
3. pattern: 行为模式（使用习惯、工作流程等）
4. skill: 技能模式（成功的工具调用序列）

返回JSON数组：
[
  {{
    "memory_type": "preference",
    "content": "用户偏好...",
    "structured_data": {{}},
    "importance_score": 0.8
  }},
  ...
]

注意：
- 只提取值得长期记住的信息
- 临时性信息（如今天的天气）不提取
- 每条记忆应独立、明确、可验证
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            response_format="json"
        )
        
        memories_data = json.loads(response.content)
        
        return [
            Memory(
                user_id=self.user_id,
                source_session_id=summary.session_id,
                **mem_data
            )
            for mem_data in memories_data
        ]
    
    # ===== 记忆存储 =====
    
    async def save_memory(self, memory: Memory) -> Memory:
        """保存记忆"""
        
        # 1. 生成Embedding
        memory.embedding = await self._generate_embedding(memory.content)
        
        # 2. 检查是否已存在相似记忆
        similar = await self.find_similar_memories(
            memory.content,
            threshold=0.95
        )
        
        if similar:
            # 合并或更新已有记忆
            existing = similar[0]
            updated = await self._merge_or_update(existing, memory)
            return updated
        
        # 3. 保存新记忆
        memory_id = await self.db.create_memory(
            user_id=self.user_id,
            memory_type=memory.memory_type,
            content=memory.content,
            structured_data=memory.structured_data,
            embedding=memory.embedding,
            source_session_id=memory.source_session_id,
            importance_score=memory.importance_score
        )
        
        memory.id = memory_id
        return memory
    
    async def _merge_or_update(
        self, 
        existing: Memory, 
        new: Memory
    ) -> Memory:
        """合并或更新记忆"""
        
        # 调用LLM判断如何处理
        prompt = f"""
已存在的记忆：
{existing.content}

新记忆：
{new.content}

请判断如何处理：
1. replace: 新记忆更准确，替换旧记忆
2. merge: 合并两者，生成综合记忆
3. keep_both: 两者都有价值，保留两条

返回JSON：
{{
  "action": "replace|merge|keep_both",
  "reason": "原因",
  "merged_content": "如果action=merge，这里是合并后的内容"
}}
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            response_format="json"
        )
        
        result = json.loads(response.content)
        
        if result["action"] == "replace":
            # 替换
            await self.db.update_memory(
                memory_id=existing.id,
                content=new.content,
                structured_data=new.structured_data,
                confidence=new.confidence
            )
            return new
        
        elif result["action"] == "merge":
            # 合并
            merged_content = result["merged_content"]
            await self.db.update_memory(
                memory_id=existing.id,
                content=merged_content,
                confidence=(existing.confidence + new.confidence) / 2
            )
            existing.content = merged_content
            return existing
        
        else:
            # 保留两条
            new_id = await self.db.create_memory(...)
            new.id = new_id
            return new
    
    # ===== 记忆检索 =====
    
    async def retrieve_relevant_memories(
        self, 
        query: str,
        k: int = 10,
        memory_types: Optional[List[MemoryType]] = None
    ) -> List[Memory]:
        """
        检索相关记忆
        
        策略：向量检索 + 时间衰减 + 重要性加权
        """
        
        # 1. 向量检索
        query_embedding = await self._generate_embedding(query)
        
        candidates = await self.vector_db.search(
            table="user_memories",
            query_vector=query_embedding,
            filter={
                "user_id": self.user_id,
                "is_active": True
            },
            limit=k * 2  # 多检索一些候选
        )
        
        # 2. 重新排序（考虑时间衰减和重要性）
        scored_memories = []
        for mem in candidates:
            score = self._calculate_relevance_score(
                mem,
                cosine_similarity=mem.similarity_score
            )
            scored_memories.append((score, mem))
        
        # 3. 排序并返回Top-K
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        top_memories = [mem for score, mem in scored_memories[:k]]
        
        # 4. 更新访问统计
        for mem in top_memories:
            await self.db.increment_access_count(mem.id)
        
        return top_memories
    
    def _calculate_relevance_score(
        self, 
        memory: Memory,
        cosine_similarity: float
    ) -> float:
        """
        计算记忆相关性得分
        
        Score = cosine_similarity × time_decay × importance
        """
        
        # 时间衰减（exponential decay）
        days_since_access = (
            datetime.now() - memory.last_accessed_at
        ).days if memory.last_accessed_at else 365
        
        time_decay = np.exp(-days_since_access / 30)  # 30天半衰期
        
        # 综合得分
        score = (
            cosine_similarity * 0.6 +
            time_decay * 0.2 +
            memory.importance_score * 0.2
        )
        
        return score
    
    async def find_similar_memories(
        self, 
        content: str,
        threshold: float = 0.9
    ) -> List[Memory]:
        """查找相似记忆（用于去重）"""
        
        embedding = await self._generate_embedding(content)
        
        similar = await self.vector_db.search(
            table="user_memories",
            query_vector=embedding,
            filter={"user_id": self.user_id},
            limit=5
        )
        
        return [
            mem for mem in similar 
            if mem.similarity_score >= threshold
        ]
    
    # ===== 记忆压缩 =====
    
    async def compress_old_memories(self, days_threshold: int = 90):
        """
        压缩旧记忆
        
        策略：
        - 低频访问且过时的记忆 → 归档/删除
        - 相似记忆 → 合并
        """
        
        # 1. 找出低频访问的旧记忆
        old_memories = await self.db.get_memories(
            user_id=self.user_id,
            days_since_access_gt=days_threshold,
            access_count_lt=5
        )
        
        # 2. 按类型分组
        grouped = {}
        for mem in old_memories:
            key = mem.memory_type
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(mem)
        
        # 3. 每组压缩
        for memory_type, memories in grouped.items():
            await self._compress_memory_group(memory_type, memories)
    
    async def _compress_memory_group(
        self, 
        memory_type: MemoryType,
        memories: List[Memory]
    ):
        """压缩一组记忆"""
        
        if len(memories) < 3:
            return  # 太少，不压缩
        
        # 调用LLM提取共性
        prompt = f"""
以下是{len(memories)}条{memory_type}类型的旧记忆：

{chr(10).join(f"{i+1}. {m.content}" for i, m in enumerate(memories))}

请将它们压缩为1-3条核心记忆，保留最重要的信息。

返回JSON数组：
[
  {{
    "content": "压缩后的记忆内容",
    "importance_score": 0.8,
    "source_memory_ids": ["id1", "id2"]
  }}
]
"""
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            response_format="json"
        )
        
        compressed = json.loads(response.content)
        
        # 保存压缩后的记忆
        for comp in compressed:
            await self.save_memory(Memory(
                user_id=self.user_id,
                memory_type=memory_type,
                content=comp["content"],
                importance_score=comp["importance_score"]
            ))
        
        # 归档原始记忆
        for mem in memories:
            await self.db.archive_memory(mem.id)
    
    # ===== 工具方法 =====
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """生成文本Embedding"""
        return await self.llm.embed(text)
```

### 4.2 与Agent集成

```python
# packages/core/agent/agent_with_memory.py

class AgentWithMemory:
    """带记忆的Agent"""
    
    def __init__(self, user_id: str, memory_manager: MemoryManager):
        self.user_id = user_id
        self.memory = memory_manager
    
    async def run(self, user_message: str, context: dict):
        """
        执行Agent推理
        
        流程：
        1. 检索相关记忆
        2. 增强Context
        3. 执行推理
        4. 提取新记忆
        """
        
        # 1. 检索相关记忆
        relevant_memories = await self.memory.retrieve_relevant_memories(
            query=user_message,
            k=10
        )
        
        # 2. 增强Context
        if relevant_memories:
            memory_context = self._format_memories_for_context(
                relevant_memories
            )
            context["user_memory"] = memory_context
        
        # 3. 构建System Prompt
        system_prompt = self._build_system_prompt(context)
        
        # 4. 调用LLM
        response = await self.llm.generate(
            system=system_prompt,
            messages=context["messages"]
        )
        
        return response
    
    def _format_memories_for_context(
        self, 
        memories: List[Memory]
    ) -> str:
        """格式化记忆用于Context"""
        
        grouped = {
            "preferences": [],
            "facts": [],
            "patterns": [],
            "skills": []
        }
        
        for mem in memories:
            if mem.memory_type == MemoryType.PREFERENCE:
                grouped["preferences"].append(mem.content)
            elif mem.memory_type == MemoryType.FACT:
                grouped["facts"].append(mem.content)
            elif mem.memory_type == MemoryType.PATTERN:
                grouped["patterns"].append(mem.content)
            elif mem.memory_type == MemoryType.SKILL:
                grouped["skills"].append(mem.content)
        
        sections = []
        
        if grouped["preferences"]:
            sections.append("## User Preferences\n" + "\n".join(
                f"- {p}" for p in grouped["preferences"]
            ))
        
        if grouped["facts"]:
            sections.append("## Known Facts\n" + "\n".join(
                f"- {f}" for f in grouped["facts"]
            ))
        
        if grouped["patterns"]:
            sections.append("## User Patterns\n" + "\n".join(
                f"- {p}" for p in grouped["patterns"]
            ))
        
        if grouped["skills"]:
            sections.append("## Proven Skills\n" + "\n".join(
                f"- {s}" for s in grouped["skills"]
            ))
        
        return "# USER MEMORY\n\n" + "\n\n".join(sections)
    
    def _build_system_prompt(self, context: dict) -> str:
        """构建System Prompt"""
        
        parts = [
            "You are an AI assistant with long-term memory.",
            ""
        ]
        
        # 添加记忆
        if "user_memory" in context:
            parts.append(context["user_memory"])
            parts.append("")
        
        # 添加对话摘要
        if context.get("summary"):
            parts.append(context["summary"])
            parts.append("")
        
        # 添加指令
        parts.append("Use the user memory to personalize your responses.")
        parts.append("If information conflicts, ask the user for clarification.")
        
        return "\n".join(parts)
```

## 5. 与其他模块集成

### 5.1 与Context-Management集成
```python
# 从对话摘要中提取记忆

class ConversationManager:
    async def _on_summary_created(self, summary):
        """摘要创建后触发记忆提取"""
        memories = await self.memory_mgr.extract_from_conversation(
            summary.session_id
        )
        logger.info(f"Extracted {len(memories)} memories")
```

### 5.2 与Context Graph集成
```python
# Context Graph记录记忆访问轨迹

class MemoryManager:
    async def retrieve_relevant_memories(self, query: str):
        memories = await self._do_retrieval(query)
        
        # 记录到Context Graph
        await self.context_graph.record_memory_access(
            query=query,
            retrieved_memory_ids=[m.id for m in memories]
        )
        
        return memories
```

### 5.3 与Skill系统集成
```python
# 成功的Skill调用序列存为Procedural Memory

class SkillExecutor:
    async def after_skill_success(self, skill_name: str, workflow: list):
        """Skill成功后记录为记忆"""
        await self.memory_mgr.save_memory(Memory(
            memory_type=MemoryType.SKILL,
            content=f"Skill '{skill_name}' 成功执行",
            structured_data={
                "skill_name": skill_name,
                "workflow": workflow
            },
            importance_score=0.7
        ))
```

## 6. 性能优化

### 6.1 向量索引优化
```sql
-- 使用IVFFlat索引加速检索
CREATE INDEX CONCURRENTLY idx_memories_embedding 
ON user_memories 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 分析表以优化查询计划
ANALYZE user_memories;
```

### 6.2 缓存热点记忆
```python
class MemoryManager:
    def __init__(self, user_id: str, redis: RedisClient):
        self.user_id = user_id
        self.redis = redis
        self.cache_key = f"user:{user_id}:hot_memories"
    
    async def get_hot_memories(self) -> List[Memory]:
        """获取高频访问的热点记忆"""
        cached = await self.redis.get(self.cache_key)
        if cached:
            return json.loads(cached)
        
        # 查询高频记忆
        hot = await self.db.get_memories(
            user_id=self.user_id,
            order_by="access_count DESC",
            limit=20
        )
        
        # 缓存1小时
        await self.redis.setex(
            self.cache_key,
            3600,
            json.dumps([m.dict() for m in hot])
        )
        
        return hot
```

## 7. 监控与调试

```python
# packages/core/memory/metrics.py

class MemoryMetrics:
    async def collect(self, user_id: str) -> dict:
        return {
            "total_memories": await self.db.count_memories(user_id),
            "by_type": await self.db.count_by_type(user_id),
            "avg_importance": await self.db.avg_importance(user_id),
            "retrieval_latency_p50": ...,
            "retrieval_latency_p99": ...,
            "cache_hit_rate": ...
        }
```

## 8. 总结

**核心价值**：
1. 跨Session持久化用户信息
2. 个性化Agent响应
3. 减少重复询问
4. 积累经验和最佳实践

**关键技术**：
1. 分层记忆架构（Episodic/Semantic/Procedural）
2. 向量检索 + 时间衰减 + 重要性加权
3. 自动提取 + 合并 + 压缩
4. 与Context管理、Context Graph深度集成
