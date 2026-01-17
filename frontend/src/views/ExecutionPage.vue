<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import ResizableDivider from '@/components/execution/ResizableDivider.vue'
import WorkflowGraph from '@/components/execution/WorkflowGraph.vue'
import StreamingInfo from '@/components/execution/StreamingInfo.vue'
import ArtifactTabs, { type TabType } from '@/components/execution/ArtifactTabs.vue'
import PreviewArea from '@/components/execution/PreviewArea.vue'
import HITLConfirmDialog from '@/components/execution/HITLConfirmDialog.vue'
import BrowserPip from '@/components/execution/BrowserPip.vue'
import { useExecutionStore } from '@/stores/execution'
import { hitlApi, type HITLRequest } from '@/api/hitl'
import { ViewfinderCircleIcon, CheckCircleIcon } from '@heroicons/vue/24/outline'

const route = useRoute()
const sessionId = ref(route.params.id as string)

// Pinia Store
const executionStore = useExecutionStore()

// Computed from store
const isRunning = computed(() => executionStore.isRunning)
const sessionStatus = computed(() => {
  if (executionStore.isLoading) return 'loading'
  if (executionStore.error) return 'error'
  return executionStore.session?.status || 'idle'
})
const elapsedTime = ref('0分0秒')
let elapsedTimer: ReturnType<typeof setInterval> | null = null

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

// Check viewport width
function checkResponsiveMode() {
  isCompactMode.value = window.innerWidth < 1280
}

// Load saved ratios
onMounted(async () => {
  const savedHorizontal = localStorage.getItem('execution-horizontal-ratio')
  const savedVertical = localStorage.getItem('execution-vertical-ratio')
  
  if (savedHorizontal) {
    const [left, right] = savedHorizontal.split(':').map(Number)
    leftWidth.value = left
    rightWidth.value = right
  }
  
  if (savedVertical) {
    const [top, bottom] = savedVertical.split(':').map(Number)
    topHeight.value = top
    bottomHeight.value = bottom
  }
  
  // Initialize responsive check
  checkResponsiveMode()
  window.addEventListener('resize', checkResponsiveMode)
  
  // Initialize store and connect SSE
  await initializeExecution()
})

onUnmounted(() => {
  // Cleanup
  executionStore.disconnect()
  window.removeEventListener('resize', checkResponsiveMode)
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
  }
})

// Initialize execution
async function initializeExecution() {
  // For demo session, skip loading and just connect SSE
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
  } else {
    // Load real session
    await executionStore.loadSession(sessionId.value)
  }
  
  // Connect SSE stream
  executionStore.sessionId = sessionId.value
  executionStore.connectSSE()
  
  // Start elapsed timer
  startElapsedTimer()
}

// Elapsed time tracking
function startElapsedTimer() {
  const startTime = Date.now()
  elapsedTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000)
    const minutes = Math.floor(elapsed / 60)
    const seconds = elapsed % 60
    elapsedTime.value = `${minutes}分${seconds}秒`
  }, 1000)
}

// Handle stop action
// Note: handlePause removed as pause is not yet implemented

