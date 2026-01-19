"""
AgentWorkspace 单元测试

重点测试路径遍历保护。
"""

from pathlib import Path

import pytest

from app.sandbox.exceptions import PathTraversalError
from app.sandbox.workspace import AgentWorkspace, WorkspaceConfig


class TestAgentWorkspace:
    """AgentWorkspace 测试"""

    @pytest.fixture
    def workspace(self, tmp_path: Path) -> AgentWorkspace:
        """创建临时工作空间"""
        config = WorkspaceConfig(base_dir=str(tmp_path))
        return AgentWorkspace("test_session", config)

    # ==================== 基本功能测试 ====================

    def test_init_creates_directories(self, workspace: AgentWorkspace):
        """初始化创建目录结构"""
        assert workspace.host_path.exists()
        assert (workspace.host_path / "code").exists()
        assert (workspace.host_path / "data").exists()
        assert (workspace.host_path / "output").exists()
        assert (workspace.host_path / "temp").exists()
        assert (workspace.host_path / ".memory").exists()

    def test_write_and_read_file(self, workspace: AgentWorkspace):
        """写入和读取文件"""
        content = "Hello, World!"
        workspace.write_file("test.txt", content)

        result = workspace.read_file("test.txt")
        assert result == content

    def test_write_file_creates_parent_dirs(self, workspace: AgentWorkspace):
        """写入文件时创建父目录"""
        workspace.write_file("deep/nested/dir/file.txt", "content")

        assert (workspace.host_path / "deep/nested/dir/file.txt").exists()

    def test_write_bytes(self, workspace: AgentWorkspace):
        """写入二进制文件"""
        content = b"\x00\x01\x02\x03"
        workspace.write_file("binary.bin", content)

        result = workspace.read_bytes("binary.bin")
        assert result == content

    def test_exists(self, workspace: AgentWorkspace):
        """检查文件存在"""
        workspace.write_file("exists.txt", "data")

        assert workspace.exists("exists.txt")
        assert not workspace.exists("not_exists.txt")

    def test_list_files(self, workspace: AgentWorkspace):
        """列出文件"""
        workspace.write_file("file1.txt", "1")
        workspace.write_file("dir/file2.txt", "2")

        files = workspace.list_files()
        file_names = [f.split("/")[-1] for f in files]

        assert "file1.txt" in file_names
        assert "file2.txt" in file_names

    def test_delete_file(self, workspace: AgentWorkspace):
        """删除文件"""
        workspace.write_file("to_delete.txt", "data")
        assert workspace.exists("to_delete.txt")

        result = workspace.delete_file("to_delete.txt")
        assert result
        assert not workspace.exists("to_delete.txt")

    def test_delete_nonexistent_file(self, workspace: AgentWorkspace):
        """删除不存在的文件返回 False"""
        result = workspace.delete_file("nonexistent.txt")
        assert not result

    def test_get_volume_mount(self, workspace: AgentWorkspace):
        """获取 Docker 挂载配置"""
        mount = workspace.get_volume_mount()

        assert str(workspace.host_path) in mount
        assert mount[str(workspace.host_path)]["bind"] == "/workspace"
        assert mount[str(workspace.host_path)]["mode"] == "rw"

    def test_get_container_path(self, workspace: AgentWorkspace):
        """获取容器内路径"""
        assert workspace.get_container_path() == "/workspace"
        assert workspace.get_container_path("file.txt") == "/workspace/file.txt"

    # ==================== 路径遍历保护测试 ====================

    def test_path_traversal_absolute_path(self, workspace: AgentWorkspace):
        """绝对路径被拒绝"""
        with pytest.raises(PathTraversalError, match="绝对路径不允许"):
            workspace.write_file("/etc/passwd", "hack")

    def test_path_traversal_dot_dot(self, workspace: AgentWorkspace):
        """.. 遍历被拒绝"""
        with pytest.raises(PathTraversalError, match="路径包含"):
            workspace.write_file("../secret.txt", "hack")

    def test_path_traversal_deep_dot_dot(self, workspace: AgentWorkspace):
        """深度 .. 遍历被拒绝"""
        with pytest.raises(PathTraversalError, match="路径包含"):
            workspace.write_file("../../etc/passwd", "hack")

    def test_path_traversal_hidden_dot_dot(self, workspace: AgentWorkspace):
        """隐藏的 .. 遍历被拒绝"""
        with pytest.raises(PathTraversalError, match="路径包含"):
            workspace.write_file("subdir/../../../etc/passwd", "hack")

    def test_path_traversal_read(self, workspace: AgentWorkspace):
        """读取时也检查路径遍历"""
        with pytest.raises(PathTraversalError):
            workspace.read_file("../secret.txt")

    def test_path_traversal_delete(self, workspace: AgentWorkspace):
        """删除时也检查路径遍历"""
        with pytest.raises(PathTraversalError):
            workspace.delete_file("../secret.txt")

    def test_path_traversal_list(self, workspace: AgentWorkspace):
        """列出文件时也检查路径遍历"""
        with pytest.raises(PathTraversalError):
            workspace.list_files("../")

    def test_path_traversal_exists(self, workspace: AgentWorkspace):
        """exists 检查路径遍历返回 False"""
        # exists 返回 False 而不是抛出异常（更安全）
        assert not workspace.exists("../secret.txt")

    def test_path_traversal_get_container_path(self, workspace: AgentWorkspace):
        """获取容器路径时也检查"""
        with pytest.raises(PathTraversalError):
            workspace.get_container_path("../secret.txt")

    # ==================== 边界情况 ====================

    def test_valid_subdirectory(self, workspace: AgentWorkspace):
        """合法的子目录路径"""
        workspace.write_file("sub/dir/file.txt", "content")

        assert workspace.exists("sub/dir/file.txt")
        assert workspace.read_file("sub/dir/file.txt") == "content"

    def test_cleanup(self, workspace: AgentWorkspace):
        """清理工作空间"""
        workspace.write_file("file.txt", "data")
        assert workspace.host_path.exists()

        workspace.cleanup()
        assert not workspace.host_path.exists()

    def test_get_size(self, workspace: AgentWorkspace):
        """获取工作空间大小"""
        workspace.write_file("file1.txt", "x" * 1024)  # 1KB
        workspace.write_file("file2.txt", "y" * 1024)  # 1KB

        size_mb = workspace.get_size_mb()
        assert size_mb > 0
        assert size_mb < 1  # 小于 1MB

    def test_is_within_limit(self, workspace: AgentWorkspace):
        """检查大小限制"""
        assert workspace.is_within_limit()
