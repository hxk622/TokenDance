<template>
  <div class="financial-test-page">
    <div class="container">
      <header class="page-header">
        <h1>金融分析 - 基础设施测试</h1>
        <p class="subtitle">
          Week 1 交付物验证
        </p>
      </header>

      <!-- Stock Search Component -->
      <section class="test-section">
        <h2>1. 股票搜索组件</h2>
        <StockSearch
          :show-hot-stocks="true"
          @select="handleStockSelect"
        />
      </section>

      <!-- Store State Display -->
      <section class="test-section">
        <h2>2. Pinia Store 状态</h2>
        <div class="state-grid">
          <div class="state-card">
            <h3>当前股票</h3>
            <p>{{ store.currentSymbol || '未选择' }}</p>
          </div>
          <div class="state-card">
            <h3>加载状态</h3>
            <p>{{ store.isLoading ? '加载中...' : '空闲' }}</p>
          </div>
          <div class="state-card">
            <h3>观察列表</h3>
            <p>{{ store.watchList.length }} 只</p>
          </div>
        </div>
      </section>

      <!-- Stock Info Display -->
      <section
        v-if="store.stockInfo"
        class="test-section"
      >
        <h2>3. 股票基本信息</h2>
        <div class="data-card">
          <div class="data-row">
            <span class="label">代码:</span>
            <span class="value">{{ store.stockInfo.symbol }}</span>
          </div>
          <div class="data-row">
            <span class="label">名称:</span>
            <span class="value">{{ store.stockInfo.name }}</span>
          </div>
          <div class="data-row">
            <span class="label">市场:</span>
            <span class="value">{{ store.stockInfo.market }}</span>
          </div>
        </div>
      </section>

      <!-- Stock Quote Display -->
      <section
        v-if="store.stockQuote"
        class="test-section"
      >
        <h2>4. 实时行情</h2>
        <div class="data-card">
          <div class="data-row">
            <span class="label">当前价:</span>
            <span class="value">¥{{ store.stockQuote.current_price }}</span>
          </div>
          <div class="data-row">
            <span class="label">涨跌幅:</span>
            <span
              class="value"
              :class="getChangeClass(store.stockQuote.change_percent)"
            >
              {{ store.stockQuote.change_percent > 0 ? '+' : '' }}{{ store.stockQuote.change_percent }}%
            </span>
          </div>
          <div class="data-row">
            <span class="label">成交量:</span>
            <span class="value">{{ formatVolume(store.stockQuote.volume) }}</span>
          </div>
        </div>
      </section>

      <!-- Sentiment Dashboard -->
      <section class="test-section">
        <h2>5. 情绪仪表盘 - SentimentDashboard</h2>
        <SentimentDashboard
          :sentiment="store.sentimentResult"
          :is-loading="store.sentimentLoading"
          :error="store.sentimentError"
        />
      </section>

      <!-- Post Stream -->
      <section
        v-if="store.sentimentResult"
        class="test-section"
      >
        <h2>6. 帖子流 - PostStream</h2>
        <PostStream
          :posts="store.sentimentResult.posts"
          :is-loading="store.sentimentLoading"
          :error="store.sentimentError"
        />
      </section>

      <!-- Key Points Card -->
      <section class="test-section">
        <h2>7. 核心观点 - KeyPointsCard</h2>
        <KeyPointsCard
          :key-points="mockKeyPoints"
          :is-loading="false"
        />
      </section>

      <!-- Combined Chart -->
      <section
        v-if="store.historicalData"
        class="test-section"
      >
        <h2>8. K线图+舆情 - CombinedChart</h2>
        <CombinedChart
          :historical-data="store.historicalData.records"
          :is-loading="store.historicalLoading"
          :error="store.historicalError"
        />
      </section>

      <!-- Comparison Card -->
      <section class="test-section">
        <h2>9. 技术vs舆情 - ComparisonCard</h2>
        <ComparisonCard
          :stock-info="store.stockInfo"
          :stock-quote="store.stockQuote"
          :sentiment-result="store.sentimentResult"
          :is-loading="store.isLoading"
        />
      </section>

      <!-- API Health Check -->
      <section class="test-section">
        <h2>6. API 健康检查</h2>
        <button
          class="test-button"
          :disabled="testingAPI"
          @click="testAPIHealth"
        >
          {{ testingAPI ? '检查中...' : '测试 API 连接' }}
        </button>
        <p
          v-if="apiStatus"
          class="status-message"
          :class="{ 'is-success': apiStatus.success }"
        >
          {{ apiStatus.message }}
        </p>
      </section>
      <!-- Week 1 + Week 2 Checklist -->
      <section class="test-section">
        <h2>10. 交付清单</h2>
        <div class="checklist">
          <h3 class="checklist-title">
            Week 1: 基础设施
          </h3>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>后端 Financial API（ 7个端点）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>TypeScript 类型定义（137 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>API Service 层（144 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>Pinia Store（407 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>StockSearch 组件（508 lines）</span>
          </div>

          <h3
            class="checklist-title"
            style="margin-top: 1.5rem;"
          >
            Week 2: 可视化组件
          </h3>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>SentimentDashboard（644 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>PostStream（575 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>KeyPointsCard（445 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>CombinedChart（513 lines）</span>
          </div>
          <div class="checklist-item">
            <span class="check">✅</span>
            <span>ComparisonCard（584 lines）</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useFinancialStore } from '@/stores/financial'
