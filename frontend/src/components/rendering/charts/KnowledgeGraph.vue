<script setup lang="ts">
/**
 * KnowledgeGraph - 知识图谱可视化组件
 * 
 * 使用 Cytoscape.js 渲染交互式知识图谱。
 * 支持：
 * - 多种布局算法（力导向、层次、圆形等）
 * - 节点/边的交互（点击、悬停、拖拽）
 * - 缩放和平移
 * - 节点高亮和聚焦
 * - 导出为图片
 */

import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import cytoscape, { type Core, type NodeSingular } from 'cytoscape'
import { 
  ArrowsPointingOutIcon, 
  ArrowDownTrayIcon,
  ArrowPathIcon,
  MagnifyingGlassMinusIcon,
  MagnifyingGlassPlusIcon,
  ViewfinderCircleIcon,
} from '@heroicons/vue/24/outline'

// Types
interface GraphNode {
  id: string
  label: string
  type?: 'concept' | 'source' | 'finding' | 'section' | 'entity' | 'event' | 'question'
  importance?: number
  color?: string
  description?: string
}

interface GraphEdge {
  source: string
  target: string
  label?: string
  type?: string
  strength?: number
  style?: 'solid' | 'dashed' | 'dotted'
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata?: {
    central_node?: string
    clusters?: string[]
    graph_type?: string
    title?: string
  }
}

// Props
interface Props {
  graph: GraphData
  title?: string
  height?: number | string
  layout?: 'cose' | 'circle' | 'breadthfirst' | 'concentric' | 'grid'
  showToolbar?: boolean
  showLegend?: boolean
  interactive?: boolean
  theme?: 'light' | 'dark' | 'auto'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  height: 500,
  layout: 'cose',
  showToolbar: true,
  showLegend: true,
  interactive: true,
  theme: 'auto',
})

// Emits
const emit = defineEmits<{
  (e: 'nodeClick', node: GraphNode): void
  (e: 'edgeClick', edge: GraphEdge): void
  (e: 'ready'): void
}>()

// Refs
const containerRef = ref<HTMLElement | null>(null)
const cy = ref<Core | null>(null)
const selectedNode = ref<GraphNode | null>(null)
const isLoading = ref(true)
const currentLayout = ref(props.layout)

// Layout options
const layoutOptions = {
  cose: {
    name: 'cose',
    animate: true,
    animationDuration: 500,
    nodeDimensionsIncludeLabels: true,
    nodeRepulsion: () => 8000,
    idealEdgeLength: () => 100,
    edgeElasticity: () => 100,
    gravity: 0.25,
    numIter: 1000,
  },
  circle: {
    name: 'circle',
    animate: true,
    animationDuration: 500,
    spacingFactor: 1.5,
  },
  breadthfirst: {
    name: 'breadthfirst',
    animate: true,
    animationDuration: 500,
    directed: true,
    spacingFactor: 1.5,
  },
  concentric: {
    name: 'concentric',
    animate: true,
    animationDuration: 500,
    levelWidth: () => 2,
    spacingFactor: 1.5,
  },
  grid: {
    name: 'grid',
    animate: true,
    animationDuration: 500,
    spacingFactor: 1.5,
  },
}

// Computed
const containerStyle = computed(() => ({
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
}))

const isDarkTheme = computed(() => {
  if (props.theme === 'dark') return true
  if (props.theme === 'light') return false
  // Auto: check document class
  return document.documentElement.classList.contains('dark')
})

// Node type colors (matching backend)
const nodeTypeColors: Record<string, string> = {
  concept: '#6366f1',   // 紫色
  source: '#10b981',    // 绿色
  finding: '#f59e0b',   // 橙色
  section: '#3b82f6',   // 蓝色
  entity: '#ec4899',    // 粉色
  event: '#ef4444',     // 红色
  question: '#8b5cf6',  // 紫罗兰
}

const nodeTypeLabels: Record<string, string> = {
  concept: '概念',
  source: '来源',
  finding: '发现',
  section: '章节',
  entity: '实体',
  event: '事件',
  question: '问题',
}

// Get used node types for legend
const usedNodeTypes = computed(() => {
  const types = new Set<string>()
  props.graph.nodes.forEach(node => {
    if (node.type) types.add(node.type)
  })
  return Array.from(types)
})

