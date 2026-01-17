<template>
  <div class="sentiment-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <h3 class="title">舆情情绪分析</h3>
      <div v-if="sentiment" class="data-sources">
        <span 
          v-for="source in sentiment.sources_used" 
          :key="source" 
          class="source-tag"
        >
          {{ getSourceLabel(source) }}
        </span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>分析舆情数据中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!sentiment" class="empty-state">
      <div class="empty-icon">📊</div>
      <p>暂无舆情数据</p>
      <p class="hint">选择股票后将自动加载</p>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="dashboard-content">
      <!-- Overall Score -->
      <div class="score-section">
        <div class="score-label">
          <span class="label-text">整体情绪</span>
          <span class="score-value" :class="getSentimentClass(sentiment.analysis?.overall_label || 'neutral')">
            {{ getSentimentLabel(sentiment.analysis?.overall_label || 'neutral') }}
          </span>
        </div>
        
        <!-- Progress Bar (-1 to +1) -->
        <div class="score-bar-container">
          <div class="score-bar-track">
            <!-- Negative zone -->
            <div class="zone negative-zone"></div>
            <!-- Neutral zone -->
            <div class="zone neutral-zone"></div>
            <!-- Positive zone -->
            <div class="zone positive-zone"></div>
            
            <!-- Score indicator -->
            <div 
              class="score-indicator" 
              :style="{ left: getScorePosition(sentiment.analysis?.overall_score || 0) }"
              :class="getSentimentClass(sentiment.analysis?.overall_label || 'neutral')"
            >
              <div class="indicator-dot"></div>
              <div class="indicator-label">{{ (sentiment.analysis?.overall_score || 0).toFixed(2) }}</div>
            </div>
          </div>
          
          <!-- Scale labels -->
          <div class="score-scale">
            <span class="scale-label">看空</span>
            <span class="scale-label">中性</span>
            <span class="scale-label">看多</span>
          </div>
        </div>
      </div>

      <!-- Sentiment Distribution -->
      <div class="distribution-section">
        <h4 class="section-title">情绪分布</h4>
        
        <div class="distribution-content">
          <!-- Pie Chart -->
          <div class="pie-chart">
            <svg viewBox="0 0 200 200" class="pie-svg">
              <g transform="translate(100, 100)">
                <!-- Background circle -->
                <circle r="80" fill="none" stroke="#f3f4f6" stroke-width="40" />
                
                <!-- Sentiment segments -->
                <circle
                  v-for="(segment, index) in pieSegments"
                  :key="index"
                  r="80"
                  fill="none"
                  :stroke="segment.color"
                  stroke-width="40"
                  :stroke-dasharray="`${segment.length} ${circumference}`"
                  :stroke-dashoffset="segment.offset"
                  transform="rotate(-90)"
                  class="pie-segment"
                />
              </g>
              
              <!-- Center label -->
              <text x="100" y="95" text-anchor="middle" class="pie-center-label">
                {{ sentiment.posts.length }}
              </text>
              <text x="100" y="110" text-anchor="middle" class="pie-center-sublabel">
                条帖子
              </text>
            </svg>
          </div>

          <!-- Legend -->
          <div class="distribution-legend">
            <div 
              v-for="item in distributionData" 
              :key="item.label"
              class="legend-item"
            >
              <div class="legend-indicator" :style="{ backgroundColor: item.color }"></div>
              <div class="legend-content">
                <span class="legend-label">{{ item.label }}</span>
                <span class="legend-value">
                  {{ item.count }} <span class="legend-percent">({{ item.percentage }}%)</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Key Metrics -->
      <div class="metrics-section">
        <div class="metric-card">
          <div class="metric-icon">📈</div>
          <div class="metric-content">
            <span class="metric-label">看多</span>
            <span class="metric-value bullish">{{ sentiment.analysis?.bullish_count || 0 }}</span>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon">📉</div>
          <div class="metric-content">
            <span class="metric-label">看空</span>
            <span class="metric-value bearish">{{ sentiment.analysis?.bearish_count || 0 }}</span>
          </div>
        </div>
        
        <div class="metric-card">
          <div class="metric-icon">➖</div>
          <div class="metric-content">
            <span class="metric-label">中性</span>
            <span class="metric-value neutral">{{ sentiment.analysis?.neutral_count || 0 }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SentimentResult } from '@/types/financial'

interface Props {
  sentiment: SentimentResult | null
  isLoading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: null,
})

// Get sentiment label in Chinese
function getSentimentLabel(label: string): string {
  const labels: Record<string, string> = {
    bullish: '看多',
    bearish: '看空',
    neutral: '中性',
  }
  return labels[label] || label
}

// Get sentiment CSS class
function getSentimentClass(label: string): string {
  return `sentiment-${label}`
}

