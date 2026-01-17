# AGENTS.md - TokenDance Frontend

> Vue 3 + TypeScript + Tailwind | Vite | pnpm

## Quick Start

```bash
# Setup
pnpm install

# Run dev server
pnpm dev

# Build
pnpm build
```

## Commands

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Dev server (auto host 0.0.0.0) |
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

**禁止:**
- ❌ AI assistant phrases: "我能帮你...", "让我帮你..."
- ❌ Emoji as icons
- ❌ Rainbow gradients, heavy glassmorphism
- ❌ Generic prompts: "帮我...", "生成..."

**要求:**
- ✅ User-as-director language
- ✅ Gray palette: #fafafa, #f1f5f9, #111827
- ✅ Transitions: 200-300ms ease
- ✅ Responsive design (mobile-first)

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
