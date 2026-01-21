"""
TaskValidator - 分层任务验证器

实现 LLM-as-a-Judge 最佳实践：
- Level 0: 快速检查 (格式、非空、exit_code)
- Level 1: LLM 自评 (单次 Yes/No 验证)
- Level 2: 对抗验证 (Critic → Defender → Judge)

设计原则：
- Binary 评估 > 连续打分
- Chain-of-Thought 提高可靠性
- 按场景选择验证级别
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.agent.llm.base import BaseLLM, LLMMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


# ========== 枚举和数据结构 ==========


class ValidationLevel(str, Enum):
    """验证级别"""
    NONE = "none"           # 不验证 (信任 exit_code)
    QUICK = "quick"         # Level 0: 快速检查
    LIGHT = "light"         # Level 1: LLM 自评 (默认)
    ADVERSARIAL = "adversarial"  # Level 2: 对抗验证 (金融等严谨场景)


@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    level: ValidationLevel
    reason: str = ""
    issues: list[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0-1.0

    # 对抗验证的详细信息
    critic_feedback: str | None = None
    defender_response: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "level": self.level.value,
            "reason": self.reason,
            "issues": self.issues,
            "confidence": self.confidence,
        }


# ========== Prompts ==========


VALIDATION_LIGHT_PROMPT = """You are a task validator. Evaluate if the output satisfies the acceptance criteria.

## Task
{task_title}

## Task Description
{task_description}

## Acceptance Criteria
{acceptance_criteria}

## Output to Validate
{output}

---

**Question**: Does this output FULLY satisfy the acceptance criteria?

**Instructions**:
1. Consider each criterion carefully
2. Check for completeness and accuracy
3. Answer PASS if ALL criteria are met, FAIL otherwise

**Response Format**:
VERDICT: [PASS or FAIL]
REASON: [One sentence explanation]
"""

VALIDATION_CRITIC_PROMPT = """You are a skeptical reviewer tasked with finding potential issues.

## Task
{task_title}

## Acceptance Criteria
{acceptance_criteria}

## Output to Review
{output}

---

**Your job**: Find up to 3 potential issues with this output. Look for:
- Factual errors or unsupported claims
- Missing information required by the criteria
- Logical inconsistencies
- Incomplete answers

**Response Format**:
If issues found:
ISSUE 1: [description]
ISSUE 2: [description]
ISSUE 3: [description]

If no issues found:
NO ISSUES FOUND

Be thorough but fair. Only report genuine issues.
"""

VALIDATION_DEFENDER_PROMPT = """You are defending the output against criticism.

## Task
{task_title}

## Output Being Defended
{output}

## Critic's Issues
{issues}

---

**Your job**: For each issue, explain why it's either:
1. Invalid (the output actually addresses this)
2. Valid (acknowledge the limitation)

**Response Format**:
RESPONSE TO ISSUE 1: [INVALID/VALID] - [explanation]
RESPONSE TO ISSUE 2: [INVALID/VALID] - [explanation]
RESPONSE TO ISSUE 3: [INVALID/VALID] - [explanation]
"""

VALIDATION_JUDGE_PROMPT = """You are the final judge. Based on the critic's issues and defender's responses, make a final verdict.

## Task
{task_title}

## Acceptance Criteria
{acceptance_criteria}

## Critic's Issues
{critic_issues}

## Defender's Responses
{defender_responses}

---

**Question**: Considering both perspectives, does the output satisfy the acceptance criteria?

