# 上下文压缩策略设计文档

> **核心理念**：KV-Cache（工作记忆） + FileSystem（长期记忆） = 双轨记忆系统
> Version: 1.0.0
> Last Updated: 2026-01-09

## 1. 设计哲学

### 1.1 认知科学视角

**人类记忆系统**：
```
工作记忆（Working Memory）：
- 容量：7±2 项
- 特点：快速访问，易失性
- 用途：当前任务的活跃信息

长期记忆（Long-term Memory）：
- 容量：几乎无限
- 特点：持久化，检索稍慢
- 用途：知识、经验、历史
```

**Agent 记忆系统**（完全对应）：
```
KV-Cache（工作记忆）：
- 容量：受 GPU 显存限制（~100GB）
- 特点：极速访问（<1ms），易失
- 用途：当前会话的上下文

FileSystem（长期记忆）：
- 容量：几乎无限（数 TB）
- 特点：持久化，访问较慢（~10ms）
- 用途：历史数据、中间结果、知识库
```

### 1.2 核心挑战

**问题**：
1. **Context 爆炸**：一个复杂任务可能产生几十 MB 的中间结果
2. **KV-Cache 限制**：显存有限，无法无限扩展
3. **信息丢失**：简单截断会丢失关键信息
4. **无法恢复**：压缩后无法找回原始数据

**解决方案**：
- ✅ 智能压缩：自动识别何时压缩
- ✅ 文件系统指针：保留完整恢复路径
- ✅ 分层存储：热数据在 KV-Cache，冷数据在文件系统
- ✅ 按需加载：需要时从文件系统加载

---

## 2. 文件系统指针（File System Pointer）

### 2.1 数据结构

```python
# backend/app/context/file_pointer.py

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from enum import Enum

class FileType(Enum):
    """文件类型"""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    CSV = "csv"

class CompressionLevel(Enum):
    """压缩级别"""
    NONE = 0           # 不压缩，直接保留在 KV-Cache
    SUMMARY = 1        # 只保留摘要
    STRUCTURED = 2     # 保留结构化元数据
    MINIMAL = 3        # 最小化，只保留路径


@dataclass
class FileSystemPointer:
    """
    文件系统指针（存储在 KV-Cache 中的轻量级引用）
    
    作用：
    - 在 KV-Cache 中占用极小空间（~1KB）
    - 保留完整的数据恢复路径
    - 提供快速检索提示
    """
    
    # 核心字段
    summary: str                    # 200-500 字摘要（人类+AI 可读）
    file_path: str                  # 完整文件路径（相对于 workspace/）
    file_type: FileType             # 文件类型
    
    # 恢复信息
    size_bytes: int                 # 原始文件大小
    checksum: str                   # SHA-256 校验和（验证完整性）
    original_url: Optional[str]     # 原始数据来源 URL（如果有）
    
    # 检索增强
    retrieval_hints: List[str]      # 关键词列表（用于向量检索）
    embedding: Optional[List[float]]  # 摘要的 embedding（768维）
    
    # 元数据
    compression_level: CompressionLevel
    created_at: datetime
    expires_at: Optional[datetime]  # 缓存过期时间（None = 永不过期）
    access_count: int = 0           # 访问次数（用于 LRU）
    last_accessed: Optional[datetime] = None
    
    # 结构化元数据（可选，针对特定文件类型）
    structured_metadata: Optional[dict] = None
    
    def __post_init__(self):
        """计算 embedding"""
        if self.embedding is None and self.summary:
            # 延迟计算，避免初始化时阻塞
            pass
    
    @property
    def size_kb(self) -> float:
        """文件大小（KB）"""
        return self.size_bytes / 1024
    
    @property
    def size_mb(self) -> float:
        """文件大小（MB）"""
        return self.size_bytes / 1024 / 1024
    
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "summary": self.summary,
            "file_path": self.file_path,
            "file_type": self.file_type.value,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "original_url": self.original_url,
            "retrieval_hints": self.retrieval_hints,
            "embedding": self.embedding,
            "compression_level": self.compression_level.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "structured_metadata": self.structured_metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileSystemPointer':
        """从字典反序列化"""
        return cls(
            summary=data["summary"],
            file_path=data["file_path"],
            file_type=FileType(data["file_type"]),
            size_bytes=data["size_bytes"],
            checksum=data["checksum"],
            original_url=data.get("original_url"),
            retrieval_hints=data["retrieval_hints"],
            embedding=data.get("embedding"),
            compression_level=CompressionLevel(data["compression_level"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]) if data.get("last_accessed") else None,
            structured_metadata=data.get("structured_metadata")
        )
```

