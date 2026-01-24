<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { 
  Globe, RefreshCw, ArrowLeft, ArrowRight, 
  Monitor, Tablet, Smartphone, Maximize2, ExternalLink,
  Code2, Eye
} from 'lucide-vue-next'

interface Props {
  /** HTML content to render */
  htmlContent?: string
  /** URL to load in iframe (if external) */
  url?: string
  /** Initial viewport mode */
  viewportMode?: 'desktop' | 'tablet' | 'mobile'
}

const props = withDefaults(defineProps<Props>(), {
  htmlContent: '',
  url: '',
  viewportMode: 'desktop'
})

const emit = defineEmits<{
  'code-toggle': [showCode: boolean]
}>()

// Viewport configurations
const viewports = {
  desktop: { width: '100%', height: '100%', label: 'Desktop' },
  tablet: { width: '768px', height: '1024px', label: 'Tablet' },
  mobile: { width: '375px', height: '667px', label: 'Mobile' }
}

// State
const iframeRef = ref<HTMLIFrameElement | null>(null)
const currentViewport = ref<'desktop' | 'tablet' | 'mobile'>(props.viewportMode)
const currentUrl = ref(props.url || 'about:blank')
const isLoading = ref(false)
const showCode = ref(false)
const history = ref<string[]>([])
const historyIndex = ref(-1)
const isFullscreen = ref(false)
const currentBlobUrl = ref<string>('')

// Computed
const viewportStyle = computed(() => {
  const vp = viewports[currentViewport.value]
  if (currentViewport.value === 'desktop') {
    return { width: '100%', height: '100%' }
  }
  return { 
    width: vp.width, 
    height: vp.height,
    maxHeight: '100%'
  }
})

const canGoBack = computed(() => historyIndex.value > 0)
const canGoForward = computed(() => historyIndex.value < history.value.length - 1)

const displayUrl = computed(() => {
  if (props.htmlContent) return 'blob://preview'
  return currentUrl.value || 'about:blank'
})

