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
  SessionStatus,
  type SSEEvent,
  type SSEConnectionError,
  type SessionDetail,
  type Message,
  type Artifact,
} from '@/api/services'
import { useWorkflowStore } from './workflow'
import type { Citation } from '@/components/execution/research/types'

/**
 * Workflow Node for UI
 */
export interface WorkflowNode {
  id: string
  type: 'web' | 'local'  // web=云端数据, local=本地数据
  status: 'pending' | 'active' | 'success' | 'error'
  label: string
  x: number
  y: number
  dependsOn?: string[]  // 依赖的节点 ID 列表
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
  type: 'thinking' | 'tool-call' | 'result' | 'error' | 'timeline-search' | 'timeline-read' | 'timeline-screenshot' | 'timeline-finding' | 'timeline-milestone'
  content: string
  // Timeline 特有字段
  timelineData?: {
    title?: string
    description?: string
    url?: string
    query?: string
    resultsCount?: number
    screenshotPath?: string
    sourceUrl?: string
  }
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
  
  // SSE connection state
  const sseConnectionState = ref<'disconnected' | 'connecting' | 'connected' | 'error' | 'fatal_error'>('disconnected')
  const sseError = ref<string | null>(null)

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

  // Research report state (for citation tracking)
  const reportContent = ref<string>('')
  const citations = ref<Citation[]>([])

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
      
      // Clean up SSE connection on session load failure
      disconnect()
      
