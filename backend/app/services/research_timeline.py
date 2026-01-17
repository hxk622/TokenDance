"""
Research Timeline Service - 研究时光长廊

管理深度研究过程中的截图和时间轴记录，用于：
- 存储关键页面截图
- 记录研究轨迹
- 支持研究过程回溯
- 生成可视化时间线

存储方式：
- 本地存储: /tmp/tokendance/research/{session_id}/
- MinIO (可选): 生产环境对象存储
"""
import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# 默认存储路径
DEFAULT_STORAGE_PATH = "/tmp/tokendance/research"


@dataclass
class TimelineEntry:
    """时间轴条目"""
    timestamp: datetime
    event_type: str  # "search", "read", "screenshot", "finding", "milestone"
    title: str
    description: str
    url: str | None = None
    screenshot_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "screenshot_path": self.screenshot_path,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TimelineEntry":
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=data["event_type"],
            title=data["title"],
            description=data["description"],
            url=data.get("url"),
            screenshot_path=data.get("screenshot_path"),
            metadata=data.get("metadata", {})
        )


@dataclass
class ResearchTimeline:
    """研究时间轴"""
    session_id: str
    topic: str
    created_at: datetime = field(default_factory=datetime.now)
    entries: list[TimelineEntry] = field(default_factory=list)

    def add_entry(self, entry: TimelineEntry) -> None:
        self.entries.append(entry)
        self.entries.sort(key=lambda e: e.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "created_at": self.created_at.isoformat(),
            "entries": [e.to_dict() for e in self.entries]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchTimeline":
        timeline = cls(
            session_id=data["session_id"],
            topic=data["topic"],
            created_at=datetime.fromisoformat(data["created_at"])
        )
        timeline.entries = [TimelineEntry.from_dict(e) for e in data.get("entries", [])]
        return timeline


class ResearchTimelineService:
    """研究时光长廊服务

    管理研究过程的截图和时间轴记录。

    使用示例:
        service = ResearchTimelineService(session_id="research_123")

        # 记录搜索事件
        service.log_search("Rust async programming", 5)

        # 存储截图
        path = await service.save_screenshot(screenshot_bytes, "arxiv_paper")

        # 记录发现
        service.log_finding("Key finding about async/await")

        # 获取时间轴
        timeline = service.get_timeline()
    """

    def __init__(
        self,
        session_id: str,
        topic: str = "Research",
        storage_path: str = DEFAULT_STORAGE_PATH
    ):
        self.session_id = session_id
        self.topic = topic
        self.storage_path = Path(storage_path) / session_id

        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.screenshots_path = self.storage_path / "screenshots"
        self.screenshots_path.mkdir(exist_ok=True)

        # 加载或创建时间轴
        self.timeline = self._load_or_create_timeline()

        logger.info(f"ResearchTimelineService initialized: {session_id}")

    def _load_or_create_timeline(self) -> ResearchTimeline:
        """加载或创建时间轴"""
        timeline_file = self.storage_path / "timeline.json"

        if timeline_file.exists():
            try:
                with open(timeline_file, encoding="utf-8") as f:
                    data = json.load(f)
                return ResearchTimeline.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load timeline: {e}")

        return ResearchTimeline(
            session_id=self.session_id,
            topic=self.topic
        )

    def _save_timeline(self) -> None:
        """保存时间轴到文件"""
        timeline_file = self.storage_path / "timeline.json"
        try:
            with open(timeline_file, "w", encoding="utf-8") as f:
                json.dump(self.timeline.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save timeline: {e}")

    # ==================== 事件记录方法 ====================

    def log_search(self, query: str, results_count: int) -> TimelineEntry:
        """记录搜索事件"""
        entry = TimelineEntry(
            timestamp=datetime.now(),
            event_type="search",
            title=f"Search: {query[:50]}",
            description=f"Searched for '{query}' and found {results_count} results",
            metadata={"query": query, "results_count": results_count}
        )
        self.timeline.add_entry(entry)
        self._save_timeline()
        logger.debug(f"Logged search: {query}")
        return entry

    def log_read(self, url: str, title: str) -> TimelineEntry:
        """记录阅读事件"""
        entry = TimelineEntry(
            timestamp=datetime.now(),
            event_type="read",
            title=f"Read: {title[:50]}",
            description=f"Read content from {url}",
            url=url,
            metadata={"title": title}
        )
        self.timeline.add_entry(entry)
        self._save_timeline()
        logger.debug(f"Logged read: {url}")
        return entry

    def log_finding(self, finding: str, source_url: str | None = None) -> TimelineEntry:
        """记录发现"""
        entry = TimelineEntry(
            timestamp=datetime.now(),
            event_type="finding",
            title=f"Finding: {finding[:50]}",
            description=finding,
            url=source_url,
            metadata={}
        )
        self.timeline.add_entry(entry)
        self._save_timeline()
        logger.debug(f"Logged finding: {finding[:50]}")
        return entry

    def log_milestone(self, milestone: str, description: str = "") -> TimelineEntry:
        """记录里程碑"""
        entry = TimelineEntry(
            timestamp=datetime.now(),
            event_type="milestone",
            title=milestone,
            description=description,
            metadata={}
        )
        self.timeline.add_entry(entry)
        self._save_timeline()
        logger.debug(f"Logged milestone: {milestone}")
        return entry

    # ==================== 截图管理方法 ====================

    async def save_screenshot(
        self,
        screenshot_data: bytes,
        name: str,
        url: str | None = None,
        metadata: dict | None = None
    ) -> str:
        """保存截图

        Args:
            screenshot_data: 截图二进制数据
            name: 截图名称
            url: 相关 URL
            metadata: 额外元数据

        Returns:
            str: 截图存储路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{name}.png"
        filepath = self.screenshots_path / filename

        try:
            with open(filepath, "wb") as f:
                f.write(screenshot_data)

            # 记录截图事件
            entry = TimelineEntry(
                timestamp=datetime.now(),
                event_type="screenshot",
                title=f"Screenshot: {name}",
                description=f"Captured screenshot of {name}",
                url=url,
                screenshot_path=str(filepath),
                metadata=metadata or {}
            )
            self.timeline.add_entry(entry)
            self._save_timeline()

            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            raise

    def get_screenshot_path(self, index: int) -> str | None:
        """获取指定索引的截图路径"""
        screenshots = [e for e in self.timeline.entries if e.event_type == "screenshot"]
        if 0 <= index < len(screenshots):
            return screenshots[index].screenshot_path
        return None

    def list_screenshots(self) -> list[dict[str, Any]]:
        """列出所有截图"""
        screenshots = []
        for entry in self.timeline.entries:
            if entry.event_type == "screenshot" and entry.screenshot_path:
                screenshots.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "name": entry.title,
                    "path": entry.screenshot_path,
                    "url": entry.url
                })
        return screenshots

    # ==================== 时间轴查询方法 ====================

    def get_timeline(self) -> ResearchTimeline:
        """获取完整时间轴"""
        return self.timeline

    def get_entries_by_type(self, event_type: str) -> list[TimelineEntry]:
        """按类型获取条目"""
        return [e for e in self.timeline.entries if e.event_type == event_type]

    def get_recent_entries(self, count: int = 10) -> list[TimelineEntry]:
        """获取最近的条目"""
        return self.timeline.entries[-count:]

    def to_markdown(self) -> str:
        """导出为 Markdown 格式"""
        md = f"# Research Timeline: {self.topic}\n\n"
        md += f"**Session**: {self.session_id}  \n"
        md += f"**Created**: {self.timeline.created_at.strftime('%Y-%m-%d %H:%M')}  \n"
        md += f"**Events**: {len(self.timeline.entries)}\n\n"
        md += "---\n\n"

        for entry in self.timeline.entries:
            time_str = entry.timestamp.strftime("%H:%M:%S")
            icon = {
                "search": "🔍",
                "read": "📖",
                "screenshot": "📸",
                "finding": "💡",
                "milestone": "🎯"
            }.get(entry.event_type, "📌")

            md += f"### {icon} {time_str} - {entry.title}\n\n"
            md += f"{entry.description}\n\n"
            if entry.url:
                md += f"**URL**: {entry.url}\n\n"
            if entry.screenshot_path:
                md += f"**Screenshot**: `{entry.screenshot_path}`\n\n"
            md += "---\n\n"

        return md

    # ==================== 清理方法 ====================

    def cleanup(self) -> None:
        """清理存储"""
        try:
            if self.storage_path.exists():
                shutil.rmtree(self.storage_path)
                logger.info(f"Cleaned up research timeline: {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup: {e}")


# ==================== 工厂函数 ====================

def create_research_timeline_service(
    session_id: str,
    topic: str = "Research"
) -> ResearchTimelineService:
    """创建研究时间轴服务"""
    return ResearchTimelineService(session_id=session_id, topic=topic)
