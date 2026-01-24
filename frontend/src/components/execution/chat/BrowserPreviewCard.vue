<script setup lang="ts">
import { ref, computed } from 'vue'
import { Globe, ExternalLink, ChevronDown, ChevronUp, RefreshCw } from 'lucide-vue-next'

interface Props {
  /** 浏览器当前 URL */
  url: string
  /** Base64 编码的截图 */
  screenshot?: string
  /** 页面标题 */
  title?: string
  /** 时间戳 */
  timestamp?: number
  /** 操作类型: navigate, click, scroll, type, screenshot */
  action?: 'navigate' | 'click' | 'scroll' | 'type' | 'screenshot' | 'extract'
  /** 操作描述 */
  actionDescription?: string
  /** 是否正在加载 */
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  screenshot: '',
  title: '',
  timestamp: () => Date.now(),
  action: 'navigate',
  actionDescription: '',
  loading: false
})

const emit = defineEmits<{
  'open-url': [url: string]
  'refresh': []
}>()

// 展开/收起状态
const isExpanded = ref(true)

// 格式化 URL 显示
const displayUrl = computed(() => {
  if (!props.url) return '无活动页面'
  try {
    const url = new URL(props.url)
    const path = url.pathname.length > 30 
      ? url.pathname.slice(0, 30) + '...' 
      : url.pathname
    return url.hostname + path
  } catch {
    return props.url.slice(0, 50)
  }
})

// 格式化时间
const displayTime = computed(() => {
  const date = new Date(props.timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
})

// 操作图标和描述
const actionInfo = computed(() => {
  const map: Record<string, { icon: string; label: string }> = {
    navigate: { icon: '🌐', label: '导航到' },
    click: { icon: '👆', label: '点击' },
    scroll: { icon: '📜', label: '滚动' },
    type: { icon: '⌨️', label: '输入' },
    screenshot: { icon: '📸', label: '截图' },
    extract: { icon: '📋', label: '提取内容' }
  }
  return map[props.action] || map.navigate
})

function handleOpenUrl() {
  if (props.url) {
    emit('open-url', props.url)
  }
}

function toggleExpand() {
  isExpanded.value = !isExpanded.value
}
</script>

<template>
  <div :class="['browser-preview-card', { loading, expanded: isExpanded }]">
    <!-- Header -->
    <div class="card-header" @click="toggleExpand">
      <div class="header-left">
        <Globe class="header-icon" />
        <span class="action-label">{{ actionInfo.label }}</span>
        <span class="url-text">{{ displayUrl }}</span>
      </div>
      <div class="header-right">
        <span class="timestamp">{{ displayTime }}</span>
        <button 
          v-if="url"
          class="btn-icon"
          title="在新窗口打开"
          @click.stop="handleOpenUrl"
        >
          <ExternalLink class="w-3.5 h-3.5" />
        </button>
        <button class="btn-icon btn-expand" :title="isExpanded ? '收起' : '展开'">
          <ChevronUp v-if="isExpanded" class="w-3.5 h-3.5" />
          <ChevronDown v-else class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- Content (Screenshot) -->
    <Transition name="expand">
      <div v-if="isExpanded" class="card-content">
        <!-- Action Description -->
        <div v-if="actionDescription" class="action-description">
          {{ actionDescription }}
        </div>

        <!-- Screenshot Preview -->
        <div class="screenshot-container">
          <img 
            v-if="screenshot" 
            :src="screenshot" 
            :alt="title || 'Browser Screenshot'"
            class="screenshot-image"
          >
          <div v-else-if="loading" class="screenshot-placeholder loading">
            <RefreshCw class="placeholder-icon spin" />
            <span>正在加载页面...</span>
          </div>
          <div v-else class="screenshot-placeholder">
            <Globe class="placeholder-icon" />
            <span>等待截图...</span>
          </div>
        </div>

        <!-- Page Title -->
        <div v-if="title" class="page-title">
          {{ title }}
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.browser-preview-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  overflow: hidden;
  transition: all 200ms ease;
}

.browser-preview-card:hover {
  border-color: var(--any-border-hover);
}

.browser-preview-card.loading {
  border-color: var(--td-state-thinking, #00D9FF);
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--any-bg-tertiary);
  cursor: pointer;
  transition: background 150ms ease;
}

.card-header:hover {
  background: var(--any-bg-hover);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.header-icon {
  width: 16px;
  height: 16px;
  color: var(--td-state-thinking, #00D9FF);
  flex-shrink: 0;
}

.action-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--td-state-thinking, #00D9FF);
  flex-shrink: 0;
}

.url-text {
  font-size: 12px;
  color: var(--any-text-secondary);
  font-family: 'SF Mono', Monaco, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.timestamp {
  font-size: 11px;
  color: var(--any-text-muted);
}

.btn-icon {
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-icon:hover {
  background: var(--any-bg-primary);
  color: var(--any-text-secondary);
}

/* Content */
.card-content {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-description {
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.5;
  padding: 8px 10px;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  border-left: 3px solid var(--td-state-thinking, #00D9FF);
}

/* Screenshot */
.screenshot-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  overflow: hidden;
}

.screenshot-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 200ms ease;
}

.screenshot-image:hover {
  transform: scale(1.02);
}

.screenshot-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--any-text-muted);
  font-size: 12px;
}

.screenshot-placeholder.loading {
  color: var(--td-state-thinking, #00D9FF);
}

.placeholder-icon {
  width: 24px;
  height: 24px;
  opacity: 0.5;
}

.placeholder-icon.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Page Title */
.page-title {
  font-size: 12px;
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Expand Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 200ms ease;
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
  max-height: 400px;
}
</style>
