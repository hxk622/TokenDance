# AGENTS.md - TokenDance

> Vibe-Agentic Workflow Platform - 人机共生的智能工作台

## Quick Context

TokenDance 是 Agent Runtime，不是通用智能体。核心架构详见 `docs/architecture/Agent-Runtime-Design.md`。

**Tech Stack**: Vue 3 + TypeScript + Tailwind | FastAPI + Celery | PostgreSQL + Neo4j + Redis

## Dev Environment

### Prerequisites
- Node.js 18+ with pnpm
- Python 3.11+ with uv
- Docker (for sandbox)

### Setup
```bash
# Frontend
pnpm install

# Backend
cd backend && uv sync --all-extras
```

## Commands Reference

| Command | Purpose |
|---------|---------|
| `cd frontend && pnpm dev` | Start Vue dev server |
| `cd backend && uv run uvicorn app.main:app --reload` | Start FastAPI dev server |
| `cd backend && uv run pytest tests/` | Run backend tests |
| `cd backend && uv run ruff check . && uv run mypy .` | Lint & type check |
| `pnpm lint` | Frontend lint |

## Testing Instructions

- Backend tests: `backend/tests/` directory only
- Test file naming: `test_*.py`
- Test class naming: `Test*`
- Run full suite before committing: `cd backend && uv run pytest tests/`
- Fix all type errors: `uv run mypy .`

## Git & PR Guidelines

**Commit format:**
```
feat: <brief description>

<details>

Co-Authored-By: Warp <agent@warp.dev>
```

**Rules:**
- Commit after completing each component/bug fix/TODO item
- Always include co-author line
- Run lint and tests before committing

## Project Structure

```
TokenDance/
├── frontend/         # Vue 3 + TypeScript + Shadcn/UI + Tailwind
├── backend/          # FastAPI + Celery
│   ├── app/
│   │   ├── skills/   # Skill definitions
│   │   └── ...
│   └── tests/        # All tests here
└── docs/             # Design documents
```

## Three-File Workflow (三文件工作法)

For complex tasks, use these files in `docs/milestone/current/`:

| File | Purpose |
|------|---------|
| `task_plan.md` | Task breakdown & phases |
| `findings.md` | Research results & decisions |
| `progress.md` | Execution log & errors |

**Key rules:**
- Every 2 major operations (web_search/read_url) → write to `findings.md`
- All errors → log to `progress.md`
- Re-read `task_plan.md` before starting new work

## Agent Behavior Guidelines

### DO:
- Identify risks proactively (performance, security, UX)
- Suggest better alternatives with reasoning
- Question unreasonable requirements
- Consider edge cases, a11y, error handling

### DON'T:
- Blindly follow obviously wrong designs
- Skip error handling
- Ignore mobile responsiveness

### Output format for issues:
```markdown
## ⚠️ Issue: [title]
**Current**: ...
**Problem**: ...
**Suggestion**: ...
```

## UI/UX Constraints

**禁止 (DO NOT):**
- ❌ AI assistant phrases: "我能帮你...", "让我帮你..."
- ❌ Emoji as icons - use Lucide Icons
- ❌ Rainbow gradients, heavy glassmorphism
- ❌ Generic prompts: "帮我...", "生成..."

**要求 (DO):**
- ✅ User-as-director language
- ✅ Restrained gray palette (#fafafa, #f1f5f9)
- ✅ Transitions: 200-300ms ease
- ✅ Reference: Linear, Notion, Vercel

## Key Documents (必读)

| Document | Content |
|----------|---------|
| `docs/product/VisionAndMission.md` | Product vision |
| `docs/architecture/Agent-Runtime-Design.md` | Agent Runtime 5 laws |
| `docs/ux/DESIGN-PRINCIPLES.md` | UI design principles |
| `docs/ux/EXECUTION-PAGE-LAYOUT.md` | Three-column layout spec |

## Financial Research Constraints (金融场景)

If working on financial features:
- ❌ No stock price predictions
- ❌ No buy/sell recommendations
- ❌ No return promises
- ❌ No insider information

## Reminders

- Context Graph records all decision traces
- Large results → file system, context only gets summary
- Context > 50K tokens → auto-summarize
- Plans/TODOs always appended to context end
- **规则同步**: 所有项目规则变动必须更新到 AGENTS.md，确保其他 Coding Agent 可理解本项目