function handleStop() {
  executionStore.disconnect()
  if (elapsedTimer) {
    clearInterval(elapsedTimer)
  }
  console.log('Stop execution')
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
    <!-- Header with Plan Recitation -->
    <header class="execution-header">
      <div class="task-info">
        <h1 class="task-title">Deep Research: AI Agent 市场分析</h1>
        <div class="status-indicator">
          <span :class="['status-badge', sessionStatus]">
            {{ sessionStatus === 'running' ? '执行中' : 
               sessionStatus === 'completed' ? '已完成' : 
               sessionStatus === 'error' ? '错误' : '准备中' }}
          </span>
          <span class="time">已执行 {{ elapsedTime }}</span>
        </div>
      </div>
      
      <!-- Plan Recitation: 当前步骤指示器 -->
      <div class="plan-progress">
        <div class="progress-step">
          <span class="step-label">Step {{ currentStepIndex + 1 }}/{{ totalSteps }}</span>
          <span class="step-name">{{ currentStepLabel }}</span>
        </div>
        <div class="progress-bar-wrapper">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: `${progressPercent}%` }" />
          </div>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
      </div>
      
      <div class="header-actions">
        <button 
          class="btn-intervention" 
          @click="requestIntervention" 
          :disabled="!isRunning || isRequestingIntervention"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          暂停并介入
        </button>
        <button class="btn-secondary" @click="handleStop">停止</button>
      </div>
    </header>

    <!-- Focus Mode Banner with Breadcrumb -->
    <Transition name="slide-down">
      <div v-if="isFocusMode" class="focus-mode-banner glass-panel-medium">
        <div class="focus-left">
          <ViewfinderCircleIcon class="focus-icon vibe-breathing-active" />
          <div class="focus-breadcrumb">
            <button class="breadcrumb-item" @click="exitFocusMode">
              执行流程
            </button>
            <span class="breadcrumb-separator">/</span>
            <span class="breadcrumb-current">
              节点 {{ focusedNodeId }}
            </span>
          </div>
        </div>
        <div class="focus-right">
          <span class="focus-hint">按 ESC 退出</span>
          <button class="focus-exit-btn glass-button" @click="exitFocusMode">
            <svg class="exit-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>退出聚焦</span>
          </button>
        </div>
      </div>
    </Transition>
    
    <!-- 任务完成庆祝 -->
    <Transition name="celebration-fade">
      <div v-if="showCompletionCelebration" class="completion-celebration">
        <div class="celebration-content">
          <CheckCircleIcon class="w-16 h-16 text-green-400" />
          <h2 class="celebration-title">任务完成！</h2>
          <p class="celebration-desc">报告已生成，可在右侧查看</p>
        </div>
      </div>
    </Transition>

    <!-- Panel Toggle (Compact Mode) -->
    <div v-if="isCompactMode" class="panel-toggle">
      <button 
        :class="['toggle-btn', { active: activePanel === 'left' }]" 
        @click="activePanel = 'left'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
        </svg>
        <span>执行跟踪</span>
      </button>
      <button 
        :class="['toggle-btn', { active: activePanel === 'right' }]" 
        @click="activePanel = 'right'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span>成果预览</span>
      </button>
    </div>

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
          @click="toggleCollapse"
          :title="isCollapsed ? '展开工作流' : '折叠工作流'"
        >
          <span class="collapse-icon">{{ isCollapsed ? '▼' : '▲' }}</span>
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
          :session-id="sessionId" 
          :task-type="taskType"
          v-model:current-tab="currentTab"
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

<style scoped>
.execution-page {
  width: 100vw;
  min-height: 100vh;
  min-height: 100dvh; /* Dynamic viewport height for mobile */
  display: flex;
  flex-direction: column;
  background: rgba(18, 18, 18, 0.95);
  color: #ffffff;
}

/* Global cursor-pointer for interactive elements */
.execution-page button,
.execution-page [role="button"],
.execution-page .clickable {
  cursor: pointer;
}

/* Global hover scale for buttons */
.execution-page button:not(:disabled):active {
  transform: scale(0.98);
}

/* Header - Glass morphism */
.execution-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(28, 28, 30, 0.75);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

.task-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.task-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: rgba(0, 217, 255, 0.2);
  color: var(--vibe-color-active);
  animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.status-badge.completed {
  background: rgba(0, 255, 136, 0.2);
  color: var(--vibe-color-success);
}

.status-badge.error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--vibe-color-error);
}

.time {
  font-size: 14px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
}

/* Plan Recitation 进度指示器 */
.plan-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 200px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-node-active, #00D9FF);
  padding: 2px 8px;
  background: rgba(0, 217, 255, 0.15);
  border-radius: 4px;
}

.step-name {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

.progress-bar-wrapper {
  display: flex;
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
  background: linear-gradient(90deg, var(--vibe-color-active), var(--vibe-color-success));
  border-radius: 2px;
  transition: width 300ms ease-out;
  position: relative;
  overflow: hidden;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
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
  gap: 12px;
}

.btn-intervention {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1px solid rgba(255, 184, 0, 0.5);
  border-radius: 8px;
  background: rgba(255, 184, 0, 0.15);
  color: #FFB800;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-intervention:hover:not(:disabled) {
  background: rgba(255, 184, 0, 0.25);
  border-color: #FFB800;
}

.btn-intervention:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-intervention svg {
  width: 16px;
  height: 16px;
}

.btn-secondary {
  padding: 8px 16px;
  border: 1px solid var(--divider-color);
  border-radius: 8px;
  background: transparent;
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--divider-hover, rgba(0, 217, 255, 0.5));
}

