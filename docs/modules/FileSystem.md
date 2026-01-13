# FileSystem 模块设计文档

> **核心理念**：文件系统是人类和 AI 最自然的协作界面
> Version: 1.0.0
> Last Updated: 2026-01-09

## 1. 设计哲学

### 1.1 Manus 的核心洞察

> "最好的上下文是文件系统，todo.md 是其灵魂"

**为什么文件系统是最好的上下文？**

1. **人类和 AI 都能理解的共享界面**
   - Agent 不需要"记住"之前做了什么，只需读取文件
   - 用户随时可以查看、修改、接管任务进度
   - 重启后 Agent 可以立即恢复工作状态

2. **天然的人机协作界面**
   - 用户可以直接编辑文件来调整优先级、删除任务、添加备注
   - Agent 通过监听文件变化来响应用户的修改
   - 透明、可审计、可干预

3. **零学习成本**
   - 不需要学习新的 UI/CLI，Markdown 人人都会
   - 任何文本编辑器都能操作
   - 可以用 git 进行版本控制

4. **简单但强大**
   - 文件系统是操作系统提供的最基础的持久化机制
   - 天然支持层级结构、权限管理、备份恢复
   - 与开发者工作流无缝集成（IDE、git、脚本）

### 1.2 设计原则

#### 原则 1：文件系统 = Source of Truth

```
┌───────────────────────────────────────────────────────────┐
│  设计决策：文件系统是唯一真相来源                          │
│                                                            │
│  文件系统 (Source of Truth)                               │
│      ↓ 单向同步                                            │
│  数据库 (Index + Cache)                                    │
│                                                            │
│  推论：                                                    │
│  - 所有状态首先写入文件                                    │
│  - 数据库作为索引和查询加速                                │
│  - 数据库崩溃不影响核心功能                                │
│  - 文件变化自动同步到数据库                                │
└───────────────────────────────────────────────────────────┘
```

#### 原则 2：Markdown 是最好的 DSL

```markdown
# Task: 实现用户认证功能

## 目标
实现 JWT-based 用户认证系统，包括注册、登录、Token 刷新。

## 当前进度
- [x] 设计数据库 Schema ✅ 10:05
- [x] 实现用户注册 API ✅ 10:10
- [ ] 实现登录 API （正在进行...）
  - [x] 验证用户名密码
  - [ ] 生成 JWT Token
  - [ ] 返回响应
- [ ] 实现 Token 刷新 API

## 决策记录
- **2026-01-09 10:05**: 使用 bcrypt 作为密码哈希算法
- **2026-01-09 10:08**: Token 有效期设置为 1 小时

## Agent 笔记
尝试使用 PyJWT 库实现 Token 生成，但遇到参数错误，已切换为 jose 库。
```

**优势**：
- ✅ 人类可读、可编辑
- ✅ Agent 可以解析、更新
- ✅ 支持层级结构（checklist 嵌套）
- ✅ 可以用 git 进行版本控制
- ✅ 支持内部链接（`[[other-file.md]]`）

#### 原则 3：监听式同步，而非轮询

```python
# ❌ 错误做法：轮询文件变化
while True:
    files = os.listdir("workspace/")
    check_for_changes(files)
    time.sleep(1)  # 浪费资源

# ✅ 正确做法：文件系统事件监听
from watchdog.observers import Observer

observer = Observer()
observer.schedule(event_handler, "workspace/", recursive=True)
observer.start()  # 零开销，事件驱动
```

#### 原则 4：YAML Frontmatter + Markdown Body

```markdown
---
id: task-001
title: 实现用户认证功能
status: in_progress
priority: high
created_at: 2026-01-09T10:00:00Z
updated_at: 2026-01-09T10:12:00Z
tags: [backend, auth, security]
---

# Task: 实现用户认证功能
...
```

**分工**：
- **Frontmatter**：结构化元数据，用于数据库索引和查询
- **Body**：人类可读内容，用于阅读和编辑

#### 原则 5：文件系统 = 无限大小的持久化内存

```
┌───────────────────────────────────────────────────────────┐
│  认知模型：双轨记忆系统                                    │
│                                                            │
│  工作记忆（KV-Cache）        长期记忆（FileSystem）       │
│  ┌─────────────────┐         ┌─────────────────┐          │
│  │ • 快速访问      │         │ • 无限容量      │          │
│  │ • 容量受限      │  ←换入→ │ • 持久化       │          │
│  │ • 易失性        │  换出   │ • 可审计        │          │
│  │ • ~100GB        │         │ • ~数TB         │          │
│  └─────────────────┘         └─────────────────┘          │
│                                                            │
│  设计原则：                                                │
│  1. Agent 学会主动读写文件作为结构化外部记忆               │
│  2. 大数据（>10KB）自动换出到文件系统                     │
│  3. KV-Cache 只保留摘要+文件路径（压缩指针）              │
│  4. 压缩策略必须可恢复（保留 URL/路径/检索提示）          │
└───────────────────────────────────────────────────────────┘
```

**核心思想**：

1. **Agent 自主决策**：Agent 自己判断何时将数据换出到文件系统
   ```python
   # Agent 的内在推理
   <|REASONING|>
   这个 API 响应有 50MB，会撑爆 KV-Cache。
   我应该：
   1. 把原始数据写入 workspace/cache/api_response_xxx.json
   2. 提取关键信息（500字）保留在 Context
   3. 在 Context 中记录文件路径，需要时再读取
   </|REASONING|>
   ```

