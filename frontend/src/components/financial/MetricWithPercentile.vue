<template>
  <div class="metric-percentile-card">
    <!-- Header Row -->
    <div class="metric-header">
      <div class="metric-info">
        <span class="metric-name">{{ benchmark.metric_name }}</span>
        <span class="metric-value">{{ formatValue(benchmark.current_value, benchmark.metric_key) }}</span>
      </div>
      <span
        class="percentile-badge"
        :class="percentileClass"
      >
        TOP {{ benchmark.percentile.toFixed(0) }}%
      </span>
    </div>

    <!-- Percentile Track -->
    <div class="percentile-track">
      <div class="track-gradient" />
      <!-- Industry Mean Marker -->
      <div
        class="mean-marker"
        :style="{ left: getMeanPosition() }"
        :title="`行业均值: ${formatValue(benchmark.mean, benchmark.metric_key)}`"
      >
        <div class="mean-line" />
        <span class="mean-label">均值</span>
      </div>
      <!-- Current Value Marker -->
      <div
        class="current-marker"
        :style="{ left: getCurrentPosition() }"
      >
        <div class="marker-dot" />
      </div>
    </div>

    <!-- Percentile Labels -->
    <div class="track-labels">
      <span class="track-label">0%</span>
      <span class="track-label center">行业中位数 {{ formatValue(benchmark.percentile_50, benchmark.metric_key) }}</span>
      <span class="track-label">100%</span>
    </div>

    <!-- Trend Description -->
    <p
      v-if="benchmark.trend_description"
      class="trend-description"
    >
      {{ benchmark.trend_description }}
    </p>

    <!-- DuPont Section (Collapsible) -->
    <div
      v-if="dupont && showDupont"
      class="dupont-section"
    >
      <button
        class="dupont-trigger"
        @click="isDupontExpanded = !isDupontExpanded"
      >
        <TrendingUp
          class="trigger-icon"
          :size="16"
        />
        <span>DuPont 分解</span>
        <ChevronDown
          class="chevron-icon"
          :class="{ expanded: isDupontExpanded }"
          :size="16"
        />
      </button>

      <Transition name="collapse">
        <div
          v-if="isDupontExpanded"
          class="dupont-breakdown"
        >
          <!-- ROE Formula -->
          <div class="dupont-formula">
            <span class="formula-label">ROE {{ dupont.roe.toFixed(1) }}%</span>
            <span class="formula-equals">=</span>
            <span class="formula-factor">净利率</span>
            <span class="formula-op">×</span>
            <span class="formula-factor">周转率</span>
            <span class="formula-op">×</span>
            <span class="formula-factor">权益乘数</span>
          </div>

          <!-- Three Factors -->
          <div class="dupont-factors">
            <DuPontFactorItem
              :factor="dupont.net_profit_margin"
              :suffix="'%'"
            />
            <DuPontFactorItem
              :factor="dupont.asset_turnover"
              :suffix="'x'"
              :decimals="2"
            />
            <DuPontFactorItem
              :factor="dupont.equity_multiplier"
              :suffix="'x'"
              :decimals="2"
            />
          </div>

          <!-- Primary Driver -->
          <div class="dupont-driver">
            <span class="driver-label">主要驱动因素:</span>
            <span class="driver-value">{{ dupont.primary_driver }}</span>
          </div>

          <!-- Insights -->
          <ul
            v-if="dupont.insights.length > 0"
            class="dupont-insights"
          >
            <li
              v-for="(insight, idx) in dupont.insights"
              :key="idx"
            >
              {{ insight }}
            </li>
          </ul>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { TrendingUp, ChevronDown } from 'lucide-vue-next'
import DuPontFactorItem from './DuPontFactorItem.vue'

// Types
interface IndustryBenchmark {
  metric_name: string
  metric_key: string
  current_value: number
  percentile: number
  percentile_10: number
  percentile_25: number
  percentile_50: number
  percentile_75: number
  percentile_90: number
  mean: number
  rank: number
  total_companies: number
  trend: string
  trend_description: string
}

interface DuPontFactor {
  name: string
  value: number
  percentile: number
  trend: string
  description: string
}

interface DuPontDecomposition {
  symbol: string
  name: string
  roe: number
  net_profit_margin: DuPontFactor
  asset_turnover: DuPontFactor
  equity_multiplier: DuPontFactor
  primary_driver: string
  insights: string[]
}

// Props
const props = defineProps<{
  benchmark: IndustryBenchmark
  dupont?: DuPontDecomposition | null
  showDupont?: boolean
}>()

// State
const isDupontExpanded = ref(false)

// Computed
const percentileClass = computed(() => {
  const p = props.benchmark.percentile
  if (p <= 10) return 'top-10'
  if (p <= 25) return 'top-25'
  if (p <= 50) return 'top-50'
  if (p <= 75) return 'bottom-50'
  return 'bottom-25'
})

