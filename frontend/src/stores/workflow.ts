/**
 * Workflow Store
 * 
 * 专门管理 WorkflowGraph 的 DAG 状态
 * 处理 Plan 相关 SSE 事件，与后端 PlanningLayer 同步
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Task 数据结构 - 与后端 Task 对齐
 */
export interface Task {
  id: string
  title: string
  description: string
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  dependsOn: string[]
  acceptanceCriteria?: string
  toolsHint?: string[]
  metadata?: {
    startTime?: number
    endTime?: number
    duration?: number
    output?: string
    errorMessage?: string
  }
}

/**
 * Plan 数据结构 - 与后端 Plan 对齐
 */
export interface Plan {
  planId: string
  goal: string
  version: number
  tasks: Task[]
  progress: {
    total: number
    completed: number
    failed: number
    running: number
    skipped: number
    pending: number
    percentage: number
  }
  createdAt: number
  updatedAt: number
}

/**
 * WorkflowNode - 用于 WorkflowGraph 渲染
 */
export interface WorkflowNode {
  id: string
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped'
  label: string
  x: number
  y: number
  dependencies: string[]
  metadata?: {
    startTime?: number
    endTime?: number
    duration?: number
    output?: string
    errorMessage?: string
  }
  // 原始 Task 数据
  task?: Task
}

/**
 * WorkflowEdge - 依赖关系连线
 */
export interface WorkflowEdge {
  id: string
  from: string
  to: string
}

// 自动布局参数
const LAYOUT_CONFIG = {
  nodeWidth: 60,
  nodeHeight: 60,
  horizontalSpacing: 150,
  verticalSpacing: 100,
  startX: 100,
  startY: 150,
}