// Cytoscape stylesheet
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const getStylesheet = (): any[] => {
  const bgColor = isDarkTheme.value ? '#1a1a1a' : '#ffffff'
  const textColor = isDarkTheme.value ? '#e5e5e5' : '#374151'
  const edgeColor = isDarkTheme.value ? '#4b5563' : '#9ca3af'
  
  return [
    // Node style
    {
      selector: 'node',
      style: {
        'background-color': 'data(color)',
        'label': 'data(label)',
        'width': 'mapData(importance, 1, 10, 30, 60)',
        'height': 'mapData(importance, 1, 10, 30, 60)',
        'font-size': '12px',
        'color': textColor,
        'text-valign': 'bottom',
        'text-halign': 'center',
        'text-margin-y': 8,
        'text-outline-width': 2,
        'text-outline-color': bgColor,
        'border-width': 2,
        'border-color': bgColor,
        'transition-property': 'background-color, width, height, border-color',
        'transition-duration': '0.2s',
      }
    },
    // Node hover
    {
      selector: 'node:active',
      style: {
        'overlay-opacity': 0.1,
      }
    },
    // Selected node
    {
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': '#00D9FF',
      }
    },
    // Central node (if marked)
    {
      selector: 'node[?central]',
      style: {
        'border-width': 3,
        'border-color': '#00FF88',
      }
    },
    // Edge style
    {
      selector: 'edge',
      style: {
        'width': 'mapData(strength, 1, 10, 1, 4)',
        'line-color': edgeColor,
        'target-arrow-color': edgeColor,
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',
        'font-size': '10px',
        'color': textColor,
        'text-rotation': 'autorotate',
        'text-margin-y': -10,
        'text-outline-width': 2,
        'text-outline-color': bgColor,
        'opacity': 0.7,
        'transition-property': 'opacity, line-color',
        'transition-duration': '0.2s',
      }
    },
    // Dashed edge
    {
      selector: 'edge[style = "dashed"]',
      style: {
        'line-style': 'dashed',
      }
    },
    // Dotted edge
    {
      selector: 'edge[style = "dotted"]',
      style: {
        'line-style': 'dotted',
      }
    },
    // Edge hover
    {
      selector: 'edge:active',
      style: {
        'opacity': 1,
      }
    },
    // Highlighted elements (neighbors of selected)
    {
      selector: '.highlighted',
      style: {
        'opacity': 1,
      }
    },
    // Dimmed elements
    {
      selector: '.dimmed',
      style: {
        'opacity': 0.2,
      }
    },
  ]
}

