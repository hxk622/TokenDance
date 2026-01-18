<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  EyeIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  DocumentIcon,
  FolderIcon
} from '@heroicons/vue/24/outline'

interface FileOperation {
  path: string
  action: 'read' | 'modified' | 'created' | 'deleted'
  timestamp: number
  originalContent?: string
  modifiedContent?: string
  linesAdded?: number
  linesRemoved?: number
}

const props = defineProps<{
  operations?: FileOperation[]
}>()

const emit = defineEmits<{
  (e: 'file-select', operation: FileOperation): void
  (e: 'file-double-click', operation: FileOperation): void
}>()

// Mock data (used when no props provided)
const defaultOperations: FileOperation[] = [
  { path: 'src/main.ts', action: 'read', timestamp: Date.now() - 60000 },
  { path: 'src/components/Button.vue', action: 'modified', timestamp: Date.now() - 50000, linesAdded: 12, linesRemoved: 3 },
  { path: 'docs/report.md', action: 'created', timestamp: Date.now() - 30000, linesAdded: 45 },
  { path: 'tests/old.spec.ts', action: 'deleted', timestamp: Date.now() - 20000, linesRemoved: 28 },
]

const internalOperations = ref<FileOperation[]>(props.operations || defaultOperations)
const selectedFile = ref<string | null>(null)

// Watch for prop changes
watch(() => props.operations, (newOps) => {
  if (newOps) {
    internalOperations.value = newOps
  }
})

// Get icon component for action
function getActionIcon(action: FileOperation['action']) {
  const icons = {
    read: EyeIcon,
    modified: PencilIcon,
    created: PlusIcon,
    deleted: TrashIcon,
  }
  return icons[action]
}

function getActionColor(action: FileOperation['action']): string {
  const colors = {
    read: 'var(--vibe-color-inactive)',
    modified: 'var(--vibe-color-active)',
    created: 'var(--vibe-color-success)',
    deleted: 'var(--vibe-color-error)',
  }
  return colors[action]
}

function getActionLabel(action: FileOperation['action']): string {
  const labels = {
    read: '读取',
    modified: '修改',
    created: '新建',
    deleted: '删除',
  }
  return labels[action]
}

function selectFile(operation: FileOperation) {
  selectedFile.value = operation.path
  emit('file-select', operation)
}

function handleDoubleClick(operation: FileOperation) {
  emit('file-double-click', operation)
}

function formatTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  return `${Math.floor(minutes / 60)}小时前`
}

// Get file extension icon
function getFileIcon(path: string) {
  const ext = path.split('.').pop()?.toLowerCase()
  // Could expand this with specific icons for different file types
  if (ext === 'vue' || ext === 'ts' || ext === 'js' || ext === 'tsx') {
    return DocumentIcon
  }
  return DocumentIcon
}

// Format diff stats
function formatDiffStats(op: FileOperation): string {
  const parts = []
  if (op.linesAdded) parts.push(`+${op.linesAdded}`)
  if (op.linesRemoved) parts.push(`-${op.linesRemoved}`)
  return parts.join(' ')
}

// Check if operation has diff stats
function hasDiffStats(op: FileOperation): boolean {
  return (op.linesAdded !== undefined && op.linesAdded > 0) || 
         (op.linesRemoved !== undefined && op.linesRemoved > 0)
}

// Computed: summary stats
const summaryStats = computed(() => {
  const stats = {
    read: 0,
    modified: 0,
    created: 0,
    deleted: 0
  }
  internalOperations.value.forEach(op => {
    stats[op.action]++
  })
  return stats
})

// Expose for parent components
defineExpose({
  selectedFile,
  operations: internalOperations
})
</script>