### 2.2 压缩指针示例

```python
# 示例 1：API 响应压缩
api_response_pointer = FileSystemPointer(
    summary="""
    查询北京天气数据（2026-01-09）：
    - 天气：晴
    - 温度：20°C
    - 湿度：45%
    - 风速：3m/s
    包含完整的 24 小时预报和空气质量指数。
    """,
    file_path="cache/api_responses/weather_beijing_20260109_143000.json",
    file_type=FileType.JSON,
    size_bytes=51200,  # 50KB
    checksum="a3f8b9c1d2e5f6g7h8i9j0k1l2m3n4o5",
    original_url="https://api.weather.com/v1/forecast?city=beijing&date=2026-01-09",
    retrieval_hints=["weather", "beijing", "forecast", "temperature", "humidity"],
    compression_level=CompressionLevel.SUMMARY,
    created_at=datetime.now(),
    expires_at=datetime.now() + timedelta(hours=24)  # 24 小时后过期
)

# 示例 2：网页抓取压缩
webpage_pointer = FileSystemPointer(
    summary="""
    TechCrunch 文章："OpenAI Launches GPT-5"
    - 发布日期：2026-01-08
    - 主要内容：GPT-5 性能提升 10x，支持多模态推理
    - 关键词：AI, GPT-5, multimodal, reasoning
    - 文章长度：5000 字
    """,
    file_path="cache/web_pages/techcrunch_gpt5_20260108.html",
    file_type=FileType.HTML,
    size_bytes=204800,  # 200KB
    checksum="b4e8c9d1a2f5g6h7i8j9k0l1m2n3o4p5",
    original_url="https://techcrunch.com/2026/01/08/openai-launches-gpt5",
    retrieval_hints=["OpenAI", "GPT-5", "AI", "launch", "multimodal"],
    compression_level=CompressionLevel.STRUCTURED,
    created_at=datetime.now(),
    expires_at=None,  # 永不过期
    structured_metadata={
        "title": "OpenAI Launches GPT-5",
        "author": "Kyle Wiggers",
        "publish_date": "2026-01-08",
        "word_count": 5000,
        "tags": ["AI", "GPT-5", "OpenAI"]
    }
)
```

---

## 3. 压缩策略

### 3.1 智能压缩决策树

