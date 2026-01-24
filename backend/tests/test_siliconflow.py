"""
SiliconFlow LLM 测试
"""
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.llm.siliconflow import (
    SILICONFLOW_FREE_MODELS,
    SILICONFLOW_PAID_MODELS,
    SiliconFlowLLM,
    create_siliconflow_llm,
    get_siliconflow_best_model,
    get_siliconflow_free_model,
    is_siliconflow_free_model,
)


class TestSiliconFlowHelpers:
    """测试辅助函数"""

    def test_get_siliconflow_free_model(self):
        """测试获取免费模型名称"""
        model = get_siliconflow_free_model()
        assert model == "Qwen/Qwen2.5-7B-Instruct"
        assert model in SILICONFLOW_FREE_MODELS

    def test_get_siliconflow_best_model(self):
        """测试获取最佳付费模型名称"""
        model = get_siliconflow_best_model()
        assert model == "Qwen/Qwen2.5-72B-Instruct"
        assert model in SILICONFLOW_PAID_MODELS

    def test_is_siliconflow_free_model(self):
        """测试检查是否为免费模型"""
        # 免费模型
        assert is_siliconflow_free_model("Qwen/Qwen2.5-7B-Instruct") is True
        assert is_siliconflow_free_model("THUDM/glm-4-9b-chat") is True

        # 付费模型
        assert is_siliconflow_free_model("Qwen/Qwen2.5-72B-Instruct") is False
        assert is_siliconflow_free_model("deepseek-ai/DeepSeek-V2.5") is False

        # 未知模型
        assert is_siliconflow_free_model("unknown/model") is False

    def test_free_models_list(self):
        """测试免费模型列表"""
        assert len(SILICONFLOW_FREE_MODELS) >= 5
        assert "Qwen/Qwen2.5-7B-Instruct" in SILICONFLOW_FREE_MODELS
        assert "meta-llama/Meta-Llama-3.1-8B-Instruct" in SILICONFLOW_FREE_MODELS

    def test_paid_models_list(self):
        """测试付费模型列表"""
        assert len(SILICONFLOW_PAID_MODELS) >= 4
        assert "Qwen/Qwen2.5-72B-Instruct" in SILICONFLOW_PAID_MODELS
        assert "deepseek-ai/DeepSeek-R1" in SILICONFLOW_PAID_MODELS


class TestSiliconFlowLLMInit:
    """测试 SiliconFlowLLM 初始化"""

    def test_init_default_values(self):
        """测试默认值初始化"""
        llm = SiliconFlowLLM(api_key="test-key")

        assert llm.api_key == "test-key"
        assert llm.model == "Qwen/Qwen2.5-72B-Instruct"
        assert llm.max_tokens == 4096
        assert llm.temperature == 0.7
        assert llm.base_url == "https://api.siliconflow.cn/v1"

    def test_init_custom_values(self):
        """测试自定义值初始化"""
        llm = SiliconFlowLLM(
            api_key="custom-key",
            model="deepseek-ai/DeepSeek-V2.5",
            max_tokens=8192,
            temperature=0.5,
            base_url="https://custom.url/v1/"
        )

        assert llm.api_key == "custom-key"
        assert llm.model == "deepseek-ai/DeepSeek-V2.5"
        assert llm.max_tokens == 8192
        assert llm.temperature == 0.5
        # base_url should be stripped of trailing slash
        assert llm.base_url == "https://custom.url/v1"


