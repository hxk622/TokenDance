/**
 * Notification API client
 */
import apiClient from './client'

export interface Notification {
  id: string
  type: 'system' | 'task' | 'mention' | 'promotion'
  title: string
  content: string
  link?: string
  isRead: boolean
  createdAt: string
  metadata?: Record<string, any>
}

export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  unreadCount: number
}

export const notificationApi = {
  /**
   * Get notification list
   */
  async list(params?: {
    page?: number
    pageSize?: number
    unreadOnly?: boolean
  }): Promise<NotificationListResponse> {
    const response = await apiClient.get('/api/v1/notifications', { params })
    return response.data
  },

  /**
   * Get unread count
   */
  async getUnreadCount(): Promise<{ count: number }> {
    const response = await apiClient.get('/api/v1/notifications/unread-count')
    return response.data
  },

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    await apiClient.post(`/api/v1/notifications/${notificationId}/read`)
  },

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    await apiClient.post('/api/v1/notifications/read-all')
  },

  /**
   * Delete notification
   */
  async delete(notificationId: string): Promise<void> {
    await apiClient.delete(`/api/v1/notifications/${notificationId}`)
  }
}