2. **压缩指针（必须可恢复）**：
   ```python
   # ❌ 错误：丢失恢复路径
   compressed = "查询了天气数据并生成了报告"
   
   # ✅ 正确：保留完整恢复信息
   compressed = {
       "summary": "查询北京天气（晴，20°C）并生成诗歌",
       "file_path": "workspace/cache/weather_20260109.json",
       "original_url": "https://api.weather.com/v1/forecast?city=beijing",
       "retrieval_hints": ["weather", "beijing", "forecast", "poetry"],
       "size_bytes": 51200,
       "checksum": "a3f8b9c..."
   }
   ```

3. **智能阈值**：
   - < 1KB：保留在 KV-Cache
   - 1KB ~ 10KB：根据重要性决定
   - > 10KB：自动换出到文件系统
   - > 100KB：必须换出，只保留压缩指针

4. **文件系统目录规划**：
   ```bash
   workspace/
   ├── cache/              # 临时缓存（7天 TTL）
   │   ├── api_responses/
   │   ├── web_pages/
   │   └── intermediate_results/
   ├── context/            # 长期上下文
   │   ├── memory.md      # Agent 记忆
   │   └── learnings.md   # 学习经验
   └── shared/             # 跨任务共享
       └── knowledge_base/
   ```

---

## 2. 目录结构设计

### 2.1 Workspace 目录结构

```bash
workspace/                      # 工作区根目录
├── tasks/                      # 任务文件夹（Agent 核心工作单元）
│   ├── task-20260109-user-auth.md
│   ├── task-20260109-ppt-generation.md
│   └── archive/                # 已完成任务归档
│       └── task-20260108-setup-project.md
├── context/                    # 上下文文件夹（长期记忆）
│   ├── memory.md              # Agent 记忆（用户偏好、项目约定）
│   ├── learnings.md           # Agent 学习经验
│   └── rules.md               # 用户定义的行为规则
├── drafts/                     # Agent 生成的草稿
│   ├── research-report-v1.md
│   ├── ppt-outline-v2.md
│   └── api-spec-draft.md
├── logs/                       # 执行日志
│   ├── 2026-01-09.log
│   └── errors.log
└── .tokendance/                # 配置文件
    ├── config.yaml            # 工作区配置
    ├── connections.yaml       # MCP 连接配置
    └── db.sqlite              # 本地缓存数据库（可选）
```

### 2.2 文件命名规则

#### 任务文件命名

```
格式：task-{timestamp}-{slug}.md
示例：task-20260109101500-user-auth.md

说明：
- timestamp：YYYYMMDDHHmmss（保证唯一性）
- slug：任务标题的 kebab-case 形式（便于人类识别）
- 最大长度：50 字符
```

#### 上下文文件命名

```
固定命名：
- memory.md       # Agent 记忆
- learnings.md    # Agent 学习经验
- rules.md        # 用户规则
```

#### 草稿文件命名

```
格式：{type}-{slug}-v{version}.md
示例：research-report-ai-trends-v3.md

说明：
- type：文件类型（research-report, ppt-outline, api-spec）
- slug：内容描述
- version：版本号（自动递增）
```

---

## 3. 核心组件设计

### 3.1 FileManager 类

```python
# backend/app/filesystem/manager.py

from pathlib import Path
from typing import Dict, List, Optional
import yaml
import aiofiles

class FileManager:
    """文件系统管理器"""
    
    def __init__(self, workspace_root: str = "workspace/"):
        self.root = Path(workspace_root)
        self.tasks_dir = self.root / "tasks"
        self.context_dir = self.root / "context"
        self.drafts_dir = self.root / "drafts"
        self.logs_dir = self.root / "logs"
        self.config_dir = self.root / ".tokendance"
        
    async def initialize(self):
        """初始化工作区目录"""
        for dir_path in [
            self.tasks_dir,
            self.context_dir,
            self.drafts_dir,
            self.logs_dir,
            self.config_dir,
            self.tasks_dir / "archive"
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 创建默认上下文文件
        await self._create_default_files()
    
    async def _create_default_files(self):
        """创建默认上下文文件"""
        default_files = {
            "context/memory.md": """# Agent Memory

## 用户偏好

## 项目约定

## 技术栈
""",
            "context/learnings.md": """# Agent Learnings

## 过往经验

## 常见问题解决方案
""",
            "context/rules.md": """# User Rules

## 行为规则

## 禁止操作
"""
        }
        
        for rel_path, content in default_files.items():
            file_path = self.root / rel_path
            if not file_path.exists():
                async with aiofiles.open(file_path, "w") as f:
                    await f.write(content)
    
    def get_tasks_dir(self) -> Path:
        """获取任务目录"""
        return self.tasks_dir
    
    def get_context_dir(self) -> Path:
        """获取上下文目录"""
        return self.context_dir
    
    async def list_tasks(self, status: Optional[str] = None) -> List[Path]:
        """列出所有任务文件"""
        tasks = []
        for file_path in self.tasks_dir.glob("task-*.md"):
            if status:
                task_data = await TaskFile.read(file_path)
                if task_data["frontmatter"].get("status") == status:
                    tasks.append(file_path)
            else:
                tasks.append(file_path)
        return sorted(tasks, key=lambda p: p.stat().st_mtime, reverse=True)
```

### 3.2 TaskFile 类

