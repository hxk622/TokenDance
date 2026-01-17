"""
Three-File Auto Writer - 三文件工作法自动化写入

实现自动写入 findings/progress 的 Hook，不完全依赖 prompt 约定：

核心机制：
1. **ActionCounter**: 追踪重大操作次数，触发 2-Action Rule
2. **FindingsHook**: 每 2 次重大操作自动写入 findings.md
3. **ProgressHook**: 关键节点自动写入 progress.md
4. **ErrorCapture**: 自动捕获并记录错误 (Keep the Failures)

设计原则：
- Hook 在 Agent 执行层自动触发，不依赖 LLM 遵守 prompt
- 异步写入，不阻塞主流程
- 幂等设计，重复写入不会破坏数据
"""
import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ActionType(str, Enum):
    """操作类型 - 用于 2-Action Rule 计数"""
    WEB_SEARCH = "web_search"
    READ_URL = "read_url"
    BROWSER_OPEN = "browser_open"
    BROWSER_SNAPSHOT = "browser_snapshot"
    CODE_EXECUTE = "code_execute"
    FILE_WRITE = "file_write"
    API_CALL = "api_call"

    # 非重大操作（不计入 2-Action Rule）
    FILE_READ = "file_read"
    GREP = "grep"
    THINKING = "thinking"


# 需要计入 2-Action Rule 的重大操作
MAJOR_ACTIONS = {
    ActionType.WEB_SEARCH,
    ActionType.READ_URL,
    ActionType.BROWSER_OPEN,
    ActionType.BROWSER_SNAPSHOT,
    ActionType.CODE_EXECUTE,
    ActionType.API_CALL,
}


@dataclass
class ActionRecord:
    """操作记录"""
    action_type: ActionType
    tool_name: str
    params: dict[str, Any]
    result_summary: str
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    error: str | None = None
    duration_ms: int | None = None


@dataclass
class SessionProgress:
    """Session 进度"""
    session_id: str
    phase: str  # init, researching, analyzing, generating, completed
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    findings_written: int = 0
    last_finding_at: datetime | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)


