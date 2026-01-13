# KV-Cache 高级设计文档

> **核心理念**：将 KV-Cache 从"加速工具"升级为"Agent 长期记忆"和"多任务切换器"
> Version: 1.0.0
> Last Updated: 2026-01-09

## 1. 设计哲学

### 1.1 超越传统：从单一缓存到基础设施

**传统 Agent 的局限**：
```
一个对话 = 一个独立的 KV-Cache
多个 Agent 实例 = 重复的内存占用
任务切换 = 重新计算全部 Context
```

**TokenDance 的突破**：
```
KV-Cache 不再是"优化手段"，而是：
1. Agent 的长期记忆存储
2. 多任务的高速切换器
3. 专家知识的即时加载器
```

### 1.2 核心设计原则

| 原则 | 说明 | 价值 |
|------|------|------|
| **层次化共享** | 三层缓存架构，从全局到会话 | 节省 90% 显存 |
| **分支探索** | 支持多路径并行探索和秒级回滚 | 允许试错，不浪费算力 |
| **持久化记忆** | 缓存可保存到磁盘，支持无感唤醒 | Agent 永不失忆 |
| **预置智慧** | 思维快照库，预装专家推理链路 | 极速响应复杂任务 |

---

## 2. 层次化缓存架构（Layered KV-Cache）

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│  层次化 KV-Cache 架构                                            │
│                                                                  │
│  Layer 1: Global Static Prefix (全局静态前缀)                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 所有工具定义 (Browser, Python, Shell, MCP)           │     │
│  │ • FSM 状态定义                                          │     │
│  │ • 核心行为规范                                          │     │
│  │ • 生命周期: 系统冷启动时预计算，永不变化               │     │
│  │ • 共享机制: Copy-on-Write，所有 Agent 共享一份物理内存  │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 挂载                                   │
│  Layer 2: Domain-Specific Modules (任务领域模块)                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • Skill-Aware Cache: 与 Skill 系统深度绑定             │     │
│  │ • 懒加载: 第一次使用时预计算，之后复用                  │     │
│  │ • 示例: "数据分析专家"、"代码重构专家"                  │     │
│  │ • 生命周期: Skill 激活时挂载，任务结束后卸载            │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 追加                                   │
│  Layer 3: Session-Specific Delta (会话动态层)                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 用户指令、Agent 推理、工具返回结果                     │     │
│  │ • Radix Tree 管理: 自动识别公共前缀，多会话共享         │     │
│  │ • Append-Only: 只追加，永不修改                         │     │
│  │ • 生命周期: 会话期间持续增长，休眠后可持久化到磁盘      │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 1: 全局静态前缀（Global Static Prefix）

### 3.1 设计目标

**核心价值**：
- 无论运行 100 个还是 1000 个 Agent 实例，物理内存中只存在一份静态前缀
- 首字延迟几乎为 0（预计算完成）
- 节省 80-90% 的显存占用

### 3.2 实现方案

```python
# backend/app/kv_cache/static_prefix.py

from typing import Optional
import asyncio
from pathlib import Path

class GlobalStaticPrefix:
    """全局静态前缀管理器（单例模式）"""
    
    _instance = None
    _kv_cache_snapshot = None
    _is_initialized = False
    _init_lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize(self, llm_client):
        """
        系统冷启动时预计算静态前缀
        
        调用时机：
        - 服务器启动时
        - 新增工具后（需要重新计算）
        """
        if self._is_initialized:
            return
        
        async with self._init_lock:
            # Double-check locking
            if self._is_initialized:
                return
            
            # 1. 构建静态前缀 Prompt
            static_prompt = self._build_static_prompt()
            
            print(f"📊 Initializing Global Static Prefix ({len(static_prompt)} chars)...")
            
            # 2. 预计算 KV-Cache（只生成 Cache，不生成输出）
            self._kv_cache_snapshot = await llm_client.prefill_only(
                messages=[{"role": "system", "content": static_prompt}],
                return_cache=True  # 只返回 KV-Cache
            )
            
            self._is_initialized = True
            
            # 3. 统计信息
            cache_size_mb = self._kv_cache_snapshot.memory_size / 1024 / 1024
            print(f"✅ Global Static Prefix initialized: {cache_size_mb:.2f} MB")
    
    def _build_static_prompt(self) -> str:
        """
        构建静态前缀（所有工具定义 + 核心规则）
        
        包含：
        - 所有工具的完整定义（Browser, Python, Shell, MCP）
        - FSM 状态机定义
        - 核心行为规范
        - 结构化标记系统
        """
        return f"""<|SYSTEM|>
你是 TokenDance，一个通用 AI Agent 平台。

<|TOOLS|>
{self._load_all_tool_definitions()}

<|FSM_STATES|>
{self._load_fsm_definitions()}

<|CORE_RULES|>
{self._load_core_rules()}

<|STRUCTURED_TAGS|>
- <|REASONING|>: Agent 推理过程
- <|TOOL_CALL|>: 工具调用
- <|TOOL_RESULT|>: 工具返回结果
- <|FINAL_ANSWER|>: 最终答案
"""
    
    def _load_all_tool_definitions(self) -> str:
        """加载所有工具定义"""
        from backend.app.tools.registry import tool_registry
        return tool_registry.get_all_tool_definitions()
    
    def _load_fsm_definitions(self) -> str:
        """加载 FSM 状态定义"""
        return """
状态机定义：
- INIT: 初始化
- PLANNING: 规划
- EXECUTING: 执行中
- WAITING: 等待工具返回
- REFLECTING: 反思
- COMPLETED: 完成
"""
    
    def _load_core_rules(self) -> str:
        """加载核心行为规范"""
        return """
1. 每次推理前必须先思考（<|REASONING|>）
2. 调用工具前必须说明原因
3. 收到错误后必须进行反思
4. 高风险操作必须 HITL 确认
"""
    
    def get_cache_snapshot(self) -> 'KVCache':
        """
        返回只读的 Cache 快照（Copy-on-Write）
        
        每个 Agent 实例调用此方法时，返回一个轻量级的 fork 副本。
        物理内存中只有一份，通过 Copy-on-Write 机制共享。
        """
        if not self._is_initialized:
            raise RuntimeError("Global Static Prefix not initialized. Call initialize() first.")
        
        return self._kv_cache_snapshot.fork()
    
    def invalidate(self):
        """使缓存失效（工具定义变更时调用）"""
        self._is_initialized = False
        self._kv_cache_snapshot = None
        print("⚠️  Global Static Prefix invalidated. Need re-initialization.")


# 使用示例：在服务器启动时初始化
async def startup_event():
    """FastAPI 启动事件"""
    from backend.app.llm.client import llm_client
    
    global_prefix = GlobalStaticPrefix.get_instance()
    await global_prefix.initialize(llm_client)
```