```python
# backend/app/filesystem/task_file.py

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import yaml
import aiofiles
import re

class TaskFile:
    """任务文件的 CRUD 操作"""
    
    @staticmethod
    async def create(
        file_manager: FileManager,
        title: str,
        description: str,
        checklist: List[str],
        priority: str = "medium",
        tags: List[str] = []
    ) -> Path:
        """创建新任务文件"""
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower())[:30]
        filename = f"task-{timestamp}-{slug}.md"
        file_path = file_manager.tasks_dir / filename
        
        # 生成内容
        task_id = f"task-{timestamp}"
        frontmatter = {
            "id": task_id,
            "title": title,
            "status": "pending",
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": tags
        }
        
        checklist_md = "\n".join([f"- [ ] {item}" for item in checklist])
        
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

# Task: {title}

## 目标
{description}

## 当前进度
{checklist_md}

## 上下文
### 相关文件

### 相关文档

## 决策记录

## 问题与障碍

## Agent 笔记
"""
        
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
        
        return file_path
    
    @staticmethod
    async def read(file_path: Path) -> Dict:
        """读取任务文件"""
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
        
        # 解析 Frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            frontmatter = yaml.safe_load(parts[1])
            body = parts[2].strip()
        else:
            frontmatter = {}
            body = content
        
        return {
            "frontmatter": frontmatter,
            "body": body,
            "file_path": str(file_path)
        }
    
    @staticmethod
    async def update_status(file_path: Path, new_status: str):
        """更新任务状态"""
        task_data = await TaskFile.read(file_path)
        frontmatter = task_data["frontmatter"]
        body = task_data["body"]
        
        # 更新元数据
        frontmatter["status"] = new_status
        frontmatter["updated_at"] = datetime.now().isoformat()
        
        # 重新写入
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

{body}
"""
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
    
    @staticmethod
    async def mark_item_done(file_path: Path, item_text: str):
        """标记某个 checklist 项为完成"""
        task_data = await TaskFile.read(file_path)
        body = task_data["body"]
        
        # 替换 [ ] 为 [x]
        pattern = re.escape(f"- [ ] {item_text}")
        replacement = f"- [x] {item_text} ✅ {datetime.now().strftime('%H:%M')}"
        updated_body = re.sub(pattern, replacement, body)
        
        # 更新文件
        frontmatter = task_data["frontmatter"]
        frontmatter["updated_at"] = datetime.now().isoformat()
        
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

{updated_body}
"""
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
    
    @staticmethod
    async def append_note(file_path: Path, note: str):
        """追加 Agent 笔记"""
        task_data = await TaskFile.read(file_path)
        body = task_data["body"]
        
        # 在 "## Agent 笔记" 部分追加
        timestamp = datetime.now().strftime('%H:%M:%S')
        note_line = f"- **{timestamp}**: {note}"
        
        if "## Agent 笔记" in body:
            updated_body = body.replace(
                "## Agent 笔记",
                f"## Agent 笔记\n{note_line}"
            )
        else:
            updated_body = body + f"\n## Agent 笔记\n{note_line}"
        
        # 更新文件
        frontmatter = task_data["frontmatter"]
        frontmatter["updated_at"] = datetime.now().isoformat()
        
        content = f"""---
{yaml.dump(frontmatter, allow_unicode=True)}---

{updated_body}
"""
        async with aiofiles.open(file_path, "w") as f:
            await f.write(content)
    
    @staticmethod
    async def archive(file_path: Path, file_manager: FileManager):
        """归档已完成的任务"""
        archive_dir = file_manager.tasks_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        new_path = archive_dir / file_path.name
        file_path.rename(new_path)
        return new_path
```

### 3.3 ContextFile 类

```python
# backend/app/filesystem/context_file.py

from pathlib import Path
from typing import Optional
import aiofiles
import re

class ContextFile:
    """上下文文件操作（memory.md, learnings.md, rules.md）"""
    
    @staticmethod
    async def read(file_manager: FileManager, filename: str) -> str:
        """读取上下文文件"""
        file_path = file_manager.context_dir / filename
        
        if not file_path.exists():
            return ""
        
        async with aiofiles.open(file_path, "r") as f:
            return await f.read()
    
    @staticmethod
    async def append(file_manager: FileManager, filename: str, content: str):
        """追加内容到上下文文件"""
        file_path = file_manager.context_dir / filename
        
        async with aiofiles.open(file_path, "a") as f:
            await f.write(f"\n{content}\n")
    
    @staticmethod
    async def update_section(
        file_manager: FileManager,
        filename: str,
        section_name: str,
        content: str
    ):
        """更新上下文文件的某个章节"""
        file_path = file_manager.context_dir / filename
        
        # 读取现有内容
        existing_content = await ContextFile.read(file_manager, filename)
        
        # 查找章节位置
        section_pattern = f"## {section_name}"
        if section_pattern in existing_content:
            # 替换章节内容
            lines = existing_content.split("\n")
            new_lines = []
            in_target_section = False
            
            for line in lines:
                if line.strip() == section_pattern:
                    in_target_section = True
                    new_lines.append(line)
                    new_lines.append(content)
                elif line.startswith("## ") and in_target_section:
                    in_target_section = False
                    new_lines.append(line)
                elif not in_target_section:
                    new_lines.append(line)
            
            updated_content = "\n".join(new_lines)
        else:
            # 追加新章节
            updated_content = existing_content + f"\n## {section_name}\n{content}\n"
        
        # 写回文件
        async with aiofiles.open(file_path, "w") as f:
            await f.write(updated_content)
    
    @staticmethod
    async def set_preference(
        file_manager: FileManager,
        key: str,
        value: str
    ):
        """设置用户偏好"""
        content = f"- **{key}**: {value}"
        
        # 读取现有内容
        memory = await ContextFile.read(file_manager, "memory.md")
        
        # 如果已存在该 key，替换；否则追加
        pattern = re.escape(f"- **{key}**:")
        if re.search(pattern, memory):
            updated_memory = re.sub(
                f"{pattern}.*",
                f"- **{key}**: {value}",
                memory
            )
        else:
            # 追加到 "## 用户偏好" 部分
            updated_memory = memory.replace(
                "## 用户偏好",
                f"## 用户偏好\n{content}"
            )
        
        # 写回文件
        file_path = file_manager.context_dir / "memory.md"
        async with aiofiles.open(file_path, "w") as f:
            await f.write(updated_memory)
```

