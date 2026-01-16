"""
Exit Tool - Agent 的主动终止工具

实现铁律三：工具是世界接口，不是插件
核心工具之一：让 Agent 能主动声明任务完成或失败

exit 的哲学：
- Agent 必须能主动说"我完成了"或"我做不到"
- 不是被动等待超时，而是主动给出明确信号
- exit_code 是对任务结果的承诺

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from ..base import BaseTool, ToolResult, ToolRiskLevel


class ExitReason(Enum):
    """退出原因"""
    SUCCESS = "success"              # 任务完成
    FAILED = "failed"                # 任务失败
    NEED_USER = "need_user"          # 需要用户介入
    CANNOT_PROCEED = "cannot_proceed"  # 无法继续
    MANUAL_STOP = "manual_stop"      # 手动停止


@dataclass
class ExitContext:
    """退出上下文 - 记录退出时的状态"""
    reason: ExitReason
    exit_code: int
    message: str
    summary: str = ""                # 任务完成摘要
    deliverables: list = field(default_factory=list)  # 交付物列表
    failures: list = field(default_factory=list)      # 失败记录
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reason": self.reason.value,
            "exit_code": self.exit_code,
            "message": self.message,
            "summary": self.summary,
            "deliverables": self.deliverables,
            "failures": self.failures,
            "metadata": self.metadata,
        }


class ExitTool(BaseTool):
    """Exit Tool - Agent 主动终止工具
    
    这是 4+2 核心工具之一，让 Agent 能够：
    1. 主动声明任务完成（exit_code=0）
    2. 主动声明任务失败（exit_code=1）
    3. 请求用户介入（exit_code=2）
    4. 报告致命错误（exit_code=3）
    
    Usage:
        exit(code=0, message="任务完成", summary="创建了3个文件...")
        exit(code=1, message="无法连接API", failures=["网络错误"])
        exit(code=2, message="需要API密钥", need_user_for="提供API密钥")
    """
    
    name: str = "exit"
    description: str = (
        "主动终止任务执行。使用 exit_code 表示结果：\n"
        "- 0: 任务成功完成\n"
        "- 1: 任务失败（可能可重试）\n"
        "- 2: 需要用户提供信息或做决定\n"
        "- 3: 致命错误（不可恢复）\n\n"
        "调用 exit 后，Agent 将停止执行并返回控制权。"
    )
    risk_level: ToolRiskLevel = ToolRiskLevel.NONE
    
    # 退出上下文（执行后填充）
    last_exit_context: Optional[ExitContext] = None
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取参数 schema"""
        return {
            "type": "object",
            "properties": {
                "exit_code": {
                    "type": "integer",
                    "description": "退出码：0=成功, 1=失败, 2=需用户, 3=致命",
                    "enum": [0, 1, 2, 3],
                    "default": 0,
                },
                "message": {
                    "type": "string",
                    "description": "退出消息，说明退出原因",
                },
                "summary": {
                    "type": "string",
                    "description": "任务完成摘要（成功时）",
                    "default": "",
                },
                "deliverables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "交付物列表（成功时），如创建的文件路径",
                    "default": [],
                },
                "failures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "失败记录（失败时）",
                    "default": [],
                },
                "need_user_for": {
                    "type": "string",
                    "description": "需要用户提供什么（exit_code=2时）",
                    "default": "",
                },
            },
            "required": ["exit_code", "message"],
        }
    
    async def execute(
        self,
        exit_code: int = 0,
        message: str = "",
        summary: str = "",
        deliverables: Optional[list] = None,
        failures: Optional[list] = None,
        need_user_for: str = "",
        **kwargs,
    ) -> ToolResult:
        """执行退出
        
        Args:
            exit_code: 退出码（0-3）
            message: 退出消息
            summary: 任务摘要
            deliverables: 交付物列表
            failures: 失败记录
            need_user_for: 需要用户提供什么
        
        Returns:
            ToolResult with exit context
        """
        # 验证 exit_code
        if exit_code not in [0, 1, 2, 3]:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid exit_code: {exit_code}. Must be 0, 1, 2, or 3.",
            )
        
        # 确定退出原因
        reason_map = {
            0: ExitReason.SUCCESS,
            1: ExitReason.FAILED,
            2: ExitReason.NEED_USER,
            3: ExitReason.CANNOT_PROCEED,
        }
        reason = reason_map[exit_code]
        
        # 构建退出上下文
        context = ExitContext(
            reason=reason,
            exit_code=exit_code,
            message=message,
            summary=summary,
            deliverables=deliverables or [],
            failures=failures or [],
            metadata={
                "need_user_for": need_user_for,
            },
        )
        
        # 保存上下文
        self.last_exit_context = context
        
        # 构建输出消息
        output_lines = [
            f"Exit Code: {exit_code}",
            f"Reason: {reason.value}",
            f"Message: {message}",
        ]
        
        if summary:
            output_lines.append(f"Summary: {summary}")
        
        if deliverables:
            output_lines.append(f"Deliverables: {', '.join(deliverables)}")
        
        if failures:
            output_lines.append(f"Failures: {', '.join(failures)}")
        
        if need_user_for:
            output_lines.append(f"Need from user: {need_user_for}")
        
        output = "\n".join(output_lines)
        
        # exit 总是"成功"的（即使 exit_code != 0）
        # 因为 exit 本身是一个有效的操作
        return ToolResult(
            success=True,
            output=output,
            error=None,
            metadata={
                "exit_context": context.to_dict(),
                "is_terminal": True,  # 标记这是终止操作
            },
        )
    
    def get_exit_context(self) -> Optional[ExitContext]:
        """获取最后的退出上下文"""
        return self.last_exit_context
    
    def was_successful(self) -> bool:
        """检查最后一次退出是否成功"""
        if self.last_exit_context is None:
            return False
        return self.last_exit_context.exit_code == 0


# 便捷函数
def create_success_exit(
    summary: str,
    deliverables: Optional[list] = None,
    message: str = "任务完成",
) -> Dict[str, Any]:
    """创建成功退出的参数"""
    return {
        "exit_code": 0,
        "message": message,
        "summary": summary,
        "deliverables": deliverables or [],
    }


def create_failure_exit(
    message: str,
    failures: Optional[list] = None,
) -> Dict[str, Any]:
    """创建失败退出的参数"""
    return {
        "exit_code": 1,
        "message": message,
        "failures": failures or [],
    }


def create_need_user_exit(
    message: str,
    need_user_for: str,
) -> Dict[str, Any]:
    """创建需要用户介入的退出参数"""
    return {
        "exit_code": 2,
        "message": message,
        "need_user_for": need_user_for,
    }


def create_fatal_exit(
    message: str,
    failures: Optional[list] = None,
) -> Dict[str, Any]:
    """创建致命错误退出的参数"""
    return {
        "exit_code": 3,
        "message": message,
        "failures": failures or [],
    }
