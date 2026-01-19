<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ResizableDivider from '@/components/execution/ResizableDivider.vue'
import WorkflowGraph from '@/components/execution/WorkflowGraph.vue'
import StreamingInfo from '@/components/execution/StreamingInfo.vue'
import ArtifactTabs, { type TabType } from '@/components/execution/ArtifactTabs.vue'
import PreviewArea from '@/components/execution/PreviewArea.vue'
import HITLConfirmDialog from '@/components/execution/HITLConfirmDialog.vue'
import BrowserPip from '@/components/execution/BrowserPip.vue'
import InfoCollectionStage from '@/components/execution/InfoCollectionStage.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnyButton from '@/components/common/AnyButton.vue'
import { useExecutionStore } from '@/stores/execution'
import { useAuthStore } from '@/stores/auth'
import { sessionService } from '@/api/services/session'
import type { IntentValidationResponse } from '@/api/services/session'
import { hitlApi, type HITLRequest } from '@/api/hitl'
import {
  Home, History, FolderOpen, Settings, Search, LayoutGrid,
  PauseCircle, StopCircle, ChevronDown, ChevronUp, X, Check,
  AlertTriangle as ExclamationTriangleIcon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const sessionId = ref(route.params.id as string)
const initialTask = ref(route.query.task as string | null)

// Task title - AI summary or first 30 chars of query
const taskTitle = computed(() => {
  // Priority: session title from store > initial task truncated
  const sessionTitle = executionStore.session?.title
  if (sessionTitle) return sessionTitle
  
  if (initialTask.value) {
    return initialTask.value.length > 30 
      ? initialTask.value.slice(0, 30) + '...' 
      : initialTask.value
  }
  return '新任务'
})

// Execution stage management
type ExecutionStage = 'info-collection' | 'executing' | 'completed'
const executionStage = ref<ExecutionStage>('executing')
const preflightLoading = ref(false)
const preflightResult = ref<IntentValidationResponse | null>(null)
const finalTaskInput = ref('')

// Sidebar navigation
const sidebarSections = [
  {
    id: 'main',
    items: [
      { id: 'home', label: '首页', icon: Home },
      { id: 'history', label: '历史', icon: History },
      { id: 'files', label: '文件', icon: FolderOpen },
    ]
  }
]

const handleNavClick = (item: { id: string }) => {
  switch (item.id) {
    case 'home':
      router.push('/')
      break
    case 'history':
      router.push('/history')
      break
  }
}

const handleNewClick = () => {
  router.push('/')
}

// Pinia Store
const executionStore = useExecutionStore()
const authStore = useAuthStore()

// User initial for avatar
const userInitial = computed(() => {
  return authStore.user?.display_name?.charAt(0) || authStore.user?.username?.charAt(0) || 'U'
})

// Computed from store
const isRunning = computed(() => executionStore.isRunning)
const sessionStatus = computed(() => {
  if (executionStore.isLoading) return 'loading'
  if (executionStore.error) return 'error'
  return executionStore.session?.status || 'idle'
})
const elapsedTime = ref('0分0秒')
let elapsedTimer: ReturnType<typeof setInterval> | null = null

// SSE connection state
const sseConnectionState = computed(() => executionStore.sseConnectionState)
const sseError = computed(() => executionStore.sseError)

// Plan Recitation: 进度跟踪
const currentStepIndex = computed(() => {
  const nodes = executionStore.nodes
  const activeIndex = nodes.findIndex(n => n.status === 'active')
  if (activeIndex >= 0) return activeIndex
  const lastCompleted = nodes.map((n, i) => n.status === 'success' ? i : -1).filter(i => i >= 0)
  return lastCompleted.length > 0 ? Math.max(...lastCompleted) : 0
})
const totalSteps = computed(() => executionStore.nodes.length)
const currentStepLabel = computed(() => {
  const nodes = executionStore.nodes
  if (nodes.length === 0) return '准备中...'
  const idx = currentStepIndex.value
  return nodes[idx]?.label || '执行中'
})
const progressPercent = computed(() => {
  const completed = executionStore.nodes.filter(n => n.status === 'success').length
  const total = totalSteps.value
  return total > 0 ? Math.round((completed / total) * 100) : 0
})

// 是否处于准备阶段（没有工作流节点）
const isPreparing = computed(() => totalSteps.value === 0)

// 显示的步骤文本
const stepDisplayText = computed(() => {
  if (isPreparing.value) {
    return '初始化中'
  }
  return `Step ${currentStepIndex.value + 1}/${totalSteps.value}`
})

// HITL 干预状态
const showHITLDialog = ref(false)
const currentHITLRequest = ref<HITLRequest | null>(null)
const isRequestingIntervention = ref(false)

async function requestIntervention() {
  isRequestingIntervention.value = true
  try {
    // 创建一个人工干预请求
    const request = await hitlApi.create(sessionId.value, {
      type: 'user_intervention',
      title: '用户请求介入',
      description: `用户在步骤 ${currentStepIndex.value + 1}/${totalSteps.value} 请求暂停并介入`,
      context: { currentStep: currentStepLabel.value },
      riskLevel: 'medium'
    })
    currentHITLRequest.value = request
    showHITLDialog.value = true
  } catch (error) {
    console.error('Failed to create intervention request:', error)
    // Fallback: 直接显示弹窗
    currentHITLRequest.value = {
      id: 'manual-' + Date.now(),
      sessionId: sessionId.value,
      type: 'user_intervention',
      title: '用户请求介入',
      description: '您可以在此介入当前执行流程',
      context: {},
      status: 'pending',
      createdAt: new Date().toISOString()
    }
    showHITLDialog.value = true
  } finally {
    isRequestingIntervention.value = false
  }
}

function handleHITLClose() {
  showHITLDialog.value = false
  currentHITLRequest.value = null
}

function handleHITLConfirmed(approved: boolean) {
  showHITLDialog.value = false
  if (!approved) {
    // 用户取消执行
    handleStop()
  }
  currentHITLRequest.value = null
}

// Layout ratios - 根据任务类型动态调整
const taskType = ref<'deep-research' | 'ppt-generation' | 'code-refactor' | 'file-operations' | 'default'>('default')
const layoutRatios = {
  'deep-research': { left: 35, right: 65 },
  'ppt-generation': { left: 30, right: 70 },
  'code-refactor': { left: 60, right: 40 },
  'file-operations': { left: 65, right: 35 },
  'default': { left: 45, right: 55 },
}

// Horizontal ratio (left vs right)
const leftWidth = ref(layoutRatios[taskType.value].left)
const rightWidth = ref(layoutRatios[taskType.value].right)

// Vertical ratio (top vs bottom in left panel)
const topHeight = ref(40)
const bottomHeight = ref(60)

// Refs for child components
const streamingInfoRef = ref<InstanceType<typeof StreamingInfo> | null>(null)

// Artifact tab state - defaults based on task type
const currentTab = ref<TabType>('timeline')

// Focus Mode state
const isFocusMode = ref(false)
const focusedNodeId = ref<string | null>(null)

// Browser PiP state
const showBrowserPip = ref(true) // 默认显示
const browserPipUrl = ref('https://www.google.com/search?q=AI+Agent+market')
const browserPipScreenshot = ref('')

// 完成庆祝状态
const showCompletionCelebration = ref(false)

// 监听任务完成
watch(() => sessionStatus.value, (newStatus) => {
  if (newStatus === 'completed') {
    showCompletionCelebration.value = true
    // 3 秒后自动关闭
    setTimeout(() => {
      showCompletionCelebration.value = false
    }, 3000)
  }
})

// Collapse Mode state (mini-graph view)
const isCollapsed = ref(false)
const collapsedHeight = 80 // px for mini-graph

// Responsive layout state
const isCompactMode = ref(false)
const activePanel = ref<'left' | 'right'>('left') // Which panel is visible in compact mode

// Check viewport width - 使用 1024px 作为主要断点
function checkResponsiveMode() {
  const width = window.innerWidth
  isCompactMode.value = width < 1024
}

// Load saved ratios
onMounted(async () => {
  try {
    const savedHorizontal = localStorage.getItem('execution-horizontal-ratio')
    const savedVertical = localStorage.getItem('execution-vertical-ratio')

    if (savedHorizontal) {
      const [left, right] = savedHorizontal.split(':').map(Number)
      // Validate parsed values
      if (!isNaN(left) && !isNaN(right) && left > 0 && right > 0 && left + right === 100) {
        leftWidth.value = left
        rightWidth.value = right
      }
    }

    if (savedVertical) {
      const [top, bottom] = savedVertical.split(':').map(Number)
      // Validate parsed values
      if (!isNaN(top) && !isNaN(bottom) && top > 0 && bottom > 0 && top + bottom === 100) {
        topHeight.value = top
        bottomHeight.value = bottom
      }
    }
  } catch (error) {
    console.error('[ExecutionPage] Failed to load saved ratios:', error)
    // Usefault values on error
  }

  // Initialize responsive check
  checkResponsiveMode()
  window.addEventListener('resize', checkResponsiveMode)

  // Initialize store and connect SSE
  try {
    await initializeExecution()
  } catch (error) {
    console.error('[ExecutionPage] Failed to initialize execution:', error)
    executionStore.error = error instanceof Error ? error.message : '初始化失败'
  }
})

onUnmounted(() => {
  try {
    // Cleanup
    executionStore.disconnect()
    window.removeEventListener('resize', checkResponsiveMode)
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
  } catch (error) {
    console.error('[ExecutionPage] Error during cleanup:', error)
  }
})

// Run preflight check to validate task intent
async function runPreflightCheck(taskInput: string) {
  preflightLoading.value = true
  try {
    const result = await sessionService.validateIntent({
      user_input: taskInput,
      context: { session_id: sessionId.value }
    })
    preflightResult.value = result
    return result
  } catch (error) {
    console.error('[ExecutionPage] Preflight check failed:', error)
    // Fallback: allow execution if preflight fails
    const fallbackResult: IntentValidationResponse = {
      is_complete: true,
      confidence_score: 0.0,
      missing_info: [],
      suggested_questions: [],
      reasoning: '预检查失败，将继续执行'
    }
    preflightResult.value = fallbackResult
    return fallbackResult
  } finally {
    preflightLoading.value = false
  }
}

// Handle info collection stage completion
function handleInfoCollectionProceed(updatedInput?: string) {
  finalTaskInput.value = updatedInput || initialTask.value || ''
  executionStage.value = 'executing'
  
  // Now start the actual execution
  startActualExecution(finalTaskInput.value)
}

// Handle info collection cancellation - go back to home
function handleInfoCollectionCancel() {
  router.push('/')
}

// Start the actual agent execution
function startActualExecution(taskInput: string) {
  executionStore.sessionId = sessionId.value
  executionStore.connectSSE(taskInput)
  startElapsedTimer()
}

// Initialize execution
async function initializeExecution() {
  try {
    // Validate sessionId
    if (!sessionId.value) {
      throw new Error('Session ID is required')
    }

    // For demo session, skip preflight and loading
    if (sessionId.value.startsWith('demo')) {
      // Initialize demo workflow
      executionStore.nodes = [
        { id: '1', type: 'manus', status: 'pending', label: '收集市场数据', x: 100, y: 100 },
        { id: '2', type: 'manus', status: 'pending', label: '研究竞争对手', x: 300, y: 100 },
        { id: '3', type: 'coworker', status: 'pending', label: '整理关键发现', x: 500, y: 100 },
        { id: '4', type: 'coworker', status: 'pending', label: '撰写分析报告', x: 700, y: 100 },
      ]
      executionStore.edges = [
        { id: 'e1', from: '1', to: '2', type: 'context', active: false },
        { id: 'e2', from: '2', to: '3', type: 'context', active: false },
        { id: 'e3', from: '3', to: '4', type: 'result', active: false },
      ]
      executionStage.value = 'executing'
      startActualExecution(initialTask.value || '')
      return
    }

    // Load real session
    await executionStore.loadSession(sessionId.value)

    // Check for fatal errors (session not found)
    if (executionStore.sseConnectionState === 'fatal_error') {
      console.error('[ExecutionPage] Session not found, redirecting to home')
      setTimeout(() => {
        router.push('/')
      }, 2000)
      return
    }

    // If there's an initial task, run preflight check
    if (initialTask.value) {
      executionStage.value = 'info-collection'
      const result = await runPreflightCheck(initialTask.value)
      
      // If intent is complete with high confidence, skip info collection
      if (result.is_complete && result.confidence_score >= 0.8) {
        executionStage.value = 'executing'
        startActualExecution(initialTask.value)
      }
      // Otherwise stay in info-collection stage for user review
    } else {
      // No initial task, go directly to executing stage
      executionStage.value = 'executing'
      startActualExecution('')
    }
  } catch (error) {
    console.error('[ExecutionPage] Failed to initialize execution:', error)
    executionStore.error = error instanceof Error ? error.message : '初始化失败'
    throw error
  }
}

// Elapsed time tracking
function startElapsedTimer() {
  try {
    // Clear existing timer if any
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }

    const startTime = Date.now()
    elapsedTimer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000)
      const minutes = Math.floor(elapsed / 60)
      const seconds = elapsed % 60
      elapsedTime.value = `${minutes}分${seconds}秒`
    }, 1000)
  } catch (error) {
    console.error('[ExecutionPage] Failed to start elapsed timer:', error)
  }
}

