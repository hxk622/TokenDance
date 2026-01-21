/**
 * Research Block Types - Block 化研究进度的类型定义
 */
import type { ResearchPhase, SearchQuery, ResearchSource } from '../types'

/** Block 状态 */
export type BlockStatus = 'pending' | 'running' | 'completed' | 'failed'

/** Block 摘要 */
export interface BlockSummary {
  /** 摘要文本，如 "3 个查询，找到 12 个来源" */
  text: string
  /** 可选的统计指标 */
  metrics?: {
    queriesCount?: number
    sourcesCount?: number
    /** 耗时（秒） */
    duration?: number
    /** 关键发现，最多 3 条 */
    keyFindings?: string[]
  }
}

/** 研究 Block */
export interface ResearchBlock {
  id: string
  /** 研究阶段 */
  phase: ResearchPhase
  /** Block 状态 */
  status: BlockStatus
  /** 开始时间戳 */
  startedAt: number
  /** 完成时间戳 */
  completedAt?: number
  
  // Phase-specific content
  /** 搜索查询（searching 阶段） */
  queries: SearchQuery[]
  /** 信息来源（reading/analyzing 阶段） */
  sources: ResearchSource[]
  /** 规划笔记（planning 阶段） */
  planningNotes?: string[]
  /** 写作大纲（writing 阶段） */
  writingOutline?: string[]
  
  // UI state
  /** 是否展开 */
  isExpanded: boolean
  /** Block 摘要 */
  summary?: BlockSummary
  
  // Progress
  /** Block 内进度 0-100 */
  progress: number
  /** 当前操作描述 */
  currentAction?: string
}

/** 研究会话 */
export interface ResearchSession {
  id: string
  /** 研究主题 */
  topic: string
  /** 开始时间戳 */
  startedAt: number
  /** Block 列表 */
  blocks: ResearchBlock[]
  /** 当前活跃的 Block ID */
  currentBlockId: string | null
  /** 总体进度 0-100 */
  overallProgress: number
  /** 会话状态 */
  status: 'idle' | 'running' | 'paused' | 'completed'
}

/** 阶段配置 */
export interface PhaseBlockConfig {
  id: ResearchPhase
  name: string
  description: string
  icon: string
}

/** 阶段配置列表 */
export const PHASE_BLOCK_CONFIG: PhaseBlockConfig[] = [
  { id: 'planning', name: '规划', description: '分析主题，制定搜索策略', icon: 'Compass' },
  { id: 'searching', name: '搜索', description: '执行搜索查询', icon: 'Search' },
  { id: 'reading', name: '阅读', description: '深度阅读来源内容', icon: 'BookOpen' },
  { id: 'analyzing', name: '分析', description: '信息综合与验证', icon: 'BrainCircuit' },
  { id: 'writing', name: '撰写', description: '生成研究报告', icon: 'FileText' },
]

/** Block 状态配置 */
export const BLOCK_STATUS_CONFIG: Record<BlockStatus, {
  label: string
  color: string
  bgColor: string
}> = {
  pending: {
    label: '等待中',
    color: 'var(--any-text-muted)',
    bgColor: 'transparent',
  },
  running: {
    label: '进行中',
    color: 'var(--exec-accent)',
    bgColor: 'rgba(0, 217, 255, 0.05)',
  },
  completed: {
    label: '已完成',
    color: 'var(--exec-success)',
    bgColor: 'rgba(0, 200, 83, 0.03)',
  },
  failed: {
    label: '失败',
    color: 'var(--exec-error)',
    bgColor: 'rgba(255, 59, 48, 0.05)',
  },
}

/** 生成 Block 摘要 */
export function generateBlockSummary(block: ResearchBlock): BlockSummary {
  const duration = block.completedAt 
    ? Math.round((block.completedAt - block.startedAt) / 1000)
    : undefined

  switch (block.phase) {
    case 'planning':
      return {
        text: `制定了 ${block.planningNotes?.length || 0} 个研究方向`,
        metrics: { duration },
      }
    case 'searching': {
      const doneQueries = block.queries.filter(q => q.status === 'done').length
      const sourcesCount = block.sources.length
      return {
        text: `${doneQueries} 个查询，发现 ${sourcesCount} 个来源`,
        metrics: { queriesCount: doneQueries, sourcesCount, duration },
      }
    }
    case 'reading': {
      const doneReading = block.sources.filter(s => s.status === 'done').length
      const highCredibility = block.sources.filter(s => s.credibility >= 70).length
      return {
        text: `深度阅读 ${doneReading} 篇，${highCredibility} 篇高可信度`,
        metrics: { sourcesCount: doneReading, duration },
      }
    }
    case 'analyzing':
      return {
        text: `综合分析 ${block.sources.length} 个信息源`,
        metrics: { sourcesCount: block.sources.length, duration },
      }
    case 'writing':
      return {
        text: `生成研究报告 ${block.writingOutline?.length || 0} 个章节`,
        metrics: { duration },
      }
    default:
      return { text: '处理中...' }
  }
}

/** 创建初始 Block */
export function createBlock(phase: ResearchPhase, isExpanded = false): ResearchBlock {
  return {
    id: `block-${phase}-${Date.now()}`,
    phase,
    status: 'pending',
    startedAt: Date.now(),
    queries: [],
    sources: [],
    isExpanded,
    progress: 0,
  }
}

/** 创建初始 Session */
export function createSession(topic: string): ResearchSession {
  const phases: ResearchPhase[] = ['planning', 'searching', 'reading', 'analyzing', 'writing']
  const blocks = phases.map((phase, index) => createBlock(phase, index === 0))
  
  return {
    id: `session-${Date.now()}`,
    topic,
    startedAt: Date.now(),
    blocks,
    currentBlockId: blocks[0].id,
    overallProgress: 0,
    status: 'idle',
  }
}
