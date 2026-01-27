<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-vue-next'
import NodeTooltip from './NodeTooltip.vue'
import { useWorkflowStore } from '@/stores/workflow'
import { storeToRefs } from 'pinia'

interface Props {
  sessionId: string
  miniMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  miniMode: false
})
const emit = defineEmits<{
  'node-click': [nodeId: string]
  'node-double-click': [nodeId: string]
  'node-rerun': [nodeId: string]
  'node-view-logs': [nodeId: string]
  'edge-disconnect': [edgeId: string]
}>()

// 使用 workflowStore 获取真实数据
const workflowStore = useWorkflowStore()
const { nodes: storeNodes, edges: storeEdges, isLoaded } = storeToRefs(workflowStore)

// Node interface - 节点只区分状态，不区分类型
interface Node {
  id: string
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  label: string  // 任务名称
  x: number
  y: number
  dependencies?: string[]  // 上游依赖节点 ID 列表
  metadata?: {
    startTime?: number
    endTime?: number
    duration?: number
    output?: string
    errorMessage?: string
  }
}

// Edge interface - 依赖关系连线
interface Edge {
  id: string
  from: string  // 上游节点 ID
  to: string    // 下游节点 ID
}

// 从 workflowStore 获取数据，如果没有数据则显示空状态
const nodes = computed<Node[]>(() => {
  if (storeNodes.value.length > 0) {
    return storeNodes.value.map(n => ({
      id: n.id,
      status: n.status,
      label: n.label,
      x: n.x,
      y: n.y,
      dependencies: n.dependencies,
      metadata: n.metadata,
    }))
  }
  // 没有 Plan 时返回空数组，显示空状态
  return []
})

// 边从 workflowStore 获取
const edges = computed<Edge[]>(() => {
  return storeEdges.value.map(e => ({
    id: e.id,
    from: e.from,
    to: e.to,
  }))
})

const selectedNodeId = ref<string | null>(null)

// Loading 状态基于 workflowStore
const isLoading = computed(() => !isLoaded.value && nodes.value.length === 0)

// Tooltip state
const tooltipVisible = ref(false)
const hoveredNode = ref<Node | null>(null)
const tooltipPosition = ref({ x: 0, y: 0 })

// Context Menu state
const contextMenuVisible = ref(false)
const contextMenuNode = ref<Node | null>(null)
const contextMenuPosition = ref({ x: 0, y: 0 })

// Edge interaction state
const draggingEdge = ref<string | null>(null)
const dragStartPos = ref({ x: 0, y: 0 })
const dragCurrentPos = ref({ x: 0, y: 0 })

function handleNodeClick(nodeId: string) {
  selectedNodeId.value = nodeId
  emit('node-click', nodeId)
}

function handleNodeDoubleClick(nodeId: string) {
  emit('node-double-click', nodeId)
}


function handleNodeHover(node: Node, event: MouseEvent) {
  tooltipVisible.value = true
  hoveredNode.value = node
  tooltipPosition.value = { x: event.clientX, y: event.clientY }
}

function handleNodeLeave() {
  tooltipVisible.value = false
  hoveredNode.value = null
}

// Context Menu handlers
function handleContextMenu(node: Node, event: MouseEvent) {
  event.preventDefault()
  contextMenuVisible.value = true
  contextMenuNode.value = node
  contextMenuPosition.value = { x: event.clientX, y: event.clientY }
}

function closeContextMenu() {
  contextMenuVisible.value = false
  contextMenuNode.value = null
}

function handleRerunNode() {
  if (contextMenuNode.value) {
    emit('node-rerun', contextMenuNode.value.id)
    console.log('Rerun node:', contextMenuNode.value.id)
  }
  closeContextMenu()
}

function handleViewLogs() {
  if (contextMenuNode.value) {
    emit('node-view-logs', contextMenuNode.value.id)
    console.log('View logs for node:', contextMenuNode.value.id)
  }
  closeContextMenu()
}

