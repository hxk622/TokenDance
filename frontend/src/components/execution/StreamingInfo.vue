<template>
  <div class="streaming-info">
    <!-- User Query Bubble -->
    <div
      v-if="userQuery"
      class="user-query-section"
    >
      <div class="user-query-bubble">
        <span class="user-avatar">{{ userInitial }}</span>
        <span class="user-query-text">{{ userQuery }}</span>
      </div>
    </div>

    <!-- Toolbar -->  
    <div class="toolbar">
      <div class="mode-tabs glass-tabs">
        <button
          :class="['glass-tab', { active: mode === 'all' }]"
          aria-label="显示全部日志"
          @click="mode = 'all'"
        >
          全部
        </button>
        <button
          :class="['glass-tab', { active: mode === 'coworker' }]"
          aria-label="显示 Coworker 模式"
          @click="mode = 'coworker'"
        >
          Coworker
        </button>
        <button
          :class="['glass-tab', { active: mode === 'browser' }]"
          aria-label="显示浏览器操作日志"
          @click="mode = 'browser'"
        >
          浏览器
        </button>
      </div>
      <div class="toolbar-actions">
        <button
          v-if="isFocusMode"
          class="btn-exit-focus glass-button"
          aria-label="退出聚焦模式"
          @click="exitFocusMode"
        >
          退出聚焦
        </button>
        <button
          :class="['btn-lock', { active: isUserReading }]"
          :title="isUserReading ? '解锁滚动' : '锁定滚动'"
          :aria-label="isUserReading ? '解锁自动滚动' : '锁定自动滚动'"
          @click="toggleScrollLock"
        >
          <svg
            v-if="isUserReading"
            class="lock-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <rect
              x="5"
              y="11"
              width="14"
              height="10"
              rx="2"
              stroke-width="2"
            />
            <path
              d="M8 11V7a4 4 0 118 0v4"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
          <svg
            v-else
            class="lock-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <rect
              x="5"
              y="11"
              width="14"
              height="10"
              rx="2"
              stroke-width="2"
            />
            <path
              d="M8 11V7a4 4 0 017.83-1"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <!-- Browser Operation Log -->
    <div
      v-if="mode === 'browser'"
      class="browser-log-container"
    >
      <BrowserOperationLog 
        :operations="browserOperations"
        :status="browserStatus"
        @show-time-lapse="showTimeLapse"
        @show-screenshot="showScreenshot"
      />
    </div>

    <!-- Coworker Mode: FileTree + LiveDiff -->
    <div
      v-else-if="mode === 'coworker'"
      class="coworker-container"
    >
      <div class="coworker-split">
        <div
          class="coworker-left"
          :style="{ flex: coworkerSplitRatio }"
        >
          <CoworkerFileTree 
            :operations="executionStore.fileOperations"
            @file-select="handleFileSelect"
          />
        </div>
        <div class="coworker-divider" />
        <div
          class="coworker-right"
          :style="{ flex: 100 - coworkerSplitRatio }"
        >
          <LiveDiff 
            v-if="selectedFileOperation"
            :file-path="selectedFileOperation.path"
          />
          <div
            v-else
            class="no-selection"
          >
            <p>选择文件查看变更</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Regular Logs -->
    <div
      v-else
      ref="logsContainerRef"
      class="logs-container"
    >
      <!-- Performance indicator when logs are trimmed -->
      <div
        v-if="executionStore.logs.length > MAX_RENDERED_LOGS"
        class="performance-indicator"
      >
        <span class="indicator-icon">⚡</span>
        <span class="indicator-text">
          显示最近 {{ MAX_RENDERED_LOGS }} 条日志（共 {{ executionStore.logs.length }} 条）
        </span>
      </div>

      <!-- Timeline track -->
      <div class="timeline-track" />
      
      <div
        v-for="log in displayLogs"
        :key="log.id"
        :class="[
          'log-entry',
          `type-${log.type}`,
          { expanded: isLogExpanded(log.id) },
          { 'timeline-entry': isTimelineType(log.type) }
        ]"
        :data-node-id="log.nodeId"
        tabindex="0"
        role="button"
        :aria-expanded="isLogExpanded(log.id)"
        :aria-label="`${log.type} 日志，${isLogExpanded(log.id) ? '已展开' : '已折叠'}，点击${isLogExpanded(log.id) ? '折叠' : '展开'}`"
        @click="toggleLogExpand(log.id)"
        @keydown.enter="toggleLogExpand(log.id)"
        @keydown.space.prevent="toggleLogExpand(log.id)"
      >
        <!-- Timeline dot -->
        <div
          class="timeline-dot"
          :style="{ background: getLogColor(log.type) }"
        />
        
        <!-- Timeline 卡片特殊渲染 -->
        <div
          v-if="isTimelineType(log.type)"
          class="timeline-card"
          :style="{ '--timeline-color': getLogColor(log.type) }"
        >
          <div class="timeline-card-header">
            <div class="timeline-card-icon-wrapper" :style="{ background: getLogColor(log.type) + '20' }">
              <component 
                :is="getLogIcon(log.type)" 
                class="timeline-card-icon"
                :style="{ color: getLogColor(log.type) }"
              />
            </div>
            <div class="timeline-card-info">
              <span class="timeline-card-label" :style="{ color: getLogColor(log.type) }">
                {{ getTimelineLabel(log.type) }}
              </span>
              <span class="timeline-card-time">{{ formatTime(log.timestamp) }}</span>
            </div>
          </div>
          <div class="timeline-card-title">
            {{ log.timelineData?.title || log.content }}
          </div>
          <div v-if="log.timelineData?.description" class="timeline-card-desc">
            {{ log.timelineData.description.slice(0, 150) }}{{ log.timelineData.description.length > 150 ? '...' : '' }}
          </div>
          <!-- 搜索结果数 -->
          <div v-if="log.type === 'timeline-search' && log.timelineData?.resultsCount" class="timeline-card-meta">
            <span class="meta-badge">{{ log.timelineData.resultsCount }} 条结果</span>
          </div>
          <!-- URL 链接 -->
          <a 
            v-if="log.type === 'timeline-read' && log.timelineData?.url" 
            class="timeline-card-url"
            :href="log.timelineData.url"
            target="_blank"
            rel="noopener"
            @click.stop
          >
            {{ log.timelineData.url }}
          </a>
          <!-- 截图预览 -->
          <div v-if="log.type === 'timeline-screenshot' && log.timelineData?.screenshotPath" class="timeline-card-screenshot">
            <img 
              :src="log.timelineData.screenshotPath" 
              alt="页面截图"
              class="screenshot-preview"
              @click.stop="showScreenshot(log.timelineData.screenshotPath)"
            />
          </div>
        </div>

        <!-- 普通日志卡片 -->
        <div v-else class="log-card">
          <div class="log-header">
            <div class="log-type-wrapper">
              <component 
                :is="getLogIcon(log.type)" 
                class="log-icon"
                :style="{ color: getLogColor(log.type) }"
              />
              <span
                class="log-type"
                :style="{ color: getLogColor(log.type) }"
              >
                {{ log.type }}
              </span>
            </div>
            <div class="log-meta">
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <ChevronDownIcon
                v-if="isLogExpanded(log.id)"
                class="expand-icon"
              />
              <ChevronRightIcon
                v-else
                class="expand-icon"
              />
            </div>
          </div>
          
          <!-- Collapsed preview -->
          <div
            v-if="!isLogExpanded(log.id)"
            class="log-preview"
          >
            {{ log.content.slice(0, 100) }}{{ log.content.length > 100 ? '...' : '' }}
          </div>
          
          <!-- Expanded content -->
          <Transition name="expand">
            <div
              v-if="isLogExpanded(log.id)"
              class="log-content"
            >
              {{ log.content }}
            </div>
          </Transition>
        </div>
      </div>
      
      <!-- Jump to latest button -->
      <Transition name="fade-up">
        <button
          v-if="showJumpToLatest"
          class="jump-to-latest glass-button-primary"
          aria-label="`跳转到最新日志，有 ${newContentCount} 条新日志`"
          @click="scrollToBottom()"
        >
          <ArrowDownIcon
            class="jump-icon"
            aria-hidden="true"
          />
          <span>{{ newContentCount }} 条新日志</span>
        </button>
      </Transition>
    </div>

    <!-- Bottom Input Box -->
    <div class="chat-input-section">
      <div class="chat-input-box">
        <textarea
          v-model="chatInputValue"
          class="chat-textarea"
          placeholder="追加指令或补充信息..."
          rows="1"
          @keydown="handleChatKeydown"
          @input="autoResizeTextarea"
        />
        <div class="chat-input-actions">
          <button
            class="chat-send-btn"
            :disabled="!chatInputValue.trim()"
            @click="sendChatMessage"
          >
            <ArrowUpIcon class="send-icon" />
          </button>
        </div>
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
        <img
          :src="screenshotPath"
          class="max-w-full max-h-full rounded-lg"
        >
        <button 
          class="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 text-white"
          @click="showScreenshotModal = false"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { BrowserOperationLog, TimeLapseGallery } from './browser'
