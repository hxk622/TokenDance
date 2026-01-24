<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  ChevronLeft, ChevronRight, ZoomIn, ZoomOut, 
  Maximize2, Download, RotateCw, FileText
} from 'lucide-vue-next'

interface Props {
  /** PDF file URL or base64 data */
  src: string
  /** Initial page number */
  initialPage?: number
  /** Initial zoom level (1 = 100%) */
  initialZoom?: number
}

const props = withDefaults(defineProps<Props>(), {
  initialPage: 1,
  initialZoom: 1
})

const emit = defineEmits<{
  'page-change': [page: number, total: number]
  'zoom-change': [zoom: number]
}>()

// State
const containerRef = ref<HTMLDivElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const pdfDoc = ref<any>(null)
const currentPage = ref(props.initialPage)
const totalPages = ref(0)
const zoom = ref(props.initialZoom)
const rotation = ref(0)
const isLoading = ref(true)
const error = ref<string | null>(null)
const isFullscreen = ref(false)

// PDF.js library reference (lazy loaded)
let pdfjsLib: any = null

// Zoom levels
const zoomLevels = [0.5, 0.75, 1, 1.25, 1.5, 2, 3]
const minZoom = 0.25
const maxZoom = 4

// Computed
const zoomPercent = computed(() => Math.round(zoom.value * 100))

const canZoomIn = computed(() => zoom.value < maxZoom)
const canZoomOut = computed(() => zoom.value > minZoom)
const canGoNext = computed(() => currentPage.value < totalPages.value)
const canGoPrev = computed(() => currentPage.value > 1)

