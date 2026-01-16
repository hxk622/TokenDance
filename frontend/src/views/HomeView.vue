<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import FileDropZone from '@/components/home/FileDropZone.vue'

const router = useRouter()
const inputValue = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 加载状态
const isLoading = ref(false)

// 三位一体架构 (The Trinity) - 非功能导向，而是能力导向
const trinityCapabilities = [
  {
    id: 'manus',
    name: 'Manus',
    role: '执行大脑',
    desc: '全自动任务链，从 0 到 1 交付',
    icon: 'cpu'
  },
  {
    id: 'coworker',
    name: 'Coworker',
    role: '执行双手',
    desc: '本地文件深度操控',
    icon: 'folder-open'
  },
  {
    id: 'vibe',
    name: 'Vibe',
    role: '生命气息',
    desc: '直觉交互，氛围感体验',
    icon: 'sparkles'
  }
]

// 工作流卡片 - 以用户任务为中心
const workflows = [
  {
    id: 'research',
    title: '市场调研',
    subtitle: '竞品分析 · 行业报告 · 数据洞察',
    icon: 'chart-bar',
    accent: 'indigo',
    featured: true // Deep Research MVP 强调
  },
  {
    id: 'presentation',
    title: '演示汇报',
    subtitle: '方案展示 · 周报总结 · 培训材料',
    icon: 'presentation',
    accent: 'amber',
    featured: false
  },
  {
    id: 'development',
    title: '开发调试',
    subtitle: '代码审查 · 性能优化 · Bug 排查',
    icon: 'code',
    accent: 'emerald',
    featured: false
  }
]

// 场景引导示例 - 用户任务导向
const suggestions = [
  '调研 2025 年 AI Agent 市场趋势',
  '把这份报告做成 10 页 PPT',
  '分析这份 CSV 数据并生成图表'
]

// 快捷操作
const quickActions = [
  { id: 'research', label: '深度研究', icon: 'search' },
  { id: 'ppt', label: '演示汇报', icon: 'presentation' },
  { id: 'code', label: '代码分析', icon: 'code' }
]

// 最近项目
const recentProjects = [
  { id: '1', name: '2024 Q4 竞品分析', time: '2 小时前', status: 'completed' },
  { id: '2', name: '产品路演 PPT', time: '昨天', status: 'in-progress' },
  { id: '3', name: 'API 性能优化', time: '3 天前', status: 'completed' }
]

// 动态氛围：色球动画状态
const activeOrbIndex = ref(0)
let orbInterval: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  // 色球轮播动画
  orbInterval = setInterval(() => {
    activeOrbIndex.value = (activeOrbIndex.value + 1) % 3
  }, 2500)
})

onUnmounted(() => {
  if (orbInterval) clearInterval(orbInterval)
})

// 处理工作流选择
const handleWorkflowSelect = (workflow: typeof workflows[0]) => {
  router.push({
    path: '/chat',
    query: { workflow: workflow.id }
  })
}

// 处理最近项目点击
const handleProjectClick = (project: typeof recentProjects[0]) => {
  router.push({
    path: `/chat/${project.id}`
  })
}

// 处理文件拖拽
const handleFileDrop = (files: FileList) => {
  console.log('Files dropped:', files)
  const fileNames = Array.from(files).map(f => f.name).join(', ')
  router.push({
    path: '/chat',
    query: { files: fileNames }
  })
}

// 处理提交
const handleSubmit = () => {
  if (!inputValue.value.trim()) return
  router.push({
    path: '/chat',
    query: { q: inputValue.value }
  })
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

// 处理场景建议点击
const handleSuggestionClick = (suggestion: string) => {
  inputValue.value = suggestion
  inputRef.value?.focus()
}

// 处理快捷操作
const handleQuickAction = (action: typeof quickActions[0]) => {
  router.push({
    path: '/chat',
    query: { mode: action.id }
  })
}

// 处理附件按钮点击
const handleAttachClick = () => {
  fileInputRef.value?.click()
}

// 处理文件选择
const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    handleFileDrop(input.files)
  }
}

// Guest 试用
const handleGuestTry = async () => {
  isLoading.value = true
  // 模拟加载延迟，实际可改为 API 调用
  await new Promise(resolve => setTimeout(resolve, 300))
  router.push({ path: '/chat', query: { guest: 'true' } })
}

