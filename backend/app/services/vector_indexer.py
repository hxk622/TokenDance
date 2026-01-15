# -*- coding: utf-8 -*-
"""
Vector Indexer Service - 向量化索引服务

功能：
- 文件内容向量化 (OpenAI Embeddings / 本地模型)
- pgvector 存储
- 语义搜索 API
- 增量更新

设计原则：
- 支持多种 Embedding 提供者
- 批量处理优化
- 缓存命中优化
"""
import os
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import json
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CHUNK_SIZE = 1000  # 字符
DEFAULT_CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 10


# ==================== 数据模型 ====================

@dataclass
class TextChunk:
    """文本块"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def content_hash(self) -> str:
        return hashlib.md5(self.content.encode()).hexdigest()


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    content: str
    embedding: List[float]
    file_path: str
    chunk_index: int
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SearchResult:
    """搜索结果"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "score": self.score,
            "metadata": self.metadata
        }


# ==================== Embedding 提供者 ====================

class EmbeddingProvider(ABC):
    """Embedding 提供者抽象基类"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的 embedding"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成 embedding"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding 维度"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI Embedding 提供者"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-3-small"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self._dimension = 1536 if "small" in model else 3072
        
        # 延迟导入
        self._client = None
    
    def _get_client(self):
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package required. Install with: pip install openai")
        return self._client
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的 embedding"""
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成 embedding"""
        client = self._get_client()
        response = await client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class LocalEmbeddingProvider(EmbeddingProvider):
    """本地 Embedding 提供者 (使用 sentence-transformers)"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # MiniLM 默认维度
    
    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError(
                    "sentence-transformers required. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model
    
    async def embed_text(self, text: str) -> List[float]:
        """生成单个文本的 embedding"""
        model = self._get_model()
        # 在线程池中运行
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: model.encode(text).tolist()
        )
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成 embedding"""
        model = self._get_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts).tolist()
        )
        return embeddings
    
    @property
    def dimension(self) -> int:
        return self._dimension


# ==================== 文本分块器 ====================

class TextChunker:
    """文本分块器"""
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_file(self, file_path: str) -> List[TextChunk]:
        """将文件分块"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.chunk_text(content, file_path)
        except Exception as e:
            logger.warning(f"Error chunking file {file_path}: {e}")
            return []
    
    def chunk_text(self, content: str, file_path: str = "") -> List[TextChunk]:
        """将文本分块"""
        chunks = []
        lines = content.splitlines()
        
        current_chunk = []
        current_start = 0
        current_length = 0
        
        for i, line in enumerate(lines):
            line_length = len(line) + 1  # +1 for newline
            
            if current_length + line_length > self.chunk_size and current_chunk:
                # 创建 chunk
                chunks.append(TextChunk(
                    content="\n".join(current_chunk),
                    file_path=file_path,
                    start_line=current_start + 1,
                    end_line=i,
                    chunk_index=len(chunks)
                ))
                
                # 计算重叠
                overlap_lines = []
                overlap_length = 0
                for prev_line in reversed(current_chunk):
                    if overlap_length + len(prev_line) > self.chunk_overlap:
                        break
                    overlap_lines.insert(0, prev_line)
                    overlap_length += len(prev_line) + 1
                
                current_chunk = overlap_lines
                current_start = i - len(overlap_lines)
                current_length = overlap_length
            
            current_chunk.append(line)
            current_length += line_length
        
        # 最后一个 chunk
        if current_chunk:
            chunks.append(TextChunk(
                content="\n".join(current_chunk),
                file_path=file_path,
                start_line=current_start + 1,
                end_line=len(lines),
                chunk_index=len(chunks)
            ))
        
        return chunks


# ==================== 向量存储 ====================

class VectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    async def add(self, documents: List[VectorDocument]) -> None:
        """添加文档"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = DEFAULT_TOP_K,
        filter_dict: Optional[Dict] = None
    ) -> List[SearchResult]:
        """搜索"""
        pass
    
    @abstractmethod
    async def delete_by_file(self, file_path: str) -> int:
        """删除文件的所有向量"""
        pass


class InMemoryVectorStore(VectorStore):
    """内存向量存储（用于开发和测试）"""
    
    def __init__(self):
        self.documents: Dict[str, VectorDocument] = {}
    
    async def add(self, documents: List[VectorDocument]) -> None:
        """添加文档"""
        for doc in documents:
            self.documents[doc.id] = doc
        logger.debug(f"Added {len(documents)} documents to memory store")
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = DEFAULT_TOP_K,
        filter_dict: Optional[Dict] = None
    ) -> List[SearchResult]:
        """搜索（余弦相似度）"""
        import math
        
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b) if norm_a * norm_b > 0 else 0
        
        results = []
        for doc in self.documents.values():
            # 过滤
            if filter_dict:
                skip = False
                for key, value in filter_dict.items():
                    if doc.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            
            score = cosine_similarity(query_embedding, doc.embedding)
            results.append(SearchResult(
                content=doc.content,
                file_path=doc.file_path,
                start_line=doc.start_line,
                end_line=doc.end_line,
                score=score,
                metadata=doc.metadata
            ))
        
        # 排序并返回 top_k
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    async def delete_by_file(self, file_path: str) -> int:
        """删除文件的所有向量"""
        to_delete = [
            doc_id for doc_id, doc in self.documents.items()
            if doc.file_path == file_path
        ]
        for doc_id in to_delete:
            del self.documents[doc_id]
        return len(to_delete)


class PgVectorStore(VectorStore):
    """PostgreSQL pgvector 存储"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self._pool = None
    
    async def _get_pool(self):
        if self._pool is None:
            try:
                import asyncpg
                self._pool = await asyncpg.create_pool(self.connection_string)
            except ImportError:
                raise ImportError("asyncpg required. Install with: pip install asyncpg")
        return self._pool
    
    async def init_table(self, dimension: int) -> None:
        """初始化表"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS vector_documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    embedding vector(%s),
                    file_path TEXT NOT NULL,
                    chunk_index INTEGER,
                    start_line INTEGER,
                    end_line INTEGER,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_vector_documents_file_path 
                ON vector_documents(file_path);
                
                CREATE INDEX IF NOT EXISTS idx_vector_documents_embedding 
                ON vector_documents USING ivfflat (embedding vector_cosine_ops);
            """ % dimension)
    
    async def add(self, documents: List[VectorDocument]) -> None:
        """添加文档"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            for doc in documents:
                await conn.execute("""
                    INSERT INTO vector_documents 
                    (id, content, embedding, file_path, chunk_index, start_line, end_line, metadata)
                    VALUES ($1, $2, $3::vector, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata
                """, doc.id, doc.content, doc.embedding, doc.file_path,
                    doc.chunk_index, doc.start_line, doc.end_line,
                    json.dumps(doc.metadata))
        
        logger.debug(f"Added {len(documents)} documents to pgvector")
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = DEFAULT_TOP_K,
        filter_dict: Optional[Dict] = None
    ) -> List[SearchResult]:
        """搜索"""
        pool = await self._get_pool()
        
        # 构建过滤条件
        where_clause = ""
        params = [query_embedding, top_k]
        if filter_dict:
            conditions = []
            for i, (key, value) in enumerate(filter_dict.items(), start=3):
                conditions.append(f"metadata->>'{key}' = ${i}")
                params.append(value)
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
        
        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT content, file_path, start_line, end_line, metadata,
                       1 - (embedding <=> $1::vector) as score
                FROM vector_documents
                {where_clause}
                ORDER BY embedding <=> $1::vector
                LIMIT $2
            """, *params)
        
        return [
            SearchResult(
                content=row["content"],
                file_path=row["file_path"],
                start_line=row["start_line"],
                end_line=row["end_line"],
                score=row["score"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {}
            )
            for row in rows
        ]
    
    async def delete_by_file(self, file_path: str) -> int:
        """删除文件的所有向量"""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM vector_documents WHERE file_path = $1",
                file_path
            )
            # 解析删除数量
            count = int(result.split()[-1])
            return count


# ==================== 向量索引服务 ====================

