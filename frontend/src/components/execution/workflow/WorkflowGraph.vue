<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface Props {
  sessionId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'node-click': [nodeId: string]
}>()

// Node types
interface Node {
  id: string
  type: 'manus' | 'coworker'
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
  label: string
  x: number
  y: number
  metadata?: {
    startTime?: number
    duration?: number
    output?: string
  }
}

// Edge types
interface Edge {
  id: string
  from: string
  to: string
  type: 'context' | 'result'
  active: boolean
}

// Mock data for Phase 1
const nodes = ref<Node[]>([
  { id: '1', type: 'manus', status: 'success', label: '搜索市场数据', x: 100, y: 100 },
  { id: '2', type: 'manus', status: 'success', label: '分析竞品', x: 300, y: 100 },
  { id: '3', type: 'coworker', status: 'active', label: '生成报告', x: 500, y: 100 },
  { id: '4', type: 'manus', status: 'inactive', label: '创建PPT', x: 700, y: 100 },
])

const edges = ref<Edge[]>([
  { id: 'e1', from: '1', to: '2', type: 'context', active: true },
  { id: 'e2', from: '2', to: '3', type: 'context', active: true },
  { id: 'e3', from: '3', to: '4', type: 'result', active: false },
])

const selectedNodeId = ref<string | null>(null)

function handleNodeClick(nodeId: string) {
  selectedNodeId.value = nodeId
  emit('node-click', nodeId)
}

function getNodeColor(status: Node['status']): string {
  const colors = {
    active: '#00D9FF',      // 青色脉冲
    success: '#00FF88',     // 绿色锁定
    pending: '#FFB800',     // 琥珀暂停
    error: '#FF3B30',       // 红色冲突
    inactive: '#8E8E93',    // 灰色待执行
  }
  return colors[status]
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
  <div class="workflow-graph">
    <!-- Toolbar -->
    <div class="graph-toolbar">
      <button class="btn-icon" title="缩小">
        <span>🔍-</span>
      </button>
      <button class="btn-icon" title="放大">
        <span>🔍+</span>
      </button>
      <button class="btn-icon" title="适应屏幕">
        <span>⛶</span>
      </button>
      <button class="btn-icon" title="重置视图">
        <span>↻</span>
      </button>
    </div>

    <!-- Canvas Area (Phase 1: Simple SVG mock) -->
    <svg class="graph-canvas" width="100%" height="100%">
      <!-- Draw edges -->
      <g class="edges">
        <line
          v-for="edge in edges"
          :key="edge.id"
          :x1="nodes.find(n => n.id === edge.from)?.x"
          :y1="nodes.find(n => n.id === edge.from)?.y"
          :x2="nodes.find(n => n.id === edge.to)?.x"
          :y2="nodes.find(n => n.id === edge.to)?.y"
          :class="['edge', { active: edge.active }]"
          stroke="rgba(255, 255, 255, 0.3)"
          stroke-width="2"
        />
      </g>

      <!-- Draw nodes -->
      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          :transform="`translate(${node.x}, ${node.y})`"
          :class="['node', node.status, { selected: selectedNodeId === node.id }]"
          @click="handleNodeClick(node.id)"
        >
          <!-- Node circle -->
          <circle
            r="30"
            :fill="getNodeColor(node.status)"
            :class="{ 'pulse': node.status === 'active' }"
          />
          
          <!-- Node label -->
          <text
            y="55"
            text-anchor="middle"
            class="node-label"
          >
            {{ node.label }}
          </text>
        </g>
      </g>
    </svg>

    <!-- Legend -->
    <div class="graph-legend">
      <div class="legend-item">
        <span class="legend-dot active"></span>
        <span>执行中</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot success"></span>
        <span>已完成</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot pending"></span>
        <span>等待确认</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot error"></span>
        <span>执行失败</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.workflow-graph {
  width: 100%;
  height: 100%;
  position: relative;
  background: var(--bg-primary, rgba(18, 18, 18, 0.95));
  display: flex;
  flex-direction: column;
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
  border: 1px solid var(--divider-color);
  border-radius: 6px;
  background: rgba(28, 28, 30, 0.8);
  backdrop-filter: blur(10px);
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 120ms ease-out;
}

.btn-icon:hover {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--color-node-active);
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
}

.edge.active {
  stroke: rgba(0, 217, 255, 0.8);
  stroke-dasharray: 10 5;
  animation: flow-energy 1s linear infinite;
}

@keyframes flow-energy {
  0% {
    stroke-dashoffset: 15;
  }
  100% {
    stroke-dashoffset: 0;
  }
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
  filter: drop-shadow(0 0 10px currentColor);
  transition: all 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.node.selected circle {
  stroke: #ffffff;
  stroke-width: 3;
}

/* Pulse animation for active nodes */
.node circle.pulse {
  animation: pulse-breath 1.5s ease-in-out infinite;
}

@keyframes pulse-breath {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
  }
}

.node-label {
  fill: var(--text-primary);
  font-size: 12px;
  font-weight: 500;
  pointer-events: none;
}

/* Legend */
.graph-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(28, 28, 30, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  border: 1px solid var(--divider-color);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.active {
  background: #00D9FF;
}

.legend-dot.success {
  background: #00FF88;
}

.legend-dot.pending {
  background: #FFB800;
}

.legend-dot.error {
  background: #FF3B30;
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
