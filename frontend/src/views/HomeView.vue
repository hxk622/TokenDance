<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import IntentCard, { type IntentType } from '@/components/home/IntentCard.vue'
import PromptSuggestions, { type PromptSuggestion } from '@/components/home/PromptSuggestions.vue'
import FileDropZone from '@/components/home/FileDropZone.vue'

const router = useRouter()
const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)

// 意图卡片数据
const intents: IntentType[] = [
  {
    id: 'research',
    icon: '🔍',
    title: '深度研究',
    description: 'AI 帮你调研分析',
    color: '#6366f1',
    gradient: 'linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%)'
  },
  {
    id: 'ppt',
    icon: '📊',
    title: '生成 PPT',
    description: '一键生成演示文稿',
    color: '#f59e0b',
    gradient: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)'
  },
  {
    id: 'code',
    icon: '💻',
    title: '执行代码',
    description: '运行和调试代码',
    color: '#10b981',
    gradient: 'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)'
  }
]

// 示例 Prompt
const suggestions: PromptSuggestion[] = [
  { id: '1', icon: '📈', text: '帮我调研 2024 年 AI Agent 市场趋势' },
  { id: '2', icon: '📝', text: '把这份报告做成 10 页 PPT' },
  { id: '3', icon: '📊', text: '分析这份 CSV 数据并生成图表' },
  { id: '4', icon: '🔧', text: '帮我重构这段代码，提升性能' }
]

// 处理意图选择
const handleIntentSelect = (intent: IntentType) => {
  const prompts: Record<string, string> = {
    research: '请帮我深度调研：',
    ppt: '请帮我生成一份 PPT：',
    code: '请帮我执行以下任务：'
  }
  inputValue.value = prompts[intent.id]
  inputRef.value?.focus()
}

// 处理示例选择
const handleSuggestionSelect = (text: string) => {
  inputValue.value = text
  // 直接提交
  handleSubmit()
}

// 处理文件拖拽
const handleFileDrop = (files: FileList) => {
  console.log('Files dropped:', files)
  // TODO: 处理文件上传，启动 Coworker
  const fileNames = Array.from(files).map(f => f.name).join(', ')
  inputValue.value = `请帮我分析这些文件：${fileNames}`
}

// 处理提交
const handleSubmit = () => {
  if (!inputValue.value.trim()) return
  
  // 跳转到聊天页并带上初始消息
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
    <!-- Background Effects -->
    <div class="bg-gradient" />
    <div class="bg-noise" />
    
    <!-- Main Content -->
    <main class="home-content">
      <!-- Hero Section -->
      <section class="hero-section">
        <h1 class="hero-title">
          <span class="hero-icon">🚀</span>
          TokenDance
        </h1>
        <p class="hero-subtitle">我能帮你完成各种任务</p>
      </section>
      
      <!-- Input Section -->
      <section class="input-section">
        <div class="input-container">
          <textarea
            ref="inputRef"
            v-model="inputValue"
            class="main-input"
            placeholder="输入你想完成的任务..."
            rows="1"
            @keydown="handleKeydown"
          />
          <button 
            class="submit-button"
            :disabled="!inputValue.trim()"
            @click="handleSubmit"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>
        </div>
      </section>
      
      <!-- Intent Cards -->
      <section class="intent-section">
        <IntentCard
          v-for="intent in intents"
          :key="intent.id"
          :intent="intent"
          @select="handleIntentSelect"
        />
      </section>
      
      <!-- Prompt Suggestions -->
      <section class="suggestions-section">
        <PromptSuggestions
          :suggestions="suggestions"
          @select="handleSuggestionSelect"
        />
      </section>
      
      <!-- File Drop Zone -->
      <section class="drop-section">
        <FileDropZone @drop="handleFileDrop" />
      </section>
    </main>
  </div>
</template>

<style scoped>
.home-view {
  @apply relative min-h-screen overflow-hidden;
}

/* Background Effects */
.bg-gradient {
  @apply absolute inset-0 -z-10;
  background: 
    radial-gradient(ellipse at 20% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(6, 182, 212, 0.15) 0%, transparent 50%),
    linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
}

.bg-noise {
  @apply absolute inset-0 -z-10 opacity-30;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
}

/* Main Content */
.home-content {
  @apply relative z-10 max-w-4xl mx-auto px-6 py-16;
}

/* Hero Section */
.hero-section {
  @apply text-center mb-12;
}

.hero-title {
  @apply text-5xl font-bold text-gray-800 mb-4
         flex items-center justify-center gap-4;
}

.hero-icon {
  @apply text-4xl;
}

.hero-subtitle {
  @apply text-xl text-gray-500;
}

/* Input Section */
.input-section {
  @apply mb-12;
}

.input-container {
  @apply relative max-w-2xl mx-auto;
}

.main-input {
  @apply w-full px-6 py-4 pr-14
         text-lg text-gray-800 placeholder-gray-400
         bg-white/80 backdrop-blur-sm
         border border-gray-200 rounded-2xl
         shadow-lg shadow-gray-200/50
         focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500
         transition-all duration-200
         resize-none;
}

.submit-button {
  @apply absolute right-3 top-1/2 -translate-y-1/2
         w-10 h-10 flex items-center justify-center
         rounded-xl bg-cyan-500 text-white
         hover:bg-cyan-600 disabled:bg-gray-300 disabled:cursor-not-allowed
         transition-colors duration-200;
}

/* Intent Section */
.intent-section {
  @apply flex justify-center gap-6 mb-12 flex-wrap;
}

/* Suggestions Section */
.suggestions-section {
  @apply mb-12;
}

/* Drop Section */
.drop-section {
  @apply mb-8;
}
</style>
