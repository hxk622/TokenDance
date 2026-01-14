"""
Context Manager

负责组装 Agent 的 LLM Context：
- System Prompt
- Tool Definitions
- Message History
- Working Memory (三文件摘要)
- Plan Recitation
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.tools.registry import ToolRegistry
from app.agent.working_memory.three_files import ThreeFilesManager
from app.agent.llm.base import LLMMessage
from app.core.logging import logger


@dataclass
class Message:
    """消息"""
    role: str  # "user" | "assistant" | "system"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ContextManager:
    """
    Context 管理器
    
    核心职责：
    1. 组装完整的 Context（System + Tools + History + Working Memory）
    2. 实现 Plan Recitation（末尾追加 TODO）
    3. 管理 Token 预算
    4. 实现 Append-Only 增长模式
    """
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        three_files: ThreeFilesManager,
        session_id: str,
        max_context_tokens: int = 100000  # Claude 的 context window
    ):
        """
        初始化 Context Manager
        
        Args:
            tool_registry: 工具注册表
            three_files: 三文件管理器
            session_id: Session ID
            max_context_tokens: 最大 context tokens
        """
        self.tool_registry = tool_registry
        self.three_files = three_files
        self.session_id = session_id
        self.max_context_tokens = max_context_tokens
        
        # Message 历史（Append-Only）
        self.messages: List[Message] = []
        
        # Token 统计
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def get_system_prompt(self) -> str:
        """
        获取 System Prompt
        
        Returns:
            str: System Prompt（包含三文件路径信息）
        """
        # 基础 System Prompt
        system = AGENT_SYSTEM_PROMPT
        
        # 添加三文件路径信息
        file_paths = self.three_files.get_file_paths()
        system += f"\n\n# Your Working Memory Files\n\n"
        system += f"- **task_plan.md**: `{file_paths['task_plan']}`\n"
        system += f"- **findings.md**: `{file_paths['findings']}`\n"
        system += f"- **progress.md**: `{file_paths['progress']}`\n"
        system += f"\n**Session ID**: `{self.session_id}`\n"
        
        return system
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取所有工具定义（LLM 格式）
        
        Returns:
            List[Dict]: 工具定义列表
        """
        tools = []
        
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(tool_name)
            tools.append(tool.to_llm_format())
        
        return tools
    
    def add_user_message(self, content: str):
        """
        添加用户消息
        
        Args:
            content: 消息内容
        """
        self.messages.append(Message(
            role="user",
            content=content
        ))
        logger.info(f"Added user message: {content[:100]}...")
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None):
        """
        添加 Assistant 消息
        
        Args:
            content: 消息内容
            metadata: 元数据（如 token usage）
        """
        self.messages.append(Message(
            role="assistant",
            content=content,
            metadata=metadata
        ))
        logger.info(f"Added assistant message: {content[:100]}...")
    
    def add_tool_result_message(self, tool_results_text: str):
        """
        添加工具结果消息（作为 user 消息注入）
        
        Args:
            tool_results_text: 格式化后的工具结果
        """
        self.messages.append(Message(
            role="user",
            content=tool_results_text
        ))
        logger.info(f"Added tool results: {tool_results_text[:100]}...")
    
    def get_messages_for_llm(self, include_plan_recitation: bool = True) -> List[LLMMessage]:
        """
        获取用于 LLM 调用的消息列表
        
        Args:
            include_plan_recitation: 是否在末尾追加 Plan Recitation
            
        Returns:
            List[LLMMessage]: LLM 消息列表
        """
        llm_messages = []
        
        # 转换为 LLMMessage 格式
        for msg in self.messages:
            llm_messages.append(LLMMessage(
                role=msg.role,
                content=msg.content
            ))
        
        # Plan Recitation: 在末尾追加当前 TODO
        if include_plan_recitation:
            plan_recitation = self._generate_plan_recitation()
            if plan_recitation:
                # 如果最后一条消息是 user，追加到其内容
                if llm_messages and llm_messages[-1].role == "user":
                    llm_messages[-1].content += f"\n\n{plan_recitation}"
                else:
                    # 否则创建新的 user 消息
                    llm_messages.append(LLMMessage(
                        role="user",
                        content=plan_recitation
                    ))
        
        return llm_messages
    
    def _generate_plan_recitation(self) -> Optional[str]:
        """
        生成 Plan Recitation（TODO 清单背诵）
        
        Returns:
            Optional[str]: Plan Recitation 文本
        """
        try:
            # 读取 task_plan.md
            task_plan = self.three_files.read_task_plan()
            content = task_plan.get("content", "")
            
            if not content or len(content.strip()) < 50:
                return None
            
            # 提取未完成的 TODO 项
            lines = content.split("\n")
            todos = []
            for line in lines:
                if line.strip().startswith("- [ ]"):
                    todos.append(line.strip())
            
            if not todos:
                return None
            
            # 生成 Recitation
            recitation = "\n\n---\n\n**🎯 Plan Recitation (Current TODO)**\n\n"
            recitation += "Remember your current goals:\n"
            for todo in todos[:5]:  # 最多显示 5 个
                recitation += f"{todo}\n"
            
            if len(todos) > 5:
                recitation += f"\n... and {len(todos) - 5} more tasks\n"
            
            recitation += "\nStay focused on these objectives!"
            
            return recitation
        
        except Exception as e:
            logger.warning(f"Failed to generate plan recitation: {e}")
            return None
    
    def get_working_memory_summary(self) -> str:
        """
        获取三文件工作记忆摘要
        
        Returns:
            str: 摘要文本
        """
        return self.three_files.get_context_summary()
    
    def should_inject_working_memory(self) -> bool:
        """
        判断是否应该注入工作记忆摘要
        
        策略：
        - 每 5 轮对话注入一次
        - 或者当 context 较长时注入
        
        Returns:
            bool: 是否注入
        """
        # 简单策略：每 5 条消息注入一次
        return len(self.messages) % 5 == 0
    
    def inject_working_memory(self):
        """
        注入工作记忆摘要到 context
        """
        summary = self.get_working_memory_summary()
        
        # 作为 user 消息注入
        self.messages.append(Message(
            role="user",
            content=f"📋 **Working Memory Snapshot**\n\n{summary}"
        ))
        logger.info("Injected working memory summary")
    
    def update_token_usage(self, input_tokens: int, output_tokens: int):
        """
        更新 Token 使用统计
        
        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
        """
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        
        logger.info(
            f"Token usage - Input: {input_tokens}, Output: {output_tokens} "
            f"(Total: {self.total_input_tokens + self.total_output_tokens})"
        )
    
    def get_token_usage(self) -> Dict[str, int]:
        """
        获取 Token 使用统计
        
        Returns:
            Dict: {"input": int, "output": int, "total": int}
        """
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "total": self.total_input_tokens + self.total_output_tokens
        }
    
    def is_context_near_limit(self, threshold: float = 0.7) -> bool:
        """
        检查 context 是否接近上限
        
        Args:
            threshold: 阈值（0-1）
            
        Returns:
            bool: 是否接近上限
        """
        total_tokens = self.total_input_tokens + self.total_output_tokens
        return total_tokens > (self.max_context_tokens * threshold)
    
    def get_message_count(self) -> int:
        """
        获取消息数量
        
        Returns:
            int: 消息数量
        """
        return len(self.messages)
    
    def get_last_message(self) -> Optional[Message]:
        """
        获取最后一条消息
        
        Returns:
            Optional[Message]: 最后一条消息
        """
        if self.messages:
            return self.messages[-1]
        return None
    
    def clear(self):
        """
        清空 context（谨慎使用）
        """
        self.messages.clear()
        logger.warning("Context cleared!")
