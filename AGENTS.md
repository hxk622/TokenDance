# AGENTS.md - TokenDance

> **⚠️ 文档已迁移**: 此文件将于 **2026-03-01** 拆分并迁移到：
> - 核心 Agent 开发指南: [`docs/guides/developer/agent-development.md`](docs/guides/developer/agent-development.md)
> - 后端开发指南: [`backend/DEVELOPMENT.md`](backend/DEVELOPMENT.md)
> - 前端开发指南: [`frontend/DEVELOPMENT.md`](frontend/DEVELOPMENT.md)
>
> 请更新您的书签。当前内容将保留 6 周以确保向后兼容。

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
- **Auto-commit**: 完成任务后自动提交代码，无需等待用户确认
- Commit after completing each component/bug fix/TODO item
- Always include co-author line
- Run lint and tests before committing
- **Branching**: 在 master 分支直接开发，目前不拉分支

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

## Development Skills (开发技能)

### 🔍 Systematic Debugging (系统化调试)

**铁律**: 不找到根因不提 Fix

**四阶段流程**:
1. **Root Cause** - 读错误、复现、查 git diff、追踪数据流
2. **Pattern** - 找工作的例子，对比差异
3. **Hypothesis** - 单一假设，最小改动验证
4. **Implementation** - 先写失败测试，再修复

**3 次失败后**: 停下来质疑架构，不要继续猜

### ✅ TDD (测试驱动开发)

**铁律**: 没有失败的测试，不写实现代码

**红绿重构循环**:
1. **RED** - 写失败测试，运行确认失败
2. **GREEN** - 写最小实现，运行确认通过
3. **REFACTOR** - 重构，保持绿色

**禁止**: 先写代码后补测试、测试立即通过、"就这一次跳过"

### 🎯 Verification Before Completion (完成前验证)

**铁律**: 证据先于断言

**流程**:
1. 识别验证命令 (什么证明完成?)
2. 运行完整命令 (不是"应该行")
3. 读完整输出 + 检查 exit code
4. 确认后才能宣称完成

**禁止词汇**: "should", "probably", "seems to", "应该没问题了"

### 🎨 UI/UX Pre-Delivery Checklist

提交前检查:
- [ ] 无 emoji 图标 (用 Lucide Icons)
- [ ] 所有可点击元素有 `cursor-pointer`
- [ ] 浅色模式对比度 ≥ 4.5:1
- [ ] 过渡 200-300ms
- [ ] 响应式: 375px / 768px / 1024px

---

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

## Documentation Maintenance (文档维护原则)

**核心原则**: 文档要压缩和变更，不要只追加内容

**DO:**
- ✅ 更新文档时，先审视现有内容是否需要合并/删除
- ✅ 相似内容合并到一处，避免重复
- ✅ 过时内容及时删除或标记 deprecated
- ✅ 保持文档结构清晰，层级不超过 3 级
- ✅ 每个文档控制在合理长度（建议 < 500 行）

**DON'T:**
- ❌ 只追加不删除，导致文档膨胀
- ❌ 同一信息在多处重复
- ❌ 保留过时/冲突的内容
- ❌ 无限嵌套的目录结构

**变更时检查清单:**
1. 是否有可以合并的相似章节？
2. 是否有过时需要删除的内容？
3. 新增内容是否与现有内容冲突？
4. 文档长度是否仍在合理范围？

---

## Reminders

- Context Graph records all decision traces
- Large results → file system, context only gets summary
- Context > 50K tokens → auto-summarize
- Plans/TODOs always appended to context end
- **规则同步**: 所有项目规则变动必须更新到 AGENTS.md，确保其他 Coding Agent 可理解本项目
- **文档维护**: 更新文档时要压缩和变更，不要只追加内容，防止文档爆炸和内容混乱
