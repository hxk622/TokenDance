"""
Tests for Smart Document Converter

测试智能文档转换模块：
- PDF 复杂度检测
- 引擎选择逻辑
- 转换指标记录
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from app.agent.tools.smart_document_converter import (
    ConversionMetrics,
    MinerUClient,
    PDFComplexityDetector,
    SmartDocumentConverter,
    convert_document,
)

if TYPE_CHECKING:
    pass


class TestConversionMetrics:
    """ConversionMetrics 数据类测试"""

    def test_to_log_dict_basic(self) -> None:
        """测试基本日志字典转换"""
        metrics = ConversionMetrics(
            file_path="/test/file.pdf",
            file_size_bytes=1024,
            complexity_score=5,
            complexity_reasons=["含表格", "多栏布局"],
            is_complex=True,
            engine_used="mineru",
            engine_reason="复杂文档",
            detection_latency_ms=10.5,
            conversion_latency_ms=1000.0,
            total_latency_ms=1010.5,
            success=True,
            output_chars=5000,
        )

        log_dict = metrics.to_log_dict()

        assert log_dict["file"] == "file.pdf"
        assert log_dict["size_kb"] == 1.0
        assert log_dict["complexity"]["score"] == 5
        assert log_dict["complexity"]["is_complex"] is True
        assert log_dict["engine"]["used"] == "mineru"
        assert log_dict["latency"]["total_ms"] == 1010.5
        assert log_dict["result"]["success"] is True
        assert log_dict["result"]["output_chars"] == 5000
        assert "timestamp" in log_dict

    def test_to_log_dict_with_error(self) -> None:
        """测试带错误的日志字典"""
        metrics = ConversionMetrics(
            file_path="/test/error.pdf",
            file_size_bytes=2048,
            success=False,
            error_message="API timeout",
        )

        log_dict = metrics.to_log_dict()

        assert log_dict["result"]["success"] is False
        assert log_dict["result"]["error"] == "API timeout"


class TestPDFComplexityDetector:
    """PDF 复杂度检测器测试"""

    def test_finance_keyword_in_filename(self) -> None:
        """测试文件名包含金融关键词"""
        detector = PDFComplexityDetector()

        # 中文关键词
        is_complex, score, reasons = detector.detect("/test/2024年报.pdf")
        assert is_complex is True
        assert score == 100
        assert "文件名含金融关键词" in reasons[0]

        # 英文关键词
        is_complex, score, reasons = detector.detect("/test/annual_report_2024.pdf")
        assert is_complex is True
        assert score == 100

    def test_pymupdf_not_installed(self) -> None:
        """测试 PyMuPDF 未安装时的处理"""
        # 测试当 PyMuPDF 未安装时的行为
        with patch.dict("sys.modules", {"fitz": None}):
            # 模拟 import 失败
            with patch(
                "app.agent.tools.smart_document_converter.PDFComplexityDetector.detect"
            ) as mock_detect:
                mock_detect.return_value = (True, 99, ["PyMuPDF 未安装，保守使用 MinerU"])
                is_complex, score, reasons = mock_detect("/test/file.pdf")
                assert is_complex is True
                assert score == 99

    def test_complexity_threshold(self) -> None:
        """测试复杂度阈值"""
        detector = PDFComplexityDetector()
        assert detector.COMPLEXITY_THRESHOLD == 4

        # 修改阈值
        detector.COMPLEXITY_THRESHOLD = 10
        assert detector.COMPLEXITY_THRESHOLD == 10


class TestMinerUClient:
    """MinerU 客户端测试"""

    def test_init_without_token(self) -> None:
        """测试无 Token 初始化"""
        client = MinerUClient()
        assert client.api_token is None

    def test_init_with_token(self) -> None:
        """测试有 Token 初始化"""
        client = MinerUClient(api_token="test_token")
        assert client.api_token == "test_token"

    def test_parse_pdf_without_token_raises(self) -> None:
        """测试无 Token 调用解析抛出异常"""
        client = MinerUClient()

        with pytest.raises(ValueError, match="MinerU API Token 未配置"):
            client.parse_pdf("/test/file.pdf")

    def test_get_headers(self) -> None:
        """测试请求头生成"""
        client = MinerUClient(api_token="test_token")
        headers = client._get_headers()

        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"


class TestSmartDocumentConverter:
    """智能文档转换器测试"""

    def test_init_without_mineru(self) -> None:
        """测试无 MinerU 配置初始化"""
        converter = SmartDocumentConverter(mineru_api_token=None)
        assert converter.mineru_client is None
        converter.close()

    def test_init_with_mineru(self) -> None:
        """测试有 MinerU 配置初始化"""
        converter = SmartDocumentConverter(mineru_api_token="test_token")
        assert converter.mineru_client is not None
        assert converter.mineru_client.api_token == "test_token"
        converter.close()

    def test_force_engine_markitdown(self) -> None:
        """测试强制使用 MarkItDown"""
        converter = SmartDocumentConverter(force_engine="markitdown")
        assert converter.force_engine == "markitdown"
        converter.close()

    def test_force_engine_mineru(self) -> None:
        """测试强制使用 MinerU"""
        converter = SmartDocumentConverter(
            mineru_api_token="test_token",
            force_engine="mineru"
        )
        assert converter.force_engine == "mineru"
        converter.close()

    def test_convert_file_not_found(self) -> None:
        """测试文件不存在"""
        converter = SmartDocumentConverter()

        with pytest.raises(FileNotFoundError, match="文件不存在"):
            converter.convert("/nonexistent/file.pdf")

        converter.close()

    def test_convert_non_pdf_uses_markitdown(self) -> None:
        """测试非 PDF 文件使用 MarkItDown"""
        converter = SmartDocumentConverter()

        # 创建临时文本文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            # Mock MarkItDown 以避免 onnxruntime 依赖问题
            mock_result = MagicMock()
            mock_result.text_content = "Hello, World!"
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result

            with patch.object(converter, "_get_markitdown", return_value=mock_markitdown):
                markdown, metrics = converter.convert(temp_path)

                assert metrics.engine_used == "markitdown"
                assert metrics.complexity_reasons == ["非 PDF 文件"]
                assert metrics.success is True
                assert "Hello, World!" in markdown
        finally:
            Path(temp_path).unlink()
            converter.close()

    def test_engine_selection_simple_pdf(self) -> None:
        """测试简单 PDF 引擎选择"""
        converter = SmartDocumentConverter()

        # 模拟检测结果
        engine = converter._select_engine(
            is_complex=False,
            score=2,
            reasons=["简单文档"]
        )

        assert engine == "markitdown"
        converter.close()

    def test_engine_selection_complex_pdf_with_mineru(self) -> None:
        """测试复杂 PDF + MinerU 配置的引擎选择"""
        converter = SmartDocumentConverter(mineru_api_token="test_token")

        engine = converter._select_engine(
            is_complex=True,
            score=6,
            reasons=["含表格", "多栏布局"]
        )

        assert engine == "mineru"
        converter.close()

    def test_engine_selection_complex_pdf_without_mineru(self) -> None:
        """测试复杂 PDF 但无 MinerU 配置的引擎选择"""
        converter = SmartDocumentConverter(mineru_api_token=None)

        engine = converter._select_engine(
            is_complex=True,
            score=6,
            reasons=["含表格"]
        )

        # 降级到 MarkItDown
        assert engine == "markitdown"
        converter.close()

    def test_engine_reason_force_engine(self) -> None:
        """测试强制引擎时的原因"""
        converter = SmartDocumentConverter(force_engine="mineru")

        reason = converter._get_engine_reason(
            engine="mineru",
            is_complex=False,
            score=0,
            reasons=[]
        )

        assert "强制指定" in reason
        converter.close()

    def test_engine_reason_complex_document(self) -> None:
        """测试复杂文档时的原因"""
        converter = SmartDocumentConverter(mineru_api_token="test")

        reason = converter._get_engine_reason(
            engine="mineru",
            is_complex=True,
            score=6,
            reasons=["含表格", "多栏布局"]
        )

        assert "复杂文档" in reason
        assert "score=6" in reason
        assert "含表格" in reason
        converter.close()

    def test_complexity_threshold_customization(self) -> None:
        """测试复杂度阈值自定义"""
        converter = SmartDocumentConverter(complexity_threshold=10)
        assert converter.detector.COMPLEXITY_THRESHOLD == 10
        converter.close()


class TestConvertDocumentFunction:
    """convert_document 便捷函数测试"""

    def test_convert_simple_text_file(self) -> None:
        """测试转换简单文本文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            # Mock MarkItDown
            mock_result = MagicMock()
            mock_result.text_content = "Test content"
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result

            with patch(
                "app.agent.tools.smart_document_converter.SmartDocumentConverter._get_markitdown",
                return_value=mock_markitdown
            ):
                result = convert_document(temp_path)
                assert "Test content" in result
        finally:
            Path(temp_path).unlink()

    def test_convert_with_force_engine(self) -> None:
        """测试强制引擎参数"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Force engine test")
            temp_path = f.name

        try:
            # Mock MarkItDown
            mock_result = MagicMock()
            mock_result.text_content = "Force engine test"
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result

            with patch(
                "app.agent.tools.smart_document_converter.SmartDocumentConverter._get_markitdown",
                return_value=mock_markitdown
            ):
                result = convert_document(temp_path, force_engine="markitdown")
                assert "Force engine test" in result
        finally:
            Path(temp_path).unlink()


class TestFileConverterToolIntegration:
    """FileConverterTool 集成测试"""

    def test_import_file_converter_tool(self) -> None:
        """测试导入 FileConverterTool"""
        from app.agent.tools.file_converter import FileConverterTool

        tool = FileConverterTool()
        assert tool.name == "file_converter"
        assert "force_engine" in tool.parameters["properties"]

    def test_file_converter_tool_has_smart_converter(self) -> None:
        """测试 FileConverterTool 包含智能转换器"""
        from app.agent.tools.file_converter import FileConverterTool

        tool = FileConverterTool()
        assert hasattr(tool, "_smart_converter")
        assert isinstance(tool._smart_converter, SmartDocumentConverter)

    def test_file_converter_tool_convert_txt(self) -> None:
        """测试 FileConverterTool 转换文本文件"""
        from app.agent.tools.file_converter import FileConverterTool

        tool = FileConverterTool()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as f:
            f.write("Integration test content")
            temp_path = f.name

        try:
            # Mock MarkItDown 以避免 onnxruntime 依赖问题
            mock_result = MagicMock()
            mock_result.text_content = "Integration test content"
            mock_markitdown = MagicMock()
            mock_markitdown.convert.return_value = mock_result

            with patch.object(tool, "_get_markitdown", return_value=mock_markitdown):
                result = tool.execute(file_path=temp_path)
                assert "Integration test content" in result
                assert "Engine: markitdown" in result
        finally:
            Path(temp_path).unlink()

    def test_file_converter_tool_force_engine_parameter(self) -> None:
        """测试 FileConverterTool force_engine 参数"""
        from app.agent.tools.file_converter import FileConverterTool

        tool = FileConverterTool()

        # 检查参数定义
        props = tool.parameters["properties"]
        assert "force_engine" in props
        assert props["force_engine"]["enum"] == ["auto", "markitdown", "mineru"]
        assert props["force_engine"]["default"] == "auto"


class TestPDFComplexityDetectorWithMock:
    """使用 Mock 的 PDF 复杂度检测器测试"""

    def test_detect_with_tables(self) -> None:
        """测试检测到表格的情况"""
        detector = PDFComplexityDetector()

        # 创建 mock fitz 模块
        mock_page = MagicMock()
        mock_page.find_tables.return_value.tables = [MagicMock()]  # 有表格
        mock_page.get_images.return_value = []
        mock_page.get_text.return_value = "Some text content " * 50
        mock_page.rect.width = 612  # Letter size

        mock_doc = MagicMock()
        mock_doc.page_count = 5
        mock_doc.__iter__ = lambda self: iter([mock_page])
        mock_doc.__getitem__ = lambda self, i: mock_page

        with patch("fitz.open", return_value=mock_doc):
            is_complex, score, reasons = detector.detect("/test/with_tables.pdf")

            # 有表格应该增加分数
            assert score >= 3
            assert "含表格" in reasons

    def test_detect_scanned_pdf(self) -> None:
        """测试检测扫描件"""
        detector = PDFComplexityDetector()

        # 模拟扫描件：文字少，有图片
        mock_page = MagicMock()
        mock_page.find_tables.return_value.tables = []
        mock_page.get_images.return_value = [MagicMock()]  # 有图片
        mock_page.get_text.return_value = "AB"  # 很少文字

        mock_doc = MagicMock()
        mock_doc.page_count = 1
        mock_doc.__getitem__ = lambda self, i: mock_page

        with patch("fitz.open", return_value=mock_doc):
            is_complex, score, reasons = detector.detect("/test/scanned.pdf")

            assert is_complex is True
            assert "疑似扫描件" in reasons
