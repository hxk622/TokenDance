<script setup lang="ts">
/**
 * 渲染引擎演示页面
 * Rendering Engine Demo - Showcasing Deep Research & Financial Research
 */

import { ref, onMounted } from 'vue'
import { 
  DynamicRenderer, 
  KLineChart, 
  MetricCard, 
  ValuationTable, 
  SourceCitation,
  ScrollyContainer,
  ScrollySection,
  registerBuiltInComponents,
  type KLineDataItem,
  type ValuationRow,
  type SourceItem,
} from '@/components/rendering'

// Register components on mount
onMounted(() => {
  registerBuiltInComponents()
})

// Demo mode toggle
const activeTab = ref<'deep-research' | 'financial'>('financial')

// ============================================================================
// Financial Research Demo Data
// ============================================================================

// Generate mock K-line data
const klineData = ref<KLineDataItem[]>(generateKLineData(100))

function generateKLineData(days: number): KLineDataItem[] {
  const data: KLineDataItem[] = []
  let basePrice = 150
  const now = Date.now()
  
  for (let i = days; i >= 0; i--) {
    const timestamp = now - i * 24 * 60 * 60 * 1000
    const change = (Math.random() - 0.48) * 5
    const open = basePrice
    const close = basePrice + change
    const high = Math.max(open, close) + Math.random() * 2
    const low = Math.min(open, close) - Math.random() * 2
    const volume = Math.floor(Math.random() * 10000000) + 5000000
    
    data.push({ timestamp, open, high, low, close, volume })
    basePrice = close
  }
  
  return data
}

// Valuation data
const valuationData: ValuationRow[] = [
  { metric: 'P/E (TTM)', current: 28.5, industry: 32.1, historical: 25.3, rating: 'fair', description: '市盈率' },
  { metric: 'P/B', current: 4.2, industry: 5.8, historical: 3.9, rating: 'undervalued', description: '市净率' },
  { metric: 'EV/EBITDA', current: 18.3, industry: 22.5, historical: 16.8, rating: 'fair' },
  { metric: 'ROE', current: 24.5, industry: 18.2, historical: 22.1, rating: 'undervalued', description: '净资产收益率' },
  { metric: 'Gross Margin', current: 42.3, industry: 38.5, historical: 40.1, rating: 'undervalued', description: '毛利率' },
  { metric: 'Net Margin', current: 21.8, industry: 15.3, historical: 19.5, rating: 'undervalued', description: '净利率' },
]

// Source data
const financialSources: SourceItem[] = [
  { id: '1', title: 'Apple Inc. 10-K Annual Report', url: 'https://investor.apple.com', author: 'SEC Filings', date: '2024-11-01', reliability: 'high' },
  { id: '2', title: 'Goldman Sachs Equity Research', author: 'Goldman Sachs', date: '2024-12-15', reliability: 'high' },
  { id: '3', title: 'Bloomberg Terminal Data', url: 'https://bloomberg.com', reliability: 'high' },
]

// ============================================================================
// Deep Research Demo Data
// ============================================================================

const deepResearchContent = ref(`
# 人工智能在医疗领域的应用研究

## 研究背景

人工智能（AI）技术正在深刻改变医疗健康行业。从疾病诊断到药物研发，AI的应用正在加速医学进步。

:::MetricCard{title="全球AI医疗市场规模" value="187.9" unit="亿美元" change=24.5 changeType="positive"}
:::

## 主要应用领域

### 1. 医学影像诊断

AI在医学影像诊断中展现出巨大潜力：

- **准确率**: 在某些领域已超越人类医生
- **效率提升**: 诊断时间减少 60-80%
- **成本降低**: 单次诊断成本降低约 40%

### 2. 药物研发

AI正在革新药物研发流程：

:::MetricCard{title="研发周期缩短" value="30-50" unit="%" changeType="positive"}
:::

### 3. 个性化医疗

基于基因组学和大数据的个性化治疗方案正在成为可能。

## 面临的挑战

1. **数据隐私**: 医疗数据的安全性和合规性
2. **监管框架**: 缺乏统一的AI医疗产品审批标准
3. **医患信任**: 如何建立对AI诊断的信任

## 结论

AI医疗的发展前景广阔，但需要在技术进步、监管完善和伦理考量之间找到平衡。
`)

const deepResearchSources: SourceItem[] = [
  { id: '1', title: 'Nature Medicine: AI in Healthcare', url: 'https://nature.com', author: 'Nature Publishing', date: '2024-10-15', reliability: 'high', snippet: '系统性综述了AI在医疗领域的最新进展' },
  { id: '2', title: 'WHO AI Ethics Guidelines', url: 'https://who.int', author: 'World Health Organization', date: '2024-06-01', reliability: 'high' },
  { id: '3', title: 'McKinsey Healthcare Report 2024', author: 'McKinsey & Company', date: '2024-09-20', reliability: 'medium' },
]

// Scrolly section handler
function handleSectionChange(data: { current: string; previous: string | null }) {
  console.log('Section changed:', data)
}
</script>