// Get source label in Chinese
function getSourceLabel(source: string): string {
  const sources: Record<string, string> = {
    xueqiu: '雪球',
    guba: '股吧',
    eastmoney: '东方财富',
  }
  return sources[source] || source
}

// Calculate score position on the bar (0% to 100%)
function getScorePosition(score: number): string {
  // Score range: -1 to +1
  // Position range: 0% to 100%
  const percentage = ((score + 1) / 2) * 100
  return `${percentage}%`
}

// Distribution data for legend
const distributionData = computed(() => {
  if (!props.sentiment) return []

  const analysis = props.sentiment.analysis
  if (!analysis) return []
  const { bullish_count, bearish_count, neutral_count } = analysis
  const total = bullish_count + bearish_count + neutral_count

  return [
    {
      label: '看多',
      count: bullish_count,
      percentage: total > 0 ? Math.round((bullish_count / total) * 100) : 0,
      color: '#10b981',
    },
    {
      label: '看空',
      count: bearish_count,
      percentage: total > 0 ? Math.round((bearish_count / total) * 100) : 0,
      color: '#ef4444',
    },
    {
      label: '中性',
      count: neutral_count,
      percentage: total > 0 ? Math.round((neutral_count / total) * 100) : 0,
      color: '#6b7280',
    },
  ]
})

// Pie chart segments
const circumference = 2 * Math.PI * 80 // radius = 80
const pieSegments = computed(() => {
  if (!props.sentiment) return []

  const data = distributionData.value
  let currentOffset = 0

  return data.map((item) => {
    const length = (item.percentage / 100) * circumference
    const segment = {
      color: item.color,
      length,
      offset: -currentOffset,
    }
    currentOffset += length
    return segment
  })
})
</script>

<style scoped>
.sentiment-dashboard {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.data-sources {
  display: flex;
  gap: 0.5rem;
}

.source-tag {
  padding: 0.25rem 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
}

/* Loading State */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  text-align: center;
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

/* Dashboard Content */
.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Score Section */
.score-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.score-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.label-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

.score-value {
  font-size: 1rem;
  font-weight: 600;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
}

.score-value.sentiment-bullish {
  background: #d1fae5;
  color: #065f46;
}

.score-value.sentiment-bearish {
  background: #fee2e2;
  color: #991b1b;
}

.score-value.sentiment-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

/* Progress Bar */
.score-bar-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.score-bar-track {
  position: relative;
  height: 2rem;
  display: flex;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.zone {
  flex: 1;
  height: 100%;
}

.negative-zone {
  background: linear-gradient(to right, #fee2e2, #fef2f2);
}

.neutral-zone {
  background: #f9fafb;
}

.positive-zone {
  background: linear-gradient(to right, #f0fdf4, #d1fae5);
}

.score-indicator {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  transition: left 300ms ease;
}

.indicator-dot {
  width: 1rem;
  height: 1rem;
  border-radius: 50%;
  border: 2px solid #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.sentiment-bullish .indicator-dot {
  background: #10b981;
}

.sentiment-bearish .indicator-dot {
  background: #ef4444;
}

.sentiment-neutral .indicator-dot {
  background: #6b7280;
}

.indicator-label {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 0.125rem 0.5rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  white-space: nowrap;
}

.score-scale {
  display: flex;
  justify-content: space-between;
}

.scale-label {
  font-size: 0.75rem;
  color: #9ca3af;
}

/* Distribution Section */
.distribution-section {
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 1rem 0;
}

.distribution-content {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 2rem;
  align-items: center;
}

.pie-chart {
  width: 200px;
  height: 200px;
}

.pie-svg {
  width: 100%;
  height: 100%;
}

.pie-segment {
  transition: opacity 200ms ease;
}

.pie-segment:hover {
  opacity: 0.8;
}

.pie-center-label {
  font-size: 2rem;
  font-weight: 700;
  fill: #111827;
}

.pie-center-sublabel {
  font-size: 0.875rem;
  fill: #6b7280;
}

.distribution-legend {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.legend-indicator {
  width: 1rem;
  height: 1rem;
  border-radius: 4px;
  flex-shrink: 0;
}

.legend-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}

.legend-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.legend-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.legend-percent {
  font-weight: 400;
  color: #9ca3af;
}

/* Metrics Section */
.metrics-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 200ms ease;
}

.metric-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.metric-icon {
  font-size: 1.5rem;
}

.metric-content {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
}

.metric-value {
  font-size: 1.25rem;
  font-weight: 700;
}

.metric-value.bullish {
  color: #10b981;
}

.metric-value.bearish {
  color: #ef4444;
}

.metric-value.neutral {
  color: #6b7280;
}

/* Responsive */
@media (max-width: 768px) {
  .distribution-content {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .pie-chart {
    margin: 0 auto;
  }

  .metrics-section {
    grid-template-columns: 1fr;
  }
}
</style>
