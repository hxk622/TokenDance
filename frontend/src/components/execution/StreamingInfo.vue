<template>
  <div class="streaming-info">
    <div class="toolbar">
      <div class="mode-tabs">
        <button :class="{ active: mode === 'all' }" @click="mode = 'all'">全部</button>
        <button :class="{ active: mode === 'coworker' }" @click="mode = 'coworker'">Coworker</button>
      </div>
      <button v-if="isFocusMode" class="btn-exit-focus" @click="exitFocusMode">
        退出聚焦模式
      </button>
    </div>

    <div class="logs-container" ref="logsContainerRef">
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  sessionId: string
}

interface LogEntry {
  id: string
  nodeId: string
  timestamp: number
  type: 'thinking' | 'tool-call' | 'result' | 'error'
  content: string
}

defineProps<Props>()

const mode = ref<'all' | 'coworker'>('all')
const isFocusMode = ref(false)
const focusedNodeId = ref<string | null>(null)
const logsContainerRef = ref<HTMLElement | null>(null)

// Mock logs
const allLogs = ref<LogEntry[]>([
  { id: '1', nodeId: '1', timestamp: Date.now() - 60000, type: 'thinking', content: '分析用户需求...' },
  { id: '2', nodeId: '1', timestamp: Date.now() - 50000, type: 'tool-call', content: 'web_search("AI Agent market")' },
  { id: '3', nodeId: '1', timestamp: Date.now() - 40000, type: 'result', content: '找到 5 篇相关文章' },
  { id: '4', nodeId: '2', timestamp: Date.now() - 30000, type: 'thinking', content: '开始深度研究...' },
  { id: '5', nodeId: '2', timestamp: Date.now() - 20000, type: 'tool-call', content: 'read_url("https://example.com/ai-market")' },
  { id: '6', nodeId: '2', timestamp: Date.now() - 10000, type: 'result', content: '提取关键信息：市场规模、增长趋势...' },
])

const displayLogs = computed(() => {
  if (isFocusMode.value && focusedNodeId.value) {
    return allLogs.value.filter(log => log.nodeId === focusedNodeId.value)
  }
  return allLogs.value
})

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