      // Set fatal error state if session not found
      if (err.response?.status === 404) {
        sseConnectionState.value = 'fatal_error'
        sseError.value = 'Session not found'
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Initialize workflow from session metadata
   * Workflow will be dynamically built from SSE events
   */
  function initializeWorkflow() {
    // 不再创建固定节点，等待 SSE 事件动态构建工作流
    nodes.value = []
    edges.value = []
  }

  /**
   * Calculate node position based on index (horizontal layout)
   */
  function calculateNodePosition(index: number): { x: number; y: number } {
    const baseX = 150
    const baseY = 100
    const spacingX = 180
    return {
      x: baseX + index * spacingX,
      y: baseY,
    }
  }

  /**
   * Connect to SSE stream
   * P1-1: First exchanges JWT for SSE token, then connects with SSE token
   * @param task - Task to execute (triggers agent execution if provided)
   */
  async function connectSSE(task: string | null = null) {
    if (!sessionId.value) return
    
    // Don't connect if we have a fatal error
    if (sseConnectionState.value === 'fatal_error') {
      console.warn('[ExecutionStore] Skipping SSE connection due to fatal error')
      return
    }

    currentTask.value = task
    sseConnectionState.value = 'connecting'
    sseError.value = null
    
    // P1-1: Get SSE token first (exchange JWT for short-lived SSE token)
    let sseToken: string | null = null
    try {
      const tokenResponse = await sessionService.getSSEToken(sessionId.value)
      sseToken = tokenResponse.sse_token
      console.log('[ExecutionStore] SSE token obtained, expires in', tokenResponse.expires_in, 'seconds')
    } catch (tokenErr: any) {
      console.warn('[ExecutionStore] Failed to get SSE token, falling back to JWT:', tokenErr.message)
      // Fall back to JWT token (deprecated but still supported)
    }

    sseConnection = createSSEConnection(
      sessionId.value,
      {
        onEvent: handleSSEEvent,
        onError: (err: SSEConnectionError) => {
          console.error('[ExecutionStore] SSE error:', err)
          
          // Update connection state based on error type
          if (err.isFatal) {
            sseConnectionState.value = 'fatal_error'
            sseError.value = err.message
            error.value = err.statusCode === 404 
              ? 'Session not found' 
              : err.statusCode === 403 
              ? 'Access denied' 
              : err.message
          } else {
            sseConnectionState.value = 'error'
            sseError.value = 'Connection lost, retrying...'
          }
        },
        onOpen: () => {
          console.log('[ExecutionStore] SSE connected')
          sseConnectionState.value = 'connected'
          sseError.value = null
        },
        onClose: () => {
          console.log('[ExecutionStore] SSE disconnected')
          if (sseConnectionState.value === 'connected' || sseConnectionState.value === 'connecting') {
            sseConnectionState.value = 'disconnected'
          }
        },
        // P1-3: Handle replay events
        onReplayStart: (lastSeq: number) => {
          console.log('[ExecutionStore] SSE replay starting from seq:', lastSeq)
        },
        onReplayEnd: (replayedCount: number) => {
          console.log('[ExecutionStore] SSE replay ended, replayed', replayedCount, 'events')
        },
        // P1-1: Refresh SSE token on reconnection (tokens are single-use)
        onTokenRefresh: async () => {
          if (!sessionId.value) return null
          try {
            const tokenResponse = await sessionService.getSSEToken(sessionId.value)
            console.log('[ExecutionStore] SSE token refreshed for reconnection')
            return tokenResponse.sse_token
          } catch (err: any) {
            console.warn('[ExecutionStore] Failed to refresh SSE token:', err.message)
            return null
          }
        },
      },
      false,     // useDemo
      task,      // task parameter
      sseToken   // P1-1: SSE token (preferred over JWT)
    )
  }
  
  /**
   * P1-2: Stop agent execution
   */
  async function stopExecution(reason?: string) {
    if (!sessionId.value) return
    
    try {
      const result = await sessionService.stopSession(sessionId.value, reason)
      if (result.success) {
        console.log('[ExecutionStore] Stop signal sent:', result.message)
        // Update local session status
        if (session.value) {
          session.value.status = SessionStatus.CANCELLED
        }
      }
    } catch (err: any) {
      console.error('[ExecutionStore] Failed to stop execution:', err.message)
      error.value = 'Failed to stop execution: ' + err.message
    }
  }

  /**
   * Handle SSE event
   */
  function handleSSEEvent(event: SSEEvent) {
    console.log('[ExecutionStore] SSE event received:', event.event, event.data)
    
    switch (event.event) {
      // Session lifecycle events
      case SSEEventType.SESSION_STARTED:
        if (session.value) {
          session.value.status = SessionStatus.RUNNING
        }
        break

      // Backend actual events: thinking, tool_call, tool_result, content, done
      case SSEEventType.THINKING:
      case SSEEventType.AGENT_THINKING:
        addLog({
          type: 'thinking',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: event.data.content,
        })
        break

      case SSEEventType.TOOL_CALL:
      case SSEEventType.AGENT_TOOL_CALL:
        addLog({
          type: 'tool-call',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: `${event.data.tool_name || event.data.name}(${JSON.stringify(event.data.arguments || event.data.args)})`,
        })
        break

      case SSEEventType.TOOL_RESULT:
      case SSEEventType.AGENT_TOOL_RESULT:
        addLog({
          type: event.data.success !== false ? 'result' : 'error',
          nodeId: event.data.node_id || activeNodeId.value || '0',
          content: event.data.success !== false
            ? JSON.stringify(event.data.result)
            : event.data.error || 'Unknown error',
        })
        break
      
      // Content streaming (from backend)
      case SSEEventType.CONTENT:
        // 累积报告内容
        reportContent.value += event.data.content || ''
        addLog({
          type: 'result',
          nodeId: activeNodeId.value || '0',
          content: event.data.content,
        })
        break

      // Research report ready (with citations)
      case SSEEventType.RESEARCH_REPORT_READY:
        if (event.data.citations && Array.isArray(event.data.citations)) {
          citations.value = event.data.citations
          console.log('[ExecutionStore] Citations received:', citations.value.length)
        }
        break
      
      // Agent done
      case SSEEventType.DONE:
        if (session.value) {
          session.value.status = SessionStatus.COMPLETED
        }
        break

      // Task planning events (dynamic workflow construction)
      case SSEEventType.PLAN_CREATED:
        // 清空旧节点，准备接收新规划
        nodes.value = []
        edges.value = []
        break
      
      // ========== Plan events (与后端 PlanningLayer 对齐) ==========
      // 这些事件由 workflowStore 处理，更新 WorkflowGraph
      case SSEEventType.PLAN_DAG_CREATED: {
        // Plan 创建，推送整个 Task DAG
        const workflowStore = useWorkflowStore()
        workflowStore.handlePlanCreated(event.data)
        console.log('[ExecutionStore] Plan DAG created:', event.data.planId)
        addLog({
          type: 'thinking',
          nodeId: '0',
          content: `📝 任务规划完成，共 ${event.data.tasks?.length || 0} 个步骤`,
        })
        break
      }
      
      case SSEEventType.PLAN_DAG_REVISED: {
        // Plan 重规划
        const workflowStore = useWorkflowStore()
        workflowStore.handlePlanRevised(event.data)
        console.log('[ExecutionStore] Plan DAG revised:', event.data.planId, 'reason:', event.data.reason)
        addLog({
          type: 'thinking',
          nodeId: '0',
          content: `🔄 任务重新规划：${event.data.reason || '调整执行策略'}`,
        })
        break
      }
      
      case SSEEventType.TASK_START: {
        // Task 开始执行
        const workflowStore = useWorkflowStore()
        workflowStore.handleTaskStart(event.data)
        console.log('[ExecutionStore] Task started:', event.data.taskId)
        addLog({
          type: 'thinking',
          nodeId: event.data.taskId || '0',
          content: `▶️ 开始执行任务: ${event.data.taskId}`,
        })
        break
      }
      
      case SSEEventType.TASK_COMPLETE: {
        // Task 执行完成
        const workflowStore = useWorkflowStore()
        workflowStore.handleTaskComplete(event.data)
        console.log('[ExecutionStore] Task completed:', event.data.taskId)
        addLog({
          type: 'result',
          nodeId: event.data.taskId || '0',
          content: `✅ 任务完成: ${event.data.taskId}`,
        })
        break
      }
      
      case SSEEventType.TASK_FAILED: {
        // Task 执行失败
        const workflowStore = useWorkflowStore()
        workflowStore.handleTaskFailed(event.data)
        console.log('[ExecutionStore] Task failed:', event.data.taskId, event.data.errorMessage)
        addLog({
          type: 'error',
          nodeId: event.data.taskId || '0',
          content: `❌ 任务失败: ${event.data.taskId} - ${event.data.errorMessage || 'Unknown error'}`,
        })
        break
      }
      
      case SSEEventType.TASK_UPDATE: {
        // Task 通用更新
        const workflowStore = useWorkflowStore()
        workflowStore.handleTaskUpdate(event.data)
        console.log('[ExecutionStore] Task updated:', event.data.id, event.data.status)
        break
      }

      case SSEEventType.NODE_CREATED: {
        // 动态添加节点
        const pos = calculateNodePosition(nodes.value.length)
        const newNode: WorkflowNode = {
          id: event.data.node_id,
          type: event.data.type as 'web' | 'local',
          status: 'pending',
          label: event.data.label,
          x: pos.x,
          y: pos.y,
          dependsOn: event.data.depends_on || [],
        }
        nodes.value.push(newNode)
        break
      }

      case SSEEventType.EDGE_CREATED:
        // 动态添加边
        edges.value.push({
          id: `e-${event.data.from}-${event.data.to}`,
          from: event.data.from,
          to: event.data.to,
          type: event.data.type === 'data' ? 'result' : 'context',
          active: false,
        })
        break

      case SSEEventType.PLAN_FINALIZED:
        // 规划完成，D3 会通过 watch 自动重新布局
        console.log('[ExecutionStore] Plan finalized:', event.data.node_count, 'nodes,', event.data.edge_count, 'edges')
        break

      // Workflow node execution events
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
          session.value.status = SessionStatus.COMPLETED
        }
        // Close SSE connection - session is done, no need to reconnect
        sseConnection?.close()
        sseConnectionState.value = 'disconnected'
        break

      case SSEEventType.SESSION_FAILED:
        if (session.value) {
          session.value.status = SessionStatus.FAILED
        }
        // Close SSE connection - session failed, no need to reconnect
        sseConnection?.close()
        sseConnectionState.value = 'disconnected'
        break

      // Error event (non-fatal errors during execution)
      case SSEEventType.ERROR:
        addLog({
          type: 'error',
          nodeId: activeNodeId.value || '0',
          content: event.data.message || 'Unknown error',
        })
        // If fatal error, update session status
        if (event.data.fatal) {
          if (session.value) {
            session.value.status = SessionStatus.FAILED
          }
          error.value = event.data.message || 'Fatal error occurred'
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

      // Timeline events (时光长廊)
      case SSEEventType.TIMELINE_SEARCH:
        addLog({
          type: 'timeline-search',
          nodeId: activeNodeId.value || '0',
          content: event.data.title || `搜索: ${event.data.query}`,
          timelineData: {
            title: event.data.title,
            description: event.data.description,
            query: event.data.query,
            resultsCount: event.data.results_count,
          }
        })
        break

      case SSEEventType.TIMELINE_READ:
        addLog({
          type: 'timeline-read',
          nodeId: activeNodeId.value || '0',
          content: event.data.title || `阅读: ${event.data.url}`,
          timelineData: {
            title: event.data.title,
            description: event.data.description,
            url: event.data.url,
          }
        })
        break

      case SSEEventType.TIMELINE_SCREENSHOT:
        addLog({
          type: 'timeline-screenshot',
          nodeId: activeNodeId.value || '0',
          content: event.data.title || '截图',
          timelineData: {
            title: event.data.title,
            description: event.data.description,
            url: event.data.url,
            screenshotPath: event.data.path,
          }
        })
        break

      case SSEEventType.TIMELINE_FINDING:
        addLog({
          type: 'timeline-finding',
          nodeId: activeNodeId.value || '0',
          content: event.data.title || `发现: ${event.data.content?.slice(0, 50)}`,
          timelineData: {
            title: event.data.title,
            description: event.data.description || event.data.content,
            sourceUrl: event.data.source_url,
          }
        })
        break

      case SSEEventType.TIMELINE_MILESTONE:
        addLog({
          type: 'timeline-milestone',
          nodeId: activeNodeId.value || '0',
          content: event.data.title,
          timelineData: {
            title: event.data.title,
            description: event.data.description,
          }
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
      type: entry.type,
      nodeId: entry.nodeId,
      content: entry.content,
      timelineData: entry.timelineData,
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
    sseConnectionState.value = 'disconnected'
    sseError.value = null
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
    // Reset research report state
    reportContent.value = ''
    citations.value = []
  }

  return {
    // State
    sessionId,
    session,
    currentTask,
    isLoading,
    error,
    sseConnectionState,
    sseError,
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
    reportContent,
    citations,

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
    stopExecution,  // P1-2
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
