"""
File Indexer Service - 本地文件索引服务

Coworker 基因：深度理解本地文件系统

功能：
- 目录遍历（支持 .gitignore）
- 文件监听（watchdog）
- 增量索引策略
- 语言检测
"""
import asyncio
import fnmatch
import hashlib
import json
import logging
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object

logger = logging.getLogger(__name__)


# ==================== 文件变更事件 ====================

class FileChangeType(Enum):
    """文件变更类型"""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileChangeEvent:
    """文件变更事件"""
    change_type: FileChangeType
    src_path: str
    dest_path: str | None = None  # 仅用于 MOVED 类型
    timestamp: datetime = field(default_factory=datetime.now)


# ==================== 数据模型 ====================

@dataclass
class FileInfo:
    """文件信息"""
    path: str
    name: str
    extension: str
    size: int
    modified_at: datetime
    content_hash: str | None = None
    language: str | None = None
    is_binary: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size": self.size,
            "modified_at": self.modified_at.isoformat(),
            "content_hash": self.content_hash,
            "language": self.language,
            "is_binary": self.is_binary,
            "metadata": self.metadata
        }


@dataclass
class DirectoryInfo:
    """目录信息"""
    path: str
    name: str
    file_count: int = 0
    total_size: int = 0
    languages: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "languages": self.languages
        }


@dataclass
class IndexState:
    """索引状态"""
    root_path: str
    indexed_at: datetime = field(default_factory=datetime.now)
    file_count: int = 0
    total_size: int = 0
    files: dict[str, FileInfo] = field(default_factory=dict)
    directories: dict[str, DirectoryInfo] = field(default_factory=dict)
    languages: dict[str, int] = field(default_factory=dict)


# ==================== 语言检测 ====================

# 扩展名到语言的映射
EXTENSION_TO_LANGUAGE = {
    # Python
    ".py": "python",
    ".pyi": "python",
    ".pyx": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".vue": "vue",
    ".svelte": "svelte",
    # Systems
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".rs": "rust",
    ".go": "go",
    # JVM
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    # .NET
    ".cs": "csharp",
    ".fs": "fsharp",
    # Shell
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".fish": "shell",
    ".ps1": "powershell",
    # Config
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".ini": "ini",
    ".conf": "config",
    # Documentation
    ".md": "markdown",
    ".rst": "rst",
    ".txt": "text",
    # Data
    ".sql": "sql",
    ".graphql": "graphql",
    ".proto": "protobuf",
    # Others
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".r": "r",
    ".R": "r",
    ".lua": "lua",
    ".pl": "perl",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".clj": "clojure",
    ".dart": "dart",
}

# 二进制文件扩展名
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".dll", ".so", ".dylib",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".ttf", ".otf", ".woff", ".woff2",
    ".pyc", ".pyo", ".class", ".o",
}


def detect_language(file_path: str) -> str | None:
    """检测文件语言"""
    ext = Path(file_path).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext)


def is_binary_file(file_path: str) -> bool:
    """判断是否为二进制文件"""
    ext = Path(file_path).suffix.lower()
    return ext in BINARY_EXTENSIONS


# ==================== Gitignore 解析 ====================