### 3.3 Copy-on-Write 机制

```python
# backend/app/kv_cache/cow.py

class KVCache:
    """KV-Cache 数据结构（支持 Copy-on-Write）"""
    
    def __init__(self, keys, values, metadata=None):
        self.keys = keys      # Tensor: (batch, num_heads, seq_len, head_dim)
        self.values = values  # Tensor: (batch, num_heads, seq_len, head_dim)
        self.metadata = metadata or {}
        self._is_fork = False
        self._parent = None
    
    def fork(self) -> 'KVCache':
        """
        创建 Fork 副本（Copy-on-Write）
        
        原理：
        - 不复制 Tensor 数据，只复制引用
        - 标记为 fork 状态
        - 第一次修改时才触发真正的复制（由 PyTorch 自动处理）
        """
        forked = KVCache(
            keys=self.keys,      # 共享引用
            values=self.values,  # 共享引用
            metadata=self.metadata.copy()
        )
        forked._is_fork = True
        forked._parent = self
        return forked
    
    @property
    def memory_size(self) -> int:
        """计算内存占用（字节）"""
        keys_size = self.keys.element_size() * self.keys.nelement()
        values_size = self.values.element_size() * self.values.nelement()
        return keys_size + values_size
    
    def to_dict(self) -> dict:
        """序列化为字典（用于持久化）"""
        return {
            "keys": self.keys.cpu().numpy(),
            "values": self.values.cpu().numpy(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict, device: str = "cuda") -> 'KVCache':
        """从字典反序列化"""
        import torch
        return cls(
            keys=torch.from_numpy(data["keys"]).to(device),
            values=torch.from_numpy(data["values"]).to(device),
            metadata=data["metadata"]
        )
```

---

## 4. Layer 2: 任务领域模块（Skill-Aware Cache）

### 4.1 设计目标

**核心价值**：
- 与 Skill 系统深度绑定，自动识别任务类型并挂载相应的专家知识
- 懒加载：第一次使用时预计算，之后所有实例复用
- 层次化构建：Global Cache → Skill Cache → Session Cache

### 4.2 实现方案

```python
# backend/app/kv_cache/skill_cache.py

from typing import Dict, Optional
import asyncio

class SkillCacheManager:
    """技能相关的 KV-Cache 管理器"""
    
    def __init__(self):
        self.skill_caches: Dict[str, KVCache] = {}  # skill_name -> KVCache
        self._cache_lock = asyncio.Lock()
        self._skill_embeddings: Dict[str, list] = {}  # 用于快速匹配
    
    async def get_or_create_skill_cache(
        self,
        skill_name: str,
        llm_client
    ) -> KVCache:
        """
        获取或创建 Skill 的 KV-Cache
        
        流程：
        1. 如果缓存存在，直接返回 fork
        2. 否则加载 Skill L2 指令并预计算
        3. 基于 Global Prefix 构建，避免重复计算
        """
        # 快速路径：缓存命中
        if skill_name in self.skill_caches:
            return self.skill_caches[skill_name].fork()
        
        # 慢速路径：创建新缓存
        async with self._cache_lock:
            # Double-check locking
            if skill_name in self.skill_caches:
                return self.skill_caches[skill_name].fork()
            
            print(f"🔧 Creating Skill Cache for: {skill_name}")
            
            # 1. 加载 Skill 的 L2 指令
            skill_instructions = await self._load_skill_l2(skill_name)
            
            # 2. 获取 Global Cache 作为基础
            global_cache = GlobalStaticPrefix.get_instance().get_cache_snapshot()
            
            # 3. 在 Global Cache 基础上追加 Skill 指令
            skill_cache = await llm_client.prefill_only(
                messages=[{"role": "system", "content": skill_instructions}],
                cache_prefix=global_cache  # 关键：基于 Global Cache 追加
            )
            
            # 4. 缓存起来
            self.skill_caches[skill_name] = skill_cache
            
            # 5. 计算 embedding（用于快速匹配）
            self._skill_embeddings[skill_name] = await self._compute_embedding(
                skill_instructions
            )
            
            cache_size_mb = skill_cache.memory_size / 1024 / 1024
            print(f"✅ Skill Cache created: {skill_name} ({cache_size_mb:.2f} MB)")
            
            return skill_cache.fork()
    
    async def _load_skill_l2(self, skill_name: str) -> str:
        """
        加载 Skill 的 L2 指令
        
        从 skills/{skill_name}/SKILL.md 中提取 L2 部分
        """
        from backend.app.skills.loader import skill_loader
        
        skill_metadata = skill_loader.get_skill(skill_name)
        if not skill_metadata:
            raise ValueError(f"Skill not found: {skill_name}")
        
        # 加载 L2 指令
        l2_instructions = await skill_loader.load_l2(skill_name)
        
        return f"""<|SKILL:{skill_name}|>
{l2_instructions}
"""
    
    async def _compute_embedding(self, text: str) -> list:
        """计算文本 embedding（用于快速匹配）"""
        from backend.app.llm.embedding import embedding_client
        return await embedding_client.embed(text)
    
    async def _store_skill_embedding_to_milvus(self, skill_name: str, embedding: list):
        """将 Skill embedding 存储到 Milvus"""
        from backend.app.vector_db.milvus_client import milvus_client
        
        await milvus_client.insert(
            collection_name="skill_embeddings",
            data=[{
                "skill_name": skill_name,
                "embedding": embedding,
                "created_at": datetime.now().isoformat()
            }]
        )
    
    async def match_best_skill(self, user_query: str) -> Optional[str]:
        """
        根据用户查询匹配最适合的 Skill
        
        使用 Milvus 向量相似度搜索
        """
        from backend.app.llm.embedding import embedding_client
        from backend.app.vector_db.milvus_client import milvus_client
        
        # 1. 计算查询的 embedding
        query_embedding = await embedding_client.embed(user_query)
        
        # 2. 在 Milvus 中搜索最相似的 Skill
        results = await milvus_client.search(
            collection_name="skill_embeddings",
            query_vectors=[query_embedding],
            limit=1,
            output_fields=["skill_name"]
        )
        
        if not results or len(results[0]) == 0:
            return None
        
        # 3. 获取最佳匹配
        best_match = results[0][0]
        best_skill = best_match.entity.get("skill_name")
        best_score = best_match.distance  # Milvus 返回的相似度分数
        
        # 4. 阈值过滤
        if best_score > 0.65:  # 相似度阈值
            print(f"🎯 Matched Skill: {best_skill} (score: {best_score:.2f})")
            return best_skill
        
        return None
    
    def invalidate_skill(self, skill_name: str):
        """使 Skill Cache 失效（Skill 更新时调用）"""
        if skill_name in self.skill_caches:
            del self.skill_caches[skill_name]
            del self._skill_embeddings[skill_name]
            print(f"⚠️  Skill Cache invalidated: {skill_name}")


# 使用示例：Agent 执行时自动匹配和加载
class AgentExecutor:
    async def execute(self, user_query: str):
        """执行用户查询"""
        
        # 1. 自动匹配最适合的 Skill
        skill_name = await self.skill_cache_mgr.match_best_skill(user_query)
        
        # 2. 加载 Skill Cache（基于 Global Cache）
        if skill_name:
            self.current_cache = await self.skill_cache_mgr.get_or_create_skill_cache(
                skill_name,
                self.llm_client
            )
        else:
            # 使用通用 Cache（只有 Global Prefix）
            self.current_cache = GlobalStaticPrefix.get_instance().get_cache_snapshot()
        
        # 3. 基于 Cache 生成响应
        response = await self.llm_client.generate(
            messages=[{"role": "user", "content": user_query}],
            cache=self.current_cache
        )
        
        return response
```

