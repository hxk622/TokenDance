"""
Failure Pattern Knowledge Base - 失败模式知识库

跨 session 记录和复用失败→修复的经验。
数据保存在 workspace/shared/knowledge_base/failure_patterns.json。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime

from app.filesystem.agent_fs import AgentFileSystem

from .signal import FailureSignal


@dataclass
class FailurePattern:
    signature: str
    category: str
    sample_error: str
    occurrences: int = 0
    successful_fixes: list[str] = None
    last_seen: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["successful_fixes"] = self.successful_fixes or []
        return d


class FailurePatternKB:
    """简单的 JSON 文件知识库。"""

    KB_PATH = "shared/knowledge_base/failure_patterns.json"

    def __init__(self, fs: AgentFileSystem):
        self.fs = fs
        self._cache: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.fs.exists(self.KB_PATH):
                raw = self.fs.read(self.KB_PATH)
                self._cache = json.loads(raw) or {}
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _save(self) -> None:
        try:
            self.fs.write(self.KB_PATH, json.dumps(self._cache, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def _signature(self, signal: FailureSignal) -> str:
        base = signal.failure_type.value
        tool = signal.tool_name or "unknown"
        # 简易签名：类型 + 工具 + 关键错误词（前 50 字符）
        msg = (signal.error_message or "").lower().strip()[:50]
        return f"{base}:{tool}:{msg}"

    def record(self, signal: FailureSignal) -> None:
        if signal.is_success():
            return
        sig = self._signature(signal)
        now = datetime.utcnow().isoformat() + "Z"
        if sig not in self._cache:
            self._cache[sig] = FailurePattern(
                signature=sig,
                category=signal.failure_type.value,
                sample_error=signal.error_message or "",
                occurrences=1,
                successful_fixes=[],
                last_seen=now,
            ).to_dict()
        else:
            item = self._cache[sig]
            item["occurrences"] = int(item.get("occurrences", 0)) + 1
            item["last_seen"] = now
        self._save()

    def record_success_fix(self, signal: FailureSignal, fix_summary: str) -> None:
        sig = self._signature(signal)
        if sig not in self._cache:
            return
        fixes = self._cache[sig].setdefault("successful_fixes", [])
        if fix_summary not in fixes:
            fixes.append(fix_summary)
            self._save()

    def get_solution(self, signal: FailureSignal) -> str | None:
        sig = self._signature(signal)
        item = self._cache.get(sig)
        if not item:
            return None
        fixes = item.get("successful_fixes") or []
        return fixes[0] if fixes else None

    def stats(self) -> dict:
        return {
            "count": len(self._cache),
            "items": list(self._cache.values())[:50],
        }
