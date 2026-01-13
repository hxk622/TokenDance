# 快速启动指南（本地开发）

## ✅ 环境已配置完成

你的开发环境已经准备就绪：
- ✅ PostgreSQL 运行中，数据库 `tokendance` 已创建
- ✅ Redis 运行中
- ✅ Python 依赖已安装（Poetry）
- ✅ 环境变量已配置（backend/.env）

---

## 🚀 启动后端服务

```bash
cd /Users/xingkaihan/Documents/Code/TokenDance/backend
$HOME/.local/bin/poetry run python -m app.main
```

后端将在 **http://localhost:8000** 启动

可以访问：
- API 文档：http://localhost:8000/api/v1/docs
- 健康检查：http://localhost:8000/health

---

## 🎨 启动前端服务

打开新终端窗口：

```bash
cd /Users/xingkaihan/Documents/Code/TokenDance/frontend
npm install  # 首次运行需要
npm run dev
```

前端将在 **http://localhost:5173** 启动

---

## 📝 下一步：创建数据库迁移

在启动后端之前，需要先创建数据库表：

```bash
cd /Users/xingkaihan/Documents/Code/TokenDance/backend

# 生成迁移文件
$HOME/.local/bin/poetry run alembic revision --autogenerate -m "Initial: User and Workspace models"

# 应用迁移
$HOME/.local/bin/poetry run alembic upgrade head
```

---

## 🧪 验证环境

### 测试 PostgreSQL 连接
```bash
psql -d tokendance -c "SELECT version();"
```

### 测试 Redis 连接
```bash
redis-cli ping
```

应该返回 `PONG`

---

## 🔧 常用命令

### Poetry 命令（添加PATH后）
```bash
export PATH="$HOME/.local/bin:$PATH"
cd backend
poetry run python -m app.main      # 启动后端
poetry run pytest                  # 运行测试
poetry run black app/              # 格式化代码
poetry run mypy app/               # 类型检查
```

### 前端命令
```bash
cd frontend
npm run dev           # 开发服务器
npm run build         # 构建生产版本
npm run lint          # 代码检查
npm run test          # 运行测试
```

---

## 💡 提示

1. **永久添加 Poetry 到 PATH**：
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

2. **查看后端日志**：
   后端会输出彩色结构化日志到控制台

3. **数据库管理**：
   ```bash
   psql -d tokendance  # 进入数据库
   \dt                 # 列出所有表
   \q                  # 退出
   ```

---

**准备好了吗？让我们开始实现认证系统！** 🚀