// Methods
function formatValue(value: number, metricKey: string): string {
  if (value === null || value === undefined) return '-'

  // 百分比类指标
  const percentMetrics = ['roe', 'roa', 'net_margin', 'gross_margin', 'revenue_growth', 'profit_growth', 'debt_ratio']
  if (percentMetrics.includes(metricKey)) {
    return `${value.toFixed(1)}%`
  }

  // 倍数类指标
  const ratioMetrics = ['pe_ttm', 'pb', 'ps', 'current_ratio', 'asset_turnover']
  if (ratioMetrics.includes(metricKey)) {
    return `${value.toFixed(2)}x`
  }

  return value.toFixed(2)
}

function getMeanPosition(): string {
  // 将均值映射到 0-100% 的位置
  const { percentile_10, percentile_90, mean } = props.benchmark
  if (percentile_90 === percentile_10) return '50%'

  const position = ((mean - percentile_10) / (percentile_90 - percentile_10)) * 100
  return `${Math.max(5, Math.min(95, position))}%`
}

function getCurrentPosition(): string {
  // 分位数直接映射到位置 (0% = best, 100% = worst -> 反转为 100% = best)
  const position = 100 - props.benchmark.percentile
  return `${Math.max(5, Math.min(95, position))}%`
}
</script>

<style scoped>
.metric-percentile-card {
  background: var(--any-bg-tertiary, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--any-border, rgba(255, 255, 255, 0.08));
  border-radius: 12px;
  padding: 1rem;
  transition: all 0.2s ease;
}

.metric-percentile-card:hover {
  border-color: var(--any-border-hover, rgba(255, 255, 255, 0.15));
}

/* Header */
.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.metric-info {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
}

.metric-name {
  font-size: 0.875rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--any-text-primary, #ffffff);
  font-family: 'Space Grotesk', monospace;
}

/* Percentile Badge */
.percentile-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.percentile-badge.top-10 {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.percentile-badge.top-25 {
  background: rgba(0, 217, 255, 0.2);
  color: #00D9FF;
}

.percentile-badge.top-50 {
  background: rgba(255, 255, 255, 0.1);
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
}

.percentile-badge.bottom-50 {
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
}

.percentile-badge.bottom-25 {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

/* Percentile Track */
.percentile-track {
  position: relative;
  height: 8px;
  margin: 0.75rem 0 0.25rem;
}

.track-gradient {
  position: absolute;
  inset: 0;
  border-radius: 4px;
  background: linear-gradient(
    to right,
    #FF3B30 0%,
    #FFB800 25%,
    rgba(255, 255, 255, 0.2) 50%,
    #00D9FF 75%,
    #00FF88 100%
  );
  opacity: 0.6;
}

/* Mean Marker */
.mean-marker {
  position: absolute;
  top: -4px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
}

.mean-line {
  width: 2px;
  height: 16px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 1px;
}

.mean-label {
  font-size: 0.625rem;
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.5));
  margin-top: 2px;
}

/* Current Marker */
.current-marker {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.marker-dot {
  width: 14px;
  height: 14px;
  background: var(--any-text-primary, #ffffff);
  border: 3px solid rgba(0, 217, 255, 0.8);
  border-radius: 50%;
  box-shadow: 0 0 8px rgba(0, 217, 255, 0.4);
}

/* Track Labels */
.track-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.25rem;
}

.track-label {
  font-size: 0.625rem;
  color: var(--any-text-muted, rgba(255, 255, 255, 0.4));
}

.track-label.center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

/* Trend Description */
.trend-description {
  font-size: 0.75rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
  margin: 0.75rem 0 0;
  padding: 0.5rem;
  background: var(--any-bg-secondary, rgba(255, 255, 255, 0.02));
  border-radius: 6px;
}

/* DuPont Section */
.dupont-section {
  margin-top: 1rem;
  border-top: 1px solid var(--any-border, rgba(255, 255, 255, 0.08));
  padding-top: 0.75rem;
}

.dupont-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem;
  background: transparent;
  border: none;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
  font-size: 0.8125rem;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.dupont-trigger:hover {
  background: var(--any-bg-hover, rgba(255, 255, 255, 0.05));
  color: var(--any-text-primary, #ffffff);
}

.trigger-icon {
  color: #00D9FF;
}

.chevron-icon {
  margin-left: auto;
  transition: transform 0.2s ease;
}

.chevron-icon.expanded {
  transform: rotate(180deg);
}

/* DuPont Breakdown */
.dupont-breakdown {
  padding: 0.75rem 0.5rem;
}

.dupont-formula {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
  font-size: 0.75rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
}

.formula-label {
  font-weight: 600;
  color: #00D9FF;
}

.formula-equals,
.formula-op {
  color: var(--any-text-muted, rgba(255, 255, 255, 0.4));
}

.formula-factor {
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.7));
}

.dupont-factors {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.dupont-driver {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  padding: 0.5rem;
  background: rgba(0, 217, 255, 0.1);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.driver-label {
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
}

.driver-value {
  color: #00D9FF;
  font-weight: 600;
}

.dupont-insights {
  margin: 0;
  padding-left: 1rem;
  font-size: 0.75rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
}

.dupont-insights li {
  margin-bottom: 0.25rem;
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
