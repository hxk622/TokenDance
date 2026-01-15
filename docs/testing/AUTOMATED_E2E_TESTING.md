# 自动化 E2E 测试指南

> 使用 Chrome DevTools Protocol (CDP) 进行浏览器自动化测试

## 🎯 概述

TokenDance 使用 **Chrome DevTools Protocol** 通过 MCP (Model Context Protocol) 工具进行端到端自动化测试。这种方式可以：

- ✅ 真实浏览器环境测试
- ✅ 自动截图和验证
- ✅ 网络请求监控
- ✅ 性能分析
- ✅ 无需额外测试框架

## 🛠️ 可用工具

通过 `user-chrome-devtools` MCP 服务器，我们可以使用以下工具：

### 页面导航
- `navigate_page` - 导航到URL
- `new_page` - 创建新页面
- `select_page` - 选择页面
- `list_pages` - 列出所有页面

### 元素操作
- `click` - 点击元素
- `fill` - 填写表单
- `fill_form` - 填写整个表单
- `press_key` - 按键
- `hover` - 悬停
- `drag` - 拖拽

### 等待和验证
- `wait_for` - 等待文本出现
- `take_snapshot` - 获取页面快照（用于获取元素uid）
- `take_screenshot` - 截图

### 网络监控
- `list_network_requests` - 列出网络请求
- `get_network_request` - 获取特定请求详情

### 性能分析
- `performance_start_trace` - 开始性能追踪
- `performance_stop_trace` - 停止性能追踪
- `performance_analyze_insight` - 分析性能数据

### 其他
- `get_console_message` - 获取控制台消息
- `list_console_messages` - 列出所有控制台消息
- `handle_dialog` - 处理对话框

## 📝 测试用例示例

### 测试1: 基础页面加载

```python
# 步骤1: 创建新页面
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="new_page",
    arguments={}
)

# 步骤2: 导航到前端
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="navigate_page",
    arguments={
        "type": "url",
        "url": "http://localhost:5173/chat",
        "timeout": 10000
    }
)

# 步骤3: 等待页面加载
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="wait_for",
    arguments={
        "text": "TokenDance",
        "timeout": 5000
    }
)

# 步骤4: 截图验证
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="take_screenshot",
    arguments={
        "format": "png",
        "filePath": "test_screenshots/01_page_load.png"
    }
)
```

### 测试2: 发送消息并验证SSE流

```python
# 步骤1: 获取页面快照（找到输入框）
snapshot = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="take_snapshot",
    arguments={}
)

# 步骤2: 填写输入框（从快照中找到input的uid）
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="fill",
    arguments={
        "uid": "input-textarea-uid",  # 从snapshot中获取
        "value": "帮我研究AI Agent市场"
    }
)

# 步骤3: 点击发送按钮
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="click",
    arguments={
        "uid": "send-button-uid"  # 从snapshot中获取
    }
)

# 步骤4: 等待Agent响应
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="wait_for",
    arguments={
        "text": "Agent 思考中",
        "timeout": 10000
    }
)

# 步骤5: 监听网络请求（验证SSE）
requests = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="list_network_requests",
    arguments={}
)

# 验证是否有SSE请求
sse_request = None
for req in requests:
    if "event-stream" in req.get("contentType", ""):
        sse_request = req
        break

assert sse_request is not None, "SSE请求未找到"
```

### 测试3: Working Memory显示

```python
# 步骤1: 点击Working Memory按钮
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="click",
    arguments={
        "uid": "working-memory-button-uid"
    }
)

# 步骤2: 等待三文件显示
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="wait_for",
    arguments={
        "text": "task_plan.md",
        "timeout": 5000
    }
)

# 步骤3: 验证三个Tab
snapshot = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="take_snapshot",
    arguments={}
)

# 从快照中查找三个Tab
tabs = ["task_plan", "findings", "progress"]
for tab in tabs:
    # 在snapshot中查找tab元素
    assert f"{tab}-tab" in snapshot, f"{tab} tab未找到"

# 步骤4: 截图
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="take_screenshot",
    arguments={
        "format": "png",
        "filePath": "test_screenshots/03_working_memory.png"
    }
)
```

### 测试4: 性能分析

```python
# 步骤1: 开始性能追踪
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="performance_start_trace",
    arguments={}
)

# 步骤2: 执行操作（发送消息等）
# ... 执行测试操作 ...

# 步骤3: 停止追踪
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="performance_stop_trace",
    arguments={}
)

# 步骤4: 分析性能
insights = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="performance_analyze_insight",
    arguments={}
)

# 验证性能指标
assert insights["firstContentfulPaint"] < 2000, "首屏渲染过慢"
assert insights["timeToInteractive"] < 3000, "可交互时间过长"
```

## 🚀 执行测试

### 方法1: 使用AI Agent执行

最简单的方式是让AI Agent帮你执行测试：

```
请使用Chrome DevTools工具执行以下E2E测试：
1. 打开 http://localhost:5173/chat
2. 发送消息"帮我研究AI Agent市场"
3. 验证Agent响应
4. 截图保存结果
```

### 方法2: 编写测试脚本

参考 `scripts/e2e_chrome_test.py`，编写自动化测试脚本。

### 方法3: 手动执行单个测试

使用Cursor的MCP工具调用功能，逐个执行测试步骤。

## 📊 测试报告

测试执行后，会生成：

1. **截图**: `test_screenshots/` 目录
2. **性能数据**: JSON格式的性能指标
3. **网络请求日志**: 所有网络请求详情
4. **控制台日志**: 浏览器控制台消息

## 🔍 调试技巧

### 1. 获取元素UID

```python
# 先获取页面快照
snapshot = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="take_snapshot",
    arguments={}
)

# 在快照中查找元素
# snapshot包含所有元素的uid和描述
```

### 2. 等待元素出现

```python
# 使用wait_for等待文本
call_mcp_tool(
    server="user-chrome-devtools",
    toolName="wait_for",
    arguments={
        "text": "Agent 思考中",
        "timeout": 10000  # 10秒超时
    }
)
```

### 3. 监控网络请求

```python
# 列出所有网络请求
requests = call_mcp_tool(
    server="user-chrome-devtools",
    toolName="list_network_requests",
    arguments={}
)

# 查找特定请求
for req in requests:
    if "/api/v1/chat" in req.get("url", ""):
        print(f"找到Chat API请求: {req}")
```

### 4. 处理异步操作

```python
# SSE是异步的，需要等待
# 先发送消息
# 然后等待多个条件：
# 1. 等待"思考中"文本
# 2. 等待网络请求
# 3. 等待最终响应
```

## ⚠️ 注意事项

1. **前置条件**: 确保后端和前端服务都在运行
2. **超时设置**: 合理设置timeout，避免测试失败
3. **元素定位**: 使用稳定的选择器（避免使用动态生成的ID）
4. **截图保存**: 测试失败时自动截图，便于调试
5. **性能影响**: 性能测试会影响实际性能，注意区分

## 📚 相关文档

- [E2E测试指南](../E2E_TEST_GUIDE.md)
- [Chrome DevTools Protocol文档](https://chromedevtools.github.io/devtools-protocol/)
- [MCP工具文档](../../mcp/README.md)

## 🎯 下一步

1. ✅ 创建基础测试用例
2. ⬜ 集成到CI/CD流程
3. ⬜ 添加性能基准测试
4. ⬜ 创建测试报告生成器

---

**最后更新**: 2026-01-14
