<script setup lang="ts">
/**
 * AhaMomentPanel - Aha Moment 集成面板
 * 
 * 整合所有"哇"时刻功能:
 * - 行业分位数 + DuPont 分解
 * - 同行 PK 矩阵
 * - 事件时间轴
 * - 情绪脉冲图
 * - 风险传导图谱
 */
import { ref, computed, watch, onMounted } from 'vue'
import { 
  TrendingUp, 
  Users, 
  Calendar, 
  Activity, 
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Loader,
  RefreshCw,
} from 'lucide-vue-next'

// 导入子组件
import MetricWithPercentile from './MetricWithPercentile.vue'
import PeerComparisonMatrix from './PeerComparisonMatrix.vue'
import EventTimeline from './EventTimeline.vue'
import SentimentPulse from './SentimentPulse.vue'
import RiskPropagationGraph from './RiskPropagationGraph.vue'

// Types
interface AhaMomentData {
  benchmark?: {
    symbol: string
    benchmarks: Array<{
      metric_name: string
      metric_key: string
      current_value: number
      percentile: number
      percentile_50: number
      trend: string
    }>
    dupont?: {
      symbol: string
      roe: number
      net_profit_margin: { name: string; value: number; percentile: number }
      asset_turnover: { name: string; value: number; percentile: number }
      equity_multiplier: { name: string; value: number; percentile: number }
      primary_driver: string
      insights: string[]
    }
  }
  peerMatrix?: object
  events?: object
  sentimentPulse?: object
  riskPropagation?: object
}

// Props
const props = withDefaults(defineProps<{
  symbol: string | null
  stockName?: string
}>(), {
  stockName: '',
})

// State
const loading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'benchmark' | 'peer' | 'events' | 'sentiment' | 'risk'>('benchmark')
const expandedSections = ref<Set<string>>(new Set(['benchmark']))

// Data
const benchmarkData = ref<AhaMomentData['benchmark'] | null>(null)
const peerMatrixData = ref<object | null>(null)
const eventsData = ref<object | null>(null)
const sentimentPulseData = ref<object | null>(null)
const riskPropagationData = ref<object | null>(null)

// Tabs configuration
const tabs = [
  { key: 'benchmark', label: '行业分位', icon: TrendingUp },
  { key: 'peer', label: '同行对比', icon: Users },
  { key: 'events', label: '事件日历', icon: Calendar },
  { key: 'sentiment', label: '情绪脉冲', icon: Activity },
  { key: 'risk', label: '风险传导', icon: AlertTriangle },
] as const

// API calls
async function fetchBenchmarkData() {
  if (!props.symbol) return
  
  try {
    const response = await fetch('/api/v1/financial/benchmark/percentile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: props.symbol,
        metrics: ['roe', 'gross_margin', 'net_margin', 'revenue_growth', 'debt_ratio'],
        include_dupont: true,
      }),
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        benchmarkData.value = result.data
      }
    }
  } catch (e) {
    console.error('Failed to fetch benchmark data:', e)
  }
}

async function fetchPeerMatrix() {
  if (!props.symbol) return
  
  try {
    const response = await fetch('/api/v1/financial/peer/matrix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: props.symbol,
        peer_count: 4,
      }),
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        peerMatrixData.value = result.data
      }
    }
  } catch (e) {
    console.error('Failed to fetch peer matrix:', e)
  }
}

async function fetchEventsData() {
  if (!props.symbol) return
  
  try {
    const response = await fetch('/api/v1/financial/events/upcoming', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: props.symbol,
        days_ahead: 90,
      }),
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        eventsData.value = result.data
      }
    }
  } catch (e) {
    console.error('Failed to fetch events data:', e)
  }
}

async function fetchSentimentPulse() {
  if (!props.symbol) return
  
  try {
    const response = await fetch('/api/v1/financial/sentiment/pulse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: props.symbol,
        days: 7,
      }),
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        sentimentPulseData.value = result.data
      }
    }
  } catch (e) {
    console.error('Failed to fetch sentiment pulse:', e)
  }
}

