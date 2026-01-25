<script setup lang="ts">
/**
 * NotificationPanel - 通知下拉面板
 * 
 * 功能:
 * - 显示最近通知列表
 * - 标记已读/全部已读
 * - 查看全部通知入口
 */
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import type { Notification } from '@/api/notification'
import { 
  Bell, CheckCheck, ExternalLink, X,
  FileText, Settings as SettingsIcon, Gift, AtSign
} from 'lucide-vue-next'

const router = useRouter()
const notificationStore = useNotificationStore()

const emit = defineEmits<{
  close: []
}>()

// Load notifications on mount
onMounted(() => {
  notificationStore.fetchNotifications()
})

// Get icon for notification type
function getTypeIcon(type: Notification['type']) {
  switch (type) {
    case 'task': return FileText
    case 'system': return SettingsIcon
    case 'promotion': return Gift
    case 'mention': return AtSign
    default: return Bell
  }
}

// Format relative time
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays < 7) return `${diffDays} 天前`
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// Handle notification click
function handleNotificationClick(notification: Notification) {
  // Mark as read
  if (!notification.isRead) {
    notificationStore.markAsRead(notification.id)
  }
  
  // Navigate if link exists
  if (notification.link) {
    router.push(notification.link)
    emit('close')
  }
}

// Handle mark all as read
function handleMarkAllRead() {
  notificationStore.markAllAsRead()
}

// Handle view all
function handleViewAll() {
  router.push('/notifications')
  emit('close')
}
</script>

<template>
  <div class="notification-panel">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-left">
        <Bell class="w-4 h-4" />
        <span class="header-title">通知</span>
        <span
          v-if="notificationStore.unreadCount > 0"
          class="unread-badge"
        >
          {{ notificationStore.unreadCount }}
        </span>
      </div>
      <button
        v-if="notificationStore.hasUnread"
        class="mark-all-btn"
        @click="handleMarkAllRead"
      >
        <CheckCheck class="w-3.5 h-3.5" />
        <span>全部已读</span>
      </button>
    </div>

    <!-- Notification list -->
    <div class="notification-list">
      <!-- Loading state -->
      <div
        v-if="notificationStore.isLoading"
        class="loading-state"
      >
        <div class="loading-spinner" />
        <span>加载中...</span>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="notificationStore.notifications.length === 0"
        class="empty-state"
      >
        <Bell class="w-8 h-8 empty-icon" />
        <span>暂无通知</span>
      </div>

      <!-- Notification items -->
      <template v-else>
        <div
          v-for="notification in notificationStore.recentNotifications"
          :key="notification.id"
          :class="['notification-item', { unread: !notification.isRead }]"
          @click="handleNotificationClick(notification)"
        >
          <div class="item-icon">
            <component
              :is="getTypeIcon(notification.type)"
              class="w-4 h-4"
            />
          </div>
          <div class="item-content">
            <div class="item-title">
              {{ notification.title }}
            </div>
            <div class="item-desc">
              {{ notification.content }}
            </div>
            <div class="item-time">
              {{ formatRelativeTime(notification.createdAt) }}
            </div>
          </div>
          <div
            v-if="!notification.isRead"
            class="unread-dot"
          />
        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="panel-footer">
      <button
        class="view-all-btn"
        @click="handleViewAll"
      >
        <span>查看全部通知</span>
        <ExternalLink class="w-3.5 h-3.5" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.notification-panel {
  width: 360px;
  max-height: 480px;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
}

/* Header */
.panel-header {
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
  color: var(--any-text-primary);
}

.header-title {
  font-size: 14px;
  font-weight: 600;
}

.unread-badge {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: white;
  background: #E95151;
  border-radius: 9999px;
}

.mark-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 150ms ease;
}

.mark-all-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

/* List */
.notification-list {
  flex: 1;
  overflow-y: auto;
  max-height: 360px;
}

/* Loading & Empty states */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: var(--any-text-muted);
  font-size: 13px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--any-border);
  border-top-color: var(--td-state-thinking);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  opacity: 0.4;
}

/* Notification item */
.notification-item {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 150ms ease;
  position: relative;
}

.notification-item:hover {
  background: var(--any-bg-hover);
}

.notification-item.unread {
  background: rgba(0, 217, 255, 0.05);
}

.notification-item.unread:hover {
  background: rgba(0, 217, 255, 0.08);
}

.item-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  color: var(--any-text-secondary);
  flex-shrink: 0;
}

.notification-item.unread .item-icon {
  background: rgba(0, 217, 255, 0.15);
  color: var(--td-state-thinking);
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
  margin-bottom: 2px;
}

.item-desc {
  font-size: 12px;
  color: var(--any-text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-time {
  font-size: 11px;
  color: var(--any-text-muted);
  margin-top: 4px;
}

.unread-dot {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 8px;
  height: 8px;
  background: var(--td-state-thinking);
  border-radius: 50%;
}

/* Footer */
.panel-footer {
  padding: 8px 12px;
  border-top: 1px solid var(--any-border);
}

.view-all-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px;
  font-size: 13px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.view-all-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

/* Scrollbar */
.notification-list::-webkit-scrollbar {
  width: 6px;
}

.notification-list::-webkit-scrollbar-track {
  background: transparent;
}

.notification-list::-webkit-scrollbar-thumb {
  background: var(--any-border);
  border-radius: 3px;
}

.notification-list::-webkit-scrollbar-thumb:hover {
  background: var(--any-border-hover);
}
</style>