**Response Format**:
VERDICT: [PASS or FAIL]
REASON: [One sentence final judgment]
"""


# ========== TaskValidator ==========


class TaskValidator:
    """
    任务验证器 - 实现分层验证

    使用示例:
    ```python
    validator = TaskValidator(llm)
    result = await validator.validate(
        task_title="Search for Python tutorials",
        task_description="Find top 5 Python tutorials",
        acceptance_criteria="Return at least 5 tutorials with titles and URLs",
        output="1. Tutorial A (url1)...",
        level=ValidationLevel.LIGHT
    )
    if result.passed:
        # 验证通过
    else:
        # 验证失败，可以重试
    ```
    """

    def __init__(self, llm: BaseLLM):
        """
        初始化验证器

        Args:
            llm: LLM 客户端 (用于 Level 1 和 Level 2 验证)
        """
        self.llm = llm

    async def validate(
        self,
        task_title: str,
        task_description: str,
        acceptance_criteria: str,
        output: str,
        level: ValidationLevel = ValidationLevel.LIGHT,
        tool_exit_codes: list[int] | None = None,
    ) -> ValidationResult:
        """
        执行验证

        Args:
            task_title: 任务标题
            task_description: 任务描述
            acceptance_criteria: 验收条件
            output: 待验证的输出
            level: 验证级别
            tool_exit_codes: 工具调用的 exit codes (用于快速检查)

        Returns:
            ValidationResult: 验证结果
        """
        logger.info(f"Validating task: {task_title} (level={level.value})")

        # Level 0: 快速检查 (所有级别都执行)
        quick_result = self._validate_quick(output, tool_exit_codes)
        if not quick_result.passed:
            return quick_result

        # 如果级别是 NONE 或 QUICK，直接返回快速检查结果
        if level in (ValidationLevel.NONE, ValidationLevel.QUICK):
            return quick_result

        # Level 1: LLM 自评
        if level == ValidationLevel.LIGHT:
            return await self._validate_light(
                task_title, task_description, acceptance_criteria, output
            )

        # Level 2: 对抗验证
        if level == ValidationLevel.ADVERSARIAL:
            return await self._validate_adversarial(
                task_title, task_description, acceptance_criteria, output
            )

        return quick_result

    def _validate_quick(
        self,
        output: str,
        tool_exit_codes: list[int] | None = None,
    ) -> ValidationResult:
        """
        Level 0: 快速检查

        检查项:
        - 输出非空
        - 工具调用成功 (exit_code = 0)
        """
        issues = []

        # 检查输出非空
        if not output or not output.strip():
            return ValidationResult(
                passed=False,
                level=ValidationLevel.QUICK,
                reason="Output is empty",
                issues=["Empty output"],
            )

        # 检查工具 exit codes
        if tool_exit_codes:
            failed_tools = [code for code in tool_exit_codes if code != 0]
            if failed_tools:
                issues.append(f"Some tools failed with exit codes: {failed_tools}")

        # 如果有问题但不致命，记录但通过
        return ValidationResult(
            passed=True,
            level=ValidationLevel.QUICK,
            reason="Quick check passed",
            issues=issues,
        )

    async def _validate_light(
        self,
        task_title: str,
        task_description: str,
        acceptance_criteria: str,
        output: str,
    ) -> ValidationResult:
        """
        Level 1: LLM 自评 (单次 Yes/No)
        """
        prompt = VALIDATION_LIGHT_PROMPT.format(
            task_title=task_title,
            task_description=task_description,
            acceptance_criteria=acceptance_criteria or "Complete the task as described",
            output=output[:2000],  # 限制长度
        )

        try:
            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=prompt)],
                system="You are a precise task validator. Be strict but fair.",
            )

            # 解析结果
            content = response.content.upper()
            passed = "VERDICT: PASS" in content or "VERDICT:PASS" in content

            # 提取原因
            reason = ""
            if "REASON:" in response.content:
                reason = response.content.split("REASON:")[-1].strip()

            return ValidationResult(
                passed=passed,
                level=ValidationLevel.LIGHT,
                reason=reason or ("Validation passed" if passed else "Validation failed"),
                confidence=0.8 if passed else 0.7,
            )

        except Exception as e:
            logger.error(f"Light validation failed: {e}")
            # 验证失败时默认通过，避免阻塞流程
            return ValidationResult(
                passed=True,
                level=ValidationLevel.LIGHT,
                reason=f"Validation error (defaulting to pass): {e}",
                confidence=0.5,
            )

    async def _validate_adversarial(
        self,
        task_title: str,
        task_description: str,
        acceptance_criteria: str,
        output: str,
    ) -> ValidationResult:
        """
        Level 2: 对抗验证 (Critic → Defender → Judge)

        适用于金融、医疗等需要严谨验证的场景
        """
        try:
            # Step 1: Critic 找问题
            critic_prompt = VALIDATION_CRITIC_PROMPT.format(
                task_title=task_title,
                acceptance_criteria=acceptance_criteria or "Complete the task as described",
                output=output[:2000],
            )

            critic_response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=critic_prompt)],
                system="You are a thorough skeptical reviewer.",
            )

            critic_content = critic_response.content

            # 如果没有发现问题，直接通过
            if "NO ISSUES FOUND" in critic_content.upper():
                return ValidationResult(
                    passed=True,
                    level=ValidationLevel.ADVERSARIAL,
                    reason="Adversarial validation passed: No issues found by critic",
                    critic_feedback=critic_content,
                    confidence=0.95,
                )

            # Step 2: Defender 回应
            defender_prompt = VALIDATION_DEFENDER_PROMPT.format(
                task_title=task_title,
                output=output[:1500],
                issues=critic_content,
            )

            defender_response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=defender_prompt)],
                system="You are a fair defender. Acknowledge valid criticisms.",
            )

            defender_content = defender_response.content

            # Step 3: Judge 最终裁定
            judge_prompt = VALIDATION_JUDGE_PROMPT.format(
                task_title=task_title,
                acceptance_criteria=acceptance_criteria or "Complete the task as described",
                critic_issues=critic_content,
                defender_responses=defender_content,
            )

            judge_response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=judge_prompt)],
                system="You are a fair and decisive judge.",
            )

            judge_content = judge_response.content.upper()
            passed = "VERDICT: PASS" in judge_content or "VERDICT:PASS" in judge_content

            # 提取原因
            reason = ""
            if "REASON:" in judge_response.content:
                reason = judge_response.content.split("REASON:")[-1].strip()

            # 提取问题列表
            issues = []
            for line in critic_content.split("\n"):
                if line.strip().startswith("ISSUE"):
                    issue_text = line.split(":", 1)[-1].strip() if ":" in line else line
                    issues.append(issue_text)

            return ValidationResult(
                passed=passed,
                level=ValidationLevel.ADVERSARIAL,
                reason=reason or ("Adversarial validation passed" if passed else "Adversarial validation failed"),
                issues=issues,
                critic_feedback=critic_content,
                defender_response=defender_content,
                confidence=0.9 if passed else 0.85,
            )

        except Exception as e:
            logger.error(f"Adversarial validation failed: {e}")
            # 对抗验证失败时，降级到 Light 验证
            logger.info("Falling back to light validation")
            return await self._validate_light(
                task_title, task_description, acceptance_criteria, output
            )


# ========== 辅助函数 ==========


def get_validation_level_for_domain(domain: str) -> ValidationLevel:
    """
    根据领域返回推荐的验证级别

    Args:
        domain: 领域标识

    Returns:
        ValidationLevel: 推荐的验证级别
    """
    # 严谨场景使用对抗验证
    strict_domains = {
        "finance", "financial", "金融",
        "medical", "health", "医疗", "健康",
        "legal", "law", "法律",
        "security", "安全",
    }

    # 代码场景使用快速检查 (依赖 exit_code)
    code_domains = {
        "code", "programming", "代码", "编程",
        "script", "automation",
    }

    domain_lower = domain.lower()

    for strict in strict_domains:
        if strict in domain_lower:
            return ValidationLevel.ADVERSARIAL

    for code in code_domains:
        if code in domain_lower:
            return ValidationLevel.QUICK

    # 默认使用轻量级验证
    return ValidationLevel.LIGHT
