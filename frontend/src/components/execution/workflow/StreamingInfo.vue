<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'

interface Props {
  sessionId: string
}

const props = defineProps<Props>()

interface LogEntry {
  id: string
  nodeId: string
  timestamp: number
  type: 'thinking' | 'tool-call' | 'result' | 'error'
  content: string
}

// Mock data for Phase 1
const logs = ref<LogEntry[]>([
  { id: '1', nodeId: '1', timestamp: Date.now() - 60000, type: 'thinking', content: '正在搜索市场数据...' },
  { id: '2', nodeId: '1', timestamp: Date.now() - 55000, type: 'tool-call', content: 'web_search("AI Agent 市场规模")' },
  { id: '3', nodeId: '1', timestamp: Date.now() - 50000, type: 'result', content: '找到3篇相关报告' },
  { id: '4', nodeId: '2', timestamp: Date.now() - 40000, type: 'thinking', content: '分析竞品特点...' },
  { id: '5', nodeId: '2', timestamp: Date.now() - 35000, type: 'tool-call', content: 'analyze_competitors(["Manus", "Coworker"])' },
  { id: '6', nodeId: '3', timestamp: Date.now() - 10000, type: 'thinking', content: '生成markdown报告...' },
  { id: '7', nodeId: '3', timestamp: Date.now() - 5000, type: 'tool-call', content: 'coworker.create_file("report.md")' },
])

const mode = ref<'all' | 'coworker'>('all')
const logStreamRef = ref<HTMLElement | null>(null)
const isScrollLocked = ref(false)
const focusNodeId = ref<string | null>(null)

// Smart scroll strategy
const lastClickTime = ref(0)
const userScrollTimeout = ref<NodeJS.Timeout | null>(null)
const isUserScrolling = ref(false)

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

// SVG path data for icons (Lucide-style)
const iconPaths = {
  thinking: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z', // message-square
  'tool-call': 'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z', // wrench
  result: 'M22 11.08V12a10 10 0 1 1-5.93-9.14|M22 4 12 14.01l-3-3', // check-circle
  error: 'M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z|M15 9l-6 6|M9 9l6 6', // x-circle
}

function getLogIconPath(type: LogEntry['type']): string {
  return iconPaths[type] || iconPaths.thinking
}

// Scroll-Sync: Scroll to specific node's logs with smart strategy
function scrollToNode(nodeId: string) {
  if (isScrollLocked.value || isUserScrolling.value) return
  
  const now = Date.now()
  const timeSinceLastClick = now - lastClickTime.value
  lastClickTime.value = now
  
  // 5秒内连续点击 → 只高亮不滚动
  const onlyHighlight = timeSinceLastClick < 5000
  
  nextTick(() => {
    const logStream = logStreamRef.value
    if (!logStream) return
    
    const targetLog = logStream.querySelector(`[data-node-id="${nodeId}"]`) as HTMLElement
    if (targetLog) {
      // 只高亮或者滚动+高亮
      if (!onlyHighlight) {
        targetLog.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
      
      // Highlight the log entry
      targetLog.style.background = 'rgba(0, 217, 255, 0.3)'
      targetLog.style.transition = 'background 120ms ease-out'
      setTimeout(() => {
        targetLog.style.background = ''
      }, 1000)
    }
  })
}

function toggleScrollLock() {
  isScrollLocked.value = !isScrollLocked.value
}

// Detect user scroll and pause auto-sync
function handleUserScroll() {
  isUserScrolling.value = true
  
  // Clear previous timeout
  if (userScrollTimeout.value) {
    clearTimeout(userScrollTimeout.value)
  }
  
  // Resume auto-sync after 3 seconds of no scrolling
  userScrollTimeout.value = setTimeout(() => {
    isUserScrolling.value = false
  }, 3000)
}

// Focus Mode: Filter logs by specific nodeId
function enterFocusMode(nodeId: string) {
  focusNodeId.value = nodeId
}

function exitFocusMode() {
  focusNodeId.value = null
}

// Computed filtered logs
const filteredLogs = computed(() => {
  let filtered = logs.value
  
  // Filter by Focus Mode
  if (focusNodeId.value) {
    filtered = filtered.filter(log => log.nodeId === focusNodeId.value)
  }
  
  // Filter by mode (Coworker only)
  if (mode.value === 'coworker') {
    filtered = filtered.filter(log => 
      log.content.includes('coworker') || log.type === 'tool-call'
    )
  }
  
  return filtered
})

// Expose methods for parent component
defineExpose({
  scrollToNode,
  enterFocusMode,
  exitFocusMode,
})
</script>

<template>
  <div class="streaming-info">
    <!-- Mode Tabs -->
    <div class="mode-tabs">
      <button
        :class="['tab', { active: mode === 'all' }]"
        @click="mode = 'all'"
      >
        全部日志
      </button>
      <button
        :class="['tab', { active: mode === 'coworker' }]"
        @click="mode = 'coworker'"
      >
        Coworker 文件操作
      </button>
      <button 
        :class="['btn-lock', { locked: isScrollLocked }]"
        :title="isScrollLocked ? '解锁视图' : '固定视图（暂停Scroll-Sync）'"
        @click="toggleScrollLock"
      >
        <!-- Lock icon (locked state) -->
        <svg
          v-if="isScrollLocked"
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect
            x="3"
            y="11"
            width="18"
            height="11"
            rx="2"
            ry="2"
          />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
        <!-- Unlock icon (unlocked state) -->
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <rect
            x="3"
            y="11"
            width="18"
            height="11"
            rx="2"
            ry="2"
          />
          <path d="M7 11V7a5 5 0 0 1 9.9-1" />
        </svg>
      </button>
    </div>

    <!-- Focus Mode Indicator -->
    <div
      v-if="focusNodeId"
      class="focus-indicator"
    >
      <span>🎯 聚焦模式：Node-{{ focusNodeId }}</span>
      <button
        class="btn-exit-focus"
        @click="exitFocusMode"
      >
        退出聚焦
      </button>
    </div>

    <!-- Log Stream -->
    <div
      ref="logStreamRef"
      class="log-stream"
      @scroll="handleUserScroll"
    >
      <div
        v-for="log in filteredLogs"
        :key="log.id"
        :class="['log-entry', log.type]"
        :data-node-id="log.nodeId"
      >
        <div class="log-meta">
          <span class="log-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path
                v-for="(d, i) in getLogIconPath(log.type).split('|')"
                :key="i"
                :d="d"
              />
            </svg>
          </span>
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-node">Node-{{ log.nodeId }}</span>
        </div>
        <div class="log-content">
          {{ log.content }}
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="filteredLogs.length === 0"
      class="empty-state"
    >
      <span class="empty-icon">📋</span>
      <p>暂无执行日志</p>
    </div>
  </div>
</template>

<style scoped>
.streaming-info {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
  padding: 16px;
  overflow: hidden;
}

/* Mode Tabs */
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--any-border);
}

