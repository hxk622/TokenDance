<script setup lang="ts">
import { computed } from 'vue'

// Types
export type ToolCallStatus = 'running' | 'success' | 'error'

// Props
interface Props {
  toolName: string
  parameters: Record<string, any>
  result?: string
  status: ToolCallStatus
}

const props = defineProps<Props>()

// Computed
const statusClasses = computed(() => {
  switch (props.status) {
    case 'running':
      return 'border-blue-400 bg-blue-50'
    case 'success':
      return 'border-green-400 bg-green-50'
    case 'error':
      return 'border-red-400 bg-red-50'
    default:
      return 'border-gray-400 bg-gray-50'
  }
})

const statusIconColor = computed(() => {
  switch (props.status) {
    case 'running':
      return 'text-blue-600'
    case 'success':
      return 'text-green-600'
    case 'error':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
})

const statusText = computed(() => {
  switch (props.status) {
    case 'running':
      return '执行中...'
    case 'success':
      return '成功'
    case 'error':
      return '失败'
    default:
      return '未知'
  }
})

const formattedParams = computed(() => {
  return JSON.stringify(props.parameters, null, 2)
})
</script>

<template>
  <div
    class="tool-call-card"
    :class="statusClasses"
  >
    <div class="tool-header">
      <!-- Status Icon -->
      <div
        class="status-icon-wrapper"
        :class="statusIconColor"
      >
        <!-- Running -->
        <svg
          v-if="status === 'running'"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="status-icon animate-spin"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
        
        <!-- Success -->
        <svg
          v-else-if="status === 'success'"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2.5"
          stroke="currentColor"
          class="status-icon"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        
        <!-- Error -->
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2.5"
          stroke="currentColor"
          class="status-icon"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
      </div>

      <!-- Tool Name -->
      <div class="tool-info">
        <span class="tool-name">{{ toolName }}</span>
        <span class="tool-status">{{ statusText }}</span>
      </div>
    </div>

    <!-- Parameters -->
    <div
      v-if="parameters && Object.keys(parameters).length > 0"
      class="tool-section"
    >
      <div class="section-title">
        参数:
      </div>
      <pre class="code-block">{{ formattedParams }}</pre>
    </div>

    <!-- Result -->
    <div
      v-if="result"
      class="tool-section"
    >
      <div class="section-title">
        结果:
      </div>
      <pre class="code-block result-text">{{ result }}</pre>
    </div>
  </div>
</template>

<style scoped>
.tool-call-card {
  @apply mx-4 mb-3 rounded-lg border-l-4 shadow-sm;
}

.tool-header {
  @apply flex items-center gap-3 px-4 py-3;
}

.status-icon-wrapper {
  @apply flex-shrink-0;
}

.status-icon {
  @apply w-5 h-5;
}

.tool-info {
  @apply flex-1 flex items-center gap-2;
}

.tool-name {
  @apply text-sm font-semibold text-gray-800;
}

.tool-status {
  @apply text-xs text-gray-600 font-medium;
}

.tool-section {
  @apply px-4 pb-3;
}

.section-title {
  @apply text-xs font-medium text-gray-600 mb-1;
}

.code-block {
  @apply text-xs font-mono bg-white rounded p-2 overflow-x-auto border border-gray-200;
}

.result-text {
  @apply max-h-40 overflow-y-auto;
}
</style>
