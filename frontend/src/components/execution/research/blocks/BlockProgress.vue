<script setup lang="ts">
/**
 * BlockProgress - Block 进度条组件
 * 
 * 显示当前 Block 的执行进度
 */
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  progress: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  showPercentage?: boolean
}>(), {
  showPercentage: true,
})

const progressWidth = computed(() => {
  return `${Math.min(100, Math.max(0, props.progress))}%`
})

const progressColor = computed(() => {
  switch (props.status) {
    case 'running':
      return 'var(--exec-accent)'
    case 'completed':
      return 'var(--exec-success)'
    case 'failed':
      return 'var(--exec-error)'
    default:
      return 'var(--any-border)'
  }
})
</script>

<template>
  <div 
    v-if="status === 'running'" 
    class="block-progress"
  >
    <div class="progress-track">
      <div 
        class="progress-bar"
        :style="{ 
          width: progressWidth,
          backgroundColor: progressColor 
        }"
      />
    </div>
    <span
      v-if="showPercentage"
      class="progress-text"
    >
      {{ progress }}%
    </span>
  </div>
</template>

<style scoped>
.block-progress {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px 12px;
}

.progress-track {
  flex: 1;
  height: 4px;
  background: var(--any-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 2px;
  transition: width 300ms ease;
}

.progress-text {
  font-size: 12px;
  font-weight: 500;
  color: var(--exec-accent);
  font-variant-numeric: tabular-nums;
  min-width: 36px;
  text-align: right;
}
</style>
