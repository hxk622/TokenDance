/**
 * HITL (Human-in-the-Loop) API Client
 * 
 * Provides interface for HITL confirmation flow:
 * - List pending confirmation requests
 * - Submit user confirmation (approve/reject)
 * - Get request details
 */
import apiClient from './client'

// Types
export interface HITLRequest {
  request_id: string
  session_id: string
  operation: string
  description: string
  context: Record<string, any>
  created_at: string
}

export interface HITLConfirmPayload {
  approved: boolean
  user_feedback?: string | null
}

export interface HITLConfirmResponse {
  request_id: string
  approved: boolean
  user_feedback: string | null
  responded_at: string
}

// API Functions
export const hitlApi = {
  /**
   * List all pending HITL requests for a session
   */
  async listPending(sessionId: string): Promise<HITLRequest[]> {
    const response = await apiClient.get<HITLRequest[]>(
      `/api/v1/sessions/${sessionId}/hitl/pending`
    )
    return response.data
  },

  /**
   * Submit confirmation for a HITL request
   */
  async confirm(
    requestId: string,
    payload: HITLConfirmPayload
  ): Promise<HITLConfirmResponse> {
    const response = await apiClient.post<HITLConfirmResponse>(
      `/api/v1/hitl/${requestId}/confirm`,
      payload
    )
    return response.data
  },

  /**
   * Get HITL request details by ID
   */
  async getRequest(requestId: string): Promise<HITLRequest> {
    const response = await apiClient.get<HITLRequest>(
      `/api/v1/hitl/${requestId}`
    )
    return response.data
  },
}

export default hitlApi