// Cmd+K 键盘快捷键
function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    inputRef.value?.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="home-view">
    <!-- Vibe Background with Animated Orbs -->
    <div class="bg-vibe">
      <div class="bg-gradient" />
      <div class="bg-pattern" />
      <!-- 动态色球 -->
      <div class="orb-container">
        <div 
          class="orb orb-manus" 
          :class="{ 'orb-active': activeOrbIndex === 0 }"
        />
        <div 
          class="orb orb-coworker" 
          :class="{ 'orb-active': activeOrbIndex === 1 }"
        />
        <div 
          class="orb orb-vibe" 
          :class="{ 'orb-active': activeOrbIndex === 2 }"
        />
        <!-- 能量连线 -->
        <svg class="energy-lines" viewBox="0 0 400 100" preserveAspectRatio="none">
          <defs>
            <linearGradient id="energy-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#6366f1" stop-opacity="0.3" />
              <stop offset="50%" stop-color="#10b981" stop-opacity="0.6" />
              <stop offset="100%" stop-color="#06b6d4" stop-opacity="0.3" />
            </linearGradient>
          </defs>
          <path class="energy-line" d="M 50 50 Q 125 20 200 50 T 350 50" />
        </svg>
      </div>
    </div>
    
    <!-- Header -->
    <header class="home-header">
      <div class="header-left">
        <h1 class="logo">TokenDance</h1>
      </div>
      <div class="header-right">
        <router-link to="/demo" class="header-btn">能力演示</router-link>
        <a href="https://github.com/your-repo/tokendance" target="_blank" class="header-btn">文档</a>
        <button class="header-btn header-btn-primary">登录</button>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="home-main">
      <!-- Hero: 差异化 Slogan + Guest CTA -->
      <section class="hero">
        <p class="hero-tagline">For the rest of the world</p>
        <h2 class="hero-title">让硬核 Agent 服务全世界</h2>
        <p class="hero-desc">和 Agent 一起完成任务，随时接管和调整</p>
        <!-- Guest CTA 强化 -->
        <div class="hero-cta">
          <button class="cta-primary" :disabled="isLoading" @click="handleGuestTry">
            <!-- Loading Spinner -->
            <svg v-if="isLoading" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            {{ isLoading ? '启动中...' : '免费试用' }}
          </button>
          <router-link to="/demo" class="cta-secondary">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            查看演示
          </router-link>
        </div>
      </section>
      
      <!-- 三位一体可视化 (The Trinity) -->
      <section class="trinity-section">
        <div class="trinity-grid">
          <div 
            v-for="(cap, index) in trinityCapabilities" 
            :key="cap.id"
            class="trinity-card"
            :class="{ 'trinity-card-active': activeOrbIndex === index }"
          >
            <div class="trinity-icon" :class="`trinity-icon--${cap.id}`">
              <!-- Manus: CPU -->
              <svg v-if="cap.icon === 'cpu'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 3v2m6-2v2M9 19v2m6-2v2M3 9h2m-2 6h2m14-6h2m-2 6h2M9 9h6v6H9V9z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 5h14a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z" />
              </svg>
              <!-- Coworker: Folder -->
              <svg v-else-if="cap.icon === 'folder-open'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
              <!-- Vibe: Sparkles -->
              <svg v-else class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
              </svg>
            </div>
            <div class="trinity-content">
              <span class="trinity-name">{{ cap.name }}</span>
              <span class="trinity-role">{{ cap.role }}</span>
              <span class="trinity-desc">{{ cap.desc }}</span>
            </div>
          </div>
        </div>
      </section>
      
      <!-- P0: Deep Research 入口强化 -->
      <section class="featured-section">
        <button class="featured-card" @click="handleWorkflowSelect(workflows[0])">
          <div class="featured-badge">MVP 核心能力</div>
          <div class="featured-icon">
            <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div class="featured-content">
            <h3 class="featured-title">市场调研</h3>
            <p class="featured-desc">多源搜索 · 信息综合 · 结构化报告</p>
          </div>
          <div class="featured-action">
            <span>立即开始</span>
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </div>
        </button>
      </section>
      
      <!-- Enhanced Input -->
      <section class="input-section">
        <div class="input-container">
          <div class="input-wrapper">
            <!-- 附件按钮 -->
            <button class="attach-btn" @click="handleAttachClick" title="添加附件">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                      d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
            </button>
            <input type="file" ref="fileInputRef" class="hidden" multiple @change="handleFileSelect" />
            
            <input
              ref="inputRef"
              v-model="inputValue"
              type="text"
              class="main-input"
              placeholder="描述你要完成的任务... (Cmd+K)"
              @keydown="handleKeydown"
            />
            <button 
              class="input-submit"
              :disabled="!inputValue.trim()"
              @click="handleSubmit"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            </button>
          </div>
          
          <!-- 快捷操作 -->
          <div class="quick-actions">
            <button
              v-for="action in quickActions"
              :key="action.id"
              class="quick-action-btn"
              @click="handleQuickAction(action)"
            >
              <svg v-if="action.icon === 'search'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <svg v-else-if="action.icon === 'presentation'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
              <span>{{ action.label }}</span>
            </button>
          </div>
        </div>
      </section>
      
      <!-- 场景引导 -->
      <section class="suggestions-section">
        <h3 class="section-title">试试这些</h3>
        <div class="suggestions-list">
          <button
            v-for="(suggestion, index) in suggestions"
            :key="index"
            class="suggestion-item"
            @click="handleSuggestionClick(suggestion)"
          >
            <svg class="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>{{ suggestion }}</span>
          </button>
        </div>
      </section>
      
      <!-- Workflows (排除 featured 的 Deep Research) -->
      <section class="workflows-section">
        <h3 class="section-title">更多工作流</h3>
        <div class="workflows-grid">
          <button
            v-for="wf in workflows.filter(w => !w.featured)"
            :key="wf.id"
            class="workflow-card"
            :class="`workflow-card--${wf.accent}`"
            @click="handleWorkflowSelect(wf)"
          >
            <div class="workflow-icon">
              <svg v-if="wf.icon === 'presentation'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <svg v-else class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
              </svg>
            </div>
            <div class="workflow-content">
              <span class="workflow-title">{{ wf.title }}</span>
              <span class="workflow-subtitle">{{ wf.subtitle }}</span>
            </div>
            <svg class="workflow-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </section>
      
      <!-- Recent Projects -->
      <section class="recent-section">
        <h3 class="section-title">最近项目</h3>
        <div class="recent-list">
          <button
            v-for="project in recentProjects"
            :key="project.id"
            class="recent-item"
            @click="handleProjectClick(project)"
          >
            <div class="recent-status" :class="`recent-status--${project.status}`" />
            <span class="recent-name">{{ project.name }}</span>
            <span class="recent-time">{{ project.time }}</span>
          </button>
        </div>
      </section>
      
      <!-- Drop Zone -->
      <section class="drop-section">
        <FileDropZone @drop="handleFileDrop" />
      </section>
    </main>
    
    <!-- Footer -->
    <footer class="home-footer">
      <p>随时接管 · 实时干预 · 沉淀复用</p>
    </footer>
  </div>
