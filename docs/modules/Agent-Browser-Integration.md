# Agent-Browser 整合方案

> Version: 1.0.0 | MVP阶段
> Last Updated: 2026-01-15
> 技术选型: Vercel Labs agent-browser

## 1. 背景与技术选型

### 1.1 为什么选择 agent-browser？

| 维度 | Playwright MCP | agent-browser | 优势 |
|-----|---------------|---------------|------|
| **Token 消耗** | 完整 Accessibility Tree（数千节点） | Snapshot + Refs（精简引用） | **节省 93% Context** |
| **工具数量** | 26+ MCP Tools | 统一 CLI 接口 | 减少决策负担 |
| **元素定位** | CSS Selector / XPath | @e1, @e2 确定性引用 | 更稳定可靠 |
| **性能** | Node.js 全量 | Rust CLI + Node.js Daemon | 更快启动 |
| **Session 隔离** | 需自行管理 | 原生 --session 支持 | 多 Agent 友好 |

### 1.2 与 TokenDance 架构契合度

| TokenDance 原则 | agent-browser 特性 | 契合度 |
|----------------|-------------------|--------|
| Dual Context Streams | Snapshot 文本化 vs Screenshot 视觉化 | ✅ 完美匹配 |
| Action Space Pruning | CLI 统一接口，无工具选择困难 | ✅ 完美匹配 |
| 三文件工作法 | 采集结果存 findings.md | ✅ 完美匹配 |
| Skill 三级加载 | 可封装为 L2/L3 Skill | ✅ 完美匹配 |

---

## 2. 整合架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     TokenDance Agent Engine                      │
├─────────────────────────────────────────────────────────────────┤
│  Skill Layer                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Deep Research Skill                                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │    │
│  │  │ web_search  │  │  read_url   │  │ browser_op  │      │    │
│  │  │   (Tavily)  │  │ (Readability)│  │(agent-browser)│    │    │
│  │  └─────────────┘  └─────────────┘  └──────┬──────┘      │    │
│  └───────────────────────────────────────────┼──────────────┘    │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                  BrowserAutomationService (抽象层)               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Interface:                                              │    │
│  │  - open(url) → snapshot                                  │    │
│  │  - click(ref) → result                                   │    │
│  │  - fill(ref, text) → result                              │    │
│  │  - get_text(ref) → text                                  │    │
│  │  - screenshot() → path                                   │    │
│  │  - close()                                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌─────────────┐           ┌─────────────┐                      │
│  │ agent-browser│           │  Playwright │                      │
│  │ (Primary)   │           │  (Fallback) │                      │
│  └──────┬──────┘           └─────────────┘                      │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agent-browser CLI + Daemon                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Rust CLI   │───▶│ Node Daemon │───▶│  Chromium   │          │
│  │ (解析命令)  │    │ (Playwright) │    │  (浏览器)   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 抽象服务层设计

