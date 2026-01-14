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

  // Messages & Artifacts
  const messages = ref<Message[]>([])
  const artifacts = ref<Artifact[]>([])

  // SSE connection
  let sseConnection: SSEConnection | null = null

  // Computed
  const isRunning = computed(() => session.value?.status === 'running')
  const isCompleted = computed(() => session.value?.status === 'completed')
  const activeNodeId = computed(() => nodes.value.find(n => n.status === 'active')?.id)

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
   */
  function connectSSE() {
    if (!sessionId.value) return

    sseConnection = createSSEConnection(sessionId.value, {
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
    })
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
    nodes.value = []
    edges.value = []
    logs.value = []
    fileOperations.value = []
    messages.value = []
    artifacts.value = []
    error.value = null
  }

  return {
    // State
    sessionId,
    session,
    isLoading,
    error,
    nodes,
    edges,
    logs,
    fileOperations,
    messages,
    artifacts,

    // Computed
    isRunning,
    isCompleted,
    activeNodeId,

    // Actions
    loadSession,
    connectSSE,
    disconnect,
    reset,
    addLog,
    updateNodeStatus,
    addFileOperation,
  }
})