function handleCopyOutput() {
  if (contextMenuNode.value?.metadata?.output) {
    navigator.clipboard.writeText(contextMenuNode.value.metadata.output)
    console.log('Output copied to clipboard')
  }
  closeContextMenu()
}

// Edge interaction handlers
function handleEdgeDoubleClick(edge: Edge) {
  // Double-click to disconnect edge
  const index = edges.value.findIndex(e => e.id === edge.id)
  if (index !== -1) {
    edges.value.splice(index, 1)
    emit('edge-disconnect', edge.id)
    console.log('Disconnected edge:', edge.id)
  }
}

function handleEdgeMouseDown(edge: Edge, event: MouseEvent) {
  // Start dragging edge for reconnection
  event.stopPropagation()
  draggingEdge.value = edge.id
  dragStartPos.value = { x: event.clientX, y: event.clientY }
  dragCurrentPos.value = { x: event.clientX, y: event.clientY }
  
  document.addEventListener('mousemove', handleEdgeDrag)
  document.addEventListener('mouseup', handleEdgeDragEnd)
}

function handleEdgeDrag(event: MouseEvent) {
  if (!draggingEdge.value) return
  dragCurrentPos.value = { x: event.clientX, y: event.clientY }
}

function handleEdgeDragEnd(event: MouseEvent) {
  if (!draggingEdge.value) return
  
  // Find if dropped on a node
  const target = document.elementFromPoint(event.clientX, event.clientY)
  const nodeElement = target?.closest('[data-node-id]')
  
  if (nodeElement) {
    const targetNodeId = nodeElement.getAttribute('data-node-id')
    const edge = edges.value.find(e => e.id === draggingEdge.value)
    
    if (edge && targetNodeId && targetNodeId !== edge.from) {
      // Reconnect edge to new target
      edge.to = targetNodeId
      console.log('Reconnected edge', edge.id, 'to node', targetNodeId)
    }
  }
  
  draggingEdge.value = null
  document.removeEventListener('mousemove', handleEdgeDrag)
  document.removeEventListener('mouseup', handleEdgeDragEnd)
}

// Close context menu on click outside
function handleCanvasClick() {
  if (contextMenuVisible.value) {
    closeContextMenu()
  }
}

// 根据状态返回节点颜色
function getNodeColor(status: Node['status']): string {
  const colors: Record<Node['status'], string> = {
    pending: 'var(--any-text-tertiary)',
    running: 'var(--exec-warning)',
    success: 'var(--exec-success)',
    error: 'var(--exec-error)',
    skipped: 'var(--any-text-muted)',
  }
  return colors[status]
}

const completedCount = computed(() => nodes.value.filter(n => n.status === 'success').length)

// 根据上游节点状态判断边是否激活（用于动画效果）
function isEdgeActive(edge: Edge): boolean {
  const fromNode = nodes.value.find(n => n.id === edge.from)
  const toNode = nodes.value.find(n => n.id === edge.to)
  // 当上游完成且下游正在执行时，边激活
  return fromNode?.status === 'success' && toNode?.status === 'running'
}

// 计算箭头指向的三角形顶点
function getArrowPoints(edge: Edge): string {
  const fromNode = nodes.value.find(n => n.id === edge.from)
  const toNode = nodes.value.find(n => n.id === edge.to)
  if (!fromNode || !toNode) return ''
  
  const dx = toNode.x - fromNode.x
  const dy = toNode.y - fromNode.y
  const len = Math.sqrt(dx * dx + dy * dy)
  if (len === 0) return ''
  
  // 单位向量
  const ux = dx / len
  const uy = dy / len
  
  // 箭头尖端位置（距离目标节点圆心 35px，因为节点半径 30）
  const tipX = toNode.x - ux * 35
  const tipY = toNode.y - uy * 35
  
  // 箭头两侧的点
  const arrowSize = 8
  const perpX = -uy * arrowSize
  const perpY = ux * arrowSize
  const backX = tipX - ux * arrowSize * 1.5
  const backY = tipY - uy * arrowSize * 1.5
  
  return `${tipX},${tipY} ${backX + perpX},${backY + perpY} ${backX - perpX},${backY - perpY}`
}

