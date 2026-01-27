<script setup lang="ts">
/**
 * ToolCallWidget - 工具调用内联小部件
 * 
 * 以内联 widget 方式展示工具调用，无独立头像
 * 设计风格：简洁徽章样式，支持状态显示
 */
import { computed } from 'vue'
import { Wrench, Check, Loader2, AlertCircle } from 'lucide-vue-next'
import type { ToolCall } from './types'

interface Props {
  toolCalls: ToolCall[]
  /** 是否显示为紧凑模式 */
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  compact: false
})

// 获取工具调用的状态图标
function getStatusIcon(status?: ToolCall['status']) {
  switch (status) {
    case 'success':
      return Check
    case 'error':
      return AlertCircle
    case 'running':
      return Loader2
    default:
      return Wrench
  }
}

// 获取状态样式类
function getStatusClass(status?: ToolCall['status']) {
  switch (status) {
    case 'success':
      return 'status-success'
    case 'error':
      return 'status-error'
    case 'running':
      return 'status-running'
    default:
      return 'status-pending'
  }
}

// 格式化参数显示
function formatArgs(args?: string): string {
  if (!args) return ''
  // 尝试解析JSON并简化显示
  try {
    const parsed = JSON.parse(args)
    if (typeof parsed === 'string') return parsed
    if (Array.isArray(parsed)) {
      return parsed.length > 3 ? `${parsed.slice(0, 3).join(', ')}...` : parsed.join(', ')
    }
    return JSON.stringify(parsed, null, 0).slice(0, 50)
  } catch {
    return args.slice(0, 50)
  }
}
</script>

<template>
  <div :class="['tool-call-widget', { compact }]">
    <div class="tool-call-list">
      <div
        v-for="(tool, index) in toolCalls"
        :key="`${tool.name}-${index}`"
        :class="['tool-call-item', getStatusClass(tool.status)]"
      >
        <component
          :is="getStatusIcon(tool.status)"
          :class="['tool-icon', { spinning: tool.status === 'running' }]"
        />
        <span class="tool-name">{{ tool.name }}</span>
        <span
          v-if="tool.args && !compact"
          class="tool-args"
        >
          {{ formatArgs(tool.args) }}
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tool-call-widget {
  margin-bottom: 8px;
}

.tool-call-widget.compact .tool-call-list {
  gap: 4px;
}

.tool-call-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool-call-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  font-size: 12px;
  transition: all 200ms ease;
}

/* Status-specific styles */
.tool-call-item.status-pending {
  color: var(--any-text-secondary);
  border-color: var(--any-border);
}

.tool-call-item.status-running {
  color: var(--td-state-thinking, #00D9FF);
  border-color: var(--td-state-thinking, #00D9FF);
  background: rgba(0, 217, 255, 0.05);
}

.tool-call-item.status-success {
  color: var(--td-state-success, #00FF88);
  border-color: var(--td-state-success, #00FF88);
  background: rgba(0, 255, 136, 0.05);
}

.tool-call-item.status-error {
  color: var(--exec-error, #FF3B30);
  border-color: var(--exec-error, #FF3B30);
  background: rgba(255, 59, 48, 0.05);
}

/* Icon */
.tool-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.tool-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Tool name */
.tool-name {
  font-weight: 500;
  font-family: 'SF Mono', 'Monaco', 'Menlo', 'Consolas', monospace;
}

/* Tool args */
.tool-args {
  color: var(--any-text-muted);
  font-size: 11px;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
