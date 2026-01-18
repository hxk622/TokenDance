<script setup lang="ts">
import { computed } from 'vue'

export interface FocusProject {
  id: string
  title: string
  progress: number
  totalSteps: number
  currentStep: number
  suggestion: string
  status: 'active' | 'paused' | 'completed'
}

const props = defineProps<{
  project?: FocusProject
}>()

const emit = defineEmits<{
  (e: 'continue'): void
  (e: 'pause'): void
}>()

// 默认项目数据
const defaultProject: FocusProject = {
  id: '1',
  title: '2024 Q4 竞品分析',
  progress: 60,
  totalSteps: 5,
  currentStep: 3,
  suggestion: '补充东南亚市场数据？',
  status: 'active'
}

const currentProject = computed(() => props.project || defaultProject)

const progressPercentage = computed(() => 
  Math.round((currentProject.value.currentStep / currentProject.value.totalSteps) * 100)
)
</script>

<template>
  <div class="focus-card">
    <h3 class="focus-label">
      你今天的焦点
    </h3>
    
    <div class="focus-content">
      <!-- 呼吸指示器 -->
      <div
        class="pulse-indicator"
        :class="`status-${currentProject.status}`"
      />
      
      <!-- 项目标题和进度 -->
      <div class="project-header">
        <div class="title-section">
          <h4 class="project-title">
            {{ currentProject.title }}
          </h4>
          <span class="progress-text">进行中 ({{ currentProject.currentStep }}/{{ currentProject.totalSteps }} 步)</span>
        </div>
        <span class="progress-percent">{{ progressPercentage }}%</span>
      </div>
      
      <!-- 进度条 -->
      <div class="progress-bar-container">
        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: `${progressPercentage}%` }"
          />
        </div>
      </div>
      
      <!-- 建议操作 -->
      <div class="suggestion-box">
        <svg
          class="suggestion-icon"
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
        <span class="suggestion-text">{{ currentProject.suggestion }}</span>
      </div>
      
      <!-- 操作按钮 -->
      <div class="actions">
        <button
          class="action-btn action-btn-primary"
          @click="emit('continue')"
        >
          继续这个任务
        </button>
        <button
          class="action-btn action-btn-secondary"
          @click="emit('pause')"
        >
          暂停
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.focus-card {
  @apply bg-white rounded-2xl border border-gray-100 p-6;
}

.focus-label {
  @apply text-xs font-medium text-gray-400 uppercase tracking-wider mb-4;
}

.focus-content {
  @apply space-y-4;
}

.pulse-indicator {
  @apply w-3 h-3 rounded-full mb-3;
}

.status-active {
  @apply bg-cyan-500;
  animation: pulse-breath 1.5s ease-in-out infinite;
}

.status-paused {
  @apply bg-amber-500;
}

.status-completed {
  @apply bg-emerald-500;
}

@keyframes pulse-breath {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 0 10px rgba(6, 182, 212, 0.5);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.2);
    box-shadow: 0 0 20px rgba(6, 182, 212, 0.8);
  }
}

.project-header {
  @apply flex items-start justify-between gap-4;
}

.title-section {
  @apply flex-1;
}

.project-title {
  @apply text-base font-semibold text-gray-900 mb-1;
}

.progress-text {
  @apply text-sm text-gray-500;
}

.progress-percent {
  @apply text-sm font-medium text-gray-700;
}

.progress-bar-container {
  @apply flex items-center gap-2;
}

.progress-bar {
  @apply flex-1 h-2 bg-gray-100 rounded-full overflow-hidden;
}

.progress-fill {
  @apply h-full bg-cyan-500 transition-all duration-500;
}

.suggestion-box {
  @apply flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-50;
}

.suggestion-icon {
  @apply w-5 h-5 text-blue-600 flex-shrink-0;
}

.suggestion-text {
  @apply text-sm text-blue-900;
}

.actions {
  @apply flex gap-2;
}

.action-btn {
  @apply px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200;
}

.action-btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800;
}

.action-btn-secondary {
  @apply border border-gray-200 text-gray-600 hover:bg-gray-50;
}
</style>
