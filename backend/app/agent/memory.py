"""
Working Memory - 三文件工作记忆系统

基于 Manus Agent 核心架构原则实现：
- task_plan.md: 任务计划路线图
- findings.md: 研究发现知识库
- progress.md: 执行日志

配套行为规则：
- 2-Action Rule: 每 2 次操作必须记录发现
- 3-Strike Protocol: 同类错误 3 次触发重启
- 5-Question Reboot: 迷茫时自我检测
"""
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkingMemory:
    """三文件工作记忆系统

    将 Agent 的工作状态外化到持久化 Markdown 文件，
    而不是完全依赖 LLM Context Window。

    核心文件：
    - task_plan.md: 任务拆解和执行计划
    - findings.md: 研究发现和技术决策
    - progress.md: 执行过程和错误日志
    """

    # 文件模板
    TASK_PLAN_TEMPLATE = """# Task Plan

## Goal
TODO: Define your task goal here (1-2 sentences)

## Current Status
- Phase: Planning
- Progress: 0%
- Blockers: None

## Execution Plan

### Phase 1: {Phase Name}
**Goal**: {Phase objective}
**Steps**:
1. [ ] Step 1
2. [ ] Step 2

**Expected Output**: {Deliverable}

## Technical Decisions
- TBD

## Risks & Mitigation
- TBD
"""

    FINDINGS_TEMPLATE = """# Research Findings

*This file stores all research discoveries and technical decisions.*

---
"""

    PROGRESS_TEMPLATE = """# Execution Progress Log

*This file records all actions, successes, and failures.*

---
"""

    def __init__(
        self,
        workspace_path: str,
        session_id: str,
        auto_init: bool = True
    ):
        """初始化 WorkingMemory

        Args:
            workspace_path: Workspace 根目录
            session_id: Session ID
            auto_init: 是否自动初始化文件（默认 True）
        """
        self.workspace_path = Path(workspace_path) / session_id
        self.session_id = session_id

        # 三个核心文件路径
        self.task_plan_file = self.workspace_path / "task_plan.md"
        self.findings_file = self.workspace_path / "findings.md"
        self.progress_file = self.workspace_path / "progress.md"

        # 规则追踪器
        self.action_counter = 0  # 2-Action Rule 计数器
        self.error_tracker: dict[str, int] = {}  # 3-Strike Protocol 错误追踪
        self.last_plan_read_time: datetime | None = None  # 上次读取计划时间

        # 自动初始化
        if auto_init:
            self._ensure_workspace()
            self._init_files()

        logger.info(f"WorkingMemory initialized: {self.workspace_path}")

    def _ensure_workspace(self) -> None:
        """确保工作目录存在"""
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    def _init_files(self) -> None:
        """初始化三个文件（如果不存在）"""
        if not self.task_plan_file.exists():
            self.task_plan_file.write_text(self.TASK_PLAN_TEMPLATE)
            logger.info("Created task_plan.md")

        if not self.findings_file.exists():
            self.findings_file.write_text(self.FINDINGS_TEMPLATE)
            logger.info("Created findings.md")

        if not self.progress_file.exists():
            self.progress_file.write_text(self.PROGRESS_TEMPLATE)
            logger.info("Created progress.md")

    # ==================== Task Plan 操作 ====================

    async def read_task_plan(self) -> str:
        """读取任务计划

        Returns:
            str: task_plan.md 内容
        """
        content = self.task_plan_file.read_text(encoding='utf-8')
        self.last_plan_read_time = datetime.now()
        logger.debug("Read task_plan.md")
        return content

    async def update_task_plan(self, content: str) -> None:
        """更新任务计划

        Args:
            content: 新的计划内容
        """
        self.task_plan_file.write_text(content, encoding='utf-8')
        await self._log_progress(
            "📝 Task Plan Updated",
            "Task plan has been modified"
        )
        logger.info("Updated task_plan.md")

    async def append_to_task_plan(self, section: str, content: str) -> None:
        """追加内容到任务计划特定章节

        Args:
            section: 章节标题（如 "## Technical Decisions"）
            content: 要追加的内容
        """
        current = await self.read_task_plan()

        # 简单实现：直接追加到文件末尾
        # TODO: 更智能的章节定位和插入
        updated = current + f"\n{content}\n"
        await self.update_task_plan(updated)

    def should_recite_plan(self, interval_minutes: int = 15) -> bool:
        """判断是否应该重读计划（Plan Recitation）

        Args:
            interval_minutes: 重读间隔（分钟）

        Returns:
            bool: 是否应该重读
        """
        if self.last_plan_read_time is None:
            return True

        elapsed = (datetime.now() - self.last_plan_read_time).total_seconds() / 60
        return elapsed >= interval_minutes

    # ==================== Findings 操作 ====================

    async def read_findings(self) -> str:
        """读取研究发现

        Returns:
            str: findings.md 内容
        """
        return self.findings_file.read_text(encoding='utf-8')

    async def append_finding(
        self,
        title: str,
        content: str,
        metadata: dict[str, str] | None = None
    ) -> None:
        """追加研究发现（2-Action Rule）

        Args:
            title: 发现标题
            content: 发现内容
            metadata: 元数据（如 query, url, tool 等）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"\n## [{timestamp}] {title}\n"

        if metadata:
            for key, value in metadata.items():
                entry += f"**{key.capitalize()}**: {value}\n"
            entry += "\n"

        entry += f"{content}\n"

        with self.findings_file.open("a", encoding='utf-8') as f:
            f.write(entry)

        logger.info(f"Appended finding: {title}")

    def should_record_finding(self) -> bool:
        """2-Action Rule 检查

        每进行 2 次信息获取操作，必须记录发现

        Returns:
            bool: 是否应该记录发现
        """
        self.action_counter += 1

        if self.action_counter >= 2:
            self.action_counter = 0
            logger.debug("2-Action Rule triggered: Time to record findings")
            return True

        return False

    def reset_action_counter(self) -> None:
        """重置动作计数器"""
        self.action_counter = 0

    # ==================== Progress 操作 ====================

    async def read_progress(self, last_n_chars: int | None = None) -> str:
        """读取执行日志

        Args:
            last_n_chars: 只读取最后 N 个字符（用于摘要）

        Returns:
            str: progress.md 内容
        """
        content = self.progress_file.read_text(encoding='utf-8')

        if last_n_chars and len(content) > last_n_chars:
            return content[-last_n_chars:]

        return content

    async def log_action(
        self,
        action: str,
        result: str,
        status: str = "✅"
    ) -> None:
        """记录动作执行

        Args:
            action: 动作描述
            result: 执行结果
            status: 状态标记（✅ 成功，❌ 失败，🔧 进行中）
        """
        await self._log_progress(
            f"{status} {action}",
            result
        )

    async def log_error(
        self,
        error_type: str,
        details: str,
        tool_name: str | None = None,
        attempt: int | None = None
    ) -> bool:
        """记录错误并检查 3-Strike Protocol

        Args:
            error_type: 错误类型（如 ImportError, SyntaxError）
            details: 错误详情
            tool_name: 工具名称
            attempt: 尝试次数（如果已知）

        Returns:
            bool: 是否触发 3-Strike（需要重启）
        """
        # 更新错误计数
        count = self.error_tracker.get(error_type, 0) + 1
        self.error_tracker[error_type] = count

        if attempt is None:
            attempt = count

        # 记录到 progress.md
        log_title = f"❌ ERROR (attempt {attempt}): {error_type}"
        if tool_name:
            log_title += f" [{tool_name}]"

        await self._log_progress(log_title, details)

        # 检查是否达到 3 次
        if count >= 3:
            await self._log_progress(
                "🚨 3-STRIKE TRIGGERED",
                f"Error type '{error_type}' has occurred 3 times. "
                "Stopping for review and reboot."
            )
            logger.warning(f"3-Strike triggered for: {error_type}")
            return True

        return False

    async def log_phase_complete(self, phase: str, summary: str) -> None:
        """记录 Phase 完成

        Args:
            phase: Phase 名称
            summary: 完成总结
        """
        await self._log_progress(
            f"✅ {phase} Completed",
            summary
        )

    async def _log_progress(self, title: str, content: str) -> None:
        """内部方法：追加日志到 progress.md

        Args:
            title: 日志标题
            content: 日志内容
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"\n## [{timestamp}] {title}\n{content}\n"

        with self.progress_file.open("a", encoding='utf-8') as f:
            f.write(entry)

        logger.debug(f"Progress logged: {title}")

    # ==================== 规则检查 ====================

    def get_error_count(self, error_type: str) -> int:
        """获取特定错误类型的发生次数

        Args:
            error_type: 错误类型

        Returns:
            int: 发生次数
        """
        return self.error_tracker.get(error_type, 0)

    def reset_error_tracker(self, error_type: str | None = None) -> None:
        """重置错误追踪器

        Args:
            error_type: 如果指定，只重置该类型；否则清空所有
        """
        if error_type:
            self.error_tracker.pop(error_type, None)
            logger.info(f"Reset error tracker for: {error_type}")
        else:
            self.error_tracker.clear()
            logger.info("Reset all error trackers")

    def get_statistics(self) -> dict[str, any]:
        """获取统计信息

        Returns:
            Dict: 统计数据
        """
        return {
            "workspace_path": str(self.workspace_path),
            "session_id": self.session_id,
            "action_counter": self.action_counter,
            "error_tracker": dict(self.error_tracker),
            "last_plan_read": self.last_plan_read_time.isoformat() if self.last_plan_read_time else None,
            "files_exist": {
                "task_plan": self.task_plan_file.exists(),
                "findings": self.findings_file.exists(),
                "progress": self.progress_file.exists(),
            }
        }

    # ==================== 文件管理 ====================

    def get_file_path(self, file_name: str) -> Path:
        """获取文件绝对路径

        Args:
            file_name: 文件名（task_plan, findings, progress）

        Returns:
            Path: 文件路径
        """
        mapping = {
            "task_plan": self.task_plan_file,
            "findings": self.findings_file,
            "progress": self.progress_file,
        }
        return mapping.get(file_name, self.workspace_path / file_name)

    async def backup_files(self, backup_dir: Path | None = None) -> None:
        """备份三个文件

        Args:
            backup_dir: 备份目录（默认为 workspace_path/backups）
        """
        if backup_dir is None:
            backup_dir = self.workspace_path / "backups"

        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for file in [self.task_plan_file, self.findings_file, self.progress_file]:
            if file.exists():
                backup_file = backup_dir / f"{file.stem}_{timestamp}{file.suffix}"
                backup_file.write_text(file.read_text(encoding='utf-8'), encoding='utf-8')

        logger.info(f"Files backed up to: {backup_dir}")

    def __repr__(self) -> str:
        return (
            f"<WorkingMemory("
            f"session={self.session_id[:8]}, "
            f"actions={self.action_counter}/2, "
            f"errors={len(self.error_tracker)})>"
        )


# ==================== 便捷函数 ====================

async def create_working_memory(
    workspace_path: str,
    session_id: str,
    initial_task: str | None = None
) -> WorkingMemory:
    """创建 WorkingMemory 实例并初始化

    Args:
        workspace_path: Workspace 根目录
        session_id: Session ID
        initial_task: 初始任务描述（可选）

    Returns:
        WorkingMemory: 初始化完成的实例
    """
    memory = WorkingMemory(workspace_path, session_id)

    # 如果提供了初始任务，写入 task_plan.md
    if initial_task:
        plan = f"""# Task Plan

## Goal
{initial_task}

## Current Status
- Phase: Phase 1
- Progress: 0%
- Blockers: None

## Execution Plan

### Phase 1: Planning
**Goal**: Break down the task and create execution plan
**Steps**:
1. [ ] Analyze requirements
2. [ ] Design solution
3. [ ] Create detailed plan

**Expected Output**: Complete execution plan

## Technical Decisions
- TBD

## Risks & Mitigation
- TBD
"""
        await memory.update_task_plan(plan)

    # 记录 Session 启动
    await memory.log_action(
        "Session Started",
        f"Session ID: {session_id}\nTask: {initial_task or 'TBD'}"
    )

    return memory
