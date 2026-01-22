<template>
  <div class="peer-matrix-card">
    <!-- Header -->
    <div class="card-header">
      <div class="header-left">
        <h3 class="card-title">
          <GitCompare
            class="title-icon"
            :size="18"
          />
          同行对比
        </h3>
        <span
          v-if="matrix"
          class="industry-tag"
        >{{ matrix.industry }}</span>
      </div>
      <button
        class="customize-btn"
        @click="$emit('customize')"
      >
        <Settings2 :size="14" />
        自定义对比
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="loading-spinner" />
      <p>正在加载同行数据...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="error-state"
    >
      <AlertCircle :size="20" />
      <p>{{ error }}</p>
    </div>

    <!-- Matrix Content -->
    <div
      v-else-if="matrix"
      class="matrix-content"
    >
      <!-- Comparison Table -->
      <div class="table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th class="metric-col">
                指标
              </th>
              <th
                v-for="peer in matrix.peers"
                :key="peer.symbol"
                class="peer-col"
                :class="{ 'target': peer.symbol === matrix.target_symbol }"
              >
                <div class="peer-header">
                  <span class="peer-name">{{ peer.name }}</span>
                  <span class="peer-symbol">{{ peer.symbol }}</span>
                </div>
              </th>
              <th class="industry-col">
                行业均值
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="metric in matrix.metrics"
              :key="metric.metric_key"
              class="metric-row"
              @click="handleMetricClick(metric)"
            >
              <td class="metric-name">
                {{ metric.metric_name }}
              </td>
              <td
                v-for="peer in matrix.peers"
                :key="peer.symbol"
                class="metric-value"
                :class="{
                  'winner': metric.winner === peer.symbol,
                  'target': peer.symbol === matrix.target_symbol
                }"
              >
                {{ formatMetricValue(metric, peer.symbol) }}
                <Trophy
                  v-if="metric.winner === peer.symbol"
                  class="trophy-icon"
                  :size="14"
                />
              </td>
              <td class="industry-value">
                {{ formatIndustryMean(metric) }}
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr class="score-row">
              <td class="score-label">
                综合评分
              </td>
              <td
                v-for="peer in matrix.peers"
                :key="peer.symbol"
                class="score-cell"
                :class="{ 'target': peer.symbol === matrix.target_symbol }"
              >
                <div class="score-display">
                  <StarRating :score="matrix.scores[peer.symbol] || 0" />
                  <span class="score-value">{{ (matrix.scores[peer.symbol] || 0).toFixed(0) }}分</span>
                </div>
              </td>
              <td />
            </tr>
          </tfoot>
        </table>
      </div>

      <!-- Insights -->
      <div
        v-if="matrix.insights.length > 0"
        class="insights-section"
      >
        <h4 class="section-title">
          <Lightbulb :size="14" />
          分析洞察
        </h4>
        <ul class="insights-list">
          <li
            v-for="(insight, idx) in matrix.insights"
            :key="idx"
          >
            {{ insight }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="empty-state"
    >
      <p>暂无同行对比数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { GitCompare, Settings2, AlertCircle, Trophy, Lightbulb } from 'lucide-vue-next'
import StarRating from './StarRating.vue'

// Types
interface PeerInfo {
  symbol: string
  name: string
  market_cap: number
}

interface PeerMetricComparison {
  metric_name: string
  metric_key: string
  metric_type: 'higher_better' | 'lower_better'
  values: Record<string, number | null>
  winner: string | null
  industry_mean: number | null
}

interface PeerComparisonMatrix {
  target_symbol: string
  target_name: string
  industry: string
  peers: PeerInfo[]
  metrics: PeerMetricComparison[]
  scores: Record<string, number>
  insights: string[]
}

// Props
defineProps<{
  matrix: PeerComparisonMatrix | null
  isLoading?: boolean
  error?: string | null
}>()

// Emits
defineEmits<{
  customize: []
  metricClick: [metric: PeerMetricComparison]
}>()

// Methods
function formatMetricValue(metric: PeerMetricComparison, symbol: string): string {
  const value = metric.values[symbol]
  if (value === null || value === undefined) return '-'

  // 百分比类指标
  const percentMetrics = ['roe', 'net_margin', 'gross_margin', 'revenue_growth', 'profit_growth', 'debt_ratio']
  if (percentMetrics.includes(metric.metric_key)) {
    return `${value.toFixed(1)}%`
  }

  // 倍数类指标
  if (metric.metric_key === 'pe_ttm' || metric.metric_key === 'pb') {
    return `${value.toFixed(1)}x`
  }

  return value.toFixed(2)
}

function formatIndustryMean(metric: PeerMetricComparison): string {
  if (metric.industry_mean === null) return '-'

  const percentMetrics = ['roe', 'net_margin', 'gross_margin', 'revenue_growth', 'profit_growth', 'debt_ratio']
  if (percentMetrics.includes(metric.metric_key)) {
    return `${metric.industry_mean.toFixed(1)}%`
  }

  if (metric.metric_key === 'pe_ttm' || metric.metric_key === 'pb') {
    return `${metric.industry_mean.toFixed(1)}x`
  }

  return metric.industry_mean.toFixed(2)
}

function handleMetricClick(metric: PeerMetricComparison) {
  // 可用于展开详细对比图表
  console.log('Metric clicked:', metric.metric_key)
}
</script>

<style scoped>
.peer-matrix-card {
  background: var(--any-bg-secondary, rgba(28, 28, 30, 0.9));
  border: 1px solid var(--any-border, rgba(255, 255, 255, 0.08));
  border-radius: 16px;
  padding: 1.25rem;
  backdrop-filter: blur(12px);
}

/* Header */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 700;
  color: var(--any-text-primary, #ffffff);
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
}

.title-icon {
  color: #00D9FF;
}

.industry-tag {
  padding: 0.25rem 0.5rem;
  background: rgba(0, 217, 255, 0.15);
  color: #00D9FF;
  font-size: 0.75rem;
  border-radius: 4px;
}

.customize-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: 1px solid var(--any-border, rgba(255, 255, 255, 0.15));
  border-radius: 8px;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.customize-btn:hover {
  background: var(--any-bg-hover, rgba(255, 255, 255, 0.05));
  border-color: var(--any-border-hover, rgba(255, 255, 255, 0.25));
  color: var(--any-text-primary, #ffffff);
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.5));
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 0.75rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1.5rem;
  color: #FF6B6B;
}

