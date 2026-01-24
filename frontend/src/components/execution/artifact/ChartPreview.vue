<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { 
  Download, Maximize2, RefreshCw, Settings,
  BarChart2, LineChart, PieChart, Activity
} from 'lucide-vue-next'
import * as echarts from 'echarts'
import type { EChartsOption, ECharts } from 'echarts'

interface Props {
  /** ECharts option configuration */
  option: EChartsOption
  /** Chart title */
  title?: string
  /** Chart type hint for toolbar */
  chartType?: 'bar' | 'line' | 'pie' | 'scatter' | 'mixed'
  /** Theme ('light' | 'dark') */
  theme?: 'light' | 'dark'
  /** Auto resize on container change */
  autoResize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  chartType: 'mixed',
  theme: 'dark',
  autoResize: true
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const emit = defineEmits<{
  (e: 'chart-ready', chart: any): void
  (e: 'click', params: unknown): void
}>()

// State
const chartRef = ref<HTMLDivElement | null>(null)
// Use any to avoid strict ECharts type compatibility issues
const chartInstance = ref<echarts.ECharts | null>(null)
const isFullscreen = ref(false)
const isLoading = ref(true)
const error = ref<string | null>(null)

// Chart type icons
const chartTypeIcons = {
  bar: BarChart2,
  line: LineChart,
  pie: PieChart,
  scatter: Activity,
  mixed: BarChart2
}

const ChartIcon = computed(() => chartTypeIcons[props.chartType] || BarChart2)

// Initialize chart
function initChart() {
  if (!chartRef.value) return
  
  try {
    // Dispose existing instance
    if (chartInstance.value) {
      chartInstance.value.dispose()
    }
    
    // Create new instance
    chartInstance.value = echarts.init(chartRef.value, props.theme)
    
    // Set option
    chartInstance.value.setOption(props.option)
    
    // Add click handler
    chartInstance.value.on('click', (params) => {
      emit('click', params)
    })
    
    emit('chart-ready', chartInstance.value)
    isLoading.value = false
    error.value = null
  } catch (e: any) {
    console.error('Chart init error:', e)
    error.value = e.message || '图表初始化失败'
    isLoading.value = false
  }
}

// Update chart
function updateChart() {
  if (!chartInstance.value) {
    initChart()
    return
  }
  
  try {
    chartInstance.value.setOption(props.option, true)
  } catch (e: any) {
    console.error('Chart update error:', e)
    error.value = e.message || '图表更新失败'
  }
}

// Resize chart
function resizeChart() {
  if (chartInstance.value) {
    chartInstance.value.resize()
  }
}

// Refresh chart
function refreshChart() {
  isLoading.value = true
  nextTick(() => {
    initChart()
  })
}

// Export as image
function exportImage() {
  if (!chartInstance.value) return
  
  try {
    const url = chartInstance.value.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: props.theme === 'dark' ? '#1a1a1a' : '#ffffff'
    })
    
    const link = document.createElement('a')
    link.download = `${props.title || 'chart'}.png`
    link.href = url
    link.click()
  } catch (e) {
    console.error('Export error:', e)
  }
}

// Toggle fullscreen
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => {
    resizeChart()
  })
}

// Watch option changes
watch(() => props.option, () => {
  updateChart()
}, { deep: true })

// Watch theme changes
watch(() => props.theme, () => {
  initChart()
})

// Resize observer
let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  nextTick(() => {
    initChart()
    
    // Setup resize observer
    if (props.autoResize && chartRef.value) {
      resizeObserver = new ResizeObserver(() => {
        resizeChart()
      })
      resizeObserver.observe(chartRef.value)
    }
  })
  
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  window.removeEventListener('resize', resizeChart)
})
</script>

<template>
  <div :class="['chart-preview', { fullscreen: isFullscreen }]">
    <!-- Toolbar -->
    <div class="chart-toolbar">
      <div class="chart-info">
        <component
          :is="ChartIcon"
          class="w-4 h-4"
        />
        <span
          v-if="title"
          class="chart-title"
        >{{ title }}</span>
      </div>
      
      <div class="chart-actions">
        <button 
          class="action-btn"
          title="刷新"
          @click="refreshChart"
        >
          <RefreshCw class="w-4 h-4" />
        </button>
        <button 
          class="action-btn"
          title="导出图片"
          @click="exportImage"
        >
          <Download class="w-4 h-4" />
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

    <!-- Chart Container -->
    <div class="chart-container">
      <!-- Loading -->
      <div
        v-if="isLoading"
        class="chart-loading"
      >
        <div class="loading-spinner" />
        <span>加载图表中...</span>
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="chart-error"
      >
        <Settings class="w-12 h-12" />
        <span>{{ error }}</span>
        <button
          class="retry-btn"
          @click="refreshChart"
        >
          重试
        </button>
      </div>

      <!-- Chart -->
      <div 
        ref="chartRef" 
        class="chart-canvas"
        :style="{ visibility: isLoading || error ? 'hidden' : 'visible' }"
      />
    </div>
  </div>
</template>

<style scoped>
.chart-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.chart-preview.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border-radius: 0;
}

/* Toolbar */
.chart-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.chart-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--any-text-secondary);
}

.chart-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.chart-actions {
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

/* Chart Container */
.chart-container {
  flex: 1;
  position: relative;
  padding: 16px;
  background: var(--any-bg-tertiary);
}

.chart-canvas {
  width: 100%;
  height: 100%;
}

/* Loading */
.chart-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: var(--any-bg-tertiary);
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

.chart-loading span {
  font-size: 13px;
  color: var(--any-text-secondary);
}

/* Error */
.chart-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
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
</style>
