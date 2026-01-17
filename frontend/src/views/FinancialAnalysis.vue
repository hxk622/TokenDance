<template>
  <div class="financial-analysis-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">投研工作台</h1>
          <p class="page-subtitle">AI 辅助的金融投资研究分析</p>
        </div>
        
        <div class="header-right">
          <StockSearch
            placeholder="搜索股票代码或名称..."
            :show-hot-stocks="false"
            @select="handleStockSelect"
            class="header-search"
          />
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Left Column: Stock Info + Chart -->
      <div class="column-left">
        <!-- Stock Header Card -->
        <div v-if="store.stockInfo" class="stock-header-card">
          <div class="stock-basic">
            <div class="stock-name-row">
              <h2 class="stock-name">{{ store.stockInfo.name }}</h2>
              <span class="stock-symbol">{{ store.stockInfo.symbol }}</span>
              <span class="stock-market">{{ store.stockInfo.market }}</span>
            </div>
            
            <div v-if="store.stockQuote" class="stock-price-row">
              <span class="current-price" :class="getPriceClass(store.stockQuote.change_percent)">
                ¥{{ store.stockQuote.current_price?.toFixed(2) }}
              </span>
              <span class="price-change" :class="getPriceClass(store.stockQuote.change_percent)">
                {{ store.stockQuote.change_percent > 0 ? '+' : '' }}{{ store.stockQuote.change_percent?.toFixed(2) }}%
              </span>
              <span class="price-amount" :class="getPriceClass(store.stockQuote.change_percent)">
                {{ store.stockQuote.change_amount > 0 ? '+' : '' }}{{ store.stockQuote.change_amount?.toFixed(2) }}
              </span>
            </div>
          </div>
          
          <div class="stock-actions">
            <button 
              class="action-button"
              :class="{ 'is-active': isInWatchList }"
              @click="toggleWatchList"
            >
              {{ isInWatchList ? '已关注' : '加自选' }}
            </button>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-stock-card">
          <div class="empty-icon">🔍</div>
          <p class="empty-title">选择一只股票开始分析</p>
          <p class="empty-hint">在上方搜索框输入股票代码或名称</p>
          
          <div class="quick-picks">
            <p class="quick-picks-label">热门推荐</p>
            <div class="quick-picks-grid">
              <button
                v-for="stock in hotStocks"
                :key="stock.symbol"
                class="quick-pick-button"
                @click="selectStock(stock)"
              >
                {{ stock.name }}
              </button>
            </div>
          </div>
        </div>

        <!-- K-Line Chart -->
        <CombinedChart
          v-if="store.stockInfo"
          :historical-data="store.historicalData || []"
          :is-loading="store.historicalLoading"
          :error="store.historicalError"
        />

        <!-- Comparison Card -->
        <ComparisonCard
          v-if="store.stockInfo"
          :stock-info="store.stockInfo"
          :stock-quote="store.stockQuote"
          :sentiment-result="store.sentimentResult"
          :is-loading="store.isLoading"
        />
        
        <!-- 分析引擎区域 -->
        <div v-if="store.stockInfo" class="analysis-engine-section">
          <div class="analysis-header">
            <h3 class="analysis-title">🧠 AI 分析引擎</h3>
            <button
              class="analyze-button"
              :disabled="isAnalyzing"
              @click="runAnalysis"
            >
              {{ isAnalyzing ? '分析中...' : '一键分析' }}
            </button>
          </div>
          
          <!-- 分析结果卡片 -->
          <div class="analysis-cards">
            <FinancialAnalysisCard
              :result="store.financialAnalysis"
              :is-loading="store.loadingFinancialAnalysis"
              :error="store.financialAnalysisError"
            />
            
            <ValuationCard
              :result="store.valuationAnalysis"
              :is-loading="store.loadingValuationAnalysis"
              :error="store.valuationAnalysisError"
            />
            
            <TechnicalAnalysisCard
              :result="store.technicalAnalysis"
              :is-loading="store.loadingTechnicalAnalysis"
              :error="store.technicalAnalysisError"
            />
          </div>
        </div>
      </div>

      <!-- Right Column: Sentiment Analysis -->
      <div class="column-right">
        <!-- Sentiment Dashboard -->
        <SentimentDashboard
          :sentiment="store.sentimentResult"
          :is-loading="store.sentimentLoading"
          :error="store.sentimentError"
        />

        <!-- Key Points -->
        <KeyPointsCard
          :key-points="keyPoints"
          :is-loading="store.sentimentLoading"
        />

        <!-- Post Stream -->
        <PostStream
          :posts="store.sentimentResult?.posts || []"
          :is-loading="store.sentimentLoading"
          :error="store.sentimentError"
        />
        
        <!-- AI 研究助手 -->
        <ResearchAssistant
          :symbol="store.stockInfo?.symbol"
          :stock-name="store.stockInfo?.name"
          :stock-info="store.stockInfo"
          :analysis-results="{
            financial: store.financialAnalysis,
            valuation: store.valuationAnalysis,
            technical: store.technicalAnalysis,
          }"
          @ask="handleAssistantAsk"
        />
      </div>
    </main>

    <!-- Footer -->
    <footer class="page-footer">
      <p class="footer-text">随时接管 · 实时干预 · 沉淀复用</p>
      <p class="footer-disclaimer">
        数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useFinancialStore } from '@/stores/financial'
