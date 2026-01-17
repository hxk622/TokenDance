# TokenDance 快速启动指南 🚀

> **⚠️ 文档已迁移**: 此文件将于 **2026-03-01** 移动到 [`docs/getting-started/quickstart.md`](docs/getting-started/quickstart.md)
>
> 请更新您的书签。当前内容将保留 6 周以确保向后兼容。

> **5分钟上手，立即体验 Vibe-Agentic Workflow**

---

## ✅ 项目状态

Phase 0（项目脚手架）已完成：

**后端 (FastAPI)**:
- ✅ Pydantic Settings 配置管理
- ✅ Structlog 结构化日志 + request_id
- ✅ Prometheus 指标采集
- ✅ SQLAlchemy 2.0 异步数据库
- ✅ 健康检查端点 + 全局错误处理

**前端 (Vue 3)**:
- ✅ TypeScript + Vue Router + Pinia
- ✅ Axios 客户端（带拦截器）
- ✅ Tailwind CSS + 严格类型检查

**基础设施**:
- ✅ Docker Compose (PostgreSQL + Redis)
- ✅ 环境变量配置模板

---

## 📋 前置要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (可选，Docker启动)
- Redis 7+ (可选，Docker启动)
- Anthropic API Key (用于Agent功能)

---

## ⚡ 方式一：一键启动 (Docker Compose)

最简单的方式，自动启动所有服务：

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 ANTHROPIC_API_KEY

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

**访问应用**：
- 前端：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/api/v1/docs

---

## 🛠️ 方式二：本地开发

适合需要快速迭代和调试的场景。

### 1️⃣ 启动基础服务

```bash
# 只启动数据库和Redis
docker-compose up -d postgres redis
```

### 2️⃣ 启动后端

```bash
cd backend

# 安装uv（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖
uv sync --all-extras

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入：
# - ANTHROPIC_API_KEY（必需）
# - POSTGRES_HOST=localhost
# - REDIS_HOST=localhost

# 应用数据库迁移
uv run alembic upgrade head

# 启动后端服务
uv run uvicorn app.main:app --reload
```

后端运行在 **http://localhost:8000**

### 3️⃣ 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端运行在 **http://localhost:5173**

---

## 📱 访问应用

| 服务 | URL | 说明 |
|------|-----|------|
| **前端应用** | http://localhost:5173 | 主Chat界面 |
| **UI组件演示** | http://localhost:5173/demo | 组件展示页 |
| **后端API** | http://localhost:8000 | REST API |
| **API文档** | http://localhost:8000/api/v1/docs | Swagger UI |
| **健康检查** | http://localhost:8000/health | 系统状态 |

---

## 🎯 核心功能使用

### 💬 Chat 对话

1. **创建新会话**
   - 点击左侧「New Chat」按钮
   - 或首次访问时点击「Start New Chat」

2. **发送消息**
   - 在底部输入框输入问题
   - 按 `Enter` 发送，`Shift+Enter` 换行
   - 实时查看 Agent 的思考过程

3. **查看推理链**
   - **Thinking Block** - Agent 思考过程（可折叠）
   - **Tool Call Block** - 工具调用详情（名称、参数、状态、结果）
   - **Message Content** - 最终回答（支持 Markdown + 代码高亮）

### 🧠 Working Memory（工作记忆）

Manus 三文件工作法的可视化展示：

1. **打开 Working Memory 面板**
   - 点击右上角「Memory」按钮
   - 侧边栏展开，显示三个文件标签

2. **查看三文件内容**
   - **Task Plan** - 任务路线图，Agent 的执行计划
   - **Findings** - 研究发现和技术决策
   - **Progress** - 执行日志和错误追踪

3. **刷新机制**
   - 点击刷新按钮手动更新
   - 发送新消息后自动刷新

---

## 🧪 验证安装

### 方法1：系统检查脚本

```bash
./scripts/check_system.sh
```

成功输出：
```
🔍 TokenDance System Check
================================
Checking Backend (http://localhost:8000)... ✓ Running
Checking Frontend (http://localhost:5173)... ✓ Running
✅ System is ready!
```

### 方法2：手动测试

**测试后端**：
```bash
curl http://localhost:8000/health
# 返回: {"status":"healthy","version":"0.1.0"}
```

