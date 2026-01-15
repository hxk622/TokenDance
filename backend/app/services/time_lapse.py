"""
TimeLapse Logger Service

记录研究过程的关键帧，用于：
- 研究过程可视化回溯
- 调试与问题排查
- 用户透明度（展示 Agent 做了什么）

基于 "关键帧 + 文字描述" 的轻量级方案，
而非连续视频流，以平衡用户体验和资源消耗。
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


class FrameType(Enum):
    """关键帧类型"""
    PAGE_LOAD = "page_load"        # 页面加载完成
    INTERACTION = "interaction"    # 用户交互（点击、填写等）
    CONTENT_EXTRACT = "extract"    # 内容提取
    ERROR = "error"                # 错误状态
    SEARCH_RESULT = "search"       # 搜索结果
    MILESTONE = "milestone"        # 里程碑（阶段完成）


@dataclass
class TimeLapseFrame:
    """单个关键帧"""
    id: str
    session_id: str
    frame_type: FrameType
    timestamp: datetime
    
    # 描述信息
    title: str                              # 简短标题
    description: str                        # 详细描述
    
    # 视觉数据（可选）
    screenshot_path: Optional[str] = None   # 截图路径
    snapshot_summary: Optional[str] = None  # Snapshot 摘要（非完整内容）
    
    # 上下文
    url: Optional[str] = None
    action: Optional[str] = None            # 执行的动作
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "frame_type": self.frame_type.value,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "description": self.description,
            "screenshot_path": self.screenshot_path,
            "snapshot_summary": self.snapshot_summary,
            "url": self.url,
            "action": self.action,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeLapseFrame":
        """从字典创建"""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            frame_type=FrameType(data["frame_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            title=data["title"],
            description=data["description"],
            screenshot_path=data.get("screenshot_path"),
            snapshot_summary=data.get("snapshot_summary"),
            url=data.get("url"),
            action=data.get("action"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TimeLapseSession:
    """TimeLapse 会话，对应一个研究任务"""
    session_id: str
    task_id: str
    created_at: datetime
    frames: List[TimeLapseFrame] = field(default_factory=list)
    
    # 元数据
    title: str = ""
    total_duration_ms: int = 0
    
    def add_frame(self, frame: TimeLapseFrame) -> None:
        """添加关键帧"""
        self.frames.append(frame)
        if len(self.frames) > 1:
            self.total_duration_ms = int(
                (frame.timestamp - self.created_at).total_seconds() * 1000
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat(),
            "title": self.title,
            "total_duration_ms": self.total_duration_ms,
            "frame_count": len(self.frames),
            "frames": [f.to_dict() for f in self.frames],
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要（不含完整帧数据）"""
        return {
            "session_id": self.session_id,
            "task_id": self.task_id,
            "created_at": self.created_at.isoformat(),
            "title": self.title,
            "total_duration_ms": self.total_duration_ms,
            "frame_count": len(self.frames),
            "frame_types": {
                ft.value: sum(1 for f in self.frames if f.frame_type == ft)
                for ft in FrameType
                if any(f.frame_type == ft for f in self.frames)
            },
        }