### 3.4 WorkspaceWatcher 类

```python
# backend/app/filesystem/watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import asyncio
import logging

logger = logging.getLogger(__name__)

class WorkspaceWatcher(FileSystemEventHandler):
    """监听 workspace/ 目录变化，自动同步到数据库"""
    
    def __init__(self, file_manager: FileManager, sync_handler):
        self.file_manager = file_manager
        self.sync_handler = sync_handler  # 回调函数：async def sync(file_path)
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # 只处理 .md 文件
        if not event.src_path.endswith(".md"):
            return
        
        logger.info(f"File modified: {event.src_path}")
        asyncio.create_task(self._sync(event.src_path))
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        if not event.src_path.endswith(".md"):
            return
        
        logger.info(f"File created: {event.src_path}")
        asyncio.create_task(self._sync(event.src_path))
    
    def on_deleted(self, event):
        if event.is_directory:
            return
        
        if not event.src_path.endswith(".md"):
            return
        
        logger.info(f"File deleted: {event.src_path}")
        asyncio.create_task(self._sync_delete(event.src_path))
    
    async def _sync(self, file_path: str):
        """同步文件到数据库"""
        try:
            await self.sync_handler(Path(file_path))
            logger.info(f"✅ Synced {file_path} to database")
        except Exception as e:
            logger.error(f"❌ Failed to sync {file_path}: {e}")
    
    async def _sync_delete(self, file_path: str):
        """处理文件删除"""
        try:
            # 从数据库中软删除
            await self.sync_handler(Path(file_path), deleted=True)
            logger.info(f"✅ Marked {file_path} as deleted in database")
        except Exception as e:
            logger.error(f"❌ Failed to handle deletion of {file_path}: {e}")


def start_watcher(file_manager: FileManager, sync_handler) -> Observer:
    """启动文件监听器"""
    event_handler = WorkspaceWatcher(file_manager, sync_handler)
    observer = Observer()
    observer.schedule(event_handler, str(file_manager.root), recursive=True)
    observer.start()
    logger.info(f"📂 Watching {file_manager.root}...")
    return observer
```

---

## 4. 与其他模块集成

### 4.1 与 Context Manager 集成

```python
# backend/app/context/manager.py

class ContextManager:
    """Context 管理器（集成文件系统）"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
    
    async def get_context_for_agent(self, session_id: str) -> dict:
        """
        获取 Agent 的上下文
        
        返回双重分身：
        1. Working Memory：精简摘要（来自数据库）
        2. File System：全量原始数据（来自文件系统）
        """
        
        # 1. 从数据库获取摘要（Working Memory）
        summary = await self.db.get_conversation_summary(session_id)
        
        # 2. 从文件系统获取上下文（File System）
        memory = await ContextFile.read(self.file_manager, "memory.md")
        learnings = await ContextFile.read(self.file_manager, "learnings.md")
        rules = await ContextFile.read(self.file_manager, "rules.md")
        
        # 3. 获取当前任务列表
        active_tasks = await self.file_manager.list_tasks(status="in_progress")
        task_summaries = []
        for task_path in active_tasks:
            task_data = await TaskFile.read(task_path)
            task_summaries.append({
                "id": task_data["frontmatter"]["id"],
                "title": task_data["frontmatter"]["title"],
                "file_path": str(task_path)
            })
        
        return {
            "working_memory": summary,  # 数据库摘要
            "file_system": {            # 文件系统上下文
                "memory": memory,
                "learnings": learnings,
                "rules": rules,
                "active_tasks": task_summaries
            }
        }
```

### 4.2 与 Memory Module 集成

```python
# backend/app/memory/manager.py

class MemoryManager:
    """记忆管理器（集成文件系统）"""
    
    def __init__(self, file_manager: FileManager, db):
        self.file_manager = file_manager
        self.db = db
    
    async def store_preference(self, key: str, value: str):
        """存储用户偏好（双写：文件 + 数据库）"""
        
        # 1. 写入文件系统（Source of Truth）
        await ContextFile.set_preference(self.file_manager, key, value)
        
        # 2. 写入数据库（Index）
        await self.db.store_memory(
            memory_type="preference",
            content=f"{key}: {value}",
            structured_data={"key": key, "value": value}
        )
    
    async def store_learning(self, learning: str):
        """存储学习经验"""
        
        # 1. 写入文件系统
        timestamp = datetime.now().strftime("%Y-%m-%d")
        content = f"- **{timestamp}**: {learning}"
        await ContextFile.append(self.file_manager, "learnings.md", content)
        
        # 2. 写入数据库
        await self.db.store_memory(
            memory_type="pattern",
            content=learning
        )
    
    async def get_relevant_context(self, query: str) -> str:
        """获取相关上下文（优先从文件读取）"""
        
        # 1. 读取文件系统上下文
        memory = await ContextFile.read(self.file_manager, "memory.md")
        learnings = await ContextFile.read(self.file_manager, "learnings.md")
        
        # 2. 从数据库检索相关记忆（向量检索）
        relevant_memories = await self.db.retrieve_memories(query, top_k=5)
        
        # 3. 合并返回
        return f"""
# Relevant Context

## Memory (从文件系统)
{memory}

## Learnings (从文件系统)
{learnings}

## Relevant Memories (从数据库检索)
{'\n'.join([m.content for m in relevant_memories])}
"""
```

