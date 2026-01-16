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
  id: string  // alias for request_id
  sessionId: string  // alias for session_id
  type: string  // alias for operation
  title?: string
  description: string
  context: Record<string, any>
  status: 'pending' | 'approved' | 'rejected'
  riskLevel?: 'low' | 'medium' | 'high'
  createdAt: string  // alias for created_at
}

// API response types (snake_case from backend)
interface HITLRequestRaw {
  request_id: string
  session_id: string
  operation: string
  description: string
  context: Record<string, any>
  created_at: string
}

interface CreateHITLPayload {
  type: string
  title?: string
  description: string
  context?: Record<string, any>
  riskLevel?: 'low' | 'medium' | 'high'
}

// Transform raw API response to frontend format
function transformRequest(raw: HITLRequestRaw): HITLRequest {
  return {
    id: raw.request_id,
    sessionId: raw.session_id,
    type: raw.operation,
    title: raw.operation,
    description: raw.description,
    context: raw.context,
    status: 'pending',
    createdAt: raw.created_at,
  }
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
   * Create a new HITL intervention request
   */
  async create(sessionId: string, payload: CreateHITLPayload): Promise<HITLRequest> {
    try {
      const response = await apiClient.post<HITLRequestRaw>(
        `/api/v1/sessions/${sessionId}/hitl`,
        {
          operation: payload.type,
          description: payload.description,
          context: payload.context || {},
        }
      )
      return transformRequest(response.data)
    } catch {
      // Fallback for demo/offline mode
      return {
        id: 'manual-' + Date.now(),
        sessionId,
        type: payload.type,
        title: payload.title,
        description: payload.description,
        context: payload.context || {},
        status: 'pending',
        riskLevel: payload.riskLevel,
        createdAt: new Date().toISOString(),
      }
    }
  },

  /**
   * List all pending HITL requests for a session
   */
  async listPending(sessionId: string): Promise<HITLRequest[]> {
    const response = await apiClient.get<HITLRequestRaw[]>(
      `/api/v1/sessions/${sessionId}/hitl/pending`
    )
    return response.data.map(transformRequest)
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
    const response = await apiClient.get<HITLRequestRaw>(
      `/api/v1/hitl/${requestId}`
    )
    return transformRequest(response.data)
  },
}

export default hitlApi
