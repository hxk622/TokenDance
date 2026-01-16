"""
WorkState Manager - 工作状态管理器

实现铁律五 PolicyLayer 的第一个组件：WorkState

WorkState 管理：
- 当前任务状态
- 上下文信息
- 资源使用情况
- 任务进度追踪

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class TaskPhase(Enum):
    """任务阶段"""
    INIT = "init"              # 初始化
    PLANNING = "planning"      # 规划中
    EXECUTING = "executing"    # 执行中
    REVIEWING = "reviewing"    # 复审中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    PAUSED = "paused"          # 暂停


@dataclass
class TaskContext:
    """任务上下文"""
    task_id: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 任务元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 相关文件
    related_files: List[str] = field(default_factory=list)
    
    # 依赖任务
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ResourceUsage:
    """资源使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    tool_calls: int = 0
    llm_calls: int = 0
    elapsed_time_seconds: float = 0.0
    
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens(),
            "tool_calls": self.tool_calls,
            "llm_calls": self.llm_calls,
            "elapsed_time_seconds": self.elapsed_time_seconds,
        }


@dataclass
class ProgressCheckpoint:
    """进度检查点"""
    name: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: str = ""


@dataclass
class WorkState:
    """工作状态
    
    存储 Agent 当前的工作状态，用于：
    1. 状态恢复（如果 Agent 被中断）
    2. 进度追踪
    3. 资源监控
    """
    
    # 会话信息
    session_id: str
    workspace_id: str
    
    # 任务阶段
    phase: TaskPhase = TaskPhase.INIT
    
    # 任务上下文
    current_task: Optional[TaskContext] = None
    
    # 资源使用
    resource_usage: ResourceUsage = field(default_factory=ResourceUsage)
    
    # 进度检查点
    checkpoints: List[ProgressCheckpoint] = field(default_factory=list)
    
    # 当前目标（来自 task_plan.md）
    current_goal: str = ""
    
    # 当前步骤（来自 TODO 列表）
    current_step: int = 0
    total_steps: int = 0
    
    # 工作目录
    working_directory: str = ""
    
    # 时间戳
    started_at: datetime = field(default_factory=datetime.now)
    last_activity_at: datetime = field(default_factory=datetime.now)
    
    def update_activity(self) -> None:
        """更新最后活动时间"""
        self.last_activity_at = datetime.now()
    
    def set_phase(self, phase: TaskPhase) -> None:
        """设置任务阶段"""
        self.phase = phase
        self.update_activity()
    
    def add_checkpoint(self, name: str, notes: str = "") -> ProgressCheckpoint:
        """添加进度检查点"""
        checkpoint = ProgressCheckpoint(name=name, notes=notes)
        self.checkpoints.append(checkpoint)
        return checkpoint
    
    def complete_checkpoint(self, name: str) -> bool:
        """完成检查点"""
        for cp in self.checkpoints:
            if cp.name == name and not cp.completed:
                cp.completed = True
                cp.completed_at = datetime.now()
                self.update_activity()
                return True
        return False
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_steps == 0:
            return 0.0
        return (self.current_step / self.total_steps) * 100
    
    def get_completed_checkpoints(self) -> List[ProgressCheckpoint]:
        """获取已完成的检查点"""
        return [cp for cp in self.checkpoints if cp.completed]
    
    def get_pending_checkpoints(self) -> List[ProgressCheckpoint]:
        """获取待完成的检查点"""
        return [cp for cp in self.checkpoints if not cp.completed]
    
    def is_terminal(self) -> bool:
        """检查是否是终止状态"""
        return self.phase in [TaskPhase.COMPLETED, TaskPhase.FAILED]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "phase": self.phase.value,
            "current_task": {
                "task_id": self.current_task.task_id,
                "description": self.current_task.description,
            } if self.current_task else None,
            "resource_usage": self.resource_usage.to_dict(),
            "progress": {
                "current_step": self.current_step,
                "total_steps": self.total_steps,
                "percentage": self.get_progress_percentage(),
            },
            "checkpoints": {
                "total": len(self.checkpoints),
                "completed": len(self.get_completed_checkpoints()),
                "pending": len(self.get_pending_checkpoints()),
            },
            "current_goal": self.current_goal,
            "working_directory": self.working_directory,
            "started_at": self.started_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
        }


class WorkStateManager:
    """工作状态管理器
    
    管理 Agent 的工作状态生命周期
    """
    
    def __init__(self, session_id: str, workspace_id: str):
        self.state = WorkState(
            session_id=session_id,
            workspace_id=workspace_id,
        )
    
    def start_task(self, task_id: str, description: str) -> None:
        """开始任务"""
        self.state.current_task = TaskContext(
            task_id=task_id,
            description=description,
        )
        self.state.set_phase(TaskPhase.PLANNING)
    
    def start_execution(self) -> None:
        """开始执行"""
        self.state.set_phase(TaskPhase.EXECUTING)
    
    def set_goal(self, goal: str) -> None:
        """设置当前目标"""
        self.state.current_goal = goal
        self.state.update_activity()
    
    def set_progress(self, current: int, total: int) -> None:
        """设置进度"""
        self.state.current_step = current
        self.state.total_steps = total
        self.state.update_activity()
    
    def add_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """添加 token 使用量"""
        self.state.resource_usage.input_tokens += input_tokens
        self.state.resource_usage.output_tokens += output_tokens
        self.state.resource_usage.llm_calls += 1
    
    def add_tool_call(self) -> None:
        """添加工具调用计数"""
        self.state.resource_usage.tool_calls += 1
    
    def complete_task(self) -> None:
        """完成任务"""
        self.state.set_phase(TaskPhase.COMPLETED)
        if self.state.current_task:
            self.state.current_task.updated_at = datetime.now()
    
    def fail_task(self, reason: str = "") -> None:
        """任务失败"""
        self.state.set_phase(TaskPhase.FAILED)
        if self.state.current_task:
            self.state.current_task.metadata["failure_reason"] = reason
    
    def pause_task(self) -> None:
        """暂停任务"""
        self.state.set_phase(TaskPhase.PAUSED)
    
    def resume_task(self) -> None:
        """恢复任务"""
        self.state.set_phase(TaskPhase.EXECUTING)
    
    def get_state(self) -> WorkState:
        """获取当前状态"""
        return self.state
    
    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return self.state.to_dict()
    
    def reset(self) -> None:
        """重置状态"""
        session_id = self.state.session_id
        workspace_id = self.state.workspace_id
        self.state = WorkState(
            session_id=session_id,
            workspace_id=workspace_id,
        )
