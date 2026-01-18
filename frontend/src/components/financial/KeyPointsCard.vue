<template>
  <div class="key-points-card">
    <!-- Header -->
    <div class="card-header">
      <h3 class="title">
        核心观点
      </h3>
      <span
        v-if="keyPoints"
        class="points-count"
      >
        {{ keyPoints.bullish.length + keyPoints.bearish.length }} 条
      </span>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>提取核心观点中...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="error-state"
    >
      <AlertTriangle class="error-icon w-8 h-8 text-warning" />
      <p>{{ error }}</p>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="!keyPoints || (keyPoints.bullish.length === 0 && keyPoints.bearish.length === 0)"
      class="empty-state"
    >
      <Lightbulb class="empty-icon w-8 h-8 text-gray-400" />
      <p>暂无核心观点</p>
      <p class="hint">
        AI 将自动提取帖子中的关键论据
      </p>
    </div>

    <!-- Key Points Content -->
    <div
      v-else
      class="points-content"
    >
      <!-- Bullish Points -->
      <div
        v-if="keyPoints.bullish.length > 0"
        class="points-section"
      >
        <div class="section-header bullish">
          <TrendingUp class="section-icon w-5 h-5 text-green-500" />
          <h4 class="section-title">
            看多观点
          </h4>
          <span class="section-count">{{ keyPoints.bullish.length }}</span>
        </div>
        
        <div class="points-list">
          <div
            v-for="(point, index) in keyPoints.bullish"
            :key="`bullish-${index}`"
            class="point-item"
          >
            <div
              class="point-header"
              @click="toggleExpand(`bullish-${index}`)"
            >
              <div class="point-number bullish">
                {{ index + 1 }}
              </div>
              <div class="point-summary">
                {{ point.summary || point.content }}
              </div>
              <button
                class="expand-icon"
                :class="{ 'is-expanded': expandedPoints.has(`bullish-${index}`) }"
              >
                ▼
              </button>
            </div>
            
            <div
              v-if="expandedPoints.has(`bullish-${index}`)"
              class="point-details"
            >
              <p class="point-detail">
                {{ point.content }}
              </p>
              <div
                v-if="point.supportingPosts && point.supportingPosts.length > 0"
                class="supporting-posts"
              >
                <div class="supporting-header">
                  支持帖子
                </div>
                <div
                  v-for="postId in point.supportingPosts.slice(0, 3)"
                  :key="postId"
                  class="supporting-post"
                >
                  <FileText class="post-icon w-4 h-4 text-gray-400" />
                  <span class="post-id">帖子 #{{ postId.slice(0, 8) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bearish Points -->
      <div
        v-if="keyPoints.bearish.length > 0"
        class="points-section"
      >
        <div class="section-header bearish">
          <TrendingDown class="section-icon w-5 h-5 text-red-500" />
          <h4 class="section-title">
            看空观点
          </h4>
          <span class="section-count">{{ keyPoints.bearish.length }}</span>
        </div>
        
        <div class="points-list">
          <div
            v-for="(point, index) in keyPoints.bearish"
            :key="`bearish-${index}`"
            class="point-item"
          >
            <div
              class="point-header"
              @click="toggleExpand(`bearish-${index}`)"
            >
              <div class="point-number bearish">
                {{ index + 1 }}
              </div>
              <div class="point-summary">
                {{ point.summary || point.content }}
              </div>
              <button
                class="expand-icon"
                :class="{ 'is-expanded': expandedPoints.has(`bearish-${index}`) }"
              >
                ▼
              </button>
            </div>
            
            <div
              v-if="expandedPoints.has(`bearish-${index}`)"
              class="point-details"
            >
              <p class="point-detail">
                {{ point.content }}
              </p>
              <div
                v-if="point.supportingPosts && point.supportingPosts.length > 0"
                class="supporting-posts"
              >
                <div class="supporting-header">
                  支持帖子
                </div>
                <div
                  v-for="postId in point.supportingPosts.slice(0, 3)"
                  :key="postId"
                  class="supporting-post"
                >
                  <FileText class="post-icon w-4 h-4 text-gray-400" />
                  <span class="post-id">帖子 #{{ postId.slice(0, 8) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { TrendingUp, TrendingDown, AlertTriangle, Lightbulb, FileText } from 'lucide-vue-next'

interface KeyPoint {
  content: string
  summary?: string
  supportingPosts?: string[]
}

interface KeyPoints {
  bullish: KeyPoint[]
  bearish: KeyPoint[]
}

interface Props {
  keyPoints: KeyPoints | null
  isLoading?: boolean
  error?: string | null
}

withDefaults(defineProps<Props>(), {
  isLoading: false,
  error: null,
})

// Expanded points
const expandedPoints = ref<Set<string>>(new Set())

// Toggle expand/collapse
function toggleExpand(pointId: string) {
  if (expandedPoints.value.has(pointId)) {
    expandedPoints.value.delete(pointId)
  } else {
    expandedPoints.value.add(pointId)
  }
}
</script>

<style scoped>
.key-points-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f3f4f6;
}

.title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.points-count {
  padding: 0.25rem 0.75rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
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

/* Points Content */
.points-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.points-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}

.section-header.bullish {
  background: #d1fae5;
}

.section-header.bearish {
  background: #fee2e2;
}

.section-icon {
  font-size: 1.25rem;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.section-header.bullish .section-title {
  color: #065f46;
}

.section-header.bearish .section-title {
  color: #991b1b;
}

.section-count {
  padding: 0.25rem 0.5rem;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.section-header.bullish .section-count {
  color: #065f46;
}

.section-header.bearish .section-count {
  color: #991b1b;
}

/* Points List */
.points-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.point-item {
  display: flex;
  flex-direction: column;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  transition: all 200ms ease;
}

.point-item:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.point-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  cursor: pointer;
  background: #f9fafb;
  transition: background 200ms ease;
}

.point-header:hover {
  background: #ffffff;
}

.point-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  font-size: 0.875rem;
  font-weight: 700;
  flex-shrink: 0;
}

.point-number.bullish {
  background: #10b981;
  color: #ffffff;
}

.point-number.bearish {
  background: #ef4444;
  color: #ffffff;
}

.point-summary {
  flex: 1;
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  line-height: 1.5;
}

.expand-icon {
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  transition: all 200ms ease;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.expand-icon.is-expanded {
  transform: rotate(180deg);
  color: #111827;
}

/* Point Details */
.point-details {
  padding: 1rem;
  background: #ffffff;
  border-top: 1px solid #e5e7eb;
  animation: slideDown 200ms ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-0.5rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.point-detail {
  font-size: 0.875rem;
  line-height: 1.6;
  color: #374151;
  margin: 0 0 1rem 0;
}

.supporting-posts {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.supporting-header {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.supporting-post {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-radius: 4px;
}

.post-icon {
  font-size: 1rem;
}

.post-id {
  font-size: 0.75rem;
  font-family: monospace;
  color: #6b7280;
}
</style>
