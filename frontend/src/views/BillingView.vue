<script setup lang="ts">
/**
 * BillingView - 订阅与账单页面
 */
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import { 
  Crown, Sparkles, CreditCard, Receipt, ArrowUpRight, Check, Zap
} from 'lucide-vue-next'

const authStore = useAuthStore()

// Mock pricing plans
const plans = [
  {
    id: 'free',
    name: '免费版',
    price: 0,
    tokens: '100K',
    features: ['每月 100,000 Token', '基础 AI 功能', '社区支持'],
    recommended: false
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 99,
    tokens: '2M',
    features: ['每月 2,000,000 Token', '高级 AI 模型', 'PPT 生成', '优先支持'],
    recommended: true
  },
  {
    id: 'team',
    name: 'Team',
    price: 299,
    tokens: '10M',
    features: ['每月 10,000,000 Token', '团队协作', 'API 访问', '专属客服'],
    recommended: false
  }
]

// Current plan
const currentPlan = computed(() => {
  const tier = authStore.user?.subscription_tier || 'free'
  return plans.find(p => p.id === tier) || plans[0]
})

// Token usage
const tokenUsed = computed(() => authStore.monthlyTokensUsed)
const tokenLimit = computed(() => authStore.maxMonthlyTokens)
const tokenPercent = computed(() => {
  if (tokenLimit.value === 0) return 0
  return Math.round((tokenUsed.value / tokenLimit.value) * 100)
})