onMounted(() => {
  // TODO: Initialize canvas or vis-network
  console.log('WorkflowGraph mounted for session:', props.sessionId)
})

watch(() => props.sessionId, (newId) => {
  console.log('Session changed:', newId)
  // TODO: Reload graph data
})
</script>

<template>
  <div
    class="workflow-graph"
    :class="{ 'mini-mode': miniMode }"
  >
    <!-- Toolbar -->
    <div class="graph-toolbar">
      <button
        class="btn-icon"
        title="缩小"
      >
        <ZoomOut class="w-4 h-4" />
      </button>
      <button
        class="btn-icon"
        title="放大"
      >
        <ZoomIn class="w-4 h-4" />
      </button>
      <button
        class="btn-icon"
        title="适应屏幕"
      >
        <Maximize2 class="w-4 h-4" />
      </button>
      <button
        class="btn-icon"
        title="重置视图"
      >
        <RefreshCw class="w-4 h-4" />
      </button>
    </div>

    <!-- Loading Skeleton -->
    <div
      v-if="isLoading"
      class="graph-skeleton"
    >
      <div
        v-for="i in 4"
        :key="i"
        class="skeleton-node"
      >
        <div class="skeleton-circle" />
        <div class="skeleton-label" />
      </div>
      <div class="skeleton-shimmer" />
    </div>

    <!-- Mini Graph (Collapsed Mode or Mini Mode) -->
    <div
      v-else-if="miniMode"
      class="mini-graph"
    >
      <div class="mini-summary">
        <span class="mini-title">执行概览</span>
        <span class="mini-meta">{{ completedCount }}/{{ nodes.length }} 已完成</span>
      </div>
      <div
        v-if="nodes.length > 0"
        class="mini-nodes"
      >
        <div 
          v-for="node in nodes" 
          :key="node.id" 
          :class="['mini-node', node.status]"
          :style="{ background: getNodeColor(node.status) }"
          @click="handleNodeClick(node.id)"
        >
          <span
            v-if="node.status === 'running'"
            class="mini-node-pulse"
          />
        </div>
      </div>
      <div
        v-else
        class="mini-empty"
      >
        暂无执行节点
      </div>
    </div>

    <!-- Canvas Area (Normal Mode) -->
    <svg
      v-else
      class="graph-canvas"
      width="100%"
      height="100%"
      @click="handleCanvasClick"
    >
      <!-- Draw edges (依赖关系连线) -->
      <g class="edges">
        <g
          v-for="edge in edges"
          :key="edge.id"
          class="edge-group"
        >
          <!-- 依赖连线 -->
          <line
            :x1="nodes.find(n => n.id === edge.from)?.x"
            :y1="nodes.find(n => n.id === edge.from)?.y"
            :x2="nodes.find(n => n.id === edge.to)?.x"
            :y2="nodes.find(n => n.id === edge.to)?.y"
            :class="['edge', { active: isEdgeActive(edge) }]"
            stroke-width="2"
          />
          <!-- 箭头标记 -->
          <polygon
            v-if="nodes.find(n => n.id === edge.to)"
            :points="getArrowPoints(edge)"
            :class="['edge-arrow', { active: isEdgeActive(edge) }]"
          />
        </g>
      </g>

      <!-- Draw nodes (任务节点) -->
      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          :data-node-id="node.id"
          :transform="`translate(${node.x}, ${node.y})`"
          :class="['node', `status-${node.status}`, { selected: selectedNodeId === node.id }]"
          @click.stop="handleNodeClick(node.id)"
          @dblclick="handleNodeDoubleClick(node.id)"
          @contextmenu="handleContextMenu(node, $event)"
          @mouseenter="handleNodeHover(node, $event)"
          @mouseleave="handleNodeLeave"
        >
          <!-- Node circle -->
          <circle
            r="30"
            :fill="getNodeColor(node.status)"
            :class="{ 'pulse': node.status === 'running' }"
          />
          
          <!-- 任务名称标签 -->
          <text
            y="50"
            text-anchor="middle"
            class="node-label"
          >
            {{ node.label }}
          </text>
        </g>
      </g>
    </svg>

    <!-- Node Tooltip -->
    <NodeTooltip
      v-if="hoveredNode"
      :visible="tooltipVisible"
      :node-id="hoveredNode.id"
      :status="hoveredNode.status"
      :label="hoveredNode.label"
      :x="tooltipPosition.x"
      :y="tooltipPosition.y"
      :metadata="hoveredNode.metadata"
      :dependencies="hoveredNode.dependencies"
    />

    <!-- Context Menu -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="contextMenuVisible && contextMenuNode"
          class="context-menu"
          :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
        >
          <div
            class="context-menu-item"
            @click="handleRerunNode"
          >
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
              <polyline points="23 4 23 10 17 10" />
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
            </svg>
            <span>重新执行</span>
          </div>
          <div
            class="context-menu-item"
            @click="handleViewLogs"
          >
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
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line
                x1="16"
                y1="13"
                x2="8"
                y2="13"
              />
              <line
                x1="16"
                y1="17"
                x2="8"
                y2="17"
              />
            </svg>
            <span>查看日志</span>
          </div>
          <div
            class="context-menu-item"
            :class="{ disabled: !contextMenuNode.metadata?.output }"
            @click="handleCopyOutput"
          >
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
              <rect
                x="9"
                y="9"
                width="13"
                height="13"
                rx="2"
                ry="2"
              />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <span>复制输出</span>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Legend (状态图例) -->
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-dot pending" />
        <span>未执行</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot running" />
        <span>执行中</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot success" />
        <span>已完成</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot error" />
        <span>出错</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workflow-graph {
  width: 100%;
  height: 100%;
  position: relative;
  --exec-warning: var(--td-state-waiting, #FFB800);
  --exec-success: var(--td-state-executing, #00FF88);
  --exec-error: var(--td-state-error, #FF3B30);
  background: var(--any-bg-primary);  /* 统一为主背景色 */
  display: flex;
  flex-direction: column;
  border: 1px solid var(--any-border);
}

/* Toolbar */
.graph-toolbar {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  z-index: 100;
}

.btn-icon {
  width: 32px;
  height: 32px;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  background: var(--any-bg-secondary);
  color: var(--any-text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 120ms ease-out;
}

.btn-icon:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

/* Canvas */
.graph-canvas {
  flex: 1;
  cursor: grab;
}

.graph-canvas:active {
  cursor: grabbing;
}

/* Edges */
.edge {
  transition: stroke 200ms ease-out;
  stroke-linecap: round;
  stroke: var(--any-border);
}

.edge.active {
  stroke: var(--exec-warning);
  stroke-width: 2.5;
  stroke-dasharray: 6 4;
}

.edge-hitbox {
  cursor: pointer;
}

.edge-hitbox:hover + .edge {
  stroke: color-mix(in srgb, var(--exec-warning) 60%, transparent);
  stroke-width: 2.5;
}

.edge.dragging {
  stroke: color-mix(in srgb, var(--exec-warning) 60%, transparent);
  stroke-width: 2.5;
  stroke-dasharray: 6 4;
}
.edge-arrow {
  fill: var(--any-border);
}

.edge-arrow.active {
  fill: var(--exec-warning);
}

/* Nodes */
.node {
  cursor: pointer;
  transition: transform 200ms ease-out;
}

.node:hover {
  transform: scale(1.1);
}

.node circle {
  transition: transform 200ms ease-out, opacity 200ms ease-out;
}

.node.selected circle {
  stroke: var(--any-text-primary);
  stroke-width: 3;
}

/* Running node - 黄色脉冲呼吸动画 */
.node circle.pulse {
  animation: vibe-node-breath 1.6s ease-in-out infinite;
}

@keyframes vibe-node-breath {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.08);
    opacity: 0.9;
  }
}

/* Pending node - 灰色静态 */
.node.status-pending circle {
  opacity: 0.85;
}

/* Success node - 绿色光晕 */
.node.status-success circle {
  opacity: 0.95;
}

.node.status-success.just-completed circle {
  animation: vibe-node-success-pop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes vibe-node-success-pop {
  0% { transform: scale(1); }
  30% { transform: scale(1.25); }
  60% { transform: scale(0.95); }
  100% { transform: scale(1); }
}

/* Error node - 红色抖动 */
.node.status-error circle {
  animation: vibe-node-error 0.4s ease-in-out;
}

@keyframes vibe-node-error {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-3px); }
  40%, 80% { transform: translateX(3px); }
}

.node-label {
  fill: var(--any-text-primary);
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
}

/* Legend - Glass panel style */
.graph-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border-radius: 10px;
  border: 1px solid var(--any-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--any-text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.pending {
  background: var(--any-text-tertiary);
}

.legend-dot.running {
  background: var(--exec-warning);
}


.legend-dot.success {
  background: var(--exec-success);
}

.legend-dot.error {
  background: var(--exec-error);
}

/* Mini Mode */
.workflow-graph.mini-mode {
  height: 110px;
  min-height: 110px;
  transition: height 200ms ease-out;
}

.mini-graph {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 8px;
  height: 100%;
  padding: 16px;
}
.mini-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 12px;
}

.mini-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.mini-meta {
  font-size: 12px;
  color: var(--any-text-secondary);
}

.mini-nodes {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mini-empty {
  font-size: 12px;
  color: var(--any-text-muted);
}

.mini-node {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  transition: all 200ms ease-out;
  cursor: pointer;
  position: relative;
}

.mini-node:hover {
  transform: scale(1.15);
}

.mini-node.running {
  animation: vibe-mini-pulse 1.6s ease-in-out infinite;
}
@keyframes vibe-mini-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.9;
  }
  50% {
    transform: scale(1.08);
    opacity: 1;
  }
}

