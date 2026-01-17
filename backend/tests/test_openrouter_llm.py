"""
OpenRouter LLM 单元测试
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.llm import LLMMessage, OpenRouterLLM, create_openrouter_llm


class TestOpenRouterLLM:
    """OpenRouter LLM 测试套件"""

    @pytest.fixture
    def llm(self):
        """创建 OpenRouterLLM 实例"""
        return OpenRouterLLM(
            api_key="test_key",
            model="anthropic/claude-3-5-sonnet"
        )

    def test_initialization(self, llm):
        """测试初始化"""
        assert llm.api_key == "test_key"
        assert llm.model == "anthropic/claude-3-5-sonnet"
        assert llm.base_url == "https://openrouter.ai/api/v1"
        assert "Authorization" in llm.headers
        assert llm.headers["Authorization"] == "Bearer test_key"

    def test_custom_base_url(self):
        """测试自定义 Base URL"""
        llm = OpenRouterLLM(
            api_key="test_key",
            model="gpt-4",
            base_url="https://custom.openrouter.ai/api/v1"
        )
        assert llm.base_url == "https://custom.openrouter.ai/api/v1"

    def test_format_messages_with_system(self, llm):
        """测试消息格式化（带系统提示词）"""
        messages = [
            LLMMessage(role="user", content="Hello"),
            LLMMessage(role="assistant", content="Hi"),
            LLMMessage(role="user", content="How are you?")
        ]
        system = "You are a helpful assistant"

        formatted = llm._format_messages(messages, system)

        assert len(formatted) == 4
        assert formatted[0]["role"] == "system"
        assert formatted[0]["content"] == system
        assert formatted[1]["role"] == "user"
        assert formatted[1]["content"] == "Hello"

    def test_format_messages_without_system(self, llm):
        """测试消息格式化（不带系统提示词）"""
        messages = [
            {"role": "user", "content": "Test message"}
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0]["role"] == "user"
        assert formatted[0]["content"] == "Test message"

    def test_format_tools(self, llm):
        """测试工具格式转换"""
        claude_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }
        ]

        functions = llm._format_tools(claude_tools)

        assert len(functions) == 1
        assert functions[0]["name"] == "get_weather"
        assert functions[0]["description"] == "Get current weather"
        assert "parameters" in functions[0]

    @pytest.mark.asyncio
    async def test_complete_success(self, llm):
        """测试完整调用成功"""
        mock_response_data = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello from OpenRouter"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Create mock response object
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response_data
            mock_response_obj.raise_for_status = MagicMock()

            # Set up async context manager
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value = mock_context

            messages = [LLMMessage(role="user", content="Hello")]
            response = await llm.complete(messages)

            assert response.content == "Hello from OpenRouter"
            assert response.stop_reason == "stop"
            assert response.usage["input_tokens"] == 10
            assert response.usage["output_tokens"] == 5

    @pytest.mark.asyncio
    async def test_complete_with_function_call(self, llm):
        """测试带 function calling 的完整调用"""
        mock_response_data = {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "",
                    "function_call": {
                        "name": "get_weather",
                        "arguments": '{"location": "Beijing"}'
                    }
                },
                "finish_reason": "function_call"
            }],
            "usage": {
                "prompt_tokens": 20,
                "completion_tokens": 15
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            # Create mock response object
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response_data
            mock_response_obj.raise_for_status = MagicMock()

            # Set up async context manager
            mock_context = AsyncMock()
            mock_context.post = AsyncMock(return_value=mock_response_obj)
            mock_client.return_value.__aenter__.return_value = mock_context

            messages = [LLMMessage(role="user", content="What's the weather?")]
            tools = [{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "parameters": {}
                }
            }]

            response = await llm.complete(messages, tools=tools)

            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["name"] == "get_weather"
            assert response.tool_calls[0]["input"]["location"] == "Beijing"

    @pytest.mark.asyncio
    async def test_stream_success(self, llm):
        """测试流式调用成功"""
        mock_stream_data = [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            'data: {"choices":[{"delta":{"content":" from"}}]}',
            'data: {"choices":[{"delta":{"content":" OpenRouter"}}]}',
            'data: [DONE]'
        ]

        async def mock_aiter_lines():
            for line in mock_stream_data:
                yield line

        with patch("httpx.AsyncClient") as mock_client:
            # Create mock stream response
            mock_stream_response = MagicMock()
            mock_stream_response.aiter_lines = mock_aiter_lines
            mock_stream_response.raise_for_status = MagicMock()

            # Set up nested async context managers
            mock_stream_context = AsyncMock()
            mock_stream_context.__aenter__.return_value = mock_stream_response
            mock_stream_context.__aexit__.return_value = AsyncMock()

            mock_context = AsyncMock()
            mock_context.stream = MagicMock(return_value=mock_stream_context)
            mock_client.return_value.__aenter__.return_value = mock_context

            messages = [LLMMessage(role="user", content="Hello")]
            chunks = []

            async for chunk in llm.stream(messages):
                chunks.append(chunk)

            assert len(chunks) == 3
            assert "".join(chunks) == "Hello from OpenRouter"


class TestCreateOpenRouterLLM:
    """测试 create_openrouter_llm 工厂函数"""

    def test_create_with_env_vars(self):
        """测试从环境变量创建"""
        with patch.dict("os.environ", {
            "OPENROUTER_API_KEY": "env_key",
            "OPENROUTER_MODEL": "gpt-4"
        }):
            llm = create_openrouter_llm()
            assert llm.api_key == "env_key"
            assert llm.model == "gpt-4"

    def test_create_with_params(self):
        """测试直接传参创建"""
        llm = create_openrouter_llm(
            api_key="param_key",
            model="anthropic/claude-3-opus",
            max_tokens=8192
        )
        assert llm.api_key == "param_key"
        assert llm.model == "anthropic/claude-3-opus"
        assert llm.max_tokens == 8192

    def test_create_without_api_key(self):
        """测试缺少 API Key 时抛出异常"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API Key not found"):
                create_openrouter_llm()

    def test_create_with_custom_site_url(self):
        """测试自定义站点 URL"""
        with patch.dict("os.environ", {
            "OPENROUTER_API_KEY": "test_key",
            "OPENROUTER_SITE_URL": "https://custom.site"
        }):
            llm = create_openrouter_llm()
            assert llm.site_url == "https://custom.site"