import type { BrowserOperation, TimeLapsePlayback } from './browser/types'
import CoworkerFileTree from './workflow/CoworkerFileTree.vue'
import LiveDiff from './artifact/LiveDiff.vue'
import { useScrollSync } from '@/composables/useScrollSync'
import {
  LightBulbIcon,
  WrenchScrewdriverIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  ArrowDownIcon,
  ArrowUpIcon,
  // Timeline 图标
  MagnifyingGlassIcon,
  DocumentTextIcon,
  CameraIcon,
  SparklesIcon,
  FlagIcon,
} from '@heroicons/vue/24/outline'

interface Props {
  sessionId: string
  userQuery?: string
  userInitial?: string
}

const props = withDefaults(defineProps<Props>(), {
  userQuery: '',
  userInitial: 'U'
})

// Use Pinia store
const executionStore = useExecutionStore()

const mode = ref<'all' | 'coworker' | 'browser'>('all')
const isFocusMode = ref(false)
const focusedNodeId = ref<string | null>(null)
const logsContainerRef = ref<HTMLElement | null>(null)

// Chat input
const chatInputValue = ref('')

// Emit events
const emit = defineEmits<{
  'send-message': [message: string]
}>()

// Handle chat input keydown
function handleChatKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendChatMessage()
  }
}

