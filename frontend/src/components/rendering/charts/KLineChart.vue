<script setup lang="ts">
/**
 * 专业级 K 线图表组件
 * Professional K-Line Chart Component
 * 
 * 基于 KLineChart 库 (3.5k stars)
 * - 零依赖，40kb gzip
 * - 移动端支持
 * - 丰富的技术指标
 */

import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import { init, dispose } from 'klinecharts'
import type { KLineDataItem, KLineChartPeriod, KLineIndicatorConfig } from '../types'

// KLineChart instance type (using any for flexibility with API changes)
type ChartInstance = ReturnType<typeof init>

// KLineData type for internal use
interface KLineData {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover?: number
}

// Props
interface Props {
  data: KLineDataItem[]
  symbol?: string
  period?: KLineChartPeriod
  indicators?: KLineIndicatorConfig[]
  theme?: 'light' | 'dark'
  height?: number | string
  showVolume?: boolean
  showGrid?: boolean
  showCrosshair?: boolean
  showTooltip?: boolean
  locale?: 'zh-CN' | 'en-US'
}

const props = withDefaults(defineProps<Props>(), {
  symbol: '',
  period: '1d',
  indicators: () => [],
  theme: 'light',
  height: 500,
  showVolume: true,
  showGrid: true,
  showCrosshair: true,
  showTooltip: true,
  locale: 'zh-CN',
})

// Emits
const emit = defineEmits<{
  (e: 'crosshairChange', data: { timestamp: number; kLineData: KLineData | null }): void
  (e: 'visibleRangeChange', data: { from: number; to: number }): void
  (e: 'click', data: { timestamp: number; kLineData: KLineData | null }): void
}>()

// Refs
const chartContainerRef = ref<HTMLElement | null>(null)
let chartInstance: ChartInstance | null = null

// Active indicator (for toggling)
const activeIndicators = ref<Set<string>>(new Set(['MA', 'VOL']))

// Period labels
const periodLabels: Record<KLineChartPeriod, string> = {
  '1m': '1分',
  '5m': '5分',
  '15m': '15分',
  '30m': '30分',
  '1h': '1时',
  '4h': '4时',
  '1d': '日K',
  '1w': '周K',
  '1M': '月K',
}

// Available indicators
const availableIndicators = [
  { name: 'MA', label: '均线', category: 'main' },
  { name: 'EMA', label: 'EMA', category: 'main' },
  { name: 'BOLL', label: '布林带', category: 'main' },
  { name: 'SAR', label: 'SAR', category: 'main' },
  { name: 'VOL', label: '成交量', category: 'sub' },
  { name: 'MACD', label: 'MACD', category: 'sub' },
  { name: 'KDJ', label: 'KDJ', category: 'sub' },
  { name: 'RSI', label: 'RSI', category: 'sub' },
]

// Computed styles
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
}))

// Convert data format
function convertData(data: KLineDataItem[]): KLineData[] {
  return data.map(item => ({
    timestamp: item.timestamp,
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume,
    turnover: item.turnover,
  }))
}

