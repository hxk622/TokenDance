"""
Document Parser Service - 文档智能解析

支持多种文档格式的智能解析，包括：
- 学术论文 (PDF)
- 财报文档
- 通用文档 (PDF, DOCX, TXT)
"""
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import BinaryIO


class DocumentType(str, Enum):
    """文档类型"""
    ACADEMIC_PAPER = "academic_paper"
    FINANCIAL_REPORT = "financial_report"
    NEWS_ARTICLE = "news_article"
    GENERAL = "general"
    UNKNOWN = "unknown"


class SectionType(str, Enum):
    """章节类型"""
    TITLE = "title"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    METHODOLOGY = "methodology"
    RESULTS = "results"
    DISCUSSION = "discussion"
    CONCLUSION = "conclusion"
    REFERENCES = "references"
    APPENDIX = "appendix"
    # 财报特有
    FINANCIAL_SUMMARY = "financial_summary"
    REVENUE = "revenue"
    EXPENSES = "expenses"
    PROFIT_LOSS = "profit_loss"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"
    RISK_FACTORS = "risk_factors"
    # 通用
    BODY = "body"
    HEADER = "header"
    FOOTER = "footer"


@dataclass
class DocumentMetadata:
    """文档元数据"""
    title: str = ""
    authors: list[str] = field(default_factory=list)
    publication_date: datetime | None = None
    source: str = ""
    doi: str | None = None
    keywords: list[str] = field(default_factory=list)
    language: str = "unknown"
    page_count: int = 0
    word_count: int = 0


@dataclass
class DocumentSection:
    """文档章节"""
    id: str
    type: SectionType
    title: str
    content: str
    page_start: int = 0
    page_end: int = 0
    confidence: float = 1.0


@dataclass
class ExtractedTable:
    """提取的表格"""
    id: str
    title: str
    headers: list[str]
    rows: list[list[str]]
    page: int = 0


@dataclass
class ExtractedFigure:
    """提取的图表"""
    id: str
    title: str
    caption: str
    page: int = 0
    image_data: bytes | None = None


@dataclass
class Citation:
    """引用"""
    id: str
    text: str
    authors: list[str]
    title: str
    year: int | None = None
    source: str = ""


@dataclass
class ParsedDocument:
    """解析后的文档"""
    id: str
    filename: str
    document_type: DocumentType
    metadata: DocumentMetadata
    sections: list[DocumentSection]
    tables: list[ExtractedTable] = field(default_factory=list)
    figures: list[ExtractedFigure] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    raw_text: str = ""
    parsed_at: datetime = field(default_factory=datetime.utcnow)


class BaseDocumentParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    def can_parse(self, filename: str, content_type: str) -> bool:
        """判断是否可以解析该文档"""
        pass

    @abstractmethod
    async def parse(self, file: BinaryIO, filename: str) -> ParsedDocument:
        """解析文档"""
        pass

    def _generate_id(self, content: bytes) -> str:
        """生成文档 ID"""
        return hashlib.sha256(content).hexdigest()[:16]

    def _detect_language(self, text: str) -> str:
        """检测语言"""
        # 简单检测：中文字符比例
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        total_chars = len(text.replace(' ', ''))

        if total_chars == 0:
            return "unknown"

        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.3:
            return "zh"
        return "en"