// Auto resize textarea
function autoResizeTextarea(e: Event) {
  const target = e.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

// Send chat message
function sendChatMessage() {
  if (!chatInputValue.value.trim()) return
  emit('send-message', chatInputValue.value.trim())
  chatInputValue.value = ''
}

// Use scroll sync composable
const {
  showJumpToLatest,
  newContentCount,
  scrollToBottom,
  notifyNewContent,
  lockScroll,
  unlockScroll,
  isUserReading
} = useScrollSync(logsContainerRef)

// Coworker mode state
const selectedFileOperation = ref<any>(null)
const coworkerSplitRatio = ref(50) // 50% FileTree, 50% LiveDiff

// Log expansion state
const expandedLogs = ref<Set<string>>(new Set())

// Performance optimization: Virtual scrolling with windowing
const MAX_RENDERED_LOGS = 500 // Maximum logs to render at once
const WINDOW_SIZE = 100 // Keep last N logs when trimming

// Use logs from store with performance optimization
const displayLogs = computed(() => {
  try {
    let logs = executionStore.logs || []

    // Validate logs is an array
    if (!Array.isArray(logs)) {
      console.error('[StreamingInfo] logs is not an array:', logs)
      return []
    }

    // Filter by focus mode
    if (isFocusMode.value && focusedNodeId.value) {
      logs = logs.filter(log => log?.nodeId === focusedNodeId.value)
    }

    // Performance optimization: Limit rendered logs
    // Keep the most recent logs to prevent DOM bloat
    if (logs.length > MAX_RENDERED_LOGS) {
      // Keep last WINDOW_SIZE logs for smooth scrolling
      logs = logs.slice(-MAX_RENDERED_LOGS)
    }

    return logs
  } catch (error) {
    console.error('[StreamingInfo] Error computing displayLogs:', error)
    return []
  }
})

// Auto-scroll to bottom when new logs arrive
watch(
  () => executionStore.logs.length,
  () => {
    notifyNewContent()
  }
)

function formatTime(timestamp: number) {
  try {
    // Validate timestamp
    if (typeof timestamp !== 'number' || isNaN(timestamp) || timestamp < 0) {
      return '--:--:--'
    }
    const date = new Date(timestamp)
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return '--:--:--'
    }
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch (error) {
    console.error('[StreamingInfo] Error formatting time:', error)
    return '--:--:--'
  }
}

// Get icon for log type
function getLogIcon(type: string) {
  switch (type) {
    case 'thinking': return LightBulbIcon
    case 'tool-call': return WrenchScrewdriverIcon
    case 'result': return CheckCircleIcon
    case 'error': return ExclamationTriangleIcon
    // Timeline 类型
    case 'timeline-search': return MagnifyingGlassIcon
    case 'timeline-read': return DocumentTextIcon
    case 'timeline-screenshot': return CameraIcon
    case 'timeline-finding': return SparklesIcon
    case 'timeline-milestone': return FlagIcon
    default: return LightBulbIcon
  }
}

// Get color for log type
function getLogColor(type: string): string {
  switch (type) {
    case 'thinking': return 'var(--vibe-color-active)'
    case 'tool-call': return 'var(--vibe-color-pending)'
    case 'result': return 'var(--vibe-color-success)'
    case 'error': return 'var(--vibe-color-error)'
    // Timeline 颜色
    case 'timeline-search': return '#3B82F6'  // 蓝色
    case 'timeline-read': return '#10B981'    // 绿色
    case 'timeline-screenshot': return '#8B5CF6'  // 紫色
    case 'timeline-finding': return '#F59E0B'  // 琥珀色
    case 'timeline-milestone': return '#EC4899'  // 玫红色
    default: return 'var(--vibe-color-active)'
  }
}

// Check if log type is timeline
function isTimelineType(type: string): boolean {
  return type.startsWith('timeline-')
}

// Get timeline type label
function getTimelineLabel(type: string): string {
  switch (type) {
    case 'timeline-search': return '搜索'
    case 'timeline-read': return '阅读'
    case 'timeline-screenshot': return '截图'
    case 'timeline-finding': return '发现'
    case 'timeline-milestone': return '里程碑'
    default: return ''
  }
}

// Toggle log expansion
function toggleLogExpand(logId: string) {
  if (expandedLogs.value.has(logId)) {
    expandedLogs.value.delete(logId)
  } else {
    expandedLogs.value.add(logId)
  }
}

// Check if log is expanded
function isLogExpanded(logId: string): boolean {
  return expandedLogs.value.has(logId)
}

// Handle file select in Coworker mode
function handleFileSelect(operation: any) {
  selectedFileOperation.value = operation
}

// Toggle scroll lock
function toggleScrollLock() {
  if (isUserReading.value) {
    unlockScroll()
  } else {
    lockScroll()
  }
}

function scrollToNode(nodeId: string) {
  try {
    if (!nodeId || !logsContainerRef.value) {
      console.warn('[StreamingInfo] Invalid nodeId or container ref')
      return
    }
    const element = logsContainerRef.value.querySelector(`[data-node-id="${nodeId}"]`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      console.warn('[StreamingInfo] Node element not found:', nodeId)
    }
  } catch (error) {
    console.error('[StreamingInfo] Error scrolling to node:', error)
  }
}

function enterFocusMode(nodeId: string) {
  try {
    if (!nodeId) {
      console.warn('[StreamingInfo] Invalid nodeId for focus mode')
      return
    }
    isFocusMode.value = true
    focusedNodeId.value = nodeId
  } catch (error) {
    console.error('[StreamingInfo] Error entering focus mode:', error)
  }
}

function exitFocusMode() {
  try {
    isFocusMode.value = false
    focusedNodeId.value = null
  } catch (error) {
    console.error('[StreamingInfo] Error exiting focus mode:', error)
  }
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
/* StreamingInfo - 使用全局主题变量 */
.streaming-info {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
}

/* User Query Section */
.user-query-section {
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.user-query-bubble {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 80%;
  margin-left: auto;
}

.user-avatar {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  background: #a855f7;
  border-radius: 50%;
  flex-shrink: 0;
}

.user-query-text {
  padding: 10px 14px;
  background: var(--any-bg-tertiary);
  border-radius: 16px 16px 4px 16px;
  font-size: 14px;
  line-height: 1.5;
  color: var(--any-text-primary);
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-lock {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-hover);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.btn-lock:hover {
  background: var(--any-bg-active);
}

.btn-lock.active {
  background: var(--td-state-waiting-bg);
  border-color: var(--td-state-waiting);
}

.lock-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-secondary);
}

.btn-lock.active .lock-icon {
  color: var(--td-state-waiting);
}

.browser-log-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Coworker split view */
.coworker-container {
  flex: 1;
  overflow: hidden;
}

.coworker-split {
  display: flex;
  height: 100%;
}

.coworker-left,
.coworker-right {
  overflow: hidden;
}

.coworker-divider {
  width: 1px;
  background: var(--any-border);
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--any-text-muted);
  font-size: 14px;
}

/* Logs container with timeline */
.logs-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 16px 16px 32px;
  position: relative;
  /* Performance optimization: Use GPU acceleration */
  will-change: scroll-position;
  transform: translateZ(0);
}

