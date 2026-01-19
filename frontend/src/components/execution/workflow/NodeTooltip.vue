<script setup lang="ts">
import { computed } from 'vue'
import { ClockIcon, CheckCircleIcon, ExclamationCircleIcon, PauseCircleIcon } from '@heroicons/vue/24/outline'

interface Props {
  visible: boolean
  nodeId: string
  status: 'pending' | 'running' | 'success' | 'error'
  label: string
  x: number
  y: number
  dependencies?: string[]
  metadata?: {
    startTime?: number
    endTime?: number
    duration?: number
    output?: string
    errorMessage?: string
  }
}

const props = defineProps<Props>()

const statusText = computed(() => {
  const statusMap = {
    pending: '未执行',
    running: '执行中',
    success: '已完成',
    error: '出错',
  }
  return statusMap[props.status]
})

const statusColor = computed(() => {
  const colorMap = {
    pending: '#8E8E93',   // 灰色
    running: '#FFB800',   // 黄色
    success: '#00FF88',   // 绿色
    error: '#FF3B30',     // 红色
  }
  return colorMap[props.status]
})

// 状态图标组件映射
const statusIconMap = {
  pending: PauseCircleIcon,
  running: ClockIcon,
  success: CheckCircleIcon,
  error: ExclamationCircleIcon,
}

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
      <!-- Header: 任务名称 + 状态图标 -->
      <div class="tooltip-header">
        <component 
          :is="statusIconMap[status]" 
          class="w-5 h-5 status-icon"
          :style="{ color: statusColor }"
        />
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
        <span class="node-id-badge">Task-{{ nodeId }}</span>
      </div>

      <!-- Metadata -->
      <div class="metadata-section">
        <div class="metadata-row">
          <span class="meta-label">执行时长</span>
          <span class="meta-value">{{ duration }}</span>
        </div>
        <div
          v-if="dependencies && dependencies.length > 0"
          class="metadata-row"
        >
          <span class="meta-label">依赖任务</span>
          <span class="meta-value">{{ dependencies.length }} 个上游</span>
        </div>
      </div>

      <!-- Error Message -->
      <div
        v-if="status === 'error' && metadata?.errorMessage"
        class="error-section"
      >
        <div class="error-label">
          错误信息
        </div>
        <div class="error-content">
          {{ metadata.errorMessage }}
        </div>
      </div>

      <!-- Output Preview -->
      <div
        v-if="metadata?.output && status !== 'error'"
        class="output-section"
      >
        <div class="output-label">
          输出摘要
        </div>
        <div class="output-content">
          {{ outputPreview }}
        </div>
      </div>

      <!-- Focus Mode Hint -->
      <div class="focus-hint">
        <span class="hint-text">双击节点查看详情</span>
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

/* Error Section */
.error-section {
  padding-top: 12px;
  border-top: 1px solid var(--any-border);
}

.error-label {
  font-size: 11px;
  color: #FF3B30;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.error-content {
  font-size: 12px;
  line-height: 1.6;
  color: #FF3B30;
  background: rgba(255, 59, 48, 0.1);
  padding: 8px;
  border-radius: var(--any-radius-sm);
  border: 1px solid rgba(255, 59, 48, 0.3);
}

/* Focus Mode Hint */
.focus-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  margin-top: 12px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
}

.hint-text {
  font-size: 11px;
  color: var(--any-text-secondary);
  letter-spacing: 0.3px;
}

.status-icon {
  flex-shrink: 0;
}
</style>