### 4.3 与 Skill 系统集成

```python
# backend/app/skills/loader.py

class SkillLoader:
    async def load_l2_with_cache_hint(self, skill_name: str) -> tuple:
        """
        加载 L2 指令，并返回是否应该缓存的提示
        
        返回：(l2_instructions, should_cache)
        """
        l2_instructions = await self.load_l2(skill_name)
        
        # 判断是否应该缓存：
        # - L2 指令较长（> 1000 tokens）
        # - 高频使用的 Skill（从统计数据判断）
        should_cache = (
            len(l2_instructions) > 5000 or
            self.get_usage_count(skill_name) > 10
        )
        
        return l2_instructions, should_cache
```

---

## 5. Layer 3: 会话动态层（Radix Tree）

### 5.1 设计目标

**核心价值**：
- 自动识别多个会话的公共前缀，共享 KV-Cache
- Append-Only：只追加，永不修改，保证 KV-Cache 持续有效
- LRU 淘汰：内存不足时自动淘汰最久未使用的节点

### 5.2 Radix Tree 数据结构

```python
# backend/app/kv_cache/radix_tree.py

from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RadixNode:
    """Radix Tree 节点"""
    key: str                    # 节点的 Key（消息序列的 Hash）
    cache: Optional[KVCache]    # 对应的 KV-Cache
    children: dict              # 子节点：prefix -> RadixNode
    access_time: datetime       # 最后访问时间（用于 LRU）
    ref_count: int = 0          # 引用计数


class RadixTree:
    """
    Radix Tree 用于管理会话级 KV-Cache
    
    原理：
    - 如果两个会话前 N 个消息相同，它们共享这部分的 Cache
    - 使用前缀树结构自动识别公共前缀
    """
    
    def __init__(self, max_nodes: int = 1000):
        self.root = RadixNode(key="", cache=None, children={}, access_time=datetime.now())
        self.max_nodes = max_nodes
        self.node_count = 0
    
    def insert(self, key: str, cache: KVCache):
        """
        插入一个 Key-Cache 对
        
        如果 Key 有公共前缀，自动共享前缀部分的 Cache
        """
        node = self.root
        
        for char in key:
            if char not in node.children:
                node.children[char] = RadixNode(
                    key=char,
                    cache=None,
                    children={},
                    access_time=datetime.now()
                )
                self.node_count += 1
                
                # 检查是否需要淘汰
                if self.node_count > self.max_nodes:
                    self._evict_lru()
            
            node = node.children[char]
            node.access_time = datetime.now()
        
        # 在叶子节点存储 Cache
        node.cache = cache
    
    def longest_prefix_match(self, key: str) -> Tuple[Optional[RadixNode], int]:
        """
        查找最长公共前缀
        
        返回：(匹配的节点, 匹配的长度)
        """
        node = self.root
        matched_length = 0
        last_cache_node = None
        
        for i, char in enumerate(key):
            if char not in node.children:
                break
            
            node = node.children[char]
            node.access_time = datetime.now()
            matched_length = i + 1
            
            if node.cache is not None:
                last_cache_node = node
        
        return last_cache_node, matched_length
    
    def _evict_lru(self):
        """淘汰最久未使用的节点（LRU）"""
        # 遍历树找到最久未使用的叶子节点
        oldest_node = self._find_oldest_leaf(self.root)
        if oldest_node:
            self._remove_node(oldest_node)
            self.node_count -= 1
    
    def _find_oldest_leaf(self, node: RadixNode) -> Optional[RadixNode]:
        """递归查找最久未使用的叶子节点"""
        if not node.children:
            return node
        
        oldest = None
        for child in node.children.values():
            candidate = self._find_oldest_leaf(child)
            if candidate and (oldest is None or candidate.access_time < oldest.access_time):
                oldest = candidate
        
        return oldest
    
    def _remove_node(self, node: RadixNode):
        """移除节点"""
        # 释放 Cache
        if node.cache:
            del node.cache
        # 清空子节点
        node.children.clear()
```

### 5.3 会话缓存管理器

