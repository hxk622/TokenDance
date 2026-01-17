"""
OpenRouter 连接测试
简单验证 API Key 是否有效以及能否正常调用
"""
import asyncio
import os

from dotenv import load_dotenv

from app.agent.llm import LLMMessage, create_openrouter_llm

# 加载环境变量
load_dotenv()


async def test_basic_connection():
    """测试基础连接"""
    print("🔍 测试 OpenRouter 连接...")
    print("=" * 50)

    try:
        # 创建客户端
        llm = create_openrouter_llm()
        print("✅ 客户端创建成功")
        print(f"   模型: {llm.model}")
        print(f"   Base URL: {llm.base_url}")
        print()

        # 发送简单测试消息
        print("📤 发送测试消息...")
        messages = [
            LLMMessage(role="user", content="请用一句话回复：你能正常工作吗？")
        ]

        response = await llm.complete(messages, max_tokens=50)

        print("✅ 收到响应！")
        print(f"   内容: {response.content}")
        print(f"   停止原因: {response.stop_reason}")
        if response.usage:
            print(f"   Token 使用: 输入={response.usage['input_tokens']}, 输出={response.usage['output_tokens']}")
        print()

        print("=" * 50)
        print("🎉 OpenRouter 集成测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print()
        print("可能的原因：")
        print("1. API Key 无效或已过期")
        print("2. 网络连接问题")
        print("3. OpenRouter 服务暂时不可用")
        print()
        print("解决方案：")
        print("- 检查 backend/.env 中的 OPENROUTER_API_KEY")
        print("- 访问 https://openrouter.ai/keys 验证 Key 状态")
        print("- 检查网络连接")
        return False


if __name__ == "__main__":
    # 检查环境变量
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ 错误: 未找到 OPENROUTER_API_KEY 环境变量")
        print("请确保 backend/.env 文件存在并包含正确的配置")
        exit(1)

    # 运行测试
    success = asyncio.run(test_basic_connection())
    exit(0 if success else 1)
