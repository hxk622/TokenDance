"""
Checkpoint Manager - 检查点管理器

核心功能：
1. 每 N 次迭代自动保存检查点
2. 失败时可回滚到最近检查点
3. 避免重复计算（从检查点恢复后继续）
4. 检查点压缩（只保留最近 K 个）
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

from app.filesystem.agent_fs import AgentFileSystem

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """检查点元信息"""
    checkpoint_id: str
    iteration: int
    timestamp: float
    elapsed_seconds: float
    token_usage: Dict[str, int]
    state: str  # Agent 状态 (REASONING/TOOL_CALLING/etc)
    context_size: int  # Context token 数
    tools_executed: int  # 已执行工具数
    success_rate: float  # 当前成功率 (0-1)


@dataclass
class Checkpoint:
    """
    检查点快照
    
    包含恢复任务所需的所有状态：
    - Context 历史
    - 工具执行记录
    - Plan & Findings & Progress
    - Memory 状态
    """
    metadata: CheckpointMetadata
    context_messages: List[Dict[str, Any]]  # 对话历史
    task_plan: str  # task_plan.md 内容
    findings: str  # findings.md 内容
    progress: str  # progress.md 内容
    failure_history: List[Dict[str, Any]]  # 失败记录
    routing_state: Dict[str, Any] = field(default_factory=dict)  # 路由状态
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典（用于序列化）"""
        return {
            "metadata": asdict(self.metadata),
            "context_messages": self.context_messages,
            "task_plan": self.task_plan,
            "findings": self.findings,
            "progress": self.progress,
            "failure_history": self.failure_history,
            "routing_state": self.routing_state,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Checkpoint:
        """从字典恢复"""
        metadata = CheckpointMetadata(**data["metadata"])
        return cls(
            metadata=metadata,
            context_messages=data["context_messages"],
            task_plan=data["task_plan"],
            findings=data["findings"],
            progress=data["progress"],
            failure_history=data["failure_history"],
            routing_state=data.get("routing_state", {}),
        )


class CheckpointManager:
    """
    检查点管理器
    
    策略：
    - 每 N 次迭代保存一次（默认 N=5）
    - 保留最近 K 个检查点（默认 K=3）
    - 失败时自动回滚到最近可用检查点
    """
    
    CHECKPOINT_DIR = "checkpoints"
    
    def __init__(
        self,
        fs: AgentFileSystem,
        save_interval: int = 5,
        max_checkpoints: int = 3,
    ):
        self.fs = fs
        self.save_interval = save_interval
        self.max_checkpoints = max_checkpoints
        
        # 内存中的检查点列表（按时间降序）
        self._checkpoints: List[Checkpoint] = []
        
        # 确保目录存在
        self._ensure_checkpoint_dir()
    
    def _ensure_checkpoint_dir(self) -> None:
        """确保检查点目录存在"""
        if not self.fs.exists(self.CHECKPOINT_DIR):
            self.fs.mkdir(self.CHECKPOINT_DIR)
    
    def should_save(self, iteration: int) -> bool:
        """判断是否应该保存检查点"""
        return iteration > 0 and iteration % self.save_interval == 0
    
    def save_checkpoint(
        self,
        iteration: int,
        state: str,
        context_messages: List[Dict[str, Any]],
        token_usage: Dict[str, int],
        task_plan: str,
        findings: str,
        progress: str,
        failure_history: List[Dict[str, Any]],
        routing_state: Optional[Dict[str, Any]] = None,
        elapsed_seconds: float = 0.0,
    ) -> str:
        """
        保存检查点
        
        Returns:
            checkpoint_id: 检查点 ID
        """
        checkpoint_id = f"ckpt_{iteration}_{int(time.time())}"
        
        # 计算成功率
        success_count = sum(1 for f in failure_history if not f.get("is_failure", True))
        total = len(failure_history) if failure_history else 1
        success_rate = success_count / total
        
        # 创建检查点
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            iteration=iteration,
            timestamp=time.time(),
            elapsed_seconds=elapsed_seconds,
            token_usage=token_usage,
            state=state,
            context_size=len(context_messages),
            tools_executed=len(failure_history),
            success_rate=success_rate,
        )
        
        checkpoint = Checkpoint(
            metadata=metadata,
            context_messages=context_messages,
            task_plan=task_plan,
            findings=findings,
            progress=progress,
            failure_history=failure_history,
            routing_state=routing_state or {},
        )
        
        # 保存到文件系统
        checkpoint_path = f"{self.CHECKPOINT_DIR}/{checkpoint_id}.json"
        self.fs.write(checkpoint_path, json.dumps(checkpoint.to_dict(), indent=2))
        
        # 添加到内存列表（头部）
        self._checkpoints.insert(0, checkpoint)
        
        # 清理旧检查点
        self._cleanup_old_checkpoints()
        
        logger.info(
            f"Checkpoint saved: {checkpoint_id} "
            f"(iter={iteration}, tokens={token_usage.get('total', 0)}, "
            f"success_rate={success_rate:.2f})"
        )
        
        return checkpoint_id
    
    def _cleanup_old_checkpoints(self) -> None:
        """清理旧检查点（只保留最近 K 个）"""
        if len(self._checkpoints) > self.max_checkpoints:
            to_remove = self._checkpoints[self.max_checkpoints:]
            for ckpt in to_remove:
                checkpoint_path = f"{self.CHECKPOINT_DIR}/{ckpt.metadata.checkpoint_id}.json"
                if self.fs.exists(checkpoint_path):
                    self.fs.delete(checkpoint_path)
                    logger.debug(f"Deleted old checkpoint: {ckpt.metadata.checkpoint_id}")
            
            self._checkpoints = self._checkpoints[:self.max_checkpoints]
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """获取最新检查点"""
        if self._checkpoints:
            return self._checkpoints[0]
        
        # 从文件系统加载
        return self._load_latest_from_fs()
    
    def _load_latest_from_fs(self) -> Optional[Checkpoint]:
        """从文件系统加载最新检查点"""
        if not self.fs.exists(self.CHECKPOINT_DIR):
            return None
        
        # 列出所有检查点文件
        files = [
            f for f in self.fs.list_files(self.CHECKPOINT_DIR)
            if f.endswith(".json")
        ]
        
        if not files:
            return None
        
        # 按时间戳排序（最新在前）
        files.sort(reverse=True)
        
        # 加载最新的
        latest_file = files[0]
        checkpoint_path = f"{self.CHECKPOINT_DIR}/{latest_file}"
        content = self.fs.read(checkpoint_path)
        data = json.loads(content)
        
        checkpoint = Checkpoint.from_dict(data)
        self._checkpoints.insert(0, checkpoint)
        
        return checkpoint
    
    def can_rollback(self) -> bool:
        """检查是否可以回滚"""
        return len(self._checkpoints) > 0 or self._has_checkpoints_in_fs()
    
    def _has_checkpoints_in_fs(self) -> bool:
        """检查文件系统中是否有检查点"""
        if not self.fs.exists(self.CHECKPOINT_DIR):
            return False
        files = self.fs.list_files(self.CHECKPOINT_DIR)
        return any(f.endswith(".json") for f in files)
    
    def rollback_to_latest(self) -> Optional[Checkpoint]:
        """
        回滚到最新检查点
        
        Returns:
            Checkpoint: 最新检查点，如果不存在返回 None
        """
        latest = self.get_latest_checkpoint()
        if latest:
            logger.info(
                f"Rolling back to checkpoint: {latest.metadata.checkpoint_id} "
                f"(iter={latest.metadata.iteration})"
            )
        else:
            logger.warning("No checkpoint available for rollback")
        
        return latest
    
    def list_checkpoints(self) -> List[CheckpointMetadata]:
        """列出所有检查点元信息"""
        return [ckpt.metadata for ckpt in self._checkpoints]
    
    def clear_all(self) -> None:
        """清空所有检查点"""
        for ckpt in self._checkpoints:
            checkpoint_path = f"{self.CHECKPOINT_DIR}/{ckpt.metadata.checkpoint_id}.json"
            if self.fs.exists(checkpoint_path):
                self.fs.delete(checkpoint_path)
        
        self._checkpoints.clear()
        logger.info("All checkpoints cleared")