/* Table */
.table-wrapper {
  overflow-x: auto;
  margin: 0 -0.5rem;
  padding: 0 0.5rem;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}

.comparison-table th,
.comparison-table td {
  padding: 0.75rem 0.5rem;
  text-align: right;
  border-bottom: 1px solid var(--any-border, rgba(255, 255, 255, 0.06));
}

.comparison-table th {
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.5));
  font-weight: 500;
  white-space: nowrap;
}

.metric-col {
  text-align: left !important;
  width: 80px;
}

.peer-col {
  min-width: 90px;
}

.peer-col.target {
  background: rgba(0, 217, 255, 0.05);
}

.industry-col {
  color: var(--any-text-muted, rgba(255, 255, 255, 0.4)) !important;
  min-width: 80px;
}

/* Peer Header */
.peer-header {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.125rem;
}

.peer-name {
  font-weight: 600;
  color: var(--any-text-primary, #ffffff);
}

.peer-symbol {
  font-size: 0.6875rem;
  color: var(--any-text-muted, rgba(255, 255, 255, 0.4));
}

/* Metric Row */
.metric-row {
  cursor: pointer;
  transition: background 0.15s ease;
}

.metric-row:hover {
  background: var(--any-bg-hover, rgba(255, 255, 255, 0.03));
}

.metric-name {
  text-align: left !important;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
}

.metric-value {
  position: relative;
  color: var(--any-text-primary, #ffffff);
  font-family: 'Space Grotesk', monospace;
}

.metric-value.target {
  background: rgba(0, 217, 255, 0.05);
}

.metric-value.winner {
  color: #00FF88;
  font-weight: 600;
}

.trophy-icon {
  position: absolute;
  top: 50%;
  right: 4px;
  transform: translateY(-50%);
  color: #FFD700;
}

.industry-value {
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.5));
  font-family: 'Space Grotesk', monospace;
}

/* Score Row */
.score-row td {
  border-bottom: none;
  padding-top: 1rem;
}

.score-label {
  text-align: left !important;
  font-weight: 600;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
}

.score-cell {
  vertical-align: middle;
}

.score-cell.target {
  background: rgba(0, 217, 255, 0.05);
}

.score-display {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.score-value {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--any-text-primary, #ffffff);
}

/* Insights */
.insights-section {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--any-border, rgba(255, 255, 255, 0.08));
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
  margin: 0 0 0.75rem;
}

.section-title svg {
  color: #FFB800;
}

.insights-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.8125rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
  line-height: 1.6;
}

.insights-list li {
  margin-bottom: 0.375rem;
}

.insights-list li:last-child {
  margin-bottom: 0;
}

/* Empty State */
.empty-state {
  padding: 2rem;
  text-align: center;
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.4));
}

/* Responsive */
@media (max-width: 640px) {
  .peer-col {
    min-width: 70px;
  }

  .comparison-table th,
  .comparison-table td {
    padding: 0.5rem 0.375rem;
    font-size: 0.75rem;
  }

  .peer-header {
    align-items: flex-end;
  }

  .peer-symbol {
    display: none;
  }
}
</style>
