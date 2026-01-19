# AGENTS.md - TokenDance Backend

> FastAPI + Celery | Python 3.11+ | uv

## Quick Start

```bash
# Setup
uv sync --all-extras

# Run dev server (logs to /tmp/backend.log)
# 稳定模式（多窗口并行开发时推荐）:
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 >> /tmp/backend.log 2>&1 &

# 热加载模式（单窗口开发时使用）:
uv run uvicorn app.main:app --reload >> /tmp/backend.log 2>&1

# Run tests
uv run pytest tests/
```

## Commands

| Command | Purpose |
|---------|---------|
| `uv sync --all-extras` | Install all dependencies |
| `uv run uvicorn app.main:app --reload >> /tmp/backend.log 2>&1` | Dev server (logs to /tmp/backend.log) |
| `uv run pytest tests/` | Run tests with coverage |
| `uv run pytest tests/ -k "test_name"` | Run specific test |
| `uv run ruff check .` | Lint check |
| `uv run ruff check . --fix` | Auto-fix lint issues |
| `uv run mypy .` | Type check (strict mode) |
| `uv run alembic upgrade head` | Apply DB migrations |
| `uv run alembic revision --autogenerate -m "msg"` | Create migration |

## Project Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # Config, security, deps
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   ├── skills/       # Skill definitions
│   │   └── builtin/  # Built-in skills
│   └── main.py       # FastAPI app entry
├── tests/            # All tests here (ONLY)
├── alembic/          # DB migrations
└── pyproject.toml    # Dependencies & config
```

## Testing Rules

- **Location**: `tests/` directory only
- **Naming**: `test_*.py` files, `Test*` classes, `test_*` functions
- **Framework**: pytest + pytest-asyncio
- **Run before commit**: `uv run pytest tests/`
- **Coverage**: Auto-generated to `htmlcov/`
- **MANDATORY**: Every API endpoint MUST have corresponding tests in `tests/`
  - New API → Create test file immediately
  - Modified API → Update tests accordingly
  - This is STRICTLY ENFORCED for code quality

## Code Style

- **Line length**: 100
- **Type hints**: Required (strict mypy)
- **Linting**: ruff (includes isort, flake8, etc.)
- **Run before commit**: `uv run ruff check . && uv run mypy .`

## 代码质量检查 (必须遵循)

**快速全量检测命令:**
```bash
uv run ruff check . && uv run mypy . && uv run pytest tests/ -x -q
```

**各命令作用:**
- `ruff check .` - 代码风格、import 顺序、常见 bug 模式
- `mypy .` - 类型不匹配、枚举用法错误
- `pytest tests/ -x -q` - 运行测试，第一个失败即停止

**CI 必跑:** PR 合并前必须通过 ruff + mypy + pytest

## Enum 定义规范 (必须遵循)

**问题:** SQLAlchemy 默认存储枚举成员名 (如 `PENDING`)，而非 `.value` (如 `pending`)，导致数据库枚举值不匹配。

**解决方案:** 所有 Enum 列必须使用 `values_callable`:

```python
# ✅ 正确写法
from sqlalchemy import Enum

status: Mapped[SessionStatus] = mapped_column(
    Enum(SessionStatus, values_callable=lambda x: [e.value for e in x]),
    default=SessionStatus.PENDING,
    nullable=False
)

# ❌ 错误写法 - 会导致 PENDING/pending 不匹配
status: Mapped[SessionStatus] = mapped_column(
    Enum(SessionStatus), default=SessionStatus.PENDING, nullable=False
)
```

**迁移规范:**
- 写迁移时优先使用 `alembic revision --autogenerate`，它会根据模型生成正确的 enum 值
- 手动写 enum 迁移时，使用 Python Enum 的 `.value` (小写)

## Optional Dependencies

```bash
# Scientific computing
uv sync --extra science-bio    # Bioinformatics
uv sync --extra science-chem   # Chemistry
uv sync --extra science-ml     # ML/Data Science
uv sync --extra science-all    # All science

# Financial data
uv sync --extra finance        # OpenBB, AKShare, etc.
```

## Database

- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Driver**: asyncpg (PostgreSQL)

**Migration workflow:**
1. Modify models in `app/models/`
2. `uv run alembic revision --autogenerate -m "description"`
3. Review generated migration
4. `uv run alembic upgrade head`

## API Conventions

- Pydantic v2 for request/response schemas
- Async endpoints preferred
- Use dependency injection (`Depends()`)
- Error responses: `HTTPException` with proper status codes

## Environment

Copy `.env.example` to `.env` and configure:
- `DATABASE_URL`
- `REDIS_URL`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`

## Logging

**日志输出规则 (必须遵循):**

- 后端日志必须输出到 `/tmp/backend.log`，不要输出到 stdout
- 启动命令: `uv run uvicorn app.main:app --reload >> /tmp/backend.log 2>&1`
- 查看日志: `tail -f /tmp/backend.log`

## 问题排查原则 (必须遵循)

**刨根问底原则:**
- 排查问题时必须追溯到根本原因，不能停留在表面现象
- 讨论问题时必须深入分析，不能敷衍了事
- 执行命令时必须验证结果，不能假设成功
- 遇到错误不轻易放弃，要像硬骨头一样坚持到底
- 每个问题都要问：为什么会发生？根本原因是什么？如何彻底解决？

## Git Workflow

**自动提交规则 (必须遵循):**

每次完成代码修改后，必须自动提交并推送代码：

```bash
# 1. Stage changes
git add <modified-files>

# 2. Commit with descriptive message
git commit -m "<type>(<scope>): <description>

<detailed-changes>

Co-Authored-By: Warp <agent@warp.dev>"

# 3. Push to remote (IMPORTANT)
git push
```

**Commit Message 规范:**
- Type: feat/fix/docs/style/refactor/test/chore
- Scope: backend/frontend/docs/etc
- 必须包含 Co-Authored-By 标记
- 提交后必须立即 push 到远程仓库
