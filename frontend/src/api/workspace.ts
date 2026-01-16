/**
 * Workspace API service
 */
import apiClient from './client'

export interface WorkspaceCreate {
  name: string
  slug: string
  description?: string
  workspace_type?: 'PERSONAL' | 'TEAM'
}

export interface WorkspaceUpdate {
  name?: string
  slug?: string
  description?: string
  settings?: Record<string, any>
}

export interface Workspace {
  id: string
  name: string
  slug: string
  description?: string
  workspace_type: 'PERSONAL' | 'TEAM'
  owner_id: string
  team_id?: string
  filesystem_path: string
  settings: Record<string, any>
  stats: Record<string, any>
  session_count: number
  created_at: string
  updated_at: string
  last_accessed_at?: string
}

export interface WorkspaceList {
  items: Workspace[]
  total: number
  limit: number
  offset: number
}

export const workspaceApi = {
  /**
   * Create a new workspace
   */
  async createWorkspace(data: WorkspaceCreate): Promise<Workspace> {
    const response = await apiClient.post<Workspace>('/api/v1/workspaces', data)
    return response.data
  },

  /**
   * List workspaces for current user
   */
  async listWorkspaces(limit: number = 20, offset: number = 0): Promise<WorkspaceList> {
    const response = await apiClient.get<WorkspaceList>('/api/v1/workspaces', {
      params: { limit, offset }
    })
    return response.data
  },

  /**
   * Get workspace by ID
   */
  async getWorkspace(workspaceId: string, includeDetails: boolean = false): Promise<Workspace> {
    const response = await apiClient.get<Workspace>(`/api/v1/workspaces/${workspaceId}`, {
      params: { include_details: includeDetails }
    })
    return response.data
  },

  /**
   * Update workspace
   */
  async updateWorkspace(workspaceId: string, data: WorkspaceUpdate): Promise<Workspace> {
    const response = await apiClient.patch<Workspace>(`/api/v1/workspaces/${workspaceId}`, data)
    return response.data
  },

  /**
   * Delete workspace
   */
  async deleteWorkspace(workspaceId: string): Promise<void> {
    await apiClient.delete(`/api/v1/workspaces/${workspaceId}`)
  },

  /**
   * Get sessions for a workspace
   */
  async getWorkspaceSessions(workspaceId: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/workspaces/${workspaceId}/sessions`)
    return response.data
  }
}
