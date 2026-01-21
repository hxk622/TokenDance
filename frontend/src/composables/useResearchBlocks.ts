/**
 * useResearchBlocks - Block 化研究进度的状态管理
 * 
 * 核心职责：
 * - 管理 ResearchSession 状态
 * - 处理 Block 生命周期转换
 * - 自动折叠完成的 Block
 * - 响应后端事件更新状态
 */
import { ref, computed, watch, type Ref } from 'vue'
import type { ResearchPhase, SearchQuery, ResearchSource } from '@/components/execution/research/types'
import {
  type ResearchBlock,
  type ResearchSession,
  type BlockStatus,
  createSession,
  generateBlockSummary,
  PHASE_BLOCK_CONFIG,
} from '@/components/execution/research/blocks/types'

/** 自动折叠延迟（毫秒） */
const AUTO_COLLAPSE_DELAY = 500

/** Block 事件类型 */
export interface BlockEvent {
  type: 'phase_start' | 'phase_progress' | 'phase_complete' | 'query_update' | 'source_update' | 'error'
  payload: {
    phase?: ResearchPhase
    progress?: number
    query?: SearchQuery
    source?: ResearchSource
    error?: string
    planningNote?: string
    outlineSection?: string
  }
}

export function useResearchBlocks(topic: Ref<string> | string) {
  // ========================================
  // State
  // ========================================
  
  const session = ref<ResearchSession | null>(null)
  const autoCollapseTimeouts = new Map<string, ReturnType<typeof setTimeout>>()
  
  // ========================================
  // Computed
  // ========================================
  
  /** 当前活跃的 Block */
  const currentBlock = computed(() => {
    if (!session.value?.currentBlockId) return null
    return session.value.blocks.find(b => b.id === session.value!.currentBlockId) ?? null
  })
  
  /** 已完成的 Blocks */
  const completedBlocks = computed(() => {
    return session.value?.blocks.filter(b => b.status === 'completed') ?? []
  })
  
  /** 进行中的 Blocks */
  const runningBlocks = computed(() => {
    return session.value?.blocks.filter(b => b.status === 'running') ?? []
  })
  
  /** 总体进度 */
  const overallProgress = computed(() => {
    if (!session.value) return 0
    const blocks = session.value.blocks
    const phaseWeight = 100 / blocks.length
    
    let progress = 0
    for (const block of blocks) {
      if (block.status === 'completed') {
        progress += phaseWeight
      } else if (block.status === 'running') {
        progress += (block.progress / 100) * phaseWeight
      }
    }
    return Math.round(progress)
  })
  
  // ========================================
  // Methods
  // ========================================
  
  /** 初始化 Session */
  function initSession() {
    const topicValue = typeof topic === 'string' ? topic : topic.value
    session.value = createSession(topicValue)
  }
  
  /** 获取 Block by ID */
  function getBlock(blockId: string): ResearchBlock | null {
    return session.value?.blocks.find(b => b.id === blockId) ?? null
  }
  
  /** 获取 Block by Phase */
  function getBlockByPhase(phase: ResearchPhase): ResearchBlock | null {
    return session.value?.blocks.find(b => b.phase === phase) ?? null
  }
  
  /** 更新 Block 状态 */
  function updateBlockStatus(blockId: string, status: BlockStatus) {
    const block = getBlock(blockId)
    if (!block) return
    
    const prevStatus = block.status
    block.status = status
    
    // 状态转换副作用
    if (status === 'running' && prevStatus !== 'running') {
      // 开始运行 -> 展开
      block.isExpanded = true
      block.startedAt = Date.now()
      if (session.value) {
        session.value.currentBlockId = blockId
        session.value.status = 'running'
      }
    }
    
    if (status === 'completed') {
      // 完成 -> 生成摘要，延迟自动折叠
      block.completedAt = Date.now()
      block.progress = 100
      block.summary = generateBlockSummary(block)
      scheduleAutoCollapse(blockId)
      
      // 检查是否移动到下一阶段
      advanceToNextBlock(blockId)
    }
    
    if (status === 'failed') {
      block.isExpanded = true
    }
    
    // 更新总体进度
    if (session.value) {
      session.value.overallProgress = overallProgress.value
    }
  }
  
  /** 安排自动折叠 */
  function scheduleAutoCollapse(blockId: string) {
    // 清除之前的定时器
    const existing = autoCollapseTimeouts.get(blockId)
    if (existing) clearTimeout(existing)
    
    const timeout = setTimeout(() => {
      const block = getBlock(blockId)
      if (block && block.status === 'completed') {
        block.isExpanded = false
      }
      autoCollapseTimeouts.delete(blockId)
    }, AUTO_COLLAPSE_DELAY)
    
    autoCollapseTimeouts.set(blockId, timeout)
  }
  
  /** 推进到下一个 Block */
  function advanceToNextBlock(completedBlockId: string) {
    if (!session.value) return
    
    const blocks = session.value.blocks
    const currentIndex = blocks.findIndex(b => b.id === completedBlockId)
    
    if (currentIndex >= 0 && currentIndex < blocks.length - 1) {
      const nextBlock = blocks[currentIndex + 1]
      session.value.currentBlockId = nextBlock.id
      // 下一个 Block 将由后端事件触发 running 状态
    } else if (currentIndex === blocks.length - 1) {
      // 所有 Block 完成
      session.value.status = 'completed'
      session.value.currentBlockId = null
    }
  }
  
  /** 更新 Block 进度 */
  function updateBlockProgress(blockId: string, progress: number, currentAction?: string) {
    const block = getBlock(blockId)
    if (!block) return
    
    block.progress = Math.min(100, Math.max(0, progress))
    if (currentAction !== undefined) {
      block.currentAction = currentAction
    }
    
    // 更新总体进度
    if (session.value) {
      session.value.overallProgress = overallProgress.value
    }
  }
  
  /** 添加查询到 Block */
  function addQuery(phase: ResearchPhase, query: SearchQuery) {
    const block = getBlockByPhase(phase)
    if (!block) return
    
    const existingIndex = block.queries.findIndex(q => q.id === query.id)
    if (existingIndex >= 0) {
      block.queries[existingIndex] = query
    } else {
      block.queries.push(query)
    }
  }
  
  /** 更新查询状态 */
  function updateQuery(queryId: string, updates: Partial<SearchQuery>) {
    if (!session.value) return
    
    for (const block of session.value.blocks) {
      const query = block.queries.find(q => q.id === queryId)
      if (query) {
        Object.assign(query, updates)
        break
      }
    }
  }
  
  /** 添加来源到 Block */
  function addSource(phase: ResearchPhase, source: ResearchSource) {
    const block = getBlockByPhase(phase)
    if (!block) return
    
    const existingIndex = block.sources.findIndex(s => s.id === source.id)
    if (existingIndex >= 0) {
      block.sources[existingIndex] = source
    } else {
      block.sources.push(source)
    }
  }
  
  /** 更新来源状态 */
  function updateSource(sourceId: string, updates: Partial<ResearchSource>) {
    if (!session.value) return
    
    for (const block of session.value.blocks) {
      const source = block.sources.find(s => s.id === sourceId)
      if (source) {
        Object.assign(source, updates)
        break
      }
    }
  }
  
  /** 添加规划笔记 */
  function addPlanningNote(note: string) {
    const block = getBlockByPhase('planning')
    if (!block) return
    
    if (!block.planningNotes) {
      block.planningNotes = []
    }
    block.planningNotes.push(note)
  }
  
  /** 添加写作大纲章节 */
  function addOutlineSection(section: string) {
    const block = getBlockByPhase('writing')
    if (!block) return
    
    if (!block.writingOutline) {
      block.writingOutline = []
    }
    block.writingOutline.push(section)
  }
  
  /** 切换 Block 展开/折叠 */
  function toggleBlockExpand(blockId: string) {
    const block = getBlock(blockId)
    if (!block) return
    
    // 取消自动折叠定时器
    const timeout = autoCollapseTimeouts.get(blockId)
    if (timeout) {
      clearTimeout(timeout)
      autoCollapseTimeouts.delete(blockId)
    }
    
    block.isExpanded = !block.isExpanded
  }
  
  /** 折叠所有 Blocks */
  function collapseAll() {
    if (!session.value) return
    for (const block of session.value.blocks) {
      // 不折叠正在运行的 Block
      if (block.status !== 'running') {
        block.isExpanded = false
      }
    }
  }
  
  /** 展开所有 Blocks */
  function expandAll() {
    if (!session.value) return
    for (const block of session.value.blocks) {
      block.isExpanded = true
    }
  }
  
  /** 处理后端事件 */
  function handleEvent(event: BlockEvent) {
    if (!session.value) {
      initSession()
    }
    
    const { type, payload } = event
    
    switch (type) {
      case 'phase_start': {
        if (payload.phase) {
          const block = getBlockByPhase(payload.phase)
          if (block) {
            updateBlockStatus(block.id, 'running')
          }
        }
        break
      }
      
      case 'phase_progress': {
        if (payload.phase !== undefined && payload.progress !== undefined) {
          const block = getBlockByPhase(payload.phase)
          if (block) {
            updateBlockProgress(block.id, payload.progress)
          }
        }
        break
      }
      
      case 'phase_complete': {
        if (payload.phase) {
          const block = getBlockByPhase(payload.phase)
          if (block) {
            updateBlockStatus(block.id, 'completed')
          }
        }
        break
      }
      
      case 'query_update': {
        if (payload.query) {
          // 默认添加到 searching 阶段
          addQuery('searching', payload.query)
        }
        break
      }
      
      case 'source_update': {
        if (payload.source) {
          // 根据当前阶段决定添加位置
          const currentPhase = currentBlock.value?.phase
          const targetPhase = currentPhase === 'reading' || currentPhase === 'analyzing' 
            ? currentPhase 
            : 'searching'
          addSource(targetPhase, payload.source)
        }
        break
      }
      
      case 'error': {
        if (currentBlock.value) {
          updateBlockStatus(currentBlock.value.id, 'failed')
          currentBlock.value.currentAction = payload.error || '发生错误'
        }
        break
      }
    }
  }
  
  /** 重置 Session */
  function reset() {
    // 清除所有自动折叠定时器
    for (const timeout of autoCollapseTimeouts.values()) {
      clearTimeout(timeout)
    }
    autoCollapseTimeouts.clear()
    
    session.value = null
  }
  
  /** 暂停 Session */
  function pause() {
    if (session.value) {
      session.value.status = 'paused'
    }
  }
  
  /** 恢复 Session */
  function resume() {
    if (session.value && session.value.status === 'paused') {
      session.value.status = 'running'
    }
  }
  
  // ========================================
  // Cleanup
  // ========================================
  
  // Watch for topic changes
  if (typeof topic !== 'string') {
    watch(topic, (newTopic) => {
      if (newTopic && !session.value) {
        initSession()
      }
    })
  }
  
  return {
    // State
    session,
    currentBlock,
    completedBlocks,
    runningBlocks,
    overallProgress,
    
    // Methods
    initSession,
    getBlock,
    getBlockByPhase,
    updateBlockStatus,
    updateBlockProgress,
    addQuery,
    updateQuery,
    addSource,
    updateSource,
    addPlanningNote,
    addOutlineSection,
    toggleBlockExpand,
    collapseAll,
    expandAll,
    handleEvent,
    reset,
    pause,
    resume,
  }
}