### 4.3 与 Agent Executor 集成

```python
# backend/app/agent/task_executor.py

class TaskExecutor:
    """Agent 任务执行器（基于文件系统）"""
    
    def __init__(self, file_manager: FileManager, agent: Agent):
        self.file_manager = file_manager
        self.agent = agent
    
    async def create_and_execute(
        self,
        title: str,
        description: str,
        checklist: List[str]
    ):
        """创建任务文件并执行"""
        
        # 1. 创建 task.md 文件
        task_file = await TaskFile.create(
            self.file_manager,
            title=title,
            description=description,
            checklist=checklist
        )
        
        print(f"📝 Created task file: {task_file}")
        
        # 2. 更新状态为 in_progress
        await TaskFile.update_status(task_file, "in_progress")
        
        # 3. 执行任务
        try:
            for i, item in enumerate(checklist):
                # 执行单个步骤
                print(f"🔄 Executing: {item}")
                result = await self.agent.execute_step(item)
                
                # 标记为完成
                await TaskFile.mark_item_done(task_file, item)
                print(f"✅ Completed: {item}")
                
                # 添加 Agent 笔记
                await TaskFile.append_note(
                    task_file,
                    f"完成步骤 {i+1}: {item}"
                )
            
            # 4. 任务完成
            await TaskFile.update_status(task_file, "completed")
            await TaskFile.archive(task_file, self.file_manager)
            print(f"🎉 Task completed and archived: {title}")
        
        except Exception as e:
            # 标记为失败
            await TaskFile.update_status(task_file, "failed")
            await TaskFile.append_note(task_file, f"❌ 执行失败: {str(e)}")
            raise
    
    async def resume_task(self, task_id: str):
        """恢复未完成的任务"""
        
        # 1. 查找任务文件
        tasks = await self.file_manager.list_tasks(status="in_progress")
        task_file = None
        for t in tasks:
            task_data = await TaskFile.read(t)
            if task_data["frontmatter"]["id"] == task_id:
                task_file = t
                break
        
        if not task_file:
            raise ValueError(f"Task {task_id} not found")
        
        # 2. 读取任务
        task_data = await TaskFile.read(task_file)
        body = task_data["body"]
        
        # 3. 解析未完成的 checklist
        uncompleted_items = []
        for line in body.split("\n"):
            if line.strip().startswith("- [ ]"):
                item = line.strip()[6:]  # 去掉 "- [ ] "
                uncompleted_items.append(item)
        
        # 4. 继续执行
        print(f"🔄 Resuming task: {task_data['frontmatter']['title']}")
        for item in uncompleted_items:
            print(f"🔄 Executing: {item}")
            result = await self.agent.execute_step(item)
            await TaskFile.mark_item_done(task_file, item)
            print(f"✅ Completed: {item}")
        
        # 5. 完成任务
        await TaskFile.update_status(task_file, "completed")
        await TaskFile.archive(task_file, self.file_manager)
        print(f"🎉 Task resumed and completed")
```

### 4.4 与 MCP 模块集成

```python
# backend/app/mcp/manager.py

class MCPManager:
    """MCP 管理器（集成文件系统）"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
    
    async def call_tool_with_logging(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
        task_id: str
    ):
        """调用 MCP Tool 并记录到任务文件"""
        
        # 1. 调用 MCP Tool
        result = await self.call_tool(server_name, tool_name, arguments)
        
        # 2. 记录到任务文件
        task_file = await self._find_task_file(task_id)
        if task_file:
            note = f"调用 MCP Tool: {server_name}.{tool_name} → {result['status']}"
            await TaskFile.append_note(task_file, note)
        
        return result
    
    async def _find_task_file(self, task_id: str) -> Optional[Path]:
        """根据 task_id 查找任务文件"""
        tasks = await self.file_manager.list_tasks()
        for task_path in tasks:
            task_data = await TaskFile.read(task_path)
            if task_data["frontmatter"]["id"] == task_id:
                return task_path
        return None
```

---

## 5. 数据库同步策略

### 5.1 同步触发器

```python
# backend/app/filesystem/sync.py

class FileSystemSyncService:
    """文件系统 → 数据库同步服务"""
    
    def __init__(self, file_manager: FileManager, db):
        self.file_manager = file_manager
        self.db = db
    
    async def sync_task_to_db(self, file_path: Path, deleted: bool = False):
        """同步任务文件到数据库"""
        
        if deleted:
            # 软删除
            await self.db.soft_delete_task_by_file_path(str(file_path))
            return
        
        # 读取文件
        task_data = await TaskFile.read(file_path)
        frontmatter = task_data["frontmatter"]
        
        # Upsert 到数据库
        await self.db.upsert_task({
            "id": frontmatter.get("id"),
            "title": frontmatter.get("title"),
            "status": frontmatter.get("status"),
            "priority": frontmatter.get("priority"),
            "file_path": str(file_path),
            "created_at": frontmatter.get("created_at"),
            "updated_at": frontmatter.get("updated_at"),
            "tags": frontmatter.get("tags", [])
        })
    
    async def full_sync(self):
        """全量同步（初始化时使用）"""
        tasks = await self.file_manager.list_tasks()
        for task_path in tasks:
            await self.sync_task_to_db(task_path)
        
        print(f"✅ Full sync completed: {len(tasks)} tasks synced")
```

