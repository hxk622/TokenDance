<script setup lang="ts">
/**
 * SourceGroup - 来源 favicon 组
 * 
 * 对标 AnyGen 的 AvatarGroup:
 * - 显示最多 maxVisible 个 favicon
 * - 超出部分显示 +N 计数
 * - 头像重叠效果
 */
import { computed } from 'vue'
import type { Source } from './types'

interface Props {
  sources: Source[]
  maxVisible?: number
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<Props>(), {
  maxVisible: 3,
  size: 'sm'
})

const emit = defineEmits<{
  click: [source: Source]
}>()

// Visible sources
const visibleSources = computed(() => {
  return props.sources.slice(0, props.maxVisible)
})

// Overflow count
const overflowCount = computed(() => {
  return Math.max(0, props.sources.length - props.maxVisible)
})

// Get favicon URL (fallback to Google's favicon service)
function getFaviconUrl(source: Source): string {
  if (source.favicon) return source.favicon
  return `https://www.google.com/s2/favicons?sz=128&domain=${source.domain}`
}

function handleClick(source: Source) {
  emit('click', source)
}
</script>

<template>
  <div :class="['source-group', `size-${size}`]">
    <div
      v-for="(source, idx) in visibleSources"
      :key="source.url"
      class="source-avatar"
      :style="{ zIndex: visibleSources.length - idx }"
      :title="source.title || source.domain"
      @click="handleClick(source)"
    >
      <img
        :src="getFaviconUrl(source)"
        :alt="source.domain"
        loading="lazy"
        @error="($event.target as HTMLImageElement).src = '/favicon-fallback.svg'"
      >
    </div>
    
    <!-- Overflow count -->
    <div
      v-if="overflowCount > 0"
      class="source-avatar overflow-count"
      :title="`还有 ${overflowCount} 个来源`"
    >
      <span>+{{ overflowCount }}</span>
    </div>
  </div>
</template>

<style scoped>
.source-group {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

/* Size variants */
.source-group.size-sm {
  --avatar-size: 24px;
  --avatar-font-size: 8px;
  --avatar-spacing: -4px;
}

.source-group.size-md {
  --avatar-size: 28px;
  --avatar-font-size: 10px;
  --avatar-spacing: -6px;
}

.source-avatar {
  position: relative;
  width: var(--avatar-size);
  height: var(--avatar-size);
  border-radius: 50%;
  border: 1px solid var(--any-border);
  background: var(--any-bg-primary);
  overflow: hidden;
  cursor: pointer;
  transition: transform 150ms ease;
}

.source-avatar:not(:first-child) {
  margin-left: var(--avatar-spacing);
}

.source-avatar:hover {
  transform: scale(1.1);
  z-index: 100 !important;
}

.source-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 4px;
}

/* Overflow count badge */
.source-avatar.overflow-count {
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  font-family: monospace;
}

.source-avatar.overflow-count span {
  font-size: var(--avatar-font-size);
  font-weight: 500;
  color: var(--any-text-muted);
  line-height: var(--avatar-size);
}
</style>
