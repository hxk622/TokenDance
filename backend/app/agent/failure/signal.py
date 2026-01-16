"""
Failure Signal System - 失败信号系统

实现铁律四：智能来自失败，不来自理解
核心洞察：exit code 是最诚实的老师，让失败可被观测

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class FailureSource(Enum):
    """失败来源"""
    TOOL = "tool"                    # 工具执行失败
    VALIDATION = "validation"        # 验证失败
    TIMEOUT = "timeout"              # 超时
    USER = "user"                    # 用户拒绝/取消
    LLM = "llm"                      # LLM 推理错误
    SYSTEM = "system"                # 系统错误


class FailureType(Enum):
    """失败类型"""
    EXECUTION_ERROR = "execution_error"          # 执行错误
    VALIDATION_FAILED = "validation_failed"      # 验证失败
    TIMEOUT = "timeout"                          # 超时
    REJECTED = "rejected"                        # 被拒绝
    NETWORK_ERROR = "network_error"              # 网络错误
    PERMISSION_DENIED = "permission_denied"      # 权限不足
    RESOURCE_NOT_FOUND = "resource_not_found"    # 资源不存在
    INVALID_PARAMS = "invalid_params"            # 参数无效
    RATE_LIMITED = "rate_limited"                # 限流
    UNKNOWN = "unknown"                          # 未知错误


class ExitCode(Enum):
    """退出码定义 - exit code 是最诚实的反馈
    
    约定：
    - 0: 成功
    - 1: 一般失败（可重试）
    - 2: 需要用户介入
    - 3: 致命错误（不可重试）
    """
    SUCCESS = 0
    FAILURE = 1
    NEED_USER = 2
    FATAL = 3


@dataclass
class FailureSignal:
    """失败信号 - 让失败可被观测
    
    核心职责：
    1. 统一的失败表示
    2. 可重试性判断
    3. 学习信息提取
    """
    
    # 信号来源
    source: FailureSource
    
    # 失败类型
    failure_type: FailureType
    
    # 关键：exit_code (0=成功, 非0=失败)
    exit_code: int
    
    # 错误信息
    error_message: str
    stderr: str = ""
    
    # 上下文
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    
    # 时间戳
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 附加元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """判断是否成功"""
        return self.exit_code == ExitCode.SUCCESS.value
    
    def is_retryable(self) -> bool:
        """判断是否可重试
        
        可重试的条件：
        - exit_code = 1 (一般失败)
        - 失败类型不是致命错误
        """
        if self.exit_code == ExitCode.FATAL.value:
            return False
        
        non_retryable_types = {
            FailureType.PERMISSION_DENIED,
            FailureType.INVALID_PARAMS,
        }
        
        return self.failure_type not in non_retryable_types
    
    def needs_user_intervention(self) -> bool:
        """判断是否需要用户介入"""
        return self.exit_code == ExitCode.NEED_USER.value
    
    def get_learning(self) -> str:
        """从失败中提取教训 - exit code 是最诚实的老师
        
        返回人类可读的学习信息
        """
        error_lower = self.error_message.lower()
        
        # 根据错误类型生成学习建议
        learnings = {
            FailureType.TIMEOUT: "操作超时，考虑增加超时时间或优化操作",
            FailureType.PERMISSION_DENIED: "权限不足，检查文件/API权限",
            FailureType.RESOURCE_NOT_FOUND: "资源不存在，检查路径/URL是否正确",
            FailureType.NETWORK_ERROR: "网络错误，检查网络连接或稍后重试",
            FailureType.RATE_LIMITED: "触发限流，降低请求频率或等待后重试",
            FailureType.INVALID_PARAMS: "参数无效，检查参数格式和类型",
            FailureType.VALIDATION_FAILED: "验证失败，检查输入数据是否符合要求",
        }
        
        if self.failure_type in learnings:
            return learnings[self.failure_type]
        
        # 根据错误消息内容推断
        if "timeout" in error_lower:
            return "操作超时，考虑增加超时时间或优化操作"
        if "permission" in error_lower or "denied" in error_lower:
            return "权限不足，检查文件/API权限"
        if "not found" in error_lower or "404" in error_lower:
            return "资源不存在，检查路径/URL是否正确"
        if "connection" in error_lower or "network" in error_lower:
            return "网络错误，检查网络连接或稍后重试"
        if "rate limit" in error_lower or "429" in error_lower:
            return "触发限流，降低请求频率或等待后重试"
        
        # 默认学习
        if self.tool_name:
            return f"工具 {self.tool_name} 执行失败：{self.error_message}"
        return f"执行失败：{self.error_message}"
    
    def get_severity(self) -> str:
        """获取严重程度"""
        if self.exit_code == ExitCode.SUCCESS.value:
            return "none"
        if self.exit_code == ExitCode.FATAL.value:
            return "critical"
        if self.exit_code == ExitCode.NEED_USER.value:
            return "warning"
        return "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "source": self.source.value,
            "failure_type": self.failure_type.value,
            "exit_code": self.exit_code,
            "error_message": self.error_message,
            "stderr": self.stderr,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "timestamp": self.timestamp.isoformat(),
            "is_retryable": self.is_retryable(),
            "needs_user": self.needs_user_intervention(),
            "learning": self.get_learning(),
            "severity": self.get_severity(),
            "metadata": self.metadata,
        }
    
    def to_progress_entry(self) -> str:
        """转换为 progress.md 记录格式
        
        用于 Keep the Failures 原则
        """
        status = "✅" if self.is_success() else "❌"
        retry = "[可重试]" if self.is_retryable() and not self.is_success() else ""
        
        lines = [
            f"{status} [{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {self.source.value}",
        ]
        
        if self.tool_name:
            lines.append(f"   Tool: {self.tool_name}")
        
        if not self.is_success():
            lines.append(f"   Exit Code: {self.exit_code} {retry}")
            lines.append(f"   Error: {self.error_message}")
            lines.append(f"   Learning: {self.get_learning()}")
        
        return "\n".join(lines)
    
    @classmethod
    def from_tool_result(
        cls,
        tool_name: str,
        success: bool,
        error: Optional[str] = None,
        stderr: str = "",
        tool_args: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> "FailureSignal":
        """从工具执行结果创建 FailureSignal
        
        工厂方法，用于工具执行后创建信号
        """
        if success:
            return cls(
                source=FailureSource.TOOL,
                failure_type=FailureType.EXECUTION_ERROR,  # 成功时类型不重要
                exit_code=ExitCode.SUCCESS.value,
                error_message="",
                stderr="",
                tool_name=tool_name,
                tool_args=tool_args,
                metadata=metadata or {},
            )
        
        # 推断失败类型
        failure_type = cls._infer_failure_type(error or "", stderr)
        exit_code = ExitCode.FAILURE.value
        
        # 某些错误不可重试
        if failure_type == FailureType.PERMISSION_DENIED:
            exit_code = ExitCode.NEED_USER.value
        
        return cls(
            source=FailureSource.TOOL,
            failure_type=failure_type,
            exit_code=exit_code,
            error_message=error or "Unknown error",
            stderr=stderr,
            tool_name=tool_name,
            tool_args=tool_args,
            metadata=metadata or {},
        )
    
    @classmethod
    def _infer_failure_type(cls, error: str, stderr: str) -> FailureType:
        """推断失败类型"""
        combined = f"{error} {stderr}".lower()
        
        if "timeout" in combined:
            return FailureType.TIMEOUT
        if "permission" in combined or "denied" in combined:
            return FailureType.PERMISSION_DENIED
        if "not found" in combined or "404" in combined:
            return FailureType.RESOURCE_NOT_FOUND
        if "connection" in combined or "network" in combined:
            return FailureType.NETWORK_ERROR
        if "rate limit" in combined or "429" in combined:
            return FailureType.RATE_LIMITED
        if "invalid" in combined or "param" in combined:
            return FailureType.INVALID_PARAMS
        
        return FailureType.EXECUTION_ERROR
    
    @classmethod
    def create_success(
        cls,
        tool_name: Optional[str] = None,
        message: str = "Success",
    ) -> "FailureSignal":
        """创建成功信号"""
        return cls(
            source=FailureSource.TOOL if tool_name else FailureSource.SYSTEM,
            failure_type=FailureType.EXECUTION_ERROR,
            exit_code=ExitCode.SUCCESS.value,
            error_message=message,
            tool_name=tool_name,
        )
    
    @classmethod
    def create_timeout(
        cls,
        tool_name: Optional[str] = None,
        timeout_seconds: int = 0,
    ) -> "FailureSignal":
        """创建超时信号"""
        return cls(
            source=FailureSource.TIMEOUT,
            failure_type=FailureType.TIMEOUT,
            exit_code=ExitCode.FAILURE.value,
            error_message=f"Operation timed out after {timeout_seconds}s",
            tool_name=tool_name,
        )
    
    @classmethod
    def create_user_cancelled(cls) -> "FailureSignal":
        """创建用户取消信号"""
        return cls(
            source=FailureSource.USER,
            failure_type=FailureType.REJECTED,
            exit_code=ExitCode.NEED_USER.value,
            error_message="Operation cancelled by user",
        )


@dataclass
class FailureSummary:
    """失败摘要 - 用于 Plan Recitation
    
    在 Context 末尾追加失败摘要，防止重复犯错
    """
    recent_failures: List[FailureSignal] = field(default_factory=list)
    max_failures: int = 5
    
    def add(self, signal: FailureSignal) -> None:
        """添加失败记录"""
        if not signal.is_success():
            self.recent_failures.append(signal)
            # 只保留最近的 N 个失败
            if len(self.recent_failures) > self.max_failures:
                self.recent_failures = self.recent_failures[-self.max_failures:]
    
    def get_same_type_count(self, failure_type: FailureType) -> int:
        """获取同类型失败的次数 (用于 3-Strike Protocol)"""
        return sum(1 for f in self.recent_failures if f.failure_type == failure_type)
    
    def get_same_tool_count(self, tool_name: str) -> int:
        """获取同一工具失败的次数"""
        return sum(1 for f in self.recent_failures if f.tool_name == tool_name)
    
    def should_trigger_3_strike(self, signal: FailureSignal) -> bool:
        """判断是否触发 3-Strike Protocol"""
        # 检查同类型错误
        if self.get_same_type_count(signal.failure_type) >= 3:
            return True
        
        # 检查同工具错误
        if signal.tool_name and self.get_same_tool_count(signal.tool_name) >= 3:
            return True
        
        return False
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式（用于 Plan Recitation）"""
        if not self.recent_failures:
            return ""
        
        lines = ["## ⚠️ 历史失败（避免重复）"]
        
        for f in self.recent_failures:
            learning = f.get_learning()
            tool_info = f" ({f.tool_name})" if f.tool_name else ""
            lines.append(f"- {f.failure_type.value}{tool_info}: {learning}")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        """清空失败记录"""
        self.recent_failures = []