```python
# backend/app/kv_cache/session_cache.py

import hashlib
import json
from typing import List

class SessionCacheManager:
    """会话级 KV-Cache 管理器"""
    
    def __init__(self, skill_cache_mgr: SkillCacheManager):
        self.radix_tree = RadixTree(max_nodes=1000)
        self.skill_cache_mgr = skill_cache_mgr
    
    async def get_cache_for_session(
        self,
        session_id: str,
        messages: List[dict],
        skill_name: Optional[str],
        llm_client
    ) -> KVCache:
        """
        获取会话的 KV-Cache
        
        流程：
        1. 计算消息序列的 Hash Key
        2. 在 Radix Tree 中查找最长公共前缀
        3. 如果完全命中，直接返回
        4. 如果部分命中，只计算差异部分
        5. 如果完全不命中，基于 Skill Cache 计算
        """
        # 1. 计算消息序列的 Key
        message_key = self._compute_message_key(messages)
        
        # 2. 查找最长公共前缀
        cached_node, cached_length = self.radix_tree.longest_prefix_match(message_key)
        
        # 3. 完全命中
        if cached_node and cached_length == len(message_key):
            print(f"✅ KV-Cache hit: {cached_length} messages")
            return cached_node.cache.fork()
        
        # 4. 部分命中
        if cached_node and cached_length > 0:
            print(f"🔶 KV-Cache partial hit: {cached_length}/{len(messages)} messages")
            
            # 只计算差异部分
            delta_messages = messages[cached_length:]
            new_cache = await llm_client.prefill_only(
                messages=delta_messages,
                cache_prefix=cached_node.cache
            )
        else:
            # 5. 完全不命中
            print(f"❌ KV-Cache miss, computing from scratch")
            
            # 基于 Skill Cache 计算
            if skill_name:
                skill_cache = await self.skill_cache_mgr.get_or_create_skill_cache(
                    skill_name,
                    llm_client
                )
            else:
                skill_cache = GlobalStaticPrefix.get_instance().get_cache_snapshot()
            
            new_cache = await llm_client.prefill_only(
                messages=messages,
                cache_prefix=skill_cache
            )
        
        # 6. 插入 Radix Tree
        self.radix_tree.insert(message_key, new_cache)
        
        return new_cache.fork()
    
    def _compute_message_key(self, messages: List[dict]) -> str:
        """
        计算消息序列的 Key
        
        使用 SHA-256 hash 前 N 个消息的内容
        """
        # 只取前 100 字符，避免 Key 过长
        content = json.dumps([
            {
                "role": m["role"],
                "content": m["content"][:100]
            }
            for m in messages
        ], sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()
```

---

## 6. KV-Cache 分支探索（Branching）

### 6.1 设计目标

**核心价值**：
- 允许 Agent 并行探索多个决策路径
- 失败后秒级回滚到分叉点，无需重新输入 Prompt
- 零成本：只是移动内存指针

### 6.2 实现方案

```python
# backend/app/kv_cache/branching.py

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import uuid

@dataclass
class CacheBranch:
    """KV-Cache 分支"""
    id: str                         # 分支 ID
    name: str                       # 分支名称
    parent_cache: KVCache           # 分叉点的 Cache（Copy-on-Write）
    created_at: datetime
    metadata: dict                  # 分支元数据（如：探索的方案）


class CacheBranchManager:
    """KV-Cache 分支管理器"""
    
    def __init__(self):
        self.branches: Dict[str, CacheBranch] = {}
    
    async def create_branch(
        self,
        parent_cache: KVCache,
        branch_name: str,
        metadata: dict = None
    ) -> str:
        """
        在当前 Cache 状态创建分支
        
        用途：
        - Agent 面临多个决策路径时，在分叉点创建分支
        - 并行或串行探索每条路径
        - 失败后可以秒级回滚到分叉点
        
        返回：branch_id
        """
        branch_id = f"branch_{uuid.uuid4().hex[:8]}"
        
        # 记录分叉点（只保存指针，不复制数据）
        branch = CacheBranch(
            id=branch_id,
            name=branch_name,
            parent_cache=parent_cache.fork(),  # Copy-on-Write
            created_at=datetime.now(),
            metadata=metadata or {}
        )
        
        self.branches[branch_id] = branch
        
        print(f"🌿 Created branch: {branch_name} (id: {branch_id})")
        
        return branch_id
    
    async def rollback_to_branch(self, branch_id: str) -> KVCache:
        """
        回滚到分支点（秒级）
        
        原理：
        - 直接返回分支点的 Cache
        - 无需重新计算任何 Token
        """
        branch = self.branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch not found: {branch_id}")
        
        print(f"↩️  Rolled back to branch: {branch.name} (id: {branch_id})")
        
        return branch.parent_cache.fork()
    
    def delete_branch(self, branch_id: str):
        """删除分支"""
        if branch_id in self.branches:
            del self.branches[branch_id]
            print(f"🗑️  Deleted branch: {branch_id}")
    
    def list_branches(self) -> List[CacheBranch]:
        """列出所有分支"""
        return list(self.branches.values())


# 使用示例：并行探索多个方案
class AgentExecutor:
    async def explore_multiple_plans(self, plans: List[str]):
        """
        并行探索多个方案
        
        场景：
        - Agent 生成了 3 个可能的解决方案
        - 需要并行测试哪个方案最优
        """
        # 1. 在当前状态创建分支
        current_cache = self.current_cache
        
        branches = []
        for plan in plans:
            branch_id = await self.cache_branch_mgr.create_branch(
                parent_cache=current_cache,
                branch_name=f"Plan: {plan[:50]}",
                metadata={"plan": plan}
            )
            branches.append((branch_id, plan))
        
        print(f"🌿 Created {len(branches)} branches for exploration")
        
        # 2. 并行探索每个分支
        results = await asyncio.gather(*[
            self._explore_plan_in_branch(branch_id, plan)
            for branch_id, plan in branches
        ])
        
        # 3. 评估结果，选择最优方案
        best_idx = self._select_best_plan(results)
        best_branch_id = branches[best_idx][0]
        
        print(f"🎯 Selected best plan: Branch {best_idx + 1}")
        
        # 4. 回滚到最优分支（秒级切换）
        self.current_cache = await self.cache_branch_mgr.rollback_to_branch(
            best_branch_id
        )
        
        # 5. 清理其他分支
        for branch_id, _ in branches:
            if branch_id != best_branch_id:
                self.cache_branch_mgr.delete_branch(branch_id)
        
        return results[best_idx]
    
    async def _explore_plan_in_branch(
        self,
        branch_id: str,
        plan: str
    ) -> dict:
        """在分支中探索一个方案"""
        # 获取分支的 Cache
        branch_cache = self.cache_branch_mgr.branches[branch_id].parent_cache.fork()
        
        # 基于 Cache 生成响应
        response = await self.llm_client.generate(
            messages=[{"role": "assistant", "content": f"<|REASONING|>执行方案：{plan}"}],
            cache=branch_cache
        )
        
        # 评估方案（例如：执行工具调用，检查结果）
        success = await self._evaluate_plan_result(response)
        
        return {
            "plan": plan,
            "response": response,
            "success": success
        }
    
    def _select_best_plan(self, results: List[dict]) -> int:
        """选择最优方案"""
        # 简单策略：选择第一个成功的方案
        for i, result in enumerate(results):
            if result["success"]:
                return i
        
        # 如果都失败，选择第一个
        return 0
```

