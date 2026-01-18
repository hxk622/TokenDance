<script setup lang="ts">
import { computed } from 'vue'

export interface ProgressStep {
  id: string
  label: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  elapsed?: number
}

export interface ProgressIndicatorProps {
  title: string
  steps: ProgressStep[]
  showProgressBar?: boolean
}

const props = withDefaults(defineProps<ProgressIndicatorProps>(), {
  showProgressBar: true,
})

const progress = computed(() => {
  const completedSteps = props.steps.filter(s => s.status === 'completed').length
  return (completedSteps / props.steps.length) * 100
})

const currentStep = computed(() => {
  return props.steps.findIndex(s => s.status === 'running') + 1
})

const totalSteps = computed(() => props.steps.length)

function getStepIcon(status: string) {
  return {
    pending: 'circle',
    running: 'spinner',
    completed: 'check',
    failed: 'error',
  }[status] || 'circle'
}

function getStepTextClass(status: string) {
  return {
    pending: 'text-text-tertiary',
    running: 'text-text-primary font-medium',
    completed: 'text-text-secondary',
    failed: 'text-red-400',
  }[status] || 'text-text-tertiary'
}
</script>

<template>
  <div class="rounded-lg border border-border-default bg-bg-secondary p-4">
    <!-- 标题和进度 -->
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm font-medium text-text-primary">{{ title }}</span>
      <span class="text-xs text-text-tertiary">
        {{ currentStep }}/{{ totalSteps }}
      </span>
    </div>
    
    <!-- 进度条 -->
    <div
      v-if="showProgressBar"
      class="h-2 bg-bg-tertiary rounded-full overflow-hidden mb-4"
    >
      <div
        class="h-full bg-accent-primary transition-all duration-300"
        :style="{ width: `${progress}%` }"
      />
    </div>
    
    <!-- 步骤列表 -->
    <div class="space-y-2">
      <div
        v-for="step in steps"
        :key="step.id"
        class="flex items-center gap-2 text-sm"
      >
        <!-- 状态图标 -->
        <div class="w-4 h-4 flex-shrink-0">
          <!-- Spinner -->
          <svg
            v-if="getStepIcon(step.status) === 'spinner'"
            class="w-4 h-4 text-accent-primary animate-spin"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="2"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          
          <!-- Check -->
          <svg
            v-else-if="getStepIcon(step.status) === 'check'"
            class="w-4 h-4 text-green-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          
          <!-- Error -->
          <svg
            v-else-if="getStepIcon(step.status) === 'error'"
            class="w-4 h-4 text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
          
          <!-- Circle -->
          <svg
            v-else
            class="w-4 h-4 text-text-tertiary"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <circle
              cx="12"
              cy="12"
              r="3"
              stroke="currentColor"
              stroke-width="2"
            />
          </svg>
        </div>
        
        <!-- 步骤标签 -->
        <span :class="getStepTextClass(step.status)">
          {{ step.label }}
        </span>
        
        <!-- 执行时间 -->
        <span
          v-if="step.status === 'running' && step.elapsed"
          class="text-xs text-text-tertiary ml-auto"
        >
          {{ step.elapsed }}s
        </span>
      </div>
    </div>
  </div>
</template>
