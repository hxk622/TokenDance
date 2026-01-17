<template>
  <div class="post-stream">
    <!-- Header with filters -->
    <div class="stream-header">
      <h3 class="title">讨论帖子</h3>
      
      <div class="filter-controls">
        <button
          v-for="filter in filters"
          :key="filter.value"
          class="filter-button"
          :class="{ 'is-active': activeFilter === filter.value }"
          @click="activeFilter = filter.value"
        >
          {{ filter.label }}
          <span v-if="getFilterCount(filter.value) > 0" class="filter-count">
            {{ getFilterCount(filter.value) }}
          </span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <p>加载帖子中...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="!posts || posts.length === 0" class="empty-state">
      <div class="empty-icon">💬</div>
      <p>暂无讨论帖子</p>
      <p class="hint">选择股票后将显示相关讨论</p>
    </div>

    <!-- Post Cards -->
    <div v-else class="post-grid">
      <div
        v-for="post in filteredPosts"
        :key="post.post_id || post.id"
        class="post-card"
      >
        <!-- Post header -->
        <div class="post-header">
          <div class="post-author">
            <div class="author-avatar">
              {{ getInitial(post.author) }}
            </div>
            <div class="author-info">
              <span class="author-name">{{ post.author }}</span>
              <span class="post-time">{{ formatTime(post.timestamp || '') }}</span>
            </div>
          </div>
          
          <div class="sentiment-badge" :class="`sentiment-${post.sentiment || post.sentiment_label || 'neutral'}`">
            {{ getSentimentLabel(post.sentiment || post.sentiment_label || 'neutral') }}
          </div>
        </div>

        <!-- Post content -->
        <div class="post-content">
          <p class="post-text" :class="{ 'is-expanded': expandedPosts.has(post.post_id || post.id) }">
            {{ post.content }}
          </p>
          <button
            v-if="post.content.length > 200"
            class="expand-button"
            @click="toggleExpand(post.post_id || post.id)"
          >
            {{ expandedPosts.has(post.post_id || post.id) ? '收起' : '展开' }}
          </button>
        </div>

        <!-- Post footer -->
        <div class="post-footer">
          <div class="post-metrics">
            <div class="metric">
              <span class="metric-icon">👍</span>
              <span class="metric-value">{{ post.likes || 0 }}</span>
            </div>
            <div class="metric">
              <span class="metric-icon">💬</span>
              <span class="metric-value">{{ post.comments || 0 }}</span>
            </div>
          </div>
          
          <a
            v-if="post.url"
            :href="post.url"
            target="_blank"
            rel="noopener noreferrer"
            class="source-link"
          >
            查看原文 →
          </a>
        </div>
      </div>
    </div>

    <!-- Load more indicator (for future pagination) -->
    <div v-if="filteredPosts.length > 0 && filteredPosts.length < posts.length" class="load-more">
      <button class="load-more-button" @click="loadMore">
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { SentimentPost } from '@/types/financial'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

interface Props {
  posts: SentimentPost[]
  isLoading?: boolean
  error?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: null,
})

// Active filter
const activeFilter = ref<string>('all')

// Expanded posts
const expandedPosts = ref<Set<string>>(new Set())

// Filter options
const filters = [
  { label: '全部', value: 'all' },
  { label: '看多', value: 'bullish' },
  { label: '看空', value: 'bearish' },
  { label: '中性', value: 'neutral' },
  { label: '高赞', value: 'popular' },
]

// Get initial letter for avatar
function getInitial(name: string): string {
  return name ? name.charAt(0).toUpperCase() : '?'
}

// Format timestamp
function formatTime(timestamp: string | null): string {
  if (!timestamp) return '未知时间'
  return dayjs(timestamp).fromNow()
}

// Get sentiment label
function getSentimentLabel(sentiment?: string): string {
  const labels: Record<string, string> = {
    bullish: '看多',
    bearish: '看空',
    neutral: '中性',
  }
  return sentiment ? (labels[sentiment] || sentiment) : '未知'
}