### 5.2 数据库 Schema 扩展

```sql
-- 任务表（增加 file_path 字段）
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- 任务元数据
    title TEXT NOT NULL,
    status TEXT NOT NULL,  -- pending/in_progress/completed/failed
    priority TEXT DEFAULT 'medium',  -- low/medium/high
    
    -- 文件系统关联
    file_path TEXT UNIQUE NOT NULL,  -- workspace/tasks/task-xxx.md
    
    -- 时间戳
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    
    -- 标签
    tags TEXT[],
    
    -- 软删除
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_tasks_user (user_id),
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_file_path (file_path)
);

-- 任务内容快照表（用于快速查询，避免频繁读文件）
CREATE TABLE task_content_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    
    -- 快照内容
    body TEXT NOT NULL,
    
    -- 版本控制
    version INT NOT NULL,
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_snapshots_task (task_id, version DESC)
);
```

---

## 6. 用户交互场景

### 6.1 场景 1：查看任务进度

```bash
# 方式 1：打开文件
$ cat workspace/tasks/task-20260109-user-auth.md

---
id: task-001
title: 实现用户认证功能
status: in_progress
...
---

# Task: 实现用户认证功能

## 当前进度
- [x] 设计数据库 Schema ✅ 10:05
- [x] 实现用户注册 API ✅ 10:10
- [ ] 实现登录 API （正在进行...）

# 方式 2：使用 CLI
$ tokendance tasks list --status in_progress

┌──────────────────────────────────────────────┐
│  📝 进行中的任务                              │
├──────────────────────────────────────────────┤
│  1. 实现用户认证功能 (70% 完成)               │
│     文件: task-20260109-user-auth.md          │
│     更新: 2 分钟前                            │
└──────────────────────────────────────────────┘
```

### 6.2 场景 2：干预 Agent

```bash
# 用户直接编辑文件
$ vim workspace/tasks/task-20260109-user-auth.md

# 修改前：
- [ ] 实现登录 API
- [ ] 实现 Token 刷新 API

# 修改后（调整优先级）：
- [ ] 实现 Token 刷新 API  # 用户提到前面
- [ ] 实现登录 API        # 降低优先级

## 用户备注
⚠️ **重要**：Token 刷新必须优先实现，客户明天要演示。

# Agent 检测到文件变化，自动调整执行顺序
```

### 6.3 场景 3：接管任务

```markdown
# 用户手动完成某个步骤后，直接标记为完成
- [x] 实现登录 API ✅ 10:30 (用户手动完成)

# Agent 检测到该步骤已完成，跳过执行，继续下一步
```

### 6.4 场景 4：查看 Agent 记忆

```bash
$ cat workspace/context/memory.md

# Agent Memory

## 用户偏好
- **编程语言**: Python 3.11+
- **Web 框架**: FastAPI
- **数据库**: PostgreSQL + Neo4j
- **代码风格**: 遵循 PEP 8，使用 Black 格式化

## 项目约定
- API 路由前缀：`/api/v1`
- 测试框架：pytest
- 认证方式：JWT Bearer Token

# 用户可以直接编辑来纠正错误的记忆
```

### 6.5 场景 5：版本控制

```bash
# 将 workspace/ 纳入 git 版本控制
$ git add workspace/
$ git commit -m "完成用户认证功能"

# 可以回溯历史状态
$ git log workspace/tasks/task-20260109-user-auth.md

# 可以查看变更历史
$ git diff HEAD~1 workspace/tasks/task-20260109-user-auth.md
```

---

## 7. 前端 UI 设计

### 7.1 文件树组件

```vue
<!-- frontend/src/components/FileTree.vue -->

<template>
  <div class="file-tree w-64 border-r border-gray-200 p-4">
    <h3 class="text-lg font-semibold mb-4">📁 Workspace</h3>
    
    <!-- 任务文件夹 -->
    <div class="folder mb-4">
      <div 
        class="folder-header flex items-center justify-between cursor-pointer hover:bg-gray-100 p-2 rounded"
        @click="toggleFolder('tasks')"
      >
        <span class="font-medium">📝 tasks/</span>
        <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
          {{ taskFiles.length }}
        </span>
      </div>
      
      <div v-if="foldersOpen.tasks" class="folder-content ml-4 mt-2">
        <div 
          v-for="file in taskFiles" 
          :key="file.id"
          class="file-item flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer"
          :class="{ 'bg-blue-50': selectedFile?.id === file.id }"
          @click="openFile(file)"
        >
          <span class="mr-2">{{ getStatusIcon(file.status) }}</span>
          <div class="flex-1">
            <div class="text-sm">{{ file.title }}</div>
            <div class="text-xs text-gray-500">{{ formatTime(file.updated_at) }}</div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 上下文文件夹 -->
    <div class="folder mb-4">
      <div 
        class="folder-header flex items-center cursor-pointer hover:bg-gray-100 p-2 rounded"
        @click="toggleFolder('context')"
      >
        <span class="font-medium">🧠 context/</span>
      </div>
      
      <div v-if="foldersOpen.context" class="folder-content ml-4 mt-2">
        <div 
          v-for="file in contextFiles" 
          :key="file"
          class="file-item p-2 hover:bg-gray-50 rounded cursor-pointer text-sm"
          @click="openContextFile(file)"
        >
          {{ file }}
        </div>
      </div>
    </div>
    
    <!-- 草稿文件夹 -->
    <div class="folder">
      <div 
        class="folder-header flex items-center cursor-pointer hover:bg-gray-100 p-2 rounded"
        @click="toggleFolder('drafts')"
      >
        <span class="font-medium">📄 drafts/</span>
      </div>
      
      <div v-if="foldersOpen.drafts" class="folder-content ml-4 mt-2">
        <div 
          v-for="file in draftFiles" 
          :key="file.name"
          class="file-item p-2 hover:bg-gray-50 rounded cursor-pointer text-sm"
          @click="openDraft(file)"
        >
          {{ file.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const taskFiles = ref([])
const contextFiles = ref(['memory.md', 'learnings.md', 'rules.md'])
const draftFiles = ref([])
const foldersOpen = ref({ tasks: true, context: false, drafts: false })
const selectedFile = ref(null)

const getStatusIcon = (status: string) => {
  const icons = {
    'pending': '📋',
    'in_progress': '⏳',
    'completed': '✅',
    'failed': '❌'
  }
  return icons[status] || '📄'
}

const formatTime = (timestamp: string) => {
  // 实现相对时间格式化
  return '2 分钟前'
}

const toggleFolder = (folder: string) => {
  foldersOpen.value[folder] = !foldersOpen.value[folder]
}

const openFile = (file: any) => {
  selectedFile.value = file
  // 触发事件通知父组件
}

onMounted(async () => {
  // 获取文件列表
  const response = await fetch('/api/filesystem/tasks')
  taskFiles.value = await response.json()
})
</script>
```

