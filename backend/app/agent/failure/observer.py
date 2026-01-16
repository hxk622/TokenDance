"""
Failure Observer - 失败观察者

实现 Keep the Failures 原则：
- 所有失败都被记录到 progress.md
- 同类失败3次触发 3-Strike Protocol
- 失败信息反馈到 Context 用于学习

参考文档：docs/architecture/Agent-Runtime-Design.md
"""

from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .signal import FailureSignal, FailureSummary, FailureType, ExitCode


logger = logging.getLogger(__name__)


# 失败事件回调类型
FailureCallback = Callable[[FailureSignal], None]


@dataclass
class FailureObserver:
    """失败观察者 - 让失败成为学习信号
    
    职责：
    1. 收集所有失败信号
    2. 记录到 progress.md (Keep the Failures)
    3. 检测 3-Strike Pattern
    4. 提供失败摘要用于 Plan Recitation
    """
    
    # 失败摘要（用于追加到 Context）
    summary: FailureSummary = field(default_factory=FailureSummary)
    
    # 所有失败历史（用于分析）
    all_failures: List[FailureSignal] = field(default_factory=list)
    
    # 3-Strike 阈值
    strike_threshold: int = 3
    
    # 回调列表
    _callbacks: List[FailureCallback] = field(default_factory=list)
    
    # progress.md 写入器（延迟注入）
    _progress_writer: Optional[Callable[[str], None]] = None
    
    def observe(self, signal: FailureSignal) -> Dict[str, Any]:
        """观察一个失败信号
        
        Returns:
            包含观察结果的字典：
            - recorded: 是否已记录
            - trigger_3_strike: 是否触发 3-Strike
            - should_escalate: 是否需要升级处理
        """
        result = {
            "recorded": False,
            "trigger_3_strike": False,
            "should_escalate": False,
            "learning": "",
        }
        
        # 记录所有信号（无论成功失败）
        self.all_failures.append(signal)
        
        # 只处理失败信号
        if signal.is_success():
            logger.debug(f"Success signal from {signal.tool_name}")
            return result
        
        # 添加到摘要
        self.summary.add(signal)
        result["recorded"] = True
        result["learning"] = signal.get_learning()
        
        # 写入 progress.md
        self._write_to_progress(signal)
        
        # 检查 3-Strike
        if self.summary.should_trigger_3_strike(signal):
            result["trigger_3_strike"] = True
            logger.warning(
                f"3-Strike triggered for {signal.failure_type.value}"
                f" (tool: {signal.tool_name})"
            )
        
        # 判断是否需要升级
        if signal.exit_code == ExitCode.NEED_USER.value:
            result["should_escalate"] = True
        elif signal.exit_code == ExitCode.FATAL.value:
            result["should_escalate"] = True
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Failure callback error: {e}")
        
        return result
    
    def register_callback(self, callback: FailureCallback) -> None:
        """注册失败回调"""
        self._callbacks.append(callback)
    
    def set_progress_writer(self, writer: Callable[[str], None]) -> None:
        """设置 progress.md 写入器
        
        通常由 ThreeFilesManager 提供
        """
        self._progress_writer = writer
    
    def _write_to_progress(self, signal: FailureSignal) -> None:
        """写入到 progress.md (Keep the Failures)"""
        if self._progress_writer:
            entry = signal.to_progress_entry()
            try:
                self._progress_writer(entry)
            except Exception as e:
                logger.error(f"Failed to write to progress.md: {e}")
        else:
            # 如果没有写入器，至少记录日志
            logger.info(f"Failure: {signal.to_progress_entry()}")
    
    def get_failure_summary_for_context(self) -> str:
        """获取失败摘要（用于 Plan Recitation）
        
        返回格式化的 Markdown，追加到 Context 末尾
        """
        return self.summary.to_markdown()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取失败统计"""
        total = len(self.all_failures)
        failures = [f for f in self.all_failures if not f.is_success()]
        
        # 按类型统计
        by_type: Dict[str, int] = {}
        for f in failures:
            key = f.failure_type.value
            by_type[key] = by_type.get(key, 0) + 1
        
        # 按工具统计
        by_tool: Dict[str, int] = {}
        for f in failures:
            if f.tool_name:
                by_tool[f.tool_name] = by_tool.get(f.tool_name, 0) + 1
        
        return {
            "total_signals": total,
            "total_failures": len(failures),
            "success_rate": (total - len(failures)) / total if total > 0 else 1.0,
            "by_type": by_type,
            "by_tool": by_tool,
            "recent_failures": [f.to_dict() for f in self.summary.recent_failures],
        }
    
    def has_repeated_failure(self, failure_type: FailureType, min_count: int = 2) -> bool:
        """检查是否有重复失败"""
        return self.summary.get_same_type_count(failure_type) >= min_count
    
    def get_most_common_failure(self) -> Optional[FailureType]:
        """获取最常见的失败类型"""
        stats = self.get_statistics()
        by_type = stats["by_type"]
        
        if not by_type:
            return None
        
        max_type = max(by_type.keys(), key=lambda k: by_type[k])
        return FailureType(max_type)
    
    def clear(self) -> None:
        """清空所有失败记录"""
        self.summary.clear()
        self.all_failures = []
    
    def should_stop_retry(self, signal: FailureSignal) -> bool:
        """判断是否应该停止重试
        
        基于 3-Strike Protocol：
        - 同类失败 >= 3 次
        - 或 exit_code == FATAL
        """
        if signal.exit_code == ExitCode.FATAL.value:
            return True
        
        return self.summary.should_trigger_3_strike(signal)
    
    def get_retry_suggestion(self, signal: FailureSignal) -> str:
        """获取重试建议"""
        if not signal.is_retryable():
            return "此错误不可重试，需要人工介入"
        
        same_type_count = self.summary.get_same_type_count(signal.failure_type)
        
        if same_type_count >= self.strike_threshold:
            return f"同类错误已出现 {same_type_count} 次，建议更换策略或人工介入"
        
        remaining = self.strike_threshold - same_type_count
        return f"可以重试，还剩 {remaining} 次机会"


class FailureReporter:
    """失败报告生成器
    
    生成用户友好的失败报告
    """
    
    @staticmethod
    def generate_report(observer: FailureObserver) -> str:
        """生成失败报告"""
        stats = observer.get_statistics()
        
        if stats["total_failures"] == 0:
            return "✅ 本次执行没有错误"
        
        lines = [
            "## 执行报告",
            "",
            f"**总操作数**: {stats['total_signals']}",
            f"**失败次数**: {stats['total_failures']}",
            f"**成功率**: {stats['success_rate']:.1%}",
            "",
        ]
        
        if stats["by_type"]:
            lines.append("### 按错误类型")
            for type_name, count in sorted(stats["by_type"].items(), key=lambda x: -x[1]):
                lines.append(f"- {type_name}: {count}")
            lines.append("")
        
        if stats["by_tool"]:
            lines.append("### 按工具")
            for tool_name, count in sorted(stats["by_tool"].items(), key=lambda x: -x[1]):
                lines.append(f"- {tool_name}: {count}")
            lines.append("")
        
        # 添加学习建议
        most_common = observer.get_most_common_failure()
        if most_common:
            lines.append("### 主要问题")
            lines.append(f"最常见错误: **{most_common.value}**")
            
            # 获取对应的学习建议
            sample_signal = FailureSignal(
                source=FailureSignal.source,  # type: ignore
                failure_type=most_common,
                exit_code=1,
                error_message="",
            )
            lines.append(f"建议: {sample_signal.get_learning()}")
        
        return "\n".join(lines)
