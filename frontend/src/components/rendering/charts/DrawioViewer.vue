<script setup lang="ts">
/**
 * DrawioViewer - draw.io 图表查看器
 * 
 * 使用 viewer.diagrams.net 嵌入式查看器渲染 draw.io XML 格式图表。
 * 支持：
 * - 流程图、架构图、时序图等
 * - 缩放和平移
 * - 点击查看大图 (lightbox)
 * - 导出为图片
 */

import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { 
  ArrowsPointingOutIcon, 
  ArrowDownTrayIcon,
  ArrowPathIcon,
} from '@heroicons/vue/24/outline'

// Props
interface Props {
  xml: string
  title?: string
  diagramType?: string
  height?: number | string
  showToolbar?: boolean
  allowZoom?: boolean
  lightbox?: boolean
  theme?: 'light' | 'dark' | 'auto'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  diagramType: 'flowchart',
  height: 400,
  showToolbar: true,
  allowZoom: true,
  lightbox: true,
  theme: 'auto',
})

// Emits
const emit = defineEmits<{
  (e: 'load'): void
  (e: 'error', error: string): void
  (e: 'export', format: string, data: string): void
}>()

// Refs
const containerRef = ref<HTMLElement | null>(null)
const iframeRef = ref<HTMLIFrameElement | null>(null)
const isLoading = ref(true)
const hasError = ref(false)
const errorMessage = ref('')

// Computed
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
}))

// 生成 viewer URL
const viewerUrl = computed(() => {
  // 使用 data-mxgraph 方式需要特殊处理
  // 这里使用 URL 方式加载
  const baseUrl = 'https://viewer.diagrams.net/'
  const params = new URLSearchParams({
    // 'highlight': '0000ff',
    'nav': '1',
    'title': props.title || 'Diagram',
    'dark': props.theme === 'dark' ? '1' : (props.theme === 'auto' ? 'auto' : '0'),
  })
  
  if (props.allowZoom) {
    params.set('toolbar', '1')
    params.set('toolbar-buttons', 'zoom')
  }
  
  if (props.lightbox) {
    params.set('lightbox', '1')
  }
  
  return `${baseUrl}?${params.toString()}`
})

// 将 XML 编码为 URL 安全格式
const encodeXml = (xml: string): string => {
  // draw.io 使用 deflate + base64 编码
  // 简化处理：直接 base64 编码
  try {
    return btoa(unescape(encodeURIComponent(xml)))
  } catch {
    return ''
  }
}

// 使用 postMessage 加载图表
const loadDiagram = async () => {
  if (!iframeRef.value || !props.xml) return
  
  isLoading.value = true
  hasError.value = false
  
  try {
    // 等待 iframe 加载
    await new Promise<void>((resolve, reject) => {
      const iframe = iframeRef.value!
      const timeout = setTimeout(() => reject(new Error('Iframe load timeout')), 10000)
      
      iframe.onload = () => {
        clearTimeout(timeout)
        resolve()
      }
      
      iframe.onerror = () => {
        clearTimeout(timeout)
        reject(new Error('Iframe load failed'))
      }
    })
    
    // 发送图表数据
    // viewer.diagrams.net 使用 hash 参数加载
    // 格式: #D{base64 encoded xml}
    const encoded = encodeXml(props.xml)
    if (iframeRef.value) {
      // 更新 iframe src 以包含数据
      const url = new URL(viewerUrl.value)
      url.hash = `D${encoded}`
      iframeRef.value.src = url.toString()
    }
    
    isLoading.value = false
    emit('load')
  } catch (error) {
    hasError.value = true
    errorMessage.value = error instanceof Error ? error.message : 'Failed to load diagram'
    isLoading.value = false
    emit('error', errorMessage.value)
  }
}

// 刷新图表
const refresh = () => {
  loadDiagram()
}

// 在新窗口打开
const openInNewWindow = () => {
  const encoded = encodeXml(props.xml)
  const url = `https://viewer.diagrams.net/?lightbox=1&nav=1#D${encoded}`
  window.open(url, '_blank')
}

// 导出为 PNG (通过 draw.io)
const exportPng = () => {
  const encoded = encodeXml(props.xml)
  const url = `https://viewer.diagrams.net/?format=png#D${encoded}`
  window.open(url, '_blank')
}

