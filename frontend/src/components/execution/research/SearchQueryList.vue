<script setup lang="ts">
/**
 * SearchQueryList - 搜索关键词列表
 * 
 * 显示研究过程中执行的搜索查询及其状态
 */
import { computed } from 'vue'
import {
  MagnifyingGlassIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/vue/24/outline'
import type { SearchQuery, QueryStatus } from './types'

// Props
const props = defineProps<{
  queries: SearchQuery[]
  maxVisible?: number
}>()

// Computed
const visibleQueries = computed(() => {
  if (!props.maxVisible || props.queries.length <= props.maxVisible) {
    return props.queries
  }
  return props.queries.slice(0, props.maxVisible)
})

const hiddenCount = computed(() => {
  if (!props.maxVisible) return 0
  return Math.max(0, props.queries.length - props.maxVisible)
})

const stats = computed(() => {
  const done = props.queries.filter(q => q.status === 'done').length
  const total = props.queries.length
  return { done, total }
})

// Methods
const getStatusConfig = (status: QueryStatus) => {
  const configs: Record<QueryStatus, { icon: typeof CheckCircleIcon; class: string; text: string }> = {
    pending: {
      icon: MagnifyingGlassIcon,
      class: 'text-[var(--any-text-muted)]',
      text: '待执行',
    },
    running: {
      icon: MagnifyingGlassIcon,
      class: 'text-[var(--exec-accent)] animate-pulse',
      text: '搜索中',
    },
    done: {
      icon: CheckCircleIcon,
      class: 'text-[var(--exec-success)]',
      text: '完成',
    },
    failed: {
      icon: XCircleIcon,
      class: 'text-[var(--exec-error)]',
      text: '失败',
    },
  }
  return configs[status]
}
</script>

<template>
  <div class="search-query-list">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <MagnifyingGlassIcon class="w-4 h-4 text-[var(--any-text-secondary)]" />
        <span class="text-sm font-medium text-[var(--any-text-primary)]">
          搜索关键词
        </span>
      </div>
      <span class="text-xs text-[var(--any-text-muted)]">
        {{ stats.done }}/{{ stats.total }}
      </span>
    </div>

    <!-- Query List -->
    <div class="space-y-2">
      <div
        v-for="query in visibleQueries"
        :key="query.id"
        class="query-item"
      >
        <!-- Status Icon -->
        <component
          :is="getStatusConfig(query.status).icon"
          :class="['w-4 h-4 flex-shrink-0', getStatusConfig(query.status).class]"
        />
        
        <!-- Query Text -->
        <span class="flex-1 text-sm text-[var(--any-text-primary)] truncate">
          {{ query.text }}
        </span>
        
        <!-- Result Count / Status -->
        <span 
          v-if="query.status === 'done' && query.resultCount !== undefined"
          class="text-xs text-[var(--any-text-muted)] whitespace-nowrap"
        >
          {{ query.resultCount }} 结果
        </span>
        <span 
          v-else-if="query.status === 'running'"
          class="text-xs text-[var(--exec-accent)] whitespace-nowrap"
        >
          搜索中...
        </span>
      </div>

      <!-- Hidden count -->
      <div
        v-if="hiddenCount > 0"
        class="text-xs text-[var(--any-text-muted)] text-center py-1"
      >
        还有 {{ hiddenCount }} 个查询
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-query-list {
  padding: 12px;
  background: var(--any-bg-secondary);
  border-radius: 8px;
}

.query-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--any-bg-primary);
  border-radius: 6px;
  transition: background 150ms ease;
}

.query-item:hover {
  background: var(--any-bg-hover);
}

/* Running animation */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}
</style>
