"""
Unit tests for FileConverterTool.

Tests the file conversion functionality using MarkItDown.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.agent.tools.file_converter import FileConverterTool


class TestFileConverterTool:
    """Test suite for FileConverterTool."""

    @pytest.fixture
    def tool(self):
        """Create a FileConverterTool instance."""
        return FileConverterTool()

    @pytest.fixture
    def sample_txt_file(self):
        """Create a temporary text file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("# Test Document\n\nThis is a test document.\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_json_file(self):
        """Create a temporary JSON file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"name": "Test", "value": 123}')
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    @pytest.fixture
    def sample_csv_file(self):
        """Create a temporary CSV file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("Name,Age,City\n")
            f.write("Alice,30,New York\n")
            f.write("Bob,25,San Francisco\n")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_tool_metadata(self, tool):
        """Test tool metadata properties."""
        assert tool.name == "file_converter"
        assert tool.category == "File Operations"
        assert "Convert files" in tool.description
        assert "PDF" in tool.description
        assert len(tool.parameters) > 0

    def test_supported_formats(self, tool):
        """Test supported file formats list."""
        supported_formats = tool.get_supported_formats()
        all_formats = [
            ext for formats in supported_formats.values()
            for ext in formats
        ]

        # Check key formats are supported
        assert ".pdf" in all_formats
        assert ".docx" in all_formats
        assert ".xlsx" in all_formats
        assert ".txt" in all_formats
        assert ".csv" in all_formats
        assert ".json" in all_formats

    def test_text_file_conversion(self, tool, sample_txt_file):
        """Test converting a text file."""
        result = tool.execute(file_path=sample_txt_file)

        assert result is not None
        assert isinstance(result, str)
        assert "# Test Document" in result
        assert "This is a test document." in result
        assert "Source:" in result
        # Check that the filename (not full path) appears in result
        from pathlib import Path
        assert Path(sample_txt_file).name in result

    def test_json_file_conversion(self, tool, sample_json_file):
        """Test converting a JSON file."""
        result = tool.execute(file_path=sample_json_file)

        assert result is not None
        assert isinstance(result, str)
        assert "name" in result.lower() or "test" in result.lower()
        assert "Source:" in result

    def test_csv_file_conversion(self, tool, sample_csv_file):
        """Test converting a CSV file."""
        result = tool.execute(file_path=sample_csv_file)

        assert result is not None
        assert isinstance(result, str)
        # CSV should be converted to markdown table
        assert "Alice" in result
        assert "Bob" in result
        assert "New York" in result or "new york" in result.lower()

    def test_nonexistent_file(self, tool):
        """Test handling of nonexistent file."""
        with pytest.raises(FileNotFoundError):
            tool.execute(file_path="/nonexistent/file.pdf")

    def test_unsupported_format(self, tool):
        """Test handling of unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                tool.execute(file_path=temp_path)
            assert "Unsupported" in str(exc_info.value) or "not supported" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_lazy_initialization(self, tool):
        """Test that MarkItDown is lazily initialized."""
        # Should not be initialized on tool creation
        assert not hasattr(tool, "_converter") or tool._converter is None

        # Should initialize on first use
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test")
            temp_path = f.name

        try:
            tool.execute(file_path=temp_path)
            assert hasattr(tool, "_converter")
            assert tool._converter is not None
        finally:
            os.unlink(temp_path)

    def test_markdown_header_format(self, tool, sample_txt_file):
        """Test that output includes proper markdown header."""
        result = tool.execute(file_path=sample_txt_file)

        # Check header format
        lines = result.split("\n")
        assert any("---" in line for line in lines[:5])  # Front matter separator
        assert any("Source:" in line for line in lines[:10])
        assert any("Format:" in line for line in lines[:10])

    def test_file_path_validation(self, tool):
        """Test file path validation."""
        # Empty path
        with pytest.raises((ValueError, FileNotFoundError)):
            tool.execute(file_path="")

        # None path
        with pytest.raises((ValueError, TypeError)):
            tool.execute(file_path=None)  # type: ignore

    def test_markitdown_error_handling(self, tool, sample_txt_file):
        """测试处理 MarkItDown 转换错误。"""
        # Force initialize the converter first
        _ = tool._get_markitdown()

        # Then mock the convert method to raise an exception
        tool._converter.convert = Mock(side_effect=Exception("Conversion failed"))

        with pytest.raises(Exception) as exc_info:
            tool.execute(file_path=sample_txt_file)
        assert "Conversion failed" in str(exc_info.value) or "failed" in str(exc_info.value).lower()

    def test_relative_path_handling(self, tool):
        """Test handling of relative file paths."""
        # Create a file in current directory
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, dir=".") as f:
            f.write("relative test")
            temp_path = Path(f.name).name  # Get just the filename

        try:
            result = tool.execute(file_path=temp_path)
            assert result is not None
            assert "relative test" in result
        finally:
            os.unlink(temp_path)

    def test_large_file_handling(self, tool):
        """Test handling of large files (basic check)."""
        # Create a large text file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            # Write 100KB of text
            for i in range(1000):
                f.write(f"Line {i}: " + "A" * 90 + "\n")
            temp_path = f.name

        try:
            result = tool.execute(file_path=temp_path)
            assert result is not None
            assert len(result) > 0
        finally:
            os.unlink(temp_path)

    def test_special_characters_in_content(self, tool):
        """Test handling of special characters in file content."""
        special_content = "# 测试文档\n\n这是一个包含特殊字符的文档：\n- Émoji: 🎉\n- Unicode: ≈ ≠ ∞\n"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(special_content)
            temp_path = f.name

        try:
            result = tool.execute(file_path=temp_path)
            assert result is not None
            # Should preserve Unicode characters
            assert "测试文档" in result or "test" in result.lower()
        finally:
            os.unlink(temp_path)
