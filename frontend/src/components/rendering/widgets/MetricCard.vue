<script setup lang="ts">
/**
 * 指标卡片组件
 * Metric Card - Display key financial/research metrics
 */

import { computed } from 'vue'
import type { MetricCardProps } from '../types'

// Props
const props = withDefaults(defineProps<MetricCardProps>(), {
  changeType: 'neutral',
  size: 'md',
})

// Computed classes
const sizeClasses = computed(() => ({
  sm: 'card-sm',
  md: 'card-md',
  lg: 'card-lg',
}[props.size]))

const changeColor = computed(() => ({
  positive: 'text-emerald-600',
  negative: 'text-red-500',
  neutral: 'text-gray-500',
}[props.changeType]))

const changeBgColor = computed(() => ({
  positive: 'bg-emerald-50',
  negative: 'bg-red-50',
  neutral: 'bg-gray-50',
}[props.changeType]))

// Format value
const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    if (props.value >= 1e9) return `${(props.value / 1e9).toFixed(2)}B`
    if (props.value >= 1e6) return `${(props.value / 1e6).toFixed(2)}M`
    if (props.value >= 1e3) return `${(props.value / 1e3).toFixed(2)}K`
    return props.value.toLocaleString()
  }
  return props.value
})

// Format change
const formattedChange = computed(() => {
  if (props.change === undefined) return null
  const sign = props.change >= 0 ? '+' : ''
  return `${sign}${props.change.toFixed(2)}%`
})

// Mini sparkline path (if trend data provided)
const sparklinePath = computed(() => {
  if (!props.trend || props.trend.length < 2) return null
  
  const width = 60
  const height = 24
  const padding = 2
  
  const min = Math.min(...props.trend)
  const max = Math.max(...props.trend)
  const range = max - min || 1
  
  const points = props.trend.map((value, index) => {
    const x = padding + (index / (props.trend!.length - 1)) * (width - padding * 2)
    const y = height - padding - ((value - min) / range) * (height - padding * 2)
    return `${x},${y}`
  })
  
  return `M ${points.join(' L ')}`
})

const sparklineColor = computed(() => {
  if (!props.trend || props.trend.length < 2) return '#6b7280'
  return props.trend[props.trend.length - 1] >= props.trend[0] ? '#10b981' : '#ef4444'
})
</script>

<template>
  <div class="metric-card" :class="sizeClasses">
    <!-- Header -->
    <div class="card-header">
      <div v-if="icon" class="card-icon">
        <component :is="icon" v-if="typeof icon === 'object'" />
        <span v-else>{{ icon }}</span>
      </div>
      <span class="card-title">{{ title }}</span>
    </div>
    
    <!-- Value -->
    <div class="card-value-row">
      <span class="card-value">
        {{ formattedValue }}
        <span v-if="unit" class="card-unit">{{ unit }}</span>
      </span>
      
      <!-- Change Badge -->
      <span 
        v-if="formattedChange" 
        class="change-badge"
        :class="[changeColor, changeBgColor]"
      >
        <svg 
          v-if="changeType === 'positive'" 
          class="change-icon" 
          viewBox="0 0 20 20" 
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M10 17a.75.75 0 01-.75-.75V5.612L5.29 9.77a.75.75 0 01-1.08-1.04l5.25-5.5a.75.75 0 011.08 0l5.25 5.5a.75.75 0 11-1.08 1.04l-3.96-4.158V16.25A.75.75 0 0110 17z" clip-rule="evenodd"/>
        </svg>
        <svg 
          v-else-if="changeType === 'negative'" 
          class="change-icon" 
          viewBox="0 0 20 20" 
          fill="currentColor"
        >
          <path fill-rule="evenodd" d="M10 3a.75.75 0 01.75.75v10.638l3.96-4.158a.75.75 0 111.08 1.04l-5.25 5.5a.75.75 0 01-1.08 0l-5.25-5.5a.75.75 0 111.08-1.04l3.96 4.158V3.75A.75.75 0 0110 3z" clip-rule="evenodd"/>
        </svg>
        {{ formattedChange }}
      </span>
    </div>
    
    <!-- Sparkline -->
    <svg v-if="sparklinePath" class="sparkline" viewBox="0 0 60 24">
      <path 
        :d="sparklinePath" 
        fill="none" 
        :stroke="sparklineColor" 
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    
    <!-- Description -->
    <p v-if="description" class="card-description">{{ description }}</p>
  </div>
</template>

<style scoped>
.metric-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

/* Size variants */
.card-sm {
  padding: 0.75rem;
}

.card-md {
  padding: 1rem;
}

.card-lg {
  padding: 1.25rem;
}

.card-sm .card-value { font-size: 1.25rem; }
.card-md .card-value { font-size: 1.5rem; }
.card-lg .card-value { font-size: 1.875rem; }

/* Header */
.card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.card-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #6b7280;
}

.card-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
}

/* Value row */
.card-value-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
}

.card-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  line-height: 1.2;
}

.card-unit {
  font-size: 0.875rem;
  font-weight: 400;
  color: #6b7280;
  margin-left: 0.25rem;
}

/* Change badge */
.change-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.change-icon {
  width: 0.875rem;
  height: 0.875rem;
}

/* Sparkline */
.sparkline {
  width: 100%;
  height: 24px;
  margin-top: 0.25rem;
}

/* Description */
.card-description {
  font-size: 0.75rem;
  color: #9ca3af;
  margin: 0;
  line-height: 1.4;
}

/* Dark theme support */
:global(.theme-dark) .metric-card {
  background: #1f2937;
  border-color: #374151;
}

:global(.theme-dark) .card-title {
  color: #9ca3af;
}

:global(.theme-dark) .card-value {
  color: #f9fafb;
}

:global(.theme-dark) .card-unit {
  color: #9ca3af;
}
</style>
