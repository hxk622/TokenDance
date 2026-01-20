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
  
  // Agent events (new backend format)
  THINKING = 'thinking',
  TOOL_CALL = 'tool_call',
  TOOL_RESULT = 'tool_result',
  CONTENT = 'content',
  DONE = 'done',
  
  // Agent events (legacy format - keep for compatibility)
  AGENT_THINKING = 'agent_thinking',
  AGENT_TOOL_CALL = 'agent_tool_call',
  AGENT_TOOL_RESULT = 'agent_tool_result',
  AGENT_MESSAGE = 'agent_message',
  AGENT_ERROR = 'agent_error',
  
  // Workflow planning events (task decomposition)
  PLAN_CREATED = 'plan_created',
  NODE_CREATED = 'node_created',
  EDGE_CREATED = 'edge_created',
  PLAN_FINALIZED = 'plan_finalized',

  // Workflow node execution events
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
  
  // P1-3: Replay events (sent on reconnection)
  REPLAY_START = 'replay_start',
  REPLAY_END = 'replay_end',
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
  node_type: 'web' | 'local'  // web=云端数据, local=本地数据
  label: string
  status: 'pending' | 'active' | 'success' | 'failed'
  depends_on?: string[]
  metadata?: Record<string, any>
}

// Task planning events
export interface PlanCreatedEvent {
  total_nodes: number
}

export interface NodeCreatedEvent {
  node_id: string
  label: string
  type: 'web' | 'local'
  depends_on: string[]
}

export interface EdgeCreatedEvent {
  from: string
  to: string
  type: 'dependency' | 'data'
}

export interface PlanFinalizedEvent {
  node_count: number
  edge_count: number
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
 * SSE Connection Error
 */
export interface SSEConnectionError extends Error {
  statusCode?: number
  isFatal?: boolean // Non-recoverable error (404, 403, etc.)
}

/**
 * SSE Connection Options
 */
export interface SSEOptions {
  onEvent?: (event: SSEEvent) => void
  onError?: (error: SSEConnectionError) => void
  onOpen?: () => void
  onClose?: () => void
  reconnectDelay?: number
  maxReconnectAttempts?: number
  /** P1-3: Callback when replay starts */
  onReplayStart?: (lastSeq: number) => void
  /** P1-3: Callback when replay ends */
  onReplayEnd?: (replayedCount: number) => void
  /** P1-1: Callback to refresh SSE token on reconnection (tokens are single-use) */
  onTokenRefresh?: () => Promise<string | null>
}

/**
 * SSE Connection Class
 * 
 * P1-1: Supports SSE token authentication (preferred over JWT in URL)
 * P1-3: Supports event replay on reconnection via lastSeq parameter
 */
export class SSEConnection {
  private eventSource: EventSource | null = null
  private url: string
  private baseUrl: string
  private sessionId: string
  private options: Required<SSEOptions>
  private reconnectAttempts = 0
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private isClosed = false
  private hasFatalError = false // Track fatal errors (404, 403)
  private task: string | null = null
  
  /** P1-3: Track last received sequence number for replay */
  private lastSeq = 0
  /** P1-1: SSE token (preferred) */
  private sseToken: string | null = null
  /** Fallback JWT token (deprecated) */
  private jwtToken: string | null = null

  constructor(
    sessionId: string,
    options: SSEOptions = {},
    useDemo = false,
    task: string | null = null,
    sseToken: string | null = null
  ) {
    this.sessionId = sessionId
    this.task = task
    this.sseToken = sseToken
    this.jwtToken = localStorage.getItem('access_token')
    
    // Use demo endpoint for testing, or real session endpoint
    if (useDemo || sessionId === 'demo' || sessionId.startsWith('demo-')) {
      this.baseUrl = `${API_BASE_URL}/api/v1/demo/stream`
      this.url = this.baseUrl
    } else {
      this.baseUrl = `${API_BASE_URL}/api/v1/sessions/${sessionId}/stream`
      this.url = this.buildUrl()
    }
    
    this.options = {
      onEvent: options.onEvent || (() => {}),
      onError: options.onError || console.error,
      onOpen: options.onOpen || (() => {}),
      onClose: options.onClose || (() => {}),
      reconnectDelay: options.reconnectDelay || 3000,
      maxReconnectAttempts: options.maxReconnectAttempts || 10,
      onReplayStart: options.onReplayStart || (() => {}),
      onReplayEnd: options.onReplayEnd || (() => {}),
      onTokenRefresh: options.onTokenRefresh || (async () => null),
    }
  }
  
  /**
   * P1-1: Set SSE token (preferred authentication method)
   */
  setSSEToken(token: string): void {
    this.sseToken = token
    this.url = this.buildUrl()
  }
  
  /**
   * Build URL with authentication and replay parameters
   */
  private buildUrl(): string {
    const params = new URLSearchParams()
    
    // P1-1: Prefer SSE token over JWT token
    if (this.sseToken) {
      params.set('sse_token', this.sseToken)
    } else if (this.jwtToken) {
      // Deprecated: fallback to JWT token
      console.warn('[SSE] Using deprecated JWT token in URL. Use SSE token instead.')
      params.set('token', this.jwtToken)
    }
    
    if (this.task) {
      params.set('task', this.task)
    }
    
    // P1-3: Include last_seq for replay on reconnection
    if (this.lastSeq > 0) {
      params.set('last_seq', this.lastSeq.toString())
    }
    
    return `${this.baseUrl}?${params.toString()}`
  }

