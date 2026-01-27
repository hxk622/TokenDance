/**
 * Message Service - Unified message sending via REST API
 * 
 * This is the PRIMARY service for sending messages to the Agent.
 * All message sending should go through this service.
 */
import type { Attachment as ChatAttachment } from '@/api/chat'
import { SSEEventType, type SSEEvent } from '@/api/services/sse'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

/**
 * Message payload for sending to Agent
 */
export interface MessagePayload {
  content: string
  attachments?: ChatAttachment[]
}

// Re-export SSEEvent and SSEEventType from sse.ts for consumers
export { type SSEEvent, SSEEventType }

/**
 * Event handler type
 */
export type SSEEventHandler = (event: SSEEvent) => void

/**
 * Send message to Agent via REST API with SSE streaming response
 * 
 * This function:
 * 1. Sends message via POST to /api/v1/chat/{sessionId}/message
 * 2. Streams the response as SSE events
 * 3. Calls the event handler for each event
 * 
 * @param sessionId - Session ID
 * @param payload - Message payload with content and optional attachments
 * @param onEvent - Event handler for SSE events
 * @param signal - Optional AbortSignal for cancellation
 * @returns Promise that resolves when stream ends
 */
export async function sendMessage(
  sessionId: string,
  payload: MessagePayload,
  onEvent: SSEEventHandler,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem('access_token')
  const url = `${API_BASE_URL}/api/v1/chat/${sessionId}/message`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    // Handle specific error codes
    if (response.status === 401) {
      throw new Error('Authentication required. Please login again.')
    }
    if (response.status === 403) {
      throw new Error('You do not have permission to access this session.')
    }
    if (response.status === 404) {
      throw new Error('Session not found.')
    }
    if (response.status === 409) {
      throw new Error('Session is already running. Please wait or stop the current execution.')
    }
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('Response body is null')
  }

  const decoder = new TextDecoder()
  let buffer = ''
  let currentEventType: SSEEventType = SSEEventType.CONTENT

  let isReading = true
  while (isReading) {
    const { done, value } = await reader.read()
    
    if (done) {
      isReading = false
      break
    }

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('event:')) {
        // Convert event type string to SSEEventType enum value
        const eventStr = line.substring(6).trim()
        // Find matching enum value (the string values in SSEEventType)
        const enumValue = Object.values(SSEEventType).find(v => v === eventStr)
        currentEventType = enumValue || SSEEventType.CONTENT
        continue
      }

      if (line.startsWith('data:')) {
        const data = line.substring(5).trim()
        if (data) {
          try {
            const parsedData = JSON.parse(data)
            // Create SSEEvent with correct structure (event, data, timestamp)
            onEvent({
              event: currentEventType,
              data: parsedData,
              timestamp: new Date().toISOString(),
            })
          } catch (e) {
            console.error('[MessageService] Failed to parse SSE data:', e)
          }
        }
      }
    }
  }
}

/**
 * Stop current Agent execution
 * 
 * @param sessionId - Session ID
 */
export async function stopExecution(sessionId: string): Promise<void> {
  const token = localStorage.getItem('access_token')
  const url = `${API_BASE_URL}/api/v1/chat/${sessionId}/stop`

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  })

  if (!response.ok) {
    throw new Error(`Failed to stop execution: ${response.status}`)
  }
}

/**
 * Create a message service instance for a session
 * 
 * This provides a more object-oriented API for managing message streams.
 */
export function createMessageService(sessionId: string) {
  let abortController: AbortController | null = null

  return {
    /**
     * Send message and stream response
     */
    async send(payload: MessagePayload, onEvent: SSEEventHandler): Promise<void> {
      // Cancel any existing stream
      if (abortController) {
        abortController.abort()
      }
      
      abortController = new AbortController()
      
      try {
        await sendMessage(sessionId, payload, onEvent, abortController.signal)
      } finally {
        abortController = null
      }
    },

    /**
     * Stop current execution
     */
    async stop(): Promise<void> {
      if (abortController) {
        abortController.abort()
        abortController = null
      }
      await stopExecution(sessionId)
    },

    /**
     * Cancel the current stream without stopping execution
     */
    cancel(): void {
      if (abortController) {
        abortController.abort()
        abortController = null
      }
    },

    /**
     * Check if currently streaming
     */
    get isStreaming(): boolean {
      return abortController !== null
    },
  }
}

export type MessageService = ReturnType<typeof createMessageService>

export default {
  sendMessage,
  stopExecution,
  createMessageService,
}
