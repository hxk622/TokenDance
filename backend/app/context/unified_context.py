"""
UnifiedExecutionContext - 统一执行上下文

管理 Skill、MCP 和 LLM 三种执行模式的共享数据和执行历史，
支持跨路径的数据传递和降级流程。
"""

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """执行状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    FALLBACK = "fallback"


class ExecutionType(Enum):
    """执行类型枚举"""
    SKILL = "skill"
    MCP_CODE = "mcp_code"
    LLM_REASONING = "llm_reasoning"


@dataclass
class ExecutionRecord:
    """单次执行记录"""
    execution_id: str              # 唯一执行 ID
    execution_type: ExecutionType  # 执行类型
    status: ExecutionStatus        # 执行状态
    user_message: str              # 用户输入
    start_time: datetime          # 开始时间
    end_time: Optional[datetime] = None  # 结束时间
    result: Optional[Any] = None   # 执行结果
    error: Optional[str] = None    # 错误信息
    duration: Optional[float] = None  # 执行耗时（秒）
    tokens_used: int = 0           # 消耗 Token 数
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 日期时间序列化
        data["start_time"] = self.start_time.isoformat()
        data["end_time"] = self.end_time.isoformat() if self.end_time else None
        data["execution_type"] = self.execution_type.value
        data["status"] = self.status.value
        return data


class ToolRegistry:
    """
    工具注册表 - 管理可用的工具和权限
    
    用于限制代码执行中的工具访问权限，
    支持 API key、数据库连接等敏感信息的管理。
    """

    def __init__(self):
        """初始化工具注册表"""
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._permissions: Dict[str, bool] = {}

    def register_tool(
        self,
        tool_name: str,
        tool_config: Dict[str, Any],
        enabled: bool = True,
    ) -> None:
        """
        注册工具
        
        Args:
            tool_name: 工具名称 (e.g., "requests", "pandas", "sqlite3")
            tool_config: 工具配置（API key、连接串等）
            enabled: 是否启用
        """
        self._tools[tool_name] = tool_config
        self._permissions[tool_name] = enabled
        logger.info(f"Tool registered: {tool_name} (enabled={enabled})")

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具配置
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具配置字典，如果未注册或已禁用返回 None
        """
        if tool_name not in self._tools:
            return None
        if not self._permissions.get(tool_name, False):
            return None
        return self._tools[tool_name]

    def is_tool_available(self, tool_name: str) -> bool:
        """
        检查工具是否可用
        
        Args:
            tool_name: 工具名称
            
        Returns:
            True 如果工具可用
        """
        return (
            tool_name in self._tools
            and self._permissions.get(tool_name, False)
        )

    def enable_tool(self, tool_name: str) -> None:
        """启用工具"""
        if tool_name in self._tools:
            self._permissions[tool_name] = True
            logger.info(f"Tool enabled: {tool_name}")

    def disable_tool(self, tool_name: str) -> None:
        """禁用工具"""
        if tool_name in self._tools:
            self._permissions[tool_name] = False
            logger.info(f"Tool disabled: {tool_name}")

    def list_available_tools(self) -> List[str]:
        """获取所有可用工具"""
        return [
            name for name, enabled in self._permissions.items()
            if enabled
        ]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "tools": list(self._tools.keys()),
            "available_tools": self.list_available_tools(),
            "permissions": self._permissions,
        }


