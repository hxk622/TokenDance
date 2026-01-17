# TokenDance Frontend 开发指南

> Vue 3 + TypeScript + Tailwind | Vite | pnpm

**最后更新**: 2026-01-17

---

## 🚀 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev

# 构建生产版本
pnpm build
```

---

## 📋 常用命令

| 命令 | 用途 |
|------|------|
| `pnpm dev` | 启动开发服务器（自动绑定 0.0.0.0） |
| `pnpm build` | 生产构建 |
| `pnpm build:with-check` | 构建前类型检查 |
| `pnpm preview` | 预览生产构建 |
| `pnpm lint` | ESLint 检查并修复 |
| `pnpm format` | Prettier 格式化 |
| `pnpm type-check` | TypeScript 类型检查 |
| `pnpm test` | 运行 Vitest 测试 |
| `pnpm test:watch` | Vitest 监听模式 |

---

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/   # Vue 组件
│   ├── views/        # 页面视图
│   ├── stores/       # Pinia 状态管理
│   ├── composables/  # Vue composables
│   ├── api/          # API 客户端
│   ├── types/        # TypeScript 类型定义
│   ├── utils/        # 工具函数
│   ├── assets/       # 静态资源
│   ├── App.vue       # 根组件
│   └── main.ts       # 入口文件
├── public/           # 公共静态文件
└── index.html        # HTML 入口
```

---

## 🎨 代码风格

- **TypeScript**: 所有 `.ts` 和 `.vue` 文件必需
- **Vue**: Composition API + `<script setup>` 语法
- **样式**: Tailwind CSS（utility-first）
- **图标**: Lucide Icons（**禁用 Emoji**）
- **提交前运行**: `pnpm lint && pnpm type-check`

---

## 🧩 组件约定

### 标准组件结构

```vue
<script setup lang="ts">
// 1. Imports
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 2. Props & Emits
interface Props {
  title: string
  count?: number
}
const props = withDefaults(defineProps<Props>(), {
  count: 0
})

const emit = defineEmits<{
  update: [value: number]
}>()

// 3. Composables & stores
const router = useRouter()

// 4. Reactive state
const isLoading = ref(false)

// 5. Computed
const displayText = computed(() => `${props.title}: ${props.count}`)

// 6. Methods
const handleClick = () => {
  emit('update', props.count + 1)
}

// 7. Lifecycle hooks
onMounted(() => {
  console.log('Component mounted')
})
</script>

<template>
  <div class="p-4">
    <h2 class="text-lg font-semibold">{{ displayText }}</h2>
    <button
      class="mt-2 px-4 py-2 bg-blue-500 text-white rounded cursor-pointer"
      @click="handleClick"
    >
      Click me
    </button>
  </div>
</template>
```

---

## 🎨 UI/UX 规范

### 禁止 (DO NOT)

- ❌ AI 助手话术: "我能帮你...", "让我帮你..."
- ❌ Emoji 作为图标
- ❌ 彩虹渐变、重度玻璃态
- ❌ 通用提示词: "帮我...", "生成..."

### 要求 (DO)

- ✅ 用户主导语言（User-as-director）
- ✅ 灰色调色板: `#fafafa`, `#f1f5f9`, `#111827`
- ✅ 过渡动画: 200-300ms ease
- ✅ 响应式设计（mobile-first）

### 详细规范

参考: [`docs/ux/design-principles.md`](../../docs/ux/design-principles.md)

---

## 🗄️ 状态管理

### Pinia Store 示例

```typescript
// src/stores/user.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)

  // Getters
  const userName = computed(() => user.value?.name ?? 'Guest')

  // Actions
  async function login(credentials: LoginCredentials) {
    const response = await api.login(credentials)
    user.value = response.user
    isAuthenticated.value = true
  }

  function logout() {
    user.value = null
    isAuthenticated.value = false
  }

  return    user,
    isAuthenticated,
    userName,
    login,
    logout
  }
})
```

---

## 🔌 API 集成

- **HTTP 客户端**: Axios
- **Base URL**: 从环境变量 `VITE_API_URL`
- **拦截器**: 在 `src/api/` 中配置

### API 客户端示例

```typescript
// src/api/client.ts
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 10000,
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

---

## 🧪 测试

- **框架**: Vitest + @vue/test-utils
- **位置**: `tests/` 或同位置 `*.spec.ts`
- **运行**: `pnpm test`

### 测试示例

```typescript
// src/components/Button.spec.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import Button from './Button.vue'

describe('Button', () => {
  it('renders properly', () => {
    const wrapper = mount(Button, {
      props: { label: 'Click me' }
    })
    expect(wrapper.text()).toContain('Click me')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted()).toHaveProperty('click')
  })
})
```

---

## 📦 核心库

| 库 | 用途 |
|---|------|
| vue-router | 路由管理 |
| pinia | 状态管理 |
| @vueuse/core | Composition 工具集 |
| axios | HTTP 客户端 |
| echarts / vue-echarts | 图表 |
| monaco-editor | 代码编辑器 |
| marked + highlight.js | Markdown 渲染 |
| lucide-vue-next | 图标库 |

---

## 🏗️ 开发工作流

### 1. 创建功能分支

```bash
git checkout -b feature/your-feature
```

### 2. 开发

- 遵循组件约定
- 使用 TypeScript 类型
- 遵循 UI/UX 规范

### 3. 提交前检查

```bash
# 代码检查
pnpm lint

# 类型检查
pnpm type-check

# 运行测试
pnpm test

# 全部通过后提交
git add .
git commit -m "feat: your feature description

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
```

---

## 🔧 环境变量

创建 `.env.local` 文件：

```bash
# API Base URL
VITE_API_URL=http://localhost:8000

# 其他配置
VITE_APP_TITLE=TokenDance
```

---

## 🔗 相关资源

- [Agent 开发指南](../../docs/guides/developer/agent-development.md)
- [后端开发指南](../../backend/DEVELOPMENT.md)
- [UI/UX 设计原则](../../docs/ux/design-principles.md)
- [组件检查清单](../../docs/ux/component-checklist.md)

---

## 💡 提示

- 使用 `pnpm` 而不是 `npm` 或 `yarn`
- 所有组件使用 Composition API + `<script setup>`
- 优先使用 Tailwind CSS utility classes
- 图标使用 Lucide Icons，不使用 Emoji
- 响应式设计测试: 375px / 768px / 1024px
