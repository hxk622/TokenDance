<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FileDropZone from '@/components/home/FileDropZone.vue'

const router = useRouter()
const inputValue = ref('')
const inputRef = ref<HTMLInputElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 工作流卡片 - 以用户任务为中心，而非功能
const workflows = [
  {
    id: 'research',
    title: '市场调研',
    subtitle: '竞品分析 · 行业报告 · 数据洞察',
    icon: 'chart-bar',
    accent: 'indigo'
  },
  {
    id: 'presentation',
    title: '演示汇报',
    subtitle: '方案展示 · 周报总结 · 培训材料',
    icon: 'presentation',
    accent: 'amber'
  },
  {
    id: 'development',
    title: '开发调试',
    subtitle: '代码审查 · 性能优化 · Bug 排查',
    icon: 'code',
    accent: 'emerald'
  }
]

// 场景引导示例
const suggestions = [
  '帮我调研 2024 年 AI Agent 市场趋势',
  '把这份报告做成 10 页 PPT',
  '分析这份 CSV 数据并生成图表'
]

// 快捷操作
const quickActions = [
  { id: 'research', label: '深度研究', icon: 'search' },
  { id: 'ppt', label: '生成 PPT', icon: 'presentation' },
  { id: 'code', label: '代码分析', icon: 'code' }
]

// 最近项目（模拟数据，实际应从 API 获取）
const recentProjects = [
  { id: '1', name: '2024 Q4 竞品分析', time: '2 小时前', status: 'completed' },
  { id: '2', name: '产品路演 PPT', time: '昨天', status: 'in-progress' },
  { id: '3', name: 'API 性能优化', time: '3 天前', status: 'completed' }
]

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
const handleGuestTry = () => {
  router.push({ path: '/chat', query: { guest: 'true' } })
}
</script>

<template>
  <div class="home-view">
    <!-- Vibe Background -->
    <div class="bg-vibe">
      <div class="bg-gradient" />
      <div class="bg-pattern" />
    </div>
    
    <!-- Header -->
    <header class="home-header">
      <div class="header-left">
        <h1 class="logo">TokenDance</h1>
      </div>
      <div class="header-right">
        <button class="header-btn" @click="handleGuestTry">免费试用</button>
        <button class="header-btn">文档</button>
        <button class="header-btn header-btn-primary">登录</button>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="home-main">
      <!-- Hero with Vibe -->
      <section class="hero">
        <div class="hero-badge">Vibe-Agentic Workflow</div>
        <h2 class="hero-title">你的智能工作台</h2>
        <p class="hero-desc">和 Agent 一起完成任务，随时接管和调整</p>
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
              placeholder="描述你要完成的任务..."
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
            <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span>{{ suggestion }}</span>
          </button>
        </div>
      </section>
      
      <!-- Workflows -->
      <section class="workflows-section">
        <h3 class="section-title">开始一个工作流</h3>
        <div class="workflows-grid">
          <button
            v-for="wf in workflows"
            :key="wf.id"
            class="workflow-card"
            :class="`workflow-card--${wf.accent}`"
            @click="handleWorkflowSelect(wf)"
          >
            <div class="workflow-icon">
              <svg v-if="wf.icon === 'chart-bar'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <svg v-else-if="wf.icon === 'presentation'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

/* Hero with Vibe */
.hero {
  @apply text-center mb-10;
}

.hero-badge {
  @apply inline-block px-3 py-1 mb-4
         text-xs font-medium text-indigo-600
         bg-indigo-50 rounded-full;
}

.hero-title {
  @apply text-3xl font-semibold text-gray-900 mb-3;
}

.hero-desc {
  @apply text-base text-slate-600;
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
         text-base text-gray-900 placeholder-slate-400
         bg-transparent border-none
         focus:outline-none;
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
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
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