class TimeLapseLogger:
    """
    TimeLapse 日志记录器
    
    负责记录研究过程的关键帧，支持：
    - 自动截图
    - Snapshot 摘要
    - 持久化存储
    - 回放数据生成
    """
    
    def __init__(
        self,
        storage_dir: str = "/tmp/tokendance/timelapse",
        max_frames_per_session: int = 100,
        auto_screenshot: bool = True,
    ):
        self.storage_dir = Path(storage_dir)
        self.max_frames_per_session = max_frames_per_session
        self.auto_screenshot = auto_screenshot
        
        # 内存中的活跃会话
        self._sessions: Dict[str, TimeLapseSession] = {}
        
        # 确保存储目录存在
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def create_session(
        self,
        task_id: str,
        title: str = "",
    ) -> str:
        """
        创建新的 TimeLapse 会话
        
        Args:
            task_id: 关联的任务 ID
            title: 会话标题
            
        Returns:
            session_id: 会话 ID
        """
        session_id = str(uuid4())
        session = TimeLapseSession(
            session_id=session_id,
            task_id=task_id,
            created_at=datetime.now(),
            title=title,
        )
        self._sessions[session_id] = session
        
        # 创建会话存储目录
        session_dir = self.storage_dir / session_id
        session_dir.mkdir(exist_ok=True)
        (session_dir / "screenshots").mkdir(exist_ok=True)
        
        return session_id
    
    async def log_frame(
        self,
        session_id: str,
        frame_type: FrameType,
        title: str,
        description: str,
        url: Optional[str] = None,
        action: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        snapshot_content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[TimeLapseFrame]:
        """
        记录一个关键帧
        
        Args:
            session_id: 会话 ID
            frame_type: 帧类型
            title: 简短标题
            description: 详细描述
            url: 当前 URL
            action: 执行的动作
            screenshot_path: 截图路径（已存在）
            snapshot_content: Snapshot 完整内容（会被摘要）
            metadata: 附加元数据
            
        Returns:
            记录的关键帧，如果会话不存在返回 None
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # 检查帧数限制
        if len(session.frames) >= self.max_frames_per_session:
            # 删除最早的非里程碑帧
            for i, f in enumerate(session.frames):
                if f.frame_type != FrameType.MILESTONE:
                    session.frames.pop(i)
                    break
        
        # 生成 Snapshot 摘要（只保留前 500 字符）
        snapshot_summary = None
        if snapshot_content:
            snapshot_summary = self._summarize_snapshot(snapshot_content)
        
        frame = TimeLapseFrame(
            id=str(uuid4()),
            session_id=session_id,
            frame_type=frame_type,
            timestamp=datetime.now(),
            title=title,
            description=description,
            screenshot_path=screenshot_path,
            snapshot_summary=snapshot_summary,
            url=url,
            action=action,
            metadata=metadata or {},
        )
        
        session.add_frame(frame)
        
        # 异步持久化（不阻塞主流程）
        asyncio.create_task(self._persist_frame(session_id, frame))
        
        return frame
    
    def _summarize_snapshot(self, content: str, max_length: int = 500) -> str:
        """
        摘要 Snapshot 内容
        
        只保留关键信息，避免 Context 膨胀
        """
        if len(content) <= max_length:
            return content
        
        # 提取交互元素（@e1, @e2 等）
        lines = content.split('\n')
        interactive_lines = [
            line for line in lines
            if '@e' in line or line.startswith('-')
        ]
        
        summary = '\n'.join(interactive_lines[:20])  # 最多 20 行
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary
    
    async def _persist_frame(
        self,
        session_id: str,
        frame: TimeLapseFrame,
    ) -> None:
        """异步持久化帧数据"""
        session_dir = self.storage_dir / session_id
        frames_file = session_dir / "frames.jsonl"
        
        try:
            async with asyncio.Lock():
                with open(frames_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(frame.to_dict(), ensure_ascii=False) + "\n")
        except Exception as e:
            # 持久化失败不影响主流程
            print(f"TimeLapse persist error: {e}")
    
    async def log_page_load(
        self,
        session_id: str,
        url: str,
        title: str,
        screenshot_path: Optional[str] = None,
    ) -> Optional[TimeLapseFrame]:
        """便捷方法：记录页面加载"""
        return await self.log_frame(
            session_id=session_id,
            frame_type=FrameType.PAGE_LOAD,
            title=f"打开: {title[:30]}",
            description=f"加载页面 {url}",
            url=url,
            action="browser_open",
            screenshot_path=screenshot_path,
        )
    
    async def log_interaction(
        self,
        session_id: str,
        action: str,
        target: str,
        url: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> Optional[TimeLapseFrame]:
        """便捷方法：记录交互操作"""
        action_names = {
            "browser_click": "点击",
            "browser_fill": "填写",
            "browser_scroll": "滚动",
        }
        action_name = action_names.get(action, action)
        
        return await self.log_frame(
            session_id=session_id,
            frame_type=FrameType.INTERACTION,
            title=f"{action_name}: {target[:30]}",
            description=f"执行 {action} 操作，目标: {target}",
            url=url,
            action=action,
            screenshot_path=screenshot_path,
        )
    
    async def log_content_extract(
        self,
        session_id: str,
        content_title: str,
        source_url: str,
        extracted_length: int,
        snapshot_content: Optional[str] = None,
    ) -> Optional[TimeLapseFrame]:
        """便捷方法：记录内容提取"""
        return await self.log_frame(
            session_id=session_id,
            frame_type=FrameType.CONTENT_EXTRACT,
            title=f"提取: {content_title[:30]}",
            description=f"从 {source_url} 提取了 {extracted_length} 字符内容",
            url=source_url,
            action="extract",
            snapshot_content=snapshot_content,
            metadata={"extracted_length": extracted_length},
        )
    
    async def log_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        url: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> Optional[TimeLapseFrame]:
        """便捷方法：记录错误"""
        return await self.log_frame(
            session_id=session_id,
            frame_type=FrameType.ERROR,
            title=f"错误: {error_type}",
            description=error_message,
            url=url,
            screenshot_path=screenshot_path,
            metadata={"error_type": error_type},
        )
    
    async def log_milestone(
        self,
        session_id: str,
        milestone_name: str,
        description: str,
        screenshot_path: Optional[str] = None,
    ) -> Optional[TimeLapseFrame]:
        """便捷方法：记录里程碑"""
        return await self.log_frame(
            session_id=session_id,
            frame_type=FrameType.MILESTONE,
            title=f"✓ {milestone_name}",
            description=description,
            screenshot_path=screenshot_path,
        )
    
    def get_session(self, session_id: str) -> Optional[TimeLapseSession]:
        """获取会话"""
        return self._sessions.get(session_id)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        session = self._sessions.get(session_id)
        if session:
            return session.get_summary()
        return None
    
    def get_playback_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取回放数据
        
        返回适合前端展示的数据结构
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "title": session.title,
            "total_duration_ms": session.total_duration_ms,
            "frames": [
                {
                    "id": f.id,
                    "type": f.frame_type.value,
                    "timestamp_ms": int(
                        (f.timestamp - session.created_at).total_seconds() * 1000
                    ),
                    "title": f.title,
                    "description": f.description,
                    "screenshot_path": f.screenshot_path,
                    "url": f.url,
                }
                for f in session.frames
            ],
        }
    
    async def close_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        关闭会话并返回完整数据
        
        Returns:
            会话完整数据，如果会话不存在返回 None
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        # 持久化完整会话数据
        session_dir = self.storage_dir / session_id
        session_file = session_dir / "session.json"
        
        session_data = session.to_dict()
        
        try:
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"TimeLapse session save error: {e}")
        
        # 从内存中移除
        del self._sessions[session_id]
        
        return session_data
    
    async def load_session(self, session_id: str) -> Optional[TimeLapseSession]:
        """
        从持久化存储加载会话
        
        用于历史回放
        """
        session_dir = self.storage_dir / session_id
        session_file = session_dir / "session.json"
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            session = TimeLapseSession(
                session_id=data["session_id"],
                task_id=data["task_id"],
                created_at=datetime.fromisoformat(data["created_at"]),
                title=data.get("title", ""),
            )
            
            for frame_data in data.get("frames", []):
                session.frames.append(TimeLapseFrame.from_dict(frame_data))
            
            session.total_duration_ms = data.get("total_duration_ms", 0)
            
            return session
            
        except Exception as e:
            print(f"TimeLapse session load error: {e}")
            return None


# 全局单例
_timelapse_logger: Optional[TimeLapseLogger] = None


def get_timelapse_logger() -> TimeLapseLogger:
    """获取 TimeLapse Logger 单例"""
    global _timelapse_logger
    if _timelapse_logger is None:
        _timelapse_logger = TimeLapseLogger()
    return _timelapse_logger
