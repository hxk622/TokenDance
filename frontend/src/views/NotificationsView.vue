<script setup lang="ts">
/**
 * NotificationsView - 通知中心页面
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import type { Notification } from '@/api/notification'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import { 
  Bell, CheckCheck, Trash2, FileText, Settings as SettingsIcon, Gift, AtSign
} from 'lucide-vue-next'

const router = useRouter()
const notificationStore = useNotificationStore()

// Filter
const filter = ref<'all' | 'unread'>('all')

// Get filtered notifications
const filteredNotifications = ref<Notification[]>([])

function updateFilteredNotifications() {
  if (filter.value === 'unread') {
    filteredNotifications.value = notificationStore.unreadNotifications
  } else {
    filteredNotifications.value = notificationStore.notifications
  }
}

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
  return date.toLocaleDateString('zh-CN', { month: 'long', day: 'numeric' })
}

// Handle notification click
function handleNotificationClick(notification: Notification) {
  if (!notification.isRead) {
    notificationStore.markAsRead(notification.id)
  }
  if (notification.link) {
    router.push(notification.link)
  }
}

// Handle mark all as read
function handleMarkAllRead() {
  notificationStore.markAllAsRead()
  updateFilteredNotifications()
}

// Handle delete
async function handleDelete(notificationId: string) {
  await notificationStore.deleteNotification(notificationId)
  updateFilteredNotifications()
}

// Load on mount
onMounted(async () => {
  await notificationStore.fetchNotifications()
  updateFilteredNotifications()
})

// Watch filter changes
function setFilter(newFilter: 'all' | 'unread') {
  filter.value = newFilter
  updateFilteredNotifications()
}
</script>

<template>
  <div class="notifications-page">
    <AnyHeader />
    <AnySidebar />
    
    <main class="notifications-main">
      <div class="notifications-container">
        <!-- Header -->
        <div class="page-header">
          <h1 class="page-title">
            通知中心
          </h1>
          <div class="header-actions">
            <button
              v-if="notificationStore.hasUnread"
              class="mark-all-btn"
              @click="handleMarkAllRead"
            >
              <CheckCheck class="w-4 h-4" />
              <span>全部已读</span>
            </button>
          </div>
        </div>

        <!-- Filter tabs -->
        <div class="filter-tabs">
          <button
            :class="['filter-tab', { active: filter === 'all' }]"
            @click="setFilter('all')"
          >
            全部
            <span
              v-if="notificationStore.notifications.length > 0"
              class="tab-count"
            >
              {{ notificationStore.notifications.length }}
            </span>
          </button>
          <button
            :class="['filter-tab', { active: filter === 'unread' }]"
            @click="setFilter('unread')"
          >
            未读
            <span
              v-if="notificationStore.unreadCount > 0"
              class="tab-count unread"
            >
              {{ notificationStore.unreadCount }}
            </span>
          </button>
        </div>

        <!-- Notifications list -->
        <div class="notifications-list">
          <!-- Loading -->
          <div
            v-if="notificationStore.isLoading"
            class="loading-state"
          >
            <div class="loading-spinner" />
            <span>加载中...</span>
          </div>

          <!-- Empty -->
          <div
            v-else-if="filteredNotifications.length === 0"
            class="empty-state"
          >
            <Bell class="w-12 h-12 empty-icon" />
            <h3>暂无通知</h3>
            <p>{{ filter === 'unread' ? '没有未读通知' : '您还没有收到任何通知' }}</p>
          </div>

          <!-- Notification items -->
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            :class="['notification-item', { unread: !notification.isRead }]"
          >
            <div
              class="notification-main"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon">
                <component
                  :is="getTypeIcon(notification.type)"
                  class="w-5 h-5"
                />
              </div>
              <div class="notification-content">
                <div class="notification-title">
                  {{ notification.title }}
                </div>
                <div class="notification-desc">
                  {{ notification.content }}
                </div>
                <div class="notification-time">
                  {{ formatRelativeTime(notification.createdAt) }}
                </div>
              </div>
              <div
                v-if="!notification.isRead"
                class="unread-indicator"
              />
            </div>
            <div class="notification-actions">
              <button
                class="action-btn delete"
                title="删除"
                @click.stop="handleDelete(notification.id)"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.notifications-page {
  min-height: 100vh;
  background: var(--any-bg-primary);
}

.notifications-main {
  margin-left: 56px;
  padding: 80px 24px 40px;
}

.notifications-container {
  max-width: 800px;
  margin: 0 auto;
}

/* Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.mark-all-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 13px;
  color: var(--any-text-secondary);
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.mark-all-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Filter tabs */
.filter-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.filter-tab:hover {
  background: var(--any-bg-hover);
}

.filter-tab.active {
  background: var(--any-bg-secondary);
  border-color: var(--any-border);
  color: var(--any-text-primary);
}

.tab-count {
  padding: 2px 8px;
  font-size: 12px;
  background: var(--any-bg-tertiary);
  border-radius: 10px;
}

.tab-count.unread {
  background: #E95151;
  color: white;
}

/* List */
.notifications-list {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  overflow: hidden;
}

/* Loading & Empty */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--any-border);
  border-top-color: var(--td-state-thinking);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  color: var(--any-text-muted);
  opacity: 0.4;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 16px;
  color: var(--any-text-primary);
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: var(--any-text-muted);
  margin: 0;
}

/* Notification item */
.notification-item {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--any-border);
  transition: background 150ms ease;
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item:hover {
  background: var(--any-bg-hover);
}

.notification-item.unread {
  background: rgba(0, 217, 255, 0.03);
}

.notification-item.unread:hover {
  background: rgba(0, 217, 255, 0.06);
}

.notification-main {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px 20px;
  cursor: pointer;
  position: relative;
}

.notification-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  border-radius: 10px;
  color: var(--any-text-secondary);
  flex-shrink: 0;
}

.notification-item.unread .notification-icon {
  background: rgba(0, 217, 255, 0.15);
  color: var(--td-state-thinking);
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  margin-bottom: 4px;
}

.notification-desc {
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.5;
  margin-bottom: 6px;
}

.notification-time {
  font-size: 12px;
  color: var(--any-text-muted);
}

.unread-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 10px;
  height: 10px;
  background: var(--td-state-thinking);
  border-radius: 50%;
}

/* Actions */
.notification-actions {
  display: flex;
  align-items: center;
  padding-right: 16px;
  opacity: 0;
  transition: opacity 150ms ease;
}

.notification-item:hover .notification-actions {
  opacity: 1;
}

.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.action-btn.delete:hover {
  color: var(--td-state-error, #FF3B30);
  background: rgba(255, 59, 48, 0.1);
}

/* Responsive */
@media (max-width: 768px) {
  .notifications-main {
    margin-left: 0;
    padding: 72px 16px 24px;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .notification-actions {
    opacity: 1;
  }
}
</style>