// Format numbers
function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`
  return n.toString()
}

// Mock billing history
const billingHistory = [
  { id: '1', date: '2024-01-01', amount: 99, status: 'paid', description: 'Pro 订阅 - 1月' },
  { id: '2', date: '2023-12-01', amount: 99, status: 'paid', description: 'Pro 订阅 - 12月' },
  { id: '3', date: '2023-11-01', amount: 99, status: 'paid', description: 'Pro 订阅 - 11月' },
]

// Methods
function handleUpgrade(planId: string) {
  console.log('Upgrade to:', planId)
  // TODO: Open payment modal
}

function handleBuyTokens() {
  console.log('Buy additional tokens')
  // TODO: Open token purchase modal
}
</script>

<template>
  <div class="billing-page">
    <AnyHeader />
    <AnySidebar />
    
    <main class="billing-main">
      <div class="billing-container">
        <h1 class="page-title">
          订阅与账单
        </h1>

        <!-- Current Plan Card -->
        <div class="current-plan-card">
          <div class="plan-header">
            <div class="plan-info">
              <div class="plan-badge">
                <Crown class="w-4 h-4" />
                <span>{{ currentPlan.name }}</span>
              </div>
              <p class="plan-desc">
                当前订阅计划
              </p>
            </div>
            <button
              v-if="currentPlan.id !== 'team'"
              class="upgrade-btn"
              @click="handleUpgrade('pro')"
            >
              <Zap class="w-4 h-4" />
              <span>升级计划</span>
            </button>
          </div>

          <!-- Token Usage -->
          <div class="token-usage">
            <div class="usage-header">
              <div class="usage-label">
                <Sparkles class="w-4 h-4" />
                <span>本月 Token 用量</span>
              </div>
              <span class="usage-value">
                {{ formatNumber(tokenUsed) }} / {{ formatNumber(tokenLimit) }}
              </span>
            </div>
            <div class="usage-bar">
              <div
                class="usage-fill"
                :style="{ width: `${tokenPercent}%` }"
                :class="{ warning: tokenPercent > 80, danger: tokenPercent > 95 }"
              />
            </div>
            <div class="usage-footer">
              <span class="usage-percent">已使用 {{ tokenPercent }}%</span>
              <button
                class="buy-tokens-btn"
                @click="handleBuyTokens"
              >
                <ArrowUpRight class="w-3.5 h-3.5" />
                <span>购买更多</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Pricing Plans -->
        <div class="plans-section">
          <h2 class="section-title">
            选择计划
          </h2>
          <div class="plans-grid">
            <div
              v-for="plan in plans"
              :key="plan.id"
              :class="['plan-card', { 
                current: plan.id === currentPlan.id,
                recommended: plan.recommended 
              }]"
            >
              <div
                v-if="plan.recommended"
                class="recommended-badge"
              >
                推荐
              </div>
              <h3 class="plan-name">
                {{ plan.name }}
              </h3>
              <div class="plan-price">
                <span class="price-amount">¥{{ plan.price }}</span>
                <span class="price-period">/月</span>
              </div>
              <div class="plan-tokens">
                {{ plan.tokens }} Token/月
              </div>
              <ul class="plan-features">
                <li
                  v-for="feature in plan.features"
                  :key="feature"
                >
                  <Check class="w-4 h-4" />
                  <span>{{ feature }}</span>
                </li>
              </ul>
              <button
                v-if="plan.id !== currentPlan.id"
                class="plan-btn"
                :class="{ primary: plan.recommended }"
                @click="handleUpgrade(plan.id)"
              >
                {{ plan.price > currentPlan.price ? '升级' : '切换' }}
              </button>
              <div
                v-else
                class="current-badge"
              >
                当前计划
              </div>
            </div>
          </div>
        </div>

        <!-- Billing History -->
        <div class="history-section">
          <h2 class="section-title">
            账单历史
          </h2>
          <div class="history-list">
            <div
              v-for="item in billingHistory"
              :key="item.id"
              class="history-item"
            >
              <div class="history-icon">
                <Receipt class="w-4 h-4" />
              </div>
              <div class="history-info">
                <span class="history-desc">{{ item.description }}</span>
                <span class="history-date">{{ item.date }}</span>
              </div>
              <div class="history-amount">
                <span class="amount">¥{{ item.amount }}</span>
                <span class="status paid">已支付</span>
              </div>
            </div>
            <div
              v-if="billingHistory.length === 0"
              class="empty-history"
            >
              暂无账单记录
            </div>
          </div>
        </div>

        <!-- Payment Method -->
        <div class="payment-section">
          <h2 class="section-title">
            支付方式
          </h2>
          <div class="payment-card">
            <div class="card-info">
              <CreditCard class="w-5 h-5" />
              <span>尚未绑定支付方式</span>
            </div>
            <button class="add-card-btn">
              添加银行卡
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.billing-page {
  min-height: 100vh;
  background: var(--any-bg-primary);
}

.billing-main {
  margin-left: var(--sidebar-width);
  padding: 80px 24px 40px;
}

.billing-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0 0 16px;
}

/* Current Plan Card */
.current-plan-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 32px;
}

.plan-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.plan-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #FFB800, #FF9500);
  color: white;
  font-weight: 600;
  border-radius: 8px;
}

.plan-desc {
  font-size: 13px;
  color: var(--any-text-muted);
  margin: 8px 0 0;
}

.upgrade-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: var(--td-state-thinking);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.upgrade-btn:hover {
  opacity: 0.9;
}

/* Token Usage */
.token-usage {
  background: var(--any-bg-tertiary);
  border-radius: 12px;
  padding: 16px;
}

.usage-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.usage-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--any-text-secondary);
}

.usage-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.usage-bar {
  height: 8px;
  background: var(--any-bg-primary);
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: linear-gradient(90deg, #00D9FF, #00FF88);
  border-radius: 4px;
  transition: width 300ms ease;
}

.usage-fill.warning {
  background: linear-gradient(90deg, #FFB800, #FF9500);
}

.usage-fill.danger {
  background: linear-gradient(90deg, #FF6B6B, #FF3B30);
}

.usage-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.usage-percent {
  font-size: 13px;
  color: var(--any-text-muted);
}

.buy-tokens-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--td-state-thinking);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: opacity 150ms ease;
}

.buy-tokens-btn:hover {
  opacity: 0.8;
}

/* Plans Grid */
.plans-section {
  margin-bottom: 32px;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.plan-card {
  position: relative;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
}

.plan-card.current {
  border-color: var(--td-state-thinking);
}

.plan-card.recommended {
  border-color: #FFB800;
  box-shadow: 0 4px 20px rgba(255, 184, 0, 0.15);
}

.recommended-badge {
  position: absolute;
  top: -10px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  color: white;
  background: #FFB800;
  border-radius: 12px;
}

.plan-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0 0 12px;
}

.plan-price {
  margin-bottom: 8px;
}

.price-amount {
  font-size: 32px;
  font-weight: 700;
  color: var(--any-text-primary);
}

.price-period {
  font-size: 14px;
  color: var(--any-text-muted);
}

.plan-tokens {
  font-size: 14px;
  color: var(--td-state-thinking);
  font-weight: 500;
  margin-bottom: 20px;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
  text-align: left;
}

.plan-features li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
  color: var(--any-text-secondary);
}

.plan-features li svg {
  color: var(--any-success, #22c55e);
  flex-shrink: 0;
}

.plan-btn {
  width: 100%;
  padding: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.plan-btn:hover {
  background: var(--any-bg-hover);
}

.plan-btn.primary {
  color: white;
  background: var(--td-state-thinking);
  border-color: var(--td-state-thinking);
}

.plan-btn.primary:hover {
  opacity: 0.9;
}

.current-badge {
  padding: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-muted);
  background: var(--any-bg-tertiary);
  border-radius: 8px;
}

/* History */
.history-section {
  margin-bottom: 32px;
}

.history-list {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  overflow: hidden;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.history-item:last-child {
  border-bottom: none;
}

.history-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  color: var(--any-text-secondary);
}

.history-info {
  flex: 1;
}

.history-desc {
  display: block;
  font-size: 14px;
  color: var(--any-text-primary);
}

.history-date {
  font-size: 12px;
  color: var(--any-text-muted);
}

.history-amount {
  text-align: right;
}

.amount {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
}

.status.paid {
  color: var(--any-success, #22c55e);
  background: rgba(34, 197, 94, 0.1);
}

.empty-history {
  padding: 40px;
  text-align: center;
  color: var(--any-text-muted);
}

/* Payment */
.payment-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  padding: 20px;
}

.card-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--any-text-secondary);
}

.add-card-btn {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.add-card-btn:hover {
  background: var(--any-bg-hover);
}

/* Responsive */
@media (max-width: 1024px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .billing-main {
    margin-left: 0;
    padding: 72px 16px 24px;
  }

  .plan-header {
    flex-direction: column;
    gap: 16px;
  }

  .upgrade-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
