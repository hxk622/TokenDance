<script setup lang="ts">
import { ref, computed } from 'vue'

export interface PreviousTask {
  id: string
  title: string
  daysAgo: number
  icon: string
}

export interface TrendingTask {
  id: string
  title: string
  count: number
  icon: string
}

const props = defineProps<{
  previousTasks?: PreviousTask[]
  trendingTasks?: TrendingTask[]
  aiSuggestion?: string
}>()

const emit = defineEmits<{
  (e: 'submit', query: string): void
  (e: 'select', task: PreviousTask | TrendingTask): void
}>()

const query = ref('')
const showSuggestions = ref(false)

// 默认数据
const defaultPreviousTasks: PreviousTask[] = [
  { id: '1', title: '2024 年中报告', daysAgo: 7, icon: '📊' },
  { id: '2', title: '竞品价格分析', daysAgo: 3, icon: '💰' },
  { id: '3', title: '市场趋势预测', daysAgo: 14, icon: '📈' }
]

const defaultTrendingTasks: TrendingTask[] = [
  { id: '1', title: '产品路演 PPT', count: 8, icon: '📽️' },
  { id: '2', title: '年度预算分析', count: 12, icon: '💼' },
  { id: '3', title: '用户满意度调查', count: 5, icon: '⭐' }
]

const previousTasks = computed(() => props.previousTasks || defaultPreviousTasks)
const trendingTasks = computed(() => props.trendingTasks || defaultTrendingTasks)
const aiSuggestion = computed(() => props.aiSuggestion || '分析 2025 年 AI Agent 市场规模')

const handleSubmit = () => {
  if (query.value.trim()) {
    emit('submit', query.value)
    query.value = ''
    showSuggestions.value = false
  }
}

const handleTaskSelect = (task: PreviousTask | TrendingTask) => {
  emit('select', task)
  if ('daysAgo' in task) {
    query.value = task.title
  } else {
    query.value = task.title
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    handleSubmit()
  }
}
</script>

<template>
  <div class="smart-input-container">
    <!-- 输入框 -->
    <div class="input-wrapper">
      <input
        v-model="query"
        type="text"
        class="smart-input"
        placeholder="描述任务，或选择下方建议..."
        @focus="showSuggestions = true"
        @blur="setTimeout(() => (showSuggestions = false), 200)"
        @keydown="handleKeydown"
      />
      <button class="input-submit" :disabled="!query.trim()" @click="handleSubmit">
        开始
      </button>
    </div>
    
    <!-- 建议下拉 -->
    <transition name="suggestions-fade">
      <div v-if="showSuggestions" class="suggestions-panel">
        <!-- 上次类似的任务 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            你上次的方法
          </h5>
          <button
            v-for="task in previousTasks"
            :key="task.id"
            class="suggestion-item previous-item"
            @click="handleTaskSelect(task)"
          >
            <span class="item-icon">{{ task.icon }}</span>
            <span class="item-title">{{ task.title }}</span>
            <span class="item-time">{{ task.daysAgo }}天前</span>
          </button>
        </div>
        
        <!-- 团队现在流行的 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.856-1.487M15 10a3 3 0 11-6 0 3 3 0 016 0zM4 20h16v-2a8 8 0 00-16 0z" />
            </svg>
            团队现在都在做
          </h5>
          <button
            v-for="task in trendingTasks"
            :key="task.id"
            class="suggestion-item trending-item"
            @click="handleTaskSelect(task)"
          >
            <span class="item-icon">{{ task.icon }}</span>
            <span class="item-title">{{ task.title }}</span>
            <span class="item-count">{{ task.count }}人</span>
          </button>
        </div>
        
        <!-- AI 的建议 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            AI 的建议
          </h5>
          <button
            class="suggestion-item ai-item"
            @click="handleTaskSelect({ title: aiSuggestion, id: 'ai', count: 0 })"
          >
            <span class="ai-badge">✨</span>
            <span class="item-title">{{ aiSuggestion }}</span>
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.smart-input-container {
  @apply relative max-w-2xl mx-auto;
}

.input-wrapper {
  @apply flex gap-3;
}

.smart-input {
  @apply flex-1 px-5 py-3.5 text-base text-gray-900 placeholder-gray-400
         bg-white border border-gray-200 rounded-xl
         focus:outline-none focus:border-gray-400 focus:ring-2 focus:ring-gray-200/50
         transition-all duration-200;
}

.input-submit {
  @apply px-6 py-3.5 text-sm font-medium text-white
         bg-gray-900 rounded-xl
         hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed
         transition-colors duration-200;
}

.suggestions-panel {
  @apply absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-gray-100 shadow-lg p-4 z-10;
}

.suggestion-group {
  @apply mb-4 last:mb-0;
}

.group-title {
  @apply text-xs font-medium text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-1.5;
}

.group-title svg {
  @apply text-gray-500;
}

.suggestion-item {
  @apply w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-left
         transition-colors duration-200;
}

.suggestion-item:hover {
  @apply bg-gray-50;
}

.previous-item {
  @apply border border-gray-100 bg-gray-50/50 hover:bg-gray-100;
}

.trending-item {
  @apply border border-amber-100 bg-amber-50/50 hover:bg-amber-100;
}

.ai-item {
  @apply border border-blue-100 bg-blue-50/50 hover:bg-blue-100;
}

.item-icon {
  @apply text-lg flex-shrink-0;
}

.item-title {
  @apply flex-1 text-sm text-gray-700 font-medium;
}

.item-time {
  @apply text-xs text-gray-400;
}

.item-count {
  @apply text-xs text-amber-600 font-medium;
}

.ai-badge {
  @apply text-lg;
}

.suggestions-fade-enter-active,
.suggestions-fade-leave-active {
  @apply transition-all duration-200;
}

.suggestions-fade-enter-from,
.suggestions-fade-leave-to {
  @apply opacity-0 -translate-y-2;
}
</style>