// Handle stop action
// Note: handlePause removed as pause is not yet implemented

function handleStop() {
  try {
    executionStore.disconnect()
    if (elapsedTimer) {
      clearInterval(elapsedTimer)
      elapsedTimer = null
    }
    console.log('Stop execution')
  } catch (error) {
    console.error('[ExecutionPage] Error stopping execution:', error)
  }
}

// Handle error retry
function handleRetry() {
  try {
    // Clear error state
    executionStore.error = null
    executionStore.sseError = null

    // Reconnect SSE
    executionStore.connectSSE(initialTask.value)

    // Restart timer
    startElapsedTimer()
  } catch (error) {
    console.error('[ExecutionPage] Error retrying execution:', error)
    executionStore.error = error instanceof Error ? error.message : '重试失败'
  }
}

// Dismiss error banner
function dismissError() {
  executionStore.error = null
  executionStore.sseError = null
}

// Handle horizontal divider drag
function handleHorizontalDrag(delta: number) {
  const containerWidth = window.innerWidth
  const deltaPercent = (delta / containerWidth) * 100
  
  let newLeft = leftWidth.value + deltaPercent
  let newRight = rightWidth.value - deltaPercent
  
  // Enforce min/max constraints
  const MIN_LEFT = (300 / containerWidth) * 100  // 300px
  const MIN_RIGHT = (400 / containerWidth) * 100 // 400px
  
  if (newLeft < MIN_LEFT) {
    newLeft = MIN_LEFT
    newRight = 100 - MIN_LEFT
  } else if (newRight < MIN_RIGHT) {
    newRight = MIN_RIGHT
    newLeft = 100 - MIN_RIGHT
  }
  
  leftWidth.value = newLeft
  rightWidth.value = newRight
  
  // Save to localStorage
  localStorage.setItem('execution-horizontal-ratio', `${newLeft}:${newRight}`)
}

