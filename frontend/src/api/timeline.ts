/**
 * Research Timeline API Client
 * 
 * Provides interface for research timeline:
 * - Get timeline entries
 * - List screenshots
 * - Export markdown
 */
import apiClient from './client'

// Types
export interface TimelineEntry {
  timestamp: string
  event_type: 'search' | 'read' | 'screenshot' | 'finding' | 'milestone'
  title: string
  description: string
  url: string | null
  screenshot_path: string | null
  metadata: Record<string, any>
}

export interface TimelineResponse {
  session_id: string
  topic: string
  created_at: string
  entries: TimelineEntry[]
  total_entries: number
}

export interface ScreenshotInfo {
  timestamp: string
  name: string
  path: string
  url: string | null
}

// API Functions
export const timelineApi = {
  /**
   * Get research timeline for a session
   */
  async getTimeline(
    sessionId: string,
    options?: { eventType?: string; limit?: number }
  ): Promise<TimelineResponse> {
    const params = new URLSearchParams()
    if (options?.eventType) {
      params.append('event_type', options.eventType)
    }
    if (options?.limit) {
      params.append('limit', options.limit.toString())
    }
    
    const queryString = params.toString()
    const url = `/api/v1/sessions/${sessionId}/timeline${queryString ? `?${queryString}` : ''}`
    
    const response = await apiClient.get<TimelineResponse>(url)
    return response.data
  },

  /**
   * List all screenshots for a session
   */
  async listScreenshots(sessionId: string): Promise<ScreenshotInfo[]> {
    const response = await apiClient.get<ScreenshotInfo[]>(
      `/api/v1/sessions/${sessionId}/timeline/screenshots`
    )
    return response.data
  },

  /**
   * Get screenshot URL by index
   */
  getScreenshotUrl(sessionId: string, index: number): string {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${baseUrl}/api/v1/sessions/${sessionId}/timeline/screenshots/${index}`
  },

  /**
   * Export timeline as Markdown
   */
  async exportMarkdown(sessionId: string): Promise<string> {
    const response = await apiClient.get<{ markdown: string }>(
      `/api/v1/sessions/${sessionId}/timeline/markdown`
    )
    return response.data.markdown
  },
}

export default timelineApi