import StockSearch from '@/components/financial/StockSearch.vue'
import SentimentDashboard from '@/components/financial/SentimentDashboard.vue'
import PostStream from '@/components/financial/PostStream.vue'
import KeyPointsCard from '@/components/financial/KeyPointsCard.vue'
import CombinedChart from '@/components/financial/CombinedChart.vue'
import ComparisonCard from '@/components/financial/ComparisonCard.vue'
import FinancialAnalysisCard from '@/components/financial/FinancialAnalysisCard.vue'
import ValuationCard from '@/components/financial/ValuationCard.vue'
import TechnicalAnalysisCard from '@/components/financial/TechnicalAnalysisCard.vue'
import ResearchAssistant from '@/components/financial/ResearchAssistant.vue'

const store = useFinancialStore()

// Hot stocks for quick selection
const hotStocks = [
  { symbol: '600519', name: '贵州茅台', market: 'SH' },
  { symbol: '000858', name: '五粮液', market: 'SZ' },
  { symbol: '601318', name: '中国平安', market: 'SH' },
  { symbol: '600036', name: '招商银行', market: 'SH' },
  { symbol: '000001', name: '平安银行', market: 'SZ' },
  { symbol: '601888', name: '中国中免', market: 'SH' },
]

// Key points (mock data, would come from AI analysis)
const keyPoints = ref({
  bullish: [] as Array<{ content: string; summary: string; supportingPosts?: string[] }>,
  bearish: [] as Array<{ content: string; summary: string; supportingPosts?: string[] }>,
})

// Check if current stock is in watch list
const isInWatchList = computed(() => {
  if (!store.stockInfo) return false
  return store.watchList.some(s => s.symbol === store.stockInfo?.symbol)
})

// Handle stock selection from search
function handleStockSelect(stock: { symbol: string; name: string }) {
  selectStock(stock)
}

// Select a stock and fetch all data
async function selectStock(stock: { symbol: string; name: string }) {
  store.setCurrentSymbol(stock.symbol)
  await store.fetchCombinedAnalysis(stock.symbol)
  
  // Update key points based on sentiment analysis
  if (store.sentimentResult?.analysis) {
    updateKeyPoints()
  }
}

// Toggle watch list
function toggleWatchList() {
  if (!store.stockInfo) return
  
  if (isInWatchList.value) {
    store.removeFromWatchList(store.stockInfo.symbol)
  } else {
    store.addToWatchList({
      symbol: store.stockInfo.symbol,
      name: store.stockInfo.name,
    })
  }
}

// Get price change CSS class
function getPriceClass(change?: number): string {
  if (!change) return ''
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return ''
}

