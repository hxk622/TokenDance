"""
Intent validation service for pre-flight checks.

Uses LLM (via OpenRouter) to analyze if user input is complete and actionable.
"""
import asyncio
import hashlib
import json
import logging
import time

from app.agent.llm.base import LLMMessage
from app.agent.llm.openrouter import OpenRouterLLM
from app.core.config import settings
from app.schemas.intent import (
    ClarificationOption,
    IntentValidationRequest,
    IntentValidationResponse,
)

logger = logging.getLogger(__name__)

# Global rate limiting for OpenRouter calls
_last_call_time: float = 0.0
_min_call_interval: float = 2.0  # Minimum 2 seconds between calls
_call_lock = asyncio.Lock()

# Simple in-memory cache for validation results
_validation_cache: dict[str, tuple[IntentValidationResponse, float]] = {}
_cache_ttl: float = 300.0  # Cache for 5 minutes
_max_cache_size: int = 100


def _get_cache_key(user_input: str, context: dict[str, str] | None) -> str:
    """Generate cache key from input and context."""
    context_str = json.dumps(context, sort_keys=True) if context else ""
    content = f"{user_input}|{context_str}"
    return hashlib.md5(content.encode()).hexdigest()


def _get_cached_response(cache_key: str) -> IntentValidationResponse | None:
    """Get cached response if valid."""
    if cache_key in _validation_cache:
        response, timestamp = _validation_cache[cache_key]
        if time.time() - timestamp < _cache_ttl:
            logger.info(f"Intent validation cache hit for key: {cache_key[:8]}...")
            return response
        else:
            # Expired, remove from cache
            del _validation_cache[cache_key]
    return None


def _set_cached_response(cache_key: str, response: IntentValidationResponse) -> None:
    """Cache a response."""
    # Evict old entries if cache is too large
    if len(_validation_cache) >= _max_cache_size:
        # Remove oldest entry
        oldest_key = min(_validation_cache.keys(), key=lambda k: _validation_cache[k][1])
        del _validation_cache[oldest_key]
    _validation_cache[cache_key] = (response, time.time())


