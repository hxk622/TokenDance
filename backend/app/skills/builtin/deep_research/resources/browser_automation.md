# 浏览器自动化操作指南

本资源定义 Deep Research 中浏览器操作的最佳实践，基于 agent-browser 的 Snapshot + Refs 机制实现 93%+ Token 节省。

## 何时使用浏览器操作

### 优先使用 web_search/read_url
- 静态内容获取
- 简单网页读取
- 搜索引擎结果

### 必须使用 browser_* 工具
- 需要登录才能访问的内容
- JavaScript 动态渲染的 SPA 应用
- 需要滚动加载更多内容
- 需要交互才能展示的数据
- 反爬虫保护的网站（如小红书、淘宝）

## 工具使用

### browser_open
打开网页，获取初始状态。

```python
# 打开页面
result = browser_open(url="https://xiaohongshu.com/search?keyword=AI")
# 返回: {"title": "...", "url": "..."}
```

### browser_snapshot
获取页面结构快照（核心工具）。

```python
# 获取交互元素快照（推荐）
snapshot = browser_snapshot(interactive_only=True, compact=True)
# 返回压缩的 Markdown 格式:
# - @e1 [搜索框] type=input
# - @e2 [搜索] type=button
# - @e3 [第一个结果] type=link href=...
```

**参数说明**：
- `interactive_only=True`: 只返回可交互元素（减少 90% 无用内容）
- `compact=True`: 压缩格式，适合 LLM 处理

### browser_click
点击元素，使用 Ref ID。

```python
# 点击第一个搜索结果
browser_click(ref="@e3")
```

### browser_fill
填充输入框。

```python
# 填写搜索关键词
browser_fill(ref="@e1", text="AI Agent 市场分析")
```

### browser_screenshot
截取关键帧（TimeLapse 用）。

```python
# 保存当前状态截图
browser_screenshot(path="/workspace/screenshots/step1.png")
```

### browser_close
完成后关闭浏览器，释放资源。

```python
browser_close()
```

## 工作流模式

### 模式 1: 搜索+提取
适用于搜索引擎、内容平台。

```
1. browser_open(搜索页面URL)
2. browser_snapshot() → 获取搜索框 ref
3. browser_fill(搜索框ref, 关键词)
4. browser_click(搜索按钮ref)
5. browser_snapshot() → 获取结果列表
6. 遍历结果:
   - browser_click(结果ref)
   - browser_snapshot() → 提取内容
   - 存储到 findings.md
7. browser_close()
```

### 模式 2: 登录+访问
适用于需要认证的平台。

```
1. browser_open(登录页)
2. browser_snapshot() → 获取表单 refs
3. browser_fill(用户名ref, 用户名)
4. browser_fill(密码ref, 密码)
5. browser_click(登录按钮ref)
6. 等待登录完成
7. 导航到目标页面
8. browser_snapshot() → 提取数据
9. browser_close()
```

### 模式 3: 无限滚动
适用于瀑布流内容（小红书、微博等）。

```
1. browser_open(内容页)
2. 循环:
   - browser_snapshot() → 获取当前内容
   - 提取并存储新内容
   - 判断是否足够
   - browser_click(加载更多) 或滚动
3. browser_close()
```

## 最佳实践

### 1. Snapshot 优先原则
- 始终使用 `interactive_only=True, compact=True`
- 每次操作后重新获取 snapshot（页面状态可能变化）
- Ref ID 在页面变化后会失效，需要重新 snapshot

### 2. 关键帧策略
研究过程中，在关键节点截图：
- 搜索结果页
- 重要内容页
- 错误/异常状态

这些截图将用于 TimeLapse 记录，方便用户回溯。

### 3. 错误处理
```python
# 元素未找到时的处理
result = browser_click(ref="@e99")
if result.error:
    # 重新获取 snapshot
    snapshot = browser_snapshot()
    # 查找新的 ref
```

### 4. Session 隔离
每个研究任务使用独立的 browser session，避免状态污染：
```python
# session_id 自动绑定到当前任务
# 多任务并行时互不影响
```

### 5. Context 控制
- Snapshot 结果自动压缩，单次约 500-2000 tokens
- 对比传统 HTML (10K-50K tokens)，节省 93%+
- 不要在 Context 中累积大量 snapshot 历史
- 提取关键信息后，只保留摘要

## 平台特定指南

### 小红书
- 搜索结果需要滚动加载
- 笔记详情在弹窗中，需要 click 打开
- 登录后可访问更多内容

### 淘宝
- 商品搜索结果分页
- 详情页需要处理图片懒加载
- 价格信息可能需要登录

### 微博
- 热搜列表直接可见
- 评论需要展开
- 登录后限制更少

### LinkedIn
- 强制登录
- 页面结构相对稳定
- 注意速率限制

## Token 预算参考

| 操作 | 预估 Tokens | 说明 |
|------|-------------|------|
| browser_open | ~50 | 基础响应 |
| browser_snapshot (compact) | 500-2000 | 取决于页面复杂度 |
| browser_click | ~50 | 基础响应 |
| browser_fill | ~50 | 基础响应 |
| browser_screenshot | ~50 | 只返回路径 |

**对比传统方案**：
- Playwright + HTML: 10K-50K tokens/页
- agent-browser + Snapshot: 500-2K tokens/页
- **节省: 93%+**

## 常见问题

### Q: Ref ID 是什么？
A: agent-browser 为每个可交互元素分配的临时标识符，格式为 `@e1`, `@e2` 等。页面变化后需要重新获取。

### Q: 如何处理验证码？
A: 当前版本暂不支持自动处理验证码。遇到验证码时，记录到 findings.md 并通知用户。

### Q: 多标签页如何处理？
A: 当前每个 session 默认单标签页。如需多标签页，使用多个 session_id。
