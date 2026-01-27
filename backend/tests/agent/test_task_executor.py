"""
TaskExecutor 单元测试

测试原子任务执行器的核心功能：
1. 基本执行流程
2. 工具调用处理
3. 失败检测和重试
4. 超时处理
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.execution_context import ExecutionContext
from app.agent.executor import ToolCallExecutor, ToolResult
from app.agent.failure import FailureObserver
from app.agent.llm.base import BaseLLM, LLMResponse
from app.agent.planning.task import Task
from app.agent.task_executor import (
    TaskExecutor,
    TaskExecutorConfig,
    build_task_prompt,
)
from app.agent.task_executor import (
    TaskResult as TaskExecutionResult,
)
from app.agent.types import SSEEventType

# ========== Fixtures ==========


@pytest.fixture
def mock_llm():
    """创建 Mock LLM"""
    llm = MagicMock(spec=BaseLLM)
    llm.complete = AsyncMock()
    
    # Mock stream method to return async iterator
    async def mock_stream(*args, **kwargs):
        # Return chunks of response
        chunks = ["<task_done>", "Task completed successfully!", "</task_done>"]
        for chunk in chunks:
            yield chunk
    
    llm.stream = mock_stream
    return llm


@pytest.fixture
def mock_tool_executor():
    """创建 Mock 工具执行器"""
    executor = MagicMock(spec=ToolCallExecutor)
    executor.has_tool_calls = MagicMock(return_value=False)
    executor.has_final_answer = MagicMock(return_value=False)
    executor.parse_tool_calls = MagicMock(return_value=[])
    executor.execute_all = AsyncMock(return_value=[])
    executor.format_tool_results = MagicMock(return_value="")
    return executor


@pytest.fixture
def failure_observer():
    """创建 FailureObserver"""
    return FailureObserver()


@pytest.fixture
def task_executor(mock_llm, mock_tool_executor, failure_observer):
    """创建 TaskExecutor 实例"""
    config = TaskExecutorConfig(
        max_iterations=5,
        timeout_seconds=10.0,
    )
    return TaskExecutor(
        llm=mock_llm,
        tool_executor=mock_tool_executor,
        failure_observer=failure_observer,
        config=config,
    )


@pytest.fixture
def sample_task():
    """创建示例 Task"""
    return Task(
        id="test_task_1",
        title="Test Task",
        description="This is a test task",
        acceptance_criteria="Task should be completed successfully",
        tools_hint=["web_search"],
    )


@pytest.fixture
def execution_context():
    """创建执行上下文"""
    return ExecutionContext(
        session_id="test_session",
        workspace_id="test_workspace",
    )


# ========== ExecutionContext 测试 ==========


class TestExecutionContext:
    """ExecutionContext 单元测试"""

    def test_create_context(self):
        """测试创建上下文"""
        ctx = ExecutionContext(
            session_id="session_1",
            workspace_id="workspace_1",
        )
        assert ctx.session_id == "session_1"
        assert ctx.workspace_id == "workspace_1"
        assert len(ctx.messages) == 0
        assert ctx.token_usage.total == 0

    def test_add_messages(self, execution_context):
        """测试添加消息"""
        execution_context.add_user_message("Hello")
        execution_context.add_assistant_message("Hi there!")
        execution_context.add_tool_result("web_search", "Search results...")

        assert len(execution_context.messages) == 3
        assert execution_context.messages[0].role == "user"
        assert execution_context.messages[1].role == "assistant"
        assert execution_context.messages[2].role == "tool_result"

    def test_variables(self, execution_context):
        """测试变量操作"""
        execution_context.set_variable("key1", "value1")
        execution_context.set_variable("key2", 123)

        assert execution_context.get_variable("key1") == "value1"
        assert execution_context.get_variable("key2") == 123
        assert execution_context.get_variable("key3") is None
        assert execution_context.get_variable("key3", "default") == "default"
        assert execution_context.has_variable("key1")
        assert not execution_context.has_variable("key3")

    def test_token_usage(self, execution_context):
        """测试 Token 统计"""
        execution_context.add_token_usage(input_tokens=100, output_tokens=50)
        execution_context.add_token_usage(input_tokens=50, output_tokens=25)

        usage = execution_context.get_token_usage()
        assert usage["input_tokens"] == 150
        assert usage["output_tokens"] == 75
        assert usage["total"] == 225

    def test_serialization(self, execution_context):
        """测试序列化和反序列化"""
        execution_context.add_user_message("Hello")
        execution_context.set_variable("key", "value")
        execution_context.add_token_usage(100, 50)

        # 序列化
        data = execution_context.to_dict()
        assert data["session_id"] == "test_session"
        assert len(data["messages"]) == 1

        # 反序列化
        restored = ExecutionContext.from_dict(data)
        assert restored.session_id == execution_context.session_id
        assert len(restored.messages) == 1
        assert restored.get_variable("key") == "value"

    def test_clone(self, execution_context):
        """测试克隆"""
        execution_context.add_user_message("Hello")
        execution_context.set_variable("key", "value")

        cloned = execution_context.clone()

        assert cloned.session_id == execution_context.session_id
        assert len(cloned.messages) == 1
        assert cloned.get_variable("key") == "value"

        # 修改原始不影响克隆
        execution_context.add_user_message("World")
        assert len(cloned.messages) == 1


# ========== TaskExecutor 测试 ==========


class TestTaskExecutor:
    """TaskExecutor 单元测试"""

    @pytest.mark.asyncio
    async def test_execute_simple_task(
        self, task_executor, sample_task, execution_context, mock_llm
    ):
        """测试执行简单任务 (无工具调用)"""
        # Mock LLM 返回验证通过结果
        mock_llm.complete.return_value = LLMResponse(
            content="VERDICT: PASS\nREASON: Task completed successfully",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        result = await task_executor.execute(sample_task, execution_context)

        assert result.status == "success"
        assert "Task completed successfully!" in result.output
        assert result.iterations == 1
        # Validation is enabled, so llm.complete should be called once for validation
        assert mock_llm.complete.call_count >= 1

    @pytest.mark.asyncio
    async def test_execute_with_tool_calls(
        self, task_executor, sample_task, execution_context, mock_llm, mock_tool_executor
    ):
        """测试执行带工具调用的任务"""
        # Mock stream to return tool call then completion
        call_count = [0]
        
        async def mock_stream_with_tool(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: return tool use
                chunks = ["<tool_use><tool_name>web_search</tool_name>", "<parameters>{}</parameters></tool_use>"]
            else:
                # Second call: return completion
                chunks = ["<task_done>Search completed!</task_done>"]
            for chunk in chunks:
                yield chunk
        
        mock_llm.stream = mock_stream_with_tool
        
        # Mock validation to pass
        mock_llm.complete.return_value = LLMResponse(
            content="VERDICT: PASS\nREASON: Task completed with tool call",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        # Mock 工具执行
        mock_tool_executor.has_tool_calls.side_effect = [True, False]
        mock_tool_executor.parse_tool_calls.return_value = [
            MagicMock(tool_name="web_search", parameters={})
        ]
        mock_tool_executor.execute_all.return_value = [
            ToolResult(tool_name="web_search", success=True, result="Search results")
        ]

        result = await task_executor.execute(sample_task, execution_context)

        assert result.status == "success"
        assert result.tool_calls_count == 1
        assert result.iterations == 2

    @pytest.mark.asyncio
    async def test_execute_max_iterations(
        self, task_executor, sample_task, execution_context, mock_llm
    ):
        """测试达到最大迭代次数"""
        # Mock stream to never return completion
        async def mock_stream_no_completion(*args, **kwargs):
            chunks = ["Still thinking..."]
            for chunk in chunks:
                yield chunk
        
        mock_llm.stream = mock_stream_no_completion
        
        # LLM 永远不返回完成标记
        mock_llm.complete.return_value = LLMResponse(
            content="VERDICT: PASS\nREASON: Validation passed",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        result = await task_executor.execute(sample_task, execution_context)

        assert result.status == "timeout"
        assert "max iterations" in result.error.lower()
        assert result.iterations == task_executor.config.max_iterations

    @pytest.mark.asyncio
    async def test_execute_stream(
        self, task_executor, sample_task, execution_context, mock_llm
    ):
        """测试流式执行"""
        mock_llm.complete.return_value = LLMResponse(
            content="<task_done>Done!</task_done>",
            usage={"input_tokens": 100, "output_tokens": 50},
        )

        events = []
        async for event in task_executor.execute_stream(sample_task, execution_context):
            events.append(event)

        # 应该有 THINKING 和 DONE 事件
        event_types = [e.type for e in events]
        assert SSEEventType.THINKING in event_types
        assert SSEEventType.DONE in event_types

        # DONE 事件应该包含成功状态
        done_event = next(e for e in events if e.type == SSEEventType.DONE)
        assert done_event.data["status"] == "success"


# ========== build_task_prompt 测试 ==========


class TestBuildTaskPrompt:
    """测试 Prompt 构建"""

    def test_basic_prompt(self, sample_task, execution_context):
        """测试基本 Prompt 构建"""
        prompt = build_task_prompt(sample_task, execution_context)

        assert "Test Task" in prompt
        assert "This is a test task" in prompt
        assert "web_search" in prompt

    def test_prompt_with_context(self, sample_task, execution_context):
        """测试带上下文的 Prompt"""
        execution_context.add_user_message("Previous message")
        execution_context.set_variable("data_key", "data_value")

        prompt = build_task_prompt(sample_task, execution_context)

        assert "Previous message" in prompt
        assert "data_key" in prompt
        assert "data_value" in prompt


# ========== TaskResult 测试 ==========


class TestTaskResult:
    """TaskResult 测试"""

    def test_is_success(self):
        """测试成功状态判断"""
        success_result = TaskExecutionResult(status="success", output="Done")
        failed_result = TaskExecutionResult(status="failed", error="Error")

        assert success_result.is_success()
        assert not failed_result.is_success()

    def test_to_dict(self):
        """测试转换为字典"""
        result = TaskExecutionResult(
            status="success",
            output="Output text",
            duration_ms=1000,
            tool_calls_count=2,
            iterations=3,
        )

        data = result.to_dict()
        assert data["status"] == "success"
        assert data["output"] == "Output text"
        assert data["duration_ms"] == 1000
        assert data["tool_calls_count"] == 2
        assert data["iterations"] == 3