```python
# backend/app/services/browser_automation.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass
import asyncio
import subprocess
import json

@dataclass
class SnapshotResult:
    """Snapshot 结果"""
    tree: str                    # Accessibility Tree 文本
    refs: Dict[str, str]         # ref -> element description
    url: str
    title: str

@dataclass  
class BrowserResult:
    """浏览器操作结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None

class BrowserAutomationService(ABC):
    """浏览器自动化服务抽象接口"""
    
    @abstractmethod
    async def open(self, url: str, session: Optional[str] = None) -> SnapshotResult:
        """打开URL并返回Snapshot"""
        pass
    
    @abstractmethod
    async def snapshot(self, interactive_only: bool = True, compact: bool = True) -> SnapshotResult:
        """获取当前页面Snapshot"""
        pass
    
    @abstractmethod
    async def click(self, ref: str) -> BrowserResult:
        """点击元素"""
        pass
    
    @abstractmethod
    async def fill(self, ref: str, text: str) -> BrowserResult:
        """填充输入框"""
        pass
    
    @abstractmethod
    async def get_text(self, ref: str) -> str:
        """获取元素文本"""
        pass
    
    @abstractmethod
    async def screenshot(self, path: Optional[str] = None) -> str:
        """截图并返回路径"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """关闭浏览器"""
        pass


class AgentBrowserService(BrowserAutomationService):
    """
    agent-browser 实现
    
    核心优势:
    - 93% Token 节省 (Snapshot + Refs vs 完整 DOM)
    - 确定性元素选择 (@e1, @e2)
    - Session 隔离支持
    """
    
    def __init__(self, session: Optional[str] = None):
        self.session = session or f"td_{uuid4().hex[:8]}"
        self._base_cmd = ["agent-browser", "--session", self.session]
    
    async def _run_cmd(self, args: list, json_output: bool = False) -> str:
        """执行 agent-browser 命令"""
        cmd = self._base_cmd + args
        if json_output:
            cmd.append("--json")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"agent-browser error: {stderr.decode()}")
        
        return stdout.decode()
    
    async def open(self, url: str, session: Optional[str] = None) -> SnapshotResult:
        """打开URL并返回Snapshot"""
        await self._run_cmd(["open", url])
        return await self.snapshot()
    
    async def snapshot(self, interactive_only: bool = True, compact: bool = True) -> SnapshotResult:
        """
        获取 Accessibility Tree Snapshot
        
        关键参数:
        - -i: 只返回交互元素 (button, input, link)
        - -c: 紧凑模式 (移除空结构元素)
        
        这两个参数是 93% Token 节省的关键!
        """
        args = ["snapshot"]
        if interactive_only:
            args.append("-i")
        if compact:
            args.append("-c")
        
        output = await self._run_cmd(args, json_output=True)
        data = json.loads(output)
        
        return SnapshotResult(
            tree=data.get("tree", ""),
            refs=data.get("refs", {}),
            url=data.get("url", ""),
            title=data.get("title", "")
        )
    
    async def click(self, ref: str) -> BrowserResult:
        """点击元素 (使用 @e1 格式)"""
        try:
            await self._run_cmd(["click", ref])
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def fill(self, ref: str, text: str) -> BrowserResult:
        """填充输入框"""
        try:
            await self._run_cmd(["fill", ref, text])
            return BrowserResult(success=True)
        except Exception as e:
            return BrowserResult(success=False, error=str(e))
    
    async def get_text(self, ref: str) -> str:
        """获取元素文本"""
        output = await self._run_cmd(["get", "text", ref])
        return output.strip()
    
    async def screenshot(self, path: Optional[str] = None) -> str:
        """截图 (关键节点时使用)"""
        if path is None:
            path = f"/workspace/screenshots/{self.session}_{int(time.time())}.png"
        await self._run_cmd(["screenshot", path])
        return path
    
    async def close(self) -> None:
        """关闭浏览器"""
        await self._run_cmd(["close"])
```

---

## 3. Skill 封装

### 3.1 作为 Deep Research 的子能力

agent-browser 不作为独立 Skill，而是作为 Deep Research Skill 的 **L3 资源** 按需加载。

```
skills/
└── deep_research/
    ├── SKILL.md                    # L1 + L2
    └── resources/
        ├── browser_automation.md   # L3: 浏览器操作指南 (新增)
        └── ...
```

### 3.2 browser_automation.md (L3 资源)

```markdown
# 浏览器自动化指南

## 何时使用

当 web_search 或 read_url 无法满足需求时使用浏览器自动化：
- 需要登录后才能访问的内容
- 需要点击、翻页才能获取的数据
- 动态加载的 JavaScript 页面

## 工作流程

1. **打开页面**: `browser_open(url)`
   - 返回 Snapshot (Accessibility Tree)
   - 每个可交互元素有唯一 ref (@e1, @e2...)

2. **识别目标**: 从 Snapshot 中找到目标元素的 ref
   - 示例: `- button "Load More" [ref=@e5]`

3. **执行操作**: 
   - `browser_click(@e5)` - 点击
   - `browser_fill(@e3, "search query")` - 填充
   - `browser_get_text(@e1)` - 获取文本

4. **获取新状态**: 操作后重新 `browser_snapshot()` 获取最新页面

5. **提取内容**: 使用 `browser_get_text()` 提取需要的信息

6. **关键节点截图**: 在重要决策点 `browser_screenshot()` 保存视觉记录

## 最佳实践

- ✅ 优先使用 `-i -c` 参数获取精简 Snapshot
- ✅ 操作后立即获取新 Snapshot 验证结果
- ✅ 关键节点截图，用于用户回溯
- ✅ 将采集结果及时写入 findings.md
- ❌ 不要频繁截图（消耗资源）
- ❌ 不要在认证复杂的企业系统使用

## 示例工作流

```
用户: "帮我看看小红书上这款相机的评价"

Agent:
1. browser_open("https://www.xiaohongshu.com/search?keyword=相机型号")
2. [解析 Snapshot，找到搜索结果列表]
3. browser_click(@e3)  # 点击第一个结果
4. browser_snapshot()   # 获取详情页
5. browser_get_text(@e5)  # 获取评价内容
6. browser_screenshot()   # 截图保存
7. [写入 findings.md]
```
```

### 3.3 Tool 注册