// Toggle expand/collapse
function toggleExpand(postId: string) {
  if (expandedPosts.value.has(postId)) {
    expandedPosts.value.delete(postId)
  } else {
    expandedPosts.value.add(postId)
  }
}

// Get filter count
function getFilterCount(filter: string): number {
  if (!props.posts) return 0
  
  const getSentiment = (p: SentimentPost) => p.sentiment || p.sentiment_label
  
  switch (filter) {
    case 'all':
      return props.posts.length
    case 'bullish':
      return props.posts.filter(p => getSentiment(p) === 'bullish').length
    case 'bearish':
      return props.posts.filter(p => getSentiment(p) === 'bearish').length
    case 'neutral':
      return props.posts.filter(p => getSentiment(p) === 'neutral').length
    case 'popular':
      return props.posts.filter(p => (p.likes || 0) >= 10).length
    default:
      return 0
  }
}

// Filtered posts
const filteredPosts = computed(() => {
  if (!props.posts) return []
  
  let filtered = [...props.posts]
  
  switch (activeFilter.value) {
    case 'bullish':
      filtered = filtered.filter(p => p.sentiment === 'bullish')
      break
    case 'bearish':
      filtered = filtered.filter(p => p.sentiment === 'bearish')
      break
    case 'neutral':
      filtered = filtered.filter(p => p.sentiment === 'neutral')
      break
    case 'popular':
      filtered = filtered.filter(p => (p.likes || 0) >= 10)
      break
  }
  
  return filtered
})

// Load more (placeholder)
function loadMore() {
  // Future: implement pagination
  console.log('Load more posts')
}
</script>

<style scoped>
.post-stream {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.stream-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
  flex-wrap: wrap;
  gap: 1rem;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.filter-controls {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 200ms ease;
}

.filter-button:hover {
  border-color: #d1d5db;
  background: #ffffff;
}

.filter-button.is-active {
  background: #111827;
  border-color: #111827;
  color: #ffffff;
}

.filter-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.375rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.filter-button.is-active .filter-count {
  background: rgba(255, 255, 255, 0.2);
  color: #ffffff;
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

/* Post Grid */
.post-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1rem;
}

.post-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 200ms ease;
}

.post-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Post Header */
.post-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.post-author {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
}

.author-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: #111827;
  color: #ffffff;
  border-radius: 50%;
  font-size: 1rem;
  font-weight: 600;
  flex-shrink: 0;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.author-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-time {
  font-size: 0.75rem;
  color: #9ca3af;
}

.sentiment-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
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

/* Post Content */
.post-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.post-text {
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-text.is-expanded {
  display: block;
  -webkit-line-clamp: unset;
}

.expand-button {
  align-self: flex-start;
  padding: 0.25rem 0.75rem;
  background: transparent;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 200ms ease;
}

.expand-button:hover {
  border-color: #d1d5db;
  color: #111827;
}

/* Post Footer */
.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.post-metrics {
  display: flex;
  gap: 1rem;
}

.metric {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.metric-icon {
  font-size: 1rem;
}

.metric-value {
  font-weight: 500;
}

.source-link {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  text-decoration: none;
  transition: color 200ms ease;
}

.source-link:hover {
  color: #111827;
}

/* Load More */
.load-more {
  display: flex;
  justify-content: center;
  padding-top: 1.5rem;
  margin-top: 1.5rem;
  border-top: 1px solid #f3f4f6;
}

.load-more-button {
  padding: 0.75rem 1.5rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 200ms ease;
}

.load-more-button:hover {
  background: #ffffff;
  border-color: #d1d5db;
  color: #111827;
}

/* Responsive */
@media (max-width: 768px) {
  .stream-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .post-grid {
    grid-template-columns: 1fr;
  }
}
</style>