// Handle vertical divider drag
function handleVerticalDrag(delta: number) {
  const containerHeight = window.innerHeight - 64 // minus header
  const deltaPercent = (delta / containerHeight) * 100
  
  let newTop = topHeight.value + deltaPercent
  let newBottom = bottomHeight.value - deltaPercent
  
  // Enforce min/max constraints
  const MIN_TOP = (120 / containerHeight) * 100    // 120px
  const MIN_BOTTOM = (200 / containerHeight) * 100 // 200px
  
  if (newTop < MIN_TOP) {
    newTop = MIN_TOP
    newBottom = 100 - MIN_TOP
  } else if (newBottom < MIN_BOTTOM) {
    newBottom = MIN_BOTTOM
    newTop = 100 - MIN_BOTTOM
  }
  
  topHeight.value = newTop
  bottomHeight.value = newBottom
  
  // Save to localStorage
  localStorage.setItem('execution-vertical-ratio', `${newTop}:${newBottom}`)
}

// Reset to default ratio on double-click
function resetHorizontalRatio() {
  const ratio = layoutRatios[taskType.value]
  leftWidth.value = ratio.left
  rightWidth.value = ratio.right
  localStorage.removeItem('execution-horizontal-ratio')
}

function resetVerticalRatio() {
  topHeight.value = 40
  bottomHeight.value = 60
  localStorage.removeItem('execution-vertical-ratio')
}