```python
# backend/app/agent/tools/builtin/browser_ops.py

from app.tools.base import BaseTool, tool_registry
from app.services.browser_automation import AgentBrowserService

@tool_registry.register
class BrowserOpenTool(BaseTool):
    """打开网页并获取 Snapshot"""
    name = "browser_open"
    description = "打开网页URL，返回页面的 Accessibility Tree Snapshot"
    
    async def execute(self, url: str) -> ToolResult:
        browser = AgentBrowserService()
        snapshot = await browser.open(url)
        
        # 控制返回大小，避免 Context 膨胀
        return ToolResult(
            status="success",
            data={
                "url": snapshot.url,
                "title": snapshot.title,
                "snapshot": snapshot.tree[:5000],  # 限制大小
                "hint": "使用 @eN 格式引用元素，如 browser_click(@e2)"
            }
        )

@tool_registry.register
class BrowserClickTool(BaseTool):
    """点击页面元素"""
    name = "browser_click"
    description = "点击 Snapshot 中的元素，使用 @eN 格式的 ref"
    
    async def execute(self, ref: str) -> ToolResult:
        browser = AgentBrowserService()
        result = await browser.click(ref)
        
        if result.success:
            # 操作后获取新 Snapshot
            snapshot = await browser.snapshot()
            return ToolResult(
                status="success",
                data={"new_snapshot": snapshot.tree[:5000]}
            )
        return ToolResult(status="error", error=result.error)

@tool_registry.register  
class BrowserSnapshotTool(BaseTool):
    """获取当前页面 Snapshot"""
    name = "browser_snapshot"
    description = "获取当前页面的 Accessibility Tree Snapshot"
    
    async def execute(self) -> ToolResult:
        browser = AgentBrowserService()
        snapshot = await browser.snapshot(interactive_only=True, compact=True)
        return ToolResult(status="success", data={"snapshot": snapshot.tree[:5000]})

@tool_registry.register
class BrowserScreenshotTool(BaseTool):
    """页面截图"""
    name = "browser_screenshot"
    description = "对当前页面截图，用于关键节点的视觉记录"
    
    async def execute(self) -> ToolResult:
        browser = AgentBrowserService()
        path = await browser.screenshot()
        return ToolResult(
            status="success", 
            data={"screenshot_path": path},
            summary=f"截图已保存: {path}"
        )
```

---

## 4. Deep Research 场景应用

### 4.1 典型工作流

```
用户: "调研 AI Agent 市场规模和主要玩家"

Phase 1: 初步搜索 (web_search)
├── web_search("AI Agent market size 2024")
├── web_search("AI Agent companies funding")
└── [结果写入 findings.md]

Phase 2: 深度采集 (agent-browser)
├── browser_open("https://www.crunchbase.com/hub/ai-agent-companies")
├── [解析 Snapshot，识别公司列表]
├── 循环:
│   ├── browser_click(@eN)  # 点击公司详情
│   ├── browser_get_text()  # 提取融资信息
│   ├── browser_screenshot() # 截图保存
│   └── [写入 findings.md]
└── browser_close()

Phase 3: 报告生成
├── 读取 findings.md
├── 生成结构化报告
└── 附上关键截图链接
```

### 4.2 时光长廊 (Time-Lapse Log)

利用 agent-browser 的低开销截图，自动生成研究过程的视觉记录：

```python
# backend/app/services/time_lapse.py

class TimeLapseLogger:
    """时光长廊 - 研究过程视觉记录"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.log_path = f"/workspace/{session_id}/time_lapse.md"
        self.screenshots = []
    
    async def log_step(
        self, 
        step_name: str, 
        url: str, 
        screenshot_path: str,
        summary: str
    ):
        """记录一个关键步骤"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "url": url,
            "screenshot": screenshot_path,
            "summary": summary
        }
        self.screenshots.append(entry)
        
        # 追加到 Markdown 日志
        await self._append_to_log(entry)
    
    async def _append_to_log(self, entry: dict):
        content = f"""
### {entry['timestamp'][:19]} - {entry['step']}
**URL**: {entry['url']}
**摘要**: {entry['summary']}
![截图]({entry['screenshot']})
---
"""
        await fs.append(self.log_path, content)
    
    def get_gallery(self) -> list:
        """获取截图画廊，用于前端展示"""
        return self.screenshots
```

---

## 5. 前端集成

### 5.1 操作日志展示 (非实时视频流)

```vue
<!-- frontend/src/components/BrowserOperationLog.vue -->
<template>
  <div class="browser-log">
    <div class="log-header">
      <h3>网页采集进度</h3>
      <span class="status-indicator" :class="status">{{ statusText }}</span>
    </div>
    
    <!-- 操作日志列表 -->
    <div class="log-entries">
      <div 
        v-for="entry in operationLog" 
        :key="entry.id"
        class="log-entry"
      >
        <div class="entry-icon">
          <component :is="getIcon(entry.type)" />
        </div>
        <div class="entry-content">
          <span class="entry-action">{{ entry.action }}</span>
          <span class="entry-target">{{ entry.target }}</span>
          <span class="entry-time">{{ formatTime(entry.timestamp) }}</span>
        </div>
        <!-- 关键节点显示缩略图 -->
        <img 
          v-if="entry.screenshot" 
          :src="entry.screenshot" 
          class="entry-thumbnail"
          @click="showFullScreenshot(entry.screenshot)"
        />
      </div>
    </div>
    
    <!-- 时光长廊入口 -->
    <button @click="showTimeLapse" class="time-lapse-btn">
      查看完整研究过程
    </button>
  </div>
</template>
```