.tab {
  padding: 6px 12px;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  background: transparent;
  color: var(--any-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.tab:hover {
  background: var(--any-bg-tertiary);
}

.tab.active {
  background: var(--td-state-thinking-bg);
  border-color: var(--td-state-thinking);
  color: var(--td-state-thinking);
}

.btn-lock {
  margin-left: auto;
  padding: 6px 12px;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-lock:hover {
  background: var(--any-bg-tertiary);
}

.btn-lock.locked {
  background: var(--td-state-waiting-bg);
  border-color: var(--td-state-waiting);
}

/* Focus Mode Indicator */
.focus-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 12px;
  background: var(--td-state-thinking-bg);
  border: 1px solid color-mix(in srgb, var(--td-state-thinking) 30%, transparent);
  border-radius: 6px;
  color: var(--td-state-thinking);
  font-size: 12px;
}

.btn-exit-focus {
  padding: 4px 10px;
  border: 1px solid color-mix(in srgb, var(--td-state-thinking) 50%, transparent);
  border-radius: 4px;
  background: transparent;
  color: var(--td-state-thinking);
  cursor: pointer;
  font-size: 11px;
  transition: all 120ms ease-out;
}

.btn-exit-focus:hover {
  background: var(--td-state-thinking-bg);
}

/* Log Stream */
.log-stream {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.log-stream::-webkit-scrollbar {
  width: 6px;
}

.log-stream::-webkit-scrollbar-track {
  background: var(--any-bg-tertiary);
  border-radius: 3px;
}

.log-stream::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 3px;
}

.log-stream::-webkit-scrollbar-thumb:hover {
  background: var(--any-text-muted);
}

/* Log Entry */
.log-entry {
  padding: 12px;
  border-radius: 8px;
  background: var(--any-bg-secondary);
  border-left: 3px solid transparent;
  transition: all 120ms ease-out;
}

.log-entry:hover {
  background: var(--any-bg-hover);
}

.log-entry.thinking {
  border-left-color: var(--any-text-tertiary);
}

.log-entry.tool-call {
  border-left-color: var(--td-state-thinking);
}

.log-entry.result {
  border-left-color: var(--td-state-executing);
}

.log-entry.error {
  border-left-color: var(--td-state-error);
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.log-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.log-icon svg {
  width: 14px;
  height: 14px;
}

.log-time {
  color: var(--any-text-secondary);
}

.log-node {
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--any-bg-tertiary);
  color: var(--any-text-secondary);
  font-size: 11px;
}

.log-content {
  color: var(--any-text-primary);
  font-size: 13px;
  line-height: 1.6;
  font-family: 'SF Mono', 'Monaco', 'Courier New', monospace;
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--any-text-secondary);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

</style>