### 7.2 Markdown 编辑器

```vue
<!-- frontend/src/components/MarkdownEditor.vue -->

<template>
  <div class="markdown-editor flex-1 flex flex-col">
    <!-- 编辑器头部 -->
    <div class="editor-header flex items-center justify-between p-4 border-b">
      <div>
        <h3 class="text-lg font-semibold">{{ file.title }}</h3>
        <div class="text-sm text-gray-500">
          {{ file.file_path }}
        </div>
      </div>
      <div class="flex gap-2">
        <button 
          @click="saveFile"
          class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          💾 保存
        </button>
        <button 
          @click="togglePreview"
          class="px-4 py-2 border rounded hover:bg-gray-50"
        >
          {{ showPreview ? '📝 编辑' : '👁️ 预览' }}
        </button>
      </div>
    </div>
    
    <!-- 编辑器内容 -->
    <div class="editor-content flex-1 flex">
      <!-- 编辑区 -->
      <div v-if="!showPreview" class="flex-1 p-4">
        <textarea 
          v-model="content"
          class="w-full h-full font-mono text-sm border-none outline-none resize-none"
          @input="onContentChange"
        />
      </div>
      
      <!-- 预览区 -->
      <div v-if="showPreview" class="flex-1 p-4 prose max-w-none">
        <div v-html="renderedMarkdown" />
      </div>
    </div>
    
    <!-- 状态栏 -->
    <div class="editor-footer flex items-center justify-between p-2 border-t text-xs text-gray-500">
      <div>
        最后更新: {{ formatTime(file.updated_at) }}
      </div>
      <div>
        {{ content.length }} 字符
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{ file: any }>()
const emit = defineEmits(['save'])

const content = ref(props.file.content)
const showPreview = ref(false)

const renderedMarkdown = computed(() => {
  return marked(content.value)
})

const saveFile = async () => {
  await fetch(`/api/filesystem/tasks/${props.file.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content: content.value })
  })
  
  emit('save')
  alert('✅ 文件已保存')
}

const togglePreview = () => {
  showPreview.value = !showPreview.value
}

const onContentChange = () => {
  // 可以在这里实现自动保存
}
</script>
```

---

## 8. API 接口设计

### 8.1 任务文件 API

```python
# backend/app/api/filesystem.py

from fastapi import APIRouter, HTTPException
from pathlib import Path
from typing import List, Optional

router = APIRouter(prefix="/api/filesystem", tags=["filesystem"])

@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """列出所有任务文件"""
    tasks = await file_manager.list_tasks(status=status)
    
    result = []
    for task_path in tasks[:limit]:
        task_data = await TaskFile.read(task_path)
        result.append({
            "id": task_data["frontmatter"]["id"],
            "title": task_data["frontmatter"]["title"],
            "status": task_data["frontmatter"]["status"],
            "priority": task_data["frontmatter"].get("priority"),
            "file_path": str(task_path),
            "updated_at": task_data["frontmatter"]["updated_at"]
        })
    
    return result

@router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    """获取任务详情"""
    tasks = await file_manager.list_tasks()
    for task_path in tasks:
        task_data = await TaskFile.read(task_path)
        if task_data["frontmatter"]["id"] == task_id:
            return {
                **task_data["frontmatter"],
                "body": task_data["body"],
                "file_path": str(task_path)
            }
    
    raise HTTPException(status_code=404, detail="Task not found")

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, content: str) -> dict:
    """更新任务内容"""
    tasks = await file_manager.list_tasks()
    for task_path in tasks:
        task_data = await TaskFile.read(task_path)
        if task_data["frontmatter"]["id"] == task_id:
            # 写入文件
            async with aiofiles.open(task_path, "w") as f:
                await f.write(content)
            
            return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/context/{filename}")
async def get_context_file(filename: str) -> dict:
    """获取上下文文件"""
    allowed_files = ["memory.md", "learnings.md", "rules.md"]
    if filename not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    content = await ContextFile.read(file_manager, filename)
    return {
        "filename": filename,
        "content": content
    }