class VectorIndexerService:
    """向量索引服务
    
    使用示例:
        # 使用 OpenAI
        indexer = VectorIndexerService(
            embedding_provider=OpenAIEmbeddingProvider()
        )
        
        # 使用本地模型
        indexer = VectorIndexerService(
            embedding_provider=LocalEmbeddingProvider()
        )
        
        # 索引文件
        await indexer.index_file("/path/to/file.py")
        
        # 语义搜索
        results = await indexer.search("用户认证逻辑")
    """
    
    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        # 默认使用本地模型和内存存储
        self.embedding_provider = embedding_provider or LocalEmbeddingProvider()
        self.vector_store = vector_store or InMemoryVectorStore()
        self.chunker = TextChunker(chunk_size, chunk_overlap)
        
        self._indexed_files: Dict[str, str] = {}  # file_path -> content_hash
        
        logger.info(f"VectorIndexerService initialized with {type(self.embedding_provider).__name__}")
    
    async def index_file(self, file_path: str, metadata: Optional[Dict] = None) -> int:
        """索引单个文件
        
        Args:
            file_path: 文件路径
            metadata: 额外元数据
            
        Returns:
            int: 索引的 chunk 数量
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return 0
        
        # 检查是否需要重新索引
        try:
            with open(file_path, "rb") as f:
                content_hash = hashlib.md5(f.read()).hexdigest()
        except Exception:
            return 0
        
        if file_path in self._indexed_files:
            if self._indexed_files[file_path] == content_hash:
                logger.debug(f"File unchanged, skipping: {file_path}")
                return 0
            # 删除旧的向量
            await self.vector_store.delete_by_file(file_path)
        
        # 分块
        chunks = self.chunker.chunk_file(file_path)
        if not chunks:
            return 0
        
        # 生成 embedding
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_provider.embed_batch(texts)
        
        # 创建文档
        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            doc_id = f"{file_path}:{chunk.chunk_index}"
            doc_metadata = {
                "language": self._detect_language(file_path),
                **(metadata or {})
            }
            documents.append(VectorDocument(
                id=doc_id,
                content=chunk.content,
                embedding=embedding,
                file_path=file_path,
                chunk_index=chunk.chunk_index,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                metadata=doc_metadata
            ))
        
        # 存储
        await self.vector_store.add(documents)
        self._indexed_files[file_path] = content_hash
        
        logger.info(f"Indexed {len(documents)} chunks from {file_path}")
        return len(documents)
    
    async def index_directory(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> int:
        """索引目录
        
        Args:
            directory: 目录路径
            extensions: 要索引的扩展名列表
            exclude_patterns: 排除的模式列表
            
        Returns:
            int: 索引的总 chunk 数量
        """
        extensions = extensions or [".py", ".js", ".ts", ".md", ".txt"]
        exclude_patterns = exclude_patterns or ["node_modules", ".venv", "__pycache__"]
        
        total_chunks = 0
        root = Path(directory)
        
        for ext in extensions:
            for file_path in root.rglob(f"*{ext}"):
                # 检查排除模式
                if any(p in str(file_path) for p in exclude_patterns):
                    continue
                
                count = await self.index_file(str(file_path))
                total_chunks += count
        
        logger.info(f"Indexed {total_chunks} total chunks from {directory}")
        return total_chunks
    
    async def search(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filter_dict: Optional[Dict] = None
    ) -> List[SearchResult]:
        """语义搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            List[SearchResult]: 搜索结果
        """
        # 生成查询 embedding
        query_embedding = await self.embedding_provider.embed_text(query)
        
        # 搜索
        results = await self.vector_store.search(
            query_embedding,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        logger.debug(f"Search '{query[:50]}...' returned {len(results)} results")
        return results
    
    async def delete_file(self, file_path: str) -> int:
        """删除文件的索引"""
        count = await self.vector_store.delete_by_file(file_path)
        if file_path in self._indexed_files:
            del self._indexed_files[file_path]
        return count
    
    def _detect_language(self, file_path: str) -> str:
        """检测语言"""
        ext_to_lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".md": "markdown",
            ".txt": "text",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
        }
        ext = Path(file_path).suffix.lower()
        return ext_to_lang.get(ext, "unknown")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "indexed_files": len(self._indexed_files),
            "embedding_provider": type(self.embedding_provider).__name__,
            "vector_store": type(self.vector_store).__name__,
            "embedding_dimension": self.embedding_provider.dimension
        }


# ==================== 工厂函数 ====================

def create_vector_indexer(
    use_openai: bool = False,
    use_pgvector: bool = False,
    **kwargs
) -> VectorIndexerService:
    """创建向量索引服务
    
    Args:
        use_openai: 是否使用 OpenAI Embedding
        use_pgvector: 是否使用 pgvector 存储
        **kwargs: 传递给 VectorIndexerService 的参数
    """
    embedding_provider = None
    vector_store = None
    
    if use_openai:
        embedding_provider = OpenAIEmbeddingProvider()
    else:
        embedding_provider = LocalEmbeddingProvider()
    
    if use_pgvector:
        vector_store = PgVectorStore()
    else:
        vector_store = InMemoryVectorStore()
    
    return VectorIndexerService(
        embedding_provider=embedding_provider,
        vector_store=vector_store,
        **kwargs
    )
