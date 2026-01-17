# AGENTS.md - TokenDance Backend

> FastAPI + Celery | Python 3.11+ | uv

## Quick Start

```bash
# Setup
uv sync --all-extras

# Run dev server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest tests/
```

## Commands

| Command | Purpose |
|---------|---------|
| `uv sync --all-extras` | Install all dependencies |
| `uv run uvicorn app.main:app --reload` | Dev server (port 8000) |
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

## Code Style

- **Line length**: 100
- **Type hints**: Required (strict mypy)
- **Linting**: ruff (includes isort, flake8, etc.)
- **Run before commit**: `uv run ruff check . && uv run mypy .`

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
