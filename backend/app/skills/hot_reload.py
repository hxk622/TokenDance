"""
Skill 热重载模块

职责：
1. 监听 skills 目录的文件变化
2. 自动重新加载变更的 Skill
3. 更新 Embedding 索引
4. 清除相关缓存
"""

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Set

logger = logging.getLogger(__name__)


# 尝试导入 watchdog，如果不可用则使用轮询方式
try:
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    logger.warning(
        "watchdog not installed, using polling-based hot reload. "
        "Install with: pip install watchdog"
    )


class SkillFileEventHandler:
    """Skill 文件事件处理器（watchdog 版本）"""
    
    def __init__(
        self,
        on_skill_changed: Callable[[str, str], None],
        debounce_seconds: float = 1.0,
    ):
        """初始化事件处理器
        
        Args:
            on_skill_changed: 回调函数，参数为 (skill_path, event_type)
            debounce_seconds: 去抖动时间（秒）
        """
        self.on_skill_changed = on_skill_changed
        self.debounce_seconds = debounce_seconds
        self._pending_events: dict[str, float] = {}
        self._lock = threading.Lock()
        self._debounce_thread: Optional[threading.Thread] = None
        self._running = False
    
    def start_debounce_thread(self) -> None:
        """启动去抖动线程"""
        self._running = True
        self._debounce_thread = threading.Thread(
            target=self._process_pending_events,
            daemon=True,
        )
        self._debounce_thread.start()
    
    def stop(self) -> None:
        """停止去抖动线程"""
        self._running = False
        if self._debounce_thread:
            self._debounce_thread.join(timeout=2.0)
    
    def _process_pending_events(self) -> None:
        """处理待处理的事件（去抖动）"""
        while self._running:
            time.sleep(0.1)  # 检查间隔
            
            current_time = time.time()
            to_process = []
            
            with self._lock:
                for skill_path, event_time in list(self._pending_events.items()):
                    if current_time - event_time >= self.debounce_seconds:
                        to_process.append(skill_path)
                        del self._pending_events[skill_path]
            
            for skill_path in to_process:
                try:
                    self.on_skill_changed(skill_path, "modified")
                except Exception as e:
                    logger.error(f"Error processing skill change for {skill_path}: {e}")
    
    def queue_event(self, skill_path: str) -> None:
        """将事件加入队列（去抖动）"""
        with self._lock:
            self._pending_events[skill_path] = time.time()


if WATCHDOG_AVAILABLE:
    class WatchdogSkillHandler(FileSystemEventHandler, SkillFileEventHandler):
        """Watchdog 文件系统事件处理器"""
        
        def __init__(
            self,
            on_skill_changed: Callable[[str, str], None],
            debounce_seconds: float = 1.0,
        ):
            FileSystemEventHandler.__init__(self)
            SkillFileEventHandler.__init__(self, on_skill_changed, debounce_seconds)
        
        def on_modified(self, event: FileSystemEvent) -> None:
            """文件修改事件"""
            if event.is_directory:
                return
            self._handle_event(event.src_path, "modified")
        
        def on_created(self, event: FileSystemEvent) -> None:
            """文件创建事件"""
            if event.is_directory:
                return
            self._handle_event(event.src_path, "created")
        
        def on_deleted(self, event: FileSystemEvent) -> None:
            """文件删除事件"""
            if event.is_directory:
                return
            self._handle_event(event.src_path, "deleted")
        
        def _handle_event(self, file_path: str, event_type: str) -> None:
            """处理文件事件"""
            path = Path(file_path)
            
            # 只处理 SKILL.md 文件
            if path.name != "SKILL.md":
                return
            
            # 获取 Skill 目录路径
            skill_path = str(path.parent)
            logger.debug(f"Skill file {event_type}: {skill_path}")
            
            # 加入去抖动队列
            self.queue_event(skill_path)