// Get theme styles
function getThemeStyles() {
  const isDark = props.theme === 'dark'
  
  return {
    grid: {
      show: props.showGrid,
      horizontal: {
        show: true,
        size: 1,
        color: isDark ? '#2d2d2d' : '#f0f0f0',
        style: 'dashed' as const,
      },
      vertical: {
        show: true,
        size: 1,
        color: isDark ? '#2d2d2d' : '#f0f0f0',
        style: 'dashed' as const,
      },
    },
    candle: {
      type: 'candle_solid' as const,
      bar: {
        upColor: '#10b981',
        downColor: '#ef4444',
        noChangeColor: '#888888',
        upBorderColor: '#10b981',
        downBorderColor: '#ef4444',
        noChangeBorderColor: '#888888',
        upWickColor: '#10b981',
        downWickColor: '#ef4444',
        noChangeWickColor: '#888888',
      },
      tooltip: {
        showRule: props.showTooltip ? 'always' : 'none' as 'always' | 'none',
        showType: 'standard' as const,
        labels: ['时间: ', '开: ', '收: ', '高: ', '低: ', '成交量: '],
        values: null,
        defaultValue: 'n/a',
        rect: {
          paddingLeft: 8,
          paddingRight: 8,
          paddingTop: 8,
          paddingBottom: 8,
          offsetLeft: 12,
          offsetTop: 12,
          offsetRight: 12,
          borderRadius: 4,
          borderSize: 1,
          borderColor: isDark ? '#3d3d3d' : '#e0e0e0',
          color: isDark ? '#1a1a1a' : '#ffffff',
        },
        text: {
          size: 12,
          family: 'system-ui, -apple-system, sans-serif',
          weight: 'normal',
          color: isDark ? '#d0d0d0' : '#333333',
          marginLeft: 8,
          marginTop: 6,
          marginRight: 8,
          marginBottom: 6,
        },
      },
    },
    indicator: {
      lastValueMark: {
        show: true,
        text: {
          show: true,
          color: '#ffffff',
          size: 12,
          family: 'system-ui',
          weight: 'normal',
          paddingLeft: 4,
          paddingTop: 4,
          paddingRight: 4,
          paddingBottom: 4,
          borderRadius: 2,
        },
      },
      tooltip: {
        showRule: 'always' as const,
        showType: 'standard' as const,
        showName: true,
        showParams: true,
        defaultValue: 'n/a',
        text: {
          size: 12,
          family: 'system-ui',
          weight: 'normal',
          color: isDark ? '#d0d0d0' : '#333333',
          marginTop: 6,
          marginRight: 8,
          marginBottom: 0,
          marginLeft: 8,
        },
      },
    },
    crosshair: {
      show: props.showCrosshair,
      horizontal: {
        show: true,
        line: {
          show: true,
          style: 'dashed' as const,
          size: 1,
          color: isDark ? '#555555' : '#888888',
        },
        text: {
          show: true,
          color: '#ffffff',
          size: 12,
          family: 'system-ui',
          weight: 'normal',
          paddingLeft: 4,
          paddingRight: 4,
          paddingTop: 2,
          paddingBottom: 2,
          borderSize: 1,
          borderColor: isDark ? '#3d3d3d' : '#e0e0e0',
          borderRadius: 2,
          backgroundColor: isDark ? '#333333' : '#555555',
        },
      },
      vertical: {
        show: true,
        line: {
          show: true,
          style: 'dashed' as const,
          size: 1,
          color: isDark ? '#555555' : '#888888',
        },
        text: {
          show: true,
          color: '#ffffff',
          size: 12,
          family: 'system-ui',
          weight: 'normal',
          paddingLeft: 4,
          paddingRight: 4,
          paddingTop: 2,
          paddingBottom: 2,
          borderSize: 1,
          borderColor: isDark ? '#3d3d3d' : '#e0e0e0',
          borderRadius: 2,
          backgroundColor: isDark ? '#333333' : '#555555',
        },
      },
    },
    xAxis: {
      show: true,
      size: 'auto' as const,
      axisLine: {
        show: true,
        color: isDark ? '#3d3d3d' : '#e0e0e0',
        size: 1,
      },
      tickText: {
        show: true,
        color: isDark ? '#888888' : '#666666',
        size: 11,
        family: 'system-ui',
        weight: 'normal',
        marginStart: 4,
        marginEnd: 4,
      },
      tickLine: {
        show: true,
        size: 1,
        length: 3,
        color: isDark ? '#3d3d3d' : '#e0e0e0',
      },
    },
    yAxis: {
      show: true,
      size: 'auto' as const,
      position: 'right' as const,
      type: 'normal' as const,
      inside: false,
      reverse: false,
      axisLine: {
        show: true,
        color: isDark ? '#3d3d3d' : '#e0e0e0',
        size: 1,
      },
      tickText: {
        show: true,
        color: isDark ? '#888888' : '#666666',
        size: 11,
        family: 'system-ui',
        weight: 'normal',
        marginStart: 4,
        marginEnd: 4,
      },
      tickLine: {
        show: true,
        size: 1,
        length: 3,
        color: isDark ? '#3d3d3d' : '#e0e0e0',
      },
    },
  }
}

// Initialize chart
function initChart() {
  if (!chartContainerRef.value) return

  // Dispose existing chart
  if (chartInstance) {
    dispose(chartContainerRef.value)
    chartInstance = null
  }

  // Create new chart
  chartInstance = init(chartContainerRef.value, {
    locale: props.locale,
    styles: getThemeStyles(),
  })

  if (!chartInstance) return

  // Set data
  const chartData = convertData(props.data)
  ;(chartInstance as any).applyNewData(chartData)

  // Add default indicators
  if (props.showVolume) {
    ;(chartInstance as any).createIndicator('VOL', false, { id: 'candle_pane' })
  }
  
  // Add MA indicator by default
  ;(chartInstance as any).createIndicator('MA', false, { id: 'candle_pane' })

  // Register event handlers
  ;(chartInstance as any).subscribeAction('onCrosshairChange', (data: any) => {
    if (data.kLineData) {
      emit('crosshairChange', {
        timestamp: data.kLineData.timestamp,
        kLineData: data.kLineData,
      })
    }
  })

  ;(chartInstance as any).subscribeAction('onVisibleRangeChange', (data: any) => {
    emit('visibleRangeChange', { from: data.from, to: data.to })
  })
}

