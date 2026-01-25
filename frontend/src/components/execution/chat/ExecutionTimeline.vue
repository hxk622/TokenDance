<script setup lang="ts">
/**
 * ExecutionTimeline - 执行步骤 Timeline 容器
 * 
 * 对标 AnyGen 的 Timeline 组件:
 * - 管理步骤列表
 * - 处理步骤状态更新
 * - 提供统一的事件处理
 */
import TimelineStep from './TimelineStep.vue'
import type { ExecutionStep, Source } from './types'

interface Props {
  steps: ExecutionStep[]
}

defineProps<Props>()

const emit = defineEmits<{
  'step-toggle': [stepId: string, collapsed: boolean]
  'source-click': [source: Source]
}>()

function handleStepToggle(stepId: string, collapsed: boolean) {
  emit('step-toggle', stepId, collapsed)
}

function handleSourceClick(source: Source) {
  emit('source-click', source)
}
</script>

<template>
  <div class="execution-timeline">
    <TimelineStep
      v-for="(step, index) in steps"
      :key="step.id"
      :step="step"
      :is-last="index === steps.length - 1"
      @update:collapsed="(val) => handleStepToggle(step.id, val)"
      @source-click="handleSourceClick"
    />
    
    <!-- Empty state -->
    <div
      v-if="steps.length === 0"
      class="timeline-empty"
    >
      <span>暂无执行步骤</span>
    </div>
  </div>
</template>

<style scoped>
.execution-timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
  position: relative;
}

.timeline-empty {
  padding: 16px;
  text-align: center;
  color: var(--any-text-muted);
  font-size: 13px;
}
</style>