// 导出为 SVG
const exportSvg = () => {
  const encoded = encodeXml(props.xml)
  const url = `https://viewer.diagrams.net/?format=svg#D${encoded}`
  window.open(url, '_blank')
}

// 在 draw.io 中编辑
const editInDrawio = () => {
  const encoded = encodeXml(props.xml)
  const url = `https://app.diagrams.net/#D${encoded}`
  window.open(url, '_blank')
}

// Watch for XML changes
watch(() => props.xml, () => {
  if (props.xml) {
    nextTick(() => loadDiagram())
  }
}, { immediate: false })

// Mount
onMounted(() => {
  if (props.xml) {
    loadDiagram()
  }
})

// Expose methods
defineExpose({
  refresh,
  openInNewWindow,
  exportPng,
  exportSvg,
  editInDrawio,
})
</script>

<template>
  <div 
    ref="containerRef"
    class="drawio-viewer"
    :style="containerStyle"
  >
    <!-- Toolbar -->
    <div 
      v-if="showToolbar"
      class="viewer-toolbar"
    >
      <span 
        v-if="title"
        class="toolbar-title"
      >
        {{ title }}
      </span>
      
      <div class="toolbar-actions">
        <button
          class="toolbar-btn"
          title="刷新"
          @click="refresh"
        >
          <ArrowPathIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn"
          title="新窗口打开"
          @click="openInNewWindow"
        >
          <ArrowsPointingOutIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn"
          title="导出 PNG"
          @click="exportPng"
        >
          <ArrowDownTrayIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn toolbar-btn--primary"
          title="在 draw.io 中编辑"
          @click="editInDrawio"
        >
          编辑
        </button>
      </div>
    </div>
    
    <!-- Loading State -->
    <div 
      v-if="isLoading"
      class="viewer-loading"
    >
      <div class="loading-spinner" />
      <span>加载图表中...</span>
    </div>
    
    <!-- Error State -->
    <div 
      v-else-if="hasError"
      class="viewer-error"
    >
      <span>{{ errorMessage }}</span>
      <button 
        class="retry-btn"
        @click="refresh"
      >
        重试
      </button>
    </div>
    
    <!-- Iframe Viewer -->
    <iframe
      v-show="!isLoading && !hasError"
      ref="iframeRef"
      :src="viewerUrl"
      class="viewer-iframe"
      frameborder="0"
      allowfullscreen
    />
  </div>
</template>

<style scoped>
.drawio-viewer {
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary, #f5f5f5);
  border: 1px solid var(--any-border, #e5e5e5);
  border-radius: 8px;
  overflow: hidden;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--any-bg-primary, #ffffff);
  border-bottom: 1px solid var(--any-border, #e5e5e5);
}

.toolbar-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary, #333);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: var(--any-text-secondary, #666);
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: var(--any-bg-hover, #f0f0f0);
  color: var(--any-text-primary, #333);
}

.toolbar-btn--primary {
  background: var(--exec-accent, #00B8D9);
  color: white;
  font-size: 12px;
  padding: 6px 12px;
}

.toolbar-btn--primary:hover {
  background: var(--exec-accent-hover, #4f46e5);
  color: white;
}

.viewer-loading,
.viewer-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: var(--any-text-muted, #999);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--any-border, #e5e5e5);
  border-top-color: var(--exec-accent, #00B8D9);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.viewer-error {
  color: var(--any-text-error, #ef4444);
}

.retry-btn {
  padding: 6px 16px;
  background: var(--exec-accent, #00B8D9);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: var(--exec-accent-hover, #4f46e5);
}

.viewer-iframe {
  flex: 1;
  width: 100%;
  min-height: 300px;
  background: white;
}

/* Dark mode support */
:root.dark .drawio-viewer,
.dark .drawio-viewer {
  background: var(--any-bg-secondary, #1a1a1a);
  border-color: var(--any-border, #333);
}

:root.dark .viewer-toolbar,
.dark .viewer-toolbar {
  background: var(--any-bg-primary, #222);
  border-color: var(--any-border, #333);
}
</style>
