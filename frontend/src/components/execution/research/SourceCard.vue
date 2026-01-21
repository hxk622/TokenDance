<script setup lang="ts">
/**
 * SourceCard - 信息来源卡片
 * 
 * 展示单个研究来源的信息，包括：
 * - 域名和 favicon
 * - 可信度等级
 * - 阅读状态
 * - 提取的关键事实
 */
import { computed } from 'vue'
import {
  DocumentTextIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/vue/24/outline'
import type { ResearchSource, SourceStatus } from './types'
import { CREDIBILITY_CONFIG, getFaviconUrl } from './types'

// Props
const props = defineProps<{
  source: ResearchSource
  compact?: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'click', source: ResearchSource): void
  (e: 'open-url', url: string): void
}>()

// Computed
const faviconUrl = computed(() => getFaviconUrl(props.source.domain))

const credibilityConfig = computed(() => 
  CREDIBILITY_CONFIG[props.source.credibilityLevel]
)

const statusConfig = computed(() => {
  const configs: Record<SourceStatus, { class: string; text: string; showPulse: boolean }> = {
    pending: {
      class: 'text-[var(--any-text-muted)]',
      text: '待阅读',
      showPulse: false,
    },
    reading: {
      class: 'text-[var(--exec-accent)]',
      text: '阅读中',
      showPulse: true,
    },
    done: {
      class: 'text-[var(--exec-success)]',
      text: '已完成',
      showPulse: false,
    },
    skipped: {
      class: 'text-[var(--any-text-tertiary)]',
      text: '已跳过',
      showPulse: false,
    },
    failed: {
      class: 'text-[var(--exec-error)]',
      text: '读取失败',
      showPulse: false,
    },
  }
  return configs[props.source.status]
})

// Methods
const handleClick = () => {
  emit('click', props.source)
}

const handleOpenUrl = (e: Event) => {
  e.stopPropagation()
  emit('open-url', props.source.url)
}
</script>

<template>
  <div
    class="source-card"
    :class="{ 'source-card--compact': compact }"
    @click="handleClick"
  >
    <!-- Header -->
    <div class="source-header">
      <!-- Favicon + Domain -->
      <div class="flex items-center gap-2 min-w-0 flex-1">
        <img
          :src="faviconUrl"
          :alt="source.domain"
          class="w-4 h-4 rounded flex-shrink-0"
          @error="($event.target as HTMLImageElement).style.display = 'none'"
        >
        <span class="text-xs text-[var(--any-text-secondary)] truncate">
          {{ source.domain }}
        </span>
      </div>

      <!-- Credibility Badge -->
      <span
        class="credibility-badge"
        :style="{
          color: credibilityConfig.color,
          backgroundColor: credibilityConfig.bgColor,
        }"
      >
        {{ credibilityConfig.label }}
      </span>
    </div>

    <!-- Title -->
    <p
      class="source-title"
      :class="{ 'line-clamp-1': compact, 'line-clamp-2': !compact }"
    >
      {{ source.title }}
    </p>

    <!-- Status + Actions -->
    <div class="source-footer">
      <!-- Status -->
      <div class="flex items-center gap-1.5">
        <span
          class="status-dot"
          :class="{
            'status-dot--pulse': statusConfig.showPulse,
            'bg-[var(--exec-accent)]': source.status === 'reading',
            'bg-[var(--exec-success)]': source.status === 'done',
            'bg-[var(--any-text-muted)]': source.status === 'pending',
            'bg-[var(--any-text-tertiary)]': source.status === 'skipped',
            'bg-[var(--exec-error)]': source.status === 'failed',
          }"
        />
        <span :class="['text-xs', statusConfig.class]">
          {{ statusConfig.text }}
        </span>
      </div>

      <!-- Open URL Button -->
      <button
        class="open-url-btn"
        title="打开原文"
        @click="handleOpenUrl"
      >
        <ArrowTopRightOnSquareIcon class="w-3.5 h-3.5" />
      </button>
    </div>

    <!-- Extracted Facts (only in non-compact mode) -->
    <div
      v-if="!compact && source.extractedFacts && source.extractedFacts.length > 0"
      class="source-facts"
    >
      <div
        v-for="(fact, index) in source.extractedFacts.slice(0, 2)"
        :key="index"
        class="fact-item"
      >
        <CheckCircleIcon class="w-3 h-3 text-[var(--exec-success)] flex-shrink-0 mt-0.5" />
        <span class="text-xs text-[var(--any-text-secondary)]">{{ fact }}</span>
      </div>
      <span
        v-if="source.extractedFacts.length > 2"
        class="text-xs text-[var(--any-text-muted)]"
      >
        +{{ source.extractedFacts.length - 2 }} 更多发现
      </span>
    </div>
  </div>
</template>

<style scoped>
.source-card {
  padding: 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.source-card:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.source-card--compact {
  padding: 10px;
}

.source-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.credibility-badge {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.source-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.source-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-dot--pulse {
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.open-url-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: var(--any-text-muted);
  border-radius: 4px;
  transition: all 150ms ease;
}

.open-url-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.source-facts {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--any-border);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fact-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
</style>
