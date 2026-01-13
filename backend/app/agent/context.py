"""
Agent Context - 运行时上下文管理
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

# from app.models import Message, Session  # TODO: Re-enable when DB is ready
from .types import Plan, ToolCallRecord


@dataclass
class AgentContext:
    """Agent 运行时上下文
    
    封装 Agent 运行过程中的所有状态信息
    """
    # Session 信息
    session_id: str
    user_id: str
    workspace_id: str
    
    # 消息历史
    messages: List[Any] = field(default_factory=list)  # TODO: Change to List[Message]
    
    # 当前轮次的临时状态
    current_message_id: Optional[str] = None
    current_thinking: str = ""
    current_tool_calls: List[ToolCallRecord] = field(default_factory=list)
    
    # Plan Recitation
    plan: Optional[Plan] = None
    
    # KV Cache（Session 级别）
    kv_cache: Dict[str, Any] = field(default_factory=dict)
    
    # Token 使用统计
    tokens_used: int = 0
    max_tokens: int = 200_000  # Claude 3.5 Sonnet context window
    
    # 执行状态
    iteration: int = 0
    max_iterations: int = 50
    
    # HITL 确认状态
    pending_confirmation: Optional[Dict[str, Any]] = None
    confirmation_result: Optional[bool] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.current_message_id is None:
            self.current_message_id = str(uuid.uuid4())
    
    def increment_iteration(self) -> None:
        """递增迭代计数"""
        self.iteration += 1
    
    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """添加 token 使用量
        
        Args:
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
        """
        self.tokens_used += input_tokens + output_tokens
    
    def reset_current_turn(self) -> None:
        """重置当前轮次的临时状态"""
        self.current_message_id = str(uuid.uuid4())
        self.current_thinking = ""
        self.current_tool_calls.clear()
    
    def append_thinking(self, content: str) -> None:
        """追加思考内容
        
        Args:
            content: 思考文本
        """
        self.current_thinking += content
    
    def add_tool_call(self, tool_call: ToolCallRecord) -> None:
        """添加工具调用记录
        
        Args:
            tool_call: 工具调用记录
        """
        self.current_tool_calls.append(tool_call)
    
    def update_tool_call(self, tool_id: str, **updates) -> None:
        """更新工具调用记录
        
        Args:
            tool_id: 工具调用 ID
            **updates: 更新的字段
        """
        for tc in self.current_tool_calls:
            if tc.id == tool_id:
                for key, value in updates.items():
                    setattr(tc, key, value)
                break
    
    def set_pending_confirmation(self, action_id: str, data: Dict[str, Any]) -> None:
        """设置待确认状态
        
        Args:
            action_id: 动作 ID
            data: 确认数据
        """
        self.pending_confirmation = {
            "action_id": action_id,
            "data": data
        }
        self.confirmation_result = None
    
    def resolve_confirmation(self, confirmed: bool) -> None:
        """解决确认状态
        
        Args:
            confirmed: 是否确认
        """
        self.confirmation_result = confirmed
        self.pending_confirmation = None
    
    def has_pending_confirmation(self) -> bool:
        """检查是否有待确认的动作
        
        Returns:
            bool: 是否有待确认
        """
        return self.pending_confirmation is not None
    
    def should_continue(self) -> bool:
        """判断是否应该继续执行
        
        Returns:
            bool: 是否继续
        """
        # 检查迭代次数
        if self.iteration >= self.max_iterations:
            return False
        
        # 检查 token 使用量（保留 5% 余量）
        if self.tokens_used >= self.max_tokens * 0.95:
            return False
        
        return True
    
    # TODO: Re-enable when DB models are available
    # @classmethod
    # async def from_session(
    #     cls,
    #     session: Session,
    #     messages: List[Message]
    # ) -> "AgentContext":
    #     """从 Session 创建 Context"""
    #     plan = None
    #     if session.todo_list:
    #         pass
    #     
    #     return cls(
    #         session_id=str(session.id),
    #         user_id=str(session.user_id),
    #         workspace_id=str(session.workspace_id),
    #         messages=messages,
    #         plan=plan
    #     )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）
        
        Returns:
            Dict: 字典表示
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "iteration": self.iteration,
            "tokens_used": self.tokens_used,
            "has_plan": self.plan is not None,
            "message_count": len(self.messages),
        }
    
    def __repr__(self) -> str:
        return (
            f"<AgentContext("
            f"session={self.session_id[:8]}, "
            f"iteration={self.iteration}, "
            f"tokens={self.tokens_used}/{self.max_tokens})>"
        )
