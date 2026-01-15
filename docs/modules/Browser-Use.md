# Browser-Use 设计文档

> **核心更新 (2026-01-15)**: 采用 Vercel Labs agent-browser 替代 Playwright MCP
> - Snapshot + Refs 模式，节省 93% Token
> - 确定性元素选择 (@e1, @e2)
> - 原生 Session 隔离支持

## 1. 核心目标

**为 Agent 提供高效率、低 Token 消耗的浏览器自动化能力**

| 维度 | Playwright MCP | agent-browser | 优势 |
|-----|---------------|---------------|------|
| **Token 消耗** | 完整 Accessibility Tree | Snapshot + Refs | **节省 93%** |
| **工具数量** | 26+ MCP Tools | 统一 CLI 接口 | 减少决策负担 |
| **元素定位** | CSS Selector | @e1, @e2 引用 | 更稳定可靠 |

## 2. 技术选型：agent-browser

```bash
# 安装
npm install -g agent-browser
agent-browser install  # 下载 Chromium
```

**架构优势**：
- Rust CLI → 快速命令解析
- Node.js Daemon → Playwright 生命周期管理
- 抽象服务层 → 可降级到原生 Playwright

## 3. 核心实现

```python
# backend/app/services/browser_automation.py

class AgentBrowserService:
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
    
    async def open(self, url: str) -> SnapshotResult:
        """打开URL并返回 Snapshot"""
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
        return SnapshotResult.from_json(output)
    
    async def click(self, ref: str) -> BrowserResult:
        """点击元素 (使用 @e1 格式)"""
        await self._run_cmd(["click", ref])
        return BrowserResult(success=True)
    
    async def fill(self, ref: str, text: str) -> BrowserResult:
        """填充输入框"""
        await self._run_cmd(["fill", ref, text])
        return BrowserResult(success=True)
    
    async def get_text(self, ref: str) -> str:
        """获取元素文本"""
        return await self._run_cmd(["get", "text", ref])
    
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

## 4. Tool 注册

```python
# backend/app/agent/tools/builtin/browser_ops.py

@tool_registry.register
class BrowserOpenTool(BaseTool):
    """打开网页并获取 Snapshot"""
    name = "browser_open"
    description = "打开网页URL，返回页面的 Accessibility Tree Snapshot"
    
    async def execute(self, url: str) -> ToolResult:
        browser = AgentBrowserService()
        snapshot = await browser.open(url)
        
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

@tool_registry.register  
class BrowserSnapshotTool(BaseTool):
    """获取当前页面 Snapshot"""
    name = "browser_snapshot"
    description = "获取当前页面的 Accessibility Tree Snapshot"

@tool_registry.register
class BrowserScreenshotTool(BaseTool):
    """页面截图"""
    name = "browser_screenshot"
    description = "对当前页面截图，用于关键节点的视觉记录"
```

## 5. Deep Research 集成

```
典型工作流:

Phase 1: 初步搜索 (web_search)
├── web_search("AI Agent market size 2024")
└── [结果写入 findings.md]

Phase 2: 深度采集 (agent-browser)
├── browser_open(url)
├── [解析 Snapshot，识别目标元素]
├── browser_click(@eN)
├── browser_get_text(@eM)
├── browser_screenshot()  # 关键节点
└── [写入 findings.md]

Phase 3: 报告生成
├── 读取 findings.md
└── 生成结构化报告 + 时光长廊截图
```

## 6. 安全限制

```python
# MVP 阶段限制使用场景
ALLOWED_PATTERNS = [
    "*.wikipedia.org",
    "*.github.com",
    "*.arxiv.org",
    "*.xiaohongshu.com",
    "*.taobao.com",
    # 开放型网站，无需复杂认证
]

# 暂时避开
AVOID_PATTERNS = [
    "*login*",
    "*auth*",
    "*sso*",
    # 复杂认证系统
]
```

## 7. 与三文件工作法集成

```python
# 采集结果存入 findings.md
async def save_to_findings(url: str, content: str, screenshot: str):
    entry = f"""
## 采集: {url}
**时间**: {datetime.now().isoformat()}
**内容摘要**: {content[:500]}...
**截图**: ![{url}]({screenshot})
---
"""
    await fs.append("findings.md", entry)
```

## 8. 成功指标

| 指标 | 目标 | 说明 |
|-----|-----|------|
| Token 节省率 | >80% | vs 原 Playwright 方案 |
| 采集成功率 | >85% | 端到端任务完成率 |
| 平均采集时间 | <30s/页 | 从 open 到提取完成 |

## 9. 参考文档

- [Agent-Browser 整合方案](./Agent-Browser-Integration.md) - 详细设计文档
- [agent-browser GitHub](https://github.com/vercel-labs/agent-browser)
- [agent-browser 官方文档](https://agent-browser.dev/)