// Update key points based on sentiment analysis
function updateKeyPoints() {
  // This would be generated by AI in production
  // For now, we create placeholder data
  const sentiment = store.sentimentResult
  if (!sentiment) return

  keyPoints.value = {
    bullish: sentiment.analysis.bullish_count > 0 
      ? [
          {
            content: '市场对该股整体持乐观态度，多数投资者看好后市表现',
            summary: '整体看多情绪占优',
            supportingPosts: sentiment.posts
              .filter(p => p.sentiment === 'bullish')
              .slice(0, 3)
              .map(p => p.post_id),
          },
        ]
      : [],
    bearish: sentiment.analysis.bearish_count > 0
      ? [
          {
            content: '部分投资者对短期走势持谨慎态度，建议关注风险',
            summary: '存在谨慎观点',
            supportingPosts: sentiment.posts
              .filter(p => p.sentiment === 'bearish')
              .slice(0, 3)
              .map(p => p.post_id),
          },
        ]
      : [],
  }
}

// Watch for sentiment changes to update key points
watch(
  () => store.sentimentResult,
  () => {
    if (store.sentimentResult) {
      updateKeyPoints()
    }
  }
)

// 分析引擎
const isAnalyzing = computed(() => {
  return store.loadingComprehensiveAnalysis ||
    store.loadingFinancialAnalysis ||
    store.loadingValuationAnalysis ||
    store.loadingTechnicalAnalysis
})

async function runAnalysis() {
  if (!store.stockInfo?.symbol) return
  await store.runComprehensiveAnalysis(store.stockInfo.symbol)
}

// AI 助手交互
function handleAssistantAsk(question: string) {
  console.log('User asked:', question)
  // 未来可以集成到后端 AI 服务
}
</script>

<style scoped>
.financial-analysis-page {
  min-height: 100vh;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
}

/* Header */
.page-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 1rem 2rem;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1600px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.header-left {
  flex-shrink: 0;
}

.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.25rem 0 0 0;
}

.header-right {
  flex: 1;
  max-width: 500px;
}

.header-search {
  width: 100%;
}

/* Main Content */
.main-content {
  flex: 1;
  max-width: 1600px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
}

.column-left,
.column-right {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Stock Header Card */
.stock-header-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.stock-basic {
  flex: 1;
}

.stock-name-row {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.stock-name {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.stock-symbol {
  font-size: 1rem;
  font-family: monospace;
  color: #6b7280;
}

.stock-market {
  padding: 0.125rem 0.5rem;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
}

.stock-price-row {
  display: flex;
  align-items: baseline;
  gap: 1rem;
}

.current-price {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
}

.price-change,
.price-amount {
  font-size: 1.125rem;
  font-weight: 600;
}

.positive {
  color: #10b981;
}

.negative {
  color: #ef4444;
}

.stock-actions {
  flex-shrink: 0;
}

.action-button {
  padding: 0.75rem 1.5rem;
  background: #111827;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.action-button:hover {
  background: #1f2937;
}

.action-button.is-active {
  background: #10b981;
}

/* Empty Stock Card */
.empty-stock-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.empty-hint {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 2rem 0;
}

.quick-picks {
  border-top: 1px solid #f3f4f6;
  padding-top: 2rem;
}

.quick-picks-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  margin: 0 0 1rem 0;
}

.quick-picks-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.75rem;
}

.quick-pick-button {
  padding: 0.5rem 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 200ms ease;
}

.quick-pick-button:hover {
  background: #ffffff;
  border-color: #d1d5db;
  color: #111827;
}

/* 分析引擎区域 */
.analysis-engine-section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.analysis-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.analyze-button {
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 200ms ease;
}

.analyze-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.analyze-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.analysis-cards {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* Footer */
.page-footer {
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  padding: 1.5rem 2rem;
  text-align: center;
}

.footer-text {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 0.5rem 0;
}

.footer-disclaimer {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
}

/* Responsive */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .column-right {
    order: -1;
  }
}

@media (max-width: 768px) {
  .page-header {
    padding: 1rem;
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 1rem;
  }

  .header-right {
    max-width: none;
  }

  .main-content {
    padding: 1rem;
  }

  .stock-header-card {
    flex-direction: column;
  }

  .stock-actions {
    width: 100%;
  }

  .action-button {
    width: 100%;
  }
}
</style>
