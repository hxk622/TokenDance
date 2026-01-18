/**
 * Server-Sent Events (SSE) Service
 * For real-time Agent execution streaming
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export enum SSEEventType {
  // Session events
  SESSION_STARTED = 'session_started',
  SESSION_COMPLETED = 'session_completed',
  SESSION_FAILED = 'session_failed',
  
  // Skill events
  SKILL_MATCHED = 'skill_matched',
  SKILL_COMPLETED = 'skill_completed',
  
  // Agent events
  AGENT_THINKING = 'agent_thinking',
  AGENT_TOOL_CALL = 'agent_tool_call',
  AGENT_TOOL_RESULT = 'agent_tool_result',
  AGENT_MESSAGE = 'agent_message',
  AGENT_ERROR = 'agent_error',
  
  // Workflow node events
  NODE_STARTED = 'node_started',
  NODE_COMPLETED = 'node_completed',
  NODE_FAILED = 'node_failed',
  
  // File events
  FILE_CREATED = 'file_created',
  FILE_MODIFIED = 'file_modified',
  FILE_DELETED = 'file_deleted',
  FILE_READ = 'file_read',
  
  // Browser events
  BROWSER_OPENED = 'browser_opened',
  BROWSER_NAVIGATED = 'browser_navigated',
  BROWSER_ACTION = 'browser_action',
  BROWSER_SCREENSHOT = 'browser_screenshot',
  BROWSER_CLOSED = 'browser_closed',
  
  // HITL events
  HITL_REQUEST = 'hitl_request',
  HITL_TIMEOUT = 'hitl_timeout',
  
  // Artifact events
  ARTIFACT_CREATED = 'artifact_created',
  ARTIFACT_UPDATED = 'artifact_updated',
  
  // Progress events
  PROGRESS_UPDATE = 'progress_update',
  ITERATION_START = 'iteration_start',
  
  // Token/Cost events
  TOKEN_USAGE = 'token_usage',
  
  // System events
  PING = 'ping',
  ERROR = 'error',
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

// Skill events
export interface SkillMatchedEvent {
  skill_id: string
  skill_name: string
  display_name: string
  description?: string
  icon?: string
  color?: string
  confidence?: number
}

export interface SkillCompletedEvent {
  skill_id: string
  status: 'success' | 'error'
  duration_ms?: number
}

// Browser events
export interface BrowserEvent {
  browser_id: string
  url?: string
  title?: string
  action?: string
  target?: string
  value?: string
  path?: string
}

// HITL events
export interface HITLRequestEvent {
  request_id: string
  tool: string
  args: Record<string, any>
  risk_level: 'low' | 'medium' | 'high' | 'critical'
  description: string
  timeout?: number
}

// Artifact events
export interface ArtifactEvent {
  artifact_id: string
  type: string
  name: string
  path?: string
  changes?: string
}

// Progress events
export interface ProgressEvent {
  current: number
  total: number
  message?: string
  percentage: number
}

export interface IterationEvent {
  iteration: number
  max_iterations: number
}

// Token usage event
export interface TokenUsageEvent {
  input_tokens: number
  output_tokens: number
  total_tokens: number
  model?: string
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

  private task: string | null = null

  constructor(sessionId: string, options: SSEOptions = {}, useDemo = false, task: string | null = null) {
    const token = localStorage.getItem('access_token')
    this.task = task
    
    // Use demo endpoint for testing, or real session endpoint
    if (useDemo || sessionId === 'demo' || sessionId.startsWith('demo-')) {
      this.url = `${API_BASE_URL}/api/v1/demo/stream`
    } else {
      const params = new URLSearchParams()
      if (token) params.set('token', token)
      if (task) params.set('task', task)
      this.url = `${API_BASE_URL}/api/v1/sessions/${sessionId}/stream?${params.toString()}`
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
 * @param sessionId - Session ID
 * @param options - SSE options
 * @param useDemo - Whether to use demo endpoint
 * @param task - Task to execute (triggers agent execution if provided)
 */
export function createSSEConnection(
  sessionId: string,
  options: SSEOptions = {},
  useDemo = false,
  task: string | null = null
): SSEConnection {
  const connection = new SSEConnection(sessionId, options, useDemo, task)
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
