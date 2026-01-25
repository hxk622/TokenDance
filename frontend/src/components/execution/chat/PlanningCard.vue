<script setup lang="ts">
/**
 * PlanningCard - 规划/思考卡片
 * 
 * 对标 AnyGen 的 Planning 卡片:
 * - 灯泡图标
 * - 可折叠
 * - 支持流式内容
 * - 思考中/完成状态
 */
import { computed } from 'vue'
import { Lightbulb } from 'lucide-vue-next'
import CollapsibleCard from './CollapsibleCard.vue'
import type { PlanningData } from './types'

interface Props {
  data: PlanningData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
}>()

// Support both status and streaming properties
const isThinking = computed(() => props.data.status === 'thinking' || props.data.streaming === true)

function handleToggle() {
  emit('update:collapsed', !props.data.collapsed)
}
</script>

<template>
  <CollapsibleCard
    :title="data.title || 'Planning'"
    :collapsed="data.collapsed"
    padding="md"
    @toggle="handleToggle"
  >
    <template #icon>
      <div :class="['planning-icon', { thinking: isThinking }]">
        <Lightbulb class="icon" />
      </div>
    </template>

    <!-- Planning content -->
    <div class="planning-content">
      <!-- Mask gradient for long content -->
      <div
        v-if="data.collapsed"
        class="content-mask"
      />
      
      <div class="prose prose-sm">
        <p
          v-for="(paragraph, idx) in data.content.split('\n\n')"
          :key="idx"
          class="paragraph"
        >
          {{ paragraph }}
        </p>
      </div>

      <!-- Streaming cursor -->
      <span
        v-if="isThinking"
        class="streaming-cursor"
      />
    </div>
  </CollapsibleCard>
</template>

<style scoped>
.planning-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.planning-icon .icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-secondary);
}

.planning-icon.thinking .icon {
  color: var(--td-state-thinking, #00D9FF);
  animation: pulse-icon 2s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.planning-content {
  position: relative;
  font-size: 12px;
  line-height: 1.6;
  color: var(--any-text-secondary);
  max-height: 128px;
  overflow-y: auto;
  scrollbar-width: none;
}

.planning-content::-webkit-scrollbar {
  display: none;
}

/* Mask for collapsed state preview */
.content-mask {
  position: absolute;
  inset: 0;
  z-index: 10;
  pointer-events: none;
  background: linear-gradient(
    to bottom,
    transparent 60%,
    var(--any-bg-secondary) 100%
  );
}

.prose {
  width: 100%;
  max-width: none;
}

.paragraph {
  margin: 4px 0;
}

.paragraph:first-child {
  margin-top: 0;
}

/* Streaming cursor */
.streaming-cursor {
  display: inline-block;
  width: 6px;
  height: 14px;
  background: var(--td-state-thinking, #00D9FF);
  margin-left: 2px;
  animation: blink 1s ease-in-out infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
