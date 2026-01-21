<script setup lang="ts">
/**
 * CitationCard - 引用详情卡片
 * 
 * 显示单个引用的详细信息：
 * - 来源标题和域名
 * - 发布日期
 * - 可信度评分
 * - 原文摘录
 * - 查看原文/复制引用按钮
 */
import { computed } from 'vue'
import { ExternalLink, Copy, Calendar, Shield, Quote, CheckCircle } from 'lucide-vue-next'
import type { Citation } from './types'
import { CREDIBILITY_CONFIG, SOURCE_TYPE_CONFIG, getFaviconUrl } from './types'

interface Props {
  /** 引用数据 */
  citation: Citation
  /** 是否展开显示 */
  expanded?: boolean
  /** 是否紧凑模式 */
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  expanded: true,
  compact: false,
})

const emit = defineEmits<{
  /** 点击查看原文 */
  openUrl: [url: string]
  /** 复制引用 */
  copy: [citation: Citation]
}>()

// 可信度配置
const credibilityInfo = computed(() => {
  return CREDIBILITY_CONFIG[props.citation.source.credibilityLevel]
})

// 来源类型标签
const sourceTypeLabel = computed(() => {
  const type = props.citation.source.type
  return type ? SOURCE_TYPE_CONFIG[type]?.label : '未知来源'
})

// Favicon URL
const faviconUrl = computed(() => getFaviconUrl(props.citation.source.domain))

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return '未知日期'
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return dateStr
  }
}

// 复制引用
async function handleCopy() {
  const text = `[${props.citation.id}] ${props.citation.source.title}. ${props.citation.source.url}`
  try {
    await navigator.clipboard.writeText(text)
    emit('copy', props.citation)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}
</script>

<template>
  <div 
    class="citation-card"
    :class="{ compact: props.compact }"
  >
    <!-- Header -->
    <div class="card-header">
      <div class="source-info">
        <img 
          :src="faviconUrl" 
          class="favicon"
          :alt="citation.source.domain"
          @error="($event.target as HTMLImageElement).style.display = 'none'"
        >
        <div class="source-text">
          <div class="citation-badge">
            [{{ citation.id }}]
          </div>
          <span class="source-title">{{ citation.source.title }}</span>
        </div>
      </div>
      <div 
        class="credibility-badge"
        :style="{ 
          color: credibilityInfo.color,
          backgroundColor: credibilityInfo.bgColor,
        }"
      >
        <Shield class="w-3 h-3" />
        <span>{{ citation.source.credibility }}</span>
      </div>
    </div>

    <!-- Meta Info -->
    <div class="card-meta">
      <span class="meta-item">
        <Calendar class="w-3.5 h-3.5" />
        {{ formatDate(citation.source.publishDate) }}
      </span>
      <span class="meta-item">
        {{ citation.source.domain }}
      </span>
      <span class="meta-item type-badge">
        {{ sourceTypeLabel }}
      </span>
    </div>

    <!-- Excerpt (when expanded) -->
    <div 
      v-if="expanded && citation.excerpt"
      class="card-excerpt"
    >
      <Quote class="quote-icon" />
      <p class="excerpt-text">
        {{ citation.excerpt }}
      </p>
    </div>

    <!-- Actions -->
    <div class="card-actions">
      <button 
        class="action-btn primary"
        @click="emit('openUrl', citation.source.url)"
      >
        <ExternalLink class="w-3.5 h-3.5" />
        查看原文
      </button>
      <button 
        class="action-btn"
        @click="handleCopy"
      >
        <Copy class="w-3.5 h-3.5" />
        复制引用
      </button>
    </div>
  </div>
</template>

<style scoped>
.citation-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.citation-card:hover {
  border-color: var(--any-border-hover);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.citation-card.compact {
  padding: 12px;
  gap: 8px;
}

/* Header */
.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.source-info {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.favicon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
  margin-top: 2px;
}

.source-text {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  min-width: 0;
}

.citation-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--exec-accent);
  flex-shrink: 0;
}

.source-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  line-height: 1.4;
  /* Text truncation for long titles */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.credibility-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--any-radius-full);
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

/* Meta */
.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--any-text-muted);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.type-badge {
  padding: 2px 6px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
}

/* Excerpt */
.card-excerpt {
  position: relative;
  padding: 12px 12px 12px 32px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-md);
  border-left: 3px solid var(--exec-accent);
}

.quote-icon {
  position: absolute;
  left: 10px;
  top: 12px;
  width: 14px;
  height: 14px;
  color: var(--exec-accent);
  opacity: 0.6;
}

.excerpt-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--any-text-secondary);
  font-style: italic;
}

/* Actions */
.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--any-text-secondary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.action-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.action-btn.primary {
  color: var(--any-bg-primary);
  background: var(--exec-accent);
  border-color: var(--exec-accent);
}

.action-btn.primary:hover {
  filter: brightness(1.1);
}

/* Compact adjustments */
.compact .source-title {
  font-size: 13px;
  -webkit-line-clamp: 1;
}

.compact .card-excerpt {
  padding: 8px 8px 8px 24px;
}

.compact .excerpt-text {
  font-size: 12px;
  -webkit-line-clamp: 2;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.compact .action-btn {
  padding: 4px 8px;
  font-size: 11px;
}
</style>
