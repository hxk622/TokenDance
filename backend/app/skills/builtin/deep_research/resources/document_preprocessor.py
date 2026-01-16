"""
Document Preprocessor - Deep Research 文档预处理器

使用 MarkItDown 将用户上传的文档转换为 Markdown，
便于 Agent 分析和提取关键信息。

支持场景：
- 研报 PDF → Markdown → 提取关键数据
- 财报 Excel → Table Markdown → 自动生成分析
- Word 文档 → Markdown → 作为研究素材
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ConvertedDocument:
    """转换后的文档"""
    source_path: str
    source_name: str
    file_type: str
    markdown_content: str
    char_count: int
    line_count: int
    metadata: Dict[str, Any]


class DocumentPreprocessor:
    """
    Deep Research 专用文档预处理器
    
    将用户上传的各类文档统一转换为 Markdown 格式，
    便于后续的 LLM 分析和信息提取。
    """
    
    SUPPORTED_EXTENSIONS = {
        # Office 文档
        ".pdf": "PDF Document",
        ".docx": "Word Document",
        ".doc": "Word Document (Legacy)",
        ".xlsx": "Excel Spreadsheet",
        ".xls": "Excel Spreadsheet (Legacy)",
        ".pptx": "PowerPoint Presentation",
        # 结构化数据
        ".csv": "CSV Data",
        ".json": "JSON Data",
        ".xml": "XML Data",
        # 网页
        ".html": "HTML Page",
        ".htm": "HTML Page",
        # 纯文本
        ".txt": "Plain Text",
        ".md": "Markdown (No conversion needed)",
    }
    
    def __init__(self, llm_client: Optional[Any] = None):
        """
        初始化预处理器
        
        Args:
            llm_client: LLM 客户端（用于图片描述），可选
        """
        self.llm_client = llm_client
        self._markitdown = None
    
    def _get_markitdown(self):
        """延迟初始化 MarkItDown"""
        if self._markitdown is None:
            try:
                from markitdown import MarkItDown
                self._markitdown = MarkItDown(
                    llm_client=self.llm_client,
                    enable_plugins=False
                )
                logger.info("MarkItDown initialized for DocumentPreprocessor")
            except ImportError as e:
                logger.error(f"MarkItDown not installed: {e}")
                raise ImportError(
                    "MarkItDown required for document preprocessing. "
                    "Install with: pip install markitdown"
                ) from e
        return self._markitdown
    
    def is_supported(self, file_path: str) -> bool:
        """检查文件是否支持转换"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS
    
    def get_file_type(self, file_path: str) -> str:
        """获取文件类型描述"""
        ext = Path(file_path).suffix.lower()
        return self.SUPPORTED_EXTENSIONS.get(ext, "Unknown")
    
    def convert_document(self, file_path: str) -> ConvertedDocument:
        """
        转换单个文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            ConvertedDocument: 转换结果
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = path.suffix.lower()
        
        # Markdown 文件无需转换
        if ext == ".md":
            content = path.read_text(encoding="utf-8")
            return ConvertedDocument(
                source_path=str(path),
                source_name=path.name,
                file_type="Markdown",
                markdown_content=content,
                char_count=len(content),
                line_count=content.count('\n') + 1,
                metadata={"conversion_needed": False}
            )
        
        if not self.is_supported(file_path):
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported: {list(self.SUPPORTED_EXTENSIONS.keys())}"
            )
        
        # 使用 MarkItDown 转换
        md = self._get_markitdown()
        
        logger.info(f"Converting document: {path.name}")
        result = md.convert(str(path))
        
        markdown_content = result.text_content
        file_size = path.stat().st_size
        
        return ConvertedDocument(
            source_path=str(path),
            source_name=path.name,
            file_type=self.get_file_type(file_path),
            markdown_content=markdown_content,
            char_count=len(markdown_content),
            line_count=markdown_content.count('\n') + 1,
            metadata={
                "file_size_bytes": file_size,
                "file_extension": ext,
                "conversion_needed": True
            }
        )
    
    def convert_multiple(
        self, 
        file_paths: List[str],
        skip_errors: bool = True
    ) -> Dict[str, ConvertedDocument]:
        """
        批量转换文档
        
        Args:
            file_paths: 文件路径列表
            skip_errors: 是否跳过错误继续处理
            
        Returns:
            Dict[str, ConvertedDocument]: 文件名 -> 转换结果
        """
        results = {}
        
        for file_path in file_paths:
            try:
                doc = self.convert_document(file_path)
                results[doc.source_name] = doc
                logger.info(f"Converted: {doc.source_name} ({doc.char_count} chars)")
            except Exception as e:
                logger.error(f"Failed to convert {file_path}: {e}")
                if not skip_errors:
                    raise
        
        return results
    
    def prepare_for_research(
        self,
        documents: List[ConvertedDocument],
        max_total_chars: int = 50000
    ) -> str:
        """
        将转换后的文档整理为研究上下文
        
        Args:
            documents: 转换后的文档列表
            max_total_chars: 最大总字符数（防止 Context 爆炸）
            
        Returns:
            str: 整理后的 Markdown 上下文
        """
        sections = []
        total_chars = 0
        
        for doc in documents:
            # 检查是否超出限制
            if total_chars + doc.char_count > max_total_chars:
                # 截断当前文档
                available = max_total_chars - total_chars
                if available > 500:  # 至少保留 500 字符
                    content = doc.markdown_content[:available] + "\n\n[...内容已截断...]"
                    sections.append(
                        f"## 📄 {doc.source_name}\n"
                        f"> 类型: {doc.file_type} | 原始大小: {doc.char_count} 字符 (已截断)\n\n"
                        f"{content}"
                    )
                break
            
            sections.append(
                f"## 📄 {doc.source_name}\n"
                f"> 类型: {doc.file_type} | 大小: {doc.char_count} 字符\n\n"
                f"{doc.markdown_content}"
            )
            total_chars += doc.char_count
        
        header = (
            "# 研究资料\n\n"
            f"以下是用户提供的 {len(sections)} 份参考文档，"
            "已自动转换为 Markdown 格式便于分析。\n\n"
            "---\n\n"
        )
        
        return header + "\n\n---\n\n".join(sections)
    
    def extract_financial_data(self, doc: ConvertedDocument) -> Dict[str, Any]:
        """
        从财报文档中提取关键财务数据（金融场景专用）
        
        Args:
            doc: 转换后的文档（Excel 财报）
            
        Returns:
            Dict: 提取的财务数据
        """
        content = doc.markdown_content
        
        # 简单的关键词提取（实际项目可用更复杂的 NER）
        financial_keywords = {
            "营业收入": ["营业收入", "营收", "Revenue", "Total Revenue"],
            "净利润": ["净利润", "Net Profit", "Net Income"],
            "毛利率": ["毛利率", "Gross Margin"],
            "资产负债率": ["资产负债率", "Debt Ratio"],
            "市盈率": ["市盈率", "P/E", "PE"],
        }
        
        extracted = {}
        for metric, keywords in financial_keywords.items():
            for kw in keywords:
                if kw.lower() in content.lower():
                    extracted[metric] = f"在文档中发现「{kw}」相关数据"
                    break
        
        return {
            "source": doc.source_name,
            "file_type": doc.file_type,
            "metrics_found": list(extracted.keys()),
            "details": extracted
        }
