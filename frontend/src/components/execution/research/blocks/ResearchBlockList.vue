<script setup lang="ts">
/**
 * ResearchBlockList - 研究 Block 列表容器
 * 
 * 职责：
 * - 渲染 Block 列表
 * - 显示 Session 摘要
 * - 协调 Block 展开/折叠
 * - 转发事件到父组件
 */
import { computed, toRef } from 'vue'
import ResearchBlock from './ResearchBlock.vue'
import SessionSummary from './SessionSummary.vue'
import type { ResearchSession } from './types'
import type { ResearchSource, ResearchIntervention } from '../types'
import { useResearchBlocks, type BlockEvent } from '@/composables/useResearchBlocks'
import { Minimize2, Maximize2 } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  /** 研究主题 */
  topic: string
  /** 是否显示 Session 摘要 */
  showSummary?: boolean
}>(), {
  showSummary: true,
})

const emit = defineEmits<{
  (e: 'block-expand', blockId: string): void
  (e: 'source-click', source: ResearchSource): void
  (e: 'open-url', url: string): void
  (e: 'intervention', intervention: ResearchIntervention): void
}>()

// Use the composable for state management
const topicRef = toRef(props, 'topic')
const {
  session,
  toggleBlockExpand,
  collapseAll,
  expandAll,
  handleEvent,
  initSession,
} = useResearchBlocks(topicRef)

// Initialize session on mount if topic exists
if (props.topic) {
  initSession()
}

// 是否有任何展开的 Block
const hasExpandedBlocks = computed(() => {
  return session.value?.blocks.some(b => b.isExpanded) ?? false
})

// 是否所有 Block 都展开
const allExpanded = computed(() => {
  return session.value?.blocks.every(b => b.isExpanded) ?? false
})

function handleToggle(blockId: string) {
  toggleBlockExpand(blockId)
  emit('block-expand', blockId)
}

function handleSourceClick(source: ResearchSource) {
  emit('source-click', source)
}

function handleOpenUrl(url: string) {
  emit('open-url', url)
}

// Expose methods for parent component
defineExpose({
  handleEvent,
  collapseAll,
  expandAll,
  session,
})
</script>

<template>
  <div class="research-block-list">
    <!-- Session Summary -->
    <SessionSummary 
      v-if="showSummary && session"
      :session="session"
    />
    
    <!-- Toolbar -->
    <div
      v-if="session && session.blocks.length > 0"
      class="list-toolbar"
    >
      <button 
        v-if="hasExpandedBlocks && !allExpanded"
        class="toolbar-btn"
        title="折叠所有"
        @click="collapseAll"
      >
        <Minimize2 class="toolbar-icon" />
        <span>折叠所有</span>
      </button>
      <button 
        v-if="!allExpanded"
        class="toolbar-btn"
        title="展开所有"
        @click="expandAll"
      >
        <Maximize2 class="toolbar-icon" />
        <span>展开所有</span>
      </button>
    </div>
    
    <!-- Blocks List -->
    <div
      v-if="session"
      class="blocks-container"
    >
      <TransitionGroup name="block-list">
        <ResearchBlock
          v-for="block in session.blocks"
          :key="block.id"
          :block="block"
          @toggle="handleToggle"
          @source-click="handleSourceClick"
          @open-url="handleOpenUrl"
        />
      </TransitionGroup>
    </div>
    
    <!-- Empty State -->
    <div
      v-else
      class="empty-state"
    >
      <p>研究尚未开始</p>
    </div>
  </div>
</template>

<style scoped>
.research-block-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Toolbar */
.list-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  margin-bottom: 10px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  font-size: 12px;
  color: var(--any-text-muted);
  background: transparent;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 150ms ease;
}

.toolbar-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
  border-color: var(--any-text-muted);
}

.toolbar-icon {
  width: 14px;
  height: 14px;
}

/* Blocks Container */
.blocks-container {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Empty State */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--any-text-muted);
  font-size: 14px;
}

/* List Transitions */
.block-list-enter-active,
.block-list-leave-active {
  transition: all 300ms ease;
}

.block-list-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.block-list-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

.block-list-move {
  transition: transform 300ms ease;
}
</style>
