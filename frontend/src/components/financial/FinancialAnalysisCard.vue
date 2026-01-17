<template>
  <div class="financial-analysis-card">
    <div class="card-header">
      <h3 class="card-title">财务分析</h3>
      <span v-if="result" class="health-badge" :class="healthClass">
        {{ healthLabel }}
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner" />
      <p>正在分析财务数据...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <p class="error-text">{{ error }}</p>
    </div>

    <!-- Result -->
    <div v-else-if="result" class="card-content">
      <!-- Overall Score -->
      <div class="score-section">
        <div class="score-circle" :style="{ '--score': result.overall_score }">
          <span class="score-value">{{ result.overall_score.toFixed(0) }}</span>
          <span class="score-label">综合评分</span>
        </div>
      </div>

      <!-- Dimension Scores -->
      <div class="dimensions-section">
        <h4 class="section-title">五维分析</h4>
        <div class="dimension-bars">
          <div v-for="(score, key) in result.dimension_scores" :key="key" class="dimension-bar">
            <div class="bar-label">
              <span>{{ dimensionLabels[key] }}</span>
              <span class="bar-value">{{ score.toFixed(0) }}</span>
            </div>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: `${score}%` }" :class="getScoreClass(score)" />
            </div>
          </div>
        </div>
      </div>

      <!-- Key Metrics -->
      <div class="metrics-section">
        <h4 class="section-title">关键指标</h4>
        <div class="metrics-grid">
          <div class="metric-item">
            <span class="metric-label">ROE</span>
            <span class="metric-value">{{ formatPercent(result.profitability.roe) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">ROA</span>
            <span class="metric-value">{{ formatPercent(result.profitability.roa) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">毛利率</span>
            <span class="metric-value">{{ formatPercent(result.profitability.gross_margin) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">净利率</span>
            <span class="metric-value">{{ formatPercent(result.profitability.net_margin) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">营收增速</span>
            <span class="metric-value" :class="getGrowthClass(result.growth.revenue_growth)">
              {{ formatPercent(result.growth.revenue_growth) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">利润增速</span>
            <span class="metric-value" :class="getGrowthClass(result.growth.net_income_growth)">
              {{ formatPercent(result.growth.net_income_growth) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">资产负债率</span>
            <span class="metric-value">{{ formatPercent(result.solvency.debt_to_assets) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">流动比率</span>
            <span class="metric-value">{{ formatNumber(result.solvency.current_ratio) }}</span>
          </div>
        </div>
      </div>

      <!-- Strengths & Risks -->
      <div class="insights-section">
        <div v-if="result.strengths.length > 0" class="insight-group">
          <h4 class="section-title">✅ 优势</h4>
          <ul class="insight-list">
            <li v-for="(item, idx) in result.strengths.slice(0, 3)" :key="idx">{{ item }}</li>
          </ul>
        </div>

        <div v-if="result.key_risks.length > 0" class="insight-group">
          <h4 class="section-title">⚠️ 风险</h4>
          <ul class="insight-list risk">
            <li v-for="(item, idx) in result.key_risks.slice(0, 3)" :key="idx">{{ item }}</li>
          </ul>
        </div>
      </div>

      <!-- Summary -->
      <div v-if="result.summary" class="summary-section">
        <p class="summary-text">{{ result.summary }}</p>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <p>点击"一键分析"查看财务分析结果</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FinancialAnalysisResult } from '@/types/financial'

const props = defineProps<{
  result: FinancialAnalysisResult | null
  isLoading?: boolean
  error?: string | null
}>()

const dimensionLabels: Record<string, string> = {
  profitability: '盈利能力',
  growth: '成长能力',
  solvency: '偿债能力',
  efficiency: '运营效率',
  cash_flow: '现金流',
}

const healthLabels: Record<string, string> = {
  excellent: '优秀',
  good: '良好',
  fair: '一般',
  poor: '较差',
  critical: '危险',
}

const healthClass = computed(() => {
  if (!props.result) return ''
  return `health-${props.result.health_level}`
})

const healthLabel = computed(() => {
  if (!props.result) return ''
  return healthLabels[props.result.health_level] || props.result.health_level
})

function getScoreClass(score: number): string {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'fair'
  if (score >= 20) return 'poor'
  return 'critical'
}

function getGrowthClass(value: number | null): string {
  if (value === null) return ''
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return ''
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return `${(value * 100).toFixed(1)}%`
}

function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2)
}
</script>

<style scoped>
.financial-analysis-card {
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

.health-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.health-excellent {
  background: #d1fae5;
  color: #065f46;
}

.health-good {
  background: #dbeafe;
  color: #1e40af;
}

.health-fair {
  background: #fef3c7;
  color: #92400e;
}

.health-poor {
  background: #fee2e2;
  color: #991b1b;
}

.health-critical {
  background: #fecaca;
  color: #7f1d1d;
}

/* Loading */
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
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error */
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

/* Score Section */
.score-section {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.score-circle {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: conic-gradient(
    #10b981 calc(var(--score) * 3.6deg),
    #e5e7eb calc(var(--score) * 3.6deg)
  );
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 80px;
  height: 80px;
  background: #ffffff;
  border-radius: 50%;
}

.score-value {
  position: relative;
  font-size: 1.75rem;
  font-weight: 700;
  color: #111827;
}

.score-label {
  position: relative;
  font-size: 0.75rem;
  color: #6b7280;
}

/* Dimensions */
.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 0.75rem 0;
}

.dimension-bars {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dimension-bar {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #6b7280;
}

.bar-value {
  font-weight: 600;
  color: #374151;
}

.bar-track {
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width var(--transition-slow) var(--ease-default);
}

.bar-fill.excellent { background: #10b981; }
.bar-fill.good { background: #3b82f6; }
.bar-fill.fair { background: #f59e0b; }
.bar-fill.poor { background: #f97316; }
.bar-fill.critical { background: #ef4444; }

/* Metrics */
.metrics-section {
  margin-top: 1.5rem;
}

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

.metric-value.positive { color: #10b981; }
.metric-value.negative { color: #ef4444; }

/* Insights */
.insights-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
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
}
</style>
