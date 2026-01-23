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

// 默认数据 - 使用 icon 名称而非 Emoji
const defaultPreviousTasks: PreviousTask[] = [
  { id: '1', title: '2024 年中报告', daysAgo: 7, icon: 'chart-bar' },
  { id: '2', title: '竞品价格分析', daysAgo: 3, icon: 'currency' },
  { id: '3', title: '市场趋势预测', daysAgo: 14, icon: 'trending-up' }
]

const defaultTrendingTasks: TrendingTask[] = [
  { id: '1', title: '产品路演 PPT', count: 8, icon: 'presentation' },
  { id: '2', title: '年度预算分析', count: 12, icon: 'briefcase' },
  { id: '3', title: '用户满意度调查', count: 5, icon: 'clipboard-check' }
]

const previousTasks = computed(() => props.previousTasks || defaultPreviousTasks)
const trendingTasks = computed(() => props.trendingTasks || defaultTrendingTasks)
const aiSuggestion = computed(() => props.aiSuggestion || '调研 2025 年 AI Agent 市场趋势')

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

// blur 时延迟关闭建议面板
const handleBlur = () => {
  window.setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// 处理推荐任务点击
const handleRecommendClick = () => {
  const task: TrendingTask = {
    id: 'recommend',
    title: aiSuggestion.value,
    count: 0,
    icon: 'sparkles'
  }
  handleTaskSelect(task)
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
        @blur="handleBlur"
        @keydown="handleKeydown"
      >
      <button
        class="input-submit"
        :disabled="!query.trim()"
        @click="handleSubmit"
      >
        开始
      </button>
    </div>
    
    <!-- 建议下拉 -->
    <transition name="suggestions-fade">
      <div
        v-if="showSuggestions"
        class="suggestions-panel"
      >
        <!-- 上次类似的任务 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            你上次的方法
          </h5>
          <button
            v-for="task in previousTasks"
            :key="task.id"
            class="suggestion-item previous-item"
            @click="handleTaskSelect(task)"
          >
            <span class="item-icon">
              <svg
                v-if="task.icon === 'chart-bar'"
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <svg
                v-else-if="task.icon === 'currency'"
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
            </span>
            <span class="item-title">{{ task.title }}</span>
            <span class="item-time">{{ task.daysAgo }}天前</span>
          </button>
        </div>
        
        <!-- 团队现在流行的 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 20h5v-2a3 3 0 00-5.856-1.487M15 10a3 3 0 11-6 0 3 3 0 016 0zM4 20h16v-2a8 8 0 00-16 0z"
              />
            </svg>
            团队现在都在做
          </h5>
          <button
            v-for="task in trendingTasks"
            :key="task.id"
            class="suggestion-item trending-item"
            @click="handleTaskSelect(task)"
          >
            <span class="item-icon">
              <svg
                v-if="task.icon === 'presentation'"
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
              <svg
                v-else-if="task.icon === 'briefcase'"
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
              </svg>
            </span>
            <span class="item-title">{{ task.title }}</span>
            <span class="item-count">{{ task.count }}人</span>
          </button>
        </div>
        
        <!-- 推荐任务 -->
        <div class="suggestion-group">
          <h5 class="group-title">
            <svg
              class="w-4 h-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
            推荐任务
          </h5>
          <button
            class="suggestion-item ai-item"
            @click="handleRecommendClick"
          >
            <span class="item-icon">
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                />
              </svg>
            </span>
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
  @apply flex-1 px-5 py-3.5 text-base text-white placeholder-gray-500
         bg-gray-900 border border-gray-700 rounded-xl
         focus:outline-none focus:border-gray-500
         transition-all duration-200;
  position: relative;
}

.smart-input:focus {
  box-shadow: 0 0 0 3px rgba(0, 184, 217, 0.15);
}

.input-submit {
  @apply px-6 py-3.5 text-sm font-semibold text-gray-900
         rounded-xl cursor-pointer;
  background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.1);
}

.input-submit:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
  box-shadow: none;
}

.input-submit:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 
    0 4px 16px rgba(255, 255, 255, 0.2),
    0 0 24px rgba(0, 217, 255, 0.15);
}

.input-submit:not(:disabled):active {
  transform: translateY(0);
}

.suggestions-panel {
  @apply absolute top-full left-0 right-0 mt-2
         bg-gray-900 rounded-xl border border-gray-800
         shadow-2xl shadow-black/50 p-4 z-10;
  backdrop-filter: blur(12px);
}

.suggestion-group {
  @apply mb-4 last:mb-0;
}

.group-title {
  @apply text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-1.5;
}

.group-title svg {
  @apply text-gray-600;
}

.suggestion-item {
  @apply w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-left cursor-pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.suggestion-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 0 3px 3px 0;
  transform: scaleY(0);
  transition: transform 0.2s ease;
}

.previous-item::before {
  background: linear-gradient(180deg, #00B8D9, #00D9FF);
}

.trending-item::before {
  background: linear-gradient(180deg, #FFB800, #FF8C00);
}

.ai-item::before {
  background: linear-gradient(180deg, #00D9FF, #00FF88);
}

.suggestion-item:hover::before {
  transform: scaleY(1);
}

.suggestion-item:hover {
  transform: translateX(6px);
}

.previous-item {
  background: rgba(0, 184, 217, 0.08);
  border: 1px solid rgba(0, 184, 217, 0.2);
  color: rgba(255, 255, 255, 0.8);
}

.previous-item:hover {
  background: rgba(0, 184, 217, 0.15);
  border-color: rgba(0, 184, 217, 0.4);
  box-shadow: 0 4px 12px rgba(0, 184, 217, 0.15);
}

.trending-item {
  background: rgba(255, 184, 0, 0.08);
  border: 1px solid rgba(255, 184, 0, 0.2);
  color: rgba(255, 255, 255, 0.8);
}

.trending-item:hover {
  background: rgba(255, 184, 0, 0.15);
  border-color: rgba(255, 184, 0, 0.4);
  box-shadow: 0 4px 12px rgba(255, 184, 0, 0.15);
}

.ai-item {
  background: rgba(0, 217, 255, 0.08);
  border: 1px solid rgba(0, 217, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
}

.ai-item:hover {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.4);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.15);
}

.item-icon {
  @apply flex items-center justify-center w-5 h-5 text-gray-400 flex-shrink-0;
}

.item-title {
  @apply flex-1 text-sm font-medium;
}

.item-time {
  @apply text-xs text-gray-500;
}

.item-count {
  @apply text-xs text-amber-400 font-medium;
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
