<script setup lang="ts">
import { ref, computed } from 'vue'

export interface ToolCall {
  id: string
  name: string
  params: Record<string, any>
  status: 'pending' | 'running' | 'success' | 'error'
  result?: string
  error?: string
  duration?: number
}

export interface ToolCallBlockProps {
  toolCall: ToolCall
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<ToolCallBlockProps>(), {
  defaultExpanded: false,
})

const expanded = ref(props.defaultExpanded)

const toggleExpanded = () => {
  if (props.toolCall.result || props.toolCall.error) {
    expanded.value = !expanded.value
  }
}

const statusConfig = computed(() => {
  const configs = {
    pending: {
      bgClass: 'bg-bg-tertiary',
      textClass: 'text-text-tertiary',
      borderClass: 'border-border-default',
      icon: 'circle',
      label: '待执行',
    },
    running: {
      bgClass: 'bg-bg-tertiary',
      textClass: 'text-accent-primary',
      borderClass: 'border-accent-primary/30',
      icon: 'spinner',
      label: '执行中',
    },
    success: {
      bgClass: 'bg-green-500/10',
      textClass: 'text-green-400',
      borderClass: 'border-green-500/30',
      icon: 'check',
      label: '成功',
    },
    error: {
      bgClass: 'bg-red-500/10',
      textClass: 'text-red-400',
      borderClass: 'border-red-500/30',
      icon: 'error',
      label: '失败',
    },
  }
  return configs[props.toolCall.status]
})

const formattedParams = computed(() => {
  return Object.entries(props.toolCall.params)
    .map(([key, value]) => {
      const displayValue = typeof value === 'string' && value.length > 50
        ? value.substring(0, 50) + '...'
        : JSON.stringify(value)
      return `${key}=${displayValue}`
    })
    .join(', ')
})

const canExpand = computed(() => {
  return !!(props.toolCall.result || props.toolCall.error)
})
</script>

<template>
  <div 
    class="mb-3 rounded-lg border overflow-hidden transition-colors"
    :class="[statusConfig.bgClass, statusConfig.borderClass]"
  >
    <!-- 工具调用头部 -->
    <div 
      class="px-4 py-2.5 flex items-center justify-between"
      :class="canExpand ? 'cursor-pointer hover:bg-bg-tertiary/50' : ''"
      @click="toggleExpanded"
    >
      <div class="flex items-center gap-3 flex-1 min-w-0">
        <!-- 状态图标 -->
        <div class="flex-shrink-0" :class="statusConfig.textClass">
          <!-- Spinner -->
          <svg
            v-if="statusConfig.icon === 'spinner'"
            class="w-4 h-4 animate-spin"
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
            v-else-if="statusConfig.icon === 'check'"
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          
          <!-- Error -->
          <svg
            v-else-if="statusConfig.icon === 'error'"
            class="w-4 h-4"
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
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" />
          </svg>
        </div>
        
        <!-- 工具名称和参数 -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-0.5">
            <svg class="w-4 h-4 text-text-secondary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <span class="font-mono font-medium text-sm text-text-primary">{{ toolCall.name }}</span>
          </div>
          <div class="text-xs text-text-tertiary truncate font-mono">
            {{ formattedParams }}
          </div>
        </div>
        
        <!-- 状态标签和时长 -->
        <div class="flex items-center gap-2 flex-shrink-0">
          <span
            class="px-2 py-1 rounded text-xs font-medium"
            :class="[statusConfig.bgClass, statusConfig.textClass]"
          >
            {{ statusConfig.label }}
          </span>
          <span v-if="toolCall.duration" class="text-xs text-text-tertiary">
            {{ toolCall.duration }}ms
          </span>
        </div>
      </div>
      
      <!-- 展开图标 -->
      <svg
        v-if="canExpand"
        class="w-4 h-4 text-text-secondary transition-transform duration-200 ml-2 flex-shrink-0"
        :class="{ 'rotate-180': expanded }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    
    <!-- 展开内容 - 结果或错误 -->
    <div
      v-show="expanded && canExpand"
      class="px-4 py-3 bg-bg-primary border-t border-border-default"
    >
      <!-- 错误信息 -->
      <div v-if="toolCall.error" class="text-sm text-red-400">
        <div class="font-medium mb-1">Error:</div>
        <pre class="text-xs overflow-x-auto whitespace-pre-wrap">{{ toolCall.error }}</pre>
      </div>
      
      <!-- 成功结果 -->
      <div v-else-if="toolCall.result" class="text-sm text-text-secondary">
        <div class="font-medium text-text-primary mb-1">Result:</div>
        <pre class="text-xs overflow-x-auto whitespace-pre-wrap max-h-64 overflow-y-auto">{{ toolCall.result }}</pre>
      </div>
    </div>
  </div>
</template>
