<script setup lang="ts">
/**
 * ResearchBlock - 单个研究 Block 容器
 * 
 * 组合：
 * - BlockHeader: 标题栏
 * - BlockContent: 展开内容
 * - BlockProgress: 进度条
 */
import { ref, watch } from 'vue'
import BlockHeader from './BlockHeader.vue'
import BlockContent from './BlockContent.vue'
import BlockProgress from './BlockProgress.vue'
import type { ResearchBlock as ResearchBlockType } from './types'
import type { ResearchSource } from '../types'

const props = defineProps<{
  block: ResearchBlockType
}>()

const emit = defineEmits<{
  (e: 'toggle', blockId: string): void
  (e: 'source-click', source: ResearchSource): void
  (e: 'open-url', url: string): void
}>()

// Ref for the block element (for scroll-into-view)
const blockRef = ref<HTMLElement | null>(null)

// Watch for running status to scroll into view
watch(() => props.block.status, (newStatus, oldStatus) => {
  if (newStatus === 'running' && oldStatus !== 'running') {
    // Scroll into view with a slight delay for animation
    setTimeout(() => {
      blockRef.value?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'nearest' 
      })
    }, 100)
  }
})

function handleToggle() {
  emit('toggle', props.block.id)
}

function handleSourceClick(source: ResearchSource) {
  emit('source-click', source)
}

function handleOpenUrl(url: string) {
  emit('open-url', url)
}
</script>

<template>
  <div 
    ref="blockRef"
    class="research-block"
    :class="[
      `research-block--${block.status}`,
      { 'research-block--expanded': block.isExpanded }
    ]"
  >
    <!-- Header (always visible) -->
    <BlockHeader 
      :block="block"
      @toggle="handleToggle"
    />
    
    <!-- Expandable Content -->
    <Transition name="expand">
      <div
        v-if="block.isExpanded"
        class="block-body"
      >
        <BlockContent 
          :block="block"
          @source-click="handleSourceClick"
          @open-url="handleOpenUrl"
        />
        
        <!-- Progress (only for running blocks) -->
        <BlockProgress 
          :progress="block.progress"
          :status="block.status"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.research-block {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 10px;
  overflow: hidden;
  transition: all 200ms ease;
}

/* Status-based border colors */
.research-block--pending {
  border-color: var(--any-border);
  opacity: 0.7;
}

.research-block--running {
  border-color: var(--exec-accent);
  box-shadow: 0 0 0 1px rgba(0, 217, 255, 0.2);
}

.research-block--completed {
  border-color: var(--exec-success);
}

.research-block--completed:not(.research-block--expanded) {
  opacity: 0.85;
}

.research-block--failed {
  border-color: var(--exec-error);
}

/* Block body */
.block-body {
  border-top: 1px solid var(--any-border);
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 250ms ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
