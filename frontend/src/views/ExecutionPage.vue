<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import ResizableDivider from '@/components/execution/ResizableDivider.vue'
import WorkflowGraph from '@/components/execution/WorkflowGraph.vue'
import StreamingInfo from '@/components/execution/StreamingInfo.vue'
import ArtifactTabs from '@/components/execution/ArtifactTabs.vue'
import PreviewArea from '@/components/execution/PreviewArea.vue'
import { useExecutionStore } from '@/stores/execution'

const route = useRoute()
const sessionId = ref(route.params.id as string)

// Pinia Store
const executionStore = useExecutionStore()

// Computed from store
const isRunning = computed(() => executionStore.isRunning)
// const isCompleted = computed(() => executionStore.isCompleted) // reserved for future use
const sessionStatus = computed(() => {
  if (executionStore.isLoading) return 'loading'
  if (executionStore.error) return 'error'
  return executionStore.session?.status || 'idle'
})
const elapsedTime = ref('0分0秒')
let elapsedTimer: ReturnType<typeof setInterval> | null = null

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

// Artifact tab state
const currentTab = ref<'report' | 'ppt' | 'file-diff'>('report')

// Focus Mode state
const isFocusMode = ref(false)
const focusedNodeId = ref<string | null>(null)

// Load saved ratios from localStorage
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
  
  // Initialize store and connect SSE
  await initializeExecution()
})

onUnmounted(() => {
  // Cleanup
  executionStore.disconnect()
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
      { id: '1', type: 'manus', status: 'pending', label: '搜索市场数据', x: 100, y: 100 },
      { id: '2', type: 'manus', status: 'pending', label: '分析竞品', x: 300, y: 100 },
      { id: '3', type: 'coworker', status: 'pending', label: '生成分析摘要', x: 500, y: 100 },
      { id: '4', type: 'coworker', status: 'pending', label: '生成最终报告', x: 700, y: 100 },
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

// Handle pause/stop actions
function handlePause() {
  console.log('Pause execution')
  // TODO: Call API to pause
}

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
function handleTabChange(tab: 'report' | 'ppt' | 'file-diff') {
  console.log('Tab changed to:', tab)
  // TODO: Update URL or trigger other side effects
}

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
</script>

<template>
  <div class="execution-page">
    <!-- Header -->
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
      <div class="header-actions">
        <button class="btn-secondary" @click="handlePause" :disabled="!isRunning">暂停</button>
        <button class="btn-secondary" @click="handleStop">停止</button>
      </div>
    </header>

    <!-- Main Content -->
    <main class="execution-content">
      <!-- Left Panel: Execution Area -->
      <div class="left-panel" :style="{ width: `${leftWidth}%` }">
        <!-- Top: Workflow Graph -->
        <div class="workflow-graph-container" :style="{ height: `${topHeight}%` }">
          <WorkflowGraph 
            :session-id="sessionId" 
            @node-click="handleNodeClick"
            @node-double-click="handleNodeDoubleClick"
          />
        </div>

        <!-- Vertical Divider -->
        <ResizableDivider
          direction="vertical"
          @resize="handleVerticalDrag"
          @reset="resetVerticalRatio"
        />

        <!-- Bottom: Streaming Info -->
        <div class="streaming-info-container" :style="{ height: `${bottomHeight}%` }">
          <StreamingInfo 
            ref="streamingInfoRef"
            :session-id="sessionId" 
          />
        </div>
      </div>

      <!-- Horizontal Divider -->
      <ResizableDivider
        direction="horizontal"
        @resize="handleHorizontalDrag"
        @reset="resetHorizontalRatio"
      />

      <!-- Right Panel: Preview Area -->
      <div class="right-panel" :style="{ width: `${rightWidth}%` }">
        <ArtifactTabs 
          :session-id="sessionId" 
          v-model:current-tab="currentTab"
          @tab-change="handleTabChange"
        />
        <PreviewArea 
          :session-id="sessionId" 
          :current-tab="currentTab"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.execution-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, rgba(18, 18, 18, 0.95));
  color: var(--text-primary, #ffffff);
}

/* Header */
.execution-header {
  height: 64px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
  background: rgba(28, 28, 30, 0.7);
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
  color: #00D9FF;
}

.time {
  font-size: 14px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
}

.header-actions {
  display: flex;
  gap: 12px;
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
}

.workflow-graph-container {
  overflow: hidden;
  border-bottom: 1px solid var(--divider-color);
}

.streaming-info-container {
  overflow: hidden;
}

/* Right Panel */
.right-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: var(--bg-secondary, rgba(28, 28, 30, 0.9));
}

/* CSS Variables */
:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --bg-secondary: rgba(28, 28, 30, 0.9);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
  --divider-hover: rgba(0, 217, 255, 0.5);
}
</style>