class AcademicPaperParser(BaseDocumentParser):
    """学术论文解析器"""

    # 常见学术论文章节标题模式
    SECTION_PATTERNS = {
        SectionType.ABSTRACT: [r'abstract', r'摘要', r'概要'],
        SectionType.INTRODUCTION: [r'introduction', r'引言', r'前言', r'1\.\s*introduction'],
        SectionType.METHODOLOGY: [r'method', r'methodology', r'materials?\s*and\s*methods?', r'方法', r'研究方法'],
        SectionType.RESULTS: [r'results?', r'findings?', r'结果', r'研究结果'],
        SectionType.DISCUSSION: [r'discussion', r'讨论', r'分析与讨论'],
        SectionType.CONCLUSION: [r'conclusion', r'conclusions?', r'结论', r'结语'],
        SectionType.REFERENCES: [r'references?', r'bibliography', r'参考文献', r'引用文献'],
    }

    def can_parse(self, filename: str, content_type: str) -> bool:
        return filename.lower().endswith('.pdf') or content_type == 'application/pdf'

    async def parse(self, file: BinaryIO, filename: str) -> ParsedDocument:
        """解析学术论文"""
        content = file.read()
        doc_id = self._generate_id(content)

        # 模拟解析（实际应使用 PyPDF2, pdfplumber 等）
        raw_text = self._extract_text(content)

        # 提取元数据
        metadata = self._extract_metadata(raw_text)

        # 识别章节
        sections = self._identify_sections(raw_text)

        # 提取引用
        citations = self._extract_citations(raw_text)

        return ParsedDocument(
            id=doc_id,
            filename=filename,
            document_type=DocumentType.ACADEMIC_PAPER,
            metadata=metadata,
            sections=sections,
            citations=citations,
            raw_text=raw_text,
        )

    def _extract_text(self, content: bytes) -> str:
        """提取文本（模拟）"""
        # 实际应使用 PDF 解析库
        return f"[Academic Paper Content - {len(content)} bytes]"

    def _extract_metadata(self, text: str) -> DocumentMetadata:
        """提取元数据"""
        return DocumentMetadata(
            title="Sample Academic Paper",
            authors=["Author 1", "Author 2"],
            language=self._detect_language(text),
        )

    def _identify_sections(self, text: str) -> list[DocumentSection]:
        """识别章节"""
        sections = []

        # 模拟章节识别
        for section_type, _patterns in self.SECTION_PATTERNS.items():
            section = DocumentSection(
                id=f"section-{section_type.value}",
                type=section_type,
                title=section_type.value.replace('_', ' ').title(),
                content=f"[{section_type.value} content]",
                confidence=0.9,
            )
            sections.append(section)

        return sections

    def _extract_citations(self, text: str) -> list[Citation]:
        """提取引用"""
        # 模拟引用提取
        return [
            Citation(
                id="cite-1",
                text="Smith et al., 2023",
                authors=["Smith", "Jones"],
                title="Sample Reference",
                year=2023,
            )
        ]


class FinancialReportParser(BaseDocumentParser):
    """财报文档解析器"""

    # 财报关键词模式
    FINANCIAL_PATTERNS = {
        SectionType.FINANCIAL_SUMMARY: [r'financial\s*highlights?', r'财务摘要', r'业绩亮点'],
        SectionType.REVENUE: [r'revenue', r'sales', r'营业收入', r'营收'],
        SectionType.EXPENSES: [r'expenses?', r'costs?', r'营业成本', r'费用'],
        SectionType.PROFIT_LOSS: [r'profit', r'loss', r'income\s*statement', r'利润', r'亏损'],
        SectionType.BALANCE_SHEET: [r'balance\s*sheet', r'资产负债表'],
        SectionType.CASH_FLOW: [r'cash\s*flow', r'现金流'],
        SectionType.RISK_FACTORS: [r'risk\s*factors?', r'风险因素', r'风险提示'],
    }

    def can_parse(self, filename: str, content_type: str) -> bool:
        # 检查文件名是否包含财报相关关键词
        financial_keywords = ['annual', 'quarterly', 'report', '年报', '季报', '财报']
        filename_lower = filename.lower()
        return any(kw in filename_lower for kw in financial_keywords)

    async def parse(self, file: BinaryIO, filename: str) -> ParsedDocument:
        """解析财报"""
        content = file.read()
        doc_id = self._generate_id(content)

        raw_text = self._extract_text(content)
        metadata = self._extract_metadata(raw_text, filename)
        sections = self._identify_sections(raw_text)
        tables = self._extract_tables(raw_text)

        return ParsedDocument(
            id=doc_id,
            filename=filename,
            document_type=DocumentType.FINANCIAL_REPORT,
            metadata=metadata,
            sections=sections,
            tables=tables,
            raw_text=raw_text,
        )

    def _extract_text(self, content: bytes) -> str:
        """提取文本"""
        return f"[Financial Report Content - {len(content)} bytes]"

    def _extract_metadata(self, text: str, filename: str) -> DocumentMetadata:
        """提取财报元数据"""
        return DocumentMetadata(
            title=f"Financial Report - {filename}",
            source="Company Annual Report",
            language=self._detect_language(text),
        )

    def _identify_sections(self, text: str) -> list[DocumentSection]:
        """识别财报章节"""
        sections = []

        for section_type, _patterns in self.FINANCIAL_PATTERNS.items():
            section = DocumentSection(
                id=f"section-{section_type.value}",
                type=section_type,
                title=section_type.value.replace('_', ' ').title(),
                content=f"[{section_type.value} data]",
                confidence=0.85,
            )
            sections.append(section)

        return sections

    def _extract_tables(self, text: str) -> list[ExtractedTable]:
        """提取财务表格"""
        # 模拟表格提取
        return [
            ExtractedTable(
                id="table-1",
                title="Revenue Summary",
                headers=["Year", "Revenue", "Growth"],
                rows=[
                    ["2023", "$1,000,000", "10%"],
                    ["2022", "$909,090", "8%"],
                ],
            )
        ]


