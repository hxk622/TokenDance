<script setup lang="ts">
import { ref, nextTick } from 'vue'

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

function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

function getLogIcon(type: LogEntry['type']): string {
  const icons = {
    thinking: '💭',
    'tool-call': '🔧',
    result: '✅',
    error: '❌',
  }
  return icons[type]
}

// Scroll-Sync: Scroll to specific node's logs
function scrollToNode(nodeId: string) {
  if (isScrollLocked.value) return
  
  nextTick(() => {
    const logStream = logStreamRef.value
    if (!logStream) return
    
    const targetLog = logStream.querySelector(`[data-node-id="${nodeId}"]`) as HTMLElement
    if (targetLog) {
      targetLog.scrollIntoView({ behavior: 'smooth', block: 'start' })
      // Highlight the log entry
      targetLog.style.background = 'rgba(0, 217, 255, 0.3)'
      setTimeout(() => {
        targetLog.style.background = ''
      }, 1000)
    }
  })
}

function toggleScrollLock() {
  isScrollLocked.value = !isScrollLocked.value
}

// Expose methods for parent component
defineExpose({
  scrollToNode,
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
        {{ isScrollLocked ? '🔒' : '🔓' }}
      </button>
    </div>

    <!-- Log Stream -->
    <div ref="logStreamRef" class="log-stream">
      <div
        v-for="log in logs"
        :key="log.id"
        :class="['log-entry', log.type]"
        :data-node-id="log.nodeId"
      >
        <div class="log-meta">
          <span class="log-icon">{{ getLogIcon(log.type) }}</span>
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-node">Node-{{ log.nodeId }}</span>
        </div>
        <div class="log-content">
          {{ log.content }}
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="logs.length === 0" class="empty-state">
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
  background: var(--bg-primary, rgba(18, 18, 18, 0.95));
  padding: 16px;
  overflow: hidden;
}

/* Mode Tabs */
.mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--divider-color);
}

.tab {
  padding: 6px 12px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.tab:hover {
  background: rgba(255, 255, 255, 0.05);
}

.tab.active {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--color-node-active);
  color: var(--color-node-active);
}

.btn-lock {
  margin-left: auto;
  padding: 6px 12px;
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-lock:hover {
  background: rgba(255, 255, 255, 0.05);
}

.btn-lock.locked {
  background: rgba(255, 184, 0, 0.2);
  border-color: #FFB800;
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
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.log-stream::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.log-stream::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Log Entry */
.log-entry {
  padding: 12px;
  border-radius: 8px;
  background: rgba(28, 28, 30, 0.6);
  border-left: 3px solid transparent;
  transition: all 120ms ease-out;
}

.log-entry:hover {
  background: rgba(28, 28, 30, 0.9);
}

.log-entry.thinking {
  border-left-color: #8E8E93;
}

.log-entry.tool-call {
  border-left-color: #00D9FF;
}

.log-entry.result {
  border-left-color: #00FF88;
}

.log-entry.error {
  border-left-color: #FF3B30;
}

.log-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 12px;
}

.log-icon {
  font-size: 14px;
}

.log-time {
  color: var(--text-secondary);
}

.log-node {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-secondary);
  font-size: 11px;
}

.log-content {
  color: var(--text-primary);
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
  color: var(--text-secondary);
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

/* CSS Variables */
:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
  --color-node-active: #00D9FF;
}
</style>
