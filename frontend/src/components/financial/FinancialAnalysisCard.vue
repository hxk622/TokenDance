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
/* ============================================
   FinancialAnalysisCard - Dark Theme
   ============================================ */

.financial-analysis-card {
  background: rgba(28, 28, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
  backdrop-filter: blur(12px);
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
  color: #ffffff;
  margin: 0;
  font-family: 'Space Grotesk', sans-serif;
}

.health-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.health-excellent {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.health-good {
  background: rgba(0, 217, 255, 0.2);
  color: #00D9FF;
}

.health-fair {
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
}

.health-poor {
  background: rgba(255, 107, 107, 0.2);
  color: #FF6B6B;
}

.health-critical {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.5);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
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
  background: rgba(255, 59, 48, 0.15);
  border: 1px solid rgba(255, 59, 48, 0.3);
  border-radius: 8px;
}

.error-text {
  color: #FF6B6B;
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
    #00FF88 calc(var(--score) * 3.6deg),
    rgba(255, 255, 255, 0.1) calc(var(--score) * 3.6deg)
  );
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  box-shadow: 0 0 24px rgba(0, 255, 136, 0.2);
}

.score-circle::before {
  content: '';
  position: absolute;
  width: 80px;
  height: 80px;
  background: rgba(28, 28, 30, 0.95);
  border-radius: 50%;
}

.score-value {
  position: relative;
  font-size: 1.75rem;
  font-weight: 700;
  color: #ffffff;
}

.score-label {
  position: relative;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Dimensions */
.dimensions-section {
  margin-top: 1.5rem;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
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
  color: rgba(255, 255, 255, 0.5);
}

.bar-value {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.bar-track {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.bar-fill.excellent { background: linear-gradient(90deg, #00FF88, #10b981); }
.bar-fill.good { background: linear-gradient(90deg, #00D9FF, #3b82f6); }
.bar-fill.fair { background: linear-gradient(90deg, #FFB800, #f59e0b); }
.bar-fill.poor { background: linear-gradient(90deg, #FF8C00, #f97316); }
.bar-fill.critical { background: linear-gradient(90deg, #FF3B30, #ef4444); }

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
  padding: 0.75rem 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.metric-item:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.metric-label {
  font-size: 0.625rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #ffffff;
}

.metric-value.positive { color: #00FF88; }
.metric-value.negative { color: #FF6B6B; }

/* Insights */
.insights-section {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.insight-group {
  padding: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.insight-list {
  margin: 0;
  padding-left: 1.25rem;
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.7);
}

.insight-list li {
  margin-bottom: 0.25rem;
}

.insight-list.risk li {
  color: #FF6B6B;
}

/* Summary */
.summary-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.summary-text {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.6;
}

/* Empty */
.empty-state {
  padding: 2rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
}

/* Responsive */
@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
