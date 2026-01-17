"""
Context Compression - Context 压缩机制

当 context 使用率超过 70% 时自动压缩，避免突然因窗口满而失败

核心功能：
1. 摘要早期对话
2. 清理过期 findings
3. 压缩工具执行历史
4. 生成中间总结

参考：AGENT_ROBUSTNESS_ASSESSMENT.md - 阶段 1.2
"""

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CompressionResult:
    """压缩结果"""
    strategy_used: str  # 使用的压缩策略
    tokens_before: int  # 压缩前的 token 数
    tokens_after: int  # 压缩后的 token 数
    tokens_saved: int  # 节省的 token 数
    compression_ratio: float  # 压缩比
    items_compressed: int  # 压缩的项目数


class ContextCompressor:
    """Context 压缩器

    自动压缩 Context 以避免窗口溢出
    """

    # 压缩阈值
    COMPRESSION_THRESHOLD = 0.70  # Context 使用率超过 70% 触发
    AGGRESSIVE_THRESHOLD = 0.85  # 使用率超过 85% 使用激进压缩

    # 消息优先级（用于决定保留哪些消息）
    MESSAGE_PRIORITY = {
        "system": 100,  # 系统消息最高优先级
        "user": 90,  # 用户消息高优先级
        "assistant": 50,  # 助手响应中等优先级
        "tool_result": 30,  # 工具结果低优先级
    }

    def __init__(
        self,
        context_window_limit: int = 200_000,
        min_messages_to_keep: int = 10,
    ):
        """初始化 Context 压缩器

        Args:
            context_window_limit: Context 窗口大小限制
            min_messages_to_keep: 最少保留的消息数
        """
        self.context_window_limit = context_window_limit
        self.min_messages_to_keep = min_messages_to_keep

        logger.info(
            f"ContextCompressor initialized: "
            f"limit={context_window_limit}, min_keep={min_messages_to_keep}"
        )

    def should_compress(self, current_tokens: int) -> tuple[bool, str]:
        """判断是否应该压缩

        Args:
            current_tokens: 当前使用的 token 数

        Returns:
            tuple[bool, str]: (是否压缩, 压缩策略)
        """
        usage_ratio = current_tokens / self.context_window_limit

        if usage_ratio >= self.AGGRESSIVE_THRESHOLD:
            return True, "aggressive"
        elif usage_ratio >= self.COMPRESSION_THRESHOLD:
            return True, "normal"
        else:
            return False, "none"

    def compress(
        self,
        messages: list[dict[str, Any]],
        current_tokens: int,
        strategy: str = "normal",
    ) -> tuple[list[dict[str, Any]], CompressionResult]:
        """压缩消息列表

        Args:
            messages: 消息列表
            current_tokens: 当前 token 数
            strategy: 压缩策略 ("normal" 或 "aggressive")

        Returns:
            tuple[List[Dict], CompressionResult]: (压缩后的消息, 压缩结果)
        """
        logger.info(f"Starting compression with strategy: {strategy}")

        if strategy == "aggressive":
            compressed_messages, result = self._aggressive_compress(messages, current_tokens)
        else:
            compressed_messages, result = self._normal_compress(messages, current_tokens)

        logger.info(
            f"Compression completed: {result.tokens_before} → {result.tokens_after} tokens "
            f"(saved {result.tokens_saved}, ratio {result.compression_ratio:.2%})"
        )

        return compressed_messages, result

    def _normal_compress(
        self,
        messages: list[dict[str, Any]],
        current_tokens: int,
    ) -> tuple[list[dict[str, Any]], CompressionResult]:
        """常规压缩策略

        策略：
        1. 摘要早期对话（保留最近 50% 的消息）
        2. 压缩工具执行历史（合并连续的工具调用）
        3. 清理冗余内容
        """
        compressed = []
        items_compressed = 0

        # 保留最近 50% 的消息
        keep_count = max(len(messages) // 2, self.min_messages_to_keep)
        early_messages = messages[:-keep_count]
        recent_messages = messages[-keep_count:]

        # 对早期消息进行摘要
        if early_messages:
            summary = self._summarize_messages(early_messages)
            compressed.append({
                "role": "system",
                "content": f"[早期对话摘要]\n{summary}",
                "metadata": {"compressed": True, "original_count": len(early_messages)}
            })
            items_compressed += len(early_messages)

        # 保留最近的消息
        compressed.extend(recent_messages)

        # 估算压缩后的 token 数（粗略估计：摘要约为原文的 20%）
        tokens_after = int(current_tokens * 0.6)  # 压缩约 40%
        tokens_saved = current_tokens - tokens_after

        result = CompressionResult(
            strategy_used="normal",
            tokens_before=current_tokens,
            tokens_after=tokens_after,
            tokens_saved=tokens_saved,
            compression_ratio=tokens_saved / current_tokens if current_tokens > 0 else 0,
            items_compressed=items_compressed,
        )

        return compressed, result

    def _aggressive_compress(
        self,
        messages: list[dict[str, Any]],
        current_tokens: int,
    ) -> tuple[list[dict[str, Any]], CompressionResult]:
        """激进压缩策略

        策略：
        1. 只保留最近 20% 的消息
        2. 工具结果只保留最终状态
        3. 生成全局摘要
        """
        compressed = []
        items_compressed = 0

        # 只保留最近 20% 的消息
        keep_count = max(len(messages) // 5, self.min_messages_to_keep)
        early_messages = messages[:-keep_count]
        recent_messages = messages[-keep_count:]

        # 生成全局摘要
        if early_messages:
            summary = self._summarize_messages(early_messages, aggressive=True)
            compressed.append({
                "role": "system",
                "content": f"[对话历史摘要]\n{summary}",
                "metadata": {"compressed": True, "original_count": len(early_messages), "aggressive": True}
            })
            items_compressed += len(early_messages)

        # 压缩最近消息中的工具结果
        for msg in recent_messages:
            if msg.get("role") == "tool_result":
                # 只保留成功/失败状态和关键信息
                compressed_msg = self._compress_tool_result(msg)
                compressed.append(compressed_msg)
            else:
                compressed.append(msg)

        # 估算压缩后的 token 数（激进压缩约 60%）
        tokens_after = int(current_tokens * 0.4)
        tokens_saved = current_tokens - tokens_after

        result = CompressionResult(
            strategy_used="aggressive",
            tokens_before=current_tokens,
            tokens_after=tokens_after,
            tokens_saved=tokens_saved,
            compression_ratio=tokens_saved / current_tokens if current_tokens > 0 else 0,
            items_compressed=items_compressed,
        )

        return compressed, result

    def _summarize_messages(
        self,
        messages: list[dict[str, Any]],
        aggressive: bool = False,
    ) -> str:
        """摘要消息列表

        Args:
            messages: 消息列表
            aggressive: 是否使用激进摘要

        Returns:
            str: 摘要文本
        """
        if not messages:
            return "无早期对话"

        # 统计消息类型
        user_messages = [m for m in messages if m.get("role") == "user"]
        assistant_messages = [m for m in messages if m.get("role") == "assistant"]
        tool_results = [m for m in messages if m.get("role") == "tool_result"]

        summary_parts = [
            f"早期对话包含 {len(messages)} 条消息：",
            f"- 用户输入: {len(user_messages)} 条",
            f"- Agent 响应: {len(assistant_messages)} 条",
            f"- 工具执行: {len(tool_results)} 条",
        ]

        if not aggressive and user_messages:
            # 常规模式：列出用户的关键问题
            summary_parts.append("\n关键用户输入：")
            for i, msg in enumerate(user_messages[:3], 1):  # 只保留前 3 条
                content = msg.get("content", "")[:100]  # 截断到 100 字符
                summary_parts.append(f"{i}. {content}...")

        return "\n".join(summary_parts)

    def _compress_tool_result(self, tool_result: dict[str, Any]) -> dict[str, Any]:
        """压缩工具结果

        只保留状态和关键信息，移除详细输出

        Args:
            tool_result: 工具结果消息

        Returns:
            Dict: 压缩后的工具结果
        """
        content = tool_result.get("content", "")

        # 提取状态信息
        if "成功" in content or "Success" in content:
            status = "✅ 成功"
        elif "失败" in content or "Error" in content:
            status = "❌ 失败"
        else:
            status = "⚠️ 未知"

        # 提取工具名称
        tool_name = tool_result.get("metadata", {}).get("tool_name", "unknown")

        return {
            "role": "tool_result",
            "content": f"[工具结果] {tool_name}: {status}",
            "metadata": {
                **tool_result.get("metadata", {}),
                "compressed": True,
            }
        }

    def cleanup_outdated_findings(
        self,
        findings: str,
        cutoff_hours: int = 24,
    ) -> str:
        """清理过期的 findings

        移除超过指定时间的 findings 条目

        Args:
            findings: findings.md 内容
            cutoff_hours: 截断时间（小时）

        Returns:
            str: 清理后的 findings
        """
        # TODO: 实现基于时间戳的清理逻辑
        # 当前简化版：如果 findings 过长，保留最后 50%

        max_length = 10000  # 最大字符数
        if len(findings) <= max_length:
            return findings

        lines = findings.split("\n")
        keep_lines = len(lines) // 2

        cleaned = "\n".join(lines[-keep_lines:])
        logger.info(f"Cleaned outdated findings: {len(lines)} → {keep_lines} lines")

        return cleaned

    def generate_intermediate_summary(
        self,
        messages: list[dict[str, Any]],
        current_iteration: int,
    ) -> str:
        """生成中间总结

        在长时间运行时生成阶段性总结

        Args:
            messages: 消息列表
            current_iteration: 当前迭代次数

        Returns:
            str: 中间总结
        """
        summary_parts = [
            f"## 中间总结 (迭代 {current_iteration})",
            "",
            f"总消息数: {len(messages)}",
        ]

        # 统计工具使用
        tool_calls = [m for m in messages if m.get("role") == "tool_result"]
        if tool_calls:
            summary_parts.append(f"工具调用: {len(tool_calls)} 次")

        # 提取最近的进展
        recent_user_msgs = [
            m for m in messages[-10:]
            if m.get("role") == "user"
        ]
        if recent_user_msgs:
            summary_parts.append("\n最近进展:")
            for msg in recent_user_msgs[-3:]:
                content = msg.get("content", "")[:80]
                summary_parts.append(f"- {content}...")

        return "\n".join(summary_parts)

    def get_compression_stats(self) -> dict[str, Any]:
        """获取压缩器统计信息

        Returns:
            Dict: 统计信息
        """
        return {
            "context_window_limit": self.context_window_limit,
            "compression_threshold": self.COMPRESSION_THRESHOLD,
            "aggressive_threshold": self.AGGRESSIVE_THRESHOLD,
            "min_messages_to_keep": self.min_messages_to_keep,
        }