// Load PDF.js dynamically
async function loadPdfJs() {
  if (pdfjsLib) return pdfjsLib
  
  try {
    // Import PDF.js - will be loaded from node_modules if available, otherwise fallback
    // @ts-expect-error - pdfjs-dist may not have types installed
    const pdfjs = await import('pdfjs-dist')
    pdfjsLib = pdfjs
    
    // Set worker source from CDN
    const version = pdfjs.version || '3.11.174'
    const workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${version}/pdf.worker.min.js`
    pdfjs.GlobalWorkerOptions.workerSrc = workerSrc
    
    return pdfjs
  } catch (e) {
    console.error('Failed to load PDF.js:', e)
    throw new Error('PDF.js 加载失败')
  }
}

// Load PDF document
async function loadPdf() {
  if (!props.src) return
  
  isLoading.value = true
  error.value = null
  
  try {
    const pdfjs = await loadPdfJs()
    
    // Load the document
    const loadingTask = pdfjs.getDocument(props.src)
    pdfDoc.value = await loadingTask.promise
    totalPages.value = pdfDoc.value.numPages
    
    // Render first page
    await renderPage(currentPage.value)
    
    emit('page-change', currentPage.value, totalPages.value)
  } catch (e: any) {
    console.error('PDF load error:', e)
    error.value = e.message || 'PDF 加载失败'
  } finally {
    isLoading.value = false
  }
}

// Render a specific page
async function renderPage(pageNum: number) {
  if (!pdfDoc.value || !canvasRef.value) return
  
  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')
    
    if (!ctx) return
    
    // Calculate scale based on zoom and rotation
    const viewport = page.getViewport({ 
      scale: zoom.value * 2, // 2x for retina
      rotation: rotation.value 
    })
    
    canvas.width = viewport.width
    canvas.height = viewport.height
    canvas.style.width = `${viewport.width / 2}px`
    canvas.style.height = `${viewport.height / 2}px`
    
    // Render
    await page.render({
      canvasContext: ctx,
      viewport
    }).promise
    
  } catch (e) {
    console.error('Page render error:', e)
  }
}

// Navigation
function goToPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  renderPage(page)
  emit('page-change', page, totalPages.value)
}

function nextPage() {
  if (canGoNext.value) goToPage(currentPage.value + 1)
}

function prevPage() {
  if (canGoPrev.value) goToPage(currentPage.value - 1)
}

// Zoom controls
function setZoom(newZoom: number) {
  zoom.value = Math.max(minZoom, Math.min(maxZoom, newZoom))
  renderPage(currentPage.value)
  emit('zoom-change', zoom.value)
}

function zoomIn() {
  const currentIndex = zoomLevels.findIndex(z => z >= zoom.value)
  if (currentIndex < zoomLevels.length - 1) {
    setZoom(zoomLevels[currentIndex + 1])
  } else {
    setZoom(Math.min(zoom.value * 1.25, maxZoom))
  }
}

function zoomOut() {
  const currentIndex = zoomLevels.findIndex(z => z >= zoom.value)
  if (currentIndex > 0) {
    setZoom(zoomLevels[currentIndex - 1])
  } else {
    setZoom(Math.max(zoom.value / 1.25, minZoom))
  }
}

// Rotation
function rotate() {
  rotation.value = (rotation.value + 90) % 360
  renderPage(currentPage.value)
}

// Fullscreen
function toggleFullscreen() {
  if (!containerRef.value) return
  
  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen?.()
    isFullscreen.value = true
  } else {
    document.exitFullscreen?.()
    isFullscreen.value = false
  }
}

// Download
function downloadPdf() {
  if (!props.src) return
  
  const link = document.createElement('a')
  link.href = props.src
  link.download = 'document.pdf'
  link.click()
}

// Handle page input
function handlePageInput(event: Event) {
  const input = event.target as HTMLInputElement
  const page = parseInt(input.value, 10)
  if (!isNaN(page)) {
    goToPage(page)
  }
}

// Keyboard shortcuts
function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
    prevPage()
    event.preventDefault()
  } else if (event.key === 'ArrowRight' || event.key === 'PageDown') {
    nextPage()
    event.preventDefault()
  } else if (event.key === '+' || event.key === '=') {
    zoomIn()
    event.preventDefault()
  } else if (event.key === '-') {
    zoomOut()
    event.preventDefault()
  }
}

// Watch for src changes
watch(() => props.src, () => {
  loadPdf()
})

// Lifecycle
onMounted(() => {
  loadPdf()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div
    ref="containerRef"
    class="pdf-viewer"
  >
    <!-- Toolbar -->
    <div class="pdf-toolbar">
      <!-- Page Navigation -->
      <div class="page-nav">
        <button 
          class="nav-btn"
          :disabled="!canGoPrev"
          title="上一页"
          @click="prevPage"
        >
          <ChevronLeft class="w-4 h-4" />
        </button>
        
        <div class="page-info">
          <input 
            type="number" 
            class="page-input"
            :value="currentPage"
            :min="1"
            :max="totalPages"
            @change="handlePageInput"
          >
          <span class="page-total">/ {{ totalPages }}</span>
        </div>
        
        <button 
          class="nav-btn"
          :disabled="!canGoNext"
          title="下一页"
          @click="nextPage"
        >
          <ChevronRight class="w-4 h-4" />
        </button>
      </div>

      <!-- Zoom Controls -->
      <div class="zoom-controls">
        <button 
          class="nav-btn"
          :disabled="!canZoomOut"
          title="缩小"
          @click="zoomOut"
        >
          <ZoomOut class="w-4 h-4" />
        </button>
        
        <span class="zoom-level">{{ zoomPercent }}%</span>
        
        <button 
          class="nav-btn"
          :disabled="!canZoomIn"
          title="放大"
          @click="zoomIn"
        >
          <ZoomIn class="w-4 h-4" />
        </button>
      </div>

      <!-- Action Buttons -->
      <div class="actions">
        <button 
          class="nav-btn"
          title="旋转"
          @click="rotate"
        >
          <RotateCw class="w-4 h-4" />
        </button>
        <button 
          class="nav-btn"
          title="全屏"
          @click="toggleFullscreen"
        >
          <Maximize2 class="w-4 h-4" />
        </button>
        <button 
          class="nav-btn"
          title="下载"
          @click="downloadPdf"
        >
          <Download class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- PDF Content -->
    <div class="pdf-content">
      <!-- Loading State -->
      <div
        v-if="isLoading"
        class="pdf-loading"
      >
        <div class="loading-spinner" />
        <span>加载 PDF 中...</span>
      </div>

      <!-- Error State -->
      <div
        v-else-if="error"
        class="pdf-error"
      >
        <FileText class="w-12 h-12" />
        <span>{{ error }}</span>
        <button
          class="retry-btn"
          @click="loadPdf"
        >
          重试
        </button>
      </div>

      <!-- Canvas -->
      <div
        v-else
        class="canvas-wrapper"
      >
        <canvas
          ref="canvasRef"
          class="pdf-canvas"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

/* Toolbar */
.pdf-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.page-nav,
.zoom-controls,
.actions {
  display: flex;
  align-items: center;
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

/* Page Info */
.page-info {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
}

.page-input {
  width: 48px;
  padding: 4px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 13px;
  color: var(--any-text-primary);
  text-align: center;
}

.page-input:focus {
  outline: none;
  border-color: var(--td-state-thinking, #00D9FF);
}

.page-input::-webkit-inner-spin-button,
.page-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.page-total {
  font-size: 13px;
  color: var(--any-text-muted);
}

/* Zoom Level */
.zoom-level {
  min-width: 48px;
  font-size: 13px;
  color: var(--any-text-secondary);
  text-align: center;
}

/* PDF Content */
.pdf-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background: var(--any-bg-tertiary);
  overflow: auto;
}

/* Loading State */
.pdf-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--any-text-secondary);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--any-border);
  border-top-color: var(--td-state-thinking, #00D9FF);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.pdf-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--any-text-muted);
}

.retry-btn {
  padding: 8px 16px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 13px;
  color: var(--any-text-primary);
  cursor: pointer;
  transition: all 150ms ease;
}

.retry-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--td-state-thinking, #00D9FF);
}

/* Canvas Wrapper */
.canvas-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 100%;
  min-height: 100%;
}

.pdf-canvas {
  max-width: 100%;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  border-radius: var(--any-radius-sm);
}

/* Fullscreen */
.pdf-viewer:fullscreen {
  border-radius: 0;
}

.pdf-viewer:fullscreen .pdf-content {
  padding: 24px;
}
</style>
