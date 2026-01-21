/**
 * Project API client - Project-First architecture
 */
import apiClient from './client'
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  ProjectList,
  Conversation,
  ConversationCreate,
  ConversationList,
  ChatMessage,
  ChatResponse,
  ProjectContextResponse,
  ProjectStatus,
  ProjectType,
} from '@/types/project'

const API_PREFIX = '/api/v1/projects'

export const projectApi = {
  // ============ Project CRUD ============

  /**
   * Create a new project
   */
  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await apiClient.post<Project>(API_PREFIX, data)
    return response.data
  },

  /**
   * List projects in a workspace
   */
  async listProjects(
    workspaceId: string,
    limit: number = 20,
    offset: number = 0,
    status?: ProjectStatus,
    projectType?: ProjectType
  ): Promise<ProjectList> {
    const params: Record<string, string | number> = {
      workspace_id: workspaceId,
      limit,
      offset,
    }
    if (status) params.status = status
    if (projectType) params.project_type = projectType

    const response = await apiClient.get<ProjectList>(API_PREFIX, { params })
    return response.data
  },

  /**
   * Get project by ID
   */
  async getProject(projectId: string): Promise<Project> {
    const response = await apiClient.get<Project>(`${API_PREFIX}/${projectId}`)
    return response.data
  },

  /**
   * Update project
   */
  async updateProject(projectId: string, data: ProjectUpdate): Promise<Project> {
    const response = await apiClient.patch<Project>(`${API_PREFIX}/${projectId}`, data)
    return response.data
  },

  /**
   * Archive project (soft delete)
   */
  async archiveProject(projectId: string): Promise<{ status: string; project_id: string }> {
    const response = await apiClient.delete<{ status: string; project_id: string }>(
      `${API_PREFIX}/${projectId}`
    )
    return response.data
  },

  /**
   * Delete project (hard delete)
   */
  async deleteProject(projectId: string): Promise<{ status: string; project_id: string }> {
    const response = await apiClient.delete<{ status: string; project_id: string }>(
      `${API_PREFIX}/${projectId}`,
      { params: { hard_delete: true } }
    )
    return response.data
  },

  // ============ Conversation Management ============

  /**
   * Create a new conversation in a project
   */
  async createConversation(
    projectId: string,
    data?: ConversationCreate
  ): Promise<Conversation> {
    const response = await apiClient.post<Conversation>(
      `${API_PREFIX}/${projectId}/conversations`,
      data || {}
    )
    return response.data
  },

  /**
   * List conversations in a project
   */
  async listConversations(projectId: string): Promise<ConversationList> {
    const response = await apiClient.get<ConversationList>(
      `${API_PREFIX}/${projectId}/conversations`
    )
    return response.data
  },

  // ============ Chat ============

  /**
   * Send a chat message in a project
   * Note: In Phase 3, this will be replaced with SSE streaming
   */
  async chat(projectId: string, data: ChatMessage): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>(
      `${API_PREFIX}/${projectId}/chat`,
      data
    )
    return response.data
  },

  // ============ Context Management ============

  /**
   * Add a decision to project context
   */
  async addDecision(
    projectId: string,
    decision: string,
    reason?: string
  ): Promise<{ status: string; decision: string; total_decisions: number }> {
    const params: Record<string, string> = { decision }
    if (reason) params.reason = reason

    const response = await apiClient.post<{
      status: string
      decision: string
      total_decisions: number
    }>(`${API_PREFIX}/${projectId}/context/decision`, null, { params })
    return response.data
  },

  /**
   * Add a failure record to project context (Keep the Failures)
   */
  async addFailure(
    projectId: string,
    failureType: string,
    message: string,
    learning?: string
  ): Promise<{ status: string; failure_type: string; total_failures: number }> {
    const params: Record<string, string> = {
      failure_type: failureType,
      message,
    }
    if (learning) params.learning = learning

    const response = await apiClient.post<{
      status: string
      failure_type: string
      total_failures: number
    }>(`${API_PREFIX}/${projectId}/context/failure`, null, { params })
    return response.data
  },

  /**
   * Add a finding to project context
   */
  async addFinding(
    projectId: string,
    finding: string,
    source?: string
  ): Promise<{ status: string; finding: string; total_findings: number }> {
    const params: Record<string, string> = { finding }
    if (source) params.source = source

    const response = await apiClient.post<{
      status: string
      finding: string
      total_findings: number
    }>(`${API_PREFIX}/${projectId}/context/finding`, null, { params })
    return response.data
  },

  /**
   * Get project context (for LLM)
   */
  async getContext(projectId: string): Promise<ProjectContextResponse> {
    const response = await apiClient.get<ProjectContextResponse>(
      `${API_PREFIX}/${projectId}/context`
    )
    return response.data
  },
}

export default projectApi
