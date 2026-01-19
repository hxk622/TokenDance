<template>
  <div
    ref="containerRef"
    class="workflow-graph"
  >
    <svg
      ref="svgRef"
      class="graph-svg"
    />
    
    <!-- Node Tooltip -->
    <NodeTooltip
      :visible="tooltipState.visible"
      :node-id="tooltipState.nodeId"
      :status="tooltipState.status"
      :label="tooltipState.label"
      :x="tooltipState.x"
      :y="tooltipState.y"
      :metadata="tooltipState.metadata"
      :dependencies="tooltipState.dependencies"
    />
    
    <!-- Node Context Menu -->
    <NodeContextMenu
      :visible="contextMenuState.visible"
      :node="contextMenuState.node"
      :x="contextMenuState.x"
      :y="contextMenuState.y"
      @close="closeContextMenu"
      @rerun="handleNodeRerun"
      @view-logs="handleViewLogs"
      @copy-output="handleCopyOutput"
      @skip="handleNodeSkip"
      @pause="handleNodePause"
      @resume="handleNodeResume"
    />
    
    <!-- Node Hover Controls (mini-buttons) -->
    <NodeHoverControls
      :visible="tooltipState.visible"
      :node-id="tooltipState.nodeId"
      :status="tooltipState.status"
      :x="tooltipState.x"
      :y="tooltipState.y"
      @pause="handleNodePause"
      @resume="handleNodeResume"
      @skip="handleNodeSkip"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import * as d3 from 'd3'
import { useExecutionStore } from '@/stores/execution'
import NodeTooltip from './workflow/NodeTooltip.vue'
import NodeContextMenu from './workflow/NodeContextMenu.vue'
import NodeHoverControls from './workflow/NodeHoverControls.vue'

interface Props {
  sessionId: string
}

interface Emits {
  (e: 'node-click', nodeId: string): void
  (e: 'node-double-click', nodeId: string): void
  (e: 'node-pause', nodeId: string): void
  (e: 'node-resume', nodeId: string): void
  (e: 'node-skip', nodeId: string): void
  (e: 'node-rerun', nodeId: string): void
  (e: 'view-logs', nodeId: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

// Use Pinia store
const executionStore = useExecutionStore()

const containerRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

// Tooltip state
const tooltipState = ref({
  visible: false,
  nodeId: '',
  status: 'pending' as 'pending' | 'running' | 'success' | 'error',
  label: '',
  x: 0,
  y: 0,
  dependencies: [] as string[],
  metadata: undefined as { startTime?: number; endTime?: number; duration?: number; output?: string; errorMessage?: string } | undefined
})

// Context menu state
const contextMenuState = ref({
  visible: false,
  node: null as { id: string; status: 'pending' | 'running' | 'success' | 'error'; label: string } | null,
  x: 0,
  y: 0
})

// Use nodes and edges from store
const nodes = computed(() => executionStore.nodes.map(n => ({
  id: n.id,
  label: n.label,
  type: n.type,
  status: n.status,
  x: n.x,
  y: n.y,
})))

const edges = computed(() => executionStore.edges.map(e => ({
  source: e.from,
  target: e.to,
  type: e.type,
})))

let simulation: d3.Simulation<d3.SimulationNodeDatum, undefined> | null = null

// Watch for node status changes to update graph
watch(
  () => executionStore.nodes.map(n => n.status).join(','),
  () => {
    updateNodeStyles()
  }
)

onMounted(() => {
  renderGraph()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (simulation) {
    simulation.stop()
  }
  window.removeEventListener('resize', handleResize)
})

function renderGraph() {
  if (!svgRef.value || !containerRef.value) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  // Clear previous content
  d3.select(svgRef.value).selectAll('*').remove()

  const svg = d3.select(svgRef.value)
    .attr('width', width)
    .attr('height', height)

  // Create defs for all effects
  const defs = svg.append('defs')
  
  // Define arrow markers for edges
  defs.selectAll('marker')
    .data(['context', 'result'])
    .enter().append('marker')
    .attr('id', d => `arrow-${d}`)
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', d => d === 'context' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 217, 255, 0.8)')

  // Add glow filter for active nodes
  const filter = defs.append('filter')
    .attr('id', 'glow')
  filter.append('feGaussianBlur')
    .attr('stdDeviation', '4')
    .attr('result', 'coloredBlur')
  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

  // 定义渐变色用于流光效果
  const energyGradient = defs.append('linearGradient')
    .attr('id', 'energy-gradient')
    .attr('gradientUnits', 'userSpaceOnUse')
  energyGradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#00D9FF')
    .attr('stop-opacity', 0.2)
  energyGradient.append('stop')
    .attr('offset', '50%')
    .attr('stop-color', '#00D9FF')
    .attr('stop-opacity', 1)
  energyGradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#00FF88')
    .attr('stop-opacity', 0.2)

  // Create force simulation
  simulation = d3.forceSimulation(nodes.value as any)
    .force('link', d3.forceLink(edges.value)
      .id((d: any) => d.id)
      .distance(150))
    .force('charge', d3.forceManyBody().strength(-300))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(50))

