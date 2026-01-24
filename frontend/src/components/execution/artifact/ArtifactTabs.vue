<script setup lang="ts">
import { ref, computed, type Component, markRaw } from 'vue'
import { 
  FileText, BarChart3, Image, GitCompare, Pin,
  Globe, FileType, LineChart, Code2, Table2, 
  Video, AudioLines, History
} from 'lucide-vue-next'

// Extended TabType to support all Manus-like artifact types
export type TabType = 
  | 'report'      // 研究报告
  | 'ppt'         // PPT
  | 'file-diff'   // 文件变更
  | 'image'       // 图像
  | 'sandbox'     // 沙盒浏览器
  | 'pdf'         // PDF
  | 'chart'       // 图表
  | 'code'        // 代码
  | 'table'       // 数据表格
  | 'video'       // 视频
  | 'audio'       // 音频
  | 'replay'      // 执行回放

interface Props {
  sessionId: string
  currentTab?: TabType
}

const props = withDefaults(defineProps<Props>(), {
  currentTab: 'report'
})

const emit = defineEmits<{
  (e: 'update:currentTab', value: TabType): void
  (e: 'tab-change', value: TabType): void
  (e: 'tabs-reordered', tabs: ArtifactTab[]): void
}>()

interface ArtifactTab {
  id: TabType
  type: TabType
  title: string
  icon: Component
  isPinned?: boolean
}

// All available tabs with their configurations
const allTabs: ArtifactTab[] = [
  // 最终产物
  { id: 'report', type: 'report', title: '研究报告', icon: markRaw(FileText) },
  { id: 'ppt', type: 'ppt', title: 'PPT', icon: markRaw(BarChart3) },
  { id: 'code', type: 'code', title: '代码', icon: markRaw(Code2) },
  { id: 'file-diff', type: 'file-diff', title: '文件变更', icon: markRaw(GitCompare) },
  // 可视化
  { id: 'chart', type: 'chart', title: '图表', icon: markRaw(LineChart) },
  { id: 'table', type: 'table', title: '数据表格', icon: markRaw(Table2) },
  // 多媒体
  { id: 'image', type: 'image', title: '图像', icon: markRaw(Image) },
  { id: 'video', type: 'video', title: '视频', icon: markRaw(Video) },
  { id: 'audio', type: 'audio', title: '音频', icon: markRaw(AudioLines) },
  // 工具
  { id: 'sandbox', type: 'sandbox', title: '实时预览', icon: markRaw(Globe) },
  { id: 'pdf', type: 'pdf', title: 'PDF', icon: markRaw(FileType) },
  { id: 'replay', type: 'replay', title: '执行回放', icon: markRaw(History) },
]

// Visible tabs (can be filtered by available artifacts)
const tabs = ref<ArtifactTab[]>(allTabs)

const current = computed({
  get: () => props.currentTab,
  set: (v: TabType) => emit('update:currentTab', v)
})

// Drag and Drop state
const draggedTab = ref<ArtifactTab | null>(null)
const dragOverIndex = ref<number | null>(null)

function switchTab(id: TabType) {
  if (current.value !== id) {
    current.value = id
    emit('tab-change', id)
  }
}

function togglePin(id: ArtifactTab['id']) {
  const t = tabs.value.find(t => t.id === id)
  if (t) t.isPinned = !t.isPinned
}

// Drag and Drop handlers
function handleDragStart(e: DragEvent, tab: ArtifactTab) {
  draggedTab.value = tab
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', tab.id)
  }
}

function handleDragOver(e: DragEvent, index: number) {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move'
  }
  dragOverIndex.value = index
}

function handleDragLeave() {
  dragOverIndex.value = null
}

function handleDrop(e: DragEvent, targetIndex: number) {
  e.preventDefault()
  
  if (!draggedTab.value) return
  
  const sourceIndex = tabs.value.findIndex(t => t.id === draggedTab.value!.id)
  if (sourceIndex === -1 || sourceIndex === targetIndex) {
    resetDragState()
    return
  }
  
  // Reorder tabs
  const [removed] = tabs.value.splice(sourceIndex, 1)
  tabs.value.splice(targetIndex, 0, removed)
  
  // Emit reorder event
  emit('tabs-reordered', [...tabs.value])
  
  resetDragState()
}

function handleDragEnd() {
  resetDragState()
}

function resetDragState() {
  draggedTab.value = null
  dragOverIndex.value = null
}
</script>

<template>
  <div class="artifact-tabs">
    <div
      v-for="(tab, index) in tabs"
      :key="tab.id"
      :class="[
        'tab',
        {
          active: current === tab.id,
          pinned: tab.isPinned,
          dragging: draggedTab?.id === tab.id,
          'drag-over': dragOverIndex === index && draggedTab?.id !== tab.id
        }
      ]"
      draggable="true"
      tabindex="0"
      role="tab"
      :aria-selected="current === tab.id"
      :aria-label="`${tab.title}标签页${tab.isPinned ? '，已固定' : ''}`"
      @click="switchTab(tab.id)"
      @keydown.enter="switchTab(tab.id)"
      @keydown.space.prevent="switchTab(tab.id)"
      @contextmenu.prevent="togglePin(tab.id)"
      @dragstart="handleDragStart($event, tab)"
      @dragover="handleDragOver($event, index)"
      @dragleave="handleDragLeave"
      @drop="handleDrop($event, index)"
      @dragend="handleDragEnd"
    >
      <span
        class="drag-handle"
        aria-hidden="true"
      >⋮⋮</span>
      <component
        :is="tab.icon"
        class="icon w-4 h-4"
        aria-hidden="true"
      />
      <span class="title">{{ tab.title }}</span>
      <Pin
        v-if="tab.isPinned"
        class="pin w-3 h-3"
        aria-hidden="true"
      />
    </div>
  </div>
</template>

<style scoped>
.artifact-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 12px 0 12px;
  border-bottom: 1px solid var(--divider-color);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(28, 28, 30, 0.8);
  border: 1px solid var(--divider-color);
  border-radius: 6px 6px 0 0;
  cursor: grab;
  color: var(--text-secondary);
  transition: all 150ms ease-out;
  user-select: none;
}

.tab:active {
  cursor: grabbing;
}

.tab.active {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--color-node-active);
  color: var(--color-node-active);
}

.tab.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.tab.drag-over {
  border-color: var(--color-node-active);
  background: rgba(0, 217, 255, 0.1);
  transform: translateX(4px);
}

/* Accessibility: Focus styles */
.tab:focus-visible {
  outline: 2px solid var(--color-node-active);
  outline-offset: 2px;
}

.drag-handle {
  font-size: 10px;
  color: var(--text-secondary);
  opacity: 0.5;
  letter-spacing: 1px;
  cursor: grab;
}

.tab:hover .drag-handle {
  opacity: 1;
}

.pin {
  margin-left: 4px;
}

:root {
  --divider-color: rgba(255, 255, 255, 0.1);
  --color-node-active: #00D9FF;
  --text-secondary: rgba(255, 255, 255, 0.6);
}
</style>
