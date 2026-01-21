<script setup lang="ts">
/**
 * SmartAdviceCard - 智能深度建议卡片
 * 
 * 基于信息饱和度检测，显示研究深度建议
 */
import { computed } from 'vue'
import {
  Lightbulb,
  TrendingUp,
  Target,
  Pause,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Gauge,
  Sparkles,
} from 'lucide-vue-next'

// Types
type SaturationLevel = 'low' | 'medium' | 'high' | 'saturated'
type AdviceAction = 'continue' | 'continue_focused' | 'consider_stop' | 'stop'

interface SaturationMetrics {
  total_findings: number
  unique_points: number
  duplicate_rate: number
  new_info_rate: number
  coverage_score: number
  quality_score: number
  saturation_level: SaturationLevel
  confidence: number
}

interface DepthAdvice {
  action: AdviceAction
  current_depth: number
  suggested_depth?: number
  saturation: SaturationMetrics
  reason: string
  focus_suggestions: string[]
  estimated_new_info: number
}

// Props
const props = withDefaults(defineProps<{
  advice: DepthAdvice | null
  loading?: boolean
  compact?: boolean
}>(), {
  loading: false,
  compact: false,
})

// Emits
const emit = defineEmits<{
  (e: 'accept', suggestedDepth: number): void
  (e: 'continue'): void
  (e: 'stop'): void
  (e: 'focus', suggestion: string): void
}>()

// Computed
const actionConfig = computed(() => {
  if (!props.advice) return null
  
  const configs: Record<AdviceAction, {
    icon: any
    title: string
    color: string
    bgColor: string
  }> = {
    continue: {
      icon: TrendingUp,
      title: '继续深入研究',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    continue_focused: {
      icon: Target,
      title: '聚焦方向研究',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    consider_stop: {
      icon: Pause,
      title: '考虑结束研究',
      color: 'text-amber-500',
      bgColor: 'bg-amber-500/10',
    },
    stop: {
      icon: CheckCircle,
      title: '信息已饱和',
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
    },
  }
  
  return configs[props.advice.action]
})

const saturationColor = computed(() => {
  if (!props.advice) return 'var(--any-text-muted)'
  
  const colors: Record<SaturationLevel, string> = {
    low: '#22c55e',      // green
    medium: '#3b82f6',   // blue
    high: '#f59e0b',     // amber
    saturated: '#10b981', // emerald
  }
  
  return colors[props.advice.saturation.saturation_level]
})

const saturationPercent = computed(() => {
  if (!props.advice) return 0
  
  const percentages: Record<SaturationLevel, number> = {
    low: 25,
    medium: 50,
    high: 75,
    saturated: 100,
  }
  
  return percentages[props.advice.saturation.saturation_level]
})

// Methods
const handleAccept = () => {
  if (props.advice?.suggested_depth) {
    emit('accept', props.advice.suggested_depth)
  }
}

const handleContinue = () => {
  emit('continue')
}

const handleStop = () => {
  emit('stop')
}

const handleFocus = (suggestion: string) => {
  emit('focus', suggestion)
}

const formatPercent = (value: number) => {
  return `${Math.round(value * 100)}%`
}
</script>

<template>
  <div 
    class="smart-advice-card"
    :class="{ 'smart-advice-card--compact': compact }"
  >
    <!-- Header -->
    <div class="card-header">
      <div class="header-left">
        <Lightbulb class="w-4 h-4 text-[var(--exec-accent)]" />
        <span class="header-title">智能建议</span>
      </div>
      <span 
        v-if="advice"
        class="confidence-badge"
        :title="`置信度: ${formatPercent(advice.saturation.confidence)}`"
      >
        <Sparkles class="w-3 h-3" />
        {{ formatPercent(advice.saturation.confidence) }}
      </span>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <div class="spinner" />
      <span>分析中...</span>
    </div>

    <!-- No Advice -->
    <div
      v-else-if="!advice"
      class="empty-state"
    >
      <AlertCircle class="w-5 h-5" />
      <span>数据不足，暂无建议</span>
    </div>

    <!-- Advice Content -->
    <div
      v-else
      class="card-content"
    >
      <!-- Action Header -->
      <div 
        class="action-header"
        :class="actionConfig?.bgColor"
      >
        <component 
          :is="actionConfig?.icon"
          class="w-5 h-5"
          :class="actionConfig?.color"
        />
        <span
          class="action-title"
          :class="actionConfig?.color"
        >
          {{ actionConfig?.title }}
        </span>
      </div>

      <!-- Reason -->
      <p class="advice-reason">
        {{ advice.reason }}
      </p>

      <!-- Saturation Progress -->
      <div class="saturation-section">
        <div class="saturation-header">
          <Gauge class="w-4 h-4" />
          <span>信息饱和度</span>
          <span class="saturation-value">{{ saturationPercent }}%</span>
        </div>
        <div class="saturation-bar">
          <div 
            class="saturation-fill"
            :style="{ 
              width: `${saturationPercent}%`,
              backgroundColor: saturationColor,
            }"
          />
        </div>
      </div>

      <!-- Metrics (collapsed in compact mode) -->
      <div
        v-if="!compact"
        class="metrics-grid"
      >
        <div class="metric-item">
          <span class="metric-label">新信息率</span>
          <span class="metric-value">{{ formatPercent(advice.saturation.new_info_rate) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">覆盖度</span>
          <span class="metric-value">{{ formatPercent(advice.saturation.coverage_score) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">重复率</span>
          <span class="metric-value">{{ formatPercent(advice.saturation.duplicate_rate) }}</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">质量分</span>
          <span class="metric-value">{{ formatPercent(advice.saturation.quality_score) }}</span>
        </div>
      </div>

      <!-- Focus Suggestions -->
      <div 
        v-if="advice.focus_suggestions.length && advice.action !== 'stop'"
        class="focus-section"
      >
        <span class="focus-label">建议方向</span>
        <div class="focus-list">
          <button
            v-for="(suggestion, idx) in advice.focus_suggestions"
            :key="idx"
            class="focus-item"
            @click="handleFocus(suggestion)"
          >
            <Target class="w-3.5 h-3.5" />
            <span>{{ suggestion }}</span>
            <ArrowRight class="w-3.5 h-3.5 arrow" />
          </button>
        </div>
      </div>

      <!-- Actions -->
      <div class="card-actions">
        <template v-if="advice.action === 'stop'">
          <button
            class="primary-btn"
            @click="handleStop"
          >
            <CheckCircle class="w-4 h-4" />
            完成研究
          </button>
        </template>

        <template v-else-if="advice.action === 'consider_stop'">
          <button
            class="secondary-btn"
            @click="handleContinue"
          >
            继续研究
          </button>
          <button
            class="primary-btn"
            @click="handleStop"
          >
            结束研究
          </button>
        </template>

        <template v-else>
          <button 
            v-if="advice.suggested_depth"
            class="primary-btn"
            @click="handleAccept"
          >
            <TrendingUp class="w-4 h-4" />
            调整至 {{ advice.suggested_depth }} 条
          </button>
          <button
            class="secondary-btn"
            @click="handleContinue"
          >
            保持当前设置
          </button>
        </template>
      </div>

      <!-- Estimated New Info -->
      <div class="estimated-info">
        继续研究预计可获得 <strong>{{ formatPercent(advice.estimated_new_info) }}</strong> 新信息
      </div>
    </div>
  </div>
</template>

<style scoped>
.smart-advice-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.confidence-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-full);
  font-size: 11px;
  color: var(--any-text-muted);
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: var(--any-text-muted);
  font-size: 13px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--any-border);
  border-top-color: var(--exec-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.card-content {
  padding: 16px;
}

.action-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: var(--any-radius-md);
  margin-bottom: 12px;
}

.action-title {
  font-size: 14px;
  font-weight: 600;
}

.advice-reason {
  font-size: 13px;
  line-height: 1.6;
  color: var(--any-text-secondary);
  margin: 0 0 16px 0;
}

.saturation-section {
  margin-bottom: 16px;
}

.saturation-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--any-text-muted);
}

.saturation-value {
  margin-left: auto;
  font-weight: 600;
  color: var(--any-text-primary);
}

.saturation-bar {
  height: 6px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-full);
  overflow: hidden;
}

