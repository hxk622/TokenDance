"""
Embedding 模块 - 提供语义向量化能力

支持多种 Embedding 实现：
1. SentenceTransformerEmbedding - 本地免费方案（默认）
2. OpenAIEmbedding - OpenAI API（付费，效果更好）
3. SimpleEmbedding - TF-IDF 降级方案（无需额外依赖）
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger(__name__)


class BaseEmbedding(ABC):
    """Embedding 抽象基类"""

    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """将文本编码为向量
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        pass

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本
        
        Args:
            texts: 输入文本列表
            
        Returns:
            向量列表的列表
        """
        return [self.encode(text) for text in texts]


class SentenceTransformerEmbedding(BaseEmbedding):
    """基于 sentence-transformers 的本地 Embedding
    
    使用 all-MiniLM-L6-v2 模型：
    - 完全免费，本地运行
    - 模型小（~80MB），加载快
    - 384 维向量
    - 多语言支持
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
    ):
        """初始化
        
        Args:
            model_name: 模型名称，默认 all-MiniLM-L6-v2
            device: 运行设备，None 表示自动选择（优先 GPU）
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._initialized = False

    def _lazy_init(self):
        """懒加载模型（首次使用时加载）"""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._initialized = True
            logger.info(f"Embedding model loaded successfully (dim={self._model.get_sentence_embedding_dimension()})")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

    def encode(self, text: str) -> List[float]:
        """将文本编码为向量"""
        self._lazy_init()
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本（利用 GPU 并行）"""
        self._lazy_init()
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """获取向量维度"""
        self._lazy_init()
        return self._model.get_sentence_embedding_dimension()


class OpenAIEmbedding(BaseEmbedding):
    """基于 OpenAI API 的 Embedding
    
    使用 text-embedding-3-small 模型：
    - 付费（$0.02/1M tokens）
    - 效果好
    - 1536 维向量
    """

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """初始化
        
        Args:
            api_key: OpenAI API Key
            model: 模型名称
        """
        self.api_key = api_key
        self.model = model
        self._client = None

    def _lazy_init(self):
        """懒加载客户端"""
        if self._client is not None:
            return

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)
        except ImportError:
            logger.error("openai not installed. Run: pip install openai")
            raise

    def encode(self, text: str) -> List[float]:
        """将文本编码为向量"""
        self._lazy_init()
        response = self._client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        self._lazy_init()
        response = self._client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


# 全局单例
_embedding_model: Optional[BaseEmbedding] = None


def get_embedding_model() -> BaseEmbedding:
    """获取全局 Embedding 模型单例
    
    默认使用 SentenceTransformerEmbedding（免费本地方案）
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformerEmbedding()
    return _embedding_model


def set_embedding_model(model: BaseEmbedding) -> None:
    """设置全局 Embedding 模型
    
    Args:
        model: Embedding 模型实例
    """
    global _embedding_model
    _embedding_model = model
