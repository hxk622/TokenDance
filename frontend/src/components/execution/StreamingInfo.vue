<template>
  <div class="streaming-info">
    <div class="toolbar">
      <div class="mode-tabs">
        <button :class="{ active: mode === 'all' }" @click="mode = 'all'">全部</button>
        <button :class="{ active: mode === 'coworker' }" @click="mode = 'coworker'">Coworker</button>
        <button :class="{ active: mode === 'browser' }" @click="mode = 'browser'">
          <svg class="w-3.5 h-3.5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          浏览器
        </button>
      </div>
      <button v-if="isFocusMode" class="btn-exit-focus" @click="exitFocusMode">
        退出聚焦模式
      </button>
    </div>

    <!-- Browser Operation Log -->
    <div v-if="mode === 'browser'" class="browser-log-container">
      <BrowserOperationLog 
        :operations="browserOperations"
        :status="browserStatus"
        @show-time-lapse="showTimeLapse"
        @show-screenshot="showScreenshot"
      />
    </div>

    <!-- Regular Logs -->
    <div v-else class="logs-container" ref="logsContainerRef" @scroll="handleScroll">
      <div 
        v-for="log in displayLogs" 
        :key="log.id"
        :class="['log-entry', `type-${log.type}`]"
        :data-node-id="log.nodeId"
      >
        <div class="log-header">
          <span class="log-type">{{ log.type }}</span>
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
        </div>
        <div class="log-content">{{ log.content }}</div>
      </div>
    </div>

    <!-- TimeLapse Gallery Modal -->
    <TimeLapseGallery 
      v-if="showTimeLapseModal"
      :playback="timeLapsePlayback"
      :loading="timeLapseLoading"
      @close="showTimeLapseModal = false"
    />

    <!-- Screenshot Modal -->
    <div 
      v-if="showScreenshotModal"
      class="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8"
      @click.self="showScreenshotModal = false"
    >
      <div class="relative max-w-4xl max-h-[90vh]">
        <img :src="screenshotPath" class="max-w-full max-h-full rounded-lg" />
        <button 
          @click="showScreenshotModal = false"
          class="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 text-white"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { BrowserOperationLog, TimeLapseGallery } from './browser'
import type { BrowserOperation, TimeLapsePlayback } from './browser/types'

interface Props {
  sessionId: string
}

const props = defineProps<Props>()

// Use Pinia store
const executionStore = useExecutionStore()

const mode = ref<'all' | 'coworker' | 'browser'>('all')
const isFocusMode = ref(false)
const focusedNodeId = ref<string | null>(null)
const logsContainerRef = ref<HTMLElement | null>(null)
const autoScroll = ref(true)

// Use logs from store
const displayLogs = computed(() => {
  let logs = executionStore.logs
  
  // Filter by focus mode
  if (isFocusMode.value && focusedNodeId.value) {
    logs = logs.filter(log => log.nodeId === focusedNodeId.value)
  }
  
  return logs
})

// Auto-scroll to bottom when new logs arrive
watch(
  () => executionStore.logs.length,
  () => {
    if (autoScroll.value) {
      nextTick(() => {
        if (logsContainerRef.value) {
          logsContainerRef.value.scrollTop = logsContainerRef.value.scrollHeight
        }
      })
    }
  }
)

// Detect user scroll to pause auto-scroll
function handleScroll(event: Event) {
  const el = event.target as HTMLElement
  const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
  autoScroll.value = isAtBottom
}

function formatTime(timestamp: number) {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function scrollToNode(nodeId: string) {
  const element = logsContainerRef.value?.querySelector(`[data-node-id="${nodeId}"]`)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function enterFocusMode(nodeId: string) {
  isFocusMode.value = true
  focusedNodeId.value = nodeId
}

function exitFocusMode() {
  isFocusMode.value = false
  focusedNodeId.value = null
}

// Browser Operations
const browserOperations = computed<BrowserOperation[]>(() => {
  // Get browser operations from store or filter from logs
  // For now, return mock data if not available
  return executionStore.browserOperations || []
})

const browserStatus = computed(() => {
  const ops = browserOperations.value
  if (ops.length === 0) return 'idle'
  if (ops.some(o => o.status === 'running')) return 'running'
  if (ops.some(o => o.status === 'error')) return 'error'
  return 'completed'
})

// TimeLapse
const showTimeLapseModal = ref(false)
const timeLapsePlayback = ref<TimeLapsePlayback | null>(null)
const timeLapseLoading = ref(false)

async function showTimeLapse() {
  showTimeLapseModal.value = true
  timeLapseLoading.value = true
  
  try {
    // TODO: Fetch from API
    // const playback = await getTimeLapsePlayback(props.sessionId)
    // timeLapsePlayback.value = playback
    
    // Mock data for now
    timeLapsePlayback.value = {
      sessionId: props.sessionId,
      title: '研究过程',
      totalDurationMs: 60000,
      frames: []
    }
  } finally {
    timeLapseLoading.value = false
  }
}

// Screenshot Modal
const showScreenshotModal = ref(false)
const screenshotPath = ref('')

function showScreenshot(path: string) {
  screenshotPath.value = path
  showScreenshotModal.value = true
}

defineExpose({
  scrollToNode,
  enterFocusMode,
  exitFocusMode
})
</script>

<style scoped>
.streaming-info {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgba(18, 18, 18, 0.8);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
}

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tabs button {
  padding: 6px 12px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.mode-tabs button.active {
  background: rgba(0, 217, 255, 0.2);
  border-color: #00D9FF;
  color: #00D9FF;
}

.mode-tabs button svg {
  display: inline-block;
  width: 14px;
  height: 14px;
  margin-right: 4px;
  vertical-align: middle;
}

.browser-log-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.btn-exit-focus {
  padding: 6px 12px;
  border: 1px solid #FFB800;
  border-radius: 6px;
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-exit-focus:hover {
  background: rgba(255, 184, 0, 0.3);
}

.logs-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.log-entry {
  margin-bottom: 16px;
  padding: 12px;
  border-left: 3px solid;
  background: rgba(28, 28, 30, 0.6);
  border-radius: 4px;
}

.log-entry.type-thinking {
  border-color: #00D9FF;
}

.log-entry.type-tool-call {
  border-color: #FFB800;
}

.log-entry.type-result {
  border-color: #00FF88;
}

.log-entry.type-error {
  border-color: #FF3B30;
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.log-type {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-primary, #ffffff);
}

.log-time {
  font-size: 11px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.4));
}

.log-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary, rgba(255, 255, 255, 0.9));
  font-family: 'Monaco', 'Menlo', monospace;
}

/* 滚动条样式 */
.logs-container::-webkit-scrollbar {
  width: 8px;
}

.logs-container::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.logs-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.logs-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