<template>
  <div class="coworker-file-tree glass-panel-light">
    <div class="tree-header">
      <div class="header-left">
        <FolderIcon class="header-icon" />
        <h3>文件操作</h3>
      </div>
      <div class="header-stats">
        <span
          v-if="summaryStats.created > 0"
          class="stat-badge created"
        >
          <PlusIcon class="stat-icon" />
          {{ summaryStats.created }}
        </span>
        <span
          v-if="summaryStats.modified > 0"
          class="stat-badge modified"
        >
          <PencilIcon class="stat-icon" />
          {{ summaryStats.modified }}
        </span>
        <span
          v-if="summaryStats.deleted > 0"
          class="stat-badge deleted"
        >
          <TrashIcon class="stat-icon" />
          {{ summaryStats.deleted }}
        </span>
      </div>
    </div>

    <div class="file-list">
      <TransitionGroup name="file-list">
        <div
          v-for="op in internalOperations"
          :key="op.path"
          :class="[
            'file-item', 
            op.action, 
            { selected: selectedFile === op.path }
          ]"
          @click="selectFile(op)"
          @dblclick="handleDoubleClick(op)"
        >
          <div class="file-main">
            <div
              class="file-icon-wrapper"
              :style="{ color: getActionColor(op.action) }"
            >
              <component
                :is="getActionIcon(op.action)"
                class="action-icon"
              />
            </div>
            <div class="file-info">
              <span class="file-path">{{ op.path }}</span>
              <div class="file-meta">
                <span
                  class="action-label"
                  :style="{ color: getActionColor(op.action) }"
                >
                  {{ getActionLabel(op.action) }}
                </span>
                <span class="timestamp">{{ formatTime(op.timestamp) }}</span>
              </div>
            </div>
          </div>
          
          <!-- Diff Stats -->
          <div
            v-if="hasDiffStats(op)"
            class="diff-stats"
          >
            <span
              v-if="op.linesAdded"
              class="diff-added"
            >+{{ op.linesAdded }}</span>
            <span
              v-if="op.linesRemoved"
              class="diff-removed"
            >-{{ op.linesRemoved }}</span>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- Empty State -->
    <div
      v-if="internalOperations.length === 0"
      class="empty-state"
    >
      <FolderIcon class="empty-icon" />
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
  padding: 16px;
}

.tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  width: 18px;
  height: 18px;
  color: var(--vibe-color-active);
}

.tree-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.header-stats {
  display: flex;
  gap: 8px;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.stat-badge.created {
  background: rgba(0, 255, 136, 0.15);
  color: var(--vibe-color-success);
}

.stat-badge.modified {
  background: rgba(0, 217, 255, 0.15);
  color: var(--vibe-color-active);
}

.stat-badge.deleted {
  background: rgba(255, 59, 48, 0.15);
  color: var(--vibe-color-error);
}

.stat-icon {
  width: 12px;
  height: 12px;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-list::-webkit-scrollbar {
  width: 6px;
}

.file-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.file-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

/* File item */
.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(28, 28, 30, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 150ms ease-out;
}

.file-item:hover {
  background: rgba(28, 28, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.file-item.selected {
  background: rgba(0, 217, 255, 0.1);
  border-color: rgba(0, 217, 255, 0.3);
}

/* Action-specific styles with animation */
.file-item.created {
  animation: file-created 0.3s ease-out;
}

@keyframes file-created {
  0% {
    opacity: 0;
    transform: translateX(-10px);
  }
  100% {
    opacity: 1;
    transform: translateX(0);
  }
}

.file-item.deleted {
  position: relative;
}

.file-item.deleted .file-path {
  text-decoration: line-through;
  opacity: 0.6;
}

.file-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.file-icon-wrapper {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  flex-shrink: 0;
}

.action-icon {
  width: 16px;
  height: 16px;
}

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.file-path {
  color: #ffffff;
  font-size: 13px;
  font-family: 'SF Mono', 'Monaco', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.timestamp {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

/* Diff stats */
.diff-stats {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.diff-added {
  font-size: 12px;
  font-weight: 600;
  color: var(--vibe-color-success);
  font-family: 'SF Mono', monospace;
}

.diff-removed {
  font-size: 12px;
  font-weight: 600;
  color: var(--vibe-color-error);
  font-family: 'SF Mono', monospace;
}

/* Empty state */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.4);
  gap: 12px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  opacity: 0.3;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* List transition animations */
.file-list-enter-active,
.file-list-leave-active {
  transition: all 200ms ease-out;
}

.file-list-enter-from {
  opacity: 0;
  transform: translateX(-10px);
}

.file-list-leave-to {
  opacity: 0;
  transform: translateX(10px);
}

.file-list-move {
  transition: transform 200ms ease-out;
}
</style>