<template>
  <div class="rendering-demo">
    <!-- Header -->
    <div class="demo-header">
      <h1 class="demo-title">
        下一代渲染引擎演示
      </h1>
      <p class="demo-subtitle">
        Next-Gen Rendering Engine Demo
      </p>
      
      <!-- Tab Switcher -->
      <div class="tab-switcher">
        <button 
          class="tab-btn"
          :class="{ active: activeTab === 'financial' }"
          @click="activeTab = 'financial'"
        >
          投研分析报告
        </button>
        <button 
          class="tab-btn"
          :class="{ active: activeTab === 'deep-research' }"
          @click="activeTab = 'deep-research'"
        >
          Deep Research
        </button>
      </div>
    </div>

    <!-- Financial Research Demo -->
    <div
      v-if="activeTab === 'financial'"
      class="demo-content"
    >
      <div class="section">
        <h2 class="section-title">
          苹果公司 (AAPL) 投资分析报告
        </h2>
        
        <!-- Metrics Row -->
        <div class="metrics-grid">
          <MetricCard 
            title="股价" 
            :value="189.95" 
            unit="USD" 
            :change="2.35"
            change-type="positive"
            :trend="[175, 178, 182, 180, 185, 188, 190]"
          />
          <MetricCard 
            title="市值" 
            :value="2950000000000" 
            unit="USD"
            :change="1.2"
            change-type="positive"
          />
          <MetricCard 
            title="PE (TTM)" 
            :value="28.5" 
            :change="-3.2"
            change-type="negative"
          />
          <MetricCard 
            title="股息率" 
            :value="0.52" 
            unit="%"
            change-type="neutral"
          />
        </div>
      </div>

      <!-- K-Line Chart -->
      <div class="section">
        <h3 class="section-subtitle">
          价格走势 (专业K线图表)
        </h3>
        <KLineChart 
          :data="klineData"
          symbol="AAPL"
          period="1d"
          theme="light"
          :height="500"
          :show-volume="true"
        />
      </div>

      <!-- Valuation Table -->
      <div class="section">
        <ValuationTable 
          title="估值指标对比"
          :data="valuationData"
          :show-comparison="true"
          :highlight-best="true"
        />
      </div>

      <!-- Sources -->
      <div class="section">
        <SourceCitation 
          :sources="financialSources"
          citation-style="footnote"
          :show-reliability="true"
        />
      </div>
    </div>

    <!-- Deep Research Demo -->
    <div
      v-if="activeTab === 'deep-research'"
      class="demo-content"
    >
      <ScrollyContainer 
        :sticky-content="true"
        :progress-bar="true"
        progress-position="right"
        sticky-width="40%"
        content-width="55%"
        @section-change="handleSectionChange"
      >
        <!-- Sticky Content (Chart/Visual) -->
        <template #sticky="{ activeSection }">
          <div class="sticky-visual">
            <div class="visual-card">
              <h3 class="visual-title">
                当前章节: {{ activeSection || '开始阅读' }}
              </h3>
              <div class="visual-placeholder">
                <div class="placeholder-icon">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.5"
                  >
                    <path d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25" />
                  </svg>
                </div>
                <p>滚动右侧内容，这里会显示对应的可视化</p>
              </div>
            </div>
          </div>
        </template>

        <!-- Scrolling Content -->
        <template #default="{ onSectionEnter, onSectionLeave }">
          <ScrollySection 
            id="intro" 
            title="研究概述"
            animation="slide"
            @enter="onSectionEnter"
            @leave="onSectionLeave"
          >
            <DynamicRenderer 
              :content="deepResearchContent"
              :context="{ theme: 'light' }"
            />
          </ScrollySection>

          <ScrollySection 
            id="sources" 
            title="参考来源"
            animation="fade"
            @enter="onSectionEnter"
            @leave="onSectionLeave"
          >
            <SourceCitation 
              :sources="deepResearchSources"
              citation-style="sidebar"
              :show-reliability="true"
            />
          </ScrollySection>
        </template>
      </ScrollyContainer>
    </div>
  </div>
</template>

<style scoped>
.rendering-demo {
  min-height: 100vh;
  background: #fafafa;
}

.demo-header {
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  padding: 2rem;
  text-align: center;
}

.demo-title {
  font-size: 1.875rem;
  font-weight: 700;
  color: #111827;
  margin: 0 0 0.5rem;
}

.demo-subtitle {
  font-size: 1rem;
  color: #6b7280;
  margin: 0 0 1.5rem;
}

.tab-switcher {
  display: inline-flex;
  background: #f3f4f6;
  border-radius: 8px;
  padding: 4px;
}

.tab-btn {
  padding: 0.5rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 200ms ease;
}

.tab-btn:hover {
  color: #374151;
}

.tab-btn.active {
  background: #ffffff;
  color: #111827;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.demo-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.section {
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 1.5rem;
}

.section-subtitle {
  font-size: 1.125rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 1rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

/* Sticky visual */
.sticky-visual {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.visual-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 2rem;
  width: 100%;
  max-width: 400px;
}

.visual-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  margin: 0 0 1rem;
  text-align: center;
}

.visual-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: #f9fafb;
  border-radius: 8px;
  text-align: center;
}

.placeholder-icon {
  width: 48px;
  height: 48px;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.placeholder-icon svg {
  width: 100%;
  height: 100%;
}

.visual-placeholder p {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .demo-content {
    padding: 1rem;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>