```python
# backend/app/context/compression.py

class CompressionDecisionEngine:
    """压缩决策引擎"""
    
    # 阈值配置
    THRESHOLD_TINY = 1024        # 1KB
    THRESHOLD_SMALL = 10240      # 10KB
    THRESHOLD_MEDIUM = 102400    # 100KB
    THRESHOLD_LARGE = 1048576    # 1MB
    
    async def should_compress(
        self,
        data: str,
        context: dict
    ) -> tuple[bool, CompressionLevel]:
        """
        判断是否需要压缩
        
        返回：(是否压缩, 压缩级别)
        """
        data_size = len(data.encode('utf-8'))
        
        # 决策树
        if data_size < self.THRESHOLD_TINY:
            # < 1KB：保留在 KV-Cache
            return False, CompressionLevel.NONE
        
        elif data_size < self.THRESHOLD_SMALL:
            # 1KB ~ 10KB：根据重要性决定
            importance = await self._assess_importance(data, context)
            if importance > 0.8:
                return False, CompressionLevel.NONE
            else:
                return True, CompressionLevel.SUMMARY
        
        elif data_size < self.THRESHOLD_MEDIUM:
            # 10KB ~ 100KB：大概率压缩，保留摘要
            return True, CompressionLevel.SUMMARY
        
        elif data_size < self.THRESHOLD_LARGE:
            # 100KB ~ 1MB：必须压缩，保留结构化元数据
            return True, CompressionLevel.STRUCTURED
        
        else:
            # > 1MB：极限压缩，只保留路径
            return True, CompressionLevel.MINIMAL
    
    async def _assess_importance(self, data: str, context: dict) -> float:
        """
        评估数据重要性（0-1）
        
        因素：
        - 是否是任务目标相关
        - 是否被多次引用
        - 是否是最终结果
        """
        score = 0.0
        
        # 1. 任务目标相关性
        if context.get("task_goal"):
            similarity = await self._compute_similarity(data, context["task_goal"])
            score += similarity * 0.5
        
        # 2. 引用次数
        reference_count = context.get("reference_count", 0)
        if reference_count > 3:
            score += 0.3
        elif reference_count > 1:
            score += 0.2
        
        # 3. 是否是最终结果
        if context.get("is_final_result"):
            score += 0.2
        
        return min(score, 1.0)
```

### 3.2 压缩执行器

```python
class ContextCompressor:
    """上下文压缩器"""
    
    def __init__(
        self,
        file_manager,
        llm_client,
        embedding_client
    ):
        self.file_manager = file_manager
        self.llm_client = llm_client
        self.embedding_client = embedding_client
        self.decision_engine = CompressionDecisionEngine()
    
    async def compress(
        self,
        data: str,
        context: dict,
        file_type: FileType = FileType.TEXT
    ) -> Union[str, FileSystemPointer]:
        """
        压缩数据
        
        返回：
        - 原始数据（如果不需要压缩）
        - FileSystemPointer（如果需要压缩）
        """
        # 1. 判断是否需要压缩
        should_compress, level = await self.decision_engine.should_compress(data, context)
        
        if not should_compress:
            return data
        
        # 2. 生成摘要
        summary = await self._generate_summary(data, level)
        
        # 3. 保存到文件系统
        file_path = await self._save_to_filesystem(data, file_type)
        
        # 4. 计算 checksum
        checksum = self._compute_checksum(data)
        
        # 5. 提取检索提示
        retrieval_hints = await self._extract_keywords(data, top_k=10)
        
        # 6. 计算 embedding
        embedding = await self.embedding_client.embed(summary)
        
        # 7. 提取结构化元数据（针对特定类型）
        structured_metadata = await self._extract_structured_metadata(data, file_type)
        
        # 8. 创建指针
        pointer = FileSystemPointer(
            summary=summary,
            file_path=file_path,
            file_type=file_type,
            size_bytes=len(data.encode('utf-8')),
            checksum=checksum,
            original_url=context.get("original_url"),
            retrieval_hints=retrieval_hints,
            embedding=embedding,
            compression_level=level,
            created_at=datetime.now(),
            expires_at=context.get("expires_at"),
            structured_metadata=structured_metadata
        )
        
        return pointer
    
    async def _generate_summary(
        self,
        data: str,
        level: CompressionLevel
    ) -> str:
        """生成摘要"""
        
        if level == CompressionLevel.SUMMARY:
            # 200-500 字摘要
            max_length = 500
        elif level == CompressionLevel.STRUCTURED:
            # 100-200 字摘要
            max_length = 200
        else:  # MINIMAL
            # 50-100 字摘要
            max_length = 100
        
        prompt = f"""
请为以下内容生成一个简洁的摘要（{max_length} 字以内）：

{data[:5000]}  # 只取前 5000 字符

摘要要求：
1. 保留关键信息（数字、日期、名称）
2. 突出核心内容
3. 便于后续检索
"""
        
        summary = await self.llm_client.generate(prompt, max_tokens=max_length)
        return summary.strip()
    
    async def _save_to_filesystem(
        self,
        data: str,
        file_type: FileType
    ) -> str:
        """保存到文件系统"""
        
        # 生成文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = uuid.uuid4().hex[:8]
        
        category = self._get_category(file_type)
        filename = f"{timestamp}_{file_id}.{file_type.value}"
        file_path = f"cache/{category}/{filename}"
        
        # 保存
        await self.file_manager.write_file(
            path=file_path,
            content=data
        )
        
        return file_path
    
    def _compute_checksum(self, data: str) -> str:
        """计算 SHA-256 checksum"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _extract_keywords(self, data: str, top_k: int = 10) -> List[str]:
        """提取关键词"""
        # 使用 TF-IDF 或 LLM 提取
        prompt = f"""
从以下文本中提取 {top_k} 个最重要的关键词：

{data[:2000]}

要求：只返回关键词列表，用逗号分隔。
"""
        
        response = await self.llm_client.generate(prompt, max_tokens=100)
        keywords = [kw.strip() for kw in response.split(",")]
        return keywords[:top_k]
    
    async def _extract_structured_metadata(
        self,
        data: str,
        file_type: FileType
    ) -> Optional[dict]:
        """提取结构化元数据"""
        
        if file_type == FileType.JSON:
            # JSON：提取 schema
            import json
            try:
                obj = json.loads(data)
                return {
                    "schema": list(obj.keys()) if isinstance(obj, dict) else None,
                    "item_count": len(obj) if isinstance(obj, (list, dict)) else None
                }
            except:
                return None
        
        elif file_type == FileType.HTML:
            # HTML：提取 title、author、publish_date
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, 'html.parser')
            return {
                "title": soup.title.string if soup.title else None,
                "meta_description": soup.find("meta", {"name": "description"}),
                "word_count": len(soup.get_text().split())
            }
        
        else:
            return None
    
    def _get_category(self, file_type: FileType) -> str:
        """获取文件分类"""
        mapping = {
            FileType.JSON: "api_responses",
            FileType.HTML: "web_pages",
            FileType.MARKDOWN: "documents",
            FileType.TEXT: "text_files",
            FileType.IMAGE: "images",
            FileType.CSV: "data_files"
        }
        return mapping.get(file_type, "misc")
```