// Scroll-Sync: When user clicks a node in WorkflowGraph, scroll to its logs
function handleNodeClick(nodeId: string) {
  streamingInfoRef.value?.scrollToNode(nodeId)
}

// Handle tab change
function handleTabChange(tab: TabType) {
  console.log('Tab changed to:', tab)
  // TODO: Update URL or trigger other side effects
}

// Set default tab based on task type
watch(taskType, (newType) => {
  const defaults: Record<string, TabType> = {
    'deep-research': 'timeline',
    'ppt-generation': 'ppt',
    'code-refactor': 'file-diff',
    'file-operations': 'file-diff',
    'default': 'report',
  }
  currentTab.value = defaults[newType] || 'report'
}, { immediate: true })

// Focus Mode: Enter when user double-clicks a node
function handleNodeDoubleClick(nodeId: string) {
  if (isFocusMode.value && focusedNodeId.value === nodeId) {
    // Exit focus mode if already focused on this node
    exitFocusMode()
  } else {
    // Enter focus mode
    enterFocusMode(nodeId)
  }
}

function enterFocusMode(nodeId: string) {
  isFocusMode.value = true
  focusedNodeId.value = nodeId
  
  // Adjust layout: 20% Graph, 80% Logs
  topHeight.value = 20
  bottomHeight.value = 80
  
  // Tell StreamingInfo to filter logs
  streamingInfoRef.value?.enterFocusMode(nodeId)
  
  console.log(`Focus Mode: Node ${nodeId}`)
}

function exitFocusMode() {
  isFocusMode.value = false
  focusedNodeId.value = null
  
  // Reset layout to default
  resetVerticalRatio()
  
  // Tell StreamingInfo to show all logs
  streamingInfoRef.value?.exitFocusMode()
  
  console.log('Exit Focus Mode')
}

// Collapse Mode: Toggle between full graph and mini-graph
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  
  if (isCollapsed.value) {
    // Exit focus mode if active
    if (isFocusMode.value) {
      exitFocusMode()
    }
  }
}

// Browser PiP handlers
function closeBrowserPip() {
  showBrowserPip.value = false
}

function openBrowserUrl(url: string) {
  window.open(url, '_blank')
}

// Handle chat message from StreamingInfo
function handleChatMessage(message: string) {
  console.log('Chat message received:', message)
  // TODO: Send message to backend to supplement task execution
  // executionStore.sendSupplementMessage(sessionId.value, message)
}

