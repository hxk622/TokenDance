<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FileDropZone from '@/components/home/FileDropZone.vue'

const router = useRouter()
const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)

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
</script>

<template>
  <div class="home-view">
    <!-- Subtle Background -->
    <div class="bg-pattern" />
    
    <!-- Header -->
    <header class="home-header">
      <div class="header-left">
        <h1 class="logo">TokenDance</h1>
      </div>
      <div class="header-right">
        <button class="header-btn">文档</button>
        <button class="header-btn header-btn-primary">登录</button>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="home-main">
      <!-- Hero -->
      <section class="hero">
        <h2 class="hero-title">你的智能工作台</h2>
        <p class="hero-desc">和 Agent 一起完成任务，随时接管和调整</p>
      </section>
      
      <!-- Input -->
      <section class="input-section">
        <div class="input-wrapper">
          <input
            ref="inputRef"
            v-model="inputValue"
            type="text"
            class="main-input"
            placeholder="描述你要完成的任务，或直接拖入文件..."
            @keydown="handleKeydown"
          />
          <button 
            class="input-submit"
            :disabled="!inputValue.trim()"
            @click="handleSubmit"
          >
            开始
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

/* Background */
.bg-pattern {
  @apply absolute inset-0 -z-10 opacity-[0.03];
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
  @apply px-4 py-2 text-sm text-gray-600 hover:text-gray-900 transition-colors;
}

.header-btn-primary {
  @apply bg-gray-900 text-white rounded-lg hover:bg-gray-800;
}

/* Main */
.home-main {
  @apply flex-1 max-w-3xl w-full mx-auto px-6 py-12;
}

/* Hero */
.hero {
  @apply text-center mb-10;
}

.hero-title {
  @apply text-3xl font-semibold text-gray-900 mb-2;
}

.hero-desc {
  @apply text-base text-gray-500;
}

/* Input */
.input-section {
  @apply mb-12;
}

.input-wrapper {
  @apply flex gap-3;
}

.main-input {
  @apply flex-1 px-5 py-3.5
         text-base text-gray-900 placeholder-gray-400
         bg-white border border-gray-200 rounded-xl
         focus:outline-none focus:border-gray-400
         transition-colors;
}

.input-submit {
  @apply px-6 py-3.5
         text-sm font-medium text-white
         bg-gray-900 rounded-xl
         hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed
         transition-colors;
}

/* Section Title */
.section-title {
  @apply text-sm font-medium text-gray-400 uppercase tracking-wider mb-4;
}

/* Workflows */
.workflows-section {
  @apply mb-12;
}

.workflows-grid {
  @apply grid grid-cols-1 md:grid-cols-3 gap-4;
}

.workflow-card {
  @apply flex items-center gap-4 p-5
         bg-white border border-gray-100 rounded-xl
         hover:border-gray-200 hover:shadow-sm
         transition-all text-left;
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
  @apply block text-sm text-gray-400 truncate;
}

.workflow-arrow {
  @apply w-5 h-5 text-gray-300 flex-shrink-0;
}

.workflow-card:hover .workflow-arrow {
  @apply text-gray-400;
}

/* Recent */
.recent-section {
  @apply mb-12;
}

.recent-list {
  @apply space-y-2;
}

.recent-item {
  @apply w-full flex items-center gap-3 px-4 py-3
         bg-white border border-gray-100 rounded-lg
         hover:border-gray-200
         transition-colors text-left;
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
  @apply flex-1 text-sm text-gray-700;
}

.recent-time {
  @apply text-xs text-gray-400;
}

/* Drop */
.drop-section {
  @apply mb-8;
}

/* Footer */
.home-footer {
  @apply py-6 text-center;
}

.home-footer p {
  @apply text-sm text-gray-400;
}
</style>
