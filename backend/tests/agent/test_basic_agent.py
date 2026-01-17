"""
BasicAgent 集成测试

测试 Agent 基类和 BasicAgent 的完整流程
"""
import asyncio
import tempfile


# Mock imports (since we don't have DB/LLM setup)
class MockLLM:
    """Mock LLM for testing"""
    async def stream(self, messages, **kwargs):
        yield "Mock "
        yield "response"


class MockDB:
    """Mock database session"""
    pass


async def test_basic_agent():
    """测试 BasicAgent 完整流程"""
    print("=" * 60)
    print("BasicAgent 集成测试")
    print("=" * 60)

    from app.agent import AgentContext, BasicAgent, create_working_memory
    from app.agent.tools import ToolRegistry

    # 创建临时工作目录
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace_path = tmpdir
        session_id = "test_session_basic_agent"

        print("\n1. 初始化组件")
        print(f"   Workspace: {workspace_path}")

        # 创建 WorkingMemory
        memory = await create_working_memory(
            workspace_path=workspace_path,
            session_id=session_id,
            initial_task="Test BasicAgent functionality"
        )
        print("   ✅ WorkingMemory 创建")

        # 创建 AgentContext
        context = AgentContext(
            session_id=session_id,
            user_id="test_user",
            workspace_id="test_workspace"
        )
        print("   ✅ AgentContext 创建")

        # 创建 ToolRegistry (空)
        tools = ToolRegistry()
        print("   ✅ ToolRegistry 创建")

        # 创建 MockLLM
        llm = MockLLM()
        print("   ✅ MockLLM 创建")

        # 创建 BasicAgent
        agent = BasicAgent(
            context=context,
            llm=llm,
            tools=tools,
            memory=memory,
            db=MockDB(),
            max_iterations=5
        )
        print(f"   ✅ BasicAgent 创建: {agent}")

        # 运行 Agent
        print("\n2. 运行 Agent")
        user_input = "Hello, BasicAgent! How are you?"
        print(f"   User Input: {user_input}")

        event_count = 0
        event_types = []

        try:
            async for event in agent.run(user_input):
                event_count += 1
                event_types.append(event.type.value)

                print(f"\n   [{event_count}] Event: {event.type.value}")

                if event.type.value == 'thinking':
                    content = event.data.get('content', '')
                    print(f"       Thinking: {content.strip()}")

                elif event.type.value == 'content':
                    content = event.data.get('content', '')
                    print(f"       Content: {content}")

                elif event.type.value == 'done':
                    print(f"       Status: {event.data.get('status')}")
                    print(f"       Iterations: {event.data.get('iterations')}")
                    print(f"       Tokens: {event.data.get('tokens_used')}")

                elif event.type.value == 'error':
                    print(f"       Error: {event.data}")

            print("\n3. Agent 执行完成")
            print(f"   总事件数: {event_count}")
            print(f"   事件类型: {', '.join(set(event_types))}")

        except Exception as e:
            print(f"\n❌ Agent 执行失败: {e}")
            import traceback
            traceback.print_exc()
            return False

        # 检查 Working Memory 文件
        print("\n4. 检查 Working Memory 文件")

        stats = memory.get_statistics()
        print("   统计信息:")
        print(f"     - Iterations: {stats['action_counter']}")
        print(f"     - Errors: {stats['error_tracker']}")

        # 读取 progress.md
        progress = await memory.read_progress()
        print("\n   progress.md (最后 300 字符):")
        print(f"   {progress[-300:]}")

        print("\n" + "=" * 60)
        print("✅ 测试通过！")
        print("=" * 60)

        return True


if __name__ == "__main__":
    success = asyncio.run(test_basic_agent())
    exit(0 if success else 1)
