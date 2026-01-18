/**
 * Execution Store
 * Pinia store for managing Agent execution state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  sessionService,
  createSSEConnection,
  SSEConnection,
  SSEEventType,
  type SSEEvent,
  type SessionDetail,
  type Message,
  type Artifact,
} from '@/api/services'

/**
 * Workflow Node for UI
 */
export interface WorkflowNode {
  id: string
  type: 'manus' | 'coworker'
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
  label: string
  x: number
  y: number
  metadata?: {
    startTime?: number
    duration?: number
    output?: string
  }
}

/**
 * Workflow Edge for UI
 */
export interface WorkflowEdge {
  id: string
  from: string
  to: string
  type: 'context' | 'result'
  active: boolean
}

/**
 * Log Entry for StreamingInfo
 */
export interface LogEntry {
  id: string
  nodeId: string
  timestamp: number
  type: 'thinking' | 'tool-call' | 'result' | 'error'
  content: string
}

/**
 * File Operation for CoworkerFileTree
 */
export interface FileOperation {
  path: string
  action: 'read' | 'modified' | 'created' | 'deleted'
  timestamp: number
}

/**
 * Browser Operation for BrowserOperationLog
 */
export interface BrowserOperation {
  id: string
  type: 'open' | 'navigate' | 'click' | 'fill' | 'snapshot' | 'screenshot' | 'close'
  url?: string
  target?: string
  value?: string
  status: 'pending' | 'running' | 'success' | 'error'
  result?: string
  error?: string
  duration?: number
  timestamp: string
  screenshotPath?: string
}

/**
 * Current Skill Info for SkillIndicator
 */
export interface CurrentSkillInfo {
  id: string
  name: string
  displayName: string
  description?: string
  icon?: string
  color?: string
  matchedAt: number
  confidence?: number
}

/**
 * Progress Info
 */
export interface ProgressInfo {
  current: number
  total: number
  message?: string
  percentage: number
}

/**
 * Token Usage Info
 */
export interface TokenUsageInfo {
  inputTokens: number
  outputTokens: number
  totalTokens: number
  model?: string
}

/**
 * HITL Request
 */
export interface HITLRequest {
  requestId: string
  tool: string
  args: Record<string, unknown>
  riskLevel: 'low' | 'medium' | 'high' | 'critical'
  description: string
  timeout?: number
  timestamp: number
}

