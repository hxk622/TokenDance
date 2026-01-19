# AGENTS.md - TokenDance Frontend

> Vue 3 + TypeScript + Tailwind | Vite | pnpm

## Quick Start

```bash
# Setup
pnpm install

# Run dev server (logs to /tmp/frontend.log)
pnpm dev >> /tmp/frontend.log 2>&1

# Build
pnpm build
```

## Commands

| Command | Purpose |
|---------|---------|
| `pnpm dev >> /tmp/frontend.log 2>&1` | Dev server (logs to /tmp/frontend.log) |
| `pnpm build` | Production build |
| `pnpm build:with-check` | Build with type check |
| `pnpm preview` | Preview production build |
| `pnpm lint` | ESLint check & fix |
| `pnpm format` | Prettier format |
| `pnpm type-check` | TypeScript check |
| `pnpm test` | Run Vitest |
| `pnpm test:watch` | Vitest watch mode |

## Project Structure

```
frontend/
├── src/
│   ├── components/   # Vue components
│   ├── views/        # Page views
│   ├── stores/       # Pinia stores
│   ├── composables/  # Vue composables
│   ├── api/          # API client
│   ├── types/        # TypeScript types
│   ├── utils/        # Utility functions
│   ├── assets/       # Static assets
│   ├── App.vue       # Root component
│   └── main.ts       # Entry point
├── public/           # Public static files
└── index.html        # HTML entry
```

## Code Style

- **TypeScript**: Required for all `.ts` and `.vue` files
- **Vue**: Composition API + `<script setup>` syntax
- **Styling**: Tailwind CSS (utility-first)
- **Icons**: Lucide Icons (禁用 Emoji)
- **Run before commit**: `pnpm lint && pnpm type-check`

## Component Conventions

```vue
<script setup lang="ts">
// 1. Imports
// 2. Props & Emits
// 3. Composables & stores
// 4. Reactive state
// 5. Computed
// 6. Methods
// 7. Lifecycle hooks
</script>

<template>
  <!-- Single root element preferred -->
</template>
```

## UI/UX Rules (必读)

**In-Place 交互原则 (核心):**

所有状态变化必须在当前页面内完成，禁止使用全屏过渡页打断用户体验：

- ❌ 禁止：全屏 loading 过渡页（如"正在分析您的任务..."）
- ❌ 禁止：全屏完成页（如"任务已完成！"独立页面）
- ❌ 禁止：任何阻断式的状态切换页面
- ✅ 要求：初始化/思考状态在页面内相应区域展示（如 StreamingInfo 区域）
- ✅ 要求：完成状态用内联效果表示（撒花动画 + 状态标签变化）
- ✅ 要求：错误/确认等交互用 Toast/内联卡片，非全屏弹窗

核心思想：用户应始终感觉 Agent "已经在工作"，而不是"在等待准入许可"。

**禁止:**
- ❌ AI assistant phrases: "我能帮你...", "让我帮你..."
- ❌ Emoji as icons
- ❌ Rainbow gradients, heavy glassmorphism
- ❌ Generic prompts: "帮我...", "生成..."
- ❌ 全屏过渡页/完成页（见 In-Place 原则）

**要求:**
- ✅ User-as-director language
- ✅ Gray palette: #fafafa, #f1f5f9, #111827
- ✅ Transitions: 200-300ms ease
- ✅ Responsive design (mobile-first)
- ✅ Placeholder 颜色使用 `--any-text-muted` (#C4C4C4)，避免视觉疲劳
- ✅ 未激活按钮/标签使用 `--any-text-tertiary` (#888888)，保证可见性

**设计规范 (必须遵循):**

前端设计必须严格遵循以下设计文档:

- `docs/ux/DESIGN-PRINCIPLES.md` - 核心设计原则 (Transparency / Controllability / Persistence)
- `docs/ux/DESIGN-SYSTEM.md` - 设计系统 (色彩/排版/间距/动画标准)
- `docs/ux/EXECUTION-PAGE-LAYOUT.md` - 三栏布局规范

**关键要点:**
- 使用设计系统定义的 CSS 变量 (color/spacing/radius/transition)
- 色球动画使用状态色: cyan (#00D9FF) / green (#00FF88) / amber (#FFB800)
- 字体: Inter (正文) + Space Grotesk (标题)
- 动画: 150ms/200ms/300ms + cubic-bezier 缓动函数
- 毛玻璃效果: backdrop-filter: blur(20px) saturate(180%)

## Theme System (必须遵循)

**所有前端页面必须使用全局主题系统，确保 light/dark 模式统一切换。**

### 核心规则

1. **禁止硬编码颜色值**
   - ❌ `color: #121212` / `background: rgba(255,255,255,0.1)`
   - ✅ `color: var(--any-text-primary)` / `background: var(--any-bg-tertiary)`

2. **使用 `--any-*` CSS 变量** (定义在 `src/styles/anygen.css`)
   ```css
   /* 文字色 */
   --any-text-primary      /* 主文字 */
   --any-text-secondary    /* 次要文字 */
   --any-text-tertiary     /* 弱化文字 */
   --any-text-muted        /* placeholder / 极弱文字 */
   --any-text-inverse      /* 反色文字 (用于深色背景上的浅色文字) */
   
   /* 背景色 */
   --any-bg-primary        /* 主背景 */
   --any-bg-secondary      /* 次要背景 */
   --any-bg-tertiary       /* 三级背景 */
   --any-bg-hover          /* 悬停状态 */
   
   /* 边框色 */
   --any-border            /* 默认边框 */
   --any-border-hover      /* 悬停边框 */
   ```

3. **状态色可保持固定** (品牌特色)
   ```css
   --exec-accent: #00D9FF;   /* cyan - 执行中 */
   --exec-success: #00FF88;  /* green - 成功 */
   --exec-warning: #FFB800;  /* amber - 警告 */
   --exec-error: #FF3B30;    /* red - 错误 */
   ```

4. **页面级变量映射** (如 ExecutionPage)
   ```css
   .my-page {
     --page-bg: var(--any-bg-primary);
     --page-text: var(--any-text-primary);
   }
   ```

5. **主题切换**
   - 使用 `useThemeStore()` 获取/设置主题
   - 默认主题: `dark`
   - 支持: `light` / `dark` / `system`

### 检查清单 (新页面开发时)
- [ ] 所有颜色使用 CSS 变量
- [ ] 在 light 和 dark 模式下测试
- [ ] 交互状态 (hover/active/disabled) 使用主题变量
- [ ] 图标颜色使用 `currentColor` 或主题变量

## State Management

- **Pinia** for global state
- Store files in `src/stores/`
- Use `defineStore` with setup syntax

## API Integration

- **Axios** for HTTP requests
- Base URL from env: `VITE_API_URL`
- Request/response interceptors in `src/api/`

## Testing

- **Framework**: Vitest + @vue/test-utils
- **Location**: `tests/` or co-located `*.spec.ts`
- **Run**: `pnpm test`

## Key Libraries

| Library | Purpose |
|---------|---------|
| vue-router | Routing |
| pinia | State management |
| @vueuse/core | Composition utilities |
| axios | HTTP client |
| echarts / vue-echarts | Charts |
| monaco-editor | Code editor |
| marked + highlight.js | Markdown rendering |

## Logging

**日志输出规则 (必须遵循):**

- 前端日志必须输出到 `/tmp/frontend.log`，不要输出到 stdout
- 启动命令: `pnpm dev >> /tmp/frontend.log 2>&1`
- 查看日志: `tail -f /tmp/frontend.log`

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