  /**
   * Connect to SSE stream
   */
  connect(): void {
    if (this.isClosed || this.hasFatalError) {
      console.warn('[SSE] Connection is closed or has fatal error, cannot reconnect')
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
          
          // P1-3: Track sequence number for replay
          if (data.data?._seq) {
            this.lastSeq = data.data._seq
          }
          
          // P1-3: Handle replay events
          if (data.event === SSEEventType.REPLAY_START) {
            this.options.onReplayStart(data.data?.last_seq || 0)
          } else if (data.event === SSEEventType.REPLAY_END) {
            this.options.onReplayEnd(data.data?.replayed_count || 0)
          }
          
          this.options.onEvent(data)
        } catch (error) {
          console.error('[SSE] Failed to parse event data:', error)
        }
      }

      // Error handler
      this.eventSource.onerror = (event) => {
        const target = event.target as EventSource
        
        // Check EventSource readyState to detect fatal HTTP errors
        // CLOSED (2) means the connection failed (likely 404, 403, 429, etc.)
        if (target.readyState === EventSource.CLOSED) {
          // Try to fetch the URL to get actual HTTP status
          this.detectHTTPError().then(statusCode => {
            const isFatal = statusCode === 404 || statusCode === 403 || statusCode === 401
            
            const error: SSEConnectionError = new Error(
              isFatal 
                ? `SSE connection failed: HTTP ${statusCode}` 
                : 'SSE connection error'
            ) as SSEConnectionError
            error.statusCode = statusCode
            error.isFatal = isFatal
            
            console.error(`[SSE] Connection error: HTTP ${statusCode || 'unknown'}`, { isFatal })
            this.options.onError(error)
            
            // Stop reconnecting on fatal errors
            if (isFatal) {
              console.error('[SSE] Fatal error detected, stopping reconnection')
              this.hasFatalError = true
              this.close()
              return
            }
            
            // Attempt reconnection with exponential backoff
            if (!this.isClosed && this.reconnectAttempts < this.options.maxReconnectAttempts) {
              this.reconnectAttempts++
              
              // Exponential backoff: delay = baseDelay * 2^(attempts - 1)
              const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
              const cappedDelay = Math.min(delay, 30000) // Max 30s
              
              console.log(`[SSE] Reconnecting in ${cappedDelay}ms (attempt ${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`)
              
              this.eventSource?.close()
              
              this.reconnectTimer = setTimeout(async () => {
                // P1-1: Refresh SSE token before reconnecting (tokens are single-use)
                try {
                  const newToken = await this.options.onTokenRefresh()
                  if (newToken) {
                    this.sseToken = newToken
                    console.log('[SSE] Token refreshed for reconnection')
                  }
                } catch (err) {
                  console.warn('[SSE] Failed to refresh token:', err)
                }
                
                // P1-3: Update URL with last_seq for replay and new token
                this.url = this.buildUrl()
                
                this.connect()
              }, cappedDelay)
            } else if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
              console.error('[SSE] Max reconnect attempts reached')
              this.close()
            }
          })
        }
      }

      // Register specific event handlers
      Object.values(SSEEventType).forEach((eventType) => {
        this.eventSource?.addEventListener(eventType, (event: Event) => {
          const messageEvent = event as MessageEvent
          try {
            // Handle edge case: "undefined" string or empty data
            if (!messageEvent.data || messageEvent.data === 'undefined' || messageEvent.data.trim() === '') {
              console.warn(`[SSE] Received empty or undefined data for ${eventType}, skipping`)
              return
            }

            const parsedData = JSON.parse(messageEvent.data)

            // P1-3: Track sequence number
            if (parsedData._seq) {
              this.lastSeq = parsedData._seq
            }

            const sseEvent: SSEEvent = {
              event: eventType as SSEEventType,
              data: parsedData,
              timestamp: new Date().toISOString(),
            }

            // P1-3: Handle replay events
            if (eventType === SSEEventType.REPLAY_START) {
              this.options.onReplayStart(parsedData.last_seq || 0)
            } else if (eventType === SSEEventType.REPLAY_END) {
              this.options.onReplayEnd(parsedData.replayed_count || 0)
            }

            this.options.onEvent(sseEvent)
          } catch (error) {
            console.error(`[SSE] Failed to parse ${eventType} event:`, error, 'Raw data:', messageEvent.data)
          }
        })
      })
    } catch (error) {
      console.error('[SSE] Failed to create EventSource:', error)
      this.options.onError(error as Error)
    }
  }

  /**
   * Detect HTTP error by attempting a HEAD request
   * EventSource doesn't expose HTTP status, so we probe manually
   */
  private async detectHTTPError(): Promise<number | undefined> {
    try {
      const response = await fetch(this.url, { 
        method: 'HEAD',
        headers: {
          'Accept': 'text/event-stream'
        }
      })
      return response.status
    } catch (error) {
      console.warn('[SSE] Could not detect HTTP status:', error)
      return undefined
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
  
  /**
   * P1-3: Get last received sequence number
   */
  getLastSeq(): number {
    return this.lastSeq
  }
}

/**
 * Create SSE connection for a session
 * @param sessionId - Session ID
 * @param options - SSE options
 * @param useDemo - Whether to use demo endpoint
 * @param task - Task to execute (triggers agent execution if provided)
 * @param sseToken - P1-1: Short-lived SSE token (preferred over JWT)
 */
export function createSSEConnection(
  sessionId: string,
  options: SSEOptions = {},
  useDemo = false,
  task: string | null = null,
  sseToken: string | null = null
): SSEConnection {
  const connection = new SSEConnection(sessionId, options, useDemo, task, sseToken)
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
