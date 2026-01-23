/**
 * Session API service
 */
import apiClient from './client'

export interface SessionCreate {
  workspace_id: string
  title?: string
  skill_id?: string
}

export interface SessionUpdate {
  title?: string
  status?: 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'ARCHIVED'
  skill_id?: string
  todo_list?: any[]
}

export interface TodoItem {
  title: string
  description?: string
  completed: boolean
}

export interface Session {
  id: string
  workspace_id: string
  title: string
  status: 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'ARCHIVED'
  skill_id?: string
  total_tokens_used: number
  message_count: number
  created_at: string
  updated_at: string
  completed_at?: string
  messages?: Message[]
}

export interface Citation {
  index: number
  url: string
  title?: string
  domain?: string
}

export interface ToolCall {
  id: string
  name: string
  args?: Record<string, unknown>
  status: 'pending' | 'running' | 'success' | 'error' | 'cancelled'
  result?: unknown
  error?: string
}

export interface Message {
  id: string
  session_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: string
  tool_calls?: ToolCall[]
  citations?: Citation[]
  tokens_used?: number
  feedback?: 'like' | 'dislike' | null
  feedback_at?: string | null
  created_at: string
}

export interface SessionList {
  items: Session[]
  total: number
  limit: number
  offset: number
}

export const sessionApi = {
  /**
   * Create a new session
   */
  async createSession(data: SessionCreate): Promise<Session> {
    const response = await apiClient.post<Session>('/api/v1/sessions', data)
    return response.data
  },

  /**
   * List sessions for a workspace
   */
  async listSessions(
    workspaceId: string,
    limit: number = 20,
    offset: number = 0,
    status?: 'ACTIVE' | 'COMPLETED' | 'FAILED' | 'ARCHIVED'
  ): Promise<SessionList> {
    const response = await apiClient.get<SessionList>('/api/v1/sessions', {
      params: { workspace_id: workspaceId, limit, offset, status }
    })
    return response.data
  },

  /**
   * Get session by ID
   */
  async getSession(sessionId: string, includeDetails: boolean = false): Promise<Session> {
    const response = await apiClient.get<Session>(`/api/v1/sessions/${sessionId}`, {
      params: { include_details: includeDetails }
    })
    return response.data
  },

  /**
   * Update session
   */
  async updateSession(sessionId: string, data: SessionUpdate): Promise<Session> {
    const response = await apiClient.patch<Session>(`/api/v1/sessions/${sessionId}`, data)
    return response.data
  },

  /**
   * Delete session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/sessions/${sessionId}`)
  },

  /**
   * Mark session as completed
   */
  async completeSession(sessionId: string): Promise<Session> {
    const response = await apiClient.post<Session>(`/api/v1/sessions/${sessionId}/complete`)
    return response.data
  }
}