.saturation-fill {
  height: 100%;
  border-radius: var(--any-radius-full);
  transition: width 0.5s ease;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 10px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
}

.metric-label {
  font-size: 11px;
  color: var(--any-text-muted);
}

.metric-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.focus-section {
  margin-bottom: 16px;
}

.focus-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: var(--any-text-muted);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.focus-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.focus-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 12px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.focus-item:hover {
  border-color: var(--exec-accent);
  color: var(--exec-accent);
}

.focus-item .arrow {
  margin-left: auto;
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.focus-item:hover .arrow {
  opacity: 1;
  transform: translateX(0);
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.primary-btn,
.secondary-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: var(--any-radius-md);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.primary-btn {
  background: var(--exec-accent);
  color: var(--any-bg-primary);
}

.primary-btn:hover {
  filter: brightness(1.1);
}

.secondary-btn {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  color: var(--any-text-secondary);
}

.secondary-btn:hover {
  border-color: var(--any-border-hover);
}

.estimated-info {
  text-align: center;
  font-size: 11px;
  color: var(--any-text-muted);
}

.estimated-info strong {
  color: var(--exec-accent);
}

/* Compact Mode */
.smart-advice-card--compact .card-content {
  padding: 12px;
}

.smart-advice-card--compact .metrics-grid {
  display: none;
}

.smart-advice-card--compact .focus-section {
  display: none;
}

.smart-advice-card--compact .action-header {
  padding: 8px 10px;
  margin-bottom: 8px;
}

.smart-advice-card--compact .advice-reason {
  font-size: 12px;
  margin-bottom: 12px;
}

.smart-advice-card--compact .card-actions {
  margin-bottom: 8px;
}

.smart-advice-card--compact .primary-btn,
.smart-advice-card--compact .secondary-btn {
  padding: 8px 12px;
  font-size: 12px;
}
</style>
