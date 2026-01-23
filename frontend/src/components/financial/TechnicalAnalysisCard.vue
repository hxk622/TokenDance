<template>
  <div class="technical-analysis-card">
    <div class="card-header">
      <h3 class="card-title">
        技术分析
      </h3>
      <span
        v-if="result"
        class="signal-badge"
        :class="signalClass"
      >
        {{ signalLabel }}
      </span>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="loading-spinner" />
      <p>正在进行技术分析...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="error-state"
    >
      <p class="error-text">
        {{ error }}
      </p>
    </div>

    <!-- Result -->
    <div
      v-else-if="result"
      class="card-content"
    >
      <!-- Score -->
      <div class="score-section">
        <div
          class="score-circle"
          :class="getScoreClass(result.score)"
        >
          <span class="score-value">{{ result.score.toFixed(0) }}</span>
        </div>
        <span class="score-label">技术评分</span>
      </div>

      <!-- Signals -->
      <div class="signals-section">
        <div
          v-if="result.buy_signals.length > 0"
          class="signal-group buy"
        >
          <h4 class="signal-title">
            🟢 买入信号
          </h4>
          <div class="signal-tags">
            <span
              v-for="(signal, idx) in result.buy_signals.slice(0, 4)"
              :key="idx"
              class="signal-tag"
            >
              {{ signal }}
            </span>
          </div>
        </div>

        <div
          v-if="result.sell_signals.length > 0"
          class="signal-group sell"
        >
          <h4 class="signal-title">
            🔴 卖出信号
          </h4>
          <div class="signal-tags">
            <span
              v-for="(signal, idx) in result.sell_signals.slice(0, 4)"
              :key="idx"
              class="signal-tag"
            >
              {{ signal }}
            </span>
          </div>
        </div>
      </div>

      <!-- Key Indicators -->
      <div class="indicators-section">
        <h4 class="section-title">
          关键指标
        </h4>
        <div class="indicator-grid">
          <div class="indicator-item">
            <span class="indicator-label">RSI</span>
            <span
              class="indicator-value"
              :class="getRsiClass(result.momentum.rsi.value)"
            >
              {{ formatNumber(result.momentum.rsi.value) }}
            </span>
          </div>
          <div class="indicator-item">
            <span class="indicator-label">MACD</span>
            <span
              class="indicator-value"
              :class="getMacdClass(result.trend.macd.signal_type)"
            >
              {{ result.trend.macd.signal_type === 'bullish' ? '多' : result.trend.macd.signal_type === 'bearish' ? '空' : '中' }}
            </span>
          </div>
          <div class="indicator-item">
            <span class="indicator-label">KDJ</span>
            <span
              class="indicator-value"
              :class="getKdjClass(result.momentum.kdj.signal)"
            >
              {{ result.momentum.kdj.signal === 'bullish' ? '金叉' : result.momentum.kdj.signal === 'bearish' ? '死叉' : '中性' }}
            </span>
          </div>
          <div class="indicator-item">
            <span class="indicator-label">布林</span>
            <span class="indicator-value">
              {{ getBollingerLabel(result.volatility.bollinger.position) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Support & Resistance -->
      <div
        v-if="result.support_levels.length > 0 || result.resistance_levels.length > 0"
        class="levels-section"
      >
        <h4 class="section-title">
          支撑/阻力位
        </h4>
        <div class="levels-grid">
          <div
            v-if="result.support_levels.length > 0"
            class="level-group"
          >
            <span class="level-label">支撑</span>
            <span class="level-value support">
              ¥{{ result.support_levels[0]?.toFixed(2) }}
            </span>
          </div>
          <div
            v-if="result.resistance_levels.length > 0"
            class="level-group"
          >
            <span class="level-label">阻力</span>
            <span class="level-value resistance">
              ¥{{ result.resistance_levels[0]?.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Summary -->
      <div
        v-if="result.summary"
        class="summary-section"
      >
        <p class="summary-text">
          {{ result.summary }}
        </p>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else
      class="empty-state"
    >
      <p>点击"一键分析"查看技术分析结果</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TechnicalAnalysisResult } from '@/types/financial'

const props = defineProps<{
  result: TechnicalAnalysisResult | null
  isLoading?: boolean
  error?: string | null
}>()

const signalLabels: Record<string, string> = {
  strong_buy: '强烈买入',
  buy: '买入',
  neutral: '中性',
  sell: '卖出',
  strong_sell: '强烈卖出',
}

const signalClass = computed(() => {
  if (!props.result) return ''
  return `signal-${props.result.overall_signal}`
})

const signalLabel = computed(() => {
  if (!props.result) return ''
  return signalLabels[props.result.overall_signal] || props.result.overall_signal
})

function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return value.toFixed(1)
}

function getScoreClass(score: number): string {
  if (score >= 70) return 'bullish'
  if (score >= 50) return 'neutral'
  return 'bearish'
}

function getRsiClass(value: number | null): string {
  if (value === null) return ''
  if (value >= 70) return 'overbought'
  if (value <= 30) return 'oversold'
  return 'neutral'
}

function getMacdClass(type: string): string {
  if (type === 'bullish') return 'bullish'
  if (type === 'bearish') return 'bearish'
  return 'neutral'
}

function getKdjClass(signal: string): string {
  if (signal === 'bullish') return 'bullish'
  if (signal === 'bearish') return 'bearish'
  return 'neutral'
}

function getBollingerLabel(position: string): string {
  const labels: Record<string, string> = {
    above_upper: '上轨上方',
    upper_half: '上半区',
    lower_half: '下半区',
    below_lower: '下轨下方',
  }
  return labels[position] || position
}
</script>

<style scoped>
.technical-analysis-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-title {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.signal-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.signal-strong_buy,
.signal-buy {
  background: #d1fae5;
  color: #065f46;
}

.signal-neutral {
  background: #e5e7eb;
  color: #374151;
}

.signal-sell,
.signal-strong_sell {
  background: #fee2e2;
  color: #991b1b;
}

/* Loading & Error */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: #6b7280;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #00D9FF;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  padding: 1rem;
  background: #fef2f2;
  border-radius: 8px;
}

.error-text {
  color: #991b1b;
  margin: 0;
  font-size: 0.875rem;
}

/* Score */
.score-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 1.5rem;
}

.score-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.score-circle.bullish {
  background: #d1fae5;
}

.score-circle.neutral {
  background: #e5e7eb;
}

.score-circle.bearish {
  background: #fee2e2;
}

.score-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

.score-label {
  font-size: 0.75rem;
  color: #6b7280;
}

/* Signals */
.signals-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.signal-group {
  padding: 0.75rem;
  border-radius: 8px;
}

.signal-group.buy {
  background: #f0fdf4;
}

.signal-group.sell {
  background: #fef2f2;
}

.signal-title {
  font-size: 0.75rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.signal-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.signal-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  color: #374151;
}

/* Indicators */
.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.75rem 0;
}

.indicator-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

.indicator-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 8px;
}

.indicator-label {
  font-size: 0.625rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.indicator-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.indicator-value.bullish { color: #059669; }
.indicator-value.bearish { color: #dc2626; }
.indicator-value.overbought { color: #dc2626; }
.indicator-value.oversold { color: #059669; }

/* Levels */
.levels-section {
  margin-top: 1rem;
}

.levels-grid {
  display: flex;
  gap: 1.5rem;
}

.level-group {
  display: flex;
  flex-direction: column;
}

.level-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.level-value {
  font-size: 1rem;
  font-weight: 600;
}

.level-value.support { color: #059669; }
.level-value.resistance { color: #dc2626; }

/* Summary */
.summary-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.summary-text {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
  line-height: 1.5;
}

/* Empty */
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #9ca3af;
}

/* Responsive */
@media (max-width: 640px) {
  .indicator-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
