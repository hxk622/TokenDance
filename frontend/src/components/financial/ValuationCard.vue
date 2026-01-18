<template>
  <div class="valuation-card">
    <div class="card-header">
      <h3 class="card-title">
        💰 估值分析
      </h3>
      <span
        v-if="result"
        class="valuation-badge"
        :class="valuationClass"
      >
        {{ valuationLabel }}
      </span>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="loading-spinner" />
      <p>正在进行估值分析...</p>
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
      <!-- Current Price -->
      <div class="price-section">
        <div class="current-price">
          <span class="price-label">当前价格</span>
          <span class="price-value">¥{{ result.current_price.toFixed(2) }}</span>
        </div>
        <div
          v-if="result.target_price_range"
          class="target-range"
        >
          <span class="range-label">目标区间</span>
          <span class="range-value">
            ¥{{ result.target_price_range.low.toFixed(2) }} - ¥{{ result.target_price_range.high.toFixed(2) }}
          </span>
          <span
            class="confidence-badge"
            :class="`confidence-${result.target_price_range.confidence}`"
          >
            {{ confidenceLabels[result.target_price_range.confidence] }}
          </span>
        </div>
      </div>

      <!-- Relative Valuation -->
      <div class="valuation-section">
        <h4 class="section-title">
          相对估值
        </h4>
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-label">PE (TTM)</span>
            <span class="metric-value">{{ formatNumber(result.relative.pe_ttm) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PB</span>
            <span class="metric-value">{{ formatNumber(result.relative.pb) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PS</span>
            <span class="metric-value">{{ formatNumber(result.relative.ps) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">PEG</span>
            <span class="metric-value">{{ formatNumber(result.relative.peg) }}</span>
          </div>
        </div>
      </div>

      <!-- Historical Comparison -->
      <div
        v-if="result.historical"
        class="historical-section"
      >
        <h4 class="section-title">
          历史分位
        </h4>
        <div class="percentile-bars">
          <div
            v-if="result.historical.pe_percentile !== null"
            class="percentile-bar"
          >
            <div class="percentile-label">
              <span>PE 分位</span>
              <span>{{ (result.historical.pe_percentile * 100).toFixed(0) }}%</span>
            </div>
            <div class="percentile-track">
              <div 
                class="percentile-fill" 
                :style="{ width: `${result.historical.pe_percentile * 100}%` }"
                :class="getPercentileClass(result.historical.pe_percentile)"
              />
              <div 
                class="percentile-marker" 
                :style="{ left: `${result.historical.pe_percentile * 100}%` }"
              />
            </div>
          </div>
          <div
            v-if="result.historical.pb_percentile !== null"
            class="percentile-bar"
          >
            <div class="percentile-label">
              <span>PB 分位</span>
              <span>{{ (result.historical.pb_percentile * 100).toFixed(0) }}%</span>
            </div>
            <div class="percentile-track">
              <div 
                class="percentile-fill" 
                :style="{ width: `${result.historical.pb_percentile * 100}%` }"
                :class="getPercentileClass(result.historical.pb_percentile)"
              />
              <div 
                class="percentile-marker" 
                :style="{ left: `${result.historical.pb_percentile * 100}%` }"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Industry Comparison -->
      <div
        v-if="result.industry"
        class="industry-section"
      >
        <h4 class="section-title">
          行业对比
        </h4>
        <div class="industry-info">
          <span
            v-if="result.industry.industry_name"
            class="industry-name"
          >
            {{ result.industry.industry_name }}
          </span>
          <div
            v-if="result.industry.premium_discount !== null"
            class="premium-discount"
          >
            <span>相对行业：</span>
            <span :class="getPremiumClass(result.industry.premium_discount)">
              {{ result.industry.premium_discount > 0 ? '溢价' : '折价' }}
              {{ Math.abs(result.industry.premium_discount * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- DCF -->
      <div
        v-if="result.dcf && result.dcf.intrinsic_value"
        class="dcf-section"
      >
        <h4 class="section-title">
          DCF 估值
        </h4>
        <div class="dcf-info">
          <div class="dcf-item">
            <span class="dcf-label">内在价值</span>
            <span class="dcf-value">¥{{ result.dcf.intrinsic_value.toFixed(2) }}</span>
          </div>
          <div
            v-if="result.dcf.margin_of_safety !== null"
            class="dcf-item"
          >
            <span class="dcf-label">安全边际</span>
            <span
              class="dcf-value"
              :class="getMarginClass(result.dcf.margin_of_safety)"
            >
              {{ (result.dcf.margin_of_safety * 100).toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- Key Points -->
      <div
        v-if="result.key_points.length > 0"
        class="insights-section"
      >
        <h4 class="section-title">
          要点
        </h4>
        <ul class="insight-list">
          <li
            v-for="(point, idx) in result.key_points.slice(0, 3)"
            :key="idx"
          >
            {{ point }}
          </li>
        </ul>
      </div>

      <!-- Risks -->
      <div
        v-if="result.risks.length > 0"
        class="insights-section"
      >
        <h4 class="section-title">
          风险提示
        </h4>
        <ul class="insight-list risk">
          <li
            v-for="(risk, idx) in result.risks.slice(0, 3)"
            :key="idx"
          >
            {{ risk }}
          </li>
        </ul>
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
      <p>点击"一键分析"查看估值分析结果</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ValuationAnalysisResult } from '@/types/financial'

const props = defineProps<{
  result: ValuationAnalysisResult | null
  isLoading?: boolean
  error?: string | null
}>()

const valuationLabels: Record<string, string> = {
  extremely_low: '极度低估',
  low: '低估',
  fair: '合理',
  high: '高估',
  extremely_high: '极度高估',
}

const confidenceLabels: Record<string, string> = {
  low: '低置信度',
  medium: '中置信度',
  high: '高置信度',
}

const valuationClass = computed(() => {
  if (!props.result) return ''
  return `valuation-${props.result.valuation_level}`
})

const valuationLabel = computed(() => {
  if (!props.result) return ''
  return valuationLabels[props.result.valuation_level] || props.result.valuation_level
})

function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2)
}

function getPercentileClass(value: number): string {
  if (value <= 0.2) return 'low'
  if (value <= 0.4) return 'low-mid'
  if (value <= 0.6) return 'mid'
  if (value <= 0.8) return 'high-mid'
  return 'high'
}

function getPremiumClass(value: number): string {
  if (value > 0.1) return 'premium'
  if (value < -0.1) return 'discount'
  return ''
}

function getMarginClass(value: number): string {
  if (value >= 0.2) return 'positive'
  if (value <= 0) return 'negative'
  return ''
}
</script>

<style scoped>
.valuation-card {
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

.valuation-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.valuation-extremely_low,
.valuation-low {
  background: #d1fae5;
  color: #065f46;
}

.valuation-fair {
  background: #dbeafe;
  color: #1e40af;
}

.valuation-high {
  background: #fef3c7;
  color: #92400e;
}

.valuation-extremely_high {
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
  border-top-color: #f59e0b;
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

/* Price Section */
.price-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
  margin-bottom: 1rem;
}

.current-price,
.target-range {
  display: flex;
  flex-direction: column;
}

.price-label,
.range-label {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.price-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
}

.range-value {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
}

.confidence-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  margin-top: 0.25rem;
  align-self: flex-start;
}

.confidence-low {
  background: #fee2e2;
  color: #991b1b;
}

.confidence-medium {
  background: #fef3c7;
  color: #92400e;
}

.confidence-high {
  background: #d1fae5;
  color: #065f46;
}

/* Section Title */
.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.75rem 0;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 8px;
}

.metric-label {
  font-size: 0.625rem;
  color: #6b7280;
  margin-bottom: 0.25rem;
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

/* Percentile Bars */
.historical-section {
  margin-top: 1rem;
}

.percentile-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.percentile-bar {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.percentile-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
}

.percentile-track {
  height: 8px;
  background: linear-gradient(to right, #d1fae5, #fef3c7, #fee2e2);
  border-radius: 4px;
  position: relative;
  overflow: visible;
}

.percentile-fill {
  height: 100%;
  border-radius: 4px;
  opacity: 0;
}

.percentile-marker {
  position: absolute;
  top: -2px;
  width: 12px;
  height: 12px;
  background: #111827;
  border: 2px solid #ffffff;
  border-radius: 50%;
  transform: translateX(-50%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

/* Industry Section */
.industry-section {
  margin-top: 1rem;
}

.industry-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 8px;
}

.industry-name {
  font-size: 0.875rem;
  color: #374151;
}

.premium-discount {
  font-size: 0.875rem;
}

.premium {
  color: #dc2626;
  font-weight: 600;
}

.discount {
  color: #059669;
  font-weight: 600;
}

/* DCF Section */
.dcf-section {
  margin-top: 1rem;
}

.dcf-info {
  display: flex;
  gap: 1.5rem;
}

.dcf-item {
  display: flex;
  flex-direction: column;
}

.dcf-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.dcf-value {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
}

.dcf-value.positive {
  color: #059669;
}

.dcf-value.negative {
  color: #dc2626;
}

/* Insights */
.insights-section {
  margin-top: 1rem;
}

.insight-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  color: #374151;
}

.insight-list li {
  margin-bottom: 0.25rem;
}

.insight-list.risk li {
  color: #991b1b;
}

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
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .price-section {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