### 5.2 时光长廊组件

```vue
<!-- frontend/src/components/TimeLapseGallery.vue -->
<template>
  <div class="time-lapse-gallery">
    <h2>研究过程回溯</h2>
    <p class="subtitle">Agent 访问的每一个关键页面</p>
    
    <div class="gallery-grid">
      <div 
        v-for="(item, index) in gallery" 
        :key="index"
        class="gallery-item"
        @click="selectItem(item)"
      >
        <img :src="item.screenshot" :alt="item.step" />
        <div class="item-overlay">
          <span class="step-name">{{ item.step }}</span>
          <span class="item-url">{{ truncateUrl(item.url) }}</span>
        </div>
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <Modal v-if="selectedItem" @close="selectedItem = null">
      <img :src="selectedItem.screenshot" class="full-screenshot" />
      <div class="item-details">
        <h3>{{ selectedItem.step }}</h3>
        <p>{{ selectedItem.summary }}</p>
        <a :href="selectedItem.url" target="_blank">访问原页面</a>
      </div>
    </Modal>
  </div>
</template>
```

---

## 6. 开发任务清单

### Phase 1: 基础集成 (Week 1)

| 任务 | 优先级 | 预估工时 | 描述 |
|-----|-------|---------|------|
| 安装 agent-browser | P0 | 2h | npm install -g agent-browser, 验证可用 |
| BrowserAutomationService | P0 | 4h | 实现抽象接口和 AgentBrowserService |
| browser_* Tools | P0 | 4h | 注册 browser_open/click/snapshot/screenshot |
| 集成测试 | P0 | 2h | 端到端测试：打开页面→Snapshot→操作 |

### Phase 2: Deep Research 集成 (Week 2)

| 任务 | 优先级 | 预估工时 | 描述 |
|-----|-------|---------|------|
| browser_automation.md | P0 | 2h | 编写 L3 资源文档 |
| Deep Research Skill 更新 | P0 | 4h | 集成 browser_* tools 到工作流 |
| TimeLapseLogger | P1 | 4h | 实现时光长廊日志 |
| 场景测试 | P0 | 4h | 测试小红书/淘宝搜索等场景 |

### Phase 3: 前端展示 (Week 3)

| 任务 | 优先级 | 预估工时 | 描述 |
|-----|-------|---------|------|
| BrowserOperationLog | P1 | 4h | 操作日志组件 |
| TimeLapseGallery | P2 | 6h | 时光长廊画廊组件 |
| 集成到任务详情页 | P1 | 2h | 在研究任务详情中展示 |

### Phase 4: 稳定性与优化 (Week 4)

| 任务 | 优先级 | 预估工时 | 描述 |
|-----|-------|---------|------|
| Playwright Fallback | P2 | 4h | agent-browser 不可用时的降级方案 |
| Session 管理 | P1 | 4h | 多任务 Session 隔离和清理 |
| 错误处理 | P1 | 4h | 超时、网络错误等异常处理 |

---

## 7. 风险与缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|-----|-----|------|---------|
| agent-browser API 变更 | 中 | 高 | 抽象服务层隔离，Playwright fallback |
| 复杂网站无法操作 | 中 | 中 | 限制使用场景，优先开放型网站 |
| Session 资源泄露 | 低 | 中 | 定时清理 + 任务结束时强制关闭 |
| Chromium 资源消耗 | 中 | 低 | 限制并发 Session 数量 |

---

## 8. 成功指标

| 指标 | 目标 | 测量方式 |
|-----|-----|---------|
| Token 节省率 | >80% (vs 原 Playwright 方案) | 对比相同任务的 Token 消耗 |
| Deep Research 成功率 | >85% | 端到端任务完成率 |
| 平均采集时间 | <30s/页 | 从 open 到提取完成 |
| 时光长廊覆盖率 | 100% 关键节点有截图 | 研究报告附带截图数量 |

---

## 9. 参考资料

- [agent-browser GitHub](https://github.com/vercel-labs/agent-browser)
- [agent-browser 官方文档](https://agent-browser.dev/)
- [TokenDance Skill 设计](./Skill-Design.md)
- [TokenDance Tool-Use 设计](./Tool-Use.md)

---

**文档维护者**: TokenDance 核心团队
**最后更新**: 2026-01-15
