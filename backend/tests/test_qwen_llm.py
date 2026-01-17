#!/usr/bin/env python3
"""
测试 Qwen LLM 集成

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
    BasicAgent,
    create_working_memory,
)
from app.agent.llm import create_qwen_llm
from app.agent.tools import ToolRegistry


async def test_qwen_llm():
    """测试 Qwen LLM 集成"""
    print("=" * 60)
    print("测试 Qwen LLM 集成")
    print("=" * 60)

    # 检查环境变量
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    model = os.getenv("QWEN_MODEL", "qwen-plus")

    print("\n配置检查:")
    print(f"  - API Key: {api_key[:10]}..." if api_key else "  - API Key: 未设置")
    print(f"  - Model: {model}")

    if not api_key:
        print("\n❌ 错误: 未设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY")
        return

    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"\n工作目录: {tmpdir}")

        # 初始化组件
        print("\n初始化组件...")

        # 1. Working Memory
        memory = await create_working_memory(
            workspace_path=tmpdir,
            session_id="test-session-qwen",
            initial_task="Test Qwen LLM integration"
        )
        print("  ✅ Working Memory")

        # 2. Agent Context
        context = AgentContext(
            session_id="test-session-qwen",
            user_id="test-user",
            workspace_id="test-workspace"
        )
        print("  ✅ Agent Context")

        # 3. Tool Registry
        tools = ToolRegistry()
        print("  ✅ Tool Registry")

        # 4. Qwen LLM
        try:
            llm = create_qwen_llm()
            print(f"  ✅ Qwen LLM (model: {llm.model})")
        except Exception as e:
            print(f"  ❌ Qwen LLM 创建失败: {e}")
            return

        # 5. BasicAgent
        agent = BasicAgent(
            context=context,
            llm=llm,
            tools=tools,
            memory=memory,
            db=None,
            max_iterations=5
        )
        print("  ✅ BasicAgent")

        # 运行 Agent
        print("\n" + "=" * 60)
        print("开始对话 (测试问题: 介绍一下中国的四大发明)")
        print("=" * 60)

        user_input = "请简单介绍一下中国的四大发明，每个用一句话概括。"

        event_count = 0
        thinking_events = 0
        content_events = 0

        try:
            async for event in agent.run(user_input):
                event_count += 1

                if event.type.value == "thinking":
                    thinking_events += 1
                    content = event.data.get('content', '')
                    print(f"💭 {content}", end='', flush=True)

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
                    print(f"  - 耗时: {stats.get('elapsed_time', 0):.2f}s")

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
        print(f"  - content 事件: {content_events}")

        # 检查 Working Memory 文件
        print("\nWorking Memory 文件:")
        for filename in ['task_plan.md', 'findings.md', 'progress.md']:
            filepath = os.path.join(tmpdir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  ✅ {filename} ({size} bytes)")
            else:
                print(f"  ❌ {filename} (不存在)")

        print("\n✅ Qwen LLM 集成测试成功!")


if __name__ == "__main__":
    asyncio.run(test_qwen_llm())