@router.put("/context/{filename}")
async def update_context_file(filename: str, content: str) -> dict:
    """更新上下文文件"""
    allowed_files = ["memory.md", "learnings.md", "rules.md"]
    if filename not in allowed_files:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = file_manager.context_dir / filename
    async with aiofiles.open(file_path, "w") as f:
        await f.write(content)
    
    return {"status": "success"}
```

---

## 9. 关键收益

### 9.1 与纯数据库方案对比

| 维度 | 纯数据库方案 | 文件系统优先方案 |
|------|-------------|------------------|
| **透明度** | ❌ 用户不知道 Agent 在做什么 | ✅ 打开文件即可查看 |
| **可干预性** | ❌ 只能通过 UI/API 干预 | ✅ 直接编辑文件即可 |
| **可审计性** | ⚠️ 需要查询数据库 | ✅ 文件自带历史（git） |
| **可移植性** | ❌ 依赖数据库 | ✅ 拷贝文件夹即可迁移 |
| **学习成本** | ⚠️ 需要学习 UI 操作 | ✅ Markdown，零学习成本 |
| **协作友好** | ❌ 多人协作需要复杂权限 | ✅ 文件共享即可协作 |
| **可扩展性** | ⚠️ 需要修改数据库 Schema | ✅ 添加新的 .md 文件即可 |
| **故障恢复** | ❌ 数据库崩溃影响核心功能 | ✅ 文件系统是最后防线 |

### 9.2 实际价值

1. **透明性**：用户随时可以查看 Agent 在做什么，打开文件即可
2. **可控性**：用户可以直接编辑文件来干预 Agent，无需复杂的 UI
3. **简单性**：不需要学习复杂的操作，Markdown 人人都会
4. **可移植性**：拷贝 `workspace/` 文件夹即可迁移所有状态
5. **协作友好**：团队成员可以直接共享文件夹，或通过 git 协作
6. **版本控制**：放入 git 可以追溯所有变化，支持回滚
7. **故障恢复**：即使数据库崩溃，文件系统仍然保留完整状态

---

## 10. 实施计划

### Phase 1: 基础框架（2天）

**目标**：搭建文件系统基础架构

- [ ] 实现 FileManager 类
- [ ] 实现 TaskFile 类
- [ ] 实现 ContextFile 类
- [ ] 创建默认目录结构
- [ ] 编写单元测试

### Phase 2: 文件监听（1天）

**目标**：实现文件变化自动同步

- [ ] 实现 WorkspaceWatcher 类
- [ ] 实现 FileSystemSyncService 类
- [ ] 测试文件变化监听
- [ ] 测试数据库同步

### Phase 3: 模块集成（2天）

**目标**：与现有模块集成

- [ ] 集成 Context Manager
- [ ] 集成 Memory Module
- [ ] 集成 Agent Executor
- [ ] 集成 MCP Manager
- [ ] 更新相关文档

### Phase 4: API 接口（1天）

**目标**：实现 RESTful API

- [ ] 实现任务文件 CRUD API
- [ ] 实现上下文文件 API
- [ ] 实现文件列表 API
- [ ] API 文档生成

### Phase 5: 前端 UI（3天）

**目标**：实现文件树和编辑器

- [ ] 实现 FileTree 组件
- [ ] 实现 MarkdownEditor 组件
- [ ] 实现文件保存功能
- [ ] 实现实时同步

### Phase 6: 测试与优化（1天）

**目标**：完整测试和性能优化

- [ ] 集成测试
- [ ] 性能测试（文件监听开销）
- [ ] 边界情况测试
- [ ] 文档完善

**总计**：10 天

---

## 11. 常见问题

### Q1: 文件系统和数据库如何保持一致性？

**A**: 文件系统是 Source of Truth，数据库只是索引。通过文件监听器自动同步，保证数据库始终反映文件系统的最新状态。

### Q2: 文件系统性能会成为瓶颈吗？

**A**: 不会。现代 SSD 读写性能远超需求，且我们使用异步 I/O 和事件驱动监听，开销极小。

### Q3: 如何处理并发修改？

**A**: 
- Agent 修改：通过文件锁保证原子性
- 用户修改：文件监听器检测变化，Agent 重新加载
- 冲突：文件系统天然支持版本控制（git），可以回溯

### Q4: 如何支持多用户？

**A**: 每个用户有独立的 workspace 目录，通过 `user_id` 路由到不同目录。

### Q5: 数据库的作用是什么？

**A**: 
- 快速查询（不需要遍历文件）
- 向量检索（Memory 检索）
- 聚合统计（Dashboard）
- 但数据库崩溃不影响核心功能

---

## 12. 总结

**核心理念**：文件系统是人类和 AI 最自然的协作界面。

**设计决策**：
1. 文件系统 = Source of Truth
2. 数据库 = Index + Cache
3. Markdown = 最好的 DSL
4. 监听式同步，而非轮询

**关键收益**：
- ✅ 透明性：用户随时可见 Agent 状态
- ✅ 可控性：直接编辑文件即可干预
- ✅ 简单性：Markdown 零学习成本
- ✅ 可移植性：拷贝文件夹即可迁移
- ✅ 协作友好：支持 git、文件共享
- ✅ 故障恢复：文件系统是最后防线

**TokenDance 的创新**：
- Dual Context Streams：Working Memory（数据库） + File System（文件）
- Plan Recitation：TODO 列表放在文件末尾
- Keep the Failures：错误记录保留在文件中

---

**参考资料**：
- Manus 产品分析："todo.md 是其灵魂"
- [Anthropic MCP Specification](https://modelcontextprotocol.io/)
- [watchdog Documentation](https://pythonhosted.org/watchdog/)
