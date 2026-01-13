# Getting Started - TokenDance Development

## ✅ Phase 0 Complete: Project Scaffolding

恭喜！项目脚手架已经搭建完成。以下是已完成的工作：

### 后端 (Backend)
- ✅ FastAPI 项目结构
- ✅ Pydantic Settings 配置管理
- ✅ Structlog 结构化日志（带 request_id）
- ✅ Prometheus 指标采集
- ✅ SQLAlchemy 2.0 异步数据库
- ✅ 健康检查端点 (/health, /readiness)
- ✅ 全局错误处理
- ✅ CORS 中间件

### 前端 (Frontend)
- ✅ Vue 3 + TypeScript + Vite
- ✅ Vue Router 路由
- ✅ Pinia 状态管理
- ✅ Axios API 客户端（带拦截器）
- ✅ Tailwind CSS
- ✅ TypeScript strict mode

### 基础设施
- ✅ Docker Compose（PostgreSQL + Redis）
- ✅ 开发环境 Dockerfile
- ✅ 环境变量配置模板
- ✅ .gitignore

---

## 🚀 下一步：启动开发环境

### 方式 1：使用 Docker Compose（推荐）

这是最简单的方式，会自动启动所有服务。

```bash
# 1. 复制环境变量文件
cd backend
cp .env.example .env
# 编辑 .env 填入必要的值（SECRET_KEY, ANTHROPIC_API_KEY 等）

# 2. 启动所有服务
cd ..
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

**注意**：首次启动可能需要 5-10 分钟下载镜像和安装依赖。

**访问应用**：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/api/v1/docs
- 健康检查：http://localhost:8000/health

---

### 方式 2：本地开发（不使用 Docker）

适合需要更快速迭代和调试的场景。

#### 1. 启动基础服务（PostgreSQL + Redis）

```bash
# 只启动数据库和 Redis
docker-compose up -d postgres redis
```

#### 2. 后端开发

```bash
cd backend

# 安装 Poetry（如果还没安装）
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 复制环境变量
cp .env.example .env
# 编辑 .env，设置：
# - SECRET_KEY（至少 32 字符）
# - POSTGRES_HOST=localhost
# - REDIS_HOST=localhost
# - ANTHROPIC_API_KEY（如果有的话）

# 运行数据库迁移（当实现了 Alembic 后）
# poetry run alembic upgrade head

# 启动开发服务器
poetry run python -m app.main
```

后端会在 http://localhost:8000 启动。

#### 3. 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端会在 http://localhost:5173 启动。

---

## 🧪 验证环境

### 测试后端

```bash
# 健康检查
curl http://localhost:8000/health

# 应该返回：
# {"status":"healthy","version":"0.1.0"}

# Readiness 检查
curl http://localhost:8000/readiness

# API 文档
open http://localhost:8000/api/v1/docs
```

### 测试前端

打开浏览器访问 http://localhost:5173，应该看到 "Welcome to TokenDance" 页面。

---

## 📋 待办事项（剩余）

还有 3 个 Phase 0 任务需要完成：

### 1. 配置质量工具链

**后端**：
```bash
cd backend

# 代码格式化
poetry run black app/
poetry run isort app/

# 代码检查
poetry run ruff app/

# 类型检查
poetry run mypy app/

# 运行测试
poetry run pytest
```

**前端**：
```bash
cd frontend

# 代码检查
npm run lint

# 代码格式化
npm run format

# 类型检查
npm run type-check

# 运行测试
npm run test
```

### 2. 建立可观测性基础

- ✅ 日志：已实现 structlog
- ✅ 指标：已实现 Prometheus metrics
- ✅ 健康检查：已实现 /health 和 /readiness
- ⏳ 追踪：OpenTelemetry（可选，后续添加）

### 3. 配置 CI/CD 基础

创建 `.github/workflows/ci.yml` 文件实现：
- Lint & Type Check
- Unit Tests
- Build Docker Image

---

## 🎯 Phase 1 规划：垂直切片 MVP

一旦 Phase 0 完成，我们将开始 Phase 1：

**目标**：在 7-10 天内打通 Personal 模式的完整 E2E 路径

**核心路径**：
```
用户注册 → 创建 Personal Workspace → Agent 简单对话（单轮）→ 文件持久化
```

**开发顺序**：
1. 数据层 + 基础设施（User/Workspace 模型）
2. 认证系统（JWT）
3. Personal Workspace CRUD API
4. FileSystem 基础（路径管理、文件读写）
5. LLM 集成 + 简单对话
6. 前端最简 UI

**Phase 1 成功标准**：
- ✅ 用户可以注册登录
- ✅ 可以创建 Personal Workspace
- ✅ 可以在 Workspace 中与 Agent 进行单轮对话
- ✅ 对话历史保存到文件系统
- ✅ 单元测试覆盖率 > 70%

---

## 💡 开发建议

### 代码规范

**后端**：
- 所有函数/类都要有 docstring
- 使用类型注解（type hints）
- 遵循 PEP 8 规范
- 异步函数使用 `async`/`await`

**前端**：
- 组件使用 `<script setup lang="ts">`
- Props 和 Emits 要有类型定义
- 使用 Composition API
- CSS 使用 Tailwind utility classes

### Git 工作流

```bash
# 创建功能分支
git checkout -b feature/user-auth

# 提交代码
git add .
git commit -m "feat: implement user authentication"

# 推送到远程
git push origin feature/user-auth

# 创建 Pull Request
```

### 调试技巧

**后端**：
- 查看结构化日志：`docker-compose logs -f backend`
- 使用 FastAPI 自动文档：http://localhost:8000/api/v1/docs
- 使用 pytest 调试：`poetry run pytest -v -s`

**前端**：
- Vue Devtools（浏览器扩展）
- 网络请求：浏览器开发者工具 Network 标签
- 日志：`console.log` 或 `console.table`

---

## 🆘 常见问题

### 1. Docker Compose 启动失败

```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# 清理并重启
docker-compose down -v
docker-compose up -d
```

### 2. 后端依赖安装失败

```bash
# 清理缓存
poetry cache clear pypi --all
poetry install
```

### 3. 前端依赖安装失败

```bash
# 清理缓存
rm -rf node_modules package-lock.json
npm install
```

### 4. 数据库连接失败

检查 `.env` 文件中的数据库配置是否正确。

---

## 📚 参考资料

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)
- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)

---

**🎉 恭喜你完成了项目脚手架搭建！现在可以开始愉快地开发了！**