class TestCreateSiliconflowLLM:
    """测试 create_siliconflow_llm 函数"""

    def test_create_with_explicit_params(self):
        """测试使用显式参数创建"""
        llm = create_siliconflow_llm(
            api_key="explicit-key",
            model="Qwen/Qwen2.5-7B-Instruct"
        )

        assert llm.api_key == "explicit-key"
        assert llm.model == "Qwen/Qwen2.5-7B-Instruct"

    @patch.dict(os.environ, {
        "SILICONFLOW_API_KEY": "env-key",
        "SILICONFLOW_MODEL": "env-model",
        "SILICONFLOW_BASE_URL": "https://env.url/v1"
    })
    def test_create_from_env_vars(self):
        """测试从环境变量创建"""
        llm = create_siliconflow_llm()

        assert llm.api_key == "env-key"
        assert llm.model == "env-model"
        assert llm.base_url == "https://env.url/v1"

    @patch.dict(os.environ, {"SILICONFLOW_API_KEY": "env-key"}, clear=True)
    def test_create_prefer_free_model(self):
        """测试优先使用免费模型"""
        # 清除可能的环境变量
        os.environ.pop("SILICONFLOW_MODEL", None)

        llm = create_siliconflow_llm(prefer_free=True)

        assert llm.model == "Qwen/Qwen2.5-7B-Instruct"

    @patch.dict(os.environ, {"SILICONFLOW_API_KEY": "env-key"}, clear=True)
    def test_create_default_paid_model(self):
        """测试默认使用付费模型"""
        os.environ.pop("SILICONFLOW_MODEL", None)

        llm = create_siliconflow_llm(prefer_free=False)

        assert llm.model == "Qwen/Qwen2.5-72B-Instruct"

    @patch.dict(os.environ, {}, clear=True)
    def test_create_without_api_key(self):
        """测试没有 API Key 时报错"""
        os.environ.pop("SILICONFLOW_API_KEY", None)

        with pytest.raises(ValueError, match="API Key not found"):
            create_siliconflow_llm()


class TestSiliconFlowLLMComplete:
    """测试 SiliconFlowLLM.complete 方法 (使用 httpx mock)"""

    @pytest.mark.asyncio
    async def test_complete_basic(self):
        """测试基本完成调用"""
        # Mock httpx response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Hello, world!", "tool_calls": None},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            llm = SiliconFlowLLM(api_key="test-key")
            response = await llm.complete(
                messages=[{"role": "user", "content": "Hi"}]
            )

            assert response.content == "Hello, world!"
            assert response.stop_reason == "stop"
            assert response.usage["input_tokens"] == 10
            assert response.usage["output_tokens"] == 5

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self):
        """测试带工具调用的响应"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "",
                    "tool_calls": [{
                        "id": "call_123",
                        "function": {
                            "name": "get_weather",
                            "arguments": '{"location": "Beijing"}'
                        }
                    }]
                },
                "finish_reason": "tool_calls"
            }],
            "usage": None
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            llm = SiliconFlowLLM(api_key="test-key")
            response = await llm.complete(
                messages=[{"role": "user", "content": "What's the weather?"}],
                tools=[{
                    "name": "get_weather",
                    "description": "Get weather information",
                    "input_schema": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}}
                    }
                }]
            )

            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["id"] == "call_123"
            assert response.tool_calls[0]["name"] == "get_weather"
            assert response.tool_calls[0]["input"] == {"location": "Beijing"}


class TestSiliconFlowLLMFormatMessages:
    """测试消息格式化"""

    def test_format_dict_messages(self):
        """测试格式化字典消息"""
        llm = SiliconFlowLLM(api_key="test-key")

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        formatted = llm._format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0] == {"role": "user", "content": "Hello"}
        assert formatted[1] == {"role": "assistant", "content": "Hi there"}

    def test_format_with_system(self):
        """测试添加 system 消息"""
        llm = SiliconFlowLLM(api_key="test-key")

        messages = [{"role": "user", "content": "Hello"}]

        formatted = llm._format_messages(messages, system="Be helpful")

        assert len(formatted) == 2
        assert formatted[0] == {"role": "system", "content": "Be helpful"}
        assert formatted[1] == {"role": "user", "content": "Hello"}


class TestSiliconFlowLLMConvertTools:
    """测试工具转换"""

    def test_convert_tools(self):
        """测试工具格式转换"""
        llm = SiliconFlowLLM(api_key="test-key")

        tools = [
            {
                "name": "search",
                "description": "Search the web",
                "input_schema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]
                }
            }
        ]

        openai_tools = llm._convert_tools(tools)

        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"
        assert openai_tools[0]["function"]["name"] == "search"
        assert openai_tools[0]["function"]["description"] == "Search the web"
        assert openai_tools[0]["function"]["parameters"]["type"] == "object"
