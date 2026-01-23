/**
 * Message API service
 */
import apiClient from './client'

export interface FeedbackResponse {
  message_id: string
  feedback: 'like' | 'dislike' | null
  feedback_at: string | null
}

export const messageApi = {
  /**
   * Submit feedback for a message (like/dislike)
   * 
   * @param messageId - The message ID
   * @param feedback - 'like', 'dislike', or null to clear
   */
  async submitFeedback(
    messageId: string, 
    feedback: 'like' | 'dislike' | null
  ): Promise<FeedbackResponse> {
    const response = await apiClient.post<FeedbackResponse>(
      `/api/v1/messages/feedback/${messageId}`,
      { feedback }
    )
    return response.data
  }
}
