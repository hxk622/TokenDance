# TokenDance UI 快速启动指南

> 版本: v0.2.0 (2026-01-13)  
> 状态: ✅ Working Memory UI 已完成

## 🚀 快速启动

### 1. 启动后端服务

```bash
cd backend
poetry run python -m app.main
```

后端将在 http://localhost:8000 启动

### 2. 启动前端服务

```bash
cd frontend
npm run dev
```

前端将在 http://localhost:5173 启动

### 3. 验证系统状态

```bash
./scripts/check_system.sh
```

如果两个服务都在运行，你会看到：
```
✅ System is ready!
```

---

## 📱 访问应用

| 服务 | URL | 说明 |
|------|-----|------|
| 前端应用 | http://localhost:5173 | 主Chat界面 |
| UI演示 | http://localhost:5173/demo | UI组件演示页 |
| 后端API | http://localhost:8000 | REST API |
| API文档 | http://localhost:8000/api/v1/docs | Swagger UI |
| 健康检查 | http://localhost:8000/health | 系统状态 |

---

## 🎯 核心功能使用

### Working Memory（工作记忆）

1. **打开Working Memory面板**
   - 点击右上角的 **Memory** 按钮
   - 侧边栏会展开，显示三个文件标签

2. **查看三文件内容**
   - **Task Plan** - 任务计划和路线图
   - **Findings** - 研究发现和技术决策
   - **Progress** - 执行日志和错误记录

3. **刷新Working Memory**
   - 点击刷新按钮（旋转图标）
   - 或发送新消息后自动刷新

### Chat对话

1. **创建新会话**
   - 点击左侧边栏的 "New Chat" 按钮
   - 或在没有会话时点击中间的 "Start New Chat"

2. **发送消息**
   - 在底部输入框输入你的问题
   - 按Enter或点击发送按钮
   - 实时查看Agent的思考过程

3. **查看推理链**
   - **Thinking Block** - 显示Agent的思考过程（可折叠）
   - **Tool Call Block** - 显示工具调用（名称、参数、状态、结果）
   - **Message Content** - 最终回答（支持Markdown）

---

## 🎨 UI组件演示

访问 http://localhost:5173/demo 查看所有UI组件的演示：

- **ThinkingBlock** - 思考过程可视化
- **ToolCallBlock** - 工具调用展示（4种状态）
- **ProgressIndicator** - 进度指示器
- **WorkingMemory** - 三文件工作法展示
- **色彩系统** - 完整的主题色展示

---

## 📊 已实现的功能

### ✅ 前端 UI

- [x] Chat界面（消息流、输入框）
- [x] Session列表（侧边栏）
- [x] Working Memory面板（三文件Tab切换）
- [x] ThinkingBlock组件（可折叠）
- [x] ToolCallBlock组件（4种状态）
- [x] ProgressIndicator组件
- [x] 深色主题（蓝紫渐变）
- [x] SSE流式响应处理
- [x] HITL确认对话框
- [x] 引用来源卡片

### ✅ 后端 API

- [x] `/api/v1/chat/{session_id}/message` - 发送消息（SSE流）
- [x] `/api/v1/chat/{session_id}/working-memory` - 获取Working Memory
- [x] `/api/v1/chat/{session_id}/confirm` - HITL确认
- [x] `/api/v1/chat/{session_id}/stop` - 停止生成
- [x] `/api/v1/sessions` - Session管理（CRUD）
- [x] `/api/v1/sessions/{id}/messages` - 获取消息列表

### ✅ Agent引擎

- [x] BaseAgent主循环
- [x] BasicAgent实现
- [x] SSE事件生成（7种类型）
- [x] Working Memory三文件系统
- [x] Plan Manager（任务管理）
- [x] 2-Action Rule
- [x] 3-Strike Protocol
- [x] Plan Recitation

---

## 🧪 测试功能

### 测试Working Memory

1. 启动服务后，访问前端
2. 创建新Session
3. 点击右上角的"Memory"按钮
4. 应该看到三个Tab: Task Plan, Findings, Progress
5. 初始内容为默认模板

### 测试SSE流式响应

1. 发送一条消息（例如："Hello"）
2. 应该看到：
   - Thinking Block显示"Analyzing your question..."
   - 然后显示消息内容
   - 最后显示"Done"事件

### 测试UI组件

访问 http://localhost:5173/demo 查看所有组件：
- 确认所有组件正确渲染
- 测试交互（折叠/展开、Tab切换）
- 检查动画效果

---

## 🔧 开发工具

### API文档

