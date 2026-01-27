"""
TaskValidator 单元测试

测试验证器的核心功能：
1. 快速检查 (Level 0)
2. LLM 自评 (Level 1)
3. 对抗验证 (Level 2)
4. Domain 到 ValidationLevel 映射
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.llm.base import BaseLLM, LLMResponse
from app.agent.validator import (
    TaskValidator,
    ValidationLevel,
    ValidationResult,
    get_validation_level_for_domain,
)

# ========== Fixtures ==========


@pytest.fixture
def mock_llm():
    """创建 Mock LLM"""
    llm = MagicMock(spec=BaseLLM)
    llm.complete = AsyncMock()
    return llm


@pytest.fixture
def validator(mock_llm):
    """创建 TaskValidator 实例"""
    return TaskValidator(llm=mock_llm)


# ========== ValidationLevel 映射测试 ==========


class TestGetValidationLevelForDomain:
    """测试 domain 到 validation_level 的映射"""

    def test_finance_domain(self):
        """金融场景应该使用 adversarial"""
        assert get_validation_level_for_domain("finance") == ValidationLevel.ADVERSARIAL
        assert get_validation_level_for_domain("金融研究报告") == ValidationLevel.ADVERSARIAL
        assert get_validation_level_for_domain("financial analysis") == ValidationLevel.ADVERSARIAL

    def test_medical_domain(self):
        """医疗场景应该使用 adversarial"""
        assert get_validation_level_for_domain("medical") == ValidationLevel.ADVERSARIAL
        assert get_validation_level_for_domain("医疗诊断") == ValidationLevel.ADVERSARIAL
        assert get_validation_level_for_domain("health advice") == ValidationLevel.ADVERSARIAL

    def test_legal_domain(self):
        """法律场景应该使用 adversarial"""
        assert get_validation_level_for_domain("legal") == ValidationLevel.ADVERSARIAL
        assert get_validation_level_for_domain("法律咨询") == ValidationLevel.ADVERSARIAL

    def test_code_domain(self):
        """代码场景应该使用 quick"""
        assert get_validation_level_for_domain("code") == ValidationLevel.QUICK
        assert get_validation_level_for_domain("编程任务") == ValidationLevel.QUICK
        assert get_validation_level_for_domain("programming task") == ValidationLevel.QUICK

    def test_default_domain(self):
        """默认场景应该使用 light"""
        assert get_validation_level_for_domain("general") == ValidationLevel.LIGHT
        assert get_validation_level_for_domain("search for tutorials") == ValidationLevel.LIGHT
        assert get_validation_level_for_domain("") == ValidationLevel.LIGHT


# ========== ValidationResult 测试 ==========


class TestValidationResult:
    """测试 ValidationResult 数据类"""

    def test_passed_result(self):
        """测试通过的验证结果"""
        result = ValidationResult(
            passed=True,
            level=ValidationLevel.LIGHT,
            reason="Validation passed",
            confidence=0.9,
        )
        assert result.passed is True
        assert result.level == ValidationLevel.LIGHT
        assert result.confidence == 0.9

    def test_failed_result_with_issues(self):
        """测试失败的验证结果"""
        result = ValidationResult(
            passed=False,
            level=ValidationLevel.ADVERSARIAL,
            reason="Validation failed",
            issues=["Issue 1", "Issue 2"],
            confidence=0.85,
        )
        assert result.passed is False
        assert len(result.issues) == 2
        assert "Issue 1" in result.issues

    def test_to_dict(self):
        """测试序列化"""
        result = ValidationResult(
            passed=True,
            level=ValidationLevel.LIGHT,
            reason="OK",
        )
        data = result.to_dict()
        assert data["passed"] is True
        assert data["level"] == "light"


# ========== TaskValidator 测试 ==========


class TestTaskValidator:
    """TaskValidator 单元测试"""

    @pytest.mark.asyncio
    async def test_validate_quick_empty_output(self, validator):
        """测试快速检查 - 空输出应该失败"""
        result = await validator.validate(
            task_title="Test Task",
            task_description="Test description",
            acceptance_criteria="Must have output",
            output="",
            level=ValidationLevel.QUICK,
        )
        assert result.passed is False
        assert "Empty output" in result.issues

    @pytest.mark.asyncio
    async def test_validate_quick_valid_output(self, validator):
        """测试快速检查 - 有效输出应该通过"""
        result = await validator.validate(
            task_title="Test Task",
            task_description="Test description",
            acceptance_criteria="Must have output",
            output="This is valid output",
            level=ValidationLevel.QUICK,
        )
        assert result.passed is True
        assert result.level == ValidationLevel.QUICK

    @pytest.mark.asyncio
    async def test_validate_none_skips_validation(self, validator):
        """测试 NONE 级别跳过验证"""
        result = await validator.validate(
            task_title="Test Task",
            task_description="Test description",
            acceptance_criteria="Any criteria",
            output="Any output",
            level=ValidationLevel.NONE,
        )
        assert result.passed is True
        # NONE 级别仍会执行快速检查
        assert result.level == ValidationLevel.QUICK

    @pytest.mark.asyncio
    async def test_validate_light_pass(self, validator, mock_llm):
        """测试轻量验证 - 通过"""
        mock_llm.complete.return_value = LLMResponse(
            content="VERDICT: PASS\nREASON: Output meets all criteria",
            usage={"input_tokens": 100, "output_tokens": 20},
        )

        result = await validator.validate(
            task_title="Search Task",
            task_description="Search for Python tutorials",
            acceptance_criteria="Return at least 3 tutorials",
            output="1. Tutorial A\n2. Tutorial B\n3. Tutorial C",
            level=ValidationLevel.LIGHT,
        )

        assert result.passed is True
        assert result.level == ValidationLevel.LIGHT
        assert mock_llm.complete.call_count == 1

    @pytest.mark.asyncio
    async def test_validate_light_fail(self, validator, mock_llm):
        """测试轻量验证 - 失败"""
        mock_llm.complete.return_value = LLMResponse(
            content="VERDICT: FAIL\nREASON: Only 2 tutorials provided, need 3",
            usage={"input_tokens": 100, "output_tokens": 20},
        )

        result = await validator.validate(
            task_title="Search Task",
            task_description="Search for Python tutorials",
            acceptance_criteria="Return at least 3 tutorials",
            output="1. Tutorial A\n2. Tutorial B",
            level=ValidationLevel.LIGHT,
        )

        assert result.passed is False
        assert result.level == ValidationLevel.LIGHT

    @pytest.mark.asyncio
    async def test_validate_light_error_fallback(self, validator, mock_llm):
        """测试轻量验证 - 错误时回退为通过"""
        mock_llm.complete.side_effect = Exception("LLM Error")

        result = await validator.validate(
            task_title="Search Task",
            task_description="Search for Python tutorials",
            acceptance_criteria="Return tutorials",
            output="Some output",
            level=ValidationLevel.LIGHT,
        )

        # 验证错误时默认通过（避免阻塞流程）
        assert result.passed is True
        assert "error" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_validate_adversarial_no_issues(self, validator, mock_llm):
        """测试对抗验证 - 无问题时直接通过"""
        mock_llm.complete.return_value = LLMResponse(
            content="NO ISSUES FOUND",
            usage={"input_tokens": 100, "output_tokens": 10},
        )

        result = await validator.validate(
            task_title="Finance Report",
            task_description="Generate quarterly report",
            acceptance_criteria="Accurate financial data",
            output="Q4 Revenue: $1.2M, Expenses: $800K",
            level=ValidationLevel.ADVERSARIAL,
        )

        assert result.passed is True
        assert result.level == ValidationLevel.ADVERSARIAL
        # 只调用了 Critic，没有调用 Defender 和 Judge
        assert mock_llm.complete.call_count == 1

    @pytest.mark.asyncio
    async def test_validate_adversarial_with_issues_pass(self, validator, mock_llm):
        """测试对抗验证 - 有问题但最终通过"""
        # Critic 找到问题
        # Defender 回应
        # Judge 最终通过
        mock_llm.complete.side_effect = [
            LLMResponse(
                content="ISSUE 1: Missing source citation",
                usage={"input_tokens": 100, "output_tokens": 20},
            ),
            LLMResponse(
                content="RESPONSE TO ISSUE 1: INVALID - Sources are implied from context",
                usage={"input_tokens": 100, "output_tokens": 30},
            ),
            LLMResponse(
                content="VERDICT: PASS\nREASON: Issues addressed satisfactorily",
                usage={"input_tokens": 100, "output_tokens": 15},
            ),
        ]

        result = await validator.validate(
            task_title="Finance Report",
            task_description="Generate report",
            acceptance_criteria="Accurate data",
            output="Revenue increased by 20%",
            level=ValidationLevel.ADVERSARIAL,
        )

        assert result.passed is True
        assert result.level == ValidationLevel.ADVERSARIAL
        assert mock_llm.complete.call_count == 3  # Critic + Defender + Judge

    @pytest.mark.asyncio
    async def test_validate_adversarial_fail(self, validator, mock_llm):
        """测试对抗验证 - 最终失败"""
        mock_llm.complete.side_effect = [
            LLMResponse(
                content="ISSUE 1: Data is incorrect\nISSUE 2: Missing calculations",
                usage={"input_tokens": 100, "output_tokens": 25},
            ),
            LLMResponse(
                content="RESPONSE TO ISSUE 1: VALID - I made an error\nRESPONSE TO ISSUE 2: VALID - Calculations missing",
                usage={"input_tokens": 100, "output_tokens": 35},
            ),
            LLMResponse(
                content="VERDICT: FAIL\nREASON: Critical issues not resolved",
                usage={"input_tokens": 100, "output_tokens": 15},
            ),
        ]

        result = await validator.validate(
            task_title="Finance Report",
            task_description="Generate report",
            acceptance_criteria="Accurate data",
            output="Revenue: unknown",
            level=ValidationLevel.ADVERSARIAL,
        )

        assert result.passed is False
        assert result.level == ValidationLevel.ADVERSARIAL
        assert len(result.issues) >= 1

    @pytest.mark.asyncio
    async def test_validate_adversarial_error_fallback(self, validator, mock_llm):
        """测试对抗验证 - 错误时回退到轻量验证"""
        # Critic 成功
        # Defender 失败
        mock_llm.complete.side_effect = [
            LLMResponse(
                content="ISSUE 1: Some issue",
                usage={"input_tokens": 100, "output_tokens": 10},
            ),
            Exception("LLM Error"),
            # 回退到 Light 验证
            LLMResponse(
                content="VERDICT: PASS",
                usage={"input_tokens": 100, "output_tokens": 5},
            ),
        ]

        result = await validator.validate(
            task_title="Finance Report",
            task_description="Generate report",
            acceptance_criteria="Accurate data",
            output="Valid output",
            level=ValidationLevel.ADVERSARIAL,
        )

        # 应该回退到 Light 验证并通过
        assert result.passed is True


# ========== TaskExecutor 验证集成测试 ==========


class TestTaskExecutorValidationIntegration:
    """测试 TaskExecutor 与 Validator 的集成"""

    @pytest.mark.asyncio
    async def test_validation_disabled(self, mock_llm):
        """测试禁用验证"""
        from app.agent.execution_context import ExecutionContext
        from app.agent.executor import ToolCallExecutor
        from app.agent.planning.task import Task
        from app.agent.task_executor import TaskExecutor, TaskExecutorConfig
        from app.agent.types import SSEEventType

        mock_tool_executor = MagicMock(spec=ToolCallExecutor)
        mock_tool_executor.has_tool_calls = MagicMock(return_value=False)
        mock_tool_executor.has_final_answer = MagicMock(return_value=False)

        config = TaskExecutorConfig(
            enable_validation=False,  # 禁用验证
            max_iterations=5,
        )

        executor = TaskExecutor(
            llm=mock_llm,
            tool_executor=mock_tool_executor,
            config=config,
        )

        # Mock stream to return completion
        async def mock_stream_completion(*args, **kwargs):
            chunks = ["<task_done>Done!</task_done>"]
            for chunk in chunks:
                yield chunk
        
        mock_llm.stream = mock_stream_completion
        
        mock_llm.complete.return_value = LLMResponse(
            content="<task_done>Done!</task_done>",
            usage={"input_tokens": 100, "output_tokens": 20},
        )

        task = Task(
            id="test",
            title="Test",
            description="Test task",
            validation_level="light",
        )
        context = ExecutionContext(session_id="s1", workspace_id="w1")

        events = []
        async for event in executor.execute_stream(task, context):
            events.append(event)

        # 不应该有验证事件
        validation_events = [
            e for e in events
            if e.type in (
                SSEEventType.VALIDATION_START,
                SSEEventType.VALIDATION_RESULT,
            )
        ]
        assert len(validation_events) == 0

        # 验证禁用时，complete 不应该被调用（因为不需要验证LLM调用）
        # 任务执行使用stream，不使用complete
        assert mock_llm.complete.call_count == 0
