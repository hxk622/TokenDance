<template>
  <div class="session-list-panel">
    <!-- Header -->
    <div class="session-list-header">
      <h3 class="session-list-title">
        会话列表
      </h3>
      <button
        class="new-session-btn"
        @click="handleNewSession"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          />
        </svg>
        新建会话
      </button>
    </div>

    <!-- Loading State -->
    <div
      v-if="isLoading"
      class="session-list-loading"
    >
      <div class="loading-spinner" />
    </div>

    <!-- Empty State -->
    <div
      v-else-if="sessions.length === 0"
      class="session-list-empty"
    >
      <svg
        class="w-12 h-12 text-gray-400"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        />
      </svg>
      <p class="empty-text">
        暂无会话
      </p>
      <button
        class="empty-action"
        @click="handleNewSession"
      >
        创建第一个会话
      </button>
    </div>

    <!-- Session List -->
    <div
      v-else
      class="session-list-content"
    >
      <!-- Active Sessions -->
      <div
        v-if="activeSessions.length > 0"
        class="session-group"
      >
        <h4 class="session-group-title">
          进行中
        </h4>
        <button
          v-for="session in activeSessions"
          :key="session.id"
          class="session-item"
          :class="{ 'session-item--active': currentSession?.id === session.id }"
          @click="handleSessionClick(session)"
        >
          <div class="session-item-content">
            <div class="session-item-icon">
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <div class="session-item-info">
              <span class="session-item-title">{{ session.title }}</span>
              <span class="session-item-meta">{{ session.message_count }} 条消息</span>
            </div>
            <div class="session-item-actions">
              <button
                class="session-item-action"
                title="删除"
                @click.stop="handleDeleteSession(session)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </button>
      </div>

      <!-- Completed Sessions -->
      <div
        v-if="completedSessions.length > 0"
        class="session-group"
      >
        <h4 class="session-group-title">
          已完成
        </h4>
        <button
          v-for="session in completedSessions"
          :key="session.id"
          class="session-item"
          :class="{ 'session-item--active': currentSession?.id === session.id }"
          @click="handleSessionClick(session)"
        >
          <div class="session-item-content">
            <div class="session-item-icon">
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <div class="session-item-info">
              <span class="session-item-title">{{ session.title }}</span>
              <span class="session-item-meta">{{ formatDate(session.updated_at) }}</span>
            </div>
            <div class="session-item-actions">
              <button
                class="session-item-action"
                title="删除"
                @click.stop="handleDeleteSession(session)"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </button>
      </div>

      <!-- Load More -->
      <button
        v-if="hasMore"
        class="load-more-btn"
        :disabled="isLoading"
        @click="handleLoadMore"
      >
        <span v-if="isLoading">加载中...</span>
        <span v-else>加载更多</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/session'
import type { Session } from '@/api/session'

const router = useRouter()
const sessionStore = useSessionStore()

const sessions = computed(() => sessionStore.sessions)
const currentSession = computed(() => sessionStore.currentSession)
const activeSessions = computed(() => sessionStore.activeSessions)
const completedSessions = computed(() => sessionStore.completedSessions)
const isLoading = computed(() => sessionStore.isLoading)
const hasMore = computed(() => sessionStore.hasMore)

function handleSessionClick(session: Session) {
  sessionStore.setCurrentSession(session)
  router.push(`/chat/${session.id}`)
}

function handleNewSession() {
  // TODO: Create new session and navigate to chat
  router.push('/chat')
}

async function handleDeleteSession(session: Session) {
  if (!confirm(`确定要删除会话 "${session.title}" 吗？`)) {
    return
  }
  
  try {
    await sessionStore.deleteSession(session.id)
  } catch (err) {
    console.error('Failed to delete session:', err)
  }
}

