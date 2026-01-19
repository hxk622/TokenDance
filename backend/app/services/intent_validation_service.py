"""
Intent validation service for pre-flight checks.

Uses LLM (via OpenRouter) to analyze if user input is complete and actionable.
"""
import json
import logging

from app.agent.llm.base import LLMMessage
from app.agent.llm.openrouter import OpenRouterLLM
from app.core.config import settings
from app.schemas.intent import IntentValidationRequest, IntentValidationResponse

logger = logging.getLogger(__name__)

# System prompt for intent validation
INTENT_VALIDATION_PROMPT = """你是一个意图验证助手。分析用户输入是否包含足够的信息来执行任务。

评估标准：
1. 意图是否清晰且可执行？
2. 是否缺少关键细节？
3. 任务是否可以按原样执行？

输出 JSON 格式（必须是有效 JSON）：
{
  "is_complete": true/false,
  "confidence_score": 0.0-1.0,
  "missing_info": ["缺少的细节1", "缺少的细节2"],
  "suggested_questions": ["澄清问题1", "澄清问题2"],
  "reasoning": "简短的推理解释"
}

规则：
- 只标记真正关键的缺失信息
- 保持简洁，不要过度提问
- 如果任务足够清晰可执行，即使某些细节可以改进，也应返回 is_complete=true
- confidence_score 表示对判断的信心（0-1）
- 如果用户意图非常模糊（如"帮我做点事"），则 is_complete=false

示例：
输入："生成一份关于AI市场的PPT"
输出：{"is_complete": true, "confidence_score": 0.9, "missing_info": [], "suggested_questions": [], "reasoning": "任务清晰，包含主题和格式"}

输入："生成一份PPT"
输出：{"is_complete": false, "confidence_score": 0.8, "missing_info": ["PPT主题或内容", "目标受众"], "suggested_questions": ["这份PPT的主题是什么？", "PPT的目标受众是谁？"], "reasoning": "缺少关键的主题信息"}

输入："帮我"
输出：{"is_complete": false, "confidence_score": 0.95, "missing_info": ["具体任务内容"], "suggested_questions": ["您需要什么帮助？请描述具体任务"], "reasoning": "意图过于模糊"}
"""


class IntentValidationService:
    """Service for validating user intent completeness using LLM (via OpenRouter)."""

    def __init__(self) -> None:
        """Initialize the intent validation service with LLM client."""
        self.llm = self._create_llm_client()

    def _create_llm_client(self) -> OpenRouterLLM:
        """Create OpenRouter LLM client.

        Returns:
            OpenRouterLLM: Initialized LLM client

        Raises:
            ValueError: If OPENROUTER_API_KEY is not configured
        """
        if not settings.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not configured. Please set it in .env file."
            )

        logger.info("Using OpenRouter for intent validation")
        return OpenRouterLLM(
            api_key=settings.OPENROUTER_API_KEY,
            model="anthropic/claude-3.5-sonnet",
            max_tokens=2048,
            temperature=0.3,  # Lower temperature for more consistent validation
        )

    async def validate_intent(
        self, request: IntentValidationRequest
    ) -> IntentValidationResponse:
        """Validate user intent using LLM.

        Args:
            request: Intent validation request with user input

        Returns:
            IntentValidationResponse: Validation results

        Raises:
            Exception: If LLM call fails
        """
        try:
            # Prepare user message
            user_message = f"用户输入: {request.user_input}"
            if request.context:
                context_str = ", ".join(
                    f"{k}: {v}" for k, v in request.context.items()
                )
                user_message += f"\n\n上下文: {context_str}"

            # Call LLM
            logger.info(f"Validating intent for input: {request.user_input[:100]}")
            response = await self.llm.complete(
                messages=[LLMMessage(role="user", content=user_message)],
                system=INTENT_VALIDATION_PROMPT,
                max_tokens=1024,
                temperature=0.3,
            )

            # Parse LLM response
            content = response.content.strip()
            logger.debug(f"LLM response: {content}")

            # Extract JSON from response (handle code blocks)
            json_content = self._extract_json(content)
            validation_result = json.loads(json_content)

            # Convert to response schema
            return IntentValidationResponse(
                is_complete=validation_result.get("is_complete", False),
                confidence_score=validation_result.get("confidence_score", 0.0),
                missing_info=validation_result.get("missing_info", []),
                suggested_questions=validation_result.get("suggested_questions", []),
                reasoning=validation_result.get("reasoning"),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            # Fallback: allow execution if parsing fails
            return IntentValidationResponse(
                is_complete=True,
                confidence_score=0.5,
                missing_info=[],
                suggested_questions=[],
                reasoning="无法解析验证结果，默认允许执行",
            )

        except Exception as e:
            logger.error(f"Intent validation failed: {e}")
            # Fallback: allow execution on error
            return IntentValidationResponse(
                is_complete=True,
                confidence_score=0.0,
                missing_info=[],
                suggested_questions=[],
                reasoning=f"验证失败: {str(e)}，默认允许执行",
            )

    def _extract_json(self, content: str) -> str:
        """Extract JSON from LLM response, handling code blocks.

        Args:
            content: Raw LLM response

        Returns:
            str: Extracted JSON string
        """
        # Try to find JSON in code blocks
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        if "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()

        # If no code block, try to find JSON object
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            return content[start:end]

        # Return as-is if no markers found
        return content