class ThreeFileAutoWriter:
    """三文件自动写入器

    自动管理 findings.md 和 progress.md 的写入：
    - 监听 Agent 操作事件
    - 按 2-Action Rule 触发 findings 写入
    - 在关键节点写入 progress
    - 自动捕获和记录错误

    Usage:
        writer = ThreeFileAutoWriter(session_id, workspace_path)

        # 在 Agent 中注册 Hook
        agent.on_tool_call(writer.on_tool_call)
        agent.on_tool_result(writer.on_tool_result)
        agent.on_phase_change(writer.on_phase_change)
        agent.on_error(writer.on_error)
        agent.on_session_end(writer.on_session_end)
    """

    def __init__(
        self,
        session_id: str,
        workspace_path: str,
        action_threshold: int = 2,  # 2-Action Rule
        redis_client = None,  # 可选 Redis 客户端用于持久化
    ):
        self.session_id = session_id
        self.workspace = Path(workspace_path)
        self.action_threshold = action_threshold
        self.redis = redis_client

        # 内部状态
        self._action_counter = 0
        self._pending_findings: list[ActionRecord] = []
        self._progress = SessionProgress(session_id=session_id, phase="init")
        self._write_lock = asyncio.Lock()

        # 确保目录存在
        self.workspace.mkdir(parents=True, exist_ok=True)

    @property
    def findings_path(self) -> Path:
        return self.workspace / "findings.md"

    @property
    def progress_path(self) -> Path:
        return self.workspace / "progress.md"

    @property
    def task_plan_path(self) -> Path:
        return self.workspace / "task_plan.md"

    # ==================== Hook 方法 ====================

    async def on_tool_call(
        self,
        tool_name: str,
        params: dict[str, Any]
    ) -> None:
        """工具调用前的 Hook"""
        logger.debug(f"[AutoWriter] Tool call: {tool_name}")

    async def on_tool_result(
        self,
        tool_name: str,
        params: dict[str, Any],
        result: Any,
        success: bool,
        error: str | None = None,
        duration_ms: int | None = None
    ) -> None:
        """工具执行结果的 Hook - 核心入口"""

        # 1. 映射到 ActionType
        action_type = self._map_tool_to_action(tool_name)

        # 2. 创建操作记录
        record = ActionRecord(
            action_type=action_type,
            tool_name=tool_name,
            params=params,
            result_summary=self._summarize_result(result),
            success=success,
            error=error,
            duration_ms=duration_ms
        )

        # 3. 更新统计
        self._progress.total_actions += 1
        if success:
            self._progress.successful_actions += 1
        else:
            self._progress.failed_actions += 1

        # 4. 错误记录 (Keep the Failures)
        if not success and error:
            await self._record_error(record)

        # 5. 检查 2-Action Rule
        if action_type in MAJOR_ACTIONS:
            self._action_counter += 1
            self._pending_findings.append(record)

            if self._action_counter >= self.action_threshold:
                await self._flush_findings()

    async def on_phase_change(self, new_phase: str) -> None:
        """阶段变更 Hook"""
        old_phase = self._progress.phase
        self._progress.phase = new_phase

        # 写入 progress
        await self._write_progress_entry(
            f"Phase transition: {old_phase} → {new_phase}"
        )

        logger.info(f"[AutoWriter] Phase changed: {old_phase} → {new_phase}")

    async def on_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None
    ) -> None:
        """错误捕获 Hook"""
        error_record = {
            "type": error_type,
            "message": error_message,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        self._progress.errors.append(error_record)

        # 立即写入 progress (Keep the Failures)
        await self._write_progress_entry(
            f"❌ Error [{error_type}]: {error_message}",
            is_error=True
        )

    async def on_session_end(self, status: str = "completed") -> None:
        """Session 结束 Hook"""
        # 1. 刷新所有待写入的 findings
        if self._pending_findings:
            await self._flush_findings(force=True)

        # 2. 写入最终进度
        summary = self._generate_session_summary(status)
        await self._write_progress_entry(summary, is_summary=True)

        # 3. 持久化到 Redis (如果可用)
        if self.redis:
            await self._persist_to_redis()

        logger.info(f"[AutoWriter] Session {self.session_id} ended: {status}")

    # ==================== 内部方法 ====================

    def _map_tool_to_action(self, tool_name: str) -> ActionType:
        """映射工具名到操作类型"""
        mapping = {
            "web_search": ActionType.WEB_SEARCH,
            "read_url": ActionType.READ_URL,
            "browser_open": ActionType.BROWSER_OPEN,
            "browser_snapshot": ActionType.BROWSER_SNAPSHOT,
            "browser_click": ActionType.BROWSER_OPEN,
            "browser_fill": ActionType.BROWSER_OPEN,
            "code_execute": ActionType.CODE_EXECUTE,
            "create_file": ActionType.FILE_WRITE,
            "edit_file": ActionType.FILE_WRITE,
            "read_file": ActionType.FILE_READ,
            "grep": ActionType.GREP,
        }
        return mapping.get(tool_name, ActionType.API_CALL)

    def _summarize_result(self, result: Any, max_length: int = 200) -> str:
        """生成结果摘要"""
        if result is None:
            return "No result"

        if isinstance(result, str):
            text = result
        elif isinstance(result, dict):
            text = json.dumps(result, ensure_ascii=False)
        elif isinstance(result, list):
            text = f"[{len(result)} items]"
        else:
            text = str(result)

        if len(text) > max_length:
            return text[:max_length] + "..."
        return text

    async def _flush_findings(self, force: bool = False) -> None:
        """刷新 findings 到文件"""
        if not self._pending_findings and not force:
            return

        async with self._write_lock:
            try:
                # 生成 findings 条目
                entries = []
                for record in self._pending_findings:
                    entry = self._format_finding_entry(record)
                    entries.append(entry)

                # 追加到文件
                content = "\n".join(entries) + "\n"
                await self._append_to_file(self.findings_path, content)

                # 更新统计
                self._progress.findings_written += len(self._pending_findings)
                self._progress.last_finding_at = datetime.now()

                # 重置
                self._action_counter = 0
                self._pending_findings.clear()

                logger.debug(f"[AutoWriter] Flushed {len(entries)} findings")

            except Exception as e:
                logger.error(f"[AutoWriter] Failed to flush findings: {e}")

    def _format_finding_entry(self, record: ActionRecord) -> str:
        """格式化单条 finding"""
        timestamp = record.timestamp.strftime("%H:%M:%S")
        status = "✅" if record.success else "❌"

        entry = f"""### {status} {record.tool_name} [{timestamp}]
**参数**: `{json.dumps(record.params, ensure_ascii=False)[:100]}`
**结果**: {record.result_summary}
"""
        if record.error:
            entry += f"**错误**: {record.error}\n"

        return entry

    async def _write_progress_entry(
        self,
        content: str,
        is_error: bool = False,
        is_summary: bool = False
    ) -> None:
        """写入 progress 条目"""
        async with self._write_lock:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if is_summary:
                    entry = f"\n---\n\n## 📊 Session 总结 [{timestamp}]\n{content}\n"
                elif is_error:
                    entry = f"\n### {timestamp}\n{content}\n"
                else:
                    entry = f"\n**[{timestamp}]** {content}\n"

                await self._append_to_file(self.progress_path, entry)

            except Exception as e:
                logger.error(f"[AutoWriter] Failed to write progress: {e}")

    async def _record_error(self, record: ActionRecord) -> None:
        """记录错误 (Keep the Failures)"""
        error_entry = {
            "tool": record.tool_name,
            "params": record.params,
            "error": record.error,
            "timestamp": record.timestamp.isoformat()
        }
        self._progress.errors.append(error_entry)

        # 写入 progress
        await self._write_progress_entry(
            f"❌ [{record.tool_name}] {record.error}",
            is_error=True
        )

    def _generate_session_summary(self, status: str) -> str:
        """生成 Session 总结"""
        p = self._progress
        success_rate = (p.successful_actions / p.total_actions * 100) if p.total_actions > 0 else 0

        summary = f"""
**状态**: {status}
**总操作数**: {p.total_actions}
**成功率**: {success_rate:.1f}% ({p.successful_actions}/{p.total_actions})
**Findings 写入**: {p.findings_written} 次
**错误数**: {len(p.errors)}
"""
        if p.errors:
            summary += "\n**错误列表**:\n"
            for err in p.errors[-5:]:  # 最近5个错误
                summary += f"- [{err.get('tool', 'unknown')}] {err.get('error', 'unknown')}\n"

        return summary

    async def _append_to_file(self, path: Path, content: str) -> None:
        """追加内容到文件"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: path.open("a", encoding="utf-8").write(content)
        )

    async def _persist_to_redis(self) -> None:
        """持久化状态到 Redis"""
        if not self.redis:
            return

        key = f"three_file:{self.session_id}"
        data = {
            "progress": {
                "phase": self._progress.phase,
                "total_actions": self._progress.total_actions,
                "successful_actions": self._progress.successful_actions,
                "failed_actions": self._progress.failed_actions,
                "findings_written": self._progress.findings_written,
                "errors": self._progress.errors,
            },
            "timestamp": datetime.now().isoformat()
        }

        await self.redis.set(key, json.dumps(data), ex=86400)  # 24h TTL


# ==================== Agent 集成 Hook ====================

class AgentHookManager:
    """Agent Hook 管理器

    集成到 BaseAgent，自动触发三文件写入
    """

    def __init__(self, agent):
        self.agent = agent
        self.writer: ThreeFileAutoWriter | None = None

    def setup(
        self,
        session_id: str,
        workspace_path: str,
        redis_client = None
    ) -> None:
        """设置自动写入器"""
        self.writer = ThreeFileAutoWriter(
            session_id=session_id,
            workspace_path=workspace_path,
            redis_client=redis_client
        )

    async def pre_tool_call(self, tool_name: str, params: dict[str, Any]) -> None:
        """工具调用前 Hook"""
        if self.writer:
            await self.writer.on_tool_call(tool_name, params)

    async def post_tool_call(
        self,
        tool_name: str,
        params: dict[str, Any],
        result: Any,
        success: bool,
        error: str | None = None,
        duration_ms: int | None = None
    ) -> None:
        """工具调用后 Hook"""
        if self.writer:
            await self.writer.on_tool_result(
                tool_name=tool_name,
                params=params,
                result=result,
                success=success,
                error=error,
                duration_ms=duration_ms
            )

    async def on_phase_change(self, new_phase: str) -> None:
        """阶段变更 Hook"""
        if self.writer:
            await self.writer.on_phase_change(new_phase)

    async def on_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None
    ) -> None:
        """错误 Hook"""
        if self.writer:
            await self.writer.on_error(error_type, error_message, context)

    async def on_session_end(self, status: str = "completed") -> None:
        """Session 结束 Hook"""
        if self.writer:
            await self.writer.on_session_end(status)


# ==================== 装饰器辅助 ====================

def auto_record_tool(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """工具自动记录装饰器

    Usage:
        @auto_record_tool
        async def web_search(self, query: str) -> ToolResult:
            ...
    """
    async def wrapper(self, *args, **kwargs):
        tool_name = func.__name__
        params = kwargs.copy()

        # 获取 hook manager (假设 agent 有此属性)
        hook_manager = getattr(self, '_hook_manager', None)

        start_time = datetime.now()
        try:
            if hook_manager:
                await hook_manager.pre_tool_call(tool_name, params)

            result = await func(self, *args, **kwargs)

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if hook_manager:
                await hook_manager.post_tool_call(
                    tool_name=tool_name,
                    params=params,
                    result=result,
                    success=True,
                    duration_ms=duration_ms
                )

            return result

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            if hook_manager:
                await hook_manager.post_tool_call(
                    tool_name=tool_name,
                    params=params,
                    result=None,
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms
                )

            raise

    return wrapper
