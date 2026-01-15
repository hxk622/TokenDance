<script setup lang="ts">
import { computed } from 'vue'

export interface ExecutingTask {
  id: string
  title: string
  progress: number
  nodeCount: number
  currentNodeIndex: number
}

const props = defineProps<{
  totalTasksRunning?: number
  totalMessagesProcessing?: number
  executingTasks?: ExecutingTask[]
}>()

const defaultTotalTasks = 247
const defaultTotalMessages = 1200000

const defaultTasks: ExecutingTask[] = [
  { id: '1', title: '竞品分析', progress: 67, nodeCount: 5, currentNodeIndex: 3 },
  { id: '2', title: 'PPT 生成', progress: 42, nodeCount: 8, currentNodeIndex: 3 },
  { id: '3', title: '代码审查', progress: 89, nodeCount: 4, currentNodeIndex: 4 }
]

const totalTasksRunning = computed(() => props.totalTasksRunning || defaultTotalTasks)
const totalMessagesProcessing = computed(() => props.totalMessagesProcessing || defaultTotalMessages)
const executingTasks = computed(() => props.executingTasks || defaultTasks)

const formatMessages = (num: number) => {
  if (num > 1000000) return `${(num / 1000000).toFixed(1)}M`
  if (num > 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}

const renderDagNodes = (task: ExecutingTask) => {
  const nodes = []
  for (let i = 0; i < Math.min(task.nodeCount, 5); i++) {
    const isActive = i < task.currentNodeIndex
    const isRunning = i === task.currentNodeIndex - 1
    nodes.push({ index: i, isActive, isRunning })
  }
  return nodes
}
</script>

<template>
  <div class="global-execution">
    <h3 class="execution-label">🌍 现在全球正在进行</h3>
    
    <!-- 实时统计 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-number pulse-number">{{ totalTasksRunning }}</div>
        <div class="stat-label">个任务运行中</div>
      </div>
      <div class="stat-card">
        <div class="stat-number pulse-number">{{ formatMessages(totalMessagesProcessing) }}</div>
        <div class="stat-label">条消息处理中</div>
      </div>
    </div>
    
    <!-- 执行任务展示 -->
    <div class="execution-showcase">
      <div v-for="task in executingTasks" :key="task.id" class="execution-card">
        <!-- 迷你 DAG 图 -->
        <div class="dag-mini">
          <svg class="dag-svg" viewBox="0 0 120 30">
            <!-- 节点 -->
            <template v-for="(node, i) in renderDagNodes(task)" :key="`node-${i}`">
              <!-- 连线 -->
              <line
                v-if="i < renderDagNodes(task).length - 1"
                :x1="15 + i * 25"
                y1="15"
                :x2="15 + (i + 1) * 25"
                y2="15"
                :class="node.isActive ? 'edge-active' : 'edge-inactive'"
              />
              <!-- 节点圆 -->
              <circle
                :cx="15 + i * 25"
                cy="15"
                r="6"
                :class="[
                  'dag-node',
                  node.isRunning ? 'node-running' : node.isActive ? 'node-active' : 'node-pending'
                ]"
              />
            </template>
          </svg>
        </div>
        
        <!-- 任务信息 -->
        <div class="task-info">
          <span class="task-title">{{ task.title }}</span>
          <span class="task-progress">{{ task.progress }}%</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.global-execution {
  @apply bg-white rounded-2xl border border-gray-100 p-6;
}

.execution-label {
  @apply text-xs font-medium text-gray-400 uppercase tracking-wider mb-4;
}

.stats-grid {
  @apply grid grid-cols-2 gap-4 mb-6;
}

.stat-card {
  @apply bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 text-center;
}

.stat-number {
  @apply text-2xl font-bold text-gray-900;
}

.stat-label {
  @apply text-xs text-gray-600 mt-1;
}

.pulse-number {
  animation: pulse-stat 2s ease-in-out infinite;
}

@keyframes pulse-stat {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

.execution-showcase {
  @apply space-y-3;
}

.execution-card {
  @apply flex items-center gap-3 px-4 py-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors;
}

.dag-mini {
  @apply w-20 h-8 flex-shrink-0;
}

.dag-svg {
  @apply w-full h-full;
}

.edge-active {
  @apply stroke-cyan-500 stroke-[1.5];
  stroke-dasharray: 3, 2;
  animation: flow-dash 1s linear infinite;
}

.edge-inactive {
  @apply stroke-gray-300 stroke-[1];
}

@keyframes flow-dash {
  to {
    stroke-dashoffset: -5;
  }
}

.dag-node {
  @apply transition-all duration-300;
}

.node-active {
  @apply fill-cyan-100 stroke-cyan-500 stroke-[1];
}

.node-running {
  @apply fill-cyan-500 stroke-cyan-600 stroke-[1.5];
  filter: drop-shadow(0 0 3px rgba(6, 182, 212, 0.5));
}

.node-pending {
  @apply fill-gray-200 stroke-gray-400 stroke-[1];
}

.task-info {
  @apply flex-1 flex items-center justify-between;
}

.task-title {
  @apply text-sm font-medium text-gray-900;
}

.task-progress {
  @apply text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded;
}
</style>
