<template>
  <div class="dupont-factor-item">
    <div class="factor-header">
      <span class="factor-name">{{ factor.name }}</span>
      <span class="factor-value">{{ formatValue() }}</span>
      <span class="factor-percentile" :class="percentileClass">
        TOP {{ factor.percentile.toFixed(0) }}%
      </span>
    </div>
    <div class="factor-bar">
      <div
        class="factor-fill"
        :class="percentileClass"
        :style="{ width: barWidth }"
      />
    </div>
    <p class="factor-description">{{ factor.description }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface DuPontFactor {
  name: string
  value: number
  percentile: number
  trend: string
  description: string
}

const props = withDefaults(
  defineProps<{
    factor: DuPontFactor
    suffix?: string
    decimals?: number
  }>(),
  {
    suffix: '%',
    decimals: 1,
  }
)

const percentileClass = computed(() => {
  const p = props.factor.percentile
  if (p <= 10) return 'top-10'
  if (p <= 30) return 'top-30'
  if (p <= 70) return 'middle'
  return 'bottom'
})

const barWidth = computed(() => {
  // 反转: 分位数越低表示越好, 条越长
  return `${100 - props.factor.percentile}%`
})

function formatValue(): string {
  const value = props.factor.value
  if (value === null || value === undefined) return '-'
  return `${value.toFixed(props.decimals)}${props.suffix}`
}
</script>

<style scoped>
.dupont-factor-item {
  padding: 0.5rem;
  background: var(--any-bg-secondary, rgba(255, 255, 255, 0.02));
  border-radius: 8px;
}

.factor-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.375rem;
}

.factor-name {
  font-size: 0.75rem;
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
}

.factor-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--any-text-primary, #ffffff);
  font-family: 'Space Grotesk', monospace;
}

.factor-percentile {
  margin-left: auto;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
}

.factor-percentile.top-10 {
  background: rgba(0, 255, 136, 0.15);
  color: #00FF88;
}

.factor-percentile.top-30 {
  background: rgba(0, 217, 255, 0.15);
  color: #00D9FF;
}

.factor-percentile.middle {
  background: rgba(255, 255, 255, 0.08);
  color: var(--any-text-secondary, rgba(255, 255, 255, 0.6));
}

.factor-percentile.bottom {
  background: rgba(255, 184, 0, 0.15);
  color: #FFB800;
}

.factor-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 0.375rem;
}

.factor-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.factor-fill.top-10 {
  background: linear-gradient(90deg, #00D9FF, #00FF88);
}

.factor-fill.top-30 {
  background: linear-gradient(90deg, #00A5CC, #00D9FF);
}

.factor-fill.middle {
  background: rgba(255, 255, 255, 0.3);
}

.factor-fill.bottom {
  background: linear-gradient(90deg, #FFB800, #FF8C00);
}

.factor-description {
  margin: 0;
  font-size: 0.6875rem;
  color: var(--any-text-tertiary, rgba(255, 255, 255, 0.5));
}
</style>
