"""
Tool Call Executor

解析 LLM 输出中的工具调用，执行工具，并返回结果
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.agent.tools.registry import ToolRegistry
from app.core.logging import logger


@dataclass
class ToolCall:
    """工具调用"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: Optional[str] = None  # 用于追踪多个工具调用


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    result: str
    error: Optional[str] = None
    call_id: Optional[str] = None


class ToolCallExecutor:
    """
    工具调用执行器
    
    职责：
    1. 从 LLM 响应中解析工具调用
    2. 执行工具
    3. 处理错误
    4. 返回格式化结果
    """
    
    def __init__(self, tool_registry: ToolRegistry):
        """
        初始化 Executor
        
        Args:
            tool_registry: 工具注册表
        """
        self.tool_registry = tool_registry
    
    def parse_tool_calls(self, llm_response: str) -> List[ToolCall]:
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
    
    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """
        执行单个工具调用
        
        Args:
            tool_call: 工具调用
            
        Returns:
            ToolResult: 工具执行结果
        """
        tool_name = tool_call.tool_name
        
        # 检查工具是否存在
        if not self.tool_registry.has_tool(tool_name):
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result="",
                error=f"Tool '{tool_name}' not found. Available tools: {list(self.tool_registry.list_tools())}",
                call_id=tool_call.call_id
            )
        
        # 获取工具实例
        tool = self.tool_registry.get_tool(tool_name)
        
        try:
            # 验证参数
            tool.validate_args(tool_call.parameters)
            
            # 执行工具
            logger.info(f"Executing tool: {tool_name} with params: {tool_call.parameters}")
            result = await tool.execute(**tool_call.parameters)
            
            logger.info(f"Tool {tool_name} executed successfully")
            
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                call_id=tool_call.call_id
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
    
    async def execute_all(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
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
    
    def format_tool_results(self, results: List[ToolResult]) -> str:
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
            formatted += f"\n<tool_result>\n"
            formatted += f"<tool_name>{result.tool_name}</tool_name>\n"
            formatted += f"<status>{'success' if result.success else 'error'}</status>\n"
            
            if result.success:
                formatted += f"<output>\n{result.result}\n</output>\n"
            else:
                formatted += f"<error>\n{result.error}\n</error>\n"
            
            formatted += f"</tool_result>\n"
        
        formatted += "</tool_results>"
        
        return formatted
    
    def extract_reasoning(self, llm_response: str) -> Optional[str]:
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
    
    def extract_answer(self, llm_response: str) -> Optional[str]:
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
