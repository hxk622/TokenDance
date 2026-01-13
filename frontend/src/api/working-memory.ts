/**
 * Working Memory API - fetches Three Files content
 * 
 * Three Files Working Memory Pattern (Manus):
 * - task_plan.md - Task roadmap and objectives
 * - findings.md - Research findings and decisions
 * - progress.md - Execution logs and errors
 */
import apiClient from './client'

export interface WorkingMemoryFile {
  content: string
  metadata: Record<string, any>
}

export interface WorkingMemoryResponse {
  session_id: string
  task_plan: WorkingMemoryFile
  findings: WorkingMemoryFile
  progress: WorkingMemoryFile
}

export const workingMemoryApi = {
  /**
   * Get Working Memory content for a session
   */
  async get(sessionId: string): Promise<WorkingMemoryResponse> {
    const response = await apiClient.get<WorkingMemoryResponse>(
      `/api/v1/chat/${sessionId}/working-memory`
    )
    return response.data
  },
}
