"""
Agent 统一工作空间

解决问题：不同 Sandbox 类型使用不同路径
- DockerSimple 挂载 /workspace
- AIOSandbox 使用 /home/gem/workspace
- Subprocess 使用 os.getcwd()

统一为：
- 宿主机: /var/tokendance/workspaces/{session_id}/
- 容器内: /workspace (Volume 挂载)
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from app.sandbox.exceptions import PathTraversalError


@dataclass
class WorkspaceConfig:
    """工作空间配置"""

    base_dir: str = "/var/tokendance/workspaces"
    max_size_mb: int = 1024
    cleanup_after_hours: int = 24


class AgentWorkspace:
    """Agent 统一工作空间

    提供安全的文件操作，带路径遍历保护。
    """

    def __init__(self, session_id: str, config: WorkspaceConfig | None = None):
        self.session_id = session_id
        self.config = config or WorkspaceConfig()

        # 宿主机路径
        self.host_path = Path(self.config.base_dir) / session_id

        # 容器内路径（统一）
        self.container_path = "/workspace"

        self._init_workspace()

    def _init_workspace(self) -> None:
        """初始化目录结构"""
        self.host_path.mkdir(parents=True, exist_ok=True)

        for subdir in ["code", "data", "output", "artifacts", "temp", ".memory"]:
            (self.host_path / subdir).mkdir(exist_ok=True)

        # 初始化 Working Memory
        for f in ["task_plan.md", "findings.md", "progress.md"]:
            filepath = self.host_path / ".memory" / f
            if not filepath.exists():
                filepath.write_text(f"# {f.replace('.md', '').replace('_', ' ').title()}\n\n")

    def _safe_path(self, relative: str) -> Path:
        """验证并返回安全路径

        防止路径遍历攻击（如 ../../etc/passwd）。

        Args:
            relative: 相对路径

        Returns:
            Path: 验证后的绝对路径

        Raises:
            PathTraversalError: 如果检测到路径遍历
        """
        # 1. 禁止绝对路径
        if relative.startswith("/"):
            raise PathTraversalError(f"绝对路径不允许: {relative}")

        # 2. 禁止明显的遍历模式
        if ".." in relative:
            raise PathTraversalError(f"路径包含 '..': {relative}")

        # 3. 规范化并验证
        resolved = (self.host_path / relative).resolve()

        # 4. 确保在 workspace 内
        try:
            resolved.relative_to(self.host_path.resolve())
        except ValueError as e:
            raise PathTraversalError(f"路径遍历检测: {relative} -> {resolved}") from e

        return resolved

    def get_host_path(self, relative: str = "") -> Path:
        """获取宿主机路径"""
        if relative:
            return self._safe_path(relative)
        return self.host_path

    def get_container_path(self, relative: str = "") -> str:
        """获取容器内路径"""
        if relative:
            # 验证路径安全性（即使只是获取容器路径）
            self._safe_path(relative)
        return f"{self.container_path}/{relative}" if relative else self.container_path

    def get_volume_mount(self) -> dict[str, dict[str, str]]:
        """获取 Docker Volume 挂载配置"""
        return {str(self.host_path): {"bind": self.container_path, "mode": "rw"}}

    def write_file(self, relative: str, content: str | bytes) -> Path:
        """写入文件

        Args:
            relative: 相对路径
            content: 文件内容

        Returns:
            Path: 写入的文件路径

        Raises:
            PathTraversalError: 如果路径不安全
        """
        filepath = self._safe_path(relative)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            filepath.write_bytes(content)
        else:
            filepath.write_text(content)

        return filepath

    def read_file(self, relative: str) -> str:
        """读取文件

        Args:
            relative: 相对路径

        Returns:
            str: 文件内容

        Raises:
            PathTraversalError: 如果路径不安全
            FileNotFoundError: 如果文件不存在
        """
        filepath = self._safe_path(relative)
        return filepath.read_text()

    def read_bytes(self, relative: str) -> bytes:
        """读取二进制文件

        Args:
            relative: 相对路径

        Returns:
            bytes: 文件内容
        """
        filepath = self._safe_path(relative)
        return filepath.read_bytes()

    def exists(self, relative: str) -> bool:
        """检查文件是否存在"""
        try:
            filepath = self._safe_path(relative)
            return filepath.exists()
        except PathTraversalError:
            return False

    def list_files(self, relative: str = "") -> list[str]:
        """列出文件

        Args:
            relative: 相对目录路径

        Returns:
            list[str]: 相对路径列表
        """
        if relative:
            dirpath = self._safe_path(relative)
        else:
            dirpath = self.host_path

        if not dirpath.exists():
            return []

        return [str(p.relative_to(self.host_path)) for p in dirpath.rglob("*") if p.is_file()]

    def delete_file(self, relative: str) -> bool:
        """删除文件

        Args:
            relative: 相对路径

        Returns:
            bool: 是否删除成功
        """
        filepath = self._safe_path(relative)
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return True
        return False

    def cleanup(self) -> None:
        """清理整个工作空间"""
        if self.host_path.exists():
            shutil.rmtree(self.host_path)

    def get_size_mb(self) -> float:
        """获取工作空间大小（MB）"""
        total = 0
        for f in self.host_path.rglob("*"):
            if f.is_file():
                total += f.stat().st_size
        return total / (1024 * 1024)

    def is_within_limit(self) -> bool:
        """检查是否在大小限制内"""
        return self.get_size_mb() < self.config.max_size_mb