</template>

<style scoped>
.home-view {
  @apply relative min-h-screen flex flex-col;
  background: #fafafa;
}

/* Dark mode support */
:global(.dark) .home-view {
  background: #0a0a0b;
}

:global(.dark) .home-header {
  @apply border-gray-800;
  background: rgba(20, 20, 21, 0.8);
}

:global(.dark) .logo {
  @apply text-white;
}

:global(.dark) .header-btn {
  @apply text-gray-300 hover:text-white;
}

:global(.dark) .header-btn-primary {
  @apply bg-white text-gray-900 hover:bg-gray-100;
}

:global(.dark) .hero-tagline {
  @apply text-indigo-400;
}

:global(.dark) .hero-title {
  @apply text-white;
}

:global(.dark) .hero-desc {
  @apply text-gray-400;
}

:global(.dark) .cta-primary {
  @apply bg-white text-gray-900 hover:bg-gray-100;
}

:global(.dark) .cta-secondary {
  @apply bg-gray-800 border-gray-700 text-gray-200 hover:bg-gray-700 hover:border-gray-600;
}

:global(.dark) .trinity-card {
  @apply bg-gray-900/50 border-gray-800;
}

:global(.dark) .trinity-card:hover,
:global(.dark) .trinity-card-active {
  @apply bg-gray-900 border-gray-700;
}

:global(.dark) .trinity-name {
  @apply text-white;
}

