# 执行 E2E 自动化测试

## 🚀 快速开始

### 前置条件

1. **启动后端服务**:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

2. **启动前端服务** (另一个终端):
```bash
cd frontend
npm run dev
```

3. **验证服务运行**:
- 后端: http://localhost:8000/health
- 前端: http://localhost:5173

## 📝 测试步骤（使用AI Agent执行）

### 测试1: 基础页面加载测试

**指令给AI Agent**:
```
请使用Chrome DevTools工具执行以下测试：

1. 创建新页面并导航到 http://localhost:5173/chat
2. 等待页面加载完成（等待"TokenDance"文本出现）
3. 获取页面快照
4. 截图保存到 test_screenshots/01_page_load.png
5. 验证页面是否包含"Chat"或"消息"相关元素
```

### 测试2: 发送消息测试

**指令给AI Agent**:
```
请执行以下测试：

1. 在已打开的页面中，获取页面快照
2. 找到消息输入框（查找包含"input"或"textarea"的元素）
3. 填写消息："帮我研究AI Agent市场"
4. 找到发送按钮并点击
5. 等待"Agent 思考中"或类似文本出现（最多等待10秒）
6. 截图保存到 test_screenshots/02_message_sent.png
```

### 测试3: SSE流式接收测试

**指令给AI Agent**:
```
请执行以下测试：

1. 在消息发送后，监听网络请求
2. 查找包含"event-stream"或"/api/v1/chat"的请求
3. 验证SSE连接是否建立
4. 等待Agent响应内容出现（等待包含"研究"或"市场"的文本）
5. 截图保存到 test_screenshots/03_sse_response.png
```

### 测试4: Working Memory测试

**指令给AI Agent**:
```
请执行以下测试：

1. 在页面中查找"Working Memory"或"Memory"按钮
2. 点击该按钮
3. 等待"task_plan.md"或"findings.md"文本出现
4. 验证三个Tab是否都存在（task_plan, findings, progress）
5. 截图保存到 test_screenshots/04_working_memory.png
```

### 测试5: 性能测试

**指令给AI Agent**:
```
请执行性能测试：

1. 开始性能追踪
2. 刷新页面
3. 等待页面完全加载
4. 停止性能追踪
5. 分析性能数据，检查：
   - First Contentful Paint < 2000ms
   - Time to Interactive < 3000ms
6. 保存性能报告
```

## 🎯 完整测试流程

**一次性执行所有测试的指令**:

```
请使用Chrome DevTools工具执行完整的E2E测试：

1. 创建新页面，导航到 http://localhost:5173/chat
2. 等待页面加载，截图保存
3. 发送测试消息："帮我研究AI Agent市场"
4. 验证SSE流式接收
5. 验证Working Memory显示
6. 执行性能测试
7. 生成测试报告（列出所有截图和验证结果）
```

## 📊 验证点

每个测试应该验证：

- ✅ 页面正常加载
- ✅ 元素可交互
- ✅ 网络请求正常
- ✅ 响应时间合理
- ✅ 错误处理正确
- ✅ UI更新及时

## 🐛 调试

如果测试失败：

1. **查看截图**: `test_screenshots/` 目录
2. **检查网络请求**: 使用 `list_network_requests` 工具
3. **查看控制台**: 使用 `list_console_messages` 工具
4. **获取页面快照**: 使用 `take_snapshot` 查看当前页面状态

## 💡 提示

- 使用 `take_snapshot` 获取元素uid，而不是猜测
- 合理设置timeout，避免测试超时
- 每个测试步骤后截图，便于问题定位
- 使用 `wait_for` 等待异步操作完成

---

**使用方式**: 将上述指令复制给AI Agent，让它使用Chrome DevTools工具执行测试