class GitignoreParser:
    """解析 .gitignore 文件"""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.patterns: list[str] = []
        self.negation_patterns: list[str] = []
        self._load_gitignore()

    def _load_gitignore(self) -> None:
        """加载 .gitignore 文件"""
        gitignore_path = self.root_path / ".gitignore"

        # 默认忽略模式
        self.patterns = [
            ".git",
            "__pycache__",
            "*.pyc",
            "node_modules",
            ".venv",
            "venv",
            ".env",
            "dist",
            "build",
            ".idea",
            ".vscode",
            "*.egg-info",
            ".DS_Store",
            "Thumbs.db",
        ]

        if gitignore_path.exists():
            try:
                with open(gitignore_path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("!"):
                            self.negation_patterns.append(line[1:])
                        else:
                            self.patterns.append(line)
            except Exception as e:
                logger.warning(f"Failed to parse .gitignore: {e}")

    def should_ignore(self, path: str) -> bool:
        """检查路径是否应该被忽略"""
        rel_path = str(Path(path).relative_to(self.root_path))
        name = Path(path).name

        # 检查否定模式
        for pattern in self.negation_patterns:
            if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(rel_path, pattern):
                return False

        # 检查忽略模式
        for pattern in self.patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # 目录模式
            if pattern.endswith("/") and fnmatch.fnmatch(name, pattern[:-1]):
                return True

        return False


# ==================== 文件索引服务 ====================

class FileIndexerService:
    """本地文件索引服务

    使用示例:
        indexer = FileIndexerService("/path/to/project")

        # 全量索引
        await indexer.index_all()

        # 增量索引
        await indexer.index_incremental()

        # 获取文件信息
        file_info = indexer.get_file("/path/to/file.py")

        # 按语言搜索
        python_files = indexer.search_by_language("python")
    """

    def __init__(
        self,
        root_path: str,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        compute_hash: bool = True
    ):
        self.root_path = Path(root_path).resolve()
        self.max_file_size = max_file_size
        self.compute_hash = compute_hash
        self.gitignore = GitignoreParser(str(self.root_path))
        self.state = IndexState(root_path=str(self.root_path))
        self._callbacks: list[Callable] = []

        logger.info(f"FileIndexerService initialized: {self.root_path}")

    async def index_all(self) -> IndexState:
        """全量索引"""
        logger.info(f"Starting full index of {self.root_path}")

        self.state = IndexState(root_path=str(self.root_path))

        for root, dirs, files in os.walk(self.root_path):
            # 过滤忽略的目录
            dirs[:] = [d for d in dirs if not self.gitignore.should_ignore(os.path.join(root, d))]

            for filename in files:
                file_path = os.path.join(root, filename)

                if self.gitignore.should_ignore(file_path):
                    continue

                try:
                    file_info = await self._index_file(file_path)
                    if file_info:
                        self.state.files[file_path] = file_info
                        self.state.file_count += 1
                        self.state.total_size += file_info.size

                        # 统计语言
                        if file_info.language:
                            self.state.languages[file_info.language] = \
                                self.state.languages.get(file_info.language, 0) + 1
                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")

        self.state.indexed_at = datetime.now()
        logger.info(f"Indexed {self.state.file_count} files, total {self.state.total_size} bytes")

        return self.state

    async def index_incremental(self) -> list[FileInfo]:
        """增量索引（基于修改时间）"""
        logger.info("Starting incremental index")

        updated_files = []

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [d for d in dirs if not self.gitignore.should_ignore(os.path.join(root, d))]

            for filename in files:
                file_path = os.path.join(root, filename)

                if self.gitignore.should_ignore(file_path):
                    continue

                try:
                    stat = os.stat(file_path)
                    modified_at = datetime.fromtimestamp(stat.st_mtime)

                    # 检查是否需要更新
                    existing = self.state.files.get(file_path)
                    if existing and existing.modified_at >= modified_at:
                        continue

                    file_info = await self._index_file(file_path)
                    if file_info:
                        self.state.files[file_path] = file_info
                        updated_files.append(file_info)

                        # 触发回调
                        for callback in self._callbacks:
                            await callback(file_info)

                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")

        logger.info(f"Incremental index updated {len(updated_files)} files")
        return updated_files

    async def _index_file(self, file_path: str) -> FileInfo | None:
        """索引单个文件"""
        try:
            path = Path(file_path)
            stat = os.stat(file_path)

            # 跳过过大的文件
            if stat.st_size > self.max_file_size:
                logger.debug(f"Skipping large file: {file_path}")
                return None

            is_binary = is_binary_file(file_path)
            content_hash = None

            # 计算内容哈希
            if self.compute_hash and not is_binary:
                try:
                    with open(file_path, "rb") as f:
                        content_hash = hashlib.md5(f.read()).hexdigest()
                except Exception:
                    pass

            return FileInfo(
                path=str(path),
                name=path.name,
                extension=path.suffix.lower(),
                size=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                content_hash=content_hash,
                language=detect_language(file_path),
                is_binary=is_binary
            )
        except Exception as e:
            logger.warning(f"Error indexing file {file_path}: {e}")
            return None

    # ==================== 查询方法 ====================

    def get_file(self, file_path: str) -> FileInfo | None:
        """获取文件信息"""
        return self.state.files.get(str(Path(file_path).resolve()))

    def search_by_language(self, language: str) -> list[FileInfo]:
        """按语言搜索文件"""
        return [f for f in self.state.files.values() if f.language == language]

    def search_by_extension(self, extension: str) -> list[FileInfo]:
        """按扩展名搜索"""
        ext = extension if extension.startswith(".") else f".{extension}"
        return [f for f in self.state.files.values() if f.extension == ext]

    def search_by_name(self, pattern: str) -> list[FileInfo]:
        """按文件名模式搜索"""
        return [f for f in self.state.files.values() if fnmatch.fnmatch(f.name, pattern)]

    def get_language_stats(self) -> dict[str, int]:
        """获取语言统计"""
        return self.state.languages.copy()

    def get_directory_tree(self, max_depth: int = 3) -> dict[str, Any]:
        """获取目录树"""
        def build_tree(path: Path, depth: int) -> dict[str, Any]:
            if depth > max_depth:
                return {"name": path.name, "type": "directory", "truncated": True}

            result = {
                "name": path.name,
                "type": "directory",
                "children": []
            }

            try:
                for item in sorted(path.iterdir()):
                    if self.gitignore.should_ignore(str(item)):
                        continue

                    if item.is_dir():
                        result["children"].append(build_tree(item, depth + 1))
                    else:
                        file_info = self.state.files.get(str(item))
                        result["children"].append({
                            "name": item.name,
                            "type": "file",
                            "language": file_info.language if file_info else None,
                            "size": file_info.size if file_info else 0
                        })
            except PermissionError:
                pass

            return result

        return build_tree(self.root_path, 0)

    # ==================== 回调注册 ====================

    def on_file_changed(self, callback: Callable) -> None:
        """注册文件变更回调"""
        self._callbacks.append(callback)

    # ==================== 持久化 ====================

    def save_index(self, path: str) -> None:
        """保存索引到文件"""
        data = {
            "root_path": self.state.root_path,
            "indexed_at": self.state.indexed_at.isoformat(),
            "file_count": self.state.file_count,
            "total_size": self.state.total_size,
            "languages": self.state.languages,
            "files": {k: v.to_dict() for k, v in self.state.files.items()}
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_index(self, path: str) -> bool:
        """从文件加载索引"""
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            self.state.root_path = data["root_path"]
            self.state.indexed_at = datetime.fromisoformat(data["indexed_at"])
            self.state.file_count = data["file_count"]
            self.state.total_size = data["total_size"]
            self.state.languages = data["languages"]

            for file_path, file_data in data.get("files", {}).items():
                self.state.files[file_path] = FileInfo(
                    path=file_data["path"],
                    name=file_data["name"],
                    extension=file_data["extension"],
                    size=file_data["size"],
                    modified_at=datetime.fromisoformat(file_data["modified_at"]),
                    content_hash=file_data.get("content_hash"),
                    language=file_data.get("language"),
                    is_binary=file_data.get("is_binary", False)
                )

            return True
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return False


# ==================== 文件监听器 (watchdog) ====================

class _FileEventHandler(FileSystemEventHandler):
    """文件事件处理器"""

    def __init__(
        self,
        indexer: FileIndexerService,
        on_change: Callable[[FileChangeEvent], None] | None = None
    ):
        self.indexer = indexer
        self.on_change = on_change
        self._debounce_timers: dict[str, threading.Timer] = {}
        self._debounce_delay = 0.5  # 防抖延迟

    def _should_process(self, path: str) -> bool:
        """检查是否应该处理该路径"""
        return not self.indexer.gitignore.should_ignore(path)

    def _debounced_process(self, event_type: FileChangeType, src_path: str, dest_path: str = None):
        """防抖处理"""
        # 取消之前的定时器
        if src_path in self._debounce_timers:
            self._debounce_timers[src_path].cancel()

        def process():
            event = FileChangeEvent(
                change_type=event_type,
                src_path=src_path,
                dest_path=dest_path
            )

            # 更新索引
            if event_type == FileChangeType.DELETED:
                if src_path in self.indexer.state.files:
                    del self.indexer.state.files[src_path]
            elif event_type in (FileChangeType.CREATED, FileChangeType.MODIFIED):
                # 同步索引文件
                loop = asyncio.new_event_loop()
                try:
                    file_info = loop.run_until_complete(
                        self.indexer._index_file(src_path)
                    )
                    if file_info:
                        self.indexer.state.files[src_path] = file_info
                finally:
                    loop.close()
            elif event_type == FileChangeType.MOVED and dest_path:
                # 处理移动
                if src_path in self.indexer.state.files:
                    del self.indexer.state.files[src_path]
                loop = asyncio.new_event_loop()
                try:
                    file_info = loop.run_until_complete(
                        self.indexer._index_file(dest_path)
                    )
                    if file_info:
                        self.indexer.state.files[dest_path] = file_info
                finally:
                    loop.close()

            # 触发回调
            if self.on_change:
                self.on_change(event)

            # 触发索引器回调
            for callback in self.indexer._callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.warning(f"Callback error: {e}")

            # 清理定时器
            self._debounce_timers.pop(src_path, None)

        # 设置新的定时器
        timer = threading.Timer(self._debounce_delay, process)
        self._debounce_timers[src_path] = timer
        timer.start()

    def on_created(self, event):
        if event.is_directory or not self._should_process(event.src_path):
            return
        logger.debug(f"File created: {event.src_path}")
        self._debounced_process(FileChangeType.CREATED, event.src_path)

    def on_modified(self, event):
        if event.is_directory or not self._should_process(event.src_path):
            return
        logger.debug(f"File modified: {event.src_path}")
        self._debounced_process(FileChangeType.MODIFIED, event.src_path)

    def on_deleted(self, event):
        if event.is_directory or not self._should_process(event.src_path):
            return
        logger.debug(f"File deleted: {event.src_path}")
        self._debounced_process(FileChangeType.DELETED, event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")
        self._debounced_process(FileChangeType.MOVED, event.src_path, event.dest_path)


class FileWatcher:
    """文件监听器

    使用示例:
        indexer = FileIndexerService("/path/to/project")
        watcher = FileWatcher(indexer)

        # 注册变更回调
        watcher.on_change(lambda event: print(f"Changed: {event.src_path}"))

        # 启动监听
        watcher.start()

        # ...

        # 停止监听
        watcher.stop()
    """

    def __init__(self, indexer: FileIndexerService):
        if not WATCHDOG_AVAILABLE:
            raise ImportError(
                "watchdog is required for file watching. "
                "Install with: pip install watchdog"
            )

        self.indexer = indexer
        self._observer: Observer | None = None
        self._change_callbacks: list[Callable[[FileChangeEvent], None]] = []
        self._running = False

    def on_change(self, callback: Callable[[FileChangeEvent], None]) -> None:
        """注册文件变更回调"""
        self._change_callbacks.append(callback)

    def start(self) -> None:
        """启动文件监听"""
        if self._running:
            return

        def notify_all(event: FileChangeEvent):
            for callback in self._change_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logger.warning(f"Change callback error: {e}")

        handler = _FileEventHandler(self.indexer, notify_all)
        self._observer = Observer()
        self._observer.schedule(
            handler,
            str(self.indexer.root_path),
            recursive=True
        )
        self._observer.start()
        self._running = True
        logger.info(f"FileWatcher started for: {self.indexer.root_path}")

    def stop(self) -> None:
        """停止文件监听"""
        if not self._running or not self._observer:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._running = False
        logger.info("FileWatcher stopped")

    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# ==================== 工厂函数 ====================

def create_file_indexer(root_path: str) -> FileIndexerService:
    """创建文件索引服务"""
    return FileIndexerService(root_path=root_path)


def create_file_watcher(indexer: FileIndexerService) -> FileWatcher | None:
    """创建文件监听器（如果 watchdog 可用）"""
    if not WATCHDOG_AVAILABLE:
        logger.warning("watchdog not available, file watching disabled")
        return None
    return FileWatcher(indexer)