---

## 4. 解压与恢复

### 4.1 数据恢复器

```python
class ContextDecompressor:
    """上下文解压器"""
    
    def __init__(self, file_manager):
        self.file_manager = file_manager
    
    async def decompress(
        self,
        pointer: FileSystemPointer,
        validate: bool = True
    ) -> str:
        """
        解压数据（从文件系统恢复）
        
        参数：
        - pointer: 文件系统指针
        - validate: 是否验证完整性
        
        返回：原始数据
        """
        # 1. 检查是否过期
        if pointer.is_expired():
            raise ValueError(f"Cache expired: {pointer.file_path}")
        
        # 2. 从文件系统读取
        data = await self.file_manager.read_file(pointer.file_path)
        
        # 3. 验证完整性
        if validate:
            checksum = self._compute_checksum(data)
            if checksum != pointer.checksum:
                raise ValueError(f"Checksum mismatch: expected {pointer.checksum}, got {checksum}")
        
        # 4. 更新访问计数
        pointer.access_count += 1
        pointer.last_accessed = datetime.now()
        
        return data
    
    def _compute_checksum(self, data: str) -> str:
        """计算 checksum"""
        import hashlib
        return hashlib.sha256(data.encode()).hexdigest()
```

---

## 5. 与 KV-Cache 的协同

### 5.1 分层存储架构