:global(.dark) .trinity-role,
:global(.dark) .trinity-desc {
  @apply text-gray-400;
}

:global(.dark) .featured-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(20, 20, 21, 0.9));
  @apply border-indigo-900/50;
}

:global(.dark) .featured-card:hover {
  @apply border-indigo-700/50;
}

:global(.dark) .featured-badge {
  @apply bg-indigo-900/50 text-indigo-300;
}

:global(.dark) .featured-icon {
  @apply bg-indigo-900/50 text-indigo-400;
}

:global(.dark) .featured-title {
  @apply text-white;
}

:global(.dark) .featured-desc {
  @apply text-gray-400;
}

:global(.dark) .featured-action {
  @apply bg-gray-800 border-gray-700 text-indigo-400;
}

:global(.dark) .input-wrapper {
  @apply bg-gray-900 border-gray-700;
}

:global(.dark) .input-wrapper:focus-within {
  @apply border-gray-500;
}

:global(.dark) .attach-btn {
  @apply text-gray-500 hover:text-gray-300 hover:bg-gray-800;
}

:global(.dark) .main-input {
  @apply text-white placeholder-gray-500;
}

:global(.dark) .input-submit {
  @apply bg-white text-gray-900 hover:bg-gray-100;
}

:global(.dark) .input-submit:disabled {
  @apply bg-gray-700 text-gray-500;
}

:global(.dark) .quick-action-btn {
  @apply bg-gray-900 border-gray-700 text-gray-300 hover:border-gray-600 hover:bg-gray-800;
}

:global(.dark) .section-title {
  @apply text-gray-500;
}

:global(.dark) .suggestion-item {
  @apply bg-gray-900/60 border-gray-800 text-gray-300 hover:bg-gray-900 hover:border-gray-700;
}

:global(.dark) .workflow-card {
  @apply bg-gray-900 border-gray-800 hover:border-gray-700;
}

:global(.dark) .workflow-title {
  @apply text-white;
}

:global(.dark) .workflow-subtitle {
  @apply text-gray-400;
}

:global(.dark) .workflow-arrow {
  @apply text-gray-600;
}

:global(.dark) .workflow-card:hover .workflow-arrow {
  @apply text-gray-400;
}

:global(.dark) .recent-item {
  @apply bg-gray-900 border-gray-800 hover:border-gray-700;
}

:global(.dark) .recent-name {
  @apply text-gray-300;
}

:global(.dark) .recent-time {
  @apply text-gray-500;
}

:global(.dark) .home-footer p {
  @apply text-gray-500;
}

/* Vibe Background */
.bg-vibe {
  @apply absolute inset-0 -z-10 overflow-hidden;
}

.bg-gradient {
  @apply absolute inset-0;
  background: 
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.08), transparent),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(139, 92, 246, 0.05), transparent),
    radial-gradient(ellipse 50% 30% at 20% 80%, rgba(6, 182, 212, 0.04), transparent);
}

