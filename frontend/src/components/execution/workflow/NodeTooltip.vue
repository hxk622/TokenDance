<script setup lang="ts">
import { computed } from 'vue'
import { CpuChipIcon, PencilSquareIcon } from '@heroicons/vue/24/outline'

interface Props {
  visible: boolean
  nodeId: string
  nodeType: 'manus' | 'coworker'
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
  label: string
  x: number
  y: number
  metadata?: {
    startTime?: number
    duration?: number
    output?: string
  }
}

const props = defineProps<Props>()

const statusText = computed(() => {
  const statusMap = {
    active: '执行中',
    success: '已完成',
    pending: '等待确认',
    error: '执行失败',
    inactive: '待执行',
  }
  return statusMap[props.status]
})

const statusColor = computed(() => {
  const colorMap = {
    active: '#00D9FF',
    success: '#00FF88',
    pending: '#FFB800',
    error: '#FF3B30',
    inactive: '#8E8E93',
  }
  return colorMap[props.status]
})

const duration = computed(() => {
  if (!props.metadata?.duration) return '-'
  const seconds = Math.floor(props.metadata.duration / 1000)
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}分${remainingSeconds}秒`
})

const outputPreview = computed(() => {
  if (!props.metadata?.output) return '无输出'
  return props.metadata.output.length > 100 
    ? props.metadata.output.substring(0, 100) + '...'
    : props.metadata.output
})
</script>

<template>
  <Teleport to="body">
    <div 
      v-if="visible" 
      class="node-tooltip"
      :style="{ 
        left: `${x + 40}px`, 
        top: `${y}px`,
        borderColor: statusColor 
      }"
    >
      <!-- Header -->
      <div class="tooltip-header">
        <span class="node-type-icon">
          <CpuChipIcon
            v-if="nodeType === 'manus'"
            class="w-5 h-5"
          />
          <PencilSquareIcon
            v-else
            class="w-5 h-5"
          />
        </span>
        <span class="node-label">{{ label }}</span>
      </div>

      <!-- Status Badge -->
      <div class="status-row">
        <span
          class="status-badge"
          :style="{ 
            background: `${statusColor}30`, 
            color: statusColor,
            borderColor: statusColor
          }"
        >
          {{ statusText }}
        </span>
        <span class="node-id-badge">Node-{{ nodeId }}</span>
      </div>

      <!-- Metadata -->
      <div class="metadata-section">
        <div class="metadata-row">
          <span class="meta-label">执行时长</span>
          <span class="meta-value">{{ duration }}</span>
        </div>
        <div class="metadata-row">
          <span class="meta-label">Agent类型</span>
          <span class="meta-value">{{ nodeType === 'manus' ? 'Manus' : 'Coworker' }}</span>
        </div>
      </div>

      <!-- Output Preview -->
      <div
        v-if="metadata?.output"
        class="output-section"
      >
        <div class="output-label">
          输出摘要
        </div>
        <div class="output-content">
          {{ outputPreview }}
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* NodeTooltip - 使用全局主题变量 */
.node-tooltip {
  position: fixed;
  z-index: 9999;
  min-width: 280px;
  max-width: 400px;
  padding: 16px;
  background: var(--any-bg-secondary);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid;
  border-radius: var(--any-radius-md);
  box-shadow: var(--any-shadow-xl);
  pointer-events: none;
  animation: tooltipFadeIn var(--any-duration-fast) var(--any-ease-out);
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--any-border);
}

.node-type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--any-text-secondary);
}

.node-label {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.status-badge {
  padding: 4px 8px;
  border-radius: var(--any-radius-sm);
  border: 1px solid;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.node-id-badge {
  padding: 4px 8px;
  border-radius: var(--any-radius-sm);
  background: var(--any-bg-hover);
  font-size: 11px;
  color: var(--any-text-secondary);
  font-family: 'SF Mono', monospace;
}

.metadata-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.metadata-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.meta-label {
  color: var(--any-text-secondary);
}

.meta-value {
  color: var(--any-text-primary);
  font-weight: 500;
}

.output-section {
  padding-top: 12px;
  border-top: 1px solid var(--any-border);
}

.output-label {
  font-size: 11px;
  color: var(--any-text-secondary);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.output-content {
  font-size: 12px;
  line-height: 1.6;
  color: var(--any-text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
  background: var(--any-bg-tertiary);
  padding: 8px;
  border-radius: var(--any-radius-sm);
  max-height: 120px;
  overflow-y: auto;
}

.output-content::-webkit-scrollbar {
  width: 4px;
}

.output-content::-webkit-scrollbar-track {
  background: var(--any-bg-tertiary);
}

.output-content::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 2px;
}
</style>