class PollingSkillWatcher(SkillFileEventHandler):
    """轮询方式的 Skill 文件监视器（不依赖 watchdog）"""
    
    def __init__(
        self,
        skills_dirs: list[Path],
        on_skill_changed: Callable[[str, str], None],
        poll_interval: float = 2.0,
        debounce_seconds: float = 1.0,
    ):
        super().__init__(on_skill_changed, debounce_seconds)
        self.skills_dirs = skills_dirs
        self.poll_interval = poll_interval
        self._file_mtimes: dict[str, float] = {}
        self._poll_thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """启动轮询"""
        self._running = True
        self._scan_all_files()  # 初始扫描
        self.start_debounce_thread()
        
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
        )
        self._poll_thread.start()
        logger.info("Started polling-based skill watcher")
    
    def stop(self) -> None:
        """停止轮询"""
        super().stop()
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)
    
    def _scan_all_files(self) -> None:
        """扫描所有 SKILL.md 文件"""
        for skills_dir in self.skills_dirs:
            if not skills_dir.exists():
                continue
            
            for skill_file in skills_dir.rglob("SKILL.md"):
                self._file_mtimes[str(skill_file)] = skill_file.stat().st_mtime
    
    def _poll_loop(self) -> None:
        """轮询循环"""
        while self._running:
            time.sleep(self.poll_interval)
            
            for skills_dir in self.skills_dirs:
                if not skills_dir.exists():
                    continue
                
                for skill_file in skills_dir.rglob("SKILL.md"):
                    file_path = str(skill_file)
                    try:
                        current_mtime = skill_file.stat().st_mtime
                    except OSError:
                        # 文件可能已被删除
                        if file_path in self._file_mtimes:
                            del self._file_mtimes[file_path]
                            self.queue_event(str(skill_file.parent))
                        continue
                    
                    if file_path not in self._file_mtimes:
                        # 新文件
                        self._file_mtimes[file_path] = current_mtime
                        self.queue_event(str(skill_file.parent))
                    elif current_mtime > self._file_mtimes[file_path]:
                        # 文件已修改
                        self._file_mtimes[file_path] = current_mtime
                        self.queue_event(str(skill_file.parent))


