<script setup lang="ts">
import { ref } from 'vue'

interface FileOperation {
  path: string
  action: 'read' | 'modified' | 'created' | 'deleted'
  timestamp: number
}

// Mock data
const operations = ref<FileOperation[]>([
  { path: 'src/main.ts', action: 'read', timestamp: Date.now() - 60000 },
  { path: 'src/components/Button.vue', action: 'modified', timestamp: Date.now() - 50000 },
  { path: 'docs/report.md', action: 'created', timestamp: Date.now() - 30000 },
  { path: 'tests/old.spec.ts', action: 'deleted', timestamp: Date.now() - 20000 },
])

const selectedFile = ref<string | null>(null)

function getActionIcon(action: FileOperation['action']): string {
  const icons = {
    read: '👁️',
    modified: '✏️',
    created: '➕',
    deleted: '🗑️',
  }
  return icons[action]
}

function getActionColor(action: FileOperation['action']): string {
  const colors = {
    read: '#8E8E93',
    modified: '#00D9FF',
    created: '#00FF88',
    deleted: '#FF3B30',
  }
  return colors[action]
}

function selectFile(path: string) {
  selectedFile.value = path
  // TODO: Emit event to show diff
}

function formatTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  return `${Math.floor(minutes / 60)}小时前`
}
</script>

<template>
  <div class="coworker-file-tree">
    <div class="tree-header">
      <h3>文件操作记录</h3>
      <span class="file-count">{{ operations.length }} 个文件</span>
    </div>

    <div class="file-list">
      <div
        v-for="op in operations"
        :key="op.path"
        :class="['file-item', op.action, { selected: selectedFile === op.path }]"
        @click="selectFile(op.path)"
      >
        <div class="file-info">
          <span class="action-icon">{{ getActionIcon(op.action) }}</span>
          <span class="file-path">{{ op.path }}</span>
        </div>
        <div class="file-meta">
          <span class="action-badge" :style="{ color: getActionColor(op.action) }">
            {{ op.action }}
          </span>
          <span class="timestamp">{{ formatTime(op.timestamp) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="operations.length === 0" class="empty-state">
      <span class="empty-icon">📁</span>
      <p>暂无文件操作</p>
    </div>
  </div>
</template>

<style scoped>
.coworker-file-tree {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, rgba(18, 18, 18, 0.95));
  padding: 16px;
}

.tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--divider-color);
}

.tree-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.file-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.file-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-list::-webkit-scrollbar {
  width: 6px;
}

.file-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.file-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.file-item {
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(28, 28, 30, 0.6);
  border-left: 3px solid transparent;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.file-item:hover {
  background: rgba(28, 28, 30, 0.9);
}

.file-item.selected {
  background: rgba(0, 217, 255, 0.15);
  border-left-color: var(--color-node-active);
}

.file-item.modified {
  border-left-color: #00D9FF;
}

.file-item.created {
  border-left-color: #00FF88;
}

.file-item.deleted {
  border-left-color: #FF3B30;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.action-icon {
  font-size: 14px;
}

.file-path {
  color: var(--text-primary);
  font-size: 13px;
  font-family: 'SF Mono', 'Monaco', monospace;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 11px;
}

.action-badge {
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  text-transform: capitalize;
}

.timestamp {
  color: var(--text-secondary);
}

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

:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
  --color-node-active: #00D9FF;
}
</style>
