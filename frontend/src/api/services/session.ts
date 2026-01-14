/**
 * Session API Service
 * Handles all session-related API calls
 */
import apiClient from '../client'

/**
 * Types
 */
export enum SessionStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export interface Session {
  id: string
  workspace_id: string
  user_id: string
  title: string
  status: SessionStatus
  task_type?: string
  metadata?: Record<string, any>
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
}

export interface SessionDetail extends Session {
  message_count: number
  artifact_count: number
  duration_seconds?: number
  working_memory?: {
    task_plan?: string
    findings?: string
    progress?: string
  }
}

export interface SessionCreate {
  workspace_id: string
  title: string
  task_type?: string
  metadata?: Record<string, any>
}

export interface SessionUpdate {
  title?: string
  status?: SessionStatus
  metadata?: Record<string, any>
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
  limit: number
  offset: number
}

export interface Message {
  id: string
  session_id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  metadata?: Record<string, any>
  created_at: string
}

export interface MessageListResponse {
  messages: Message[]
  total: number
}

export interface Artifact {
  id: string
  session_id: string
  type: 'report' | 'ppt' | 'code' | 'file' | 'other'
  title: string
  content?: string
  file_path?: string
  metadata?: Record<string, any>
  created_at: string
}

export interface ArtifactListResponse {
  artifacts: Artifact[]
  total: number
}

/**
 * Session API Service Class
 */
class SessionService {
  private readonly basePath = '/sessions'

  /**
   * Create a new session
   */
  async createSession(data: SessionCreate): Promise<Session> {
    const response = await apiClient.post<Session>(this.basePath, data)
    return response.data
  }

  /**
   * List sessions for a workspace
   */
  async listSessions(params: {
    workspace_id: string
    limit?: number
    offset?: number
    status?: SessionStatus
  }): Promise<SessionListResponse> {
    const response = await apiClient.get<SessionListResponse>(this.basePath, {
      params,
    })
    return response.data
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string, includeDetails = false): Promise<Session | SessionDetail> {
    const response = await apiClient.get<Session | SessionDetail>(
      `${this.basePath}/${sessionId}`,
      {
        params: { include_details: includeDetails },
      }
    )
    return response.data
  }

  /**
   * Update session
   */
  async updateSession(sessionId: string, data: SessionUpdate): Promise<Session> {
    const response = await apiClient.patch<Session>(
      `${this.basePath}/${sessionId}`,
      data
    )
    return response.data
  }

  /**
   * Delete session
   */
  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`${this.basePath}/${sessionId}`)
  }

  /**
   * Mark session as completed
   */
  async completeSession(sessionId: string): Promise<Session> {
    const response = await apiClient.post<Session>(
      `${this.basePath}/${sessionId}/complete`
    )
    return response.data
  }

  /**
   * Get messages for a session
   */
  async getSessionMessages(
    sessionId: string,
    limit?: number
  ): Promise<MessageListResponse> {
    const response = await apiClient.get<MessageListResponse>(
      `${this.basePath}/${sessionId}/messages`,
      {
        params: { limit },
      }
    )
    return response.data
  }

  /**
   * Get artifacts for a session
   */
  async getSessionArtifacts(sessionId: string): Promise<ArtifactListResponse> {
    const response = await apiClient.get<ArtifactListResponse>(
      `${this.basePath}/${sessionId}/artifacts`
    )
    return response.data
  }

  /**
   * Get working memory files (三文件工作法)
   */
  async getWorkingMemory(sessionId: string): Promise<{
    task_plan: string
    findings: string
    progress: string
  }> {
    // TODO: 实现获取三文件内容的API
    // 临时返回mock数据
    return {
      task_plan: '# Task Plan\n\n## Phase 1\n- Research market data\n\n## Phase 2\n- Analyze competitors',
      findings: '# Findings\n\n- Found 3 relevant reports',
      progress: '# Progress\n\n- [x] Completed Phase 1\n- [ ] Phase 2 in progress',
    }
  }
}

// Export singleton instance
export const sessionService = new SessionService()

// Export default
export default sessionService