.bg-pattern {
  @apply absolute inset-0 opacity-[0.02];
  background-image: 
    linear-gradient(to right, #000 1px, transparent 1px),
    linear-gradient(to bottom, #000 1px, transparent 1px);
  background-size: 24px 24px;
}

/* Header */
.home-header {
  @apply flex items-center justify-between px-8 py-4 border-b border-gray-100;
  background: rgba(255,255,255,0.8);
  backdrop-filter: blur(8px);
}

.logo {
  @apply text-xl font-semibold text-gray-900 tracking-tight;
}

.header-right {
  @apply flex items-center gap-2;
}

.header-btn {
  @apply px-4 py-2 text-sm text-slate-600 hover:text-slate-900 
         cursor-pointer transition-colors duration-200;
}

.header-btn-primary {
  @apply bg-gray-900 text-white rounded-lg hover:bg-gray-800;
}

/* Main */
.home-main {
  @apply flex-1 max-w-3xl w-full mx-auto px-6 py-12;
}

/* 动态色球 */
.orb-container {
  @apply absolute inset-0 pointer-events-none;
}

.orb {
  @apply absolute w-24 h-24 rounded-full opacity-30;
  filter: blur(40px);
  transition: all 0.8s ease-in-out;
}

.orb-manus {
  @apply bg-indigo-500;
  top: 15%;
  left: 20%;
}

.orb-coworker {
  @apply bg-emerald-500;
  top: 25%;
  left: 50%;
  transform: translateX(-50%);
}

.orb-vibe {
  @apply bg-cyan-500;
  top: 15%;
  right: 20%;
}

.orb-active {
  @apply opacity-60;
  transform: scale(1.3);
  animation: orb-breath 2s ease-in-out infinite;
}

@keyframes orb-breath {
  0%, 100% { opacity: 0.6; transform: scale(1.3); }
  50% { opacity: 0.4; transform: scale(1.5); }
}

/* 能量连线 */
.energy-lines {
  @apply absolute w-full h-24 top-1/4 left-0 opacity-20;
}

.energy-line {
  fill: none;
  stroke: url(#energy-gradient);
  stroke-width: 2;
  stroke-dasharray: 8 4;
  animation: energy-flow 3s linear infinite;
}

@keyframes energy-flow {
  from { stroke-dashoffset: 0; }
  to { stroke-dashoffset: -24; }
}

/* Hero */
.hero {
  @apply text-center mb-8;
}

.hero-tagline {
  @apply text-sm font-medium text-indigo-500 mb-2 tracking-wide;
}

.hero-title {
  @apply text-3xl md:text-4xl font-bold text-gray-900 mb-3;
}

.hero-desc {
  @apply text-base text-slate-600 mb-6;
}

/* Hero CTA */
.hero-cta {
  @apply flex items-center justify-center gap-4;
}

.cta-primary {
  @apply flex items-center gap-2 px-6 py-3
         text-base font-medium text-white
         bg-gray-900 rounded-xl
         hover:bg-gray-800
         cursor-pointer transition-colors duration-200;
}

.cta-secondary {
  @apply flex items-center gap-2 px-6 py-3
         text-base font-medium text-slate-700
         bg-white border border-gray-200 rounded-xl
         hover:bg-gray-50 hover:border-gray-300
         cursor-pointer transition-all duration-200;
}

/* 三位一体可视化 */
.trinity-section {
  @apply mb-10;
}

.trinity-grid {
  @apply grid grid-cols-1 sm:grid-cols-3 gap-4;
}

.trinity-card {
  @apply flex flex-col items-center text-center p-4 rounded-xl
         bg-white/50 border border-gray-100
         cursor-pointer
         transition-all duration-300;
}

.trinity-card:hover {
  @apply bg-white border-gray-200 shadow-md;
  transform: translateY(-2px);
}

.trinity-card-active {
  @apply bg-white border-gray-200 shadow-lg;
  transform: translateY(-4px);
}

.trinity-icon {
  @apply w-12 h-12 rounded-xl flex items-center justify-center mb-3
         transition-all duration-300;
}

.trinity-icon--manus {
  @apply bg-indigo-50 text-indigo-600;
}

.trinity-icon--coworker {
  @apply bg-emerald-50 text-emerald-600;
}

.trinity-icon--vibe {
  @apply bg-cyan-50 text-cyan-600;
}

.trinity-card-active .trinity-icon--manus {
  @apply bg-indigo-100;
}

.trinity-card-active .trinity-icon--coworker {
  @apply bg-emerald-100;
}

.trinity-card-active .trinity-icon--vibe {
  @apply bg-cyan-100;
}

.trinity-content {
  @apply flex flex-col gap-0.5;
}

.trinity-name {
  @apply text-sm font-semibold text-gray-900;
}

.trinity-role {
  @apply text-xs text-slate-500;
}

.trinity-desc {
  @apply text-xs text-slate-500 mt-1;
}

/* Featured Card (Deep Research 强调) */
.featured-section {
  @apply mb-8;
}

.featured-card {
  @apply w-full flex items-center gap-5 p-6
         bg-gradient-to-r from-indigo-50 to-white
         border border-indigo-100 rounded-2xl
         hover:shadow-md hover:border-indigo-200
         cursor-pointer transition-all duration-200 text-left
         relative overflow-hidden;
}

.featured-badge {
  @apply absolute top-3 right-3
         px-2 py-0.5 text-xs font-medium
         text-indigo-600 bg-indigo-100 rounded-full;
}

.featured-icon {
  @apply w-14 h-14 rounded-xl flex items-center justify-center flex-shrink-0
         bg-indigo-100 text-indigo-600;
}

.featured-content {
  @apply flex-1;
}

.featured-title {
  @apply text-lg font-semibold text-gray-900 mb-1;
}

.featured-desc {
  @apply text-sm text-slate-600;
}

.featured-action {
  @apply flex items-center gap-2 px-4 py-2
         text-sm font-medium text-indigo-600
         bg-white rounded-lg border border-indigo-100
         transition-colors duration-200;
}

.featured-card:hover .featured-action {
  @apply bg-indigo-50 border-indigo-200;
}

/* Enhanced Input */
.input-section {
  @apply mb-10;
}

.input-container {
  @apply space-y-3;
}

.input-wrapper {
  @apply flex items-center gap-2 px-2
         bg-white border border-gray-200 rounded-xl
         focus-within:border-gray-400 focus-within:shadow-sm
         transition-all duration-200;
}

.attach-btn {
  @apply p-2.5 text-slate-400 hover:text-slate-600 
         cursor-pointer transition-colors duration-200 rounded-lg
         hover:bg-gray-50;
}

.main-input {
  @apply flex-1 py-3.5
         text-base text-gray-900 placeholder-slate-500
         bg-transparent border-none;
  /* Focus handled by parent .input-wrapper focus-within */
}

.input-submit {
  @apply p-3 mr-1
         text-white bg-gray-900 rounded-lg
         hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed
         cursor-pointer transition-colors duration-200;
}

/* Quick Actions */
.quick-actions {
  @apply flex items-center gap-2;
}

.quick-action-btn {
  @apply flex items-center gap-1.5 px-3 py-1.5
         text-sm text-slate-600
         bg-white border border-gray-200 rounded-lg
         hover:border-gray-300 hover:bg-gray-50
         cursor-pointer transition-all duration-200;
}

/* Suggestions Section */
.suggestions-section {
  @apply mb-10;
}

.suggestions-list {
  @apply space-y-2;
}

.suggestion-item {
  @apply w-full flex items-center gap-3 px-4 py-3
         text-sm text-slate-700
         bg-white/60 border border-gray-100 rounded-lg
         hover:bg-white hover:border-gray-200 hover:shadow-sm
         cursor-pointer transition-all duration-200 text-left;
}

/* Section Title - Fixed Contrast */
.section-title {
  @apply text-xs font-medium text-slate-500 uppercase tracking-wider mb-4;
}

/* Workflows */
.workflows-section {
  @apply mb-10;
}

.workflows-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.workflow-card {
  @apply flex items-center gap-4 p-5
         bg-white border border-gray-100 rounded-xl
         hover:border-gray-200 hover:shadow-sm
         cursor-pointer transition-all duration-200 text-left;
}

.workflow-icon {
  @apply w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0;
}

.workflow-card--indigo .workflow-icon {
  @apply bg-indigo-50 text-indigo-600;
}

.workflow-card--amber .workflow-icon {
  @apply bg-amber-50 text-amber-600;
}

.workflow-card--emerald .workflow-icon {
  @apply bg-emerald-50 text-emerald-600;
}

.workflow-content {
  @apply flex-1 min-w-0;
}

.workflow-title {
  @apply block text-base font-medium text-gray-900;
}

.workflow-subtitle {
  @apply block text-sm text-slate-500 truncate;
}

.workflow-arrow {
  @apply w-5 h-5 text-gray-300 flex-shrink-0 transition-colors duration-200;
}

.workflow-card:hover .workflow-arrow {
  @apply text-slate-500;
}

/* Recent */
.recent-section {
  @apply mb-10;
}

.recent-list {
  @apply space-y-2;
}

.recent-item {
  @apply w-full flex items-center gap-3 px-4 py-3
         bg-white border border-gray-100 rounded-lg
         hover:border-gray-200 hover:shadow-sm
         cursor-pointer transition-all duration-200 text-left;
}

.recent-status {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}

.recent-status--completed {
  @apply bg-emerald-500;
}

.recent-status--in-progress {
  @apply bg-amber-500;
}

.recent-name {
  @apply flex-1 text-sm text-slate-700;
}

.recent-time {
  @apply text-xs text-slate-500;
}

/* Drop Section */
.drop-section {
  @apply mb-8;
}

/* Footer */
.home-footer {
  @apply py-6 text-center;
}

.home-footer p {
  @apply text-sm text-slate-500;
}

/* Hidden utility */
.hidden {
  display: none;
}
</style>
