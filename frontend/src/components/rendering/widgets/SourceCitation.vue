<script setup lang="ts">
/**
 * 来源引用组件
 * Source Citation - Display research sources and references
 */

import { computed } from 'vue'
import type { SourceCitationProps, SourceItem } from '../types'

// Props
const props = withDefaults(defineProps<SourceCitationProps>(), {
  citationStyle: 'inline',
  showReliability: true,
})

// Reliability indicator
const reliabilityConfig: Record<string, { color: string; label: string; icon: string }> = {
  high: { color: 'text-emerald-600', label: '高可信度', icon: '●' },
  medium: { color: 'text-amber-500', label: '中等可信度', icon: '◐' },
  low: { color: 'text-red-500', label: '低可信度', icon: '○' },
}

// Format date
function formatDate(dateStr?: string): string {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}
</script>

<template>
  <div
    class="source-citation"
    :class="[`style-${citationStyle}`]"
  >
    <!-- Inline Style -->
    <template v-if="citationStyle === 'inline'">
      <div class="inline-sources">
        <span class="sources-label">来源:</span>
        <span 
          v-for="(source, index) in sources" 
          :key="source.id"
          class="inline-source"
        >
          <a 
            v-if="source.url" 
            :href="source.url" 
            target="_blank" 
            rel="noopener noreferrer"
            class="source-link"
          >
            [{{ index + 1 }}] {{ source.title }}
          </a>
          <span
            v-else
            class="source-text"
          >[{{ index + 1 }}] {{ source.title }}</span>
          <span 
            v-if="showReliability && source.reliability" 
            class="reliability-dot"
            :class="reliabilityConfig[source.reliability].color"
            :title="reliabilityConfig[source.reliability].label"
          >
            {{ reliabilityConfig[source.reliability].icon }}
          </span>
          <span
            v-if="index < sources.length - 1"
            class="separator"
          >,</span>
        </span>
      </div>
    </template>

    <!-- Footnote Style -->
    <template v-else-if="citationStyle === 'footnote'">
      <div class="footnote-sources">
        <div class="footnote-header">
          <svg
            class="footnote-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <span class="footnote-title">参考来源</span>
        </div>
        <ol class="footnote-list">
          <li 
            v-for="source in sources" 
            :key="source.id"
            class="footnote-item"
          >
            <div class="footnote-content">
              <a 
                v-if="source.url" 
                :href="source.url" 
                target="_blank" 
                rel="noopener noreferrer"
                class="source-link"
              >
                {{ source.title }}
              </a>
              <span
                v-else
                class="source-text"
              >{{ source.title }}</span>
              
              <span
                v-if="source.author"
                class="source-meta"
              >— {{ source.author }}</span>
              <span
                v-if="source.date"
                class="source-meta"
              >({{ formatDate(source.date) }})</span>
              
              <span 
                v-if="showReliability && source.reliability" 
                class="reliability-badge"
                :class="reliabilityConfig[source.reliability].color"
              >
                {{ reliabilityConfig[source.reliability].label }}
              </span>
            </div>
            
            <p
              v-if="source.snippet"
              class="source-snippet"
            >
              {{ source.snippet }}
            </p>
          </li>
        </ol>
      </div>
    </template>

    <!-- Sidebar Style -->
    <template v-else-if="citationStyle === 'sidebar'">
      <div class="sidebar-sources">
        <div class="sidebar-header">
          <span class="sidebar-title">相关来源</span>
          <span class="sidebar-count">{{ sources.length }}</span>
        </div>
        <div class="sidebar-list">
          <div 
            v-for="source in sources" 
            :key="source.id"
            class="sidebar-item"
          >
            <div class="sidebar-item-header">
              <span 
                v-if="showReliability && source.reliability" 
                class="reliability-indicator"
                :class="reliabilityConfig[source.reliability].color"
              >
                {{ reliabilityConfig[source.reliability].icon }}
              </span>
              <a 
                v-if="source.url" 
                :href="source.url" 
                target="_blank" 
                rel="noopener noreferrer"
                class="sidebar-link"
              >
                {{ source.title }}
              </a>
              <span
                v-else
                class="sidebar-text"
              >{{ source.title }}</span>
            </div>
            
            <div
              v-if="source.author || source.date"
              class="sidebar-meta"
            >
              <span v-if="source.author">{{ source.author }}</span>
              <span v-if="source.author && source.date"> · </span>
              <span v-if="source.date">{{ formatDate(source.date) }}</span>
            </div>
            
            <p
              v-if="source.snippet"
              class="sidebar-snippet"
            >
              {{ source.snippet }}
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.source-citation {
  font-size: 0.875rem;
}

/* Inline Style */
.inline-sources {
  display: inline;
  color: #6b7280;
}

.sources-label {
  font-weight: 500;
  margin-right: 0.5rem;
}

.inline-source {
  display: inline;
}

.source-link {
  color: #4f46e5;
  text-decoration: none;
}

.source-link:hover {
  text-decoration: underline;
}

.source-text {
  color: #374151;
}

.reliability-dot {
  margin-left: 0.25rem;
  font-size: 0.625rem;
  vertical-align: middle;
}

.separator {
  margin-right: 0.375rem;
}

/* Footnote Style */
.footnote-sources {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.footnote-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.footnote-icon {
  width: 1.25rem;
  height: 1.25rem;
  color: #6b7280;
}

.footnote-title {
  font-weight: 600;
  color: #111827;
}

.footnote-list {
  margin: 0;
  padding-left: 1.5rem;
  list-style-type: decimal;
}

.footnote-item {
  margin-bottom: 0.75rem;
  color: #374151;
}

.footnote-content {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.375rem;
}

.source-meta {
  color: #9ca3af;
  font-size: 0.75rem;
}

.reliability-badge {
  font-size: 0.625rem;
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  background: #f3f4f6;
}

.source-snippet {
  margin: 0.375rem 0 0;
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  line-height: 1.5;
}

/* Sidebar Style */
.sidebar-sources {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.sidebar-title {
  font-weight: 600;
  color: #111827;
}

.sidebar-count {
  background: #e5e7eb;
  color: #6b7280;
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
}

.sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.sidebar-item {
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.sidebar-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.sidebar-item-header {
  display: flex;
  align-items: center;
  gap: 0.375rem;
}

.reliability-indicator {
  font-size: 0.625rem;
}

.sidebar-link {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
}

.sidebar-link:hover {
  text-decoration: underline;
}

.sidebar-text {
  color: #111827;
  font-weight: 500;
}

.sidebar-meta {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-top: 0.25rem;
}

.sidebar-snippet {
  margin: 0.375rem 0 0;
  font-size: 0.75rem;
  color: #6b7280;
  line-height: 1.4;
}

/* Dark theme */
:global(.theme-dark) .inline-sources {
  color: #9ca3af;
}

:global(.theme-dark) .source-text {
  color: #d1d5db;
}

:global(.theme-dark) .footnote-sources {
  border-top-color: #374151;
}

:global(.theme-dark) .footnote-title {
  color: #f9fafb;
}

:global(.theme-dark) .footnote-item {
  color: #d1d5db;
}

:global(.theme-dark) .reliability-badge {
  background: #374151;
}

:global(.theme-dark) .sidebar-sources {
  background: #1f2937;
  border-color: #374151;
}

:global(.theme-dark) .sidebar-title {
  color: #f9fafb;
}

:global(.theme-dark) .sidebar-count {
  background: #374151;
  color: #9ca3af;
}

:global(.theme-dark) .sidebar-item {
  border-bottom-color: #374151;
}

:global(.theme-dark) .sidebar-text {
  color: #f9fafb;
}
</style>