---

## 7. KV-Cache 持久化（Paging/Swapping）

### 7.1 设计目标

**核心价值**：
- Agent 休眠时，将 Cache 交换到 Host 内存（CPU RAM）或 NVMe 硬盘
- 唤醒时瞬间加载（~100ms），无感恢复状态
- 支持长期记忆：即使几天没说话，Agent 也不会失忆

### 7.2 实现方案

```python
# backend/app/kv_cache/persistence.py

import gzip
import pickle
from pathlib import Path
from typing import Optional

class CachePersistenceManager:
    """KV-Cache 持久化管理器（基于 Redis）"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        import redis.asyncio as aioredis
        self.redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)
        self.key_prefix = "kv_cache:"
    
    async def save_cache_to_redis(
        self,
        session_id: str,
        cache: KVCache,
        ttl: Optional[int] = None  # 过期时间（秒），None 表示永不过期
    ):
        """
        将 Cache 保存到 Redis
        
        场景：
        - Agent 进入休眠状态
        - 会话长时间未活跃
        - 显存不足，需要腾出空间
        
        优势：
        - 支持 RDB/AOF 持久化
        - 自动过期（TTL）
        - 分布式访问
        """
        key = f"{self.key_prefix}{session_id}"
        
        # 1. 序列化 Cache（使用 msgpack，比 pickle 更快更小）
        import msgpack
        serialized = cache.to_dict()
        
        # 将 numpy 数组转换为 bytes
        data = {
            "keys": serialized["keys"].tobytes(),
            "values": serialized["values"].tobytes(),
            "keys_shape": serialized["keys"].shape,
            "values_shape": serialized["values"].shape,
            "keys_dtype": str(serialized["keys"].dtype),
            "values_dtype": str(serialized["values"].dtype),
            "metadata": serialized["metadata"]
        }
        
        packed = msgpack.packb(data, use_bin_type=True)
        
        # 2. 保存到 Redis（自动压缩由 Redis 处理）
        if ttl:
            await self.redis.setex(key, ttl, packed)
        else:
            await self.redis.set(key, packed)
        
        # 3. 统计信息
        size_mb = len(packed) / 1024 / 1024
        print(f"💾 Cache saved to Redis: {session_id} ({size_mb:.2f} MB)")
    
    async def load_cache_from_redis(
        self,
        session_id: str,
        device: str = "cuda"
    ) -> Optional[KVCache]:
        """
        从 Redis 加载 Cache（极速唤醒）
        
        场景：
        - 用户唤醒休眠的 Agent
        - 恢复之前的会话
        
        性能：
        - 本地 Redis: ~20-50ms
        - 远程 Redis (同机房): ~50-100ms
        """
        key = f"{self.key_prefix}{session_id}"
        
        # 1. 从 Redis 读取
        packed = await self.redis.get(key)
        if not packed:
            return None
        
        print(f"📂 Loading cache from Redis: {session_id}")
        
        # 2. 反序列化
        import msgpack
        import numpy as np
        data = msgpack.unpackb(packed, raw=False)
        
        # 3. 重建 numpy 数组
        keys_array = np.frombuffer(data["keys"], dtype=data["keys_dtype"]).reshape(data["keys_shape"])
        values_array = np.frombuffer(data["values"], dtype=data["values_dtype"]).reshape(data["values_shape"])
        
        serialized = {
            "keys": keys_array,
            "values": values_array,
            "metadata": data["metadata"]
        }
        
        # 4. 转换为 KVCache
        cache = KVCache.from_dict(serialized, device=device)
        
        print(f"✅ Cache loaded from Redis: {session_id}")
        
        return cache
    
    async def delete_cache(self, session_id: str):
        """删除持久化的 Cache"""
        key = f"{self.key_prefix}{session_id}"
        deleted = await self.redis.delete(key)
        if deleted:
            print(f"🗑️  Cache deleted: {session_id}")
    
    async def list_cached_sessions(self) -> List[str]:
        """列出所有持久化的会话"""
        pattern = f"{self.key_prefix}*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern, count=100):
            session_id = key.decode().replace(self.key_prefix, "")
            keys.append(session_id)
        return keys
    
    async def get_cache_ttl(self, session_id: str) -> Optional[int]:
        """获取 Cache 的剩余 TTL（秒）"""
        key = f"{self.key_prefix}{session_id}"
        ttl = await self.redis.ttl(key)
        return ttl if ttl > 0 else None


# 使用示例：自动休眠和唤醒
class AgentLifecycleManager:
    async def hibernate_agent(self, session_id: str, ttl: int = 3600 * 24 * 7):
        """Agent 进入休眠状态"""
        # 1. 获取当前 Cache
        current_cache = self.get_current_cache(session_id)
        
        # 2. 保存到 Redis（7 天后自动过期）
        await self.cache_persistence_mgr.save_cache_to_redis(
            session_id,
            current_cache,
            ttl=ttl
        )
        
        # 3. 释放 GPU 内存
        del current_cache
        torch.cuda.empty_cache()
        
        print(f"😴 Agent hibernated: {session_id}")
    
    async def wake_up_agent(self, session_id: str) -> bool:
        """唤醒 Agent（极速恢复状态）"""
        # 1. 从 Redis 加载 Cache
        cache = await self.cache_persistence_mgr.load_cache_from_redis(
            session_id,
            device="cuda"
        )
        
        if not cache:
            return False
        
        # 2. 恢复到内存
        self.set_current_cache(session_id, cache)
        
        print(f"👋 Agent woke up: {session_id}")
        
        return True
```

### 7.3 自动换入换出策略