// Generate blob URL from HTML content (managed to avoid memory leaks)
function createBlobUrl(htmlContent: string): string {
  // Revoke previous blob URL to prevent memory leak
  if (currentBlobUrl.value) {
    URL.revokeObjectURL(currentBlobUrl.value)
  }
  
  // Wrap content in full HTML if needed
  let html = htmlContent
  if (!html.includes('<html') && !html.includes('<!DOCTYPE')) {
    html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    * { box-sizing: border-box; }
    body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
  </style>
</head>
<body>
${html}
</body>
</html>`
  }
  
  const blob = new Blob([html], { type: 'text/html' })
  currentBlobUrl.value = URL.createObjectURL(blob)
  return currentBlobUrl.value
}

// Watch for content changes
watch(() => props.htmlContent, (newContent) => {
  if (newContent && iframeRef.value) {
    loadContent()
  }
})

watch(() => props.url, (newUrl) => {
  if (newUrl) {
    currentUrl.value = newUrl
    loadUrl(newUrl)
  }
})

// Methods
function loadContent() {
  if (!iframeRef.value || !props.htmlContent) return
  isLoading.value = true
  
  const url = createBlobUrl(props.htmlContent)
  iframeRef.value.src = url
}

function loadUrl(url: string) {
  if (!iframeRef.value) return
  isLoading.value = true
  
  // Add to history
  if (historyIndex.value < history.value.length - 1) {
    history.value = history.value.slice(0, historyIndex.value + 1)
  }
  history.value.push(url)
  historyIndex.value = history.value.length - 1
  
  iframeRef.value.src = url
}

function handleIframeLoad() {
  isLoading.value = false
}

function refresh() {
  if (!iframeRef.value) return
  isLoading.value = true
  const currentSrc = iframeRef.value.src
  iframeRef.value.src = 'about:blank'
  setTimeout(() => {
    if (iframeRef.value) {
      iframeRef.value.src = currentSrc
    }
  }, 0)
}

function goBack() {
  if (!canGoBack.value) return
  historyIndex.value--
  currentUrl.value = history.value[historyIndex.value]
  if (iframeRef.value) {
    iframeRef.value.src = currentUrl.value
  }
}

function goForward() {
  if (!canGoForward.value) return
  historyIndex.value++
  currentUrl.value = history.value[historyIndex.value]
  if (iframeRef.value) {
    iframeRef.value.src = currentUrl.value
  }
}

function setViewport(mode: 'desktop' | 'tablet' | 'mobile') {
  currentViewport.value = mode
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function toggleCodeView() {
  showCode.value = !showCode.value
  emit('code-toggle', showCode.value)
}

function copyCode() {
  if (props.htmlContent) {
    navigator.clipboard.writeText(props.htmlContent)
  }
}

function openExternal() {
  if (props.url) {
    window.open(props.url, '_blank')
  } else if (currentBlobUrl.value) {
    window.open(currentBlobUrl.value, '_blank')
  }
}

onMounted(() => {
  if (props.htmlContent) {
    loadContent()
  } else if (props.url) {
    loadUrl(props.url)
  }
})

onUnmounted(() => {
  // Clean up blob URL to prevent memory leak
  if (currentBlobUrl.value) {
    URL.revokeObjectURL(currentBlobUrl.value)
  }
})
</script>

<template>
  <div :class="['sandbox-browser', { fullscreen: isFullscreen }]">
    <!-- Browser Chrome -->
    <div class="browser-chrome">
      <!-- Navigation Controls -->
      <div class="nav-controls">
        <button 
          class="nav-btn" 
          :disabled="!canGoBack"
          title="后退"
          @click="goBack"
        >
          <ArrowLeft class="w-4 h-4" />
        </button>
        <button 
          class="nav-btn" 
          :disabled="!canGoForward"
          title="前进"
          @click="goForward"
        >
          <ArrowRight class="w-4 h-4" />
        </button>
        <button 
          class="nav-btn"
          :class="{ loading: isLoading }"
          title="刷新"
          @click="refresh"
        >
          <RefreshCw class="w-4 h-4" />
        </button>
      </div>

      <!-- URL Bar -->
      <div class="url-bar">
        <Globe class="url-icon" />
        <span class="url-text">{{ displayUrl }}</span>
      </div>

      <!-- Viewport Switcher -->
      <div class="viewport-switcher">
        <button 
          :class="['viewport-btn', { active: currentViewport === 'desktop' }]"
          title="Desktop (1280px)"
          @click="setViewport('desktop')"
        >
          <Monitor class="w-4 h-4" />
        </button>
        <button 
          :class="['viewport-btn', { active: currentViewport === 'tablet' }]"
          title="Tablet (768px)"
          @click="setViewport('tablet')"
        >
          <Tablet class="w-4 h-4" />
        </button>
        <button 
          :class="['viewport-btn', { active: currentViewport === 'mobile' }]"
          title="Mobile (375px)"
          @click="setViewport('mobile')"
        >
          <Smartphone class="w-4 h-4" />
        </button>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button 
          :class="['action-btn', { active: showCode }]"
          title="查看代码"
          @click="toggleCodeView"
        >
          <Code2
            v-if="!showCode"
            class="w-4 h-4"
          />
          <Eye
            v-else
            class="w-4 h-4"
          />
        </button>
        <button 
          class="action-btn"
          title="在新窗口打开"
          @click="openExternal"
        >
          <ExternalLink class="w-4 h-4" />
        </button>
        <button 
          class="action-btn"
          title="全屏"
          @click="toggleFullscreen"
        >
          <Maximize2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Preview Container -->
    <div class="preview-container">
      <div 
        class="iframe-wrapper"
        :class="currentViewport"
        :style="viewportStyle"
      >
        <!-- Loading Overlay -->
        <div
          v-if="isLoading"
          class="loading-overlay"
        >
          <RefreshCw class="loading-icon" />
          <span>加载中...</span>
        </div>

        <!-- Iframe -->
        <iframe
          ref="iframeRef"
          class="preview-iframe"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
          :src="currentBlobUrl || url || 'about:blank'"
          @load="handleIframeLoad"
        />

        <!-- Viewport Frame (for non-desktop modes) -->
        <div
          v-if="currentViewport !== 'desktop'"
          class="viewport-frame"
        >
          <div class="frame-notch" />
        </div>
      </div>
    </div>

    <!-- Code Panel (shown when code view is active) -->
    <Transition name="slide">
      <div
        v-if="showCode && htmlContent"
        class="code-panel"
      >
        <div class="code-header">
          <span>源代码</span>
          <button
            class="copy-btn"
            @click="copyCode"
          >
            复制
          </button>
        </div>
        <pre class="code-content"><code>{{ htmlContent }}</code></pre>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.sandbox-browser {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.sandbox-browser.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border-radius: 0;
}

/* Browser Chrome */
.browser-chrome {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.nav-controls {
  display: flex;
  gap: 4px;
}

.nav-btn {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.nav-btn:hover:not(:disabled) {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.nav-btn.loading svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* URL Bar */
.url-bar {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
}

.url-icon {
  width: 14px;
  height: 14px;
  color: var(--any-text-muted);
  flex-shrink: 0;
}

.url-text {
  font-size: 12px;
  font-family: 'SF Mono', Monaco, monospace;
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Viewport Switcher */
.viewport-switcher {
  display: flex;
  gap: 2px;
  padding: 2px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-md);
}

.viewport-btn {
  padding: 6px 8px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.viewport-btn:hover {
  color: var(--any-text-secondary);
}

.viewport-btn.active {
  background: var(--any-bg-primary);
  color: var(--td-state-thinking, #00D9FF);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.action-btn.active {
  background: var(--td-state-thinking-bg);
  color: var(--td-state-thinking);
}

/* Preview Container */
.preview-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: var(--any-bg-tertiary);
  overflow: auto;
}

.iframe-wrapper {
  position: relative;
  background: white;
  border-radius: var(--any-radius-md);
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
  transition: all 300ms ease;
}

.iframe-wrapper.desktop {
  width: 100%;
  height: 100%;
  border-radius: 0;
  box-shadow: none;
}

.iframe-wrapper.tablet,
.iframe-wrapper.mobile {
  border: 8px solid #1c1c1e;
  border-radius: 24px;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}

/* Loading Overlay */
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}

.loading-icon {
  width: 24px;
  height: 24px;
  color: var(--td-state-thinking, #00D9FF);
  animation: spin 1s linear infinite;
}

.loading-overlay span {
  font-size: 13px;
  color: var(--any-text-secondary);
}

/* Viewport Frame */
.viewport-frame {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  pointer-events: none;
}

.frame-notch {
  width: 120px;
  height: 24px;
  background: #1c1c1e;
  border-radius: 0 0 12px 12px;
}

/* Code Panel */
.code-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40%;
  background: var(--any-bg-secondary);
  border-top: 1px solid var(--any-border);
  display: flex;
  flex-direction: column;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  border-bottom: 1px solid var(--any-border);
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.copy-btn {
  padding: 4px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.copy-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.code-content {
  flex: 1;
  margin: 0;
  padding: 16px;
  overflow: auto;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 200ms ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