function handleLoadMore() {
  sessionStore.loadMore()
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const minutes = Math.floor(diff / (1000 * 60))
      return `${minutes} 分钟前`
    }
    return `${hours} 小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}
</script>

<style scoped>
.session-list-panel {
  @apply w-full h-full flex flex-col;
}

.session-list-header {
  @apply flex items-center justify-between mb-4;
}

.session-list-title {
  @apply text-sm font-semibold text-gray-900;
}

.new-session-btn {
  @apply flex items-center gap-1 px-3 py-1.5 text-sm text-blue-600 
         bg-blue-50 rounded-md hover:bg-blue-100 transition-colors;
}

.session-list-loading {
  @apply flex items-center justify-center py-8;
}

.loading-spinner {
  @apply w-6 h-6 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin;
}

.session-list-empty {
  @apply flex flex-col items-center justify-center py-12 text-center;
}

.empty-text {
  @apply mt-4 text-sm text-gray-500;
}

.empty-action {
  @apply mt-4 px-4 py-2 text-sm text-blue-600 bg-blue-50 
         rounded-md hover:bg-blue-100 transition-colors;
}

.session-list-content {
  @apply flex-1 overflow-y-auto;
}

.session-group {
  @apply mb-4;
}

.session-group-title {
  @apply px-2 mb-2 text-xs font-medium text-gray-500 uppercase tracking-wide;
}

.session-item {
  @apply flex items-center gap-3 w-full px-3 py-2.5 text-left
         bg-white border border-gray-200 rounded-lg
         hover:bg-gray-50 hover:border-gray-300
         transition-all duration-200;
}

.session-item--active {
  @apply bg-blue-50 border-blue-200;
}

.session-item-content {
  @apply flex items-center gap-3 flex-1;
}

.session-item-icon {
  @apply flex-shrink-0 text-gray-400;
}

.session-item--active .session-item-icon {
  @apply text-blue-600;
}

.session-item-info {
  @apply flex flex-col flex-1 min-w-0;
}

.session-item-title {
  @apply text-sm font-medium text-gray-900 truncate;
}

.session-item--active .session-item-title {
  @apply text-blue-900;
}

.session-item-meta {
  @apply text-xs text-gray-500;
}

.session-item-actions {
  @apply flex-shrink-0;
}

.session-item-action {
  @apply p-1.5 text-gray-400 hover:text-red-600 
         hover:bg-red-50 rounded transition-colors;
}

.load-more-btn {
  @apply w-full py-2 text-sm text-gray-600 bg-gray-50 
         border border-gray-200 rounded-lg hover:bg-gray-100
         disabled:opacity-50 disabled:cursor-not-allowed transition-colors;
}

/* Dark mode */
:global(.dark) .session-list-title {
  @apply text-gray-100;
}

:global(.dark) .new-session-btn {
  @apply bg-blue-900/30 text-blue-400 hover:bg-blue-900/50;
}

:global(.dark) .session-item {
  @apply bg-gray-900 border-gray-800 hover:bg-gray-800 hover:border-gray-700;
}

:global(.dark) .session-item--active {
  @apply bg-blue-900/30 border-blue-800;
}

:global(.dark) .session-item-title {
  @apply text-gray-100;
}

:global(.dark) .session-item--active .session-item-title {
  @apply text-blue-300;
}

:global(.dark) .session-item-meta {
  @apply text-gray-500;
}

:global(.dark) .session-item-icon {
  @apply text-gray-600;
}

:global(.dark) .session-item--active .session-item-icon {
  @apply text-blue-400;
}

:global(.dark) .session-item-action {
  @apply text-gray-600 hover:text-red-400 hover:bg-red-900/30;
}

:global(.dark) .session-group-title {
  @apply text-gray-600;
}

:global(.dark) .load-more-btn {
  @apply bg-gray-900 border-gray-800 text-gray-400 hover:bg-gray-800;
}

:global(.dark) .empty-text {
  @apply text-gray-500;
}

:global(.dark) .empty-action {
  @apply bg-blue-900/30 text-blue-400 hover:bg-blue-900/50;
}
</style>