.mini-node-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid var(--exec-warning);
  animation: vibe-ring-expand 1.6s ease-out infinite;
}

@keyframes vibe-ring-expand {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  100% {
    transform: scale(1.6);
    opacity: 0;
  }
}

/* Second ring for layered effect */
.mini-node.active::after {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 1px solid var(--exec-warning);
  animation: vibe-ring-expand 1.6s ease-out infinite 0.3s;
}

/* Skeleton Loading */
.graph-skeleton {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 60px;
  position: relative;
  overflow: hidden;
}

.skeleton-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.skeleton-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(90deg, var(--any-bg-tertiary) 0%, var(--any-bg-hover) 50%, var(--any-bg-tertiary) 100%);
}

.skeleton-label {
  width: 80px;
  height: 12px;
  border-radius: 4px;
  background: linear-gradient(90deg, var(--any-bg-tertiary) 0%, var(--any-bg-hover) 50%, var(--any-bg-tertiary) 100%);
}

.skeleton-shimmer {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    color-mix(in srgb, var(--any-bg-hover) 40%, transparent) 50%,
    transparent 100%
  );
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 1000;
  min-width: 160px;
  background: var(--any-bg-secondary);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  padding: 6px 0;
  box-shadow: 0 8px 32px color-mix(in srgb, var(--any-bg-primary) 40%, transparent);
}

.context-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 13px;
  color: var(--any-text-primary);
  cursor: pointer;
  transition: all 120ms ease-out;
}

.context-menu-item:hover {
  background: var(--td-state-thinking-bg);
}

.context-menu-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.context-menu-item.disabled:hover {
  background: transparent;
}

.context-menu-item svg {
  flex-shrink: 0;
  color: var(--any-text-secondary);
}

.context-menu-item:hover svg {
  color: var(--td-state-thinking);
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