// Convert graph data to Cytoscape format
const getCytoscapeElements = () => {
  const centralNodeId = props.graph.metadata?.central_node
  
  const nodes = props.graph.nodes.map(node => ({
    data: {
      id: node.id,
      label: node.label,
      type: node.type || 'concept',
      importance: node.importance || 5,
      color: node.color || nodeTypeColors[node.type || 'concept'] || '#6366f1',
      description: node.description || '',
      central: node.id === centralNodeId,
    }
  }))
  
  const edges = props.graph.edges.map((edge, index) => ({
    data: {
      id: `edge-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.label || '',
      type: edge.type || 'relates_to',
      strength: edge.strength || 5,
      style: edge.style || 'solid',
    }
  }))
  
  return [...nodes, ...edges]
}

// Initialize Cytoscape
const initCytoscape = async () => {
  if (!containerRef.value) return
  
  isLoading.value = true
  
  await nextTick()
  
  cy.value = cytoscape({
    container: containerRef.value,
    elements: getCytoscapeElements(),
    style: getStylesheet(),
    layout: layoutOptions[currentLayout.value] || layoutOptions.cose,
    wheelSensitivity: 0.3,
    minZoom: 0.2,
    maxZoom: 3,
    userZoomingEnabled: props.interactive,
    userPanningEnabled: props.interactive,
    boxSelectionEnabled: false,
  })
  
  // Event listeners
  if (props.interactive) {
    // Node click
    cy.value.on('tap', 'node', (evt) => {
      const node = evt.target
      const nodeData = node.data() as GraphNode
      selectedNode.value = nodeData
      emit('nodeClick', nodeData)
      highlightNeighbors(node)
    })
    
    // Edge click
    cy.value.on('tap', 'edge', (evt) => {
      const edge = evt.target
      const edgeData = edge.data() as GraphEdge
      emit('edgeClick', edgeData)
    })
    
    // Background click - reset highlight
    cy.value.on('tap', (evt) => {
      if (evt.target === cy.value) {
        selectedNode.value = null
        resetHighlight()
      }
    })
    
    // Node hover
    cy.value.on('mouseover', 'node', (evt) => {
      const node = evt.target
      node.style('cursor', 'pointer')
    })
  }
  
  // Layout complete
  cy.value.on('layoutstop', () => {
    isLoading.value = false
    emit('ready')
  })
}

// Highlight neighbors of selected node
const highlightNeighbors = (node: NodeSingular) => {
  if (!cy.value) return
  
  const neighborhood = node.closedNeighborhood()
  
  cy.value.elements().addClass('dimmed')
  neighborhood.removeClass('dimmed').addClass('highlighted')
  node.removeClass('dimmed').addClass('highlighted')
}

// Reset highlight
const resetHighlight = () => {
  if (!cy.value) return
  
  cy.value.elements().removeClass('dimmed highlighted')
}

// Change layout
const changeLayout = (layout: typeof props.layout) => {
  if (!cy.value) return
  
  currentLayout.value = layout
  const layoutConfig = layoutOptions[layout] || layoutOptions.cose
  cy.value.layout(layoutConfig).run()
}

// Zoom controls
const zoomIn = () => {
  if (!cy.value) return
  cy.value.zoom(cy.value.zoom() * 1.2)
}

const zoomOut = () => {
  if (!cy.value) return
  cy.value.zoom(cy.value.zoom() / 1.2)
}

const fitToScreen = () => {
  if (!cy.value) return
  cy.value.fit(undefined, 50)
}

const centerOnNode = () => {
  if (!cy.value || !selectedNode.value) return
  const node = cy.value.$id(selectedNode.value.id)
  cy.value.center(node)
}

// Export as PNG
const exportPng = () => {
  if (!cy.value) return
  
  const png = cy.value.png({
    bg: isDarkTheme.value ? '#1a1a1a' : '#ffffff',
    scale: 2,
    full: true,
  })
  
  const link = document.createElement('a')
  link.download = `${props.title || 'knowledge-graph'}.png`
  link.href = png
  link.click()
}

// Refresh
const refresh = () => {
  if (!cy.value) return
  
  cy.value.elements().remove()
  cy.value.add(getCytoscapeElements())
  cy.value.layout(layoutOptions[currentLayout.value] || layoutOptions.cose).run()
}

// Watch for graph changes
watch(() => props.graph, () => {
  if (cy.value) {
    refresh()
  }
}, { deep: true })

// Watch for theme changes
watch(isDarkTheme, () => {
  if (cy.value) {
    cy.value.style(getStylesheet())
  }
})

// Lifecycle
onMounted(() => {
  initCytoscape()
})

onUnmounted(() => {
  if (cy.value) {
    cy.value.destroy()
  }
})

// Expose methods
defineExpose({
  refresh,
  zoomIn,
  zoomOut,
  fitToScreen,
  exportPng,
  changeLayout,
})
</script>

<template>
  <div 
    class="knowledge-graph"
    :class="{ 'theme-dark': isDarkTheme }"
    :style="containerStyle"
  >
    <!-- Toolbar -->
    <div 
      v-if="showToolbar"
      class="graph-toolbar"
    >
      <span 
        v-if="title || graph.metadata?.title"
        class="toolbar-title"
      >
        {{ title || graph.metadata?.title }}
      </span>
      
      <div class="toolbar-actions">
        <!-- Layout selector -->
        <select 
          v-model="currentLayout"
          class="layout-select"
          @change="changeLayout(currentLayout)"
        >
          <option value="cose">
            力导向
          </option>
          <option value="circle">
            圆形
          </option>
          <option value="breadthfirst">
            层次
          </option>
          <option value="concentric">
            同心
          </option>
          <option value="grid">
            网格
          </option>
        </select>
        
        <div class="toolbar-divider" />
        
        <button
          class="toolbar-btn"
          title="放大"
          @click="zoomIn"
        >
          <MagnifyingGlassPlusIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn"
          title="缩小"
          @click="zoomOut"
        >
          <MagnifyingGlassMinusIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn"
          title="适应屏幕"
          @click="fitToScreen"
        >
          <ArrowsPointingOutIcon class="w-4 h-4" />
        </button>
        
        <button
          v-if="selectedNode"
          class="toolbar-btn"
          title="居中选中节点"
          @click="centerOnNode"
        >
          <ViewfinderCircleIcon class="w-4 h-4" />
        </button>
        
        <div class="toolbar-divider" />
        
        <button
          class="toolbar-btn"
          title="刷新布局"
          @click="refresh"
        >
          <ArrowPathIcon class="w-4 h-4" />
        </button>
        
        <button
          class="toolbar-btn"
          title="导出图片"
          @click="exportPng"
        >
          <ArrowDownTrayIcon class="w-4 h-4" />
        </button>
      </div>
    </div>
    
    <!-- Graph Container -->
    <div 
      ref="containerRef" 
      class="graph-container"
    />
    
    <!-- Loading Overlay -->
    <div 
      v-if="isLoading"
      class="graph-loading"
    >
      <div class="loading-spinner" />
      <span>生成知识图谱中...</span>
    </div>
    
    <!-- Legend -->
    <div 
      v-if="showLegend && usedNodeTypes.length > 0"
      class="graph-legend"
    >
      <div 
        v-for="type in usedNodeTypes"
        :key="type"
        class="legend-item"
      >
        <span 
          class="legend-dot"
          :style="{ backgroundColor: nodeTypeColors[type] }"
        />
        <span class="legend-label">{{ nodeTypeLabels[type] || type }}</span>
      </div>
    </div>
    
    <!-- Selected Node Info -->
    <div 
      v-if="selectedNode"
      class="node-info"
    >
      <div class="node-info-header">
        <span 
          class="node-type-badge"
          :style="{ backgroundColor: nodeTypeColors[selectedNode.type || 'concept'] }"
        >
          {{ nodeTypeLabels[selectedNode.type || 'concept'] }}
        </span>
        <span class="node-label">{{ selectedNode.label }}</span>
      </div>
      <p 
        v-if="selectedNode.description"
        class="node-description"
      >
        {{ selectedNode.description }}
      </p>
    </div>
    
    <!-- Stats -->
    <div class="graph-stats">
      {{ graph.nodes.length }} 节点 · {{ graph.edges.length }} 关系
    </div>
  </div>
</template>

<style scoped>
.knowledge-graph {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary, #f5f5f5);
  border: 1px solid var(--any-border, #e5e5e5);
  border-radius: 12px;
  overflow: hidden;
}

.knowledge-graph.theme-dark {
  background: var(--any-bg-secondary, #1a1a1a);
  border-color: var(--any-border, #333);
}

.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--any-bg-primary, #ffffff);
  border-bottom: 1px solid var(--any-border, #e5e5e5);
}

.theme-dark .graph-toolbar {
  background: var(--any-bg-primary, #222);
  border-color: var(--any-border, #333);
}

.toolbar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary, #333);
}

.theme-dark .toolbar-title {
  color: var(--any-text-primary, #f5f5f5);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--any-border, #e5e5e5);
  margin: 0 4px;
}

.theme-dark .toolbar-divider {
  background: var(--any-border, #444);
}

.layout-select {
  padding: 6px 10px;
  font-size: 12px;
  background: var(--any-bg-tertiary, #f5f5f5);
  border: 1px solid var(--any-border, #e5e5e5);
  border-radius: 6px;
  color: var(--any-text-primary, #333);
  cursor: pointer;
}

.theme-dark .layout-select {
  background: var(--any-bg-tertiary, #333);
  border-color: var(--any-border, #444);
  color: var(--any-text-primary, #f5f5f5);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: var(--any-text-secondary, #666);
  transition: all 0.2s ease;
}

.toolbar-btn:hover {
  background: var(--any-bg-hover, #f0f0f0);
  color: var(--any-text-primary, #333);
}

.theme-dark .toolbar-btn:hover {
  background: var(--any-bg-hover, #333);
  color: var(--any-text-primary, #f5f5f5);
}

.graph-container {
  flex: 1;
  min-height: 400px;
}

.graph-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--any-text-muted, #999);
}

.theme-dark .graph-loading {
  background: rgba(26, 26, 26, 0.9);
}

.loading-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--any-border, #e5e5e5);
  border-top-color: var(--exec-accent, #6366f1);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.graph-legend {
  position: absolute;
  bottom: 40px;
  left: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  background: var(--any-bg-primary, rgba(255, 255, 255, 0.95));
  border: 1px solid var(--any-border, #e5e5e5);
  border-radius: 8px;
  backdrop-filter: blur(8px);
}

.theme-dark .graph-legend {
  background: var(--any-bg-primary, rgba(34, 34, 34, 0.95));
  border-color: var(--any-border, #444);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  font-size: 11px;
  color: var(--any-text-secondary, #666);
}

.theme-dark .legend-label {
  color: var(--any-text-secondary, #aaa);
}

.node-info {
  position: absolute;
  bottom: 40px;
  right: 12px;
  max-width: 280px;
  padding: 12px 14px;
  background: var(--any-bg-primary, rgba(255, 255, 255, 0.95));
  border: 1px solid var(--any-border, #e5e5e5);
  border-radius: 8px;
  backdrop-filter: blur(8px);
}

.theme-dark .node-info {
  background: var(--any-bg-primary, rgba(34, 34, 34, 0.95));
  border-color: var(--any-border, #444);
}

.node-info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.node-type-badge {
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 500;
  color: white;
  border-radius: 10px;
}

.node-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary, #333);
}

.theme-dark .node-label {
  color: var(--any-text-primary, #f5f5f5);
}

.node-description {
  font-size: 12px;
  color: var(--any-text-secondary, #666);
  line-height: 1.5;
  margin: 0;
}

.theme-dark .node-description {
  color: var(--any-text-secondary, #aaa);
}

.graph-stats {
  position: absolute;
  bottom: 12px;
  right: 12px;
  font-size: 11px;
  color: var(--any-text-muted, #999);
}
</style>
