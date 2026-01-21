<script setup lang="ts">
/**
 * BlockHeader - Block 标题栏组件
 * 
 * 显示：
 * - 阶段图标 + 名称
 * - 状态指示
 * - 折叠时显示摘要
 * - 展开/折叠按钮
 */
import { computed } from 'vue'
import {
  ChevronRightIcon,
  ChevronDownIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'
import {
  Compass,
  Search,
  BookOpen,
  BrainCircuit,
  FileText,
  Loader2,
} from 'lucide-vue-next'
import type { ResearchBlock } from './types'
import { PHASE_BLOCK_CONFIG, BLOCK_STATUS_CONFIG } from './types'

const props = defineProps<{
  block: ResearchBlock
}>()

const emit = defineEmits<{
  (e: 'toggle'): void
}>()

// 阶段配置
const phaseConfig = computed(() => {
  return PHASE_BLOCK_CONFIG.find(p => p.id === props.block.phase)
})

// 状态配置
const statusConfig = computed(() => {
  return BLOCK_STATUS_CONFIG[props.block.status]
})

// 图标组件映射
const iconComponents: Record<string, unknown> = {
  Compass,
  Search,
  BookOpen,
  BrainCircuit,
  FileText,
}

const PhaseIcon = computed(() => {
  const iconName = phaseConfig.value?.icon || 'FileText'
  return iconComponents[iconName] || FileText
})

// 状态文本
const statusText = computed(() => {
  if (props.block.status === 'running' && props.block.currentAction) {
    return props.block.currentAction
  }
  return statusConfig.value.label
})

// 摘要文本（仅在折叠时显示）
const summaryText = computed(() => {
  if (props.block.isExpanded) return null
  return props.block.summary?.text || null
})

// 耗时格式化
const durationText = computed(() => {
  if (!props.block.summary?.metrics?.duration) return null
  const seconds = props.block.summary.metrics.duration
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
})
</script>

<template>
  <div 
    class="block-header"
    :class="[
      `block-header--${block.status}`,
      { 'block-header--expanded': block.isExpanded }
    ]"
    @click="emit('toggle')"
  >
    <!-- Left: Icon + Phase Name -->
    <div class="header-left">
      <!-- Expand/Collapse Chevron -->
      <div class="chevron-wrapper">
        <ChevronDownIcon 
          v-if="block.isExpanded" 
          class="chevron-icon" 
        />
        <ChevronRightIcon 
          v-else 
          class="chevron-icon" 
        />
      </div>
      
      <!-- Phase Icon -->
      <div class="phase-icon-wrapper" :class="`phase-icon--${block.status}`">
        <component :is="PhaseIcon" class="phase-icon" />
      </div>
      
      <!-- Phase Name -->
      <span class="phase-name">{{ phaseConfig?.name || '未知阶段' }}</span>
      
      <!-- Summary (collapsed state) -->
      <span v-if="summaryText" class="summary-text">
        {{ summaryText }}
      </span>
    </div>
    
    <!-- Right: Status + Duration -->
    <div class="header-right">
      <!-- Duration -->
      <span v-if="durationText" class="duration-text">
        {{ durationText }}
      </span>
      
      <!-- Status Indicator -->
      <div class="status-indicator" :class="`status--${block.status}`">
        <template v-if="block.status === 'running'">
          <Loader2 class="status-icon status-icon--spinning" />
        </template>
        <template v-else-if="block.status === 'completed'">
          <CheckCircleIcon class="status-icon status-icon--success" />
        </template>
        <template v-else-if="block.status === 'failed'">
          <XCircleIcon class="status-icon status-icon--error" />
        </template>
        <span class="status-text">{{ statusText }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  cursor: pointer;
  border-radius: 10px 10px 0 0;
  transition: background 150ms ease;
  user-select: none;
}

.block-header:hover {
  background: var(--any-bg-hover);
}

.block-header--pending {
  opacity: 0.6;
}

.block-header--running {
  background: var(--block-running-bg, rgba(0, 217, 255, 0.05));
}

.block-header--completed:not(.block-header--expanded) {
  border-radius: 10px;
}

/* Left Section */
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.chevron-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  color: var(--any-text-muted);
  flex-shrink: 0;
}

.chevron-icon {
  width: 14px;
  height: 14px;
  transition: transform 150ms ease;
}

.phase-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--any-bg-tertiary);
  flex-shrink: 0;
  transition: all 200ms ease;
}

.phase-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-secondary);
}

.phase-icon--running {
  background: rgba(0, 217, 255, 0.15);
}

.phase-icon--running .phase-icon {
  color: var(--exec-accent);
}

.phase-icon--completed {
  background: rgba(0, 200, 83, 0.1);
}

.phase-icon--completed .phase-icon {
  color: var(--exec-success);
}

.phase-icon--failed {
  background: rgba(255, 59, 48, 0.1);
}

.phase-icon--failed .phase-icon {
  color: var(--exec-error);
}

.phase-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  flex-shrink: 0;
}

.summary-text {
  font-size: 13px;
  color: var(--any-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 8px;
  border-left: 1px solid var(--any-border);
  margin-left: 4px;
}

/* Right Section */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.duration-text {
  font-size: 12px;
  color: var(--any-text-muted);
  font-variant-numeric: tabular-nums;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}

.status-icon {
  width: 14px;
  height: 14px;
}

.status-icon--spinning {
  color: var(--exec-accent);
  animation: spin 1s linear infinite;
}

.status-icon--success {
  color: var(--exec-success);
}

.status-icon--error {
  color: var(--exec-error);
}

.status-text {
  color: var(--any-text-muted);
}

.status--running .status-text {
  color: var(--exec-accent);
}

.status--completed .status-text {
  color: var(--exec-success);
}

.status--failed .status-text {
  color: var(--exec-error);
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
