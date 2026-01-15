"""
TimeLapseLogger 单元测试
"""

import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path

from app.services.time_lapse import (
    TimeLapseLogger,
    TimeLapseFrame,
    TimeLapseSession,
    FrameType,
    get_timelapse_logger,
)


@pytest.fixture
def temp_storage_dir():
    """创建临时存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def logger(temp_storage_dir):
    """创建测试用 Logger"""
    return TimeLapseLogger(
        storage_dir=temp_storage_dir,
        max_frames_per_session=10,
    )


class TestTimeLapseLogger:
    """TimeLapseLogger 测试"""
    
    def test_create_session(self, logger):
        """测试创建会话"""
        session_id = logger.create_session(
            task_id="task-123",
            title="测试研究任务",
        )
        
        assert session_id is not None
        assert len(session_id) == 36  # UUID 长度
        
        # 验证会话存在
        session = logger.get_session(session_id)
        assert session is not None
        assert session.task_id == "task-123"
        assert session.title == "测试研究任务"
        assert len(session.frames) == 0
    
    @pytest.mark.asyncio
    async def test_log_frame(self, logger):
        """测试记录关键帧"""
        session_id = logger.create_session(task_id="task-123")
        
        frame = await logger.log_frame(
            session_id=session_id,
            frame_type=FrameType.PAGE_LOAD,
            title="打开测试页面",
            description="加载 https://example.com",
            url="https://example.com",
            action="browser_open",
        )
        
        assert frame is not None
        assert frame.title == "打开测试页面"
        assert frame.frame_type == FrameType.PAGE_LOAD
        
        # 验证帧已添加到会话
        session = logger.get_session(session_id)
        assert len(session.frames) == 1
    
    @pytest.mark.asyncio
    async def test_log_page_load(self, logger):
        """测试便捷方法：记录页面加载"""
        session_id = logger.create_session(task_id="task-123")
        
        frame = await logger.log_page_load(
            session_id=session_id,
            url="https://xiaohongshu.com",
            title="小红书搜索页",
        )
        
        assert frame is not None
        assert frame.frame_type == FrameType.PAGE_LOAD
        assert "打开:" in frame.title
    
    @pytest.mark.asyncio
    async def test_log_interaction(self, logger):
        """测试便捷方法：记录交互操作"""
        session_id = logger.create_session(task_id="task-123")
        
        frame = await logger.log_interaction(
            session_id=session_id,
            action="browser_click",
            target="搜索按钮",
        )
        
        assert frame is not None
        assert frame.frame_type == FrameType.INTERACTION
        assert "点击:" in frame.title
    
    @pytest.mark.asyncio
    async def test_log_error(self, logger):
        """测试便捷方法：记录错误"""
        session_id = logger.create_session(task_id="task-123")
        
        frame = await logger.log_error(
            session_id=session_id,
            error_type="ElementNotFound",
            error_message="找不到元素 @e99",
        )
        
        assert frame is not None
        assert frame.frame_type == FrameType.ERROR
        assert "错误:" in frame.title
    
    @pytest.mark.asyncio
    async def test_log_milestone(self, logger):
        """测试便捷方法：记录里程碑"""
        session_id = logger.create_session(task_id="task-123")
        
        frame = await logger.log_milestone(
            session_id=session_id,
            milestone_name="搜索完成",
            description="完成第一阶段搜索",
        )
        
        assert frame is not None
        assert frame.frame_type == FrameType.MILESTONE
        assert "✓" in frame.title
    
    @pytest.mark.asyncio
    async def test_snapshot_summary(self, logger):
        """测试 Snapshot 摘要功能"""
        session_id = logger.create_session(task_id="task-123")
        
        # 模拟一个长 snapshot
        long_snapshot = "\n".join([
            f"@e{i} [元素{i}] type=button"
            for i in range(100)
        ])
        
        frame = await logger.log_frame(
            session_id=session_id,
            frame_type=FrameType.PAGE_LOAD,
            title="测试",
            description="测试 snapshot 摘要",
            snapshot_content=long_snapshot,
        )
        
        assert frame is not None
        assert frame.snapshot_summary is not None
        assert len(frame.snapshot_summary) <= 500 + 3  # +3 for "..."
    
    @pytest.mark.asyncio
    async def test_max_frames_limit(self, logger):
        """测试帧数限制"""
        session_id = logger.create_session(task_id="task-123")
        
        # 记录超过限制的帧
        for i in range(15):
            await logger.log_frame(
                session_id=session_id,
                frame_type=FrameType.INTERACTION,
                title=f"操作 {i}",
                description=f"测试操作 {i}",
            )
        
        session = logger.get_session(session_id)
        # 应该只保留 max_frames_per_session 个帧
        assert len(session.frames) <= logger.max_frames_per_session
    
    @pytest.mark.asyncio
    async def test_milestone_preserved(self, logger):
        """测试里程碑帧在清理时被保留"""
        session_id = logger.create_session(task_id="task-123")
        
        # 先记录一个里程碑
        await logger.log_milestone(
            session_id=session_id,
            milestone_name="重要里程碑",
            description="这个帧应该被保留",
        )
        
        # 然后记录很多普通帧
        for i in range(15):
            await logger.log_frame(
                session_id=session_id,
                frame_type=FrameType.INTERACTION,
                title=f"操作 {i}",
                description=f"测试操作 {i}",
            )
        
        session = logger.get_session(session_id)
        # 里程碑帧应该仍然存在
        milestone_frames = [
            f for f in session.frames
            if f.frame_type == FrameType.MILESTONE
        ]
        assert len(milestone_frames) >= 1
    
    def test_get_session_summary(self, logger):
        """测试获取会话摘要"""
        session_id = logger.create_session(
            task_id="task-123",
            title="测试任务",
        )
        
        summary = logger.get_session_summary(session_id)
        
        assert summary is not None
        assert summary["session_id"] == session_id
        assert summary["task_id"] == "task-123"
        assert summary["frame_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_playback_data(self, logger):
        """测试获取回放数据"""
        session_id = logger.create_session(
            task_id="task-123",
            title="测试任务",
        )
        
        # 添加一些帧
        await logger.log_page_load(
            session_id=session_id,
            url="https://example.com",
            title="Example",
        )
        await logger.log_interaction(
            session_id=session_id,
            action="browser_click",
            target="按钮",
        )
        
        playback = logger.get_playback_data(session_id)
        
        assert playback is not None
        assert playback["session_id"] == session_id
        assert len(playback["frames"]) == 2
        
        # 验证帧数据结构
        frame = playback["frames"][0]
        assert "id" in frame
        assert "type" in frame
        assert "timestamp_ms" in frame
        assert "title" in frame
    
    @pytest.mark.asyncio
    async def test_close_session(self, logger, temp_storage_dir):
        """测试关闭会话"""
        session_id = logger.create_session(
            task_id="task-123",
            title="测试任务",
        )
        
        await logger.log_page_load(
            session_id=session_id,
            url="https://example.com",
            title="Example",
        )
        
        # 关闭会话
        result = await logger.close_session(session_id)
        
        assert result is not None
        assert result["session_id"] == session_id
        
        # 会话应该被移除
        assert logger.get_session(session_id) is None
        
        # 验证持久化文件存在
        session_file = Path(temp_storage_dir) / session_id / "session.json"
        assert session_file.exists()
    
    @pytest.mark.asyncio
    async def test_load_session(self, logger, temp_storage_dir):
        """测试加载会话"""
        # 创建并关闭会话
        session_id = logger.create_session(
            task_id="task-123",
            title="测试任务",
        )
        await logger.log_page_load(
            session_id=session_id,
            url="https://example.com",
            title="Example",
        )
        await logger.close_session(session_id)
        
        # 重新加载
        loaded_session = await logger.load_session(session_id)
        
        assert loaded_session is not None
        assert loaded_session.task_id == "task-123"
        assert loaded_session.title == "测试任务"
        assert len(loaded_session.frames) == 1
    
    @pytest.mark.asyncio
    async def test_log_frame_nonexistent_session(self, logger):
        """测试向不存在的会话记录帧"""
        frame = await logger.log_frame(
            session_id="nonexistent",
            frame_type=FrameType.PAGE_LOAD,
            title="测试",
            description="测试",
        )
        
        assert frame is None


class TestTimeLapseFrame:
    """TimeLapseFrame 测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        from datetime import datetime
        
        frame = TimeLapseFrame(
            id="frame-123",
            session_id="session-123",
            frame_type=FrameType.PAGE_LOAD,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            title="测试帧",
            description="测试描述",
            url="https://example.com",
        )
        
        data = frame.to_dict()
        
        assert data["id"] == "frame-123"
        assert data["frame_type"] == "page_load"
        assert data["title"] == "测试帧"
    
    def test_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "frame-123",
            "session_id": "session-123",
            "frame_type": "interaction",
            "timestamp": "2024-01-15T10:00:00",
            "title": "测试帧",
            "description": "测试描述",
            "url": "https://example.com",
        }
        
        frame = TimeLapseFrame.from_dict(data)
        
        assert frame.id == "frame-123"
        assert frame.frame_type == FrameType.INTERACTION
        assert frame.title == "测试帧"


