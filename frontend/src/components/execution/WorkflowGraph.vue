<template>
  <div class="workflow-graph" ref="containerRef">
    <svg ref="svgRef" class="graph-svg"></svg>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import * as d3 from 'd3'
import { useExecutionStore } from '@/stores/execution'

interface Props {
  sessionId: string
}

interface Emits {
  (e: 'node-click', nodeId: string): void
  (e: 'node-double-click', nodeId: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

// Use Pinia store
const executionStore = useExecutionStore()

const containerRef = ref<HTMLElement | null>(null)
const svgRef = ref<SVGSVGElement | null>(null)

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

  // Define arrow markers for edges
  svg.append('defs').selectAll('marker')
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
    .attr('class', 'edge')
    .attr('stroke', d => d.type === 'context' ? 'rgba(255, 255, 255, 0.3)' : 'rgba(0, 217, 255, 0.8)')
    .attr('stroke-width', 2)
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

  // Node circles
  node.append('circle')
    .attr('r', 40)
    .attr('class', d => `node-circle status-${d.status}`)
    .attr('fill', d => getNodeColor(d.status))
    .attr('stroke', d => getNodeColor(d.status))
    .attr('stroke-width', 3)
    .attr('filter', d => d.status === 'active' ? 'url(#glow)' : 'none')

  // Node labels
  node.append('text')
    .attr('class', 'node-label')
    .attr('text-anchor', 'middle')
    .attr('dy', '.35em')
    .attr('fill', d => d.status === 'inactive' ? '#fff' : '#000')
    .attr('font-size', '12px')
    .attr('font-weight', '600')
    .text(d => d.label)

  // Add glow filter for active nodes
  const defs = svg.select('defs')
  const filter = defs.append('filter')
    .attr('id', 'glow')
  filter.append('feGaussianBlur')
    .attr('stdDeviation', '4')
    .attr('result', 'coloredBlur')
  const feMerge = filter.append('feMerge')
  feMerge.append('feMergeNode').attr('in', 'coloredBlur')
  feMerge.append('feMergeNode').attr('in', 'SourceGraphic')

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
  
  svg.selectAll('.node-circle')
    .data(nodes.value)
    .attr('fill', (d: any) => getNodeColor(d.status))
    .attr('stroke', (d: any) => getNodeColor(d.status))
    .attr('filter', (d: any) => d.status === 'active' ? 'url(#glow)' : 'none')
    .attr('class', (d: any) => `node-circle status-${d.status}`)
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

:deep(.node-circle.status-active) {
  animation: pulse-breath 1.5s ease-in-out infinite;
}

:deep(.edge) {
  transition: stroke 200ms ease-out;
}

:deep(.edge:hover) {
  stroke-width: 3 !important;
}

@keyframes pulse-breath {
  0%, 100% {
    r: 40;
    opacity: 1;
  }
  50% {
    r: 44;
    opacity: 0.9;
  }
}
</style>
