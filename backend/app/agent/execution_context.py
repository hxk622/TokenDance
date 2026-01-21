"""
ExecutionContext - 执行上下文

跨 Task 共享的状态容器，支持：
- Append-Only 消息历史
- 全局变量传递
- Token 使用统计
- 断点恢复
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.agent.planning.task import Plan


@dataclass
class Message:
    """上下文消息"""
    role: str  # "user" | "assistant" | "tool_result" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenUsage:
    """Token 使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total": self.total,
        }


@dataclass
class ExecutionContext:
    """
    执行上下文 - 跨 Task 共享的状态

    设计原则：
    - Append-Only: 消息只追加，不修改
    - 可序列化: 支持断点恢复
    - 隔离性: 每个 session 独立的上下文
    """

    session_id: str
    workspace_id: str

    # 消息历史 (跨 Task 共享)
    messages: list[Message] = field(default_factory=list)

    # 当前 Plan (如果在 Planning 模式)
    current_plan: Plan | None = None

    # 全局变量 (Task 间传递数据)
    variables: dict[str, Any] = field(default_factory=dict)

    # Token 使用统计
    token_usage: TokenUsage = field(default_factory=TokenUsage)

    # 创建时间
    created_at: datetime = field(default_factory=datetime.now)

    # ========== 消息操作 ==========

    def add_user_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加用户消息"""
        self.messages.append(Message(
            role="user",
            content=content,
            metadata=metadata or {},
        ))

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加助手消息"""
        self.messages.append(Message(
            role="assistant",
            content=content,
            metadata=metadata or {},
        ))

    def add_tool_result(self, tool_name: str, result: str, success: bool = True) -> None:
        """添加工具结果"""
        self.messages.append(Message(
            role="tool_result",
            content=result,
            metadata={
                "tool_name": tool_name,
                "success": success,
            },
        ))

    def add_system_message(self, content: str) -> None:
        """添加系统消息"""
        self.messages.append(Message(
            role="system",
            content=content,
        ))

    # ========== 变量操作 ==========

    def set_variable(self, key: str, value: Any) -> None:
        """设置全局变量"""
        self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        """获取全局变量"""
        return self.variables.get(key, default)

    def has_variable(self, key: str) -> bool:
        """检查变量是否存在"""
        return key in self.variables

    # ========== Token 统计 ==========

    def add_token_usage(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """添加 Token 使用量"""
        self.token_usage.add(input_tokens, output_tokens)

    def get_token_usage(self) -> dict[str, int]:
        """获取 Token 使用统计"""
        return self.token_usage.to_dict()

    # ========== 消息查询 ==========

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        """获取用于 LLM 的消息列表"""
        return [
            {"role": msg.role if msg.role != "tool_result" else "user", "content": msg.content}
            for msg in self.messages
        ]

    def get_last_n_messages(self, n: int) -> list[Message]:
        """获取最近 n 条消息"""
        return self.messages[-n:] if n < len(self.messages) else self.messages

    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self.messages)

    # ========== 序列化 ==========

    def to_dict(self) -> dict[str, Any]:
        """转换为字典 (用于持久化)"""
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in self.messages
            ],
            "variables": self.variables,
            "token_usage": self.token_usage.to_dict(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionContext":
        """从字典恢复"""
        ctx = cls(
            session_id=data["session_id"],
            workspace_id=data["workspace_id"],
        )

        for msg_data in data.get("messages", []):
            ctx.messages.append(Message(
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata", {}),
            ))

        ctx.variables = data.get("variables", {})

        token_data = data.get("token_usage", {})
        ctx.token_usage = TokenUsage(
            input_tokens=token_data.get("input_tokens", 0),
            output_tokens=token_data.get("output_tokens", 0),
        )

        if "created_at" in data:
            ctx.created_at = datetime.fromisoformat(data["created_at"])

        return ctx

    # ========== 辅助方法 ==========

    def clone(self) -> "ExecutionContext":
        """克隆上下文 (用于并行执行时隔离)"""
        return ExecutionContext.from_dict(self.to_dict())

    def clear_messages(self) -> None:
        """清空消息 (谨慎使用)"""
        self.messages = []

    def __repr__(self) -> str:
        return (
            f"ExecutionContext(session={self.session_id}, "
            f"messages={len(self.messages)}, "
            f"tokens={self.token_usage.total})"
        )
