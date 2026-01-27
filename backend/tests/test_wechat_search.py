"""
Tests for WeChat search tool.

Tests the wechat_search tool functionality.
"""
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.tools.builtin.wechat_search import (
    WeChatSearchTool,
    create_wechat_search_tool,
    wechat_search_tool,
)


class TestWeChatSearchTool:
    """Tests for WeChatSearchTool."""

    def test_tool_creation(self):
        """Test that tool can be created."""
        tool = WeChatSearchTool()
        assert tool.name == "wechat_search"
        assert tool.risk_level.value == "none"

    def test_factory_function(self):
        """Test factory function."""
        tool = create_wechat_search_tool()
        assert isinstance(tool, WeChatSearchTool)

    def test_global_instance(self):
        """Test global instance exists."""
        assert wechat_search_tool is not None
        assert isinstance(wechat_search_tool, WeChatSearchTool)

    def test_parameters_schema(self):
        """Test parameters schema is correct."""
        tool = WeChatSearchTool()
        params = tool.parameters

        assert params["type"] == "object"
        assert "query" in params["properties"]
        assert "max_results" in params["properties"]
        assert "account_name" in params["properties"]
        assert params["required"] == ["query"]

    @pytest.mark.asyncio
    async def test_empty_query_returns_error(self):
        """Test that empty query returns error."""
        tool = WeChatSearchTool()
        result = await tool.execute(query="")

        assert result["success"] is False
        assert "Query parameter is required" in result["error"]

    @pytest.mark.asyncio
    async def test_query_construction(self):
        """Test that query is correctly constructed with site: filter."""
        tool = WeChatSearchTool()

        # Mock the searcher
        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": True,
            "results": [
                {
                    "title": "Test Article",
                    "link": "https://mp.weixin.qq.com/s/abc123",
                    "snippet": "Test snippet"
                }
            ],
            "provider": "serper"
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            await tool.execute(query="AI Agent")

            # Verify search was called with site: filter
            mock_searcher.search.assert_called_once()
            call_args = mock_searcher.search.call_args
            assert "site:mp.weixin.qq.com" in call_args[0][0]
            assert "AI Agent" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_account_name_filter(self):
        """Test that account_name is added to query."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": True,
            "results": [],
            "provider": "serper"
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            await tool.execute(query="AI", account_name="36氪")

            call_args = mock_searcher.search.call_args
            query = call_args[0][0]
            assert "36氪" in query
            assert "AI" in query
            assert "site:mp.weixin.qq.com" in query

    @pytest.mark.asyncio
    async def test_result_filtering(self):
        """Test that non-WeChat results are filtered out."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": True,
            "results": [
                {
                    "title": "WeChat Article",
                    "link": "https://mp.weixin.qq.com/s/abc123",
                    "snippet": "WeChat content"
                },
                {
                    "title": "Non-WeChat",
                    "link": "https://example.com/article",
                    "snippet": "Other content"
                },
                {
                    "title": "Another WeChat",
                    "link": "https://mp.weixin.qq.com/s/def456",
                    "snippet": "More WeChat content"
                }
            ],
            "provider": "serper"
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            result = await tool.execute(query="test")

            assert result["success"] is True
            assert result["count"] == 2
            # All results should be WeChat links
            for r in result["results"]:
                assert "mp.weixin.qq.com" in r["link"]

    @pytest.mark.asyncio
    async def test_max_results_limit(self):
        """Test that max_results is respected."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": True,
            "results": [
                {"title": f"Article {i}", "link": f"https://mp.weixin.qq.com/s/{i}", "snippet": ""}
                for i in range(10)
            ],
            "provider": "serper"
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            result = await tool.execute(query="test", max_results=3)

            assert result["success"] is True
            assert result["count"] == 3
            assert len(result["results"]) == 3

    @pytest.mark.asyncio
    async def test_search_failure_handling(self):
        """Test handling of search failures."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": False,
            "errors": ["API error"]
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            result = await tool.execute(query="test")

            assert result["success"] is False
            assert "Search failed" in result["error"]

    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """Test handling of exceptions."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(side_effect=Exception("Network error"))

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            result = await tool.execute(query="test")

            assert result["success"] is False
            assert "Network error" in result["error"]

    @pytest.mark.asyncio
    async def test_result_structure(self):
        """Test that result has correct structure."""
        tool = WeChatSearchTool()

        mock_searcher = AsyncMock()
        mock_searcher.search = AsyncMock(return_value={
            "success": True,
            "results": [
                {
                    "title": "Test",
                    "link": "https://mp.weixin.qq.com/s/abc",
                    "snippet": "Content"
                }
            ],
            "provider": "serper"
        })

        with patch.object(tool, "_get_searcher", return_value=mock_searcher):
            result = await tool.execute(query="test")

            # Check top-level structure
            assert "success" in result
            assert "query" in result
            assert "wechat_query" in result
            assert "count" in result
            assert "results" in result
            assert "provider" in result
            assert "hint" in result

            # Check result item structure
            if result["results"]:
                item = result["results"][0]
                assert "title" in item
                assert "link" in item
                assert "snippet" in item


class TestIntegration:
    """Integration tests (require network and API keys)."""

    @pytest.mark.skip(reason="Requires network and API keys")
    @pytest.mark.asyncio
    async def test_real_search(self):
        """Test real search (requires SERPER_API_KEY)."""
        tool = WeChatSearchTool()
        result = await tool.execute(query="AI Agent", max_results=5)

        print(f"Found {result.get('count', 0)} results")
        for r in result.get("results", []):
            print(f"  - {r['title']}: {r['link']}")

        assert result["success"] is True
