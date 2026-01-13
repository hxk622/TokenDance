"""
AgentFileSystem - Agent文件系统抽象层

设计理念：
1. 文件系统 = Source of Truth
2. 多租户物理隔离 (Org/Team/Workspace/Session)
3. YAML Frontmatter + Markdown Body
4. 支持监听式同步
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class AgentFileSystem:
    """
    Agent文件系统抽象层
    
    目录结构：
    workspace_root/
      └── {org_id}/
          └── {team_id}/
              └── {workspace_id}/
                  ├── cache/              # 临时缓存（7天 TTL）
                  │   ├── api_responses/
                  │   ├── web_pages/
                  │   └── intermediate_results/
                  ├── context/            # 长期上下文
                  │   ├── memory.md       # Agent 记忆
                  │   └── learnings.md    # 学习经验
                  ├── sessions/           # Session工作目录
                  │   └── {session_id}/
                  │       ├── task_plan.md    # 任务计划（三文件之一）
                  │       ├── findings.md     # 研究发现（三文件之二）
                  │       ├── progress.md     # 执行日志（三文件之三）
                  │       └── artifacts/      # 生成的产物
                  └── shared/             # 跨任务共享
                      └── knowledge_base/
    """
    
    def __init__(
        self,
        workspace_root: str = "./workspace",
        org_id: str = "default_org",
        team_id: str = "default_team",
        workspace_id: str = "default_workspace",
    ):
        """
        初始化AgentFileSystem
        
        Args:
            workspace_root: 工作区根目录
            org_id: 组织ID
            team_id: 团队ID
            workspace_id: 工作空间ID
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.org_id = org_id
        self.team_id = team_id
        self.workspace_id = workspace_id
        
        # 工作空间路径
        self.workspace_path = self.workspace_root / org_id / team_id / workspace_id
        
        # 确保目录存在
        self._ensure_directory_structure()
    
    def _ensure_directory_structure(self):
        """确保目录结构存在"""
        directories = [
            self.workspace_path / "cache" / "api_responses",
            self.workspace_path / "cache" / "web_pages",
            self.workspace_path / "cache" / "intermediate_results",
            self.workspace_path / "context",
            self.workspace_path / "sessions",
            self.workspace_path / "shared" / "knowledge_base",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_session_dir(self, session_id: str) -> Path:
        """
        获取Session工作目录
        
        Args:
            session_id: Session ID
            
        Returns:
            Path: Session目录路径
        """
        session_dir = self.workspace_path / "sessions" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建artifacts子目录
        (session_dir / "artifacts").mkdir(exist_ok=True)
        
        return session_dir
    
    def read(self, relative_path: str) -> str:
        """
        读取文件内容
        
        Args:
            relative_path: 相对于workspace的路径
            
        Returns:
            str: 文件内容
        """
        file_path = self.workspace_path / relative_path
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {relative_path}")
        
        if not self._is_safe_path(file_path):
            raise PermissionError(f"不允许访问工作空间外的文件: {relative_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def write(self, relative_path: str, content: str) -> Path:
        """
        写入文件内容
        
        Args:
            relative_path: 相对于workspace的路径
            content: 文件内容
            
        Returns:
            Path: 文件路径
        """
        file_path = self.workspace_path / relative_path
        
        if not self._is_safe_path(file_path):
            raise PermissionError(f"不允许写入工作空间外的文件: {relative_path}")
        
        # 确保父目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return file_path
    
    def read_with_frontmatter(self, relative_path: str) -> Dict[str, Any]:
        """
        读取带YAML Frontmatter的Markdown文件
        
        Args:
            relative_path: 相对于workspace的路径
            
        Returns:
            dict: {"metadata": dict, "content": str}
        """
        content = self.read(relative_path)
        
        # 解析YAML Frontmatter
        if content.startswith("---\n"):
            parts = content.split("---\n", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    return {
                        "metadata": metadata or {},
                        "content": body,
                    }
                except yaml.YAMLError:
                    pass
        
        # 没有Frontmatter
        return {
            "metadata": {},
            "content": content,
        }
    
    def write_with_frontmatter(
        self,
        relative_path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        写入带YAML Frontmatter的Markdown文件
        
        Args:
            relative_path: 相对于workspace的路径
            content: Markdown内容
            metadata: YAML Frontmatter元数据
            
        Returns:
            Path: 文件路径
        """
        # 构建完整内容
        if metadata:
            # 添加updated_at
            if "created_at" not in metadata:
                metadata["created_at"] = datetime.utcnow().isoformat() + "Z"
            metadata["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            yaml_str = yaml.dump(metadata, allow_unicode=True, sort_keys=False)
            full_content = f"---\n{yaml_str}---\n\n{content}"
        else:
            full_content = content
        
        return self.write(relative_path, full_content)
    
    def list_files(self, relative_dir: str = "", pattern: str = "*") -> List[str]:
        """
        列出目录下的文件
        
        Args:
            relative_dir: 相对于workspace的目录路径
            pattern: 文件名模式（支持通配符）
            
        Returns:
            List[str]: 相对路径列表
        """
        dir_path = self.workspace_path / relative_dir
        
        if not dir_path.exists():
            return []
        
        if not self._is_safe_path(dir_path):
            raise PermissionError(f"不允许访问工作空间外的目录: {relative_dir}")
        
        # 收集匹配的文件
        files = []
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                # 返回相对于workspace的路径
                rel_path = file_path.relative_to(self.workspace_path)
                files.append(str(rel_path))
        
        return sorted(files)
    
    def delete(self, relative_path: str):
        """
        删除文件
        
        Args:
            relative_path: 相对于workspace的路径
        """
        file_path = self.workspace_path / relative_path
        
        if not file_path.exists():
            return
        
        if not self._is_safe_path(file_path):
            raise PermissionError(f"不允许删除工作空间外的文件: {relative_path}")
        
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
    
    def exists(self, relative_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            relative_path: 相对于workspace的路径
            
        Returns:
            bool: 是否存在
        """
        file_path = self.workspace_path / relative_path
        return file_path.exists()
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """
        获取绝对路径
        
        Args:
            relative_path: 相对于workspace的路径
            
        Returns:
            Path: 绝对路径
        """
        return self.workspace_path / relative_path
    
    def _is_safe_path(self, path: Path) -> bool:
        """
        检查路径是否在工作空间内
        
        Args:
            path: 要检查的路径
            
        Returns:
            bool: 是否安全
        """
        try:
            # 解析为绝对路径
            abs_path = path.resolve()
            # 检查是否在工作空间内
            abs_path.relative_to(self.workspace_path)
            return True
        except ValueError:
            return False
    
    def get_workspace_info(self) -> Dict[str, str]:
        """
        获取工作空间信息
        
        Returns:
            dict: 工作空间信息
        """
        return {
            "workspace_root": str(self.workspace_root),
            "org_id": self.org_id,
            "team_id": self.team_id,
            "workspace_id": self.workspace_id,
            "workspace_path": str(self.workspace_path),
        }