import financialService from '@/services/financial'
import StockSearch from '@/components/financial/StockSearch.vue'
import SentimentDashboard from '@/components/financial/SentimentDashboard.vue'
import PostStream from '@/components/financial/PostStream.vue'
import KeyPointsCard from '@/components/financial/KeyPointsCard.vue'
import CombinedChart from '@/components/financial/CombinedChart.vue'
import ComparisonCard from '@/components/financial/ComparisonCard.vue'

const store = useFinancialStore()
const testingAPI = ref(false)
const apiStatus = ref<{ success: boolean; message: string } | null>(null)

// Mock key points data
const mockKeyPoints = ref({
  bullish: [
    {
      content: '公司三季度营收同比增长35%，连续5个季度保持高速增长，市场份额持续扩大',
      summary: '业绩持续高增长',
      supportingPosts: ['post-1', 'post-2', 'post-3']
    },
    {
      content: '新产品线预计Q4上市，市场预期贡献20%增量收入',
      summary: '新产品亮点突出',
      supportingPosts: ['post-4']
    }
  ],
  bearish: [
    {
      content: '行业竞争加剧，主要竞对手降价策略可能影响毛利率',
      summary: '竞争压力增大',
      supportingPosts: ['post-5', 'post-6']
    }
  ]
})

interface StockItem {
  symbol: string
  name: string
  market?: string
}

function handleStockSelect(stock: StockItem) {
  console.log('Selected stock:', stock)
}

async function testAPIHealth() {
  testingAPI.value = true
  apiStatus.value = null

  try {
    const response = await financialService.healthCheck()
    apiStatus.value = {
      success: response.success,
      message: response.success
        ? '✅ API 连接正常'
        : `❌ API 错误: ${response.error}`,
    }
  } catch (error) {
    apiStatus.value = {
      success: false,
      message: `❌ 网络错误: ${error instanceof Error ? error.message : '未知错误'}`,
    }
  } finally {
    testingAPI.value = false
  }
}

function getChangeClass(change: number) {
  if (change > 0) return 'positive'
  if (change < 0) return 'negative'
  return 'neutral'
}

function formatVolume(volume: number) {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`
  }
  return volume.toString()
}

function getSentimentLabel(label: string) {
  const labels: Record<string, string> = {
    bullish: '看多',
    bearish: '看空',
    neutral: '中性',
  }
  return labels[label] || label
}
</script>

<style scoped>
.financial-test-page {
  min-height: 100vh;
  background: #fafafa;
  padding: 2rem 1rem;
}

.container {
  max-width: 56rem;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 3rem;
  text-align: center;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 700;
  color: #111827;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1rem;
  color: #6b7280;
}

.test-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.test-section h2 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1rem;
}

.state-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.state-card {
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.state-card h3 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.state-card p {
  font-size: 1rem;
  color: #111827;
}

.data-card {
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.data-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e5e7eb;
}

.data-row:last-child {
  border-bottom: none;
}

.label {
  font-size: 0.875rem;
  color: #6b7280;
}

.value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
}

.positive {
  color: #10b981 !important;
}

.negative {
  color: #ef4444 !important;
}

.neutral {
  color: #6b7280 !important;
}

.sentiment-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.sentiment-bullish {
  background: #d1fae5;
  color: #065f46;
}

.sentiment-bearish {
  background: #fee2e2;
  color: #991b1b;
}

.sentiment-neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.test-button {
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

.test-button:hover:not(:disabled) {
  background: #1f2937;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.test-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.status-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 8px;
  font-size: 0.875rem;
}

.status-message.is-success {
  background: #d1fae5;
  color: #065f46;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.checklist-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f3f4f6;
}

.checklist-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.check {
  font-size: 1.25rem;
}
</style>