```
┌─────────────────────────────────────────────────────────────────┐
│  五层记忆架构                                                    │
│                                                                  │
│  Layer 0: FileSystem (长期记忆)                                  │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 无限容量（数 TB）                                     │     │
│  │ • 持久化存储                                            │     │
│  │ • 访问速度：~10ms                                       │     │
│  │ • 存储：原始数据（完整保留）                            │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 压缩指针                               │
│  Layer 1: Global Static Prefix (全局静态前缀)                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 工具定义、FSM 状态、核心规则                          │     │
│  │ • 所有 Agent 共享（Copy-on-Write）                      │     │
│  │ • 存储：结构化定义                                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 挂载                                   │
│  Layer 2: Skill Cache (领域专家知识)                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • Skill L2 指令                                         │     │
│  │ • 懒加载 + 复用                                         │     │
│  │ • 存储：专家知识 + 压缩指针                             │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 追加                                   │
│  Layer 3: Session Cache (会话上下文)                            │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 用户指令、Agent 推理、工具返回                        │     │
│  │ • Radix Tree 管理                                       │     │
│  │ • 存储：热数据 + 压缩指针（指向 Layer 0）              │     │
│  └────────────────────────────────────────────────────────┘     │
│                         ↓ 分支                                   │
│  Layer 4: Branch Exploration (分支探索)                         │
│  ┌────────────────────────────────────────────────────────┐     │
│  │ • 并行探索多个决策路径                                  │     │
│  │ • 秒级回滚                                              │     │
│  │ • 存储：分支点 + 压缩指针                               │     │
│  └────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 协同工作流程

```python
class ContextManager:
    """上下文管理器（协调 KV-Cache 和 FileSystem）"""
    
    def __init__(
        self,
        kv_cache_manager,
        file_manager,
        compressor,
        decompressor
    ):
        self.kv_cache = kv_cache_manager
        self.file_manager = file_manager
        self.compressor = compressor
        self.decompressor = decompressor
    
    async def add_to_context(
        self,
        data: str,
        context: dict,
        file_type: FileType = FileType.TEXT
    ) -> None:
        """
        添加数据到上下文
        
        智能决策：
        - 小数据：直接加入 KV-Cache
        - 大数据：压缩到文件系统，KV-Cache 只保留指针
        """
        # 1. 压缩决策
        result = await self.compressor.compress(data, context, file_type)
        
        if isinstance(result, str):
            # 不需要压缩，直接加入 KV-Cache
            await self.kv_cache.append(result)
        else:
            # 需要压缩，加入指针
            pointer = result
            await self.kv_cache.append_pointer(pointer)
    
    async def retrieve_from_context(
        self,
        pointer: FileSystemPointer
    ) -> str:
        """
        从上下文检索数据
        
        流程：
        1. 检查 pointer 是否在 KV-Cache
        2. 如果需要完整数据，从文件系统恢复
        """
        # 从文件系统恢复完整数据
        data = await self.decompressor.decompress(pointer)
        
        # 可选：加载到 KV-Cache（热数据）
        if pointer.access_count > 3:
            await self.kv_cache.append(data)
        
        return data
```

---

## 6. 使用示例

### 6.1 Agent 自动压缩

```python
# Agent 执行任务时自动触发压缩

class AgentExecutor:
    async def execute_tool(self, tool_call: dict) -> str:
        """执行工具调用"""
        
        # 1. 执行工具
        result = await self.tool_manager.execute(tool_call)
        
        # 2. 智能压缩
        context = {
            "task_goal": self.current_task.goal,
            "reference_count": 0,
            "is_final_result": False
        }
        
        compressed_result = await self.context_mgr.add_to_context(
            data=result,
            context=context,
            file_type=FileType.JSON
        )
        
        # 3. 在推理中使用
        if isinstance(compressed_result, FileSystemPointer):
            # 只在推理中提及摘要
            reasoning = f"""
工具返回结果已保存到文件系统：
{compressed_result.summary}

完整数据路径：{compressed_result.file_path}
"""
        else:
            # 直接使用原始数据
            reasoning = f"工具返回结果：{compressed_result}"
        
        return reasoning
```

### 6.2 按需恢复

```python
# Agent 需要完整数据时按需恢复

