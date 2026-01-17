<template>
  <div class="comparison-card">
    <!-- Header -->
    <div class="card-header">
      <h3 class="title">技术面 vs 舆情面</h3>
      <span v-if="stockInfo && sentimentResult" class="sync-indicator">
        <span class="sync-dot"></span>
        实时同步
      </span>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载对比数据中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!stockInfo && !sentimentResult" class="empty-state">
      <div class="empty-icon">⚖️</div>
      <p>暂无对比数据</p>
      <p class="hint">选择股票后显示技术面与舆情面对比</p>
    </div>

    <!-- Comparison Content -->
    <div v-else class="comparison-content">
      <!-- Technical Side -->
      <div class="comparison-side technical">
        <div class="side-header">
          <h4 class="side-title">技术面</h4>
        </div>

        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-label">当前价</div>
            <div class="metric-value" :class="getPriceChangeClass(stockQuote?.change_percent || 0)">
              ¥{{ stockQuote?.current_price?.toFixed(2) || '--' }}
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">涨跌幅</div>
            <div class="metric-value" :class="getPriceChangeClass(stockQuote?.change_percent || 0)">
              {{ stockQuote?.change_percent ? (stockQuote.change_percent > 0 ? '+' : '') + stockQuote.change_percent.toFixed(2) : '--' }}%
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">市值</div>
            <div class="metric-value">
              {{ formatMarketCap(stockInfo?.market_cap) }}
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">换手率</div>
            <div class="metric-value">
              {{ stockQuote?.turnover_rate?.toFixed(2) || '--' }}%
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">成交量</div>
            <div class="metric-value">
              {{ formatVolume(stockQuote?.volume) }}
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">市盈率</div>
            <div class="metric-value">
              {{ stockInfo?.pe_ratio?.toFixed(2) || '--' }}
            </div>
          </div>
        </div>
      </div>

      <!-- Divider -->
      <div class="comparison-divider">
        <div class="divider-line"></div>
        <div class="divider-icon">⚡</div>
        <div class="divider-line"></div>
      </div>

      <!-- Sentiment Side -->
      <div class="comparison-side sentiment">
        <div class="side-header">
          <div class="side-icon">💬</div>
          <h4 class="side-title">舆情面</h4>
        </div>

        <div class="metrics-grid">
          <div class="metric-item">
            <div class="metric-label">整体情绪</div>
            <div class="metric-value">
              <span 
                class="sentiment-badge" 
                :class="`sentiment-${sentimentResult?.analysis?.overall_label || 'neutral'}`"
              >
                {{ getSentimentLabel(sentimentResult?.analysis?.overall_label) }}
              </span>
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">情绪评分</div>
            <div class="metric-value" :class="getSentimentScoreClass(sentimentResult?.analysis?.overall_score || 0)">
              {{ sentimentResult?.analysis?.overall_score?.toFixed(2) || '--' }}
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">讨论数</div>
            <div class="metric-value">
              {{ sentimentResult?.posts.length || 0 }} 条
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">看多占比</div>
            <div class="metric-value positive">
              {{ getBullishPercentage() }}%
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">看空占比</div>
            <div class="metric-value negative">
              {{ getBearishPercentage() }}%
            </div>
          </div>

          <div class="metric-item">
            <div class="metric-label">数据源</div>
            <div class="metric-value">
              <div class="source-tags">
                <span 
                  v-for="source in sentimentResult?.sources_used || []" 
                  :key="source"
                  class="source-tag"
                >
                  {{ getSourceLabel(source) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Alignment Indicator -->
    <div v-if="stockInfo && sentimentResult" class="alignment-indicator">
      <div class="alignment-label">技术面与舆情面一致性</div>
      <div class="alignment-bar">
        <div class="alignment-fill" :style="{ width: `${getAlignment()}%` }"></div>
      </div>
      <div class="alignment-text">{{ getAlignmentLabel() }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Note: computed is available via Vue's template compiler
import { } from 'vue'
import type { StockInfo, StockQuote, SentimentResult } from '@/types/financial'

interface Props {
  stockInfo: StockInfo | null
  stockQuote: StockQuote | null
  sentimentResult: SentimentResult | null
  isLoading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: null,
})

// Get price change class
function getPriceChangeClass(change: number): string {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

// Get sentiment score class
function getSentimentScoreClass(score: number): string {
  if (score > 0.2) return 'positive'
  if (score < -0.2) return 'negative'
  return 'neutral'
}

// Get sentiment label
function getSentimentLabel(label?: string): string {
  const labels: Record<string, string> = {
    bullish: '看多',
    bearish: '看空',
    neutral: '中性',
  }
  return label ? labels[label] || label : '--'
}

// Get source label
function getSourceLabel(source: string): string {
  const sources: Record<string, string> = {
    xueqiu: '雪球',
    guba: '股吧',
    eastmoney: '东方财富',
  }
  return sources[source] || source
}

// Format market cap
function formatMarketCap(cap?: string | number): string {
  if (!cap) return '--'
  const numCap = typeof cap === 'string' ? parseFloat(cap) : cap
  if (isNaN(numCap)) return cap.toString()
  if (numCap >= 1e12) return `${(numCap / 1e12).toFixed(2)}万亿`
  if (numCap >= 1e8) return `${(numCap / 1e8).toFixed(2)}亿`
  if (numCap >= 1e4) return `${(numCap / 1e4).toFixed(2)}万`
  return numCap.toString()
}

// Format volume
function formatVolume(volume?: number): string {
  if (!volume) return '--'
  if (volume >= 1e8) return `${(volume / 1e8).toFixed(2)}亿`
  if (volume >= 1e4) return `${(volume / 1e4).toFixed(2)}万`
  return volume.toString()
}

// Get bullish percentage
function getBullishPercentage(): number {
  if (!props.sentimentResult?.analysis) return 0
  const { bullish_count, bearish_count, neutral_count } = props.sentimentResult.analysis
  const total = bullish_count + bearish_count + neutral_count
  return total > 0 ? Math.round((bullish_count / total) * 100) : 0
}

// Get bearish percentage
function getBearishPercentage(): number {
  if (!props.sentimentResult?.analysis) return 0
  const { bullish_count, bearish_count, neutral_count } = props.sentimentResult.analysis
  const total = bullish_count + bearish_count + neutral_count
  return total > 0 ? Math.round((bearish_count / total) * 100) : 0
}

// Calculate alignment between technical and sentiment
function getAlignment(): number {
  if (!props.stockQuote || !props.sentimentResult) return 50

  const priceChange = props.stockQuote.change_percent || 0
  const sentimentScore = props.sentimentResult.analysis?.overall_score || 0

  // Both positive or both negative = high alignment
  if ((priceChange > 0 && sentimentScore > 0) || (priceChange < 0 && sentimentScore < 0)) {
    return 80
  }
  // Opposite directions = low alignment
  if ((priceChange > 0 && sentimentScore < 0) || (priceChange < 0 && sentimentScore > 0)) {
    return 20
  }
  // Neutral = medium alignment
  return 50
}

// Get alignment label
function getAlignmentLabel(): string {
  const alignment = getAlignment()
  if (alignment >= 70) return '高度一致'
  if (alignment >= 50) return '基本一致'
  return '存在分歧'
}
</script>

<style scoped>
.comparison-card {
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
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.sync-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.sync-dot {
  width: 0.5rem;
  height: 0.5rem;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
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

/* Comparison Content */
.comparison-content {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 2rem;
  align-items: start;
}

.comparison-side {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.side-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.side-icon {
  font-size: 1.5rem;
}

.side-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.metric-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 200ms ease;
}

.metric-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.metric-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.metric-value {
  font-size: 1.125rem;
  font-weight: 700;
  color: #111827;
}

.metric-value.positive {
  color: #10b981;
}

.metric-value.negative {
  color: #ef4444;
}

.metric-value.neutral {
  color: #6b7280;
}

.sentiment-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 600;
}

.sentiment-badge.sentiment-bullish {
  background: #d1fae5;
  color: #065f46;
}

.sentiment-badge.sentiment-bearish {
  background: #fee2e2;
  color: #991b1b;
}

.sentiment-badge.sentiment-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
}

.source-tag {
  padding: 0.125rem 0.5rem;
  background: #e5e7eb;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #374151;
}

/* Comparison Divider */
.comparison-divider {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding-top: 3rem;
}

.divider-line {
  width: 1px;
  flex: 1;
  background: #e5e7eb;
}

.divider-icon {
  font-size: 1.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 50%;
}

/* Alignment Indicator */
.alignment-indicator {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-top: 1.5rem;
  margin-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.alignment-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

.alignment-bar {
  height: 0.5rem;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.alignment-fill {
  height: 100%;
  background: linear-gradient(to right, #ef4444, #fbbf24, #10b981);
  border-radius: 4px;
  transition: width 300ms ease;
}

.alignment-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  text-align: center;
}

/* Responsive */
@media (max-width: 1024px) {
  .comparison-content {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .comparison-divider {
    flex-direction: row;
    padding-top: 0;
  }

  .divider-line {
    width: auto;
    height: 1px;
    flex: 1;
  }

  .metrics-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