```python
# backend/app/kv_cache/auto_paging.py

class AutoPagingManager:
    """自动换入换出管理器"""
    
    def __init__(
        self,
        persistence_mgr: CachePersistenceManager,
        max_gpu_caches: int = 100
    ):
        self.persistence_mgr = persistence_mgr
        self.max_gpu_caches = max_gpu_caches
        self.active_sessions: Dict[str, datetime] = {}  # session_id -> last_access_time
    
    async def on_cache_access(self, session_id: str, cache: KVCache):
        """Cache 被访问时调用"""
        self.active_sessions[session_id] = datetime.now()
        
        # 检查是否需要淘汰
        if len(self.active_sessions) > self.max_gpu_caches:
            await self._evict_oldest()
    
    async def _evict_oldest(self):
        """淘汰最久未使用的 Cache"""
        # 找到最久未使用的 session
        oldest_session = min(
            self.active_sessions.items(),
            key=lambda x: x[1]
        )[0]
        
        print(f"🔄 Evicting cache: {oldest_session}")
        
        # 保存到磁盘
        cache = self.get_cache(oldest_session)
        await self.persistence_mgr.save_cache_to_disk(oldest_session, cache)
        
        # 从内存中移除
        self.remove_cache(oldest_session)
        del self.active_sessions[oldest_session]
```

---

## 8. 思维快照库（Thought Snapshot Library）

### 8.1 设计哲学

**核心理念**：
- 将人类专家的解题过程预先跑一遍，持久化为 KV-Cache 文件
- 用户发起类似任务时，直接加载快照，瞬间拥有专家级推理链路
- **跳过 Prefill 阶段**，极速响应复杂任务

**与传统 Few-Shot 的区别**：
| 维度 | Few-Shot Prompting | 思维快照库 |
|------|-------------------|-----------|
| **方式** | 在 Prompt 中提供示例 | 直接加载预计算的 KV-Cache |
| **成本** | 每次都要计算示例的 Token | 只计算一次，之后零成本 |
| **深度** | 浅层示例（1-2 轮） | 深度推理链路（10+ 轮） |
| **速度** | 需要 Prefill 示例 | 跳过 Prefill，秒级响应 |

### 8.2 快照数据结构

```python
# backend/app/kv_cache/snapshot.py

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ReasoningStep:
    """推理步骤"""
    step_num: int
    reasoning: str              # 思考过程
    tool_call: Optional[str]    # 工具调用
    tool_result: Optional[str]  # 工具返回
    timestamp: datetime


@dataclass
class ThoughtSnapshot:
    """思维快照"""
    name: str                           # 快照名称
    description: str                    # 描述
    kv_cache: KVCache                   # 预计算的 KV-Cache
    reasoning_chain: List[ReasoningStep]  # 推理链路
    tags: List[str]                     # 标签（用于搜索）
    embedding: Optional[list]           # Embedding（用于匹配）
    created_at: datetime
    metadata: Dict                      # 元数据
    
    def to_dict(self) -> dict:
        """序列化为字典（用于持久化）"""
        return {
            "name": self.name,
            "description": self.description,
            "kv_cache": self.kv_cache.to_dict(),
            "reasoning_chain": [
                {
                    "step_num": step.step_num,
                    "reasoning": step.reasoning,
                    "tool_call": step.tool_call,
                    "tool_result": step.tool_result,
                    "timestamp": step.timestamp.isoformat()
                }
                for step in self.reasoning_chain
            ],
            "tags": self.tags,
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ThoughtSnapshot':
        """从字典反序列化"""
        return cls(
            name=data["name"],
            description=data["description"],
            kv_cache=KVCache.from_dict(data["kv_cache"]),
            reasoning_chain=[
                ReasoningStep(
                    step_num=step["step_num"],
                    reasoning=step["reasoning"],
                    tool_call=step.get("tool_call"),
                    tool_result=step.get("tool_result"),
                    timestamp=datetime.fromisoformat(step["timestamp"])
                )
                for step in data["reasoning_chain"]
            ],
            tags=data["tags"],
            embedding=data.get("embedding"),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data["metadata"]
        )
```

### 8.3 快照库管理器

```python
# backend/app/kv_cache/snapshot_library.py

from typing import Optional, List
import numpy as np

class ThoughtSnapshotLibrary:
    """思维快照库"""
    
    def __init__(self, snapshot_dir: str = "snapshots/"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots: Dict[str, ThoughtSnapshot] = {}
        self._load_all_snapshots()
    
    def _load_all_snapshots(self):
        """加载所有预置快照"""
        print("📚 Loading Thought Snapshot Library...")
        
        for snapshot_file in self.snapshot_dir.glob("*.snapshot"):
            name = snapshot_file.stem
            snapshot = self._load_snapshot(snapshot_file)
            self.snapshots[name] = snapshot
            print(f"  ✅ Loaded snapshot: {name}")
        
        print(f"📚 Loaded {len(self.snapshots)} snapshots")
    
    def _load_snapshot(self, path: Path) -> ThoughtSnapshot:
        """加载单个快照文件"""
        with gzip.open(path, "rb") as f:
            data = pickle.load(f)
        return ThoughtSnapshot.from_dict(data)
    
    async def match_snapshot(self, user_query: str, threshold: float = 0.7) -> Optional[str]:
        """
        匹配最适合的快照
        
        使用 Milvus 向量相似度搜索
        """
        if not self.snapshots:
            return None
        
        from backend.app.llm.embedding import embedding_client
        from backend.app.vector_db.milvus_client import milvus_client
        
        # 1. 计算查询的 embedding
        query_embedding = await embedding_client.embed(user_query)
        
        # 2. 在 Milvus 中搜索最相似的快照
        results = await milvus_client.search(
            collection_name="thought_snapshots",
            query_vectors=[query_embedding],
            limit=1,
            output_fields=["snapshot_name"]
        )
        
        if not results or len(results[0]) == 0:
            return None
        
        # 3. 获取最佳匹配
        best_match = results[0][0]
        best_name = best_match.entity.get("snapshot_name")
        best_score = best_match.distance
        
        # 4. 阈值过滤
        if best_score > threshold:
            print(f"🎯 Matched Thought Snapshot: {best_name} (score: {best_score:.2f})")
            return best_name
        
        return None
    
    async def _store_snapshot_to_milvus(self, snapshot: ThoughtSnapshot):
        """将快照 embedding 存储到 Milvus"""
        from backend.app.vector_db.milvus_client import milvus_client
        
        await milvus_client.insert(
            collection_name="thought_snapshots",
            data=[{
                "snapshot_name": snapshot.name,
                "embedding": snapshot.embedding,
                "description": snapshot.description,
                "tags": snapshot.tags,
                "created_at": snapshot.created_at.isoformat()
            }]
        )
    
    def get_snapshot(self, name: str) -> Optional[ThoughtSnapshot]:
        """获取快照"""
        return self.snapshots.get(name)
    
    def list_snapshots(self) -> List[str]:
        """列出所有快照"""
        return list(self.snapshots.keys())


# 使用示例：匹配并加载快照
class AgentExecutor:
    async def execute_with_snapshot(self, user_query: str):
        """使用思维快照执行（极速响应）"""
        
        # 1. 尝试匹配快照
        snapshot_name = await self.snapshot_lib.match_snapshot(user_query)
        
        if snapshot_name:
            print(f"⚡ Using Thought Snapshot: {snapshot_name}")
            
            # 2. 加载快照的 KV-Cache
            snapshot = self.snapshot_lib.get_snapshot(snapshot_name)
            self.current_cache = snapshot.kv_cache.fork()
            
            # 3. 跳过 Prefill，直接生成（极速响应）
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": user_query}],
                cache=self.current_cache,
                skip_prefill=True  # 关键：跳过 Prefill 阶段
            )
            
            print(f"⚡ Response generated in <1s (using snapshot)")
        else:
            # 4. 常规流程
            print("📝 No matching snapshot, using normal flow")
            response = await self.execute_normal(user_query)
        
        return response
```

