/**
 * Research API Service
 * Handles deep research related API calls including interventions
 */
import apiClient from '../client'
import type { ResearchIntervention } from '@/components/execution/research/types'

/**
 * Types
 */
export interface InterventionResponse {
  session_id: string
  intervention_id: string
  status: 'queued' | 'processing' | 'applied' | 'rejected'
  message: string
}

export interface PendingInterventionsResponse {
  session_id: string
  pending: Array<{
    id: string
    type: string
    content: string
    timestamp: string
    status: string
  }>
}

/**
 * Research API Service Class
 */
class ResearchService {
  private readonly basePath = '/api/v1/research'

  /**
   * Send research intervention
   * Allows users to guide ongoing deep research
   */
  async sendIntervention(
    sessionId: string,
    intervention: ResearchIntervention
  ): Promise<InterventionResponse> {
    const response = await apiClient.post<InterventionResponse>(
      `${this.basePath}/sessions/${sessionId}/intervene`,
      {
        type: intervention.type,
        content: intervention.content,
        timestamp: intervention.timestamp,
      }
    )
    return response.data
  }

  /**
   * Get pending interventions for a session
   */
  async getPendingInterventions(sessionId: string): Promise<PendingInterventionsResponse> {
    const response = await apiClient.get<PendingInterventionsResponse>(
      `${this.basePath}/sessions/${sessionId}/interventions`
    )
    return response.data
  }

  /**
   * Acknowledge intervention has been processed
   */
  async acknowledgeIntervention(
    sessionId: string,
    interventionId: string,
    status: 'applied' | 'rejected' = 'applied'
  ): Promise<{ status: string; intervention_id: string }> {
    const response = await apiClient.post<{ status: string; intervention_id: string }>(
      `${this.basePath}/sessions/${sessionId}/interventions/${interventionId}/ack`,
      null,
      { params: { status } }
    )
    return response.data
  }
}

// Export singleton instance
export const researchService = new ResearchService()
export default researchService