/* Performance indicator */
.performance-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: rgba(255, 184, 0, 0.1);
  border: 1px solid rgba(255, 184, 0, 0.3);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--td-state-waiting);
}

.indicator-icon {
  font-size: 14px;
  animation: pulse-icon 1.5s ease-in-out infinite;
}

@keyframes pulse-icon {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

.indicator-text {
  font-weight: 500;
}

.timeline-track {
  position: absolute;
  left: 24px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--any-border);
}

/* Log entry with timeline dot */
.log-entry {
  position: relative;
  margin-bottom: 12px;
  cursor: pointer;
}

.timeline-dot {
  position: absolute;
  left: -20px;
  top: 16px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
  z-index: 1;
}

.log-card {
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border-light);
  border-radius: var(--any-radius-md);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.log-entry:hover .log-card {
  background: var(--any-bg-tertiary);
  border-color: var(--any-border);
}

.log-entry.expanded .log-card {
  background: var(--any-bg-tertiary);
  border-color: var(--any-border-hover);
}

.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.log-type-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-icon {
  width: 16px;
  height: 16px;
}

.log-type {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-time {
  font-size: 11px;
  color: var(--any-text-muted);
}

.expand-icon {
  width: 14px;
  height: 14px;
  color: var(--any-text-muted);
  transition: transform var(--any-duration-fast) var(--any-ease-out);
}

.log-preview {
  margin-top: 8px;
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.5;
}

.log-content {
  margin-top: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--any-text-primary);
  font-family: 'SF Mono', 'Monaco', monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Jump to latest button */
.jump-to-latest {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  z-index: 10;
}

.jump-icon {
  width: 16px;
  height: 16px;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(3px); }
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 200ms ease-out;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

/* Fade up transition for jump button */
.fade-up-enter-active,
.fade-up-leave-active {
  transition: all 200ms ease-out;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(10px);
}

/* Accessibility: Focus styles */
.glass-tab:focus-visible {
  outline: 2px solid var(--vibe-color-active);
  outline-offset: 2px;
}

.btn-exit-focus:focus-visible,
.btn-lock:focus-visible {
  outline: 2px solid var(--vibe-color-active);
  outline-offset: 2px;
}

.log-entry:focus-visible {
  outline: 2px solid var(--vibe-color-active);
  outline-offset: 2px;
}

.jump-to-latest:focus-visible {
  outline: 2px solid var(--vibe-color-active);
  outline-offset: 2px;
}

/* Timeline 卡片样式 */
.timeline-entry {
  margin-bottom: 16px;
}

.timeline-card {
  padding: 16px;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--timeline-color) 8%, var(--any-bg-secondary)),
    var(--any-bg-secondary)
  );
  border: 1px solid color-mix(in srgb, var(--timeline-color) 25%, var(--any-border));
  border-radius: var(--any-radius-lg);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.timeline-entry:hover .timeline-card {
  border-color: var(--timeline-color);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--timeline-color) 15%, transparent);
}