  // Draw edges
  const link = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(edges.value)
    .enter().append('line')
    .attr('class', d => `edge ${d.type === 'result' ? 'edge-active' : ''}`)
    .attr('stroke', d => d.type === 'context' ? 'rgba(255, 255, 255, 0.3)' : 'url(#energy-gradient)')
    .attr('stroke-width', 2)
    .attr('stroke-dasharray', d => d.type === 'result' ? '10 5' : 'none')
    .attr('marker-end', d => `url(#arrow-${d.type})`)

  // Draw nodes
  const node = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes.value)
    .enter().append('g')
    .attr('class', 'node-group')
    .on('click', (event, d) => {
      event.stopPropagation()
      emit('node-click', d.id)
    })
    .on('dblclick', (event, d) => {
      event.stopPropagation()
      emit('node-double-click', d.id)
    })
    .on('mouseenter', (event, d: any) => {
      showTooltip(event, d)
    })
    .on('mouseleave', () => {
      hideTooltip()
    })
    .on('contextmenu', (event, d: any) => {
      event.preventDefault()
      showContextMenu(event, d)
    })

  // Node circles - Different shapes based on type
  node.each(function(d: any) {
    const nodeGroup = d3.select(this)

    if (d.type === 'manus') {
      // Manus: 六边形 (Hexagon) - 代表"智能大脑"
      const hexagonPath = d3.path()
      const size = 38
      for (let i = 0; i < 6; i++) {
        const angle = (i * 60 - 30) * Math.PI / 180
        const x = size * Math.cos(angle)
        const y = size * Math.sin(angle)
        if (i === 0) hexagonPath.moveTo(x, y)
        else hexagonPath.lineTo(x, y)
      }
      hexagonPath.closePath()

      nodeGroup.append('path')
        .attr('d', hexagonPath.toString())
        .attr('class', `node-shape status-${d.status}`)
        .attr('fill', getNodeColor(d.status))
        .attr('stroke', getNodeColor(d.status))
        .attr('stroke-width', 3)
        .attr('filter', d.status === 'active' ? 'url(#glow)' : 'none')

      // Manus icon (brain/cpu)
      nodeGroup.append('text')
        .attr('class', 'node-icon')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('fill', d.status === 'active' ? '#000' : '#fff')
        .attr('font-size', '18px')
        .text('⚡')

    } else if (d.type === 'coworker') {
      // Coworker: 圆角方形 (Rounded Square) - 代表"执行双手"
      nodeGroup.append('rect')
        .attr('x', -32)
        .attr('y', -32)
        .attr('width', 64)
        .attr('height', 64)
        .attr('rx', 12)
        .attr('ry', 12)
        .attr('class', `node-shape status-${d.status}`)
        .attr('fill', getNodeColor(d.status))
        .attr('stroke', getNodeColor(d.status))
        .attr('stroke-width', 3)
        .attr('filter', d.status === 'active' ? 'url(#glow)' : 'none')

      // Coworker icon (folder/file)
      nodeGroup.append('text')
        .attr('class', 'node-icon')
        .attr('text-anchor', 'middle')
        .attr('dy', '.35em')
        .attr('fill', d.status === 'active' ? '#000' : '#fff')
        .attr('font-size', '18px')
        .text('📁')

    } else {
      // Default: 圆形
      nodeGroup.append('circle')
        .attr('r', 40)
        .attr('class', `node-shape status-${d.status}`)
        .attr('fill', getNodeColor(d.status))
        .attr('stroke', getNodeColor(d.status))
        .attr('stroke-width', 3)
        .attr('filter', d.status === 'active' ? 'url(#glow)' : 'none')
    }
  })

  // Node labels
  node.append('text')
    .attr('class', 'node-label')
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .attr('fill', d => d.status === 'inactive' ? '#fff' : '#000')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .text(d => d.label)


  // Update positions on simulation tick
  simulation!.on('tick', () => {
    link
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)

    node.attr('transform', (d: any) => `translate(${d.x},${d.y})`)
  })
}