### 8.4 创建快照

```python
# tools/create_snapshot.py

async def create_financial_analysis_snapshot():
    """
    创建"财务分析专家"快照
    
    流程：
    1. 让 Agent 完整执行一个财务分析任务
    2. 记录完整的推理链路
    3. 捕获 KV-Cache
    4. 持久化为快照文件
    """
    from backend.app.agent.executor import AgentExecutor
    from backend.app.kv_cache.snapshot import ThoughtSnapshot
    
    # 1. 定义专家任务
    expert_task = """
分析以下财务报表，提供深度洞察：

1. 营收分析：同比/环比增长率，主要驱动因素
2. 利润率分析：毛利率、净利率、营业利润率
3. 现金流分析：经营现金流、自由现金流
4. 资产负债率：负债结构、偿债能力
5. 风险评估：财务风险、经营风险

请使用以下工具：
- read_file: 读取财务报表文件
- python_execute: 计算财务指标
- web_search: 搜索行业对比数据
"""
    
    # 2. 执行任务并捕获推理链路
    agent = AgentExecutor()
    
    cache, reasoning_chain = await agent.execute_and_capture(expert_task)
    
    # 3. 计算 embedding
    from backend.app.llm.embedding import embedding_client
    embedding = await embedding_client.embed(expert_task)
    
    # 4. 创建快照
    snapshot = ThoughtSnapshot(
        name="financial_analysis_expert",
        description="财务分析专家的完整推理链路，包含营收、利润、现金流、风险评估等深度分析",
        kv_cache=cache,
        reasoning_chain=reasoning_chain,
        tags=["finance", "analysis", "expert", "deep"],
        embedding=embedding,
        created_at=datetime.now(),
        metadata={
            "task_tokens": len(expert_task.split()),
            "reasoning_steps": len(reasoning_chain),
            "tools_used": ["read_file", "python_execute", "web_search"]
        }
    )
    
    # 5. 持久化
    snapshot_path = Path("snapshots/financial_analysis_expert.snapshot")
    with gzip.open(snapshot_path, "wb") as f:
        pickle.dump(snapshot.to_dict(), f)
    
    print(f"✅ Snapshot created: {snapshot_path}")
    print(f"   - Reasoning steps: {len(reasoning_chain)}")
    print(f"   - Cache size: {cache.memory_size / 1024 / 1024:.2f} MB")


# Agent Executor 需要支持捕获模式
class AgentExecutor:
    async def execute_and_capture(
        self,
        task: str
    ) -> Tuple[KVCache, List[ReasoningStep]]:
        """
        执行任务并捕获 KV-Cache 和推理链路
        
        专门用于创建思维快照
        """
        reasoning_chain = []
        
        # 执行任务
        messages = [{"role": "user", "content": task}]
        
        for step_num in range(1, 100):  # 最多 100 步
            # 生成推理
            response = await self.llm_client.generate(
                messages=messages,
                stop=["<|TOOL_CALL|>", "<|FINAL_ANSWER|>"]
            )
            
            # 记录推理步骤
            reasoning_step = ReasoningStep(
                step_num=step_num,
                reasoning=response.content,
                tool_call=None,
                tool_result=None,
                timestamp=datetime.now()
            )
            
            # 如果是工具调用
            if "<|TOOL_CALL|>" in response.content:
                tool_call = self.parse_tool_call(response.content)
                tool_result = await self.execute_tool(tool_call)
                
                reasoning_step.tool_call = tool_call
                reasoning_step.tool_result = tool_result
                
                # 追加到 messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "tool", "content": f"<|TOOL_RESULT|>{tool_result}"})
            
            # 如果是最终答案
            if "<|FINAL_ANSWER|>" in response.content:
                reasoning_chain.append(reasoning_step)
                break
            
            reasoning_chain.append(reasoning_step)
        
        # 获取当前 KV-Cache
        final_cache = self.current_cache
        
        return final_cache, reasoning_chain
```

### 8.5 预置快照示例

**建议预置的快照**：

1. **`financial_analysis_expert`**: 财务分析专家
2. **`code_refactor_expert`**: 代码重构专家
3. **`data_analysis_expert`**: 数据分析专家（Pandas/Matplotlib）
4. **`deep_research_expert`**: 深度研究专家（多源搜索+总结）
5. **`ppt_generation_expert`**: PPT 生成专家
6. **`api_debugging_expert`**: API 调试专家
7. **`sql_optimization_expert`**: SQL 优化专家
8. **`ui_design_expert`**: UI 设计专家

---

## 9. 技术栈与实施路线图

### 9.1 技术栈选型

```python
# 必选技术栈
vLLM              # PagedAttention + Prefix Caching
PyTorch           # KV-Cache 序列化/反序列化
asyncio           # 异步 I/O
Redis             # KV-Cache 持久化存储（支持 RDB/AOF）
Milvus            # 向量数据库（快照匹配、Skill 匹配）

# 可选技术栈（高级优化）
Ray               # 分布式 KV-Cache 管理
Redis Cluster     # Redis 集群（多节点分布式）
```

### 9.2 实施路线图

#### Phase 1: 基础层（Week 1-2）

**目标**：搭建层次化缓存的基础架构

- [ ] 实现 `GlobalStaticPrefix`（全局静态前缀）
- [ ] 实现 `KVCache` 数据结构（Copy-on-Write）
- [ ] 集成 vLLM Prefix Caching
- [ ] 单元测试：验证 Copy-on-Write 机制