export const useWorkflowStore = defineStore('workflow', () => {
  // Plan 状态
  const plan = ref<Plan | null>(null)
  
  // WorkflowGraph 渲染状态
  const nodes = ref<WorkflowNode[]>([])
  const edges = ref<WorkflowEdge[]>([])
  
  // 选中状态
  const selectedNodeId = ref<string | null>(null)
  
  // Computed
  const isLoaded = computed(() => plan.value !== null)
  const progress = computed(() => plan.value?.progress || { total: 0, completed: 0, percentage: 0 })
  const currentTask = computed(() => nodes.value.find(n => n.status === 'running'))
  const completedTasks = computed(() => nodes.value.filter(n => n.status === 'success'))
  const failedTasks = computed(() => nodes.value.filter(n => n.status === 'error'))
  
  // ========== Plan 事件处理 ==========
  
  /**
   * 处理 plan.created 事件
   * 初始化 WorkflowGraph
   */
  function handlePlanCreated(data: Plan) {
    console.log('[WorkflowStore] Plan created:', data.planId, 'with', data.tasks.length, 'tasks')
    
    plan.value = data
    
    // 转换 Task 为 WorkflowNode
    nodes.value = data.tasks.map((task, index) => {
      const pos = calculateNodePosition(task, data.tasks)
      return {
        id: task.id,
        status: task.status,
        label: task.title,
        x: pos.x,
        y: pos.y,
        dependencies: task.dependsOn,
        metadata: task.metadata,
        task,
      }
    })
    
    // 生成 edges
    edges.value = generateEdgesFromTasks(data.tasks)
  }
  
  /**
   * 处理 plan.revised 事件
   * 重新渲染 WorkflowGraph
   */
  function handlePlanRevised(data: Plan & { reason?: string }) {
    console.log('[WorkflowStore] Plan revised:', data.planId, 'version', data.version, 'reason:', data.reason)
    
    plan.value = data
    
    // 重新计算布局
    nodes.value = data.tasks.map((task, index) => {
      const pos = calculateNodePosition(task, data.tasks)
      return {
        id: task.id,
        status: task.status,
        label: task.title,
        x: pos.x,
        y: pos.y,
        dependencies: task.dependsOn,
        metadata: task.metadata,
        task,
      }
    })
    
    edges.value = generateEdgesFromTasks(data.tasks)
  }
  
  /**
   * 处理 task.start 事件
   */
  function handleTaskStart(data: { taskId: string; status: string; startTime?: number }) {
    console.log('[WorkflowStore] Task started:', data.taskId)
    
    const node = nodes.value.find(n => n.id === data.taskId)
    if (node) {
      node.status = 'running'
      if (!node.metadata) node.metadata = {}
      node.metadata.startTime = data.startTime
    }
    
    // 更新 plan 中的 task
    if (plan.value) {
      const task = plan.value.tasks.find(t => t.id === data.taskId)
      if (task) {
        task.status = 'running'
        if (!task.metadata) task.metadata = {}
        task.metadata.startTime = data.startTime
      }
    }
  }
  
  /**
   * 处理 task.complete 事件
   */
  function handleTaskComplete(data: {
    taskId: string
    status: string
    output?: string
    endTime?: number
    duration?: number
  }) {
    console.log('[WorkflowStore] Task completed:', data.taskId)
    
    const node = nodes.value.find(n => n.id === data.taskId)
    if (node) {
      node.status = 'success'
      if (!node.metadata) node.metadata = {}
      node.metadata.output = data.output
      node.metadata.endTime = data.endTime
      node.metadata.duration = data.duration
    }
    
    // 更新 plan
    if (plan.value) {
      const task = plan.value.tasks.find(t => t.id === data.taskId)
      if (task) {
        task.status = 'success'
        if (!task.metadata) task.metadata = {}
        task.metadata.output = data.output
        task.metadata.endTime = data.endTime
        task.metadata.duration = data.duration
      }
      // 更新进度
      updateProgress()
    }
  }
  
  /**
   * 处理 task.failed 事件
   */
  function handleTaskFailed(data: {
    taskId: string
    status: string
    errorMessage?: string
    endTime?: number
    retryCount?: number
    canRetry?: boolean
  }) {
    console.log('[WorkflowStore] Task failed:', data.taskId, 'error:', data.errorMessage)
    
    const node = nodes.value.find(n => n.id === data.taskId)
    if (node) {
      node.status = 'error'
      if (!node.metadata) node.metadata = {}
      node.metadata.errorMessage = data.errorMessage
      node.metadata.endTime = data.endTime
    }
    
    // 更新 plan
    if (plan.value) {
      const task = plan.value.tasks.find(t => t.id === data.taskId)
      if (task) {
        task.status = 'error'
        if (!task.metadata) task.metadata = {}
        task.metadata.errorMessage = data.errorMessage
        task.metadata.endTime = data.endTime
      }
      updateProgress()
    }
  }
  
  /**
   * 处理 task.update 事件 (通用更新)
   */
  function handleTaskUpdate(data: Task) {
    console.log('[WorkflowStore] Task updated:', data.id, 'status:', data.status)
    
    const node = nodes.value.find(n => n.id === data.id)
    if (node) {
      node.status = data.status
      node.metadata = data.metadata
      node.task = data
    }
    
    if (plan.value) {
      const taskIndex = plan.value.tasks.findIndex(t => t.id === data.id)
      if (taskIndex >= 0) {
        plan.value.tasks[taskIndex] = data
      }
      updateProgress()
    }
  }
  
  // ========== 辅助函数 ==========
  
  /**
   * 更新进度统计
   */
  function updateProgress() {
    if (!plan.value) return
    
    const tasks = plan.value.tasks
    const total = tasks.length
    const completed = tasks.filter(t => t.status === 'success').length
    const failed = tasks.filter(t => t.status === 'error').length
    const running = tasks.filter(t => t.status === 'running').length
    const skipped = tasks.filter(t => t.status === 'skipped').length
    const pending = total - completed - failed - running - skipped
    
    plan.value.progress = {
      total,
      completed,
      failed,
      running,
      skipped,
      pending,
      percentage: total > 0 ? Math.round((completed + skipped) / total * 100) : 0,
    }
  }
  
  /**
   * 计算节点位置 (基于依赖关系的分层布局)
   */
  function calculateNodePosition(task: Task, allTasks: Task[]): { x: number; y: number } {
    // 计算任务所在的层级 (基于依赖深度)
    const level = calculateTaskLevel(task.id, allTasks, new Set())
    
    // 统计同层级任务数量，确定在该层的位置
    const sameLevel = allTasks.filter(t => calculateTaskLevel(t.id, allTasks, new Set()) === level)
    const indexInLevel = sameLevel.findIndex(t => t.id === task.id)
    
    const x = LAYOUT_CONFIG.startX + level * LAYOUT_CONFIG.horizontalSpacing
    const y = LAYOUT_CONFIG.startY + indexInLevel * LAYOUT_CONFIG.verticalSpacing
    
    return { x, y }
  }
  
  /**
   * 计算任务的层级 (递归计算依赖深度)
   */
  function calculateTaskLevel(taskId: string, allTasks: Task[], visited: Set<string>): number {
    if (visited.has(taskId)) return 0 // 防止循环依赖
    visited.add(taskId)
    
    const task = allTasks.find(t => t.id === taskId)
    if (!task || task.dependsOn.length === 0) return 0
    
    const depLevels = task.dependsOn.map(depId => 
      calculateTaskLevel(depId, allTasks, visited)
    )
    
    return Math.max(...depLevels) + 1
  }
  
  /**
   * 从 Tasks 生成 Edges
   */
  function generateEdgesFromTasks(tasks: Task[]): WorkflowEdge[] {
    const edges: WorkflowEdge[] = []
    
    for (const task of tasks) {
      for (const depId of task.dependsOn) {
        edges.push({
          id: `${depId}-${task.id}`,
          from: depId,
          to: task.id,
        })
      }
    }
    
    return edges
  }
  
  /**
   * 选中节点
   */
  function selectNode(nodeId: string | null) {
    selectedNodeId.value = nodeId
  }
  
  /**
   * 获取节点详情
   */
  function getNodeDetail(nodeId: string): WorkflowNode | undefined {
    return nodes.value.find(n => n.id === nodeId)
  }
  
  /**
   * 重置状态
   */
  function reset() {
    plan.value = null
    nodes.value = []
    edges.value = []
    selectedNodeId.value = null
  }
  
  return {
    // 状态
    plan,
    nodes,
    edges,
    selectedNodeId,
    
    // Computed
    isLoaded,
    progress,
    currentTask,
    completedTasks,
    failedTasks,
    
    // Plan 事件处理
    handlePlanCreated,
    handlePlanRevised,
    handleTaskStart,
    handleTaskComplete,
    handleTaskFailed,
    handleTaskUpdate,
    
    // 操作
    selectNode,
    getNodeDetail,
    reset,
  }
})