class TestTimeLapseSession:
    """TimeLapseSession 测试"""
    
    def test_add_frame(self):
        """测试添加帧"""
        from datetime import datetime
        
        session = TimeLapseSession(
            session_id="session-123",
            task_id="task-123",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )
        
        frame = TimeLapseFrame(
            id="frame-1",
            session_id="session-123",
            frame_type=FrameType.PAGE_LOAD,
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            title="测试",
            description="测试",
        )
        
        session.add_frame(frame)
        
        assert len(session.frames) == 1
    
    def test_duration_calculation(self):
        """测试持续时间计算"""
        from datetime import datetime
        
        session = TimeLapseSession(
            session_id="session-123",
            task_id="task-123",
            created_at=datetime(2024, 1, 15, 10, 0, 0),
        )
        
        # 添加第一帧
        frame1 = TimeLapseFrame(
            id="frame-1",
            session_id="session-123",
            frame_type=FrameType.PAGE_LOAD,
            timestamp=datetime(2024, 1, 15, 10, 0, 0),
            title="帧1",
            description="帧1",
        )
        session.add_frame(frame1)
        
        # 添加第二帧（5秒后）
        frame2 = TimeLapseFrame(
            id="frame-2",
            session_id="session-123",
            frame_type=FrameType.INTERACTION,
            timestamp=datetime(2024, 1, 15, 10, 0, 5),
            title="帧2",
            description="帧2",
        )
        session.add_frame(frame2)
        
        # 持续时间应该是 5000ms
        assert session.total_duration_ms == 5000
    
    def test_get_summary(self):
        """测试获取摘要"""
        from datetime import datetime
        
        session = TimeLapseSession(
            session_id="session-123",
            task_id="task-123",
            created_at=datetime.now(),
            title="测试会话",
        )
        
        summary = session.get_summary()
        
        assert summary["session_id"] == "session-123"
        assert summary["title"] == "测试会话"
        assert summary["frame_count"] == 0
