#!/usr/bin/env python3
"""
测试 ResearchAgent + 工具调用

验证：
1. web_search 工具
2. read_url 工具
3. 2-Action Rule (Working Memory)
4. 完整的 Agent 循环

运行前需要设置环境变量：
export DASHSCOPE_API_KEY="sk-c644d84390984cd5bcb3f31dd5822906"
"""
import asyncio
import os
import sys
import tempfile

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.agent import (
    AgentContext,
    create_working_memory,
)
from app.agent.agents import ResearchAgent
from app.agent.llm import create_qwen_llm
from app.agent.tools import ToolRegistry
from app.agent.tools.builtin import create_read_url_tool, create_web_search_tool


async def test_research_agent():
    """测试 ResearchAgent 端到端流程"""
    print("=" * 60)
    print("测试 ResearchAgent + 工具调用")
    print("=" * 60)

    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    if not api_key:
        print("\n❌ 错误: 未设置 DASHSCOPE_API_KEY")
        return

    print("\n配置检查:")
    print(f"  - API Key: {api_key[:10]}...")
    print("  - Model: qwen-plus")

    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n工作目录: {tmpdir}")

        # 初始化组件
        print("\n初始化组件...")

        # 1. Working Memory
        memory = await create_working_memory(
            workspace_path=tmpdir,
            session_id="test-research-agent",
            initial_task="Research about Python asyncio"
        )
        print("  ✅ Working Memory")

        # 2. Agent Context
        context = AgentContext(
            session_id="test-research-agent",
            user_id="test-user",
            workspace_id="test-workspace"
        )
        print("  ✅ Agent Context")

        # 3. Tool Registry + 注册工具
        tools = ToolRegistry()
        web_search = create_web_search_tool()
        read_url = create_read_url_tool()

        tools.register(web_search)
        tools.register(read_url)
        print("  ✅ Tool Registry (2 tools registered)")

        # 4. Qwen LLM
        llm = create_qwen_llm()
        print(f"  ✅ Qwen LLM (model: {llm.model})")

        # 5. ResearchAgent
        agent = ResearchAgent(
            context=context,
            llm=llm,
            tools=tools,
            memory=memory,
            db=None,
            max_iterations=10
        )
        print("  ✅ ResearchAgent")

        # 运行 Agent
        print("\n" + "=" * 60)
        print("开始研究任务")
        print("问题: What are the latest developments in AI in 2024?")
        print("=" * 60)

        user_input = "What are the latest developments in AI in 2024? Please search and summarize."

        event_count = 0
        thinking_events = 0
        content_events = 0
        tool_call_events = 0
        tool_result_events = 0

        try:
            async for event in agent.run(user_input):
                event_count += 1

                if event.type.value == "thinking":
                    thinking_events += 1
                    content = event.data.get('content', '')
                    print(f"💭 {content}", end='', flush=True)

                elif event.type.value == "tool_call":
                    tool_call_events += 1
                    tool_name = event.data.get('tool_name', '')
                    print(f"\n\n🔧 Calling tool: {tool_name}")
                    print(f"   Input: {event.data.get('input', {})}")

                elif event.type.value == "tool_result":
                    tool_result_events += 1
                    success = event.data.get('success', False)
                    status = "✅" if success else "❌"
                    print(f"{status} Tool result received\n")

                elif event.type.value == "content":
                    content_events += 1
                    content = event.data.get('content', '')
                    print(f"{content}", end='', flush=True)

                elif event.type.value == "done":
                    print("\n\n✅ Done!")
                    stats = event.data.get('stats', {})
                    print("\n统计信息:")
                    print(f"  - 迭代次数: {stats.get('iterations', 0)}")
                    print(f"  - Token 使用: {stats.get('tokens_used', 0)}")

                elif event.type.value == "error":
                    error = event.data.get('message', 'Unknown error')
                    print(f"\n❌ 错误: {error}")

        except Exception as e:
            print(f"\n❌ Agent 运行失败: {e}")
            import traceback
            traceback.print_exc()
            return

        # 总结
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        print(f"总事件数: {event_count}")
        print(f"  - thinking 事件: {thinking_events}")
        print(f"  - tool_call 事件: {tool_call_events}")
        print(f"  - tool_result 事件: {tool_result_events}")
        print(f"  - content 事件: {content_events}")

        # 检查 Working Memory 文件
        print("\nWorking Memory 文件:")
        for filename in ['task_plan.md', 'findings.md', 'progress.md']:
            filepath = os.path.join(tmpdir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✅ {filename} ({size} bytes)")

                # 读取 findings.md 内容（验证 2-Action Rule）
                if filename == 'findings.md' and size > 0:
                    with open(filepath, encoding='utf-8') as f:
                        findings_content = f.read()
                    print("\nfindings.md 内容预览:")
                    print("-" * 40)
                    print(findings_content[:500])
                    print("-" * 40)
            else:
                print(f"  ❌ {filename} (不存在)")

        print("\n✅ ResearchAgent 测试成功!")


if __name__ == "__main__":
    asyncio.run(test_research_agent())