**验收标准**：
- 100 个 Agent 实例共享一份 Global Prefix
- 显存节省 > 80%

---

#### Phase 2: Skill Cache（Week 3-4）

**目标**：实现 Skill-Aware Cache

- [ ] 实现 `SkillCacheManager`
- [ ] 与 Skill 系统集成
- [ ] 实现懒加载 + 预计算
- [ ] 实现向量匹配（自动识别 Skill）

**验收标准**：
- Skill 首次加载 < 2s
- 后续复用 < 100ms
- 自动匹配准确率 > 80%

---

#### Phase 3: Session Cache + Radix Tree（Week 5-6）

**目标**：实现会话级缓存管理

- [ ] 实现 `RadixTree` 数据结构
- [ ] 实现 `SessionCacheManager`
- [ ] 自动前缀检测
- [ ] LRU 淘汰策略

**验收标准**：
- 公共前缀自动识别
- Cache 命中率 > 70%

---

#### Phase 4: 分支探索（Week 7）

**目标**：实现 KV-Cache Branching

- [ ] 实现 `CacheBranchManager`
- [ ] 支持并行探索多个方案
- [ ] 秒级回滚机制

**验收标准**：
- 分支创建 < 10ms
- 回滚延迟 < 100ms

---

#### Phase 5: 持久化（Week 8）

**目标**：实现 KV-Cache Paging

- [ ] 实现 `CachePersistenceManager`
- [ ] 支持保存到磁盘（压缩）
- [ ] 支持从磁盘加载（瞬间唤醒）
- [ ] 自动换入换出策略

**验收标准**：
- 保存速度 < 500ms
- 加载速度 < 200ms
- 压缩率 > 50%

---

#### Phase 6: 思维快照库（Week 9-10）

**目标**：实现 Thought Snapshot Library

- [ ] 实现 `ThoughtSnapshot` 数据结构
- [ ] 实现 `ThoughtSnapshotLibrary`
- [ ] 创建工具：`create_snapshot.py`
- [ ] 预置 5-8 个专家快照

**验收标准**：
- 快照加载 < 200ms
- 匹配准确率 > 75%
- 跳过 Prefill，极速响应

---

## 10. 监控与指标

### 10.1 关键指标

```python
# backend/app/monitoring/kv_cache_metrics.py

from prometheus_client import Counter, Histogram, Gauge

# KV-Cache 命中率
kv_cache_hit_rate = Gauge(
    "kv_cache_hit_rate",
    "KV-Cache hit rate",
    ["layer"]  # global/skill/session
)

# 显存节省
memory_savings = Gauge(
    "kv_cache_memory_savings",
    "Memory savings by KV-Cache sharing (bytes)"
)

# 分支回滚延迟
branch_rollback_latency = Histogram(
    "kv_cache_branch_rollback_latency_seconds",
    "Branch rollback latency"
)

# 快照加载延迟
snapshot_load_latency = Histogram(
    "kv_cache_snapshot_load_latency_seconds",
    "Snapshot load latency"
)

# 快照匹配准确率
snapshot_match_accuracy = Gauge(
    "kv_cache_snapshot_match_accuracy",
    "Snapshot match accuracy"
)
```

### 10.2 目标 SLA

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **Global Prefix 命中率** | > 99% | 几乎所有请求都命中 |
| **Skill Cache 命中率** | > 90% | 大部分任务复用 Skill Cache |
| **Session Cache 命中率** | > 70% | 多会话共享公共前缀 |
| **显存节省率** | > 80% | 相比无共享方案 |
| **分支回滚延迟** | < 100ms | 秒级切换 |
| **快照加载延迟** | < 200ms | 瞬间唤醒 |
| **快照匹配准确率** | > 75% | 大部分任务匹配到快照 |

---

## 11. 常见问题

### Q1: 与 vLLM 的 Prefix Caching 有什么区别？

**A**: 
- **vLLM Prefix Caching**: 自动识别重复的前缀，底层优化
- **TokenDance 层次化缓存**: 在 vLLM 基础上，增加了三层架构、分支探索、思维快照库等高级功能
- **关系**: TokenDance 是应用层设计，vLLM 是底层实现

### Q2: Copy-on-Write 会不会导致内存泄漏？

**A**: 
- PyTorch 的引用计数机制会自动回收
- 当所有 fork 副本都被释放后，原始 Tensor 会被回收
- 建议定期运行 `torch.cuda.empty_cache()` 清理碎片

### Q3: Radix Tree 的内存开销有多大？

**A**: 
- 每个节点只存储指针（~100 bytes）
- 1000 个节点 ≈ 100KB
- 相比 KV-Cache 本身（~100MB），可忽略不计

### Q4: 思维快照库会占用多少磁盘空间？

**A**: 
- 单个快照：50-200MB（压缩后）
- 10 个快照：~1GB
- 建议使用 NVMe SSD 存储

### Q5: 如何保证多进程/多机的 Cache 一致性？

**A**: 
- **单机多进程**: 使用共享内存（`torch.multiprocessing`）
- **多机**: 使用 Ray 的分布式对象存储
- **一致性**: Global Prefix 只读，无需同步；Session Cache 各自独立

---

## 12. 总结

### 12.1 核心创新点

✅ **层次化缓存**：Global → Skill → Session，节省 90% 显存
✅ **分支探索**：允许试错，秒级回滚，零成本
✅ **持久化记忆**：Agent 永不失忆，支持无感唤醒
✅ **思维快照库**：预装专家推理链路，极速响应复杂任务

### 12.2 与 Manus 的对比

| 维度 | Manus | TokenDance |
|------|-------|-----------|
| **缓存共享** | 每个 Agent 独立 | 三层共享，节省 90% 显存 |
| **任务切换** | 重新加载 | 分支探索，秒级切换 |
| **长期记忆** | 依赖文件系统 | KV-Cache 持久化 + 思维快照库 |
| **专家知识** | 依赖 Prompt | 思维快照库，极速加载 |

### 12.3 业务价值

1. **成本降低**：显存节省 90%，支持更多并发用户
2. **性能提升**：分支探索允许试错，快照库极速响应
3. **用户体验**：Agent 永不失忆，唤醒无感知
4. **可扩展性**：层次化架构，易于扩展新功能

---

**下一步**：开始 Phase 1 实施，搭建 Global Static Prefix 基础架构！🚀