// ESC 键盘快捷键退出聚焦模式
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isFocusMode.value) {
    exitFocusMode()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="execution-page">
    <!-- Info Collection Stage (Phase 1) -->
    <Transition name="stage-fade">
      <InfoCollectionStage
        v-if="executionStage === 'info-collection'"
        :user-input="initialTask || ''"
        :is-complete="preflightResult?.is_complete ?? true"
        :confidence-score="preflightResult?.confidence_score ?? 0"
        :missing-info="preflightResult?.missing_info ?? []"
        :suggested-questions="preflightResult?.suggested_questions ?? []"
        :reasoning="preflightResult?.reasoning"
        :loading="preflightLoading"
        @proceed="handleInfoCollectionProceed"
        @cancel="handleInfoCollectionCancel"
      />
    </Transition>

    <!-- Fixed Header (always visible) -->
    <AnyHeader />
    
    <!-- Task Title (top-left, next to sidebar) -->
    <div class="task-title-bar">
      <h1 class="task-title-text">
        {{ taskTitle }}
      </h1>
    </div>

    <!-- Main Execution UI (Phase 2) -->
    <template v-if="executionStage === 'executing' || executionStage === 'completed'">
      <!-- Sidebar -->
      <AnySidebar
        :sections="sidebarSections"
        @nav-click="handleNavClick"
        @new-click="handleNewClick"
      >
        <template #footer>
          <button
            class="sidebar-footer-btn"
            data-tooltip="设置"
          >
            <Settings class="icon" />
          </button>
        </template>
      </AnySidebar>

      <!-- Main execution area -->
      <div class="execution-main">
        <!-- Header with status and progress -->
        <header class="execution-header">
          <!-- Status indicator -->
          <div class="status-indicator">
            <span :class="['status-badge', sessionStatus]">
              {{ sessionStatus === 'running' ? '执行中' : 
                sessionStatus === 'completed' ? '已完成' : 
                sessionStatus === 'error' ? '错误' : '准备中' }}
            </span>
            <span class="time">已执行 {{ elapsedTime }}</span>
          </div>
        
          <!-- Plan Recitation: 当前步骤指示器 - Enhanced Design -->
          <div class="plan-progress">
            <!-- Circular Progress Ring (or Spinner for preparing state) -->
            <div class="progress-ring">
              <!-- Preparing state: Indeterminate spinner -->
              <svg
                v-if="isPreparing"
                viewBox="0 0 36 36"
                class="preparing-spinner"
              >
                <circle
                  class="spinner-track"
                  cx="18"
                  cy="18"
                  r="16"
                />
                <circle
                  class="spinner-fill"
                  cx="18"
                  cy="18"
                  r="16"
                />
              </svg>
              <!-- Normal state: Progress ring -->
              <svg
                v-else
                viewBox="0 0 36 36"
              >
                <defs>
                  <linearGradient
                    id="progress-gradient"
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="0%"
                  >
                    <stop
                      offset="0%"
                      stop-color="#00D9FF"
                    />
                    <stop
                      offset="100%"
                      stop-color="#00FF88"
                    />
                  </linearGradient>
                </defs>
                <circle
                  class="bg"
                  cx="18"
                  cy="18"
                  r="16"
                />
                <circle
                  class="fill"
                  cx="18"
                  cy="18"
                  r="16"
                  :stroke-dasharray="`${progressPercent} 100`"
                />
              </svg>
              <span
                v-if="!isPreparing"
                class="percent"
              >{{ progressPercent }}%</span>
            </div>
            <!-- Step Info -->
            <div class="progress-step">
              <span class="step-label">{{ stepDisplayText }}</span>
              <span class="step-name">{{ currentStepLabel }}</span>
            </div>
          </div>
        
          <div class="header-actions">
            <AnyButton
              variant="secondary"
              :disabled="!isRunning || isRequestingIntervention"
              :title="isRunning ? '暂停任务并进行人工干预' : '任务未运行'"
              :aria-label="isRunning ? '暂停任务并进行人工干预' : '任务未运行'"
              @click="requestIntervention"
            >
              <PauseCircle
                class="w-4 h-4"
                aria-hidden="true"
              />
              <span>介入</span>
            </AnyButton>
            <AnyButton
              variant="ghost"
              class="btn-stop"
              :title="'终止任务执行'"
              :aria-label="'终止任务执行'"
              @click="handleStop"
            >
              <StopCircle
                class="w-4 h-4"
                aria-hidden="true"
              />
              <span>终止</span>
            </AnyButton>
          </div>
        </header>

        <!-- Error Banner -->
        <Transition name="slide-down">
          <div
            v-if="sessionStatus === 'error' || sseError"
            class="error-banner"
            role="alert"
            aria-live="assertive"
          >
            <div class="error-left">
              <ExclamationTriangleIcon
                class="error-icon"
                aria-hidden="true"
              />
              <div class="error-content">
                <span class="error-title">执行出错</span>
                <span class="error-message">{{ executionStore.error || sseError || '未知错误' }}</span>
              </div>
            </div>
            <div class="error-right">
              <AnyButton
                variant="ghost"
                size="sm"
                aria-label="重试任务执行"
                @click="handleRetry"
              >
                <span>重试</span>
              </AnyButton>
              <AnyButton
                variant="ghost"
                size="sm"
                aria-label="关闭错误提示"
                @click="dismissError"
              >
                <X
                  class="w-4 h-4"
                  aria-hidden="true"
                />
              </AnyButton>
            </div>
          </div>
        </Transition>

        <!-- Focus Mode Banner with Breadcrumb -->
        <Transition name="slide-down">
          <div
            v-if="isFocusMode"
            class="focus-mode-banner"
            role="status"
            aria-live="polite"
          >
            <div class="focus-left">
              <Search
                class="focus-icon"
                aria-hidden="true"
              />
              <div class="focus-breadcrumb">
                <button
                  class="breadcrumb-item"
                  aria-label="退出聚焦模式，返回执行流程"
                  @click="exitFocusMode"
                >
                  执行流程
                </button>
                <span
                  class="breadcrumb-separator"
                  aria-hidden="true"
                >/</span>
                <span class="breadcrumb-current">
                  节点 {{ focusedNodeId }}
                </span>
              </div>
            </div>
            <div class="focus-right">
              <span
                class="focus-hint"
                aria-hidden="true"
              >按 ESC 退出</span>
              <AnyButton
                variant="ghost"
                size="sm"
                aria-label="退出聚焦模式"
                @click="exitFocusMode"
              >
                <X
                  class="w-4 h-4"
                  aria-hidden="true"
                />
                <span>退出聚焦</span>
              </AnyButton>
            </div>
          </div>
        </Transition>
      
        <!-- 任务完成庆祝 -->
        <Transition name="celebration-fade">
          <div
            v-if="showCompletionCelebration"
            class="completion-celebration"
          >
            <div class="celebration-content">
              <Check class="celebration-icon" />
              <h2 class="celebration-title">
                任务完成！
              </h2>
              <p class="celebration-desc">
                报告已生成，可在右侧查看
              </p>
            </div>
          </div>
        </Transition>

        <!-- Panel Toggle (Compact Mode) -->
        <div
          v-if="isCompactMode"
          class="panel-toggle"
        >
          <button 
            :class="['toggle-btn', { active: activePanel === 'left' }]" 
            @click="activePanel = 'left'"
          >
            <LayoutGrid class="w-4 h-4" />
            <span>执行跟踪</span>
          </button>
          <button 
            :class="['toggle-btn', { active: activePanel === 'right' }]" 
            @click="activePanel = 'right'"
          >
            <FolderOpen class="w-4 h-4" />
            <span>成果预览</span>
          </button>
        </div>

        <!-- Loading Overlay -->
        <Transition name="fade">
          <div
            v-if="executionStore.isLoading"
            class="loading-overlay"
          >
            <div class="loading-content">
              <div class="loading-spinner" />
              <p class="loading-text">
                加载任务执行环境...
              </p>
            </div>
          </div>
        </Transition>

        <!-- Main Content -->
        <main :class="['execution-content', { 'compact-mode': isCompactMode }]">
          <!-- Left Panel: Execution Area -->
          <div
            class="left-panel"
            :class="{ hidden: isCompactMode && activePanel !== 'left' }"
            :style="isCompactMode ? {} : { width: `${leftWidth}%` }"
          >
            <!-- Collapse Toggle Button -->
            <button
              class="collapse-toggle"
              :class="{ collapsed: isCollapsed }"
              :title="isCollapsed ? '展开工作流' : '折叠工作流'"
              :aria-label="isCollapsed ? '展开工作流图' : '折叠工作流图'"
              :aria-expanded="!isCollapsed"
              @click="toggleCollapse"
            >
              <component
                :is="isCollapsed ? ChevronDown : ChevronUp"
                class="w-4 h-4"
                aria-hidden="true"
              />
            </button>

            <!-- Top: Workflow Graph -->
            <div 
              class="workflow-graph-container" 
              :class="{ collapsed: isCollapsed }"
              :style="{ height: isCollapsed ? `${collapsedHeight}px` : `${topHeight}%` }"
            >
              <WorkflowGraph 
                :session-id="sessionId" 
                :mini-mode="isCollapsed || isCompactMode"
                @node-click="handleNodeClick"
                @node-double-click="handleNodeDoubleClick"
              />
            </div>

            <!-- Vertical Divider (hidden when collapsed) -->
            <ResizableDivider
              v-if="!isCollapsed && !isCompactMode"
              direction="vertical"
              @resize="handleVerticalDrag"
              @reset="resetVerticalRatio"
            />

            <!-- Bottom: Streaming Info -->
            <div 
              class="streaming-info-container" 
              :style="{ height: isCollapsed ? 'calc(100% - 80px)' : (isCompactMode ? 'calc(100% - 100px)' : `${bottomHeight}%`) }"
            >
            <StreamingInfo 
                ref="streamingInfoRef"
                :session-id="sessionId"
                :user-query="initialTask || ''"
                :user-initial="userInitial"
                @send-message="handleChatMessage"
              />
            </div>
          </div>

          <!-- Horizontal Divider (hidden in compact mode) -->
          <ResizableDivider
            v-if="!isCompactMode"
            direction="horizontal"
            @resize="handleHorizontalDrag"
            @reset="resetHorizontalRatio"
          />

          <!-- Right Panel: Preview Area -->
          <div 
            class="right-panel" 
            :class="{ hidden: isCompactMode && activePanel !== 'right' }"
            :style="isCompactMode ? {} : { width: `${rightWidth}%` }"
          >
            <ArtifactTabs 
              v-model:current-tab="currentTab" 
              :session-id="sessionId"
              :task-type="taskType"
              @tab-change="handleTabChange"
            />
            <PreviewArea 
              :session-id="sessionId" 
              :current-tab="currentTab"
              :is-executing="isRunning"
            />
          </div>
        </main>
      
        <!-- HITL 干预弹窗 -->
        <HITLConfirmDialog
          :visible="showHITLDialog"
          :request="currentHITLRequest"
          @close="handleHITLClose"
          @confirmed="handleHITLConfirmed"
        />
      
        <!-- 浏览器画中画 -->
        <BrowserPip
          :visible="showBrowserPip && isRunning"
          :url="browserPipUrl"
          :screenshot="browserPipScreenshot"
          title="Manus 浏览器"
          @close="closeBrowserPip"
          @open-url="openBrowserUrl"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
.execution-page {
  width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  background: var(--exec-bg-primary);
  color: var(--exec-text-primary);
}

/* Execution-specific CSS Variables - 使用全局主题变量 */
.execution-page {
  --exec-bg-primary: var(--any-bg-primary);
  --exec-bg-secondary: var(--any-bg-secondary);
  --exec-bg-tertiary: var(--any-bg-tertiary);
  --exec-text-primary: var(--any-text-primary);
  --exec-text-secondary: var(--any-text-secondary);
  --exec-text-muted: var(--any-text-muted);
  --exec-border: var(--any-border);
  --exec-border-hover: var(--any-border-hover);
  /* 状态色保持品牌特色 */
  --exec-accent: #00D9FF;
  --exec-success: #00FF88;
  --exec-warning: #FFB800;
  --exec-error: #FF3B30;
}

/* Task title bar - fixed top-left */
.task-title-bar {
  position: fixed;
  top: 12px;
  left: 72px; /* sidebar width (56px) + gap (16px) */
  z-index: 100;
}

.task-title-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}