// Toggle indicator
function toggleIndicator(name: string) {
  if (!chartInstance) return

  if (activeIndicators.value.has(name)) {
    // Remove indicator
    ;(chartInstance as any).removeIndicator('candle_pane', name)
    activeIndicators.value.delete(name)
  } else {
    // Add indicator
    const indicator = availableIndicators.find(i => i.name === name)
    if (indicator) {
      const paneId = indicator.category === 'main' ? 'candle_pane' : undefined
      ;(chartInstance as any).createIndicator(name, false, paneId ? { id: paneId } : undefined)
      activeIndicators.value.add(name)
    }
  }
}

// Update chart styles
function updateStyles() {
  if (!chartInstance) return
  ;(chartInstance as any).setStyles(getThemeStyles())
}

// Update chart data
function updateData() {
  if (!chartInstance || !props.data.length) return
  const chartData = convertData(props.data)
  ;(chartInstance as any).applyNewData(chartData)
}

// Lifecycle
onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

onUnmounted(() => {
  if (chartContainerRef.value) {
    dispose(chartContainerRef.value)
  }
})

// Watchers
watch(() => props.data, updateData, { deep: true })
watch(() => props.theme, updateStyles)
watch(() => [props.showGrid, props.showCrosshair, props.showTooltip], updateStyles)

// Expose methods
defineExpose({
  getChart: () => chartInstance,
  toggleIndicator,
  refresh: initChart,
})
</script>

<template>
  <div class="kline-chart-wrapper" :class="[`theme-${theme}`]">
    <!-- Header -->
    <div class="chart-header">
      <div class="chart-info">
        <span v-if="symbol" class="symbol">{{ symbol }}</span>
        <span class="period">{{ periodLabels[period] }}</span>
      </div>
      
      <!-- Indicator Buttons -->
      <div class="indicator-buttons">
        <button
          v-for="indicator in availableIndicators"
          :key="indicator.name"
          class="indicator-btn"
          :class="{ active: activeIndicators.has(indicator.name) }"
          @click="toggleIndicator(indicator.name)"
        >
          {{ indicator.label }}
        </button>
      </div>
    </div>

    <!-- Chart Container -->
    <div 
      ref="chartContainerRef" 
      class="chart-container"
      :style="containerStyle"
    />

    <!-- Loading Overlay -->
    <div v-if="!data.length" class="empty-state">
      <div class="empty-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 3v18h18"/>
          <path d="m19 9-5 5-4-4-3 3"/>
        </svg>
      </div>
      <p class="empty-text">暂无K线数据</p>
      <p class="empty-hint">选择股票后将显示K线走势</p>
    </div>
  </div>
</template>

<style scoped>
.kline-chart-wrapper {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.theme-dark.kline-chart-wrapper {
  background: #1a1a1a;
  border-color: #2d2d2d;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 12px;
}

.theme-dark .chart-header {
  border-bottom-color: #2d2d2d;
}

.chart-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.symbol {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.theme-dark .symbol {
  color: #ffffff;
}

.period {
  font-size: 0.875rem;
  color: #6b7280;
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
}

.theme-dark .period {
  background: #2d2d2d;
  color: #a0a0a0;
}

.indicator-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.indicator-btn {
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 150ms ease;
}

.indicator-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.indicator-btn.active {
  background: #111827;
  border-color: #111827;
  color: #ffffff;
}

.theme-dark .indicator-btn {
  background: #2d2d2d;
  border-color: #3d3d3d;
  color: #a0a0a0;
}

.theme-dark .indicator-btn:hover {
  background: #3d3d3d;
  color: #d0d0d0;
}

.theme-dark .indicator-btn.active {
  background: #4f46e5;
  border-color: #4f46e5;
  color: #ffffff;
}

.chart-container {
  width: 100%;
  min-height: 400px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: #9ca3af;
}

.theme-dark .empty-state {
  color: #6b7280;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-text {
  font-size: 1rem;
  margin: 0 0 4px;
}

.empty-hint {
  font-size: 0.875rem;
  margin: 0;
  opacity: 0.7;
}

/* Responsive */
@media (max-width: 640px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .indicator-buttons {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