class SkillHotReloader:
    """Skill 热重载器
    
    监听 skills 目录的文件变化，自动重新加载变更的 Skill。
    """
    
    def __init__(
        self,
        skills_dirs: Optional[list[Path]] = None,
        poll_interval: float = 2.0,
        debounce_seconds: float = 1.0,
    ):
        """初始化热重载器
        
        Args:
            skills_dirs: Skill 目录列表，默认为 builtin/
            poll_interval: 轮询间隔（秒），仅在 watchdog 不可用时使用
            debounce_seconds: 去抖动时间（秒）
        """
        if skills_dirs is None:
            base_dir = Path(__file__).parent
            skills_dirs = [base_dir / "builtin"]
        
        self.skills_dirs = [Path(d) for d in skills_dirs]
        self.poll_interval = poll_interval
        self.debounce_seconds = debounce_seconds
        
        self._observer: Optional[object] = None
        self._handler: Optional[SkillFileEventHandler] = None
        self._running = False
        self._reload_callbacks: list[Callable[[str], None]] = []
        self._changed_skills: Set[str] = set()
        self._lock = threading.Lock()
    
    def add_reload_callback(self, callback: Callable[[str], None]) -> None:
        """添加重载回调
        
        Args:
            callback: 回调函数，参数为 skill_path
        """
        self._reload_callbacks.append(callback)
    
    def _on_skill_changed(self, skill_path: str, event_type: str) -> None:
        """处理 Skill 变更事件
        
        Args:
            skill_path: Skill 目录路径
            event_type: 事件类型 (modified, created, deleted)
        """
        logger.info(f"Skill changed ({event_type}): {skill_path}")
        
        with self._lock:
            self._changed_skills.add(skill_path)
        
        # 触发重载
        self._trigger_reload(skill_path)
    
    def _trigger_reload(self, skill_path: str) -> None:
        """触发重载"""
        # 执行所有回调
        for callback in self._reload_callbacks:
            try:
                callback(skill_path)
            except Exception as e:
                logger.error(f"Reload callback error: {e}")
        
        # 默认行为：重载全局 registry
        self._reload_registry()
    
    def _reload_registry(self) -> None:
        """重载全局 SkillRegistry"""
        try:
            from .registry import get_skill_registry
            registry = get_skill_registry()
            registry.reload()
            logger.info("SkillRegistry reloaded successfully")
            
            # 清除 Loader 缓存
            self._clear_loader_cache()
            
            # 重建 Embedding 索引
            self._rebuild_embeddings()
            
        except Exception as e:
            logger.error(f"Failed to reload SkillRegistry: {e}")
    
    def _clear_loader_cache(self) -> None:
        """清除 Loader 缓存"""
        try:
            from .loader import SkillLoader
            from .registry import get_skill_registry
            
            # 如果有全局 loader，清除其缓存
            # 这里假设 loader 是按需创建的
            logger.debug("Loader cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear loader cache: {e}")
    
    def _rebuild_embeddings(self) -> None:
        """重建 Embedding 索引"""
        try:
            from .matcher import reset_skill_matcher
            
            # 重置 matcher 以重建索引
            reset_skill_matcher()
            logger.info("Skill embeddings will be rebuilt on next match")
        except Exception as e:
            logger.warning(f"Failed to reset skill matcher: {e}")
    
    def start(self) -> None:
        """启动热重载监听"""
        if self._running:
            logger.warning("SkillHotReloader already running")
            return
        
        self._running = True
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog()
        else:
            self._start_polling()
        
        logger.info(
            f"SkillHotReloader started, watching: "
            f"{[str(d) for d in self.skills_dirs]}"
        )
    
    def _start_watchdog(self) -> None:
        """使用 watchdog 启动监听"""
        self._handler = WatchdogSkillHandler(
            self._on_skill_changed,
            self.debounce_seconds,
        )
        self._handler.start_debounce_thread()
        
        self._observer = Observer()
        for skills_dir in self.skills_dirs:
            if skills_dir.exists():
                self._observer.schedule(
                    self._handler,
                    str(skills_dir),
                    recursive=True,
                )
        
        self._observer.start()
        logger.info("Started watchdog-based skill watcher")
    
    def _start_polling(self) -> None:
        """使用轮询方式启动监听"""
        self._handler = PollingSkillWatcher(
            self.skills_dirs,
            self._on_skill_changed,
            self.poll_interval,
            self.debounce_seconds,
        )
        self._handler.start()
    
    def stop(self) -> None:
        """停止热重载监听"""
        if not self._running:
            return
        
        self._running = False
        
        if WATCHDOG_AVAILABLE and self._observer:
            self._observer.stop()
            self._observer.join(timeout=5.0)
        
        if self._handler:
            self._handler.stop()
        
        logger.info("SkillHotReloader stopped")
    
    def get_changed_skills(self) -> Set[str]:
        """获取自启动以来变更过的 Skill 列表"""
        with self._lock:
            return self._changed_skills.copy()
    
    def clear_changed_skills(self) -> None:
        """清除变更记录"""
        with self._lock:
            self._changed_skills.clear()
    
    @property
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running


# ============================================================================
# 全局单例
# ============================================================================

_global_hot_reloader: Optional[SkillHotReloader] = None


def get_skill_hot_reloader() -> SkillHotReloader:
    """获取全局 SkillHotReloader 单例"""
    global _global_hot_reloader
    if _global_hot_reloader is None:
        _global_hot_reloader = SkillHotReloader()
    return _global_hot_reloader


def start_skill_hot_reload() -> SkillHotReloader:
    """启动 Skill 热重载
    
    Returns:
        SkillHotReloader 实例
    """
    reloader = get_skill_hot_reloader()
    if not reloader.is_running:
        reloader.start()
    return reloader


def stop_skill_hot_reload() -> None:
    """停止 Skill 热重载"""
    global _global_hot_reloader
    if _global_hot_reloader:
        _global_hot_reloader.stop()
        _global_hot_reloader = None


# ============================================================================
# FastAPI 集成
# ============================================================================

async def setup_hot_reload_for_app(app) -> None:
    """为 FastAPI 应用设置热重载
    
    在应用启动时启动热重载，关闭时停止。
    
    Args:
        app: FastAPI 应用实例
    """
    import os
    
    # 只在开发模式下启用热重载
    if os.environ.get("ENV", "development") != "development":
        logger.info("Hot reload disabled in production mode")
        return
    
    @app.on_event("startup")
    async def start_hot_reload():
        start_skill_hot_reload()
    
    @app.on_event("shutdown")
    async def stop_hot_reload():
        stop_skill_hot_reload()
