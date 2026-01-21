<script setup lang="ts">
/**
 * SessionSummary - 研究会话总体进度卡片
 * 
 * 显示：
 * - 研究主题
 * - 总体进度
 * - 已完成/进行中阶段数
 * - 总耗时
 */
import { computed } from 'vue'
import { CheckCircle2, Clock, Sparkles } from 'lucide-vue-next'
import type { ResearchSession } from './types'

const props = defineProps<{
  session: ResearchSession
}>()

// 统计
const stats = computed(() => {
  const blocks = props.session.blocks
  const completed = blocks.filter(b => b.status === 'completed').length
  const running = blocks.filter(b => b.status === 'running').length
  const total = blocks.length
  return { completed, running, total }
})

// 总耗时
const totalDuration = computed(() => {
  const now = Date.now()
  const seconds = Math.floor((now - props.session.startedAt) / 1000)
  
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  if (minutes < 60) {
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
})

// 状态文本
const statusText = computed(() => {
  switch (props.session.status) {
    case 'idle':
      return '准备开始'
    case 'running':
      return '研究进行中'
    case 'paused':
      return '已暂停'
    case 'completed':
      return '研究完成'
    default:
      return ''
  }
})

// 状态颜色
const statusColor = computed(() => {
  switch (props.session.status) {
    case 'running':
      return 'var(--exec-accent)'
    case 'completed':
      return 'var(--exec-success)'
    case 'paused':
      return 'var(--exec-warning, #ff9500)'
    default:
      return 'var(--any-text-muted)'
  }
})
</script>

<template>
  <div 
    class="session-summary"
    :class="{ 'session-summary--completed': session.status === 'completed' }"
  >
    <!-- Left: Topic + Status -->
    <div class="summary-left">
      <div class="topic-row">
        <Sparkles v-if="session.status === 'completed'" class="topic-icon topic-icon--success" />
        <span class="topic-text">{{ session.topic }}</span>
      </div>
      <div class="status-row">
        <span class="status-badge" :style="{ color: statusColor }">
          {{ statusText }}
        </span>
        <span class="status-divider">·</span>
        <span class="phases-text">
          {{ stats.completed }}/{{ stats.total }} 阶段完成
        </span>
      </div>
    </div>
    
    <!-- Right: Progress + Duration -->
    <div class="summary-right">
      <!-- Progress Ring -->
      <div class="progress-ring">
        <svg viewBox="0 0 36 36" class="ring-svg">
          <circle
            cx="18"
            cy="18"
            r="16"
            fill="none"
            stroke="var(--any-border)"
            stroke-width="2.5"
          />
          <circle
            cx="18"
            cy="18"
            r="16"
            fill="none"
            :stroke="statusColor"
            stroke-width="2.5"
            stroke-linecap="round"
            :stroke-dasharray="`${session.overallProgress}, 100`"
            transform="rotate(-90 18 18)"
            class="ring-progress"
          />
        </svg>
        <span class="ring-text">{{ session.overallProgress }}%</span>
      </div>
      
      <!-- Duration -->
      <div class="duration">
        <Clock class="duration-icon" />
        <span class="duration-text">{{ totalDuration }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.session-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  margin-bottom: 12px;
}

.session-summary--completed {
  background: rgba(0, 200, 83, 0.05);
  border-color: var(--exec-success);
}

/* Left Section */
.summary-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.topic-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.topic-icon--success {
  color: var(--exec-success);
}

.topic-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.status-badge {
  font-weight: 500;
}

.status-divider {
  color: var(--any-text-muted);
}

.phases-text {
  color: var(--any-text-muted);
}

/* Right Section */
.summary-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.progress-ring {
  position: relative;
  width: 44px;
  height: 44px;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.ring-progress {
  transition: stroke-dasharray 300ms ease;
}

.ring-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 11px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.duration {
  display: flex;
  align-items: center;
  gap: 5px;
}

.duration-icon {
  width: 14px;
  height: 14px;
  color: var(--any-text-muted);
}

.duration-text {
  font-size: 12px;
  color: var(--any-text-muted);
  font-variant-numeric: tabular-nums;
}

/* Responsive */
@media (max-width: 480px) {
  .session-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .summary-right {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