**测试前端**：  
打开浏览器访问 http://localhost:5173

**测试数据库**：
```bash
psql -d tokendance -c "SELECT version();"
```

**测试 Redis**：
```bash
redis-cli ping
# 返回: PONG
```

---

## 🔧 常用命令

### 后端命令
```bash
cd backend

# 启动服务
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest

# 代码质量
uv run ruff check app/
uv run mypy app/

# 数据库迁移
uv run alembic upgrade head              # 应用迁移
uv run alembic revision --autogenerate   # 生成迁移
```

### 前端命令
```bash
cd frontend

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 代码检查
npm run lint
npm run type-check

# 运行测试
npm run test
```

### Docker Compose 命令
```bash
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d postgres redis

# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 停止并清理
docker-compose down -v
```

## 🧰 质量工具链

### 后端（在 backend/）
```bash
# 代码格式化
uv run black app/
uv run isort app/

# 代码检查
uv run ruff check app/

# 类型检查
uv run mypy app/

# 单元测试
uv run pytest
```

### 前端（在 frontend/）
```bash
# 代码检查
npm run lint

# 代码格式化（若配置）
npm run format

# 类型检查
npm run type-check

# 单元测试
npm run test
```

## 🧑‍💻 Git 工作流
```bash
# 创建功能分支
git checkout -b feature/<short-name>

# 提交代码
git add .
git commit -m "feat: <message>"

# 推送并创建 PR
git push origin feature/<short-name>
# 然后在远程仓库创建 PR
```

> 提交信息建议包含范围与类型，如 feat/fix/docs/chore，并保持小步提交。

---

## 🐛 常见问题

### Q: 后端无法启动

**症状**：`ModuleNotFoundError`

**解决**：
```bash
cd backend
uv sync --all-extras
```

### Q: 前端显示 "Network Error"

**原因**：后端未启动或 CORS 配置错误

**解决**：
1. 检查后端：`curl http://localhost:8000/health`
2. 检查 `backend/.env` 中的 `BACKEND_CORS_ORIGINS` 包含 `http://localhost:5173`

### Q: Working Memory 面板是空的

**原因**：需要先发送消息触发 Agent

**解决**：
1. 发送任意消息
2. Agent 会自动创建三文件
3. 刷新 Working Memory 面板

### Q: API Key 错误

**症状**：`401 Unauthorized` from Anthropic

**解决**：
1. 检查 `backend/.env` 中的 `ANTHROPIC_API_KEY`
2. 确认 API Key 有效且有余额
3. 访问 https://console.anthropic.com/ 查看配额

### Q: 数据库连接失败

**解决**：
```bash
# 检查 PostgreSQL 状态
docker-compose ps postgres

# 重启数据库
docker-compose restart postgres

# 查看日志
docker-compose logs postgres
```

---

## 💡 开发提示

### 1. 查看后端日志
后端使用 structlog 输出彩色结构化日志：
```bash
cd backend
uv run uvicorn app.main:app --reload
# 实时查看日志输出
```

### 2. 数据库管理
```bash
# 进入数据库
psql -d tokendance

# 列出所有表
\dt

# 查看表结构
\d users

# 退出
\q
```

### 3. 热重载
- **后端**：修改代码后自动重启（`--reload` 模式）
- **前端**：修改代码后自动刷新（Vite HMR）

### 4. API 调试
使用 Swagger UI：http://localhost:8000/api/v1/docs
- 查看所有端点
- 在线测试 API
- 查看请求/响应格式

---

## 📚 下一步

- 📖 阅读上文「🧑‍💻 Git 工作流」与「🧰 质量工具链」章节，完善开发环境
- 🧪 查看 [E2E_TEST_GUIDE.md](E2E_TEST_GUIDE.md) 学习测试
- 🎨 访问 http://localhost:5173/demo 体验 UI 组件
- 📝 阅读 [产品文档](docs/product/PRD.md) 了解设计理念
- 🏗️ 查看 [架构文档](docs/architecture/HLD.md) 理解技术架构

---

**准备好探索 Vibe-Agentic Workflow 了吗？** ✨

有问题？查看文档或提交 [Issue](https://github.com/hxk622/TokenDance/issues)。