.timeline-card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.timeline-card-icon-wrapper {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md);
}

.timeline-card-icon {
  width: 20px;
  height: 20px;
}

.timeline-card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.timeline-card-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.timeline-card-time {
  font-size: 11px;
  color: var(--any-text-muted);
}

.timeline-card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  line-height: 1.4;
  margin-bottom: 8px;
}

.timeline-card-desc {
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.5;
  margin-bottom: 12px;
}

.timeline-card-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.meta-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-full);
  color: var(--any-text-secondary);
}

.timeline-card-url {
  display: block;
  font-size: 12px;
  color: var(--vibe-color-active);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 8px;
}

.timeline-card-url:hover {
  text-decoration: underline;
}

.timeline-card-screenshot {
  margin-top: 12px;
  border-radius: var(--any-radius-md);
  overflow: hidden;
  border: 1px solid var(--any-border);
}

.screenshot-preview {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  cursor: zoom-in;
  transition: opacity var(--any-duration-fast);
}

.screenshot-preview:hover {
  opacity: 0.9;
}

/* Scrollbar */
.logs-container::-webkit-scrollbar {
  width: 6px;
}

.logs-container::-webkit-scrollbar-track {
  background: var(--any-bg-tertiary);
  border-radius: 3px;
}

.logs-container::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 3px;
}

/* Chat Input Section */
.chat-input-section {
  padding: 12px 16px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.chat-input-box {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 8px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 20px;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.chat-input-box:focus-within {
  border-color: var(--any-border-hover);
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.1);
}

.chat-textarea {
  flex: 1;
  min-height: 20px;
  max-height: 120px;
  padding: 0;
  font-size: 14px;
  line-height: 1.4;
  color: var(--any-text-primary);
  background: transparent;
  border: none;
  resize: none;
  outline: none;
}

.chat-textarea::placeholder {
  color: var(--any-text-muted);
}

.chat-input-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chat-send-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--exec-accent, #00D9FF);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.chat-send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 217, 255, 0.4);
}

.chat-send-btn:disabled {
  background: var(--any-bg-tertiary);
  cursor: not-allowed;
}

.chat-send-btn .send-icon {
  width: 16px;
  height: 16px;
  color: white;
}

.chat-send-btn:disabled .send-icon {
  color: var(--any-text-muted);
}
</style>
