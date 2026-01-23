"""
Tool Call Executor

解析 LLM 输出中的工具调用，执行工具，并返回结果
支持统一重试策略，自动处理瞬时错误
"""

import json
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from app.agent.retry import RetryExecutor, RetryPolicy
from app.agent.tools.registry import ToolRegistry
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    parameters: dict[str, Any]
    call_id: str | None = None  # 用于追踪多个工具调用


@dataclass
class ToolResult:
    """工具执行结果

    result 字段存储 JSON 序列化后的工具返回值，便于注入 LLM Context。
    原始的 dict 结果存储在 result_data 字段（如果需要程序化访问）。
    """
    tool_name: str
    success: bool
    result: str  # JSON 序列化的结果文本
    error: str | None = None
    call_id: str | None = None
    result_data: dict[str, Any] | None = None  # 原始 dict 结果


class ToolCallExecutor:
    """
    工具调用执行器

    职责：
    1. 从 LLM 响应中解析工具调用
    2. 执行工具（带自动重试）
    3. 处理错误
    4. 返回格式化结果
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        enable_retry: bool = True,
        default_retry_policy: RetryPolicy | None = None,
    ):
        """
        初始化 Executor

        Args:
            tool_registry: 工具注册表
            enable_retry: 是否启用自动重试（默认启用）
            default_retry_policy: 默认重试策略（可选）
        """
        self.tool_registry = tool_registry
        self.enable_retry = enable_retry
        self.default_retry_policy = default_retry_policy or RetryPolicy.default()

    def parse_tool_calls(self, llm_response: str) -> list[ToolCall]:
        """
        从 LLM 响应中解析工具调用

        支持格式：
        <tool_use>
        <tool_name>web_search</tool_name>
        <parameters>
        {
          "query": "FastAPI best practices"
        }
        </parameters>
        </tool_use>

        Args:
            llm_response: LLM 的完整响应文本

        Returns:
            List[ToolCall]: 解析出的工具调用列表
        """
        tool_calls = []

        # 正则匹配 <tool_use>...</tool_use> 块
        tool_use_pattern = r'<tool_use>(.*?)</tool_use>'
        matches = re.findall(tool_use_pattern, llm_response, re.DOTALL)

        for i, match in enumerate(matches):
            # 提取 tool_name
            name_match = re.search(r'<tool_name>(.*?)</tool_name>', match)
            if not name_match:
                logger.warning(f"Tool call {i} missing tool_name")
                continue

            tool_name = name_match.group(1).strip()

            # 提取 parameters
            params_match = re.search(r'<parameters>(.*?)</parameters>', match, re.DOTALL)
            if not params_match:
                logger.warning(f"Tool call {i} missing parameters")
                continue

            params_str = params_match.group(1).strip()

            try:
                # 解析 JSON 参数
                parameters = json.loads(params_str)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse parameters for {tool_name}: {e}")
                logger.error(f"Parameters string: {params_str}")
                continue

            tool_calls.append(ToolCall(
                tool_name=tool_name,
                parameters=parameters,
                call_id=f"call_{i}"
            ))

        return tool_calls

    async def execute_tool_call(
        self,
        tool_call: ToolCall,
        retry_policy: RetryPolicy | None = None,
    ) -> ToolResult:
        """
        执行单个工具调用（带自动重试）

        Args:
            tool_call: 工具调用
            retry_policy: 自定义重试策略（可选，覆盖默认策略）

        Returns:
            ToolResult: 工具执行结果
        """
        tool_name = tool_call.tool_name

        # 检查工具是否存在
        if not self.tool_registry.has(tool_name):
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result="",
                error=f"Tool '{tool_name}' not found. Available tools: {self.tool_registry.list_names()}",
                call_id=tool_call.call_id
            )

        # 获取工具实例
        tool = self.tool_registry.get(tool_name)

        # 内部执行函数（用于重试）
        async def _execute() -> dict[str, Any]:
            tool.validate_args(tool_call.parameters)
            return await tool.execute(**tool_call.parameters)

        # 决定重试策略
        policy = retry_policy or self.default_retry_policy

        if self.enable_retry:
            # 使用统一重试执行器
            executor = RetryExecutor(policy=policy, tool_name=tool_name)
            retry_result = await executor.execute(_execute)

            if retry_result.success:
                logger.info(
                    f"Tool {tool_name} executed successfully"
                    + (f" (attempts={retry_result.attempts})" if retry_result.attempts > 1 else "")
                )
                # 序列化结果为 JSON 字符串（支持 dict 和 dataclass）
                result_data = retry_result.result
                result_dict = self._normalize_result(result_data)
                result_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result_str,
                    call_id=tool_call.call_id,
                    result_data=result_dict
                )
            else:
                # 重试失败
                error_msg = retry_result.error or "Unknown error"
                if retry_result.attempts > 1:
                    error_msg += f" (after {retry_result.attempts} attempts)"

                logger.error(f"Tool {tool_name} execution failed: {error_msg}")
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result="",
                    error=error_msg,
                    call_id=tool_call.call_id
                )
        else:
            # 不重试，直接执行
            try:
                logger.info(f"Executing tool: {tool_name} with params: {tool_call.parameters}")
                result_data = await _execute()
                logger.info(f"Tool {tool_name} executed successfully")
                # 序列化结果为 JSON 字符串（支持 dict 和 dataclass）
                result_dict = self._normalize_result(result_data)
                result_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
                return ToolResult(
                    tool_name=tool_name,
                    success=True,
                    result=result_str,
                    call_id=tool_call.call_id,
                    result_data=result_dict
                )
            except Exception as e:
                logger.error(f"Tool {tool_name} execution failed: {e}")
                return ToolResult(
                    tool_name=tool_name,
                    success=False,
                    result="",
                    error=str(e),
                    call_id=tool_call.call_id
                )

    def _normalize_result(self, result: Any) -> dict[str, Any]:
        """
        将工具返回值规范化为 dict

        支持：
        - dict: 直接返回
        - dataclass (e.g. ToolResult from base.py): 转换为 dict
        - 其他类型: 包装为 {"result": str(value)}

        Args:
            result: 工具执行返回值

        Returns:
            dict[str, Any]: 规范化的结果字典
        """
        if isinstance(result, dict):
            return result
        elif is_dataclass(result) and not isinstance(result, type):
            # dataclass 实例，使用 asdict 转换
            return asdict(result)
        else:
            # 其他类型，包装为字典
            return {"result": str(result)}

    async def execute_all(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """
        执行多个工具调用

        Args:
            tool_calls: 工具调用列表

        Returns:
            List[ToolResult]: 工具执行结果列表
        """
        results = []

        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call)
            results.append(result)

        return results

    def format_tool_results(self, results: list[ToolResult]) -> str:
        """
        格式化工具执行结果为文本（注入回 LLM Context）

        Args:
            results: 工具执行结果列表

        Returns:
            str: 格式化后的文本
        """
        if not results:
            return ""

        formatted = "<tool_results>\n"

        for result in results:
            formatted += "\n<tool_result>\n"
            formatted += f"<tool_name>{result.tool_name}</tool_name>\n"
            formatted += f"<status>{'success' if result.success else 'error'}</status>\n"

            if result.success:
                formatted += f"<output>\n{result.result}\n</output>\n"
            else:
                formatted += f"<error>\n{result.error}\n</error>\n"

            formatted += "</tool_result>\n"

        formatted += "</tool_results>"

        return formatted

    def extract_reasoning(self, llm_response: str) -> str | None:
        """
        从 LLM 响应中提取推理过程

        Args:
            llm_response: LLM 响应

        Returns:
            Optional[str]: 推理文本，如果没有则返回 None
        """
        reasoning_match = re.search(r'<reasoning>(.*?)</reasoning>', llm_response, re.DOTALL)
        if reasoning_match:
            return reasoning_match.group(1).strip()
        return None

    def extract_answer(self, llm_response: str) -> str | None:
        """
        从 LLM 响应中提取最终答案

        Args:
            llm_response: LLM 响应

        Returns:
            Optional[str]: 答案文本，如果没有则返回 None
        """
        answer_match = re.search(r'<answer>(.*?)</answer>', llm_response, re.DOTALL)
        if answer_match:
            return answer_match.group(1).strip()
        return None

    def has_tool_calls(self, llm_response: str) -> bool:
        """
        检查 LLM 响应是否包含工具调用

        Args:
            llm_response: LLM 响应

        Returns:
            bool: 是否包含工具调用
        """
        return '<tool_use>' in llm_response

    def has_final_answer(self, llm_response: str) -> bool:
        """
        检查 LLM 响应是否包含最终答案

        Args:
            llm_response: LLM 响应

        Returns:
            bool: 是否包含最终答案
        """
        return '<answer>' in llm_response
