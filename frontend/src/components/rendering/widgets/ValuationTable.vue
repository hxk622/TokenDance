<script setup lang="ts">
/**
 * 估值表格组件
 * Valuation Table - Display financial valuation metrics
 */

import { computed } from 'vue'
import type { ValuationTableProps, ValuationRow } from '../types'

// Props
const props = withDefaults(defineProps<ValuationTableProps>(), {
  showComparison: true,
  highlightBest: true,
})

// Rating colors
const ratingColors: Record<string, { bg: string; text: string; label: string }> = {
  undervalued: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: '低估' },
  fair: { bg: 'bg-gray-50', text: 'text-gray-600', label: '合理' },
  overvalued: { bg: 'bg-red-50', text: 'text-red-700', label: '高估' },
}

// Format value
function formatValue(value: number | string | undefined): string {
  if (value === undefined || value === null) return '-'
  if (typeof value === 'string') return value
  
  if (Math.abs(value) >= 1e9) return `${(value / 1e9).toFixed(2)}B`
  if (Math.abs(value) >= 1e6) return `${(value / 1e6).toFixed(2)}M`
  if (Math.abs(value) >= 1e3) return `${(value / 1e3).toFixed(2)}K`
  if (Number.isInteger(value)) return value.toLocaleString()
  return value.toFixed(2)
}

// Check if current value is better than comparison
function isBetterValue(row: ValuationRow): boolean {
  if (!props.highlightBest) return false
  if (typeof row.current !== 'number') return false
  
  const metric = row.metric.toLowerCase()
  const current = row.current as number
  const industry = row.industry as number | undefined
  
  if (industry === undefined) return false
  
  // For P/E, P/B, EV/EBITDA - lower is better
  if (metric.includes('p/e') || metric.includes('p/b') || metric.includes('ev/')) {
    return current < industry
  }
  
  // For margins, ROE, ROA - higher is better
  if (metric.includes('margin') || metric.includes('roe') || metric.includes('roa')) {
    return current > industry
  }
  
  return false
}
</script>

<template>
  <div class="valuation-table-wrapper">
    <!-- Title -->
    <h3
      v-if="title"
      class="table-title"
    >
      {{ title }}
    </h3>
    
    <!-- Table -->
    <div class="table-container">
      <table class="valuation-table">
        <thead>
          <tr>
            <th class="metric-col">
              指标
            </th>
            <th class="value-col">
              当前值
            </th>
            <th
              v-if="showComparison"
              class="value-col"
            >
              行业平均
            </th>
            <th
              v-if="showComparison"
              class="value-col"
            >
              历史均值
            </th>
            <th class="rating-col">
              评级
            </th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="row in data" 
            :key="row.metric"
            :class="{ 'highlight-row': isBetterValue(row) }"
          >
            <td class="metric-col">
              <span class="metric-name">{{ row.metric }}</span>
              <span
                v-if="row.description"
                class="metric-desc"
              >{{ row.description }}</span>
            </td>
            <td class="value-col">
              <span 
                class="value"
                :class="{ 'is-better': isBetterValue(row) }"
              >
                {{ formatValue(row.current) }}
              </span>
            </td>
            <td
              v-if="showComparison"
              class="value-col"
            >
              <span class="value secondary">{{ formatValue(row.industry) }}</span>
            </td>
            <td
              v-if="showComparison"
              class="value-col"
            >
              <span class="value secondary">{{ formatValue(row.historical) }}</span>
            </td>
            <td class="rating-col">
              <span 
                v-if="row.rating"
                class="rating-badge"
                :class="[ratingColors[row.rating].bg, ratingColors[row.rating].text]"
              >
                {{ ratingColors[row.rating].label }}
              </span>
              <span
                v-else
                class="rating-badge bg-gray-50 text-gray-400"
              >-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.valuation-table-wrapper {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
}

.table-title {
  font-size: 1rem;
  font-weight: 600;
  color: #111827;
  padding: 1rem 1.25rem;
  margin: 0;
  border-bottom: 1px solid #f3f4f6;
}

.table-container {
  overflow-x: auto;
}

.valuation-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.valuation-table th {
  text-align: left;
  font-weight: 500;
  color: #6b7280;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
  white-space: nowrap;
}

.valuation-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  vertical-align: top;
}

.valuation-table tbody tr:last-child td {
  border-bottom: none;
}

.valuation-table tbody tr:hover {
  background: #fafafa;
}

/* Columns */
.metric-col {
  min-width: 150px;
}

.value-col {
  min-width: 100px;
  text-align: right;
}

.rating-col {
  min-width: 80px;
  text-align: center;
}

/* Metric cell */
.metric-name {
  display: block;
  font-weight: 500;
  color: #111827;
}

.metric-desc {
  display: block;
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 2px;
}

/* Value cell */
.value {
  font-weight: 500;
  color: #111827;
  font-variant-numeric: tabular-nums;
}

.value.secondary {
  color: #6b7280;
  font-weight: 400;
}

.value.is-better {
  color: #059669;
}

/* Rating badge */
.rating-badge {
  display: inline-block;
  padding: 0.25rem 0.625rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

/* Highlight row */
.highlight-row {
  background: #f0fdf4;
}

.highlight-row:hover {
  background: #dcfce7;
}

/* Dark theme */
:global(.theme-dark) .valuation-table-wrapper {
  background: #1f2937;
  border-color: #374151;
}

:global(.theme-dark) .table-title {
  color: #f9fafb;
  border-bottom-color: #374151;
}

:global(.theme-dark) .valuation-table th {
  color: #9ca3af;
  background: #111827;
  border-bottom-color: #374151;
}

:global(.theme-dark) .valuation-table td {
  border-bottom-color: #374151;
}

:global(.theme-dark) .valuation-table tbody tr:hover {
  background: #374151;
}

:global(.theme-dark) .metric-name {
  color: #f9fafb;
}

:global(.theme-dark) .value {
  color: #f9fafb;
}

:global(.theme-dark) .value.secondary {
  color: #9ca3af;
}
</style>