/* Main area with sidebar offset */
.execution-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 56px;
}

/* Sidebar footer button */
.sidebar-footer-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.sidebar-footer-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.sidebar-footer-btn .icon {
  width: 20px;
  height: 20px;
}

.sidebar-footer-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 8px;
  padding: 6px 10px;
  background: var(--any-text-primary);
  color: var(--any-bg-primary);
  font-size: 12px;
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  pointer-events: none;
  z-index: 1000;
}

.sidebar-footer-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

/* Header - Glass morphism */
.execution-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--exec-border);
  background: var(--exec-bg-secondary);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--any-radius-full);
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: rgba(0, 217, 255, 0.2);
  color: var(--exec-accent);
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.status-badge.completed {
  background: rgba(0, 255, 136, 0.2);
  color: var(--exec-success);
}

.status-badge.error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--exec-error);
}

.time {
  font-size: 14px;
  color: var(--exec-text-secondary);
}

/* Plan Recitation 进度指示器 - Enhanced Design */
.plan-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(0, 217, 255, 0.08);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: var(--any-radius-lg);
}

/* Circular Progress Ring */
.progress-ring {
  position: relative;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.progress-ring svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.progress-ring .bg {
  fill: none;
  stroke: var(--exec-border);
  stroke-width: 3;
}

.progress-ring .fill {
  fill: none;
  stroke: url(#progress-gradient);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 100;
  stroke-dashoffset: 0;
  transition: stroke-dasharray var(--any-duration-slow) var(--any-ease-default);
}

.progress-ring .percent {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--exec-accent);
  letter-spacing: -0.02em;
}

/* Preparing spinner */
.preparing-spinner {
  animation: spin 1.5s linear infinite;
}

.preparing-spinner .spinner-track {
  fill: none;
  stroke: var(--exec-border);
  stroke-width: 3;
}

.preparing-spinner .spinner-fill {
  fill: none;
  stroke: var(--exec-accent);
  stroke-width: 3;
  stroke-linecap: round;
  stroke-dasharray: 80;
  stroke-dashoffset: 60;
}

@keyframes spin {
  0% { transform: rotate(-90deg); }
  100% { transform: rotate(270deg); }
}

.progress-step {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--exec-accent);
  padding: 2px 10px;
  background: rgba(0, 217, 255, 0.2);
  border-radius: var(--any-radius-sm);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
}

