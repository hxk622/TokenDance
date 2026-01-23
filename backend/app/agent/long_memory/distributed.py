"""
Distributed Memory - 简易跨 session 记忆系统

将经验教训 Lessons 存入 workspace/context/learnings.md，并在新任务时按关键词回忆。
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.datetime_utils import utc_now_naive
from app.filesystem.agent_fs import AgentFileSystem


@dataclass
class Lesson:
    title: str
    summary: str
    tags: list[str]
    created_at: str

    def to_markdown(self) -> str:
        tags = ", ".join(self.tags)
        return f"### {self.title}\n- tags: {tags}\n- created_at: {self.created_at}\n\n{self.summary}\n"


class DistributedMemory:
    """将 Lessons 以 Markdown 形式追加存储，并提供简单的关键词召回。"""

    PATH = "context/learnings.md"

    def __init__(self, fs: AgentFileSystem):
        self.fs = fs

    def store_lessons(self, lessons: list[Lesson]) -> None:
        body = ""
        for lesson in lessons:
            body += lesson.to_markdown() + "\n"
        if self.fs.exists(self.PATH):
            prev = self.fs.read(self.PATH)
            content = prev + "\n" + body
        else:
            header = "# Learnings\n\n" + f"> updated_at: {utc_now_naive().isoformat()}Z\n\n"
            content = header + body
        self.fs.write(self.PATH, content)

    def recall(self, query: str, top_k: int = 5) -> list[str]:
        if not self.fs.exists(self.PATH):
            return []
        text = self.fs.read(self.PATH)
        # 极简召回：按标签/关键词匹配段落，按出现次数排序
        blocks = re.split(r"\n(?=### )", text)
        scored = []
        for b in blocks:
            score = b.lower().count(query.lower())
            if score > 0:
                scored.append((score, b.strip()))
        scored.sort(key=lambda x: -x[0])
        return [b for _, b in scored[:top_k]]
