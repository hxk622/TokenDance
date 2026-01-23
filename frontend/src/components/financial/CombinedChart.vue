<template>
  <div class="combined-chart">
    <!-- Header -->
    <div class="chart-header">
      <h3 class="title">
        价格走势 + 舆情叠加
      </h3>
      
      <div class="chart-controls">
        <div class="time-range-selector">
          <button
            v-for="range in timeRanges"
            :key="range.value"
            class="range-button"
            :class="{ 'is-active': activeRange === range.value }"
            @click="activeRange = range.value"
          >
            {{ range.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>加载图表数据中...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="error-state"
    >
      <div class="error-icon">
        ⚠️
      </div>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!historicalData || historicalData.length === 0"
      class="empty-state"
    >
      <p>暂无图表数据</p>
      <p class="hint">
        选择股票后将显示价格走势
      </p>
    </div>

    <!-- Chart Container -->
    <div
      v-else
      class="chart-container"
    >
      <div
        ref="chartRef"
        class="chart-canvas"
      />
      
      <!-- Legend -->
      <div class="chart-legend">
        <div class="legend-item">
          <div
            class="legend-indicator"
            style="background: #10b981"
          />
          <span class="legend-label">看多情绪</span>
        </div>
        <div class="legend-item">
          <div
            class="legend-indicator"
            style="background: #ef4444"
          />
          <span class="legend-label">看空情绪</span>
        </div>
        <div class="legend-item">
          <div
            class="legend-indicator"
            style="background: #6b7280"
          />
          <span class="legend-label">中性情绪</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import type { HistoricalDataPoint } from '@/types/financial'

interface Props {
  historicalData: HistoricalDataPoint[]
  sentimentData?: Array<{ date: string; score: number; sentiment: string }>
  isLoading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  sentimentData: () => [],
  isLoading: false,
  error: null,
})

// Chart instance
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// Active time range
const activeRange = ref('1M')

// Time range options
const timeRanges = [
  { label: '1周', value: '1W' },
  { label: '1月', value: '1M' },
  { label: '3月', value: '3M' },
  { label: '6月', value: '6M' },
  { label: '1年', value: '1Y' },
]

// Initialize chart
function initChart() {
  if (!chartRef.value) return

  chartInstance = echarts.init(chartRef.value)
  updateChart()
  
  // Handle resize
  window.addEventListener('resize', handleResize)
}

// Handle window resize
function handleResize() {
  chartInstance?.resize()
}

// Update chart with data
function updateChart() {
  if (!chartInstance || !props.historicalData.length) return

  // Prepare candlestick data
  const dates = props.historicalData.map(d => d.date)
  const candlestickData = props.historicalData.map(d => [
    d.open,
    d.close,
    d.low,
    d.high,
  ])
  const volumes = props.historicalData.map(d => d.volume)

  // Prepare sentiment data (mock for now)
  const sentimentScores = props.historicalData.map(() => 
    Math.random() * 2 - 1 // Random score between -1 and 1
  )

  const option: EChartsOption = {
    animation: true,
    grid: [
      {
        left: '10%',
        right: '10%',
        top: '10%',
        height: '50%',
      },
      {
        left: '10%',
        right: '10%',
        top: '70%',
        height: '15%',
      },
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLine: { lineStyle: { color: '#e5e7eb' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
        },
        gridIndex: 0,
      },
      {
        type: 'category',
        data: dates,
        boundaryGap: true,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { show: false },
        gridIndex: 1,
      },
    ],
    yAxis: [
      {
        type: 'value',
        scale: true,
        splitLine: {
          lineStyle: { color: '#f3f4f6' },
        },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
        },
        gridIndex: 0,
      },
      {
        type: 'value',
        scale: true,
        splitLine: { show: false },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
        },
        gridIndex: 1,
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100,
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        start: 50,
        end: 100,
        height: 20,
        bottom: 10,
        borderColor: '#e5e7eb',
        fillerColor: 'rgba(107, 114, 128, 0.1)',
        handleStyle: {
          color: '#6b7280',
        },
        textStyle: {
          color: '#6b7280',
          fontSize: 11,
        },
      },
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candlestickData,
        itemStyle: {
          color: '#10b981',
          color0: '#ef4444',
          borderColor: '#10b981',
          borderColor0: '#ef4444',
        },
        xAxisIndex: 0,
        yAxisIndex: 0,
      },
      {
        name: '成交量',
        type: 'bar',
        data: volumes,
        itemStyle: {
          color: (params: any) => {
            const index = params.dataIndex
            const current = props.historicalData[index]
            return current.close >= current.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
          },
        },
        xAxisIndex: 1,
        yAxisIndex: 1,
      },
      {
        name: '舆情评分',
        type: 'line',
        data: sentimentScores,
        smooth: true,
        lineStyle: {
          color: '#00B8D9',
          width: 2,
        },
        itemStyle: {
          color: '#00B8D9',
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0.05)' },
          ]),
        },
        yAxisIndex: 0,
        z: 2,
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: {
          color: '#9ca3af',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e5e7eb',
      borderWidth: 1,
      textStyle: {
        color: '#374151',
        fontSize: 12,
      },
      formatter: (params: any) => {
        const date = params[0].axisValue
        let html = `<div style="padding: 4px 0; font-weight: 600;">${date}</div>`
        
        params.forEach((param: any) => {
          if (param.seriesName === 'K线') {
            const data = param.data
            html += `<div style="margin-top: 8px;">
              <div style="color: #6b7280; font-size: 11px;">开: ${data[0]} 收: ${data[1]}</div>
              <div style="color: #6b7280; font-size: 11px;">低: ${data[2]} 高: ${data[3]}</div>
            </div>`
          } else if (param.seriesName === '舆情评分') {
            const score = param.data.toFixed(2)
            const sentiment = score > 0.2 ? '看多' : score < -0.2 ? '看空' : '中性'
            html += `<div style="margin-top: 4px;">舆情: ${sentiment} (${score})</div>`
          }
        })
        
        return html
      },
    },
  }

  chartInstance.setOption(option)
}

// Lifecycle hooks
onMounted(() => {
  nextTick(() => {
    initChart()
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// Watch for data changes
watch(
  () => [props.historicalData, props.sentimentData],
  () => {
    if (chartInstance) {
      updateChart()
    }
  },
  { deep: true }
)

// Watch for range changes
watch(activeRange, () => {
  // Future: filter data based on selected range
  console.log('Time range changed:', activeRange.value)
})
</script>

<style scoped>
.combined-chart {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 1rem;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.time-range-selector {
  display: flex;
  gap: 0.25rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 0.25rem;
}

.range-button {
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 200ms ease;
}

.range-button:hover {
  color: #111827;
}

.range-button.is-active {
  background: #111827;
  color: #ffffff;
}

/* Loading/Error/Empty States */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
  min-height: 400px;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #f3f4f6;
  border-top-color: #111827;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.error-state p {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.error-icon,
.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state p {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.25rem 0;
}

.hint {
  font-size: 0.75rem;
  color: #9ca3af;
}

/* Chart Container */
.chart-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.chart-canvas {
  width: 100%;
  height: 500px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 2rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-indicator {
  width: 1rem;
  height: 1rem;
  border-radius: 4px;
}

.legend-label {
  font-size: 0.875rem;
  color: #6b7280;
}

/* Responsive */
@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-canvas {
    height: 350px;
  }

  .chart-legend {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
}
</style>
