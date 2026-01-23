"""
InfiniteMemoryManager - Manus 无限记忆模式核心实现

设计原则：
1. 文件系统是无限记忆，Context 只是工作台
2. 中间结果写入文件，只将摘要加载到 Context
3. 支持从文件恢复状态（检查点/崩溃恢复）

核心流程：
1. Agent 执行过程中，所有中间结果写入 findings.md
2. 当 Context 接近阈值时，清理旧消息，用文件摘要替代
3. 崩溃/恢复时，从文件读取状态而非依赖内存

参考：Manus Agent 核心架构原则
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.agent.working_memory.three_files import ThreeFilesManager
from app.filesystem import AgentFileSystem

logger = logging.getLogger(__name__)


@dataclass
class ResearchStateSnapshot:
    """研究状态快照（从文件恢复）"""
    topic: str
    phase: str
    sources_count: int
    queries_executed: list[str]
    knowledge_gaps: list[str]
    findings_summary: str
    last_activity: str | None = None


@dataclass
class ContextInjection:
    """Context 注入内容"""
    summary: str
    recent_findings: str
    current_objective: str
    token_estimate: int


@dataclass
class InfiniteMemoryConfig:
    """无限记忆配置"""
    # Context 清理阈值
    context_clear_threshold: int = 15  # 超过 15 条消息触发清理
    context_token_threshold: int = 50000  # 超过 50K tokens 触发清理

    # 摘要配置
    summary_max_length: int = 3000  # 摘要最大长度
    recent_messages_to_keep: int = 5  # 清理后保留最近 N 条消息

    # 自动保存配置
    auto_save_interval: int = 2  # 每 2 次操作自动保存

    # 检查点配置
    checkpoint_interval: int = 5  # 每 5 次迭代保存检查点


class InfiniteMemoryManager:
    """
    无限记忆管理器（Manus 模式核心）

    职责：
    1. 管理文件作为无限记忆存储
    2. 决定何时清理 Context
    3. 生成 Context 注入内容
    4. 支持从文件恢复状态
    """

    # 状态文件名
    STATE_FILE = "agent_state.json"

    def __init__(
        self,
        three_files: ThreeFilesManager,
        filesystem: AgentFileSystem,
        session_id: str,
        config: InfiniteMemoryConfig | None = None,
    ):
        """
        初始化无限记忆管理器

        Args:
            three_files: 三文件管理器
            filesystem: 文件系统
            session_id: Session ID
            config: 配置
        """
        self.three_files = three_files
        self.filesystem = filesystem
        self.session_id = session_id
        self.config = config or InfiniteMemoryConfig()

        # 操作计数器（用于 2-Action Rule）
        self._operation_count = 0

        # 状态文件路径
        self._state_path = f"sessions/{session_id}/{self.STATE_FILE}"

        logger.info(f"InfiniteMemoryManager initialized for session {session_id}")

    # ========== 核心接口 ==========

    def should_clear_context(
        self,
        message_count: int,
        token_count: int | None = None,
    ) -> bool:
        """
        判断是否应该清理 Context（Manus 核心逻辑）

        条件（满足任一即清理）：
        1. 消息数超过阈值
        2. Token 数超过阈值
        3. Findings 需要压缩

        Args:
            message_count: 当前消息数
            token_count: 当前 token 数（可选）

        Returns:
            bool: 是否应该清理
        """
        # 条件 1: 消息数
        if message_count > self.config.context_clear_threshold:
            logger.info(f"Context clear triggered: message_count={message_count}")
            return True

        # 条件 2: Token 数
        if token_count and token_count > self.config.context_token_threshold:
            logger.info(f"Context clear triggered: token_count={token_count}")
            return True

        # 条件 3: Findings 需要压缩
        if self.three_files.should_generate_summary():
            logger.info("Context clear triggered: findings needs summary")
            return True

        return False

    def get_context_injection(self) -> ContextInjection:
        """
        获取应注入到 Context 的内容（替代完整历史）

        这是 Manus 模式的核心：用文件摘要替代消息历史

        Returns:
            ContextInjection: 注入内容
        """
        # 获取累积摘要
        summary = self.three_files.get_accumulated_summary()

        # 获取最近的 findings
        recent_findings = self._get_recent_findings()

        # 获取当前目标
        current_objective = self._get_current_objective()

        # 估算 token 数（粗略：4 字符 ≈ 1 token）
        total_text = summary + recent_findings + current_objective
        token_estimate = len(total_text) // 4

        return ContextInjection(
            summary=summary,
            recent_findings=recent_findings,
            current_objective=current_objective,
            token_estimate=token_estimate,
        )

    def save_intermediate_result(
        self,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        保存中间结果到文件（2-Action Rule 实现）

        Args:
            title: 结果标题
            content: 结果内容
            metadata: 元数据
        """
        # 追加到 findings.md
        finding_text = content
        if metadata:
            meta_str = "\n".join(f"- **{k}**: {v}" for k, v in metadata.items())
            finding_text = f"{meta_str}\n\n{content}"

        self.three_files.update_findings(f"**{title}**\n\n{finding_text}")

        # 更新操作计数器
        self._operation_count += 1

        # 检查是否需要压缩
        if self._operation_count >= self.config.auto_save_interval:
            self._operation_count = 0
            self._maybe_compress_findings()

        logger.debug(f"Intermediate result saved: {title}")

    def restore_from_files(self) -> ResearchStateSnapshot | None:
        """
        从文件恢复研究状态（崩溃恢复核心）

        流程：
        1. 读取 agent_state.json（如果存在）
        2. 解析 findings.md 提取状态
        3. 返回状态快照

        Returns:
            ResearchStateSnapshot: 状态快照，如果无法恢复返回 None
        """
        try:
            # 尝试从状态文件恢复
            if self.filesystem.exists(self._state_path):
                state_content = self.filesystem.read(self._state_path)
                state_data = json.loads(state_content)
                return ResearchStateSnapshot(**state_data)

            # 从 findings.md 推断状态
            return self._infer_state_from_findings()

        except Exception as e:
            logger.warning(f"Failed to restore state: {e}")
            return None

    def save_state(self, state: dict[str, Any]) -> None:
        """
        保存当前状态到文件

        Args:
            state: 状态数据
        """
        try:
            state["last_saved"] = datetime.now().isoformat()
            self.filesystem.write(
                self._state_path,
                json.dumps(state, indent=2, ensure_ascii=False)
            )
            logger.debug("State saved to file")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def clear_and_summarize(self) -> str:
        """
        清理 Context 并生成替代摘要（Manus 核心操作）

        流程：
        1. 先保存当前状态到文件
        2. 压缩 findings 如果需要
        3. 返回应注入到 Context 的摘要

        Returns:
            str: 应注入到新 Context 的摘要
        """
        # 1. 压缩 findings
        self._maybe_compress_findings()

        # 2. 生成替代摘要
        injection = self.get_context_injection()

        # 3. 记录到 progress.md
        self.three_files.update_progress(
            "Context cleared and summarized (Manus infinite memory mode)"
        )

        logger.info("Context cleared and summarized")
        return injection.summary

    # ========== 内部方法 ==========

    def _get_recent_findings(self, max_length: int = 500) -> str:
        """获取最近的 findings"""
        try:
            findings_data = self.three_files.read_findings()
            content = findings_data.get("content", "")

            # 取最后 max_length 字符
            if len(content) > max_length:
                return "..." + content[-max_length:]
            return content
        except Exception:
            return ""

    def _get_current_objective(self) -> str:
        """获取当前目标"""
        try:
            task_plan = self.three_files.read_task_plan()
            content = task_plan.get("content", "")

            # 提取目标部分（假设在 ## 目标 或 ## Goal 下）
            lines = content.split("\n")
            in_goal_section = False
            goal_lines = []

            for line in lines:
                if line.strip().startswith("## 目标") or line.strip().startswith("## Goal"):
                    in_goal_section = True
                    continue
                elif line.strip().startswith("##"):
                    if in_goal_section:
                        break
                elif in_goal_section:
                    goal_lines.append(line)

            goal = "\n".join(goal_lines).strip()
            return goal[:300] if goal else "No specific objective defined."

        except Exception:
            return "No objective available."

    def _maybe_compress_findings(self) -> None:
        """如果需要，压缩 findings"""
        if self.three_files.should_generate_summary():
            self.three_files.trim_findings_to_summary()
            logger.info("Findings compressed to summary")

    def _infer_state_from_findings(self) -> ResearchStateSnapshot | None:
        """从 findings.md 推断研究状态"""
        try:
            findings_data = self.three_files.read_findings()
            content = findings_data.get("content", "")

            if not content or len(content) < 50:
                return None

            # 解析 findings 条目
            entries = self.three_files._parse_findings_entries(content)

            # 提取查询
            queries = []
            for entry in entries:
                title = entry.get("title", "")
                if "search" in title.lower() or "搜索" in title:
                    queries.append(title)

            # 从 task_plan 获取主题
            task_plan = self.three_files.read_task_plan()
            plan_content = task_plan.get("content", "")
            topic = self._extract_topic_from_plan(plan_content)

            # 推断阶段
            phase = self._infer_phase(entries)

            return ResearchStateSnapshot(
                topic=topic,
                phase=phase,
                sources_count=len(entries),
                queries_executed=queries[-10:],  # 最近 10 个查询
                knowledge_gaps=[],  # 无法从文件推断
                findings_summary=self.three_files.generate_findings_summary(max_length=1000),
                last_activity=entries[-1].get("timestamp") if entries else None,
            )

        except Exception as e:
            logger.warning(f"Failed to infer state from findings: {e}")
            return None

    def _extract_topic_from_plan(self, plan_content: str) -> str:
        """从 task_plan 提取主题"""
        lines = plan_content.split("\n")
        for line in lines:
            if line.strip() and not line.startswith("#"):
                return line.strip()[:100]
        return "Unknown topic"

    def _infer_phase(self, entries: list[dict]) -> str:
        """根据 findings 条目推断当前阶段"""
        if not entries:
            return "init"

        count = len(entries)
        if count < 3:
            return "searching"
        elif count < 8:
            return "reading"
        elif count < 15:
            return "synthesizing"
        else:
            return "reporting"

    # ========== 辅助方法 ==========

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        findings_stats = self.three_files.get_findings_stats()
        return {
            "session_id": self.session_id,
            "operation_count": self._operation_count,
            "findings_stats": findings_stats,
            "config": {
                "context_clear_threshold": self.config.context_clear_threshold,
                "context_token_threshold": self.config.context_token_threshold,
                "auto_save_interval": self.config.auto_save_interval,
            },
        }

    def record_action(self, action_type: str, details: str) -> bool:
        """
        记录操作（兼容 2-Action Rule）

        Args:
            action_type: 操作类型
            details: 详情

        Returns:
            bool: 是否应该写入 findings
        """
        return self.three_files.record_action(action_type, {"details": details})
