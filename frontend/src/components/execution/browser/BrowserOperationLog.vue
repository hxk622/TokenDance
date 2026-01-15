<script setup lang="ts">
import { computed } from 'vue'
import type { BrowserOperation } from './types'
import { OPERATION_CONFIG } from './types'

export interface BrowserOperationLogProps {
  operations: BrowserOperation[]
  status?: 'idle' | 'running' | 'completed' | 'error'
  onShowTimeLapse?: () => void
}

const props = withDefaults(defineProps<BrowserOperationLogProps>(), {
  status: 'idle',
})

const emit = defineEmits<{
  showTimeLapse: []
  showScreenshot: [path: string]
}>()

const statusConfig = computed(() => {
  const configs = {
    idle: { text: '待开始', class: 'text-text-tertiary' },
    running: { text: '采集中', class: 'text-accent-primary' },
    completed: { text: '已完成', class: 'text-green-400' },
    error: { text: '出错', class: 'text-red-400' },
  }
  return configs[props.status]
})

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const getOperationIcon = (type: string) => {
  return OPERATION_CONFIG[type]?.icon || 'cog'
}

const getOperationLabel = (type: string) => {
  return OPERATION_CONFIG[type]?.label || type
}

const getOperationColor = (type: string) => {
  return OPERATION_CONFIG[type]?.color || 'text-text-secondary'
}

const truncateTarget = (target?: string, maxLen = 40) => {
  if (!target) return ''
  return target.length > maxLen ? target.slice(0, maxLen) + '...' : target
}
</script>

<template>
  <div class="browser-operation-log bg-bg-secondary rounded-lg border border-border-default">
    <!-- 头部 -->
    <div class="px-4 py-3 border-b border-border-default flex items-center justify-between">
      <div class="flex items-center gap-2">
        <svg class="w-4 h-4 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
            d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
        </svg>
        <span class="text-sm font-medium text-text-primary">网页采集</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs" :class="statusConfig.class">
          {{ statusConfig.text }}
        </span>
        <button 
          v-if="operations.length > 0"
          @click="emit('showTimeLapse')"
          class="text-xs text-accent-primary hover:text-accent-primary/80 transition-colors"
        >
          查看完整过程
        </button>
      </div>
    </div>
    
    <!-- 操作列表 -->
    <div class="max-h-80 overflow-y-auto">
      <div v-if="operations.length === 0" class="p-4 text-center text-text-tertiary text-sm">
        暂无浏览器操作
      </div>
      
      <div v-else class="divide-y divide-border-default">
        <div 
          v-for="op in operations"
          :key="op.id"
          class="px-4 py-2.5 flex items-center gap-3 hover:bg-bg-tertiary/50 transition-colors"
        >
          <!-- 状态指示器 -->
          <div class="flex-shrink-0 w-1.5 h-1.5 rounded-full" :class="{
            'bg-gray-400': op.status === 'pending',
            'bg-accent-primary animate-pulse': op.status === 'running',
            'bg-green-400': op.status === 'success',
            'bg-red-400': op.status === 'error',
          }" />
          
          <!-- 操作图标 -->
          <div class="flex-shrink-0" :class="getOperationColor(op.type)">
            <!-- Globe -->
            <svg v-if="getOperationIcon(op.type) === 'globe'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
            <!-- Cursor Click -->
            <svg v-else-if="getOperationIcon(op.type) === 'cursor-click'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
            </svg>
            <!-- Pencil -->
            <svg v-else-if="getOperationIcon(op.type) === 'pencil'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <!-- Camera -->
            <svg v-else-if="getOperationIcon(op.type) === 'camera'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <!-- Photo -->
            <svg v-else-if="getOperationIcon(op.type) === 'photo'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <!-- X Circle -->
            <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          
          <!-- 操作信息 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm text-text-primary">{{ getOperationLabel(op.type) }}</span>
              <span v-if="op.target" class="text-xs text-text-tertiary font-mono truncate">
                {{ truncateTarget(op.target) }}
              </span>
            </div>
            <div v-if="op.error" class="text-xs text-red-400 mt-0.5 truncate">
              {{ op.error }}
            </div>
          </div>
          
          <!-- 时间和截图 -->
          <div class="flex items-center gap-2 flex-shrink-0">
            <span class="text-xs text-text-tertiary">{{ formatTime(op.timestamp) }}</span>
            <img 
              v-if="op.screenshotPath"
              :src="op.screenshotPath"
              class="w-8 h-6 rounded object-cover cursor-pointer hover:opacity-80 border border-border-default"
              @click="emit('showScreenshot', op.screenshotPath)"
            />
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部统计 -->
    <div v-if="operations.length > 0" class="px-4 py-2 border-t border-border-default flex items-center justify-between text-xs text-text-tertiary">
      <span>共 {{ operations.length }} 次操作</span>
      <span v-if="operations.some(o => o.screenshotPath)">
        {{ operations.filter(o => o.screenshotPath).length }} 张截图
      </span>
    </div>
  </div>
</template>

<style scoped>
.browser-operation-log {
  min-width: 280px;
}
</style>
