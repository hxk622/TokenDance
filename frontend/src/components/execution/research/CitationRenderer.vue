<script setup lang="ts">
/**
 * CitationRenderer - 引用渲染器
 * 
 * 功能：
 * - 解析 Markdown 文本中的 [1] [2] 等引用标记
 * - 将引用标记渲染为可点击的引用角标
 * - 点击角标展开引用详情卡片
 * - 支持悬停预览
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import type { Citation, ReportWithCitations } from './types'
import CitationCard from './CitationCard.vue'
import { sanitizeHtml } from '@/utils/sanitize'

interface Props {
  /** 报告内容 (带引用的 Markdown 或 HTML) */
  content: string
  /** 引用列表 */
  citations: Citation[]
  /** 是否为 HTML 内容 */
  isHtml?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isHtml: false,
})

const emit = defineEmits<{
  /** 打开外部链接 */
  openUrl: [url: string]
  /** 复制引用 */
  copyCitation: [citation: Citation]
}>()

// 当前展开的引用 ID
const expandedCitationId = ref<number | null>(null)
// 悬停预览的引用 ID
const hoveredCitationId = ref<number | null>(null)
// 引用角标元素位置缓存
const citationPositions = ref<Map<number, DOMRect>>(new Map())
// 容器 ref
const containerRef = ref<HTMLElement | null>(null)

// 获取引用数据
function getCitation(id: number): Citation | undefined {
  return props.citations.find(c => c.id === id)
}

// 处理角标点击
function handleCitationClick(citationId: number, event: Event) {
  event.preventDefault()
  event.stopPropagation()
  
  if (expandedCitationId.value === citationId) {
    expandedCitationId.value = null
  } else {
    expandedCitationId.value = citationId
    // 更新位置
    const target = event.target as HTMLElement
    if (target) {
      citationPositions.value.set(citationId, target.getBoundingClientRect())
    }
  }
}

// 处理角标悬停
function handleCitationHover(citationId: number, event: Event) {
  hoveredCitationId.value = citationId
  const target = event.target as HTMLElement
  if (target) {
    citationPositions.value.set(citationId, target.getBoundingClientRect())
  }
}

function handleCitationLeave() {
  hoveredCitationId.value = null
}

// 关闭卡片
function closeCard() {
  expandedCitationId.value = null
}

// 计算卡片位置
function getCardPosition(citationId: number): { top: string; left: string } {
  const rect = citationPositions.value.get(citationId)
  if (!rect || !containerRef.value) {
    return { top: '0', left: '0' }
  }
  
  const containerRect = containerRef.value.getBoundingClientRect()
  const top = rect.bottom - containerRect.top + 8
  let left = rect.left - containerRect.left
  
  // 确保卡片不超出容器右边界
  const cardWidth = 400
  if (left + cardWidth > containerRect.width) {
    left = containerRect.width - cardWidth - 16
  }
  if (left < 0) left = 8
  
  return {
    top: `${top}px`,
    left: `${left}px`,
  }
}

// 解析内容，将 [1] [2] 转换为可交互元素
const parsedContent = computed(() => {
  if (props.isHtml) {
    // 如果是 HTML，注入交互属性
    const output = props.content.replace(
      /\[(\d+)\]/g,
      (match, id) => {
        const citationId = parseInt(id)
        const citation = getCitation(citationId)
        if (!citation) return match
        return `<span class="citation-ref" data-citation-id="${citationId}" title="${citation.source.title}">${match}</span>`
      }
    )
    return sanitizeHtml(output)
  } else {
    // 纯文本/Markdown，需要先转义再处理
    const escaped = props.content
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    
    const output = escaped.replace(
      /\[(\d+)\]/g,
      (match, id) => {
        const citationId = parseInt(id)
        const citation = getCitation(citationId)
        if (!citation) return match
        return `<span class="citation-ref" data-citation-id="${citationId}" title="${citation.source.title}">${match}</span>`
      }
    )
    return sanitizeHtml(output)
  }
})

// 当前显示的引用
const activeCitation = computed(() => {
  const id = expandedCitationId.value ?? hoveredCitationId.value
  return id ? getCitation(id) : null
})

const activeCardPosition = computed(() => {
  const id = expandedCitationId.value ?? hoveredCitationId.value
  return id ? getCardPosition(id) : { top: '0', left: '0' }
})

// 绑定事件代理
function setupEventDelegation() {
  if (!containerRef.value) return
  
  containerRef.value.addEventListener('click', (e) => {
    const target = (e.target as HTMLElement).closest('.citation-ref')
    if (target) {
      const citationId = parseInt(target.getAttribute('data-citation-id') || '0')
      if (citationId) {
        handleCitationClick(citationId, e)
      }
    }
  })
  
  containerRef.value.addEventListener('mouseenter', (e) => {
    const target = (e.target as HTMLElement).closest('.citation-ref')
    if (target) {
      const citationId = parseInt(target.getAttribute('data-citation-id') || '0')
      if (citationId) {
        handleCitationHover(citationId, e)
      }
    }
  }, true)
  
  containerRef.value.addEventListener('mouseleave', (e) => {
    const target = (e.target as HTMLElement).closest('.citation-ref')
    if (target) {
      handleCitationLeave()
    }
  }, true)
}

// 点击外部关闭卡片
function handleClickOutside(e: MouseEvent) {
  if (expandedCitationId.value === null) return
  
  const target = e.target as HTMLElement
  if (!target.closest('.citation-card') && !target.closest('.citation-ref')) {
    closeCard()
  }
}

onMounted(() => {
  setupEventDelegation()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div 
    ref="containerRef"
    class="citation-renderer"
  >
    <!-- 渲染内容 -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div 
      class="content"
      v-html="parsedContent"
    />
    
    <!-- 引用卡片 (悬停预览或点击展开) -->
    <Transition name="citation-card">
      <div 
        v-if="activeCitation && (expandedCitationId || hoveredCitationId)"
        class="citation-card-wrapper"
        :class="{ expanded: expandedCitationId !== null }"
        :style="activeCardPosition"
      >
        <CitationCard
          :citation="activeCitation"
          :expanded="expandedCitationId !== null"
          :compact="hoveredCitationId !== null && expandedCitationId === null"
          @open-url="emit('openUrl', $event)"
          @copy="emit('copyCitation', $event)"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.citation-renderer {
  position: relative;
}

.content {
  line-height: 1.7;
}

/* 引用角标样式 */
.content :deep(.citation-ref) {
  display: inline;
  padding: 0 2px;
  font-size: 0.85em;
  font-weight: 600;
  color: var(--exec-accent);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
  border-radius: 2px;
}

.content :deep(.citation-ref:hover) {
  background: rgba(0, 217, 255, 0.15);
  text-decoration: underline;
}

/* 引用卡片容器 */
.citation-card-wrapper {
  position: absolute;
  z-index: 100;
  width: 400px;
  max-width: calc(100% - 32px);
}

.citation-card-wrapper.expanded {
  z-index: 101;
}

/* 卡片动画 */
.citation-card-enter-active,
.citation-card-leave-active {
  transition: all 0.2s var(--any-ease-out);
}

.citation-card-enter-from,
.citation-card-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