async function fetchRiskPropagation() {
  if (!props.symbol) return
  
  try {
    const response = await fetch('/api/v1/financial/risk/propagation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: props.symbol,
      }),
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        riskPropagationData.value = result.data
      }
    }
  } catch (e) {
    console.error('Failed to fetch risk propagation:', e)
  }
}

// Main fetch function
async function fetchAllData() {
  if (!props.symbol) return
  
  loading.value = true
  error.value = null
  
  try {
    // Fetch data in parallel
    await Promise.all([
      fetchBenchmarkData(),
      fetchPeerMatrix(),
      fetchEventsData(),
      fetchSentimentPulse(),
      fetchRiskPropagation(),
    ])
  } catch (e) {
    error.value = 'Failed to load Aha Moment data'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// Refresh current tab data
async function refreshCurrentTab() {
  if (!props.symbol) return
  
  loading.value = true
  
  try {
    switch (activeTab.value) {
      case 'benchmark':
        await fetchBenchmarkData()
        break
      case 'peer':
        await fetchPeerMatrix()
        break
      case 'events':
        await fetchEventsData()
        break
      case 'sentiment':
        await fetchSentimentPulse()
        break
      case 'risk':
        await fetchRiskPropagation()
        break
    }
  } finally {
    loading.value = false
  }
}

// Toggle section
function toggleSection(key: string) {
  if (expandedSections.value.has(key)) {
    expandedSections.value.delete(key)
  } else {
    expandedSections.value.add(key)
  }
}

// Watch for symbol changes
watch(() => props.symbol, (newSymbol) => {
  if (newSymbol) {
    fetchAllData()
  }
}, { immediate: true })

// Get tab data
const currentTabData = computed(() => {
  switch (activeTab.value) {
    case 'benchmark':
      return benchmarkData.value
    case 'peer':
      return peerMatrixData.value
    case 'events':
      return eventsData.value
    case 'sentiment':
      return sentimentPulseData.value
    case 'risk':
      return riskPropagationData.value
    default:
      return null
  }
})
</script>

<template>
  <div class="aha-moment-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-title">
        <span class="title-icon">✨</span>
        <h3 class="title-text">
          Aha Moment
        </h3>
        <span
          v-if="stockName"
          class="stock-badge"
        >{{ stockName }}</span>
      </div>
      
      <button 
        class="refresh-btn"
        :disabled="loading || !symbol"
        @click="refreshCurrentTab"
      >
        <RefreshCw 
          class="w-4 h-4"
          :class="{ 'animate-spin': loading }"
        />
      </button>
    </div>

    <!-- Empty State -->
    <div
      v-if="!symbol"
      class="empty-state"
    >
      <p>请先选择一只股票</p>
    </div>

    <!-- Loading -->
    <div
      v-else-if="loading && !currentTabData"
      class="loading-state"
    >
      <Loader class="w-6 h-6 animate-spin" />
      <span>加载中...</span>
    </div>

    <!-- Content -->
    <div
      v-else
      class="panel-content"
    >
      <!-- Tab Bar -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ 'is-active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component
            :is="tab.icon"
            class="w-4 h-4"
          />
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Benchmark Tab -->
        <div
          v-if="activeTab === 'benchmark'"
          class="content-section"
        >
          <div
            v-if="benchmarkData && (benchmarkData as any)?.benchmarks?.length"
            class="benchmark-list"
          >
            <MetricWithPercentile
              v-for="(bm, idx) in (benchmarkData as any).benchmarks"
              :key="idx"
              :benchmark="bm"
              :dupont="idx === 0 ? (benchmarkData as any)?.dupont || null : null"
              :show-dupont="idx === 0 && (benchmarkData as any)?.dupont"
            />
          </div>
          <div
            v-else
            class="no-data"
          >
            暂无数据
          </div>
        </div>

        <!-- Peer Matrix Tab -->
        <div
          v-else-if="activeTab === 'peer'"
          class="content-section"
        >
          <PeerComparisonMatrix
            v-if="peerMatrixData"
            :matrix="peerMatrixData as any"
          />
          <div
            v-else
            class="no-data"
          >
            暂无数据
          </div>
        </div>

        <!-- Events Tab -->
        <div
          v-else-if="activeTab === 'events'"
          class="content-section"
        >
          <EventTimeline
            v-if="eventsData"
            :events="(eventsData as any)?.upcoming_events || []"
            :next-critical-event="(eventsData as any)?.next_critical_event || null"
          />
          <div
            v-else
            class="no-data"
          >
            暂无数据
          </div>
        </div>

        <!-- Sentiment Pulse Tab -->
        <div
          v-else-if="activeTab === 'sentiment'"
          class="content-section"
        >
          <SentimentPulse
            v-if="sentimentPulseData"
            :current-score="(sentimentPulseData as any)?.current_score || 0"
            :current-level="(sentimentPulseData as any)?.current_level || 'neutral'"
            :score-change24h="(sentimentPulseData as any)?.score_change_24h || 0"
            :confidence="(sentimentPulseData as any)?.confidence || 0"
            :daily-moods="(sentimentPulseData as any)?.daily_moods || []"
            :trending-topics="(sentimentPulseData as any)?.trending_topics || []"
            :top-bullish-opinions="(sentimentPulseData as any)?.top_bullish_opinions || []"
            :top-bearish-opinions="(sentimentPulseData as any)?.top_bearish_opinions || []"
            :heat-index="(sentimentPulseData as any)?.heat_index || 0"
            :source-distribution="(sentimentPulseData as any)?.source_distribution || {}"
          />
          <div
            v-else
            class="no-data"
          >
            暂无数据
          </div>
        </div>

        <!-- Risk Propagation Tab -->
        <div
          v-else-if="activeTab === 'risk'"
          class="content-section"
        >
          <RiskPropagationGraph
            v-if="riskPropagationData"
            :symbol="(riskPropagationData as any)?.symbol || symbol || ''"
            :name="(riskPropagationData as any)?.name || stockName"
            :total-risk-score="(riskPropagationData as any)?.total_risk_score || 0"
            :overall-risk-level="(riskPropagationData as any)?.overall_risk_level || 'low'"
            :high-risk-count="(riskPropagationData as any)?.high_risk_count || 0"
            :critical-risk-count="(riskPropagationData as any)?.critical_risk_count || 0"
            :self-risks="(riskPropagationData as any)?.self_risks || []"
            :incoming-risks="(riskPropagationData as any)?.incoming_risks || []"
            :outgoing-risks="(riskPropagationData as any)?.outgoing_risks || []"
            :risk-by-type="(riskPropagationData as any)?.risk_by_type || {}"
            :key-insights="(riskPropagationData as any)?.key_insights || []"
          />
          <div
            v-else
            class="no-data"
          >
            暂无数据
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.aha-moment-panel {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

/* Header */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.title-icon {
  font-size: 1.25rem;
}

.title-text {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.stock-badge {
  background: #f3f4f6;
  color: #6b7280;
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}

.refresh-btn:hover:not(:disabled) {
  background: #e5e7eb;
  color: #374151;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Empty & Loading States */
.empty-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #9ca3af;
  gap: 0.5rem;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0.25rem;
  padding: 0.75rem;
  background: #fafafa;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  border: none;
  background: transparent;
  border-radius: 6px;
  color: #6b7280;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.tab-item:hover {
  background: #e5e7eb;
  color: #374151;
}

.tab-item.is-active {
  background: #111827;
  color: #ffffff;
}

/* Tab Content */
.tab-content {
  padding: 1rem;
  min-height: 300px;
}

.content-section {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.no-data {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #9ca3af;
  font-size: 0.875rem;
}

.benchmark-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