class GeneralDocumentParser(BaseDocumentParser):
    """通用文档解析器"""

    SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx']

    def can_parse(self, filename: str, content_type: str) -> bool:
        ext = '.' + filename.lower().split('.')[-1] if '.' in filename else ''
        return ext in self.SUPPORTED_EXTENSIONS

    async def parse(self, file: BinaryIO, filename: str) -> ParsedDocument:
        """解析通用文档"""
        content = file.read()
        doc_id = self._generate_id(content)

        # 根据扩展名处理
        ext = filename.lower().split('.')[-1] if '.' in filename else ''

        if ext == 'txt' or ext == 'md':
            raw_text = content.decode('utf-8', errors='ignore')
        else:
            raw_text = f"[Document Content - {len(content)} bytes]"

        metadata = DocumentMetadata(
            title=filename,
            word_count=len(raw_text.split()),
            language=self._detect_language(raw_text),
        )

        sections = [
            DocumentSection(
                id="section-body",
                type=SectionType.BODY,
                title="Content",
                content=raw_text,
            )
        ]

        return ParsedDocument(
            id=doc_id,
            filename=filename,
            document_type=DocumentType.GENERAL,
            metadata=metadata,
            sections=sections,
            raw_text=raw_text,
        )


class DocumentParserService:
    """文档解析服务"""

    def __init__(self):
        self.parsers: list[BaseDocumentParser] = [
            AcademicPaperParser(),
            FinancialReportParser(),
            GeneralDocumentParser(),
        ]

    def detect_document_type(self, filename: str, content: bytes) -> DocumentType:
        """检测文档类型"""
        filename_lower = filename.lower()

        # 学术论文检测
        academic_keywords = ['paper', 'journal', 'research', 'study', 'arxiv']
        if any(kw in filename_lower for kw in academic_keywords):
            return DocumentType.ACADEMIC_PAPER

        # 财报检测
        financial_keywords = ['annual', 'quarterly', 'report', 'financial', '年报', '季报']
        if any(kw in filename_lower for kw in financial_keywords):
            return DocumentType.FINANCIAL_REPORT

        return DocumentType.GENERAL

    async def parse(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str = "",
    ) -> ParsedDocument:
        """
        解析文档

        Args:
            file: 文件对象
            filename: 文件名
            content_type: MIME 类型

        Returns:
            ParsedDocument: 解析结果
        """
        # 选择合适的解析器
        for parser in self.parsers:
            if parser.can_parse(filename, content_type):
                return await parser.parse(file, filename)

        # 默认使用通用解析器
        return await self.parsers[-1].parse(file, filename)

    def extract_key_findings(
        self,
        document: ParsedDocument,
        max_findings: int = 10,
    ) -> list[str]:
        """
        提取文档关键发现

        Args:
            document: 解析后的文档
            max_findings: 最大发现数

        Returns:
            list[str]: 关键发现列表
        """
        findings = []

        # 从不同章节提取
        priority_sections = [
            SectionType.ABSTRACT,
            SectionType.CONCLUSION,
            SectionType.RESULTS,
            SectionType.FINANCIAL_SUMMARY,
        ]

        for section_type in priority_sections:
            for section in document.sections:
                if section.type == section_type:
                    # 提取要点（模拟）
                    findings.append(f"[Key finding from {section_type.value}]")

        return findings[:max_findings]

    def get_research_context(
        self,
        document: ParsedDocument,
    ) -> dict:
        """
        获取研究上下文

        将解析的文档转换为可用于研究的上下文
        """
        return {
            "document_id": document.id,
            "document_type": document.document_type.value,
            "title": document.metadata.title,
            "authors": document.metadata.authors,
            "language": document.metadata.language,
            "sections": [
                {
                    "type": s.type.value,
                    "title": s.title,
                    "summary": s.content[:200] if len(s.content) > 200 else s.content,
                }
                for s in document.sections
            ],
            "tables_count": len(document.tables),
            "figures_count": len(document.figures),
            "citations_count": len(document.citations),
        }


# 单例
_parser_service: DocumentParserService | None = None


def get_document_parser() -> DocumentParserService:
    """获取文档解析服务单例"""
    global _parser_service
    if _parser_service is None:
        _parser_service = DocumentParserService()
    return _parser_service