.step-label::before {
  content: '';
  width: 6px;
  height: 6px;
  background: var(--exec-accent);
  border-radius: 50%;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.step-name {
  font-size: 13px;
  color: var(--exec-text-primary);
  font-weight: 500;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Responsive Header adjustments */
@media (max-width: 768px) {
  .execution-header {
    height: auto;
    min-height: 64px;
    flex-wrap: wrap;
    gap: 12px;
    padding: 12px 16px;
  }
  
  .task-info {
    width: 100%;
    order: 1;
  }
  
  .plan-progress {
    order: 3;
    width: 100%;
    justify-content: center;
  }
  
  .header-actions {
    order: 2;
    margin-left: auto;
  }
  
  .step-name {
    max-width: 200px;
  }
}

/* Legacy progress bar (fallback) */
.progress-bar-wrapper {
  display: none; /* Hidden in favor of ring */
  align-items: center;
  gap: 8px;
}

.progress-bar-bg {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #00D9FF, #00FF88);
  border-radius: 2px;
  transition: width 300ms ease-out;
  position: relative;
  overflow: hidden;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
  animation: progress-shimmer 1.5s ease-in-out infinite;
}

@keyframes progress-shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-percent {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 36px;
  text-align: right;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Stop button warning style */
.btn-stop:hover {
  color: var(--exec-error) !important;
  border-color: var(--exec-error) !important;
}

/* Loading Overlay */
.loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--exec-bg-primary);
  backdrop-filter: blur(8px);
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--exec-border);
  border-top-color: var(--exec-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: var(--exec-text-secondary);
  margin: 0;
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--any-duration-normal) var(--any-ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Main Content */
.execution-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* Left Panel */
.left-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  position: relative;
}

.workflow-graph-container {
  overflow: hidden;
  border-bottom: 1px solid var(--exec-border);
  transition: height var(--any-duration-normal) var(--any-ease-default);
}

.workflow-graph-container.collapsed {
  min-height: 80px;
}

/* Collapse Toggle */
.collapse-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--exec-bg-secondary);
  border: 1px solid var(--exec-border);
  border-radius: var(--any-radius-md);
  color: var(--exec-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.collapse-toggle:hover {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--exec-accent);
  color: var(--exec-accent);
}

/* Accessibility: Focus styles */
.collapse-toggle:focus-visible {
  outline: 2px solid var(--exec-accent);
  outline-offset: 2px;
}

.collapse-toggle.collapsed {
  background: rgba(0, 217, 255, 0.15);
}

/* Error Banner */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(255, 59, 48, 0.1);
  border-bottom: 1px solid rgba(255, 59, 48, 0.3);
  backdrop-filter: blur(8px);
}

.error-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.error-icon {
  width: 24px;
  height: 24px;
  color: var(--exec-error);
  flex-shrink: 0;
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.error-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--exec-error);
}

.error-message {
  font-size: 13px;
  color: var(--exec-text-secondary);
  max-width: 600px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.error-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Focus Mode Banner - Enhanced Prominence */
.focus-mode-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.15) 0%, rgba(0, 255, 136, 0.1) 100%);
  border-bottom: 2px solid rgba(0, 217, 255, 0.4);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.15);
  animation: banner-glow 3s ease-in-out infinite;
}

@keyframes banner-glow {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(0, 217, 255, 0.15);
  }
  50% {
    box-shadow: 0 4px 20px rgba(0, 217, 255, 0.25);
  }
}

.focus-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.focus-icon {
  width: 24px;
  height: 24px;
  color: var(--exec-accent);
  animation: icon-pulse 2s ease-in-out infinite;
}