# System prompt for intent validation
INTENT_VALIDATION_PROMPT = """
你是一个意图分析助手。分析用户输入，判断意图是否完整可执行，并识别任务类型。

## 任务类型识别
根据用户意图识别 task_type：
- "deep_research": 调研、研究、分析、了解、调查类任务
- "ppt_generation": PPT、演示文稿、幻灯片生成
- "code_refactor": 代码重构、优化、修改
- "file_operations": 文件操作、整理、批量处理
- "general": 其他通用任务

## 评估规则
1. **研究类任务（调研/分析/了解）**: 只要主题明确，直接返回 is_complete=true
   - "调研下agent memory" → is_complete=true, task_type="deep_research"
   - "分析一下市场趋势" → is_complete=true, task_type="deep_research"
   - "了解下 RAG 技术" → is_complete=true, task_type="deep_research"

2. **生成类任务（PPT/报告）**: 需要主题，但不需要完整细节
   - "生成AI市场PPT" → is_complete=true
   - "生成一份PPT" → is_complete=false（缺主题）

3. **模糊意图**: 仅当完全无法理解用户想做什么时才返回 is_complete=false
   - "帮我" → is_complete=false
   - "做点事" → is_complete=false

## 输出格式
输出有效 JSON：
{
  "is_complete": true/false,
  "confidence_score": 0.0-1.0,
  "detected_task_type": "deep_research|ppt_generation|code_refactor|file_operations|general",
  "clarification_options": [
    {"label": "选项显示文本", "value": "附加到输入的值"}
  ],
  "reasoning": "简短推理"
}

## clarification_options 规则
- 仅当 is_complete=false 时才需要提供
- 每个选项必须有 label（展示）和 value（提交值）
- 提供 2-4 个实用选项

## 示例
输入："调研下agent memory"
输出：{"is_complete": true, "confidence_score": 0.95, "detected_task_type": "deep_research", "clarification_options": [], "reasoning": "研究类任务，主题明确"}

输入："生成一份PPT"
输出：{"is_complete": false, "confidence_score": 0.8, "detected_task_type": "ppt_generation", "clarification_options": [{"label": "关于 AI 技术趋势", "value": "主题：AI技术趋势"}, {"label": "关于公司业务介绍", "value": "主题：公司业务介绍"}, {"label": "关于项目进展汇报", "value": "主题：项目进展汇报"}], "reasoning": "缺少PPT主题"}

输入："帮我"
输出：{"is_complete": false, "confidence_score": 0.95, "detected_task_type": "general", "clarification_options": [{"label": "进行调研分析", "value": "帮我调研"}, {"label": "生成文档/PPT", "value": "帮我生成文档"}, {"label": "处理代码问题", "value": "帮我处理代码"}], "reasoning": "意图过于模糊"}
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

        # Use a globally available model (Claude may be region-restricted)
        # Fallback order: claude -> deepseek -> llama
        model = settings.DEFAULT_LLM_MODEL or "deepseek/deepseek-chat"
        logger.info(f"Using OpenRouter for intent validation with model: {model}")
        return OpenRouterLLM(
            api_key=settings.OPENROUTER_API_KEY,
            model=model,
            max_tokens=2048,
            temperature=0.3,  # Lower temperature for more consistent validation
        )

    async def validate_intent(
        self, request: IntentValidationRequest
    ) -> IntentValidationResponse:
        """Validate user intent using LLM with caching and rate limiting.

        Args:
            request: Intent validation request with user input

        Returns:
            IntentValidationResponse: Validation results

        Raises:
            Exception: If LLM call fails
        """
        global _last_call_time

        # Check cache first
        cache_key = _get_cache_key(request.user_input, request.context)
        cached_response = _get_cached_response(cache_key)
        if cached_response is not None:
            return cached_response

        try:
            # Rate limiting: ensure minimum interval between calls
            async with _call_lock:
                elapsed = time.time() - _last_call_time
                if elapsed < _min_call_interval:
                    wait_time = _min_call_interval - elapsed
                    logger.info(f"Rate limiting: waiting {wait_time:.1f}s before LLM call")
                    await asyncio.sleep(wait_time)
                _last_call_time = time.time()

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

            # Parse clarification_options
            raw_options = validation_result.get("clarification_options", [])
            clarification_options = []
            for opt in raw_options:
                if isinstance(opt, dict) and "label" in opt and "value" in opt:
                    clarification_options.append(
                        ClarificationOption(label=opt["label"], value=opt["value"])
                    )

            # If incomplete but no options provided, generate defaults
            is_complete = validation_result.get("is_complete", False)
            detected_task_type = validation_result.get("detected_task_type", "general")

            if not is_complete and not clarification_options:
                clarification_options = self._generate_default_options(detected_task_type)

            # Convert to response schema
            result = IntentValidationResponse(
                is_complete=is_complete,
                confidence_score=validation_result.get("confidence_score", 0.0),
                # Legacy fields for backward compatibility
                missing_info=validation_result.get("missing_info", []),
                suggested_questions=validation_result.get("suggested_questions", []),
                # New fields
                clarification_options=clarification_options,
                detected_task_type=detected_task_type,
                reasoning=validation_result.get("reasoning"),
            )

            # Cache successful response
            _set_cached_response(cache_key, result)
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {content}")
            # Fallback: allow execution if parsing fails, detect task type from input
            detected_type = self._detect_task_type_fallback(request.user_input)
            return IntentValidationResponse(
                is_complete=True,
                confidence_score=0.5,
                missing_info=[],
                suggested_questions=[],
                clarification_options=[],
                detected_task_type=detected_type,
                reasoning="无法解析验证结果，默认允许执行",
            )

        except Exception as e:
            logger.error(f"Intent validation failed: {e}")
            # Fallback: allow execution on error
            detected_type = self._detect_task_type_fallback(request.user_input)
            return IntentValidationResponse(
                is_complete=True,
                confidence_score=0.0,
                missing_info=[],
                suggested_questions=[],
                clarification_options=[],
                detected_task_type=detected_type,
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

    def _generate_default_options(
        self, task_type: str
    ) -> list[ClarificationOption]:
        """Generate default clarification options based on task type.

        Args:
            task_type: Detected task type

        Returns:
            list[ClarificationOption]: Default options
        """
        defaults = {
            "ppt_generation": [
                ClarificationOption(label="关于 AI/技术趋势", value="主题：AI技术趋势分析"),
                ClarificationOption(label="关于业务/产品介绍", value="主题：产品介绍"),
                ClarificationOption(label="关于项目进展汇报", value="主题：项目进展汇报"),
            ],
            "deep_research": [
                ClarificationOption(label="深入调研并生成报告", value="请深入调研并生成完整报告"),
                ClarificationOption(label="快速概述即可", value="只需快速概述即可"),
            ],
            "general": [
                ClarificationOption(label="进行调研分析", value="帮我调研分析"),
                ClarificationOption(label="生成文档/报告", value="帮我生成文档"),
                ClarificationOption(label="处理代码问题", value="帮我处理代码"),
            ],
        }
        return defaults.get(task_type, defaults["general"])

    def _detect_task_type_fallback(self, user_input: str) -> str:
        """Fallback task type detection using simple keyword matching.

        Args:
            user_input: User's input text

        Returns:
            str: Detected task type
        """
        input_lower = user_input.lower()

        # Research keywords
        if any(kw in input_lower for kw in ["调研", "研究", "分析", "了解", "调查", "research", "analyze"]):
            return "deep_research"

        # PPT keywords
        if any(kw in input_lower for kw in ["ppt", "演示", "幻灯片", "文稿", "slides"]):
            return "ppt_generation"

        # Code keywords
        if any(kw in input_lower for kw in ["代码", "重构", "code", "refactor", "优化"]):
            return "code_refactor"

        # File keywords
        if any(kw in input_lower for kw in ["文件", "批量", "file", "整理"]):
            return "file_operations"

        return "general"
