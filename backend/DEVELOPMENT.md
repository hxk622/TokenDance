# TokenDance Backend 开发指南

> FastAPI + Celery | Python 3.11+ | uv

**最后更新**: 2026-01-17

---

## 🚀 快速开始

```bash
# 安装依赖
uv sync --all-extras

# 启动开发服务器
uv run uvicorn app.main:app --reload

# 运行测试
uv run pytest tests/
```

---

## 📋 常用命令

| 命令 | 用途 |
|------|------|
| `uv sync --all-extras` | 安装所有依赖 |
| `uv run uvicorn app.main:app --reload` | 启动开发服务器（端口 8000） |
| `uv run pytest tests/` | 运行测试（含覆盖率） |
| `uv run pytest tests/ -k "test_name"` | 运行特定测试 |
| `uv run ruff check .` | 代码检查 |
| `uv run ruff check . --fix` | 自动修复代码问题 |
| `uv run mypy .` | 类型检查（严格模式） |
| `uv run alembic upgrade head` | 应用数据库迁移 |
| `uv run alembic revision --autogenerate -m "msg"` | 创建迁移 |

---

## 📁 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 配置、安全、依赖注入
│   ├── models/       # SQLAlchemy 模型
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # 业务逻辑
│   ├── skills/       # Skill 定义
│   │   └── builtin/  # 内置 skills
│   └── main.py       # FastAPI 应用入口
├── tests/            # 所有测试（仅此目录）
├── alembic/          # 数据库迁移
└── pyproject.toml    # 依赖与配置
```

---

## 🧪 测试规范

### 规则

- **位置**: 仅 `tests/` 目录
- **命名**: `test_*.py` 文件，`Test*` 类，`test_*` 函数
- **框架**: pytest + pytest-asyncio
- **提交前运行**: `uv run pytest tests/`
- **覆盖率**: 自动生成到 `htmlcov/`

### 示例

```python
# tests/test_example.py
import pytest
from app.services.example import example_function

class TestExample:
    def test_example_function(self):
        result = example_function()
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_function(self):
        result = await async_function()
        assert result is not None
```

---

## 🎨 代码风格

- **行长度**: 100
- **类型提示**: 必需（严格 mypy）
- **Linting**: ruff（包含 isort, flake8 等）
- **提交前运行**: `uv run ruff check . && uv run mypy .`

### 配置

所有配置在 `pyproject.toml` 中：

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
strict = true
```

---

## 🗄️ 数据库

### 技术栈

- **ORM**: SQLAlchemy 2.0（异步）
- **迁移**: Alembic
- **驱动**: asyncpg（PostgreSQL）

### 迁移工作流

1. 修改 `app/models/` 中的模型
2. 生成迁移: `uv run alembic revision --autogenerate -m "description"`
3. 审查生成的迁移文件
4. 应用迁移: `uv run alembic upgrade head`

### 示例模型

```python
from sqlalchemy import Column, Integer, String
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
```

---

## 🔌 API 约定

- **Schemas**: Pydantic v2 用于请求/响应
- **异步优先**: 使用 async/await
- **依赖注入**: 使用 `Depends()`
- **错误响应**: `HTTPException` 配合正确的状态码

### 示例路由

```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService

router = APIRouter()

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends()
):
    try:
        return await service.create_user(user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 📦 可选依赖

```bash
# 科学计算
uv sync --extra science-bio    # 生物信息学
uv sync --extra science-chem   # 化学
uv sync --extra science-ml     # ML/数据科学
uv sync --extra science-all    # 所有科学计算

# 金融数据
uv sync --extra finance        # OpenBB, AKShare 等
```

---

## 🔧 环境配置

复制 `.env.example` 到 `.env` 并配置：

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/tokendance

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENROUTER_API_KEY=sk-or-xxxxx

# 环境
ENVIRONMENT=development
DEBUG=true
```

---

## 🏗️ 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature
```

### 2. 开发

- 遵循 TDD（测试驱动开发）
- 先写测试，再写实现
- 保持小步提交

### 3. 提交前检查

```bash
# 代码检查
uv run ruff check .

# 类型检查
uv run mypy .

# 运行测试
uv run pytest tests/

# 全部通过后提交
git add .
git commit -m "feat: your feature description

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 🔗 相关资源

- [Agent 开发指南](../../docs/guides/developer/agent-development.md)
- [前端开发指南](../../frontend/DEVELOPMENT.md)
- [架构文档](../../docs/architecture/)
- [API 文档](http://localhost:8000/api/v1/docs)（开发服务器运行时）

---

## 💡 提示

- 使用 `uv` 而不是 `pip` 进行依赖管理
- 所有异步代码使用 `async`/`await`
- 数据库操作使用 SQLAlchemy 2.0 异步 API
- API 文档自动生成，访问 `/api/v1/docs`
