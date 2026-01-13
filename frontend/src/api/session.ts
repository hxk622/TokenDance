/**
 * Session API client
 */
import apiClient from './client'

// Types
export interface Session {
  id: string
  workspace_id: string
  title: string
  status: 'active' | 'completed' | 'failed' | 'archived'
  skill_id?: string
  total_tokens_used: number
  message_count: number
  created_at: string
  updated_at: string
  completed_at?: string
}

export interface SessionDetail extends Session {
  context_summary?: string
  todo_list?: TodoItem[]
  extra_data?: Record<string, any>
}

export interface TodoItem {
  title: string
  description?: string
  completed: boolean
}

export interface SessionCreate {
  workspace_id: string
  title?: string
  skill_id?: string
}

export interface SessionUpdate {
  title?: string
  status?: Session['status']
  skill_id?: string
  todo_list?: TodoItem[]
}

export interface SessionList {
  items: Session[]
  total: number
  limit: number
  offset: number
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content?: string
  thinking?: string
  tool_calls?: ToolCall[]
  citations?: Citation[]
  tokens_used: number
  created_at: string
}

export interface ToolCall {
  id: string
  name: string
  args: Record<string, any>
  status: 'pending' | 'running' | 'success' | 'error' | 'cancelled'
  result?: any
  error?: string
}

export interface Citation {
  index: number
  url: string
  title: string
  domain?: string
  snippet?: string
}

export interface Artifact {
  id: string
  session_id: string
  name: string
  artifact_type: 'document' | 'ppt' | 'report' | 'code' | 'data' | 'image' | 'kv_snapshot'
  file_path: string
  file_size: number
  download_url: string
  preview_url?: string
  thumbnail_url?: string
  created_at: string
  updated_at: string
}

// API Methods
export const sessionApi = {
  /**
   * Create a new session
   */
  async create(data: SessionCreate): Promise<Session> {
    const response = await apiClient.post<Session>('/api/v1/sessions', data)
    return response.data
  },

  /**
   * List sessions with pagination
   */
  async list(params: {
    workspace_id: string
    limit?: number
    offset?: number
    status?: Session['status']
  }): Promise<SessionList> {
    const response = await apiClient.get<SessionList>('/api/v1/sessions', { params })
    return response.data
  },

  /**
   * Get session by ID
   */
  async get(sessionId: string, includeDetails = false): Promise<Session | SessionDetail> {
    const response = await apiClient.get<Session | SessionDetail>(
      `/api/v1/sessions/${sessionId}`,
      { params: { include_details: includeDetails } }
    )
    return response.data
  },

  /**
   * Update session
   */
  async update(sessionId: string, data: SessionUpdate): Promise<Session> {
    const response = await apiClient.patch<Session>(`/api/v1/sessions/${sessionId}`, data)
    return response.data
  },

  /**
   * Delete session
   */
  async delete(sessionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/sessions/${sessionId}`)
  },

  /**
   * Mark session as completed
   */
  async complete(sessionId: string): Promise<Session> {
    const response = await apiClient.post<Session>(`/api/v1/sessions/${sessionId}/complete`)
    return response.data
  },

  /**
   * Get messages for a session
   */
  async getMessages(sessionId: string, limit?: number): Promise<{ items: Message[]; total: number }> {
    const response = await apiClient.get<{ items: Message[]; total: number }>(
      `/api/v1/sessions/${sessionId}/messages`,
      { params: { limit } }
    )
    return response.data
  },

  /**
   * Get artifacts for a session
   */
  async getArtifacts(sessionId: string): Promise<{ items: Artifact[]; total: number }> {
    const response = await apiClient.get<{ items: Artifact[]; total: number }>(
      `/api/v1/sessions/${sessionId}/artifacts`
    )
    return response.data
  },
}
