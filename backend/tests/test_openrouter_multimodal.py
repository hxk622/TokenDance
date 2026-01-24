"""
OpenRouterLLM 多模态消息格式化测试

测试 _format_messages() 和 _format_content() 对多模态内容的支持。
"""
import pytest

from app.agent.llm.base import ImageContent, LLMMessage, TextContent
from app.agent.llm.openrouter import OpenRouterLLM


class TestOpenRouterMultimodal:
    """OpenRouterLLM 多模态消息测试"""

    @pytest.fixture
    def llm(self) -> OpenRouterLLM:
        """创建测试用 LLM 实例"""
        return OpenRouterLLM(
            api_key="test-key",
            model="anthropic/claude-3-5-sonnet",
            max_tokens=4096
        )

    def test_format_text_only_message(self, llm: OpenRouterLLM):
        """测试纯文本消息格式化"""
        messages = [
            {"role": "user", "content": "Hello, world!"}
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Hello, world!"

    def test_format_message_with_system(self, llm: OpenRouterLLM):
        """测试带 system 提示的消息格式化"""
        messages = [
            {"role": "user", "content": "What is 2+2?"}
        ]

        formatted = llm._format_messages(messages, system="You are a helpful assistant.")

        assert len(formatted) == 2
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == "You are a helpful assistant."
        assert formatted[1]["role"] == "user"

    def test_format_multimodal_message_dict(self, llm: OpenRouterLLM):
        """测试多模态消息格式化（dict 格式）"""
        multimodal_content = [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc123"}},
            {"type": "text", "text": "What's in this image?"}
        ]
        messages = [
            {"role": "user", "content": multimodal_content}
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"

        content = formatted[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["type"] == "image_url"
        assert content[0]["image_url"]["url"] == "data:image/png;base64,abc123"
        assert content[1]["type"] == "text"
        assert content[1]["text"] == "What's in this image?"

    def test_format_multimodal_message_pydantic(self, llm: OpenRouterLLM):
        """测试多模态消息格式化（Pydantic 模型格式）"""
        multimodal_content = [
            ImageContent(image_url={"url": "data:image/jpeg;base64,xyz789"}),
            TextContent(text="Analyze this chart")
        ]
        messages = [
            LLMMessage(role="user", content=multimodal_content)
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"

        content = formatted[0]["content"]
        assert isinstance(content, list)
        assert len(content) == 2
        assert content[0]["type"] == "image_url"
        assert content[1]["type"] == "text"
        assert content[1]["text"] == "Analyze this chart"

    def test_format_content_string(self, llm: OpenRouterLLM):
        """测试 _format_content 处理字符串"""
        result = llm._format_content("Hello")
        assert result == "Hello"

    def test_format_content_empty(self, llm: OpenRouterLLM):
        """测试 _format_content 处理空值"""
        result = llm._format_content("")
        assert result == ""

        result = llm._format_content(None)
        assert result == ""

    def test_format_content_multimodal_list(self, llm: OpenRouterLLM):
        """测试 _format_content 处理多模态列表"""
        content = [
            {"type": "text", "text": "Look at this"},
            {"type": "image_url", "image_url": {"url": "data:image/gif;base64,..."}}
        ]

        result = llm._format_content(content)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["type"] == "text"
        assert result[1]["type"] == "image_url"

    def test_format_multiple_images(self, llm: OpenRouterLLM):
        """测试多张图片的格式化"""
        multimodal_content = [
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,img1"}},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,img2"}},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,img3"}},
            {"type": "text", "text": "Compare these three charts"}
        ]
        messages = [
            {"role": "user", "content": multimodal_content}
        ]

        formatted = llm._format_messages(messages)
        content = formatted[0]["content"]

        assert len(content) == 4
        assert all(c["type"] == "image_url" for c in content[:3])
        assert content[3]["type"] == "text"

    def test_filter_system_message(self, llm: OpenRouterLLM):
        """测试系统消息被正确过滤"""
        messages = [
            {"role": "system", "content": "Should be filtered"},
            {"role": "user", "content": "Hello"}
        ]

        # 不传 system 参数时，messages 中的 system 应被过滤
        formatted = llm._format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"

    def test_assistant_message_preserved(self, llm: OpenRouterLLM):
        """测试 assistant 消息被保留"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 3
        assert formatted[0]["role"] == "user"
        assert formatted[1]["role"] == "assistant"
        assert formatted[2]["role"] == "user"


class TestLLMMessageMultimodal:
    """LLMMessage 多模态支持测试"""

    def test_text_content_message(self):
        """测试纯文本 LLMMessage"""
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_multimodal_content_message(self):
        """测试多模态 LLMMessage"""
        content = [
            TextContent(text="What is this?"),
            ImageContent(image_url={"url": "data:image/png;base64,..."})
        ]
        msg = LLMMessage(role="user", content=content)

        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2

    def test_image_content_model(self):
        """测试 ImageContent 模型"""
        img = ImageContent(image_url={"url": "data:image/png;base64,abc"})
        assert img.type == "image_url"
        assert img.image_url["url"] == "data:image/png;base64,abc"

    def test_text_content_model(self):
        """测试 TextContent 模型"""
        text = TextContent(text="Hello world")
        assert text.type == "text"
        assert text.text == "Hello world"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
