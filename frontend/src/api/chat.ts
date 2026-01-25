/**
 * Chat API client - handles SSE streaming
 */
import apiClient from './client'

export interface ChatRequest {
  content: string
  attachments?: Attachment[]
}

export interface Attachment {
  type: string
  file_id?: string
  url?: string
  name?: string
}

export interface ConfirmRequest {
  action_id: string
  confirmed: boolean
}

// SSE Event Types
export type SSEEventType =
  | 'thinking'
  | 'tool_call'
  | 'tool_result'
  | 'content'
  | 'confirm_required'
  | 'done'
  | 'error'

export interface SSEEvent<T = any> {
  type: SSEEventType
  data: T
}

export interface ThinkingEvent {
  content: string
  status?: 'start' | 'end'
}

export interface ToolCallEvent {
  id: string
  name: string
  args?: Record<string, any>
  status: 'pending' | 'running'
}

export interface ToolResultEvent {
  id: string
  status: 'success' | 'error' | 'cancelled'
  result?: string
  error?: string
}

export interface ContentEvent {
  content: string
  citations?: Array<{
    index: number
    url: string
    title: string
    snippet?: string
  }>
}

export interface ConfirmRequiredEvent {
  action_id: string
  tool: string
  args: Record<string, any>
  description: string
}

export interface DoneEvent {
  status: 'completed' | 'stopped' | 'max_iterations_reached'
  message_id: string
  tokens_used: number
}

export interface ErrorEvent {
  message: string
  code?: string
}

export type SSEEventHandler = (event: SSEEvent) => void

export const chatApi = {
  /**
   * Send message to Agent and get SSE stream
   * 
   * Returns an EventSource for handling SSE events
   */
  sendMessage(sessionId: string, _request: ChatRequest): EventSource {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    
    // Create EventSource for SSE
    const url = `${baseUrl}/api/v1/chat/${sessionId}/message`
    
    // EventSource doesn't support POST or custom headers directly
    // We'll need to use fetch API for POST, which will be handled in the composable
    // For now, return a mock EventSource
    const eventSource = new EventSource(url)
    
    return eventSource
  },

  /**
   * Confirm or reject HITL action
   */
  async confirm(sessionId: string, request: ConfirmRequest): Promise<{
    status: string
    action_id: string
    message: string
  }> {
    const response = await apiClient.post(
      `/api/v1/chat/${sessionId}/confirm`,
      request
    )
    return response.data
  },

  /**
   * Stop current Agent execution
   */
  async stop(sessionId: string): Promise<{
    status: string
    message: string
  }> {
    const response = await apiClient.post(`/api/v1/chat/${sessionId}/stop`)
    return response.data
  },

  /**
   * Send message using fetch API (for POST with SSE)
   * This is used by the composable to handle SSE with POST
   */
  async sendMessageStream(
    sessionId: string,
    request: ChatRequest,
    onEvent: SSEEventHandler,
    onError?: (error: Error) => void,
    signal?: AbortSignal
  ): Promise<void> {
    const token = localStorage.getItem('access_token')
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseUrl}/api/v1/chat/${sessionId}/message`

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(request),
        signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is null')
      }

      const decoder = new TextDecoder()
      let buffer = ''
      let currentEventType: SSEEventType = 'content'

      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEventType = line.substring(6).trim() as SSEEventType
            continue
          }

          if (line.startsWith('data:')) {
            const data = line.substring(5).trim()
            if (data) {
              try {
                const parsedData = JSON.parse(data)
                onEvent({ type: currentEventType, data: parsedData })
              } catch (e) {
                console.error('Failed to parse SSE data:', e)
              }
            }
          }
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        onError?.(error)
      }
    }
  },
}