访问 http://localhost:8000/api/v1/docs 查看完整的API文档：
- 所有端点列表
- 请求/响应格式
- 在线测试工具

### 系统检查脚本

```bash
./scripts/check_system.sh
```

输出示例：
```
🔍 TokenDance System Check
================================
Checking Backend (http://localhost:8000)... ✓ Running
  Version: 0.1.0
Checking Frontend (http://localhost:5173)... ✓ Running

================================
📡 Testing API Endpoints...
  /health... ✓
  /api/v1/docs... ✓

✅ System is ready!
```

---

## 📋 下一步开发

### 高优先级

1. **MarkdownRenderer组件**
   - 集成`marked`和`highlight.js`
   - 在ChatMessage中渲染Markdown
   - 支持代码高亮

2. **完善HITL机制**
   - Redis状态管理
   - Agent暂停/恢复
   - 超时处理

3. **Tool集成测试**
   - 注册ShellTool, FileOpsTool, WebSearchTool
   - 测试完整的工具调用流程
   - Working Memory自动记录

### 中优先级

4. **ProgressIndicator集成**
   - 在长任务中显示进度
   - 多步骤可视化

5. **Session持久化**
   - 消息保存到数据库
   - 历史会话加载
   - 会话恢复

---

## 🐛 常见问题

### Q: 前端显示"Network Error"

**A:** 检查后端是否正在运行：
```bash
curl http://localhost:8000/health
```

如果没有响应，启动后端：
```bash
cd backend && poetry run python -m app.main
```

### Q: Working Memory面板是空的

**A:** 这是正常的，因为：
1. 需要先发送消息触发Agent
2. Agent会自动创建三文件
3. 刷新Working Memory面板查看内容

### Q: SSE流式响应不工作

**A:** 检查：
1. 浏览器是否支持EventSource（现代浏览器都支持）
2. 网络请求是否被代理/防火墙拦截
3. 后端日志是否有错误

### Q: 如何查看后端日志

**A:** 后端运行时会在控制台输出日志：
```bash
cd backend
poetry run python -m app.main
# 查看实时日志
```

---

## 📝 项目结构

```
TokenDance/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/           # API客户端
│   │   │   ├── chat.ts
│   │   │   ├── session.ts
│   │   │   └── working-memory.ts  ✨ 新增
│   │   ├── components/
│   │   │   ├── chat/      # Chat组件
│   │   │   ├── execution/ # 执行相关组件
│   │   │   │   ├── ThinkingBlock.vue
│   │   │   │   ├── ToolCallBlock.vue
│   │   │   │   ├── ProgressIndicator.vue
│   │   │   │   └── WorkingMemory.vue  ✨
│   │   │   └── session/   # Session组件
│   │   ├── views/
│   │   │   ├── ChatView.vue  ✨ 更新
│   │   │   └── DemoView.vue
│   │   └── stores/        # Pinia状态管理
│   └── package.json
│
├── backend/               # FastAPI后端
│   ├── app/
│   │   ├── api/v1/
│   │   │   └── chat.py    ✨ 更新（+Working Memory API）
│   │   ├── agent/         # Agent引擎
│   │   │   ├── base.py
│   │   │   ├── agents/
│   │   │   ├── working_memory/
│   │   │   │   └── three_files.py
│   │   │   └── planning/
│   │   └── filesystem/    # 文件系统
│   └── pyproject.toml
│
├── scripts/
│   └── check_system.sh    ✨ 新增
│
└── docs/
    └── milestone/
        └── Phase3-UI-Integration-Complete.md  ✨ 新增
```

---

## 🎓 技术栈

### 前端
- **Vue 3** - 前端框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Tailwind CSS** - 样式系统
- **Pinia** - 状态管理
- **Vue Router** - 路由管理

### 后端
- **FastAPI** - Web框架
- **Python 3.11+** - 编程语言
- **Poetry** - 依赖管理
- **PostgreSQL** - 数据库
- **Redis** - 缓存（待集成）

---

## 📚 相关文档

- [开发路线图](docs/Development-Roadmap-v2.md)
- [架构设计](docs/architecture/HLD.md)
- [Phase 3 完成总结](docs/milestone/Phase3-UI-Integration-Complete.md)
- [MVP完成总结](docs/MVP-Complete-Summary.md)
- [UI设计](docs/UI/UI-Design.md)

---

## 🤝 贡献

欢迎贡献代码！请确保：
1. 遵循现有的代码风格
2. 添加必要的类型注解
3. 编写清晰的提交信息
4. 测试你的更改

---

**祝你使用愉快！** 🎉

如有问题，请查看文档或提交Issue。