/* Main Content */
.execution-content {
  flex: 1;
  display: flex;
  overflow: hidden;
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
  border-bottom: 1px solid var(--divider-color);
  transition: height 200ms ease-out;
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
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(28, 28, 30, 0.9);
  border: 1px solid var(--divider-color);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease-out;
}

.collapse-toggle:hover {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--color-node-active, #00D9FF);
  color: var(--color-node-active, #00D9FF);
}

.collapse-toggle:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(18, 18, 18, 0.95), 0 0 0 4px #00D9FF;
}

.collapse-toggle:focus:not(:focus-visible) {
  box-shadow: none;
}

.collapse-toggle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px rgba(18, 18, 18, 0.95), 0 0 0 4px #00D9FF;
}

.collapse-toggle.collapsed {
  background: rgba(0, 217, 255, 0.15);
}

.collapse-icon {
  font-size: 10px;
}

/* Focus Mode Banner - Enhanced */
.focus-mode-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: rgba(0, 217, 255, 0.1);
  border-bottom: 1px solid rgba(0, 217, 255, 0.2);
}

.focus-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.focus-icon {
  width: 20px;
  height: 20px;
  color: var(--vibe-color-active);
}

.focus-breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
}

.breadcrumb-item {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.breadcrumb-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}

.breadcrumb-separator {
  color: rgba(255, 255, 255, 0.3);
}

.breadcrumb-current {
  font-size: 13px;
  font-weight: 600;
  color: var(--vibe-color-active);
}

.focus-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.focus-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.focus-exit-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  font-size: 13px;
}

.exit-icon {
  width: 14px;
  height: 14px;
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

/* 完成庆祝动画 - Enhanced with Confetti */
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

/* Confetti particles */
.completion-celebration::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 30%, var(--vibe-color-success) 2px, transparent 2px),
    radial-gradient(circle at 80% 20%, var(--vibe-color-active) 2px, transparent 2px),
    radial-gradient(circle at 40% 70%, #FFB800 2px, transparent 2px),
    radial-gradient(circle at 70% 60%, #FF6B6B 2px, transparent 2px),
    radial-gradient(circle at 10% 80%, var(--vibe-color-success) 2px, transparent 2px),
    radial-gradient(circle at 90% 90%, var(--vibe-color-active) 2px, transparent 2px);
  background-size: 100px 100px;
  animation: confetti-fall 3s linear infinite;
  pointer-events: none;
}

@keyframes confetti-fall {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}

.celebration-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 56px 72px;
  background: rgba(28, 28, 30, 0.95);
  border: 1px solid rgba(0, 255, 136, 0.4);
  border-radius: 24px;
  box-shadow: 
    0 0 80px rgba(0, 255, 136, 0.25),
    0 0 120px rgba(0, 217, 255, 0.15);
  animation: celebration-pop 0.5s var(--vibe-ease-bounce);
}

@keyframes celebration-pop {
  0% {
    opacity: 0;
    transform: scale(0.6) rotate(-2deg);
  }
  50% {
    transform: scale(1.05) rotate(1deg);
  }
  100% {
    opacity: 1;
    transform: scale(1) rotate(0);
  }
}

.celebration-icon {
  width: 64px;
  height: 64px;
  color: var(--vibe-color-success);
  animation: success-bounce 0.6s var(--vibe-ease-bounce) 0.3s both;
}

@keyframes success-bounce {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); opacity: 1; }
}

.celebration-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--vibe-color-success);
  margin: 0;
  text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
}

.celebration-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
}

.celebration-dismiss {
  margin-top: 8px;
  padding: 10px 28px;
  background: var(--vibe-color-success);
  border: none;
  border-radius: 10px;
  color: #000;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 150ms ease-out;
}

.celebration-dismiss:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
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
  background: var(--bg-secondary, rgba(28, 28, 30, 0.9));
}

/* Panel Toggle (Compact Mode) */
.panel-toggle {
  display: flex;
  padding: 8px 16px;
  gap: 8px;
  background: rgba(28, 28, 30, 0.9);
  border-bottom: 1px solid var(--divider-color);
}

.toggle-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--divider-color);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 150ms ease-out;
}

.toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.toggle-btn.active {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
  color: var(--color-node-active, #00D9FF);
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

/* Responsive adjustments */
@media (max-width: 1279px) {
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

/* CSS Variables */
:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --bg-secondary: rgba(28, 28, 30, 0.9);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
  --divider-hover: rgba(0, 217, 255, 0.5);
  --color-node-active: #00D9FF;
}
</style>