class AgentExecutor:
    async def analyze_data(self, pointer: FileSystemPointer):
        """分析数据（需要完整数据）"""
        
        # 1. 从文件系统恢复
        full_data = await self.context_mgr.retrieve_from_context(pointer)
        
        # 2. 分析
        analysis = await self.llm_client.generate(f"""
请分析以下数据：

{full_data}

要求：提取关键洞察。
""")
        
        return analysis
```

---

## 7. 性能优化

### 7.1 LRU 缓存

```python
class LRUCache:
    """LRU 缓存（管理热数据）"""
    
    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self.cache: Dict[str, FileSystemPointer] = {}
        self.access_order: List[str] = []
    
    def get(self, file_path: str) -> Optional[FileSystemPointer]:
        """获取缓存项"""
        if file_path in self.cache:
            # 更新访问顺序
            self.access_order.remove(file_path)
            self.access_order.append(file_path)
            return self.cache[file_path]
        return None
    
    def put(self, pointer: FileSystemPointer):
        """放入缓存"""
        if len(self.cache) >= self.max_items:
            # 淘汰最久未使用
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[pointer.file_path] = pointer
        self.access_order.append(pointer.file_path)
```

### 7.2 预加载策略

```python
class PreloadManager:
    """预加载管理器"""
    
    async def preload_likely_needed(
        self,
        current_context: dict,
        pointers: List[FileSystemPointer]
    ):
        """
        预加载可能需要的数据
        
        策略：
        - 访问次数 > 3 的高频数据
        - 与当前任务相关性 > 0.8 的数据
        """
        for pointer in pointers:
            # 高频数据
            if pointer.access_count > 3:
                await self._preload(pointer)
            
            # 高相关性数据
            elif current_context.get("task_goal"):
                similarity = await self._compute_similarity(
                    pointer.summary,
                    current_context["task_goal"]
                )
                if similarity > 0.8:
                    await self._preload(pointer)
    
    async def _preload(self, pointer: FileSystemPointer):
        """预加载到 KV-Cache"""
        data = await self.decompressor.decompress(pointer)
        await self.kv_cache.append(data)
```

---

## 8. 监控与指标

### 8.1 关键指标

```python
from prometheus_client import Counter, Histogram, Gauge

# 压缩率
compression_ratio = Gauge(
    "context_compression_ratio",
    "Context compression ratio (original / compressed)"
)

# 压缩延迟
compression_latency = Histogram(
    "context_compression_latency_seconds",
    "Compression latency"
)

# 解压延迟
decompression_latency = Histogram(
    "context_decompression_latency_seconds",
    "Decompression latency"
)

# 缓存命中率
cache_hit_rate = Gauge(
    "file_cache_hit_rate",
    "File cache hit rate"
)

# 文件系统占用
filesystem_usage_bytes = Gauge(
    "filesystem_usage_bytes",
    "Total filesystem usage"
)
```

### 8.2 目标 SLA

| 指标 | 目标值 |
|------|--------|
| 压缩率 | > 10x |
| 压缩延迟 | < 500ms |
| 解压延迟 | < 100ms |
| 缓存命中率 | > 80% |
| 文件系统占用 | < 100GB/用户 |

---

## 9. 总结

### 9.1 核心价值

✅ **双轨记忆**：KV-Cache（工作记忆） + FileSystem（长期记忆）
✅ **智能压缩**：自动识别何时压缩，避免 Context 爆炸
✅ **可恢复性**：压缩指针保留完整恢复路径
✅ **按需加载**：热数据在 KV-Cache，冷数据在文件系统

### 9.2 设计亮点

1. **认知对齐**：完全对应人类记忆系统（工作记忆 + 长期记忆）
2. **零信息丢失**：压缩指针保留所有恢复路径
3. **智能决策**：Agent 自己判断何时压缩，何时恢复
4. **性能优化**：LRU 缓存 + 预加载 + 分层存储

---

**下一步**：集成到 Context-Management.md，并更新 KV-Cache-Advanced.md 中的 Layer 0 设计！🚀
