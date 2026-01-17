"""
OpenRouter LLM 使用示例

演示如何使用 OpenRouter 调用不同的 LLM 模型
"""
import asyncio
import os

from app.agent.llm import LLMMessage, create_openrouter_llm


async def example_basic_chat():
    """基础对话示例"""
    print("=== 基础对话示例 ===")

    # 使用环境变量中的 API Key
    llm = create_openrouter_llm()

    messages = [
        LLMMessage(role="user", content="你好！请用一句话介绍你自己。")
    ]

    response = await llm.complete(messages)
    print(f"模型: {llm.model}")
    print(f"回复: {response.content}")
    print(f"使用 Token: {response.usage}")
    print()


async def example_stream_chat():
    """流式对话示例"""
    print("=== 流式对话示例 ===")

    llm = create_openrouter_llm()

    messages = [
        LLMMessage(role="user", content="写一首关于春天的五言绝句。")
    ]

    print(f"模型: {llm.model}")
    print("回复: ", end="", flush=True)

    async for chunk in llm.stream(messages):
        print(chunk, end="", flush=True)

    print("\n")


async def example_model_routing():
    """智能路由示例 - 根据任务选择不同模型"""
    print("=== 智能路由示例 ===")

    tasks = [
        ("deep_research", "anthropic/claude-3-opus", "解释量子纠缠的本质"),
        ("fast_qa", "anthropic/claude-3-haiku", "1+1等于几？"),
        ("code_generation", "deepseek/deepseek-coder", "写一个Python快速排序函数"),
    ]

    for task_type, model, prompt in tasks:
        llm = create_openrouter_llm(model=model)
        messages = [LLMMessage(role="user", content=prompt)]

        response = await llm.complete(messages, max_tokens=200)

        print(f"任务类型: {task_type}")
        print(f"模型: {model}")
        print(f"回复: {response.content[:100]}...")
        print(f"Token 使用: {response.usage}")
        print()


async def example_with_tools():
    """Tool Calling 示例"""
    print("=== Tool Calling 示例 ===")

    llm = create_openrouter_llm()

    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如：北京、上海"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位"
                    }
                },
                "required": ["location"]
            }
        }
    }]

    messages = [
        LLMMessage(role="user", content="北京今天的天气怎么样？")
    ]

    response = await llm.complete(messages, tools=tools)

    print(f"模型: {llm.model}")
    if response.tool_calls:
        print("模型请求调用工具:")
        for tool_call in response.tool_calls:
            print(f"  - 工具: {tool_call['name']}")
            print(f"  - 参数: {tool_call['input']}")
    else:
        print(f"直接回复: {response.content}")
    print()


async def example_temperature_control():
    """温度参数控制示例"""
    print("=== 温度参数控制示例 ===")

    prompt = "续写故事：在一个月黑风高的晚上，"

    # 低温度 - 确定性输出
    print("低温度 (0.2) - 确定性:")
    llm_precise = create_openrouter_llm(temperature=0.2)
    response = await llm_precise.complete(
        [LLMMessage(role="user", content=prompt)],
        max_tokens=50
    )
    print(response.content)
    print()

    # 高温度 - 创意输出
    print("高温度 (1.0) - 创意:")
    llm_creative = create_openrouter_llm(temperature=1.0)
    response = await llm_creative.complete(
        [LLMMessage(role="user", content=prompt)],
        max_tokens=50
    )
    print(response.content)
    print()


async def main():
    """主函数 - 运行所有示例"""
    # 检查环境变量
    if not os.getenv("OPENROUTER_API_KEY"):
        print("错误: 未设置 OPENROUTER_API_KEY 环境变量")
        print("请先设置: export OPENROUTER_API_KEY=sk-or-v1-xxxxx")
        return

    try:
        # 运行各个示例
        await example_basic_chat()
        await example_stream_chat()
        await example_model_routing()
        await example_with_tools()
        await example_temperature_control()

        print("✅ 所有示例运行完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
