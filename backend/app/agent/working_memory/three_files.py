"""
ThreeFilesManager - 三文件工作法管理器

管理三个核心文件：
1. task_plan.md - 任务计划
2. findings.md - 研究发现  
3. progress.md - 执行日志

实现核心规则：
- 2-Action Rule
- 3-Strike Protocol
- 自动读写机制
"""

from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

from app.filesystem import AgentFileSystem


class ThreeFilesManager:
    """
    三文件工作法管理器
    
    设计理念：
    1. 文件是 Agent 的工作记忆，而非 Context Window
    2. 通过文件持久化，实现跨 Session 恢复
    3. 强制 Agent 定期记录，防止 Context 爆炸
    """
    
    # 文件路径（相对于session目录）
    TASK_PLAN_FILE = "task_plan.md"
    FINDINGS_FILE = "findings.md"
    PROGRESS_FILE = "progress.md"
    
    # 2-Action Rule 计数器阈值
    ACTION_THRESHOLD = 2
    
    # 3-Strike Protocol 错误计数器阈值
    ERROR_THRESHOLD = 3
    
    def __init__(self, filesystem: AgentFileSystem, session_id: str):
        """
        初始化ThreeFilesManager
        
        Args:
            filesystem: AgentFileSystem实例
            session_id: Session ID
        """
        self.fs = filesystem
        self.session_id = session_id
        
        # Session目录
        self.session_dir = self.fs.get_session_dir(session_id)
        
        # 计数器
        self.action_counter = 0  # 2-Action Rule 计数器
        self.error_counts = {}   # 3-Strike Protocol 错误计数器 {error_type: count}
        
        # 初始化三个文件
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """确保三个文件存在，如果不存在则创建初始版本"""
        
        # 获取相对于workspace的路径
        base_path = f"sessions/{self.session_id}"
        
        # 1. task_plan.md
        task_plan_path = f"{base_path}/{self.TASK_PLAN_FILE}"
        if not self.fs.exists(task_plan_path):
            self.fs.write_with_frontmatter(
                task_plan_path,
                self._get_initial_task_plan_content(),
                metadata={
                    "title": "Task Plan",
                    "session_id": self.session_id,
                    "status": "in_progress",
                }
            )
        
        # 2. findings.md
        findings_path = f"{base_path}/{self.FINDINGS_FILE}"
        if not self.fs.exists(findings_path):
            self.fs.write_with_frontmatter(
                findings_path,
                self._get_initial_findings_content(),
                metadata={
                    "title": "Findings",
                    "session_id": self.session_id,
                }
            )
        
        # 3. progress.md
        progress_path = f"{base_path}/{self.PROGRESS_FILE}"
        if not self.fs.exists(progress_path):
            self.fs.write_with_frontmatter(
                progress_path,
                self._get_initial_progress_content(),
                metadata={
                    "title": "Progress Log",
                    "session_id": self.session_id,
                }
            )
    
    def _get_initial_task_plan_content(self) -> str:
        """获取task_plan.md的初始内容"""
        return """# Task Plan

## 目标
（待Agent填写任务目标）

## 当前进度
- [ ] Phase 1: ...
- [ ] Phase 2: ...

## 决策记录
（重要决策将记录在此）

## Agent 笔记
（Agent的思考和备注）
"""
    
    def _get_initial_findings_content(self) -> str:
        """获取findings.md的初始内容"""
        return """# Findings

## 研究发现

（Agent将在此记录搜索/浏览操作的发现）

## 技术决策

（技术选型和决策理由）

## 关键信息

（重要的事实和数据）
"""
    
    def _get_initial_progress_content(self) -> str:
        """获取progress.md的初始内容"""
        return """# Progress Log

## 执行记录

（Agent的执行步骤记录）

## 错误日志

（所有错误必须记录在此，防止重复失败）

## 成功经验

（成功的尝试和模式）
"""
    
    # ========== 读取操作 ==========
    
    def read_task_plan(self) -> Dict:
        """
        读取task_plan.md
        
        Returns:
            dict: {"metadata": dict, "content": str}
        """
        path = f"sessions/{self.session_id}/{self.TASK_PLAN_FILE}"
        return self.fs.read_with_frontmatter(path)
    
    def read_findings(self) -> Dict:
        """
        读取findings.md
        
        Returns:
            dict: {"metadata": dict, "content": str}
        """
        path = f"sessions/{self.session_id}/{self.FINDINGS_FILE}"
        return self.fs.read_with_frontmatter(path)
    
    def read_progress(self) -> Dict:
        """
        读取progress.md
        
        Returns:
            dict: {"metadata": dict, "content": str}
        """
        path = f"sessions/{self.session_id}/{self.PROGRESS_FILE}"
        return self.fs.read_with_frontmatter(path)
    
    def read_all(self) -> Dict[str, Dict]:
        """
        读取所有三个文件
        
        Returns:
            dict: {
                "task_plan": {...},
                "findings": {...},
                "progress": {...}
            }
        """
        return {
            "task_plan": self.read_task_plan(),
            "findings": self.read_findings(),
            "progress": self.read_progress(),
        }
    
    # ========== 写入操作 ==========
    
    def update_task_plan(self, content: str, append: bool = False):
        """
        更新task_plan.md
        
        Args:
            content: 新内容
            append: 是否追加（True）还是覆盖（False）
        """
        path = f"sessions/{self.session_id}/{self.TASK_PLAN_FILE}"
        
        if append:
            old_data = self.read_task_plan()
            content = old_data["content"] + "\n\n" + content
        
        self.fs.write_with_frontmatter(
            path,
            content,
            metadata={"status": "in_progress"}
        )
    
    def update_findings(self, finding: str):
        """
        追加新发现到findings.md
        
        Args:
            finding: 新发现内容
        """
        path = f"sessions/{self.session_id}/{self.FINDINGS_FILE}"
        old_data = self.read_findings()
        
        # 添加时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_finding = f"\n\n### [{timestamp}]\n{finding}"
        
        content = old_data["content"] + new_finding
        
        self.fs.write_with_frontmatter(path, content)
    
    def update_progress(self, log_entry: str, is_error: bool = False):
        """
        追加执行日志到progress.md
        
        Args:
            log_entry: 日志内容
            is_error: 是否是错误日志
        """
        path = f"sessions/{self.session_id}/{self.PROGRESS_FILE}"
        old_data = self.read_progress()
        
        # 添加时间戳和标记
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = "❌ ERROR" if is_error else "✅"
        new_entry = f"\n\n### [{timestamp}] {prefix}\n{log_entry}"
        
        content = old_data["content"] + new_entry
        
        self.fs.write_with_frontmatter(path, content)
    
    # ========== 核心规则实现 ==========
    
    def record_action(self, action_type: str, action_data: Dict):
        """
        记录Agent动作（用于2-Action Rule）
        
        Args:
            action_type: 动作类型（如 "web_search", "read_url"）
            action_data: 动作数据
        """
        # 增加计数器
        if action_type in ["web_search", "read_url"]:
            self.action_counter += 1
        
        # 2-Action Rule: 每2次动作强制写入findings
        if self.action_counter >= self.ACTION_THRESHOLD:
            # 重置计数器
            self.action_counter = 0
            # 返回True表示应该写入findings
            return True
        
        return False
    
    def record_error(self, error_type: str, error_message: str):
        """
        记录错误（用于3-Strike Protocol）
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
        """
        # 更新错误计数
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
        
        # 记录到progress.md
        self.update_progress(
            f"**Error Type**: {error_type}\n**Message**: {error_message}",
            is_error=True
        )
        
        # 3-Strike Protocol: 同类错误3次触发
        if self.error_counts[error_type] >= self.ERROR_THRESHOLD:
            return {
                "should_reread_plan": True,
                "error_type": error_type,
                "count": self.error_counts[error_type],
            }
        
        return {"should_reread_plan": False}
    
    def get_context_summary(self) -> str:
        """
        获取三文件的摘要，用于注入Agent的Context
        
        Returns:
            str: 摘要文本
        """
        data = self.read_all()
        
        task_plan_preview = data["task_plan"]["content"][:500]
        findings_preview = data["findings"]["content"][:300]
        progress_preview = data["progress"]["content"][:300]
        
        summary = f"""
# Working Memory (三文件摘要)

## Task Plan (任务计划)
{task_plan_preview}...

## Findings (研究发现)
{findings_preview}...

## Progress (执行日志)
{progress_preview}...

**完整内容请使用file_ops工具读取对应文件**
"""
        return summary
    
    def get_file_paths(self) -> Dict[str, str]:
        """
        获取三个文件的路径
        
        Returns:
            dict: {"task_plan": path, "findings": path, "progress": path}
        """
        base = f"sessions/{self.session_id}"
        return {
            "task_plan": f"{base}/{self.TASK_PLAN_FILE}",
            "findings": f"{base}/{self.FINDINGS_FILE}",
            "progress": f"{base}/{self.PROGRESS_FILE}",
        }
