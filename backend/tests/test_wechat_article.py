"""
WeChat Article Tool 单元测试

测试内容：
- URL 验证
- API 调用
- 错误处理
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWeChatArticleTool:
    """微信公众号文章提取工具测试"""

    @pytest.fixture
    def tool(self):
        """创建工具实例"""
        from app.agent.tools.builtin.wechat_article import WeChatArticleTool
        return WeChatArticleTool()

    # ============== URL 验证测试 ==============

    def test_validate_wechat_url_valid(self, tool):
        """测试有效的微信公众号链接"""
        valid_urls = [
            "https://mp.weixin.qq.com/s/abc123",
            "http://mp.weixin.qq.com/s/abc123",
            "mp.weixin.qq.com/s/abc123",
        ]
        for url in valid_urls:
            is_valid, error = tool._validate_wechat_url(url)
            assert is_valid, f"URL should be valid: {url}, got error: {error}"

    def test_validate_wechat_url_invalid_domain(self, tool):
        """测试非微信域名"""
        invalid_urls = [
            "https://example.com/article",
            "https://weibo.com/article",
            "https://www.baidu.com",
        ]
        for url in invalid_urls:
            is_valid, error = tool._validate_wechat_url(url)
            assert not is_valid, f"URL should be invalid: {url}"
            assert "mp.weixin.qq.com" in error

    def test_validate_wechat_url_empty(self, tool):
        """测试空 URL"""
        is_valid, error = tool._validate_wechat_url("")
        assert not is_valid
        assert "empty" in error.lower()

    # ============== 图片移除测试 ==============

    def test_remove_images_from_markdown(self, tool):
        """测试从 Markdown 中移除图片"""
        content = """
# 标题

这是一段文字。

![图片描述](https://example.com/image.png)

这是另一段文字。

![](https://example.com/another.jpg)

结束。
"""
        result = tool._remove_images_from_markdown(content)
        assert "![" not in result
        assert "这是一段文字" in result
        assert "这是另一段文字" in result
        assert "结束" in result

    # ============== API 调用测试 ==============

    @pytest.mark.asyncio
    async def test_execute_invalid_url(self, tool):
        """测试执行时使用无效 URL"""
        result = await tool.execute(url="https://example.com/article")
        assert not result["success"]
        assert "error" in result
        assert "mp.weixin.qq.com" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_empty_url(self, tool):
        """测试执行时使用空 URL"""
        result = await tool.execute(url="")
        assert not result["success"]
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_success(self, tool):
        """测试成功提取文章（Mock API）"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "title": "测试文章标题",
                "content": "# 测试文章\n\n这是文章内容。",
                "author": "测试作者",
                "publish_time": "2024-01-15"
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await tool.execute(
                url="https://mp.weixin.qq.com/s/test123",
                format="markdown"
            )

            assert result["success"]
            assert result["title"] == "测试文章标题"
            assert "测试文章" in result["content"]
            assert result["author"] == "测试作者"
            assert result["format"] == "markdown"

    @pytest.mark.asyncio
    async def test_execute_api_error(self, tool):
        """测试 API 返回错误"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 500,
            "msg": "服务器内部错误"
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await tool.execute(
                url="https://mp.weixin.qq.com/s/test123"
            )

            assert not result["success"]
            assert "API error" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_timeout(self, tool):
        """测试请求超时"""
        import httpx

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = httpx.TimeoutException("timeout")
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await tool.execute(
                url="https://mp.weixin.qq.com/s/test123"
            )

            assert not result["success"]
            assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_without_images(self, tool):
        """测试不包含图片的输出"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "code": 0,
            "data": {
                "title": "测试文章",
                "content": "# 标题\n\n![图片](https://example.com/img.png)\n\n正文内容",
                "author": "",
                "publish_time": ""
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_client.return_value = mock_instance

            result = await tool.execute(
                url="https://mp.weixin.qq.com/s/test123",
                format="markdown",
                include_images=False
            )

            assert result["success"]
            assert "![" not in result["content"]
            assert "正文内容" in result["content"]


class TestWeChatArticleToolIntegration:
    """集成测试（需要网络连接，可选）"""

    @pytest.fixture
    def tool(self):
        from app.agent.tools.builtin.wechat_article import WeChatArticleTool
        return WeChatArticleTool()

    @pytest.mark.skip(reason="需要网络连接和有效的微信文章链接")
    @pytest.mark.asyncio
    async def test_real_api_call(self, tool):
        """测试真实 API 调用（手动运行）"""
        # 替换为有效的微信文章链接
        test_url = "https://mp.weixin.qq.com/s/your-test-article"
        result = await tool.execute(url=test_url)

        print(f"Title: {result.get('title')}")
        print(f"Author: {result.get('author')}")
        print(f"Length: {result.get('length')}")
        print(f"Content preview: {result.get('content', '')[:500]}...")

        assert result["success"]
        assert result["title"]
        assert result["content"]
