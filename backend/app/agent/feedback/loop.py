"""
Feedback Loop - 用户反馈学习回路（占位实现）

提供基础 API：记录反馈、按类型更新后续策略（当前仅写入 learnings.md）。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
from datetime import datetime

from app.filesystem.agent_fs import AgentFileSystem


FeedbackType = Literal["misunderstanding", "wrong_tool", "incomplete", "other"]


@dataclass
class UserFeedback:
    feedback_type: FeedbackType
    message: str
    created_at: str


class FeedbackLoop:
    def __init__(self, fs: AgentFileSystem):
        self.fs = fs

    def record(self, feedback: UserFeedback) -> None:
        """将反馈以一条 Lesson 的形式写入 learnings.md"""
        from app.agent.memory.distributed import Lesson, DistributedMemory

        dm = DistributedMemory(self.fs)
        dm.store_lessons([
            Lesson(
                title=f"User Feedback ({feedback.feedback_type})",
                summary=feedback.message,
                tags=["feedback", feedback.feedback_type],
                created_at=feedback.created_at or (datetime.utcnow().isoformat() + "Z"),
            )
        ])
