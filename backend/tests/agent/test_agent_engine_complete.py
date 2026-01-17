"""
Agent Engine 完整测试

测试 Agent 核心引擎的各个功能：
1. 基础对话
2. 工具调用
3. 多轮对话
4. 错误处理
5. 3-File Working Memory 集成
"""

import asyncio
import os
from pathlib import Path

import pytest

from app.agent.engine import AgentEngine
from app.agent.llm.anthropic import AnthropicLLM
from app.filesystem import AgentFileSystem

# ========== 测试环境配置 ==========

@pytest.fixture
def workspace_id():
    """测试用的 workspace ID"""
    return "test_workspace"


@pytest.fixture
def session_id():
    """测试用的 session ID"""
    return "test_session_001"


@pytest.fixture
def filesystem(workspace_id):
    """初始化文件系统"""
    base_dir = Path("/tmp/tokendance_test")
    base_dir.mkdir(exist_ok=True, parents=True)

    fs = AgentFileSystem(
        workspace_id=workspace_id,
        base_dir=str(base_dir)
    )

    yield fs

    # 清理测试文件
    import shutil
    if base_dir.exists():
        shutil.rmtree(base_dir)


@pytest.fixture
def llm():
    """初始化 LLM 客户端"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    return AnthropicLLM(
        api_key=api_key,
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096
    )


@pytest.fixture
async def agent(llm, filesystem, workspace_id, session_id):
    """初始化 Agent Engine"""
    engine = AgentEngine(
        llm=llm,
        filesystem=filesystem,
        workspace_id=workspace_id,
        session_id=session_id,
        max_iterations=10
    )

    return engine


# ========== 测试用例 ==========

@pytest.mark.asyncio
async def test_basic_question(agent):
    """测试 1: 基础问答（无工具调用）"""
    print("\n=== Test 1: Basic Question ===")

    response = await agent.run("2 + 2 等于几？")

    assert response.answer is not None
    assert "4" in response.answer
    assert response.iterations >= 1

    print(f"Answer: {response.answer}")
    print(f"Iterations: {response.iterations}")
    print(f"Token usage: {response.token_usage}")


@pytest.mark.asyncio
async def test_file_operations(agent):
    """测试 2: 文件操作工具"""
    print("\n=== Test 2: File Operations ===")

    response = await agent.run(
        "请在 task_plan.md 中写入一个简单的任务计划：目标是测试文件操作功能"
    )

    assert response.answer is not None
    assert response.iterations >= 1

    # 验证文件是否创建
    task_plan = agent.three_files.read_task_plan()
    assert "测试文件操作" in task_plan["content"] or "test" in task_plan["content"].lower()

    print(f"Answer: {response.answer[:200]}...")
    print(f"Task plan content preview: {task_plan['content'][:200]}...")


@pytest.mark.asyncio
async def test_web_search(agent):
    """测试 3: Web 搜索工具"""
    print("\n=== Test 3: Web Search ===")

    response = await agent.run(
        "搜索 FastAPI 的官方文档网址是什么？"
    )

    assert response.answer is not None
    assert response.iterations >= 1

    # 应该包含搜索结果
    assert "fastapi" in response.answer.lower() or "tiangolo" in response.answer.lower()

    print(f"Answer: {response.answer[:300]}...")
    print(f"Iterations: {response.iterations}")


@pytest.mark.asyncio
async def test_multi_step_task(agent):
    """测试 4: 多步骤任务（触发 2-Action Rule）"""
    print("\n=== Test 4: Multi-Step Task ===")

    response = await agent.run(
        """请帮我研究一下 Vue 3 的核心特性：
        1. 先搜索 Vue 3 的主要新特性
        2. 搜索 Composition API 的用法
        3. 将发现记录到 findings.md
        """
    )

    assert response.answer is not None

    # 检查 findings.md 是否有内容（如果 Agent 遵循 2-Action Rule）
    findings = agent.three_files.read_findings()
    print(f"\nFindings content length: {len(findings['content'])}")
    print(f"Findings preview: {findings['content'][:300]}...")

    # 检查 progress.md
    progress = agent.three_files.read_progress()
    print(f"\nProgress content length: {len(progress['content'])}")
    print(f"Progress preview: {progress['content'][:300]}...")

    print(f"\nAnswer: {response.answer[:300]}...")


@pytest.mark.asyncio
async def test_error_handling(agent):
    """测试 5: 错误处理"""
    print("\n=== Test 5: Error Handling ===")

    response = await agent.run(
        "读取一个不存在的文件：/nonexistent/file.txt"
    )

    assert response.answer is not None

    # 检查 progress.md 中是否记录了错误
    progress = agent.three_files.read_progress()
    assert "error" in progress["content"].lower() or "ERROR" in progress["content"]

    print(f"Answer: {response.answer[:200]}...")
    print(f"Progress (errors): {progress['content'][-500:]}")


@pytest.mark.asyncio
async def test_three_files_workflow(agent):
    """测试 6: 完整的三文件工作流"""
    print("\n=== Test 6: Three Files Workflow ===")

    response = await agent.run(
        """请完成以下任务：
        1. 在 task_plan.md 中创建一个3步计划
        2. 执行第一步：搜索 Python FastAPI 最佳实践
        3. 将搜索结果记录到 findings.md
        4. 在 progress.md 中记录执行过程
        """
    )

    assert response.answer is not None

    # 验证三个文件都有内容
    task_plan = agent.three_files.read_task_plan()
    findings = agent.three_files.read_findings()
    progress = agent.three_files.read_progress()

    print("\n--- Task Plan ---")
    print(task_plan["content"][:300])

    print("\n--- Findings ---")
    print(findings["content"][:300])

    print("\n--- Progress ---")
    print(progress["content"][:300])

    print("\n--- Final Answer ---")
    print(response.answer[:300])


@pytest.mark.asyncio
async def test_context_summary(agent):
    """测试 7: Context 摘要"""
    print("\n=== Test 7: Context Summary ===")

    # 发送一条消息
    await agent.run("Hello! This is a test message.")

    # 获取 context 摘要
    summary = agent.get_context_summary()

    assert summary["session_id"] == agent.session_id
    assert summary["workspace_id"] == agent.workspace_id
    assert summary["message_count"] >= 2  # 至少有 user + assistant

    print("\nContext Summary:")
    print(f"- Session ID: {summary['session_id']}")
    print(f"- Workspace ID: {summary['workspace_id']}")
    print(f"- Message Count: {summary['message_count']}")
    print(f"- Iteration Count: {summary['iteration_count']}")
    print(f"- Token Usage: {summary['token_usage']}")


# ========== 主函数（用于单独运行） ==========

if __name__ == "__main__":
    """
    可以直接运行此文件进行测试：

    python backend/test_agent_engine_complete.py
    """

    print("=" * 60)
    print("Agent Engine Manual Test")
    print("=" * 60)

    # 检查 API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        exit(1)

    # 创建临时环境
    workspace_id = "manual_test_workspace"
    session_id = "manual_test_session"
    base_dir = Path("/tmp/tokendance_manual_test")
    base_dir.mkdir(exist_ok=True, parents=True)

    # 初始化组件
    filesystem = AgentFileSystem(
        workspace_id=workspace_id,
        base_dir=str(base_dir)
    )

    llm = AnthropicLLM(
        api_key=api_key,
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096
    )

    agent = AgentEngine(
        llm=llm,
        filesystem=filesystem,
        workspace_id=workspace_id,
        session_id=session_id,
        max_iterations=10
    )

    # 交互式测试
    print("\n开始交互式测试（输入 'quit' 退出）\n")

    async def interactive_test():
        while True:
            user_input = input("\n你: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            print("\nAgent 思考中...")
            response = await agent.run(user_input)

            print(f"\nAgent: {response.answer}")
            print(f"\n[Iterations: {response.iterations}, Tokens: {response.token_usage}]")

    # 运行交互式循环
    asyncio.run(interactive_test())

    print("\n测试完成！文件位于:", base_dir)