function getNodeColor(status: string): string {
  const colors: Record<string, string> = {
    active: '#00D9FF',
    success: '#00FF88',
    pending: '#FFB800',
    error: '#FF3B30',
    inactive: '#8E8E93',
  }
  return colors[status] || colors.inactive
}

function handleResize() {
  renderGraph()
}

// Update node visual styles without re-rendering entire graph
function updateNodeStyles() {
  if (!svgRef.value) return

  const svg = d3.select(svgRef.value)

  svg.selectAll('.node-shape')
    .data(nodes.value)
    .attr('fill', (d: any) => getNodeColor(d.status))
    .attr('stroke', (d: any) => getNodeColor(d.status))
    .attr('filter', (d: any) => d.status === 'active' ? 'url(#glow)' : 'none')
    .attr('class', (d: any) => `node-shape status-${d.status}`)
}

// Tooltip functions
function showTooltip(event: MouseEvent, d: any) {
  const storeNode = executionStore.nodes.find(n => n.id === d.id)
  // 将旧状态映射到新状态
  const statusMap: Record<string, 'pending' | 'running' | 'success' | 'error'> = {
    'active': 'running',
    'inactive': 'pending',
    'pending': 'pending',
    'running': 'running',
    'success': 'success',
    'error': 'error'
  }
  tooltipState.value = {
    visible: true,
    nodeId: d.id,
    status: statusMap[d.status] || 'pending',
    label: d.label,
    x: event.clientX,
    y: event.clientY,
    dependencies: (storeNode as any)?.dependencies || [],
    metadata: storeNode?.metadata
  }
}

function hideTooltip() {
  tooltipState.value.visible = false
}

// Context menu functions
function showContextMenu(event: MouseEvent, d: any) {
  // 将旧状态映射到新状态
  const statusMap: Record<string, 'pending' | 'running' | 'success' | 'error'> = {
    'active': 'running',
    'inactive': 'pending',
    'pending': 'pending',
    'running': 'running',
    'success': 'success',
    'error': 'error'
  }
  contextMenuState.value = {
    visible: true,
    node: {
      id: d.id,
      status: statusMap[d.status] || 'pending',
      label: d.label
    },
    x: event.clientX,
    y: event.clientY
  }
}

function closeContextMenu() {
  contextMenuState.value.visible = false
}

// Node action handlers
function handleNodePause(nodeId: string) {
  emit('node-pause', nodeId)
}

function handleNodeResume(nodeId: string) {
  emit('node-resume', nodeId)
}

function handleNodeSkip(nodeId: string) {
  emit('node-skip', nodeId)
}

function handleNodeRerun(nodeId: string) {
  emit('node-rerun', nodeId)
}

function handleViewLogs(nodeId: string) {
  emit('view-logs', nodeId)
}

function handleCopyOutput(nodeId: string) {
  const node = executionStore.nodes.find(n => n.id === nodeId)
  if (node?.metadata?.output) {
    navigator.clipboard.writeText(node.metadata.output)
  }
}
</script>

<style scoped>
.workflow-graph {
  width: 100%;
  height: 100%;
  background: rgba(28, 28, 30, 0.5);
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
}

/* D3 node styles */
:deep(.node-group) {
  cursor: pointer;
  transition: all 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

:deep(.node-group:hover) {
  transform: scale(1.1);
}

:deep(.node-shape.status-active) {
  animation: pulse-breath 1.5s ease-in-out infinite;
}

:deep(.node-icon) {
  pointer-events: none;
}

:deep(.edge) {
  transition: stroke 200ms ease-out;
}

:deep(.edge-active) {
  animation: flow-energy 1s linear infinite;
}

:deep(.edge:hover) {
  stroke-width: 3 !important;
}

/* Manus hexagon specific animation */
:deep(.node-shape.status-active[d]) {
  animation: hexagon-pulse 1.5s ease-in-out infinite;
}

@keyframes hexagon-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

/* Coworker rect specific animation */
:deep(rect.node-shape.status-active) {
  animation: rect-pulse 1.5s ease-in-out infinite;
}

@keyframes rect-pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.03);
    opacity: 0.9;
  }
}

@keyframes flow-energy {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -30;
  }
}

@keyframes pulse-breath {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.85;
  }
}
</style>