@keyframes icon-pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.focus-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-item {
  padding: 4px 10px;
  background: var(--exec-bg-tertiary);
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--exec-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.breadcrumb-item:hover {
  background: var(--exec-border-hover);
  color: var(--exec-text-primary);
}

/* Accessibility: Focus styles for breadcrumb */
.breadcrumb-item:focus-visible {
  outline: 2px solid var(--exec-accent);
  outline-offset: 2px;
}

.breadcrumb-separator {
  color: var(--exec-text-muted);
}

.breadcrumb-current {
  font-size: 13px;
  font-weight: 600;
  color: var(--exec-accent);
}

.focus-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.focus-hint {
  font-size: 12px;
  color: var(--exec-text-muted);
}

/* Slide Down Transition */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 200ms ease-out;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-100%);
}

/* 完成庆祝动画 */
.completion-celebration {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(12px);
  overflow: hidden;
}

.celebration-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 56px 72px;
  background: var(--exec-bg-secondary);
  border: 1px solid rgba(0, 255, 136, 0.4);
  border-radius: var(--any-radius-xl);
  box-shadow: 
    0 0 80px rgba(0, 255, 136, 0.25),
    0 0 120px rgba(0, 217, 255, 0.15);
  animation: celebration-pop 0.5s var(--any-ease-bounce);
}

@keyframes celebration-pop {
  0% {
    opacity: 0;
    transform: scale(0.6);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.celebration-icon {
  width: 64px;
  height: 64px;
  color: var(--exec-success);
}

.celebration-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--exec-success);
  margin: 0;
}

.celebration-desc {
  font-size: 16px;
  color: var(--exec-text-secondary);
  margin: 0;
}

/* Celebration Fade Transition */
.celebration-fade-enter-active,
.celebration-fade-leave-active {
  transition: all 300ms ease-out;
}

.celebration-fade-enter-from,
.celebration-fade-leave-to {
  opacity: 0;
}

.celebration-fade-enter-from .celebration-content,
.celebration-fade-leave-to .celebration-content {
  transform: scale(0.9);
}

.streaming-info-container {
  overflow: hidden;
}

/* Skeleton loading styles */
.skeleton {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.04) 25%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.04) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s ease-in-out infinite;
  border-radius: 6px;
}

.skeleton-text {
  height: 16px;
  width: 100%;
}

.skeleton-text-short {
  height: 14px;
  width: 60%;
}

.skeleton-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.skeleton-rect {
  height: 80px;
  width: 100%;
}

@keyframes skeleton-shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Right Panel */
.right-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--exec-bg-secondary);
}

/* Panel Toggle (Compact Mode) */
.panel-toggle {
  display: flex;
  padding: 8px 16px;
  gap: 8px;
  background: var(--exec-bg-secondary);
  border-bottom: 1px solid var(--exec-border);
}

.toggle-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--exec-bg-tertiary);
  border: 1px solid var(--exec-border);
  border-radius: var(--any-radius-md);
  color: var(--exec-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.toggle-btn:hover {
  background: var(--exec-border-hover);
  border-color: var(--exec-border-hover);
}

.toggle-btn.active {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
  color: var(--exec-accent);
}

.toggle-btn svg {
  flex-shrink: 0;
}

/* Compact Mode Styles */
.execution-content.compact-mode {
  flex-direction: column;
}

.execution-content.compact-mode .left-panel,
.execution-content.compact-mode .right-panel {
  width: 100% !important;
  flex: 1;
}

.execution-content.compact-mode .left-panel.hidden,
.execution-content.compact-mode .right-panel.hidden {
  display: none;
}

.execution-content.compact-mode .workflow-graph-container {
  height: 100px !important;
  min-height: 100px;
}

/* Responsive adjustments - 多级断点优化 */

/* Tablet landscape (1024px - 1366px) */
@media (max-width: 1366px) and (min-width: 1024px) {
  .execution-header {
    padding: 0 20px;
  }

  .task-title {
    font-size: 17px;
  }

  .plan-progress {
    padding: 6px 12px;
  }

  .step-name {
    max-width: 150px;
  }
}

/* Tablet portrait and below (< 1024px) */
@media (max-width: 1023px) {
  .execution-header {
    padding: 0 16px;
  }

  .task-title {
    font-size: 16px;
  }

  .status-indicator {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .header-actions {
    gap: 8px;
  }

  .btn-secondary {
    padding: 6px 12px;
    font-size: 13px;
  }

  .plan-progress {
    padding: 6px 12px;
  }

  .step-name {
    max-width: 140px;
  }
}

@media (max-width: 768px) {
  .execution-header {
    height: auto;
    padding: 12px 16px;
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .task-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .plan-progress {
    display: none; /* 小屏幕隐藏进度条 */
  }
  
  .header-actions {
    justify-content: flex-end;
  }
  
  .btn-intervention span:not(.sr-only) {
    display: none; /* 小屏幕只显示图标 */
  }
  
  .focus-mode-banner {
    padding: 8px 16px;
    font-size: 12px;
  }
}

/* Stage Fade Transition - for switching between info-collection and executing */
.stage-fade-enter-active,
.stage-fade-leave-active {
  transition: opacity 400ms ease, transform 400ms ease;
}

.stage-fade-enter-from {
  opacity: 0;
  transform: scale(1.02);
}

.stage-fade-leave-to {
  opacity: 0;
  transform: scale(0.98);
}
</style>
