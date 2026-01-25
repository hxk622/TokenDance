/**
 * Notification store using Pinia
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationApi, type Notification } from '@/api/notification'

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref<Notification[]>([])
  const unreadCount = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const hasUnread = computed(() => unreadCount.value > 0)
  const unreadNotifications = computed(() => 
    notifications.value.filter(n => !n.isRead)
  )
  const recentNotifications = computed(() => 
    notifications.value.slice(0, 10)
  )

  /**
   * Fetch notifications
   */
  async function fetchNotifications(unreadOnly = false) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await notificationApi.list({ unreadOnly })
      notifications.value = response.notifications
      unreadCount.value = response.unreadCount
    } catch (err: any) {
      error.value = err.message || '获取通知失败'
      // Fallback: use mock data in development
      if (import.meta.env.DEV) {
        notifications.value = getMockNotifications()
        unreadCount.value = notifications.value.filter(n => !n.isRead).length
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch unread count only
   */
  async function fetchUnreadCount() {
    try {
      const response = await notificationApi.getUnreadCount()
      unreadCount.value = response.count
    } catch (err) {
      // Fallback for development
      if (import.meta.env.DEV) {
        unreadCount.value = getMockNotifications().filter(n => !n.isRead).length
      }
    }
  }

  /**
   * Mark single notification as read
   */
  async function markAsRead(notificationId: string) {
    try {
      await notificationApi.markAsRead(notificationId)
      
      // Update local state
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification && !notification.isRead) {
        notification.isRead = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (err: any) {
      error.value = err.message || '标记已读失败'
    }
  }

  /**
   * Mark all notifications as read
   */
  async function markAllAsRead() {
    try {
      await notificationApi.markAllAsRead()
      
      // Update local state
      notifications.value.forEach(n => {
        n.isRead = true
      })
      unreadCount.value = 0
    } catch (err: any) {
      error.value = err.message || '标记全部已读失败'
    }
  }

  /**
   * Delete notification
   */
  async function deleteNotification(notificationId: string) {
    try {
      await notificationApi.delete(notificationId)
      
      // Update local state
      const index = notifications.value.findIndex(n => n.id === notificationId)
      if (index !== -1) {
        const notification = notifications.value[index]
        if (!notification.isRead) {
          unreadCount.value = Math.max(0, unreadCount.value - 1)
        }
        notifications.value.splice(index, 1)
      }
    } catch (err: any) {
      error.value = err.message || '删除通知失败'
    }
  }

  /**
   * Clear all notifications (local only)
   */
  function clearAll() {
    notifications.value = []
    unreadCount.value = 0
  }

  return {
    // State
    notifications,
    unreadCount,
    isLoading,
    error,
    
    // Computed
    hasUnread,
    unreadNotifications,
    recentNotifications,
    
    // Actions
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
    clearAll
  }
})

/**
 * Mock notifications for development
 */
function getMockNotifications(): Notification[] {
  const now = new Date()
  return [
    {
      id: '1',
      type: 'task',
      title: '任务完成',
      content: '您的深度研究任务「2024年新能源汽车市场分析」已完成',
      link: '/execution/task-001',
      isRead: false,
      createdAt: new Date(now.getTime() - 5 * 60 * 1000).toISOString()
    },
    {
      id: '2',
      type: 'system',
      title: '系统升级',
      content: 'TokenDance 已升级到 v2.0，支持更多 AI 模型',
      isRead: false,
      createdAt: new Date(now.getTime() - 30 * 60 * 1000).toISOString()
    },
    {
      id: '3',
      type: 'promotion',
      title: '新用户福利',
      content: '恭喜获得 10,000 免费 Token，立即体验 AI 助手',
      link: '/billing',
      isRead: false,
      createdAt: new Date(now.getTime() - 2 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '4',
      type: 'task',
      title: 'PPT 生成完成',
      content: '您的演示文稿「Q4 业绩汇报」已生成完毕',
      link: '/ppt/preview/ppt-001',
      isRead: true,
      createdAt: new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString()
    },
    {
      id: '5',
      type: 'mention',
      title: '有人@了您',
      content: '张三 在项目「产品需求分析」中提到了您',
      link: '/project/proj-001',
      isRead: true,
      createdAt: new Date(now.getTime() - 48 * 60 * 60 * 1000).toISOString()
    }
  ]
}
