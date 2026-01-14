/**
 * Server-Sent Events (SSE) Service
 * For real-time Agent execution streaming
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export enum SSEEventType {
  // Agent events
  AGENT_THINKING = 'agent_thinking',
  AGENT_TOOL_CALL = 'agent_tool_call',
  AGENT_TOOL_RESULT = 'agent_tool_result',
  AGENT_MESSAGE = 'agent_message',
  AGENT_ERROR = 'agent_error',
  
  // Session events
  SESSION_STARTED = 'session_started',
  SESSION_COMPLETED = 'session_completed',
  SESSION_FAILED = 'session_failed',
  
  // Workflow events
  NODE_STARTED = 'node_started',
  NODE_COMPLETED = 'node_completed',
  NODE_FAILED = 'node_failed',
  
  // File events
  FILE_CREATED = 'file_created',
  FILE_MODIFIED = 'file_modified',
  FILE_DELETED = 'file_deleted',
  
  // Keepalive
  PING = 'ping',
}

export interface SSEEvent<T = any> {
  event: SSEEventType
  data: T
  timestamp: string
}

export interface AgentThinkingEvent {
  content: string
  node_id?: string
}

export interface AgentToolCallEvent {
  tool_name: string
  arguments: Record<string, any>
  node_id?: string
}

export interface AgentToolResultEvent {
  tool_name: string
  result: any
  success: boolean
  error?: string
  node_id?: string
}

export interface NodeEvent {
  node_id: string
  node_type: 'manus' | 'coworker'
  label: string
  status: 'active' | 'success' | 'failed'
  metadata?: Record<string, any>
}

export interface FileEvent {
  path: string
  action: 'read' | 'created' | 'modified' | 'deleted'
  content?: string
}

/**
 * SSE Connection Options
 */
export interface SSEOptions {
  onEvent?: (event: SSEEvent) => void
  onError?: (error: Error) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectDelay?: number
  maxReconnectAttempts?: number
}

/**
 * SSE Connection Class
 */
export class SSEConnection {
  private eventSource: EventSource | null = null
  private url: string
  private options: Required<SSEOptions>
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isClosed = false

  constructor(sessionId: string, options: SSEOptions = {}, useDemo = false) {
    const token = localStorage.getItem('access_token')
    
    // Use demo endpoint for testing, or real session endpoint
    if (useDemo || sessionId === 'demo' || sessionId.startsWith('demo-')) {
      this.url = `${API_BASE_URL}/api/v1/demo/stream`
    } else {
      this.url = `${API_BASE_URL}/api/v1/sessions/${sessionId}/stream?token=${token || ''}`
    }
    
    this.options = {
      onEvent: options.onEvent || (() => {}),
      onError: options.onError || console.error,
      onOpen: options.onOpen || (() => {}),
      onClose: options.onClose || (() => {}),
      reconnectDelay: options.reconnectDelay || 3000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
    }
  }

  /**
   * Connect to SSE stream
   */
  connect(): void {
    if (this.isClosed) {
      console.warn('SSE connection is closed, cannot reconnect')
      return
    }

    try {
      this.eventSource = new EventSource(this.url)

      // Connection opened
      this.eventSource.onopen = () => {
        console.log('[SSE] Connection opened')
        this.reconnectAttempts = 0
        this.options.onOpen()
      }

      // Generic message handler
      this.eventSource.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data) as SSEEvent
          this.options.onEvent(data)
        } catch (error) {
          console.error('[SSE] Failed to parse event data:', error)
        }
      }

      // Error handler
      this.eventSource.onerror = (error) => {
        console.error('[SSE] Connection error:', error)
        this.options.onError(new Error('SSE connection error'))

        // Attempt to reconnect
        if (!this.isClosed && this.reconnectAttempts < this.options.maxReconnectAttempts) {
          this.reconnectAttempts++
          console.log(`[SSE] Reconnecting... (attempt ${this.reconnectAttempts})`)
          
          this.eventSource?.close()
          this.reconnectTimer = setTimeout(() => {
            this.connect()
          }, this.options.reconnectDelay)
        } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
          console.error('[SSE] Max reconnect attempts reached')
          this.close()
        }
      }

      // Register specific event handlers
      Object.values(SSEEventType).forEach((eventType) => {
        this.eventSource?.addEventListener(eventType, (event: Event) => {
          const messageEvent = event as MessageEvent
          try {
            const parsedData = JSON.parse(messageEvent.data)
            const sseEvent: SSEEvent = {
              event: eventType as SSEEventType,
              data: parsedData,
              timestamp: new Date().toISOString(),
            }
            this.options.onEvent(sseEvent)
          } catch (error) {
            console.error(`[SSE] Failed to parse ${eventType} event:`, error)
          }
        })
      })
    } catch (error) {
      console.error('[SSE] Failed to create EventSource:', error)
      this.options.onError(error as Error)
    }
  }

  /**
   * Close SSE connection
   */
  close(): void {
    this.isClosed = true
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
      console.log('[SSE] Connection closed')
      this.options.onClose()
    }
  }

  /**
   * Check if connection is active
   */
  isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN
  }
}

/**
 * Create SSE connection for a session
 */
export function createSSEConnection(
  sessionId: string,
  options: SSEOptions = {},
  useDemo = false
): SSEConnection {
  const connection = new SSEConnection(sessionId, options, useDemo)
  connection.connect()
  return connection
}

/**
 * Create SSE connection to demo stream (for testing)
 */
export function createDemoSSEConnection(
  options: SSEOptions = {}
): SSEConnection {
  return createSSEConnection('demo', options, true)
}

export default {
  SSEEventType,
  SSEConnection,
  createSSEConnection,
}