class UnifiedExecutionContext:
    """
    统一执行上下文
    
    管理 Skill、MCP 和 LLM 三种执行模式的共享数据，包括：
    1. 共享变量空间（用于跨路径数据传递）
    2. 执行历史（用于决策和调试）
    3. 工具访问权限（API keys、数据库连接等）
    4. Session 隔离（不同用户的数据独立）
    """

    def __init__(self, session_id: Optional[str] = None):
        """
        初始化统一执行上下文
        
        Args:
            session_id: Session ID（用于隔离），如果为 None 则自动生成
        """
        self.session_id = session_id or str(uuid.uuid4())
        
        # 共享变量空间（可被 Skill 和 MCP 访问）
        self.shared_vars: Dict[str, Any] = {}
        
        # 执行历史（按执行顺序记录）
        self.execution_history: List[ExecutionRecord] = []
        
        # 工具注册表
        self.tools = ToolRegistry()
        
        # 上下文元数据
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        logger.info(f"UnifiedExecutionContext created: {self.session_id}")

    def set_var(self, key: str, value: Any) -> None:
        """
        设置共享变量
        
        Args:
            key: 变量名
            value: 变量值
        """
        self.shared_vars[key] = value
        self.last_updated = datetime.now()
        logger.debug(f"Variable set: {key} = {type(value).__name__}")

    def get_var(self, key: str, default: Any = None) -> Any:
        """
        获取共享变量
        
        Args:
            key: 变量名
            default: 默认值（如果变量不存在）
            
        Returns:
            变量值或默认值
        """
        return self.shared_vars.get(key, default)

    def has_var(self, key: str) -> bool:
        """检查变量是否存在"""
        return key in self.shared_vars

    def delete_var(self, key: str) -> None:
        """删除变量"""
        if key in self.shared_vars:
            del self.shared_vars[key]
            self.last_updated = datetime.now()
            logger.debug(f"Variable deleted: {key}")

    def clear_vars(self) -> None:
        """清空所有变量"""
        self.shared_vars.clear()
        self.last_updated = datetime.now()
        logger.info("All variables cleared")

    def get_all_vars(self) -> Dict[str, Any]:
        """获取所有变量的副本"""
        return self.shared_vars.copy()

    def record_execution(
        self,
        execution_type: ExecutionType,
        user_message: str,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionRecord:
        """
        记录执行事件
        
        Args:
            execution_type: 执行类型
            user_message: 用户消息
            status: 执行状态
            result: 执行结果
            error: 错误信息（如果有）
            tokens_used: 消耗 Token 数
            metadata: 额外元数据
            
        Returns:
            ExecutionRecord 对象
        """
        now = datetime.now()
        record = ExecutionRecord(
            execution_id=str(uuid.uuid4()),
            execution_type=execution_type,
            status=status,
            user_message=user_message,
            start_time=now,
            end_time=now if status in [
                ExecutionStatus.SUCCESS,
                ExecutionStatus.FAILED,
                ExecutionStatus.TIMEOUT,
            ] else None,
            result=result,
            error=error,
            tokens_used=tokens_used,
            metadata=metadata or {},
        )
        
        self.execution_history.append(record)
        self.last_updated = datetime.now()
        
        logger.info(
            f"Execution recorded: {execution_type.value} - {status.value} "
            f"(id={record.execution_id})"
        )
        
        return record

    def update_execution_record(
        self,
        execution_id: str,
        status: ExecutionStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        tokens_used: int = 0,
    ) -> Optional[ExecutionRecord]:
        """
        更新执行记录
        
        Args:
            execution_id: 执行 ID
            status: 新状态
            result: 执行结果
            error: 错误信息
            tokens_used: 消耗 Token 数
            
        Returns:
            更新后的 ExecutionRecord，如果未找到则返回 None
        """
        for record in self.execution_history:
            if record.execution_id == execution_id:
                record.status = status
                record.end_time = datetime.now()
                record.result = result
                record.error = error
                record.tokens_used = tokens_used
                
                # 计算耗时
                if record.end_time and record.start_time:
                    duration = (record.end_time - record.start_time).total_seconds()
                    record.duration = duration
                
                self.last_updated = datetime.now()
                logger.info(
                    f"Execution record updated: {execution_id} - {status.value}"
                )
                return record
        
        logger.warning(f"Execution record not found: {execution_id}")
        return None

    def get_execution_record(self, execution_id: str) -> Optional[ExecutionRecord]:
        """获取执行记录"""
        for record in self.execution_history:
            if record.execution_id == execution_id:
                return record
        return None

    def get_execution_history(
        self,
        execution_type: Optional[ExecutionType] = None,
        limit: Optional[int] = None,
    ) -> List[ExecutionRecord]:
        """
        获取执行历史
        
        Args:
            execution_type: 可选的执行类型过滤
            limit: 最近 N 条记录
            
        Returns:
            执行记录列表
        """
        records = self.execution_history
        
        if execution_type:
            records = [r for r in records if r.execution_type == execution_type]
        
        if limit:
            records = records[-limit:]
        
        return records

    def get_last_execution(
        self,
        execution_type: Optional[ExecutionType] = None,
    ) -> Optional[ExecutionRecord]:
        """获取最后一次执行记录"""
        records = self.get_execution_history(execution_type=execution_type)
        return records[-1] if records else None

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息
        
        Returns:
            统计字典
        """
        total = len(self.execution_history)
        if total == 0:
            return {
                "total_executions": 0,
                "success_count": 0,
                "failed_count": 0,
                "by_type": {},
            }
        
        stats = {
            "total_executions": total,
            "success_count": sum(
                1 for r in self.execution_history
                if r.status == ExecutionStatus.SUCCESS
            ),
            "failed_count": sum(
                1 for r in self.execution_history
                if r.status in [
                    ExecutionStatus.FAILED,
                    ExecutionStatus.TIMEOUT,
                ]
            ),
            "by_type": {},
        }
        
        # 按执行类型统计
        for exec_type in ExecutionType:
            type_records = [
                r for r in self.execution_history
                if r.execution_type == exec_type
            ]
            if type_records:
                stats["by_type"][exec_type.value] = {
                    "count": len(type_records),
                    "success_count": sum(
                        1 for r in type_records
                        if r.status == ExecutionStatus.SUCCESS
                    ),
                    "total_tokens": sum(r.tokens_used for r in type_records),
                }
        
        return stats

    def clear_history(self) -> None:
        """清空执行历史"""
        self.execution_history.clear()
        self.last_updated = datetime.now()
        logger.info("Execution history cleared")

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典（用于序列化）
        
        Returns:
            包含上下文所有信息的字典
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "shared_vars": {
                k: str(v) if not isinstance(v, (str, int, float, bool, list, dict))
                else v
                for k, v in self.shared_vars.items()
            },
            "execution_history": [r.to_dict() for r in self.execution_history],
            "tools": self.tools.to_dict(),
            "execution_stats": self.get_execution_stats(),
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), indent=2, default=str)


# 上下文管理器：Session 隔离
_context_instances: Dict[str, UnifiedExecutionContext] = {}


def get_unified_context(session_id: Optional[str] = None) -> UnifiedExecutionContext:
    """
    获取或创建统一执行上下文（Session 隔离）
    
    Args:
        session_id: Session ID，如果为 None 则创建新的 context
        
    Returns:
        UnifiedExecutionContext 实例
    """
    if session_id is None:
        # 创建新的 context
        context = UnifiedExecutionContext()
        _context_instances[context.session_id] = context
        return context
    
    # 获取或创建对应 session 的 context
    if session_id not in _context_instances:
        _context_instances[session_id] = UnifiedExecutionContext(session_id=session_id)
    
    return _context_instances[session_id]


def delete_context(session_id: str) -> None:
    """删除指定 session 的上下文"""
    if session_id in _context_instances:
        del _context_instances[session_id]
        logger.info(f"Context deleted: {session_id}")


def clear_all_contexts() -> None:
    """清空所有上下文（用于测试）"""
    _context_instances.clear()
    logger.info("All contexts cleared")