export const useExecutionStore = defineStore('execution', () => {
  // Session state
  const sessionId = ref<string | null>(null)
  const session = ref<SessionDetail | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Workflow state
  const nodes = ref<WorkflowNode[]>([])
  const edges = ref<WorkflowEdge[]>([])

  // Logs state
  const logs = ref<LogEntry[]>([])
  const maxLogs = 1000

  // File operations state
  const fileOperations = ref<FileOperation[]>([])

  // Browser operations state
  const browserOperations = ref<BrowserOperation[]>([])

  // Current skill state
  const currentSkill = ref<CurrentSkillInfo | null>(null)
  const skillHistory = ref<CurrentSkillInfo[]>([])

  // Progress state
  const progress = ref<ProgressInfo | null>(null)
  const currentIteration = ref(0)
  const maxIterations = ref(50)

  // Token usage state
  const tokenUsage = ref<TokenUsageInfo | null>(null)

  // HITL state
  const pendingHITL = ref<HITLRequest | null>(null)

  // Messages & Artifacts
  const messages = ref<Message[]>([])
  const artifacts = ref<Artifact[]>([])

  // SSE connection
  let sseConnection: SSEConnection | null = null

  // Current task
  const currentTask = ref<string | null>(null)

  // Pause state
  const isPaused = ref(false)

  // Computed
  const isRunning = computed(() => session.value?.status === 'running' && !isPaused.value)
  const isCompleted = computed(() => session.value?.status === 'completed')
  const activeNodeId = computed(() => nodes.value.find(n => n.status === 'active')?.id)
  const progressPercentage = computed(() => progress.value?.percentage || 0)

  /**
   * Load session data
   */
  async function loadSession(id: string) {
    try {
      isLoading.value = true
      error.value = null
      sessionId.value = id

      // Fetch session details
      const sessionData = await sessionService.getSession(id, true) as SessionDetail
      session.value = sessionData

      // Fetch messages
      const messageResponse = await sessionService.getSessionMessages(id)
      messages.value = messageResponse.messages

      // Fetch artifacts
      const artifactResponse = await sessionService.getSessionArtifacts(id)
      artifacts.value = artifactResponse.artifacts

      // Initialize workflow nodes from session metadata
      initializeWorkflow()

    } catch (err: any) {
      error.value = err.message || 'Failed to load session'
      console.error('[ExecutionStore] Load session error:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Initialize workflow from session metadata
   */
  function initializeWorkflow() {
    // TODO: Parse actual workflow from session metadata
    // For now, use mock data
    nodes.value = [
      {
        id: '1',
        type: 'manus',
        status: 'success',
        label: '搜索市场数据',
        x: 100,
        y: 100,
        metadata: { duration: 45000 }
      },
      {
        id: '2',
        type: 'manus',
        status: 'success',
        label: '分析竞品',
        x: 300,
        y: 100,
        metadata: { duration: 38000 }
      },
      {
        id: '3',
        type: 'coworker',
        status: 'active',
        label: '生成报告',
        x: 500,
        y: 100,
        metadata: { duration: 15000 }
      },
      {
        id: '4',
        type: 'manus',
        status: 'inactive',
        label: '创建PPT',
        x: 700,
        y: 100
      },
    ]

    edges.value = [
      { id: 'e1', from: '1', to: '2', type: 'context', active: true },
      { id: 'e2', from: '2', to: '3', type: 'context', active: true },
      { id: 'e3', from: '3', to: '4', type: 'result', active: false },
    ]
  }

  /**
   * Connect to SSE stream
   * @param task - Task to execute (triggers agent execution if provided)
   */
  function connectSSE(task: string | null = null) {
    if (!sessionId.value) return

    currentTask.value = task

    sseConnection = createSSEConnection(
      sessionId.value,
      {
        onEvent: handleSSEEvent,
        onError: (err) => {
          console.error('[ExecutionStore] SSE error:', err)
          error.value = 'Connection lost'
        },
        onOpen: () => {
          console.log('[ExecutionStore] SSE connected')
        },
        onClose: () => {
          console.log('[ExecutionStore] SSE disconnected')
        },
      },
      false, // useDemo
      task   // task parameter
    )
  }

  /**
   * Handle SSE event
   */
  function handleSSEEvent(event: SSEEvent) {
    switch (event.event) {
      case SSEEventType.AGENT_THINKING:
        addLog({
          type: 'thinking',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: event.data.content,
        })
        break

      case SSEEventType.AGENT_TOOL_CALL:
        addLog({
          type: 'tool-call',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: `${event.data.tool_name}(${JSON.stringify(event.data.arguments)})`,
        })
        break

      case SSEEventType.AGENT_TOOL_RESULT:
        addLog({
          type: event.data.success ? 'result' : 'error',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: event.data.success
            ? JSON.stringify(event.data.result)
            : event.data.error || 'Unknown error',
        })
        break

      case SSEEventType.NODE_STARTED:
        updateNodeStatus(event.data.node_id, 'active')
        break

      case SSEEventType.NODE_COMPLETED:
        updateNodeStatus(event.data.node_id, 'success')
        break

      case SSEEventType.NODE_FAILED:
        updateNodeStatus(event.data.node_id, 'error')
        break

      case SSEEventType.FILE_CREATED:
      case SSEEventType.FILE_MODIFIED:
      case SSEEventType.FILE_DELETED:
        addFileOperation({
          path: event.data.path,
          action: event.event === SSEEventType.FILE_CREATED
            ? 'created'
            : event.event === SSEEventType.FILE_MODIFIED
            ? 'modified'
            : 'deleted',
          timestamp: Date.now(),
        })
        break

      case SSEEventType.SESSION_COMPLETED:
        if (session.value) {
          session.value.status = 'completed' as any
        }
        break

      case SSEEventType.SESSION_FAILED:
        if (session.value) {
          session.value.status = 'failed' as any
        }
        break

      // Skill events
      case SSEEventType.SKILL_MATCHED:
        setCurrentSkill({
          id: event.data.skill_id,
          name: event.data.skill_name,
          displayName: event.data.display_name || event.data.skill_name,
          description: event.data.description,
          icon: event.data.icon,
          color: event.data.color,
          matchedAt: Date.now(),
          confidence: event.data.confidence,
        })
        addLog({
          type: 'thinking',
          nodeId: activeNodeId.value || '0',
          content: `匹配 Skill: ${event.data.display_name || event.data.skill_name}`,
        })
        break

      case SSEEventType.SKILL_COMPLETED:
        clearCurrentSkill()
        break

      // Browser events
      case SSEEventType.BROWSER_OPENED:
        addBrowserOperation({
          id: event.data.browser_id || crypto.randomUUID(),
          type: 'open',
          url: event.data.url,
          status: 'success',
          timestamp: new Date().toISOString(),
        })
        break

      case SSEEventType.BROWSER_NAVIGATED:
        addBrowserOperation({
          id: event.data.browser_id || crypto.randomUUID(),
          type: 'navigate',
          url: event.data.url,
          status: 'success',
          timestamp: new Date().toISOString(),
        })
        break

      case SSEEventType.BROWSER_ACTION:
        addBrowserOperation({
          id: event.data.browser_id || crypto.randomUUID(),
          type: event.data.action as BrowserOperation['type'] || 'click',
          target: event.data.target,
          value: event.data.value,
          status: 'success',
          timestamp: new Date().toISOString(),
        })
        break

      case SSEEventType.BROWSER_SCREENSHOT:
        addBrowserOperation({
          id: event.data.browser_id || crypto.randomUUID(),
          type: 'screenshot',
          screenshotPath: event.data.path,
          status: 'success',
          timestamp: new Date().toISOString(),
        })
        break

      case SSEEventType.BROWSER_CLOSED:
        addBrowserOperation({
          id: event.data.browser_id || crypto.randomUUID(),
          type: 'close',
          status: 'success',
          timestamp: new Date().toISOString(),
        })
        break

      // HITL events
      case SSEEventType.HITL_REQUEST:
        pendingHITL.value = {
          requestId: event.data.request_id,
          tool: event.data.tool,
          args: event.data.args,
          riskLevel: event.data.risk_level,
          description: event.data.description,
          timeout: event.data.timeout,
          timestamp: Date.now(),
        }
        break

      case SSEEventType.HITL_TIMEOUT:
        if (pendingHITL.value?.requestId === event.data.request_id) {
          pendingHITL.value = null
        }
        break

      // Artifact events
      case SSEEventType.ARTIFACT_CREATED:
      case SSEEventType.ARTIFACT_UPDATED:
        // Refresh artifacts list
        if (sessionId.value) {
          sessionService.getSessionArtifacts(sessionId.value).then(res => {
            artifacts.value = res.artifacts
          })
        }
        break

      // Progress events
      case SSEEventType.PROGRESS_UPDATE:
        progress.value = {
          current: event.data.current,
          total: event.data.total,
          message: event.data.message,
          percentage: event.data.percentage,
        }
        break

      case SSEEventType.ITERATION_START:
        currentIteration.value = event.data.iteration
        maxIterations.value = event.data.max_iterations
        break

      // Token usage events
      case SSEEventType.TOKEN_USAGE:
        tokenUsage.value = {
          inputTokens: event.data.input_tokens,
          outputTokens: event.data.output_tokens,
          totalTokens: event.data.total_tokens,
          model: event.data.model,
        }
        break

      // System events
      case SSEEventType.ERROR:
        error.value = event.data.message
        addLog({
          type: 'error',
          nodeId: activeNodeId.value || '0',
          content: event.data.message,
        })
        break

      case SSEEventType.PING:
        // Keepalive, no action needed
        break
    }
  }

  /**
   * Add log entry
   */
  function addLog(entry: Omit<LogEntry, 'id' | 'timestamp'>) {
    const newLog: LogEntry = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      ...entry,
    }

    logs.value.push(newLog)

    // Limit log count
    if (logs.value.length > maxLogs) {
      logs.value = logs.value.slice(-maxLogs)
    }
  }

  /**
   * Update node status
   */
  function updateNodeStatus(nodeId: string, status: WorkflowNode['status']) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      node.status = status
    }

    // Update edges
    if (status === 'active') {
      edges.value.forEach(edge => {
        if (edge.to === nodeId) {
          edge.active = true
        }
      })
    }
  }

  /**
   * Add file operation
   */
  function addFileOperation(op: FileOperation) {
    fileOperations.value.unshift(op)

    // Limit count
    if (fileOperations.value.length > 100) {
      fileOperations.value = fileOperations.value.slice(0, 100)
    }
  }

  /**
   * Add browser operation
   */
  function addBrowserOperation(op: BrowserOperation) {
    browserOperations.value.unshift(op)

    // Limit count
    if (browserOperations.value.length > 100) {
      browserOperations.value = browserOperations.value.slice(0, 100)
    }
  }

  /**
   * Set current skill
   */
  function setCurrentSkill(skill: CurrentSkillInfo) {
    // Save previous skill to history
    if (currentSkill.value) {
      skillHistory.value.unshift(currentSkill.value)
      // Limit history
      if (skillHistory.value.length > 10) {
        skillHistory.value = skillHistory.value.slice(0, 10)
      }
    }
    currentSkill.value = skill
  }

  /**
   * Clear current skill
   */
  function clearCurrentSkill() {
    if (currentSkill.value) {
      skillHistory.value.unshift(currentSkill.value)
      if (skillHistory.value.length > 10) {
        skillHistory.value = skillHistory.value.slice(0, 10)
      }
    }
    currentSkill.value = null
  }

  /**
   * Clear HITL request
   */
  function clearHITLRequest() {
    pendingHITL.value = null
  }

  /**
   * Pause execution
   */
  function pause() {
    isPaused.value = true
    // TODO: Call API to pause backend execution
  }

  /**
   * Resume execution
   */
  function resume() {
    isPaused.value = false
    // TODO: Call API to resume backend execution
  }

  /**
   * Disconnect SSE and cleanup
   */
  function disconnect() {
    sseConnection?.close()
    sseConnection = null
  }

  /**
   * Reset store
   */
  function reset() {
    disconnect()
    sessionId.value = null
    session.value = null
    currentTask.value = null
    nodes.value = []
    edges.value = []
    logs.value = []
    fileOperations.value = []
    browserOperations.value = []
    currentSkill.value = null
    skillHistory.value = []
    progress.value = null
    currentIteration.value = 0
    tokenUsage.value = null
    pendingHITL.value = null
    messages.value = []
    artifacts.value = []
    error.value = null
  }

  return {
    // State
    sessionId,
    session,
    currentTask,
    isLoading,
    error,
    nodes,
    edges,
    logs,
    fileOperations,
    browserOperations,
    currentSkill,
    skillHistory,
    progress,
    currentIteration,
    maxIterations,
    tokenUsage,
    pendingHITL,
    messages,
    artifacts,

    // Computed
    isRunning,
    isCompleted,
    isPaused,
    activeNodeId,
    progressPercentage,

    // Actions
    loadSession,
    pause,
    resume,
    connectSSE,
    disconnect,
    reset,
    addLog,
    updateNodeStatus,
    addFileOperation,
    addBrowserOperation,
    setCurrentSkill,
    clearCurrentSkill,
    clearHITLRequest,
  }
})
