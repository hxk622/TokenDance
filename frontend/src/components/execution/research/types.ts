/**
 * Research Progress Types - 研究进度类型定义
 */

/** 研究阶段 */
export type ResearchPhase = 
  | 'planning'    // 规划阶段：分析主题、生成搜索策略
  | 'searching'   // 搜索阶段：执行搜索查询
  | 'reading'     // 阅读阶段：深度阅读来源内容
  | 'analyzing'   // 分析阶段：信息综合、冲突解决
  | 'writing'     // 撰写阶段：生成报告

/** 阶段配置 */
export interface PhaseConfig {
  id: ResearchPhase
  name: string
  description: string
}

export const PHASE_CONFIG: PhaseConfig[] = [
  { id: 'planning', name: '规划', description: '分析主题，制定搜索策略' },
  { id: 'searching', name: '搜索', description: '执行搜索查询' },
  { id: 'reading', name: '阅读', description: '深度阅读来源内容' },
  { id: 'analyzing', name: '分析', description: '信息综合与验证' },
  { id: 'writing', name: '撰写', description: '生成研究报告' },
]

/** 查询状态 */
export type QueryStatus = 'pending' | 'running' | 'done' | 'failed'

/** 搜索查询 */
export interface SearchQuery {
  id: string
  text: string
  status: QueryStatus
  resultCount?: number
  timestamp?: string
}

/** 来源类型 */
export type SourceType = 
  | 'academic'   // 学术论文
  | 'report'     // 行业报告
  | 'news'       // 新闻资讯
  | 'blog'       // 博客文章
  | 'official'   // 官方文档
  | 'social'     // 社交媒体
  | 'unknown'    // 未知类型

/** 可信度等级 */
export type CredibilityLevel = 
  | 'authoritative'  // 权威 (95-100)
  | 'reliable'       // 可靠 (70-94)
  | 'moderate'       // 一般 (40-69)
  | 'questionable'   // 存疑 (0-39)

/** 来源状态 */
export type SourceStatus = 'pending' | 'reading' | 'done' | 'skipped' | 'failed'

/** 信息来源 */
export interface ResearchSource {
  id: string
  url: string
  domain: string
  title: string
  type: SourceType
  credibility: number        // 0-100
  credibilityLevel: CredibilityLevel
  status: SourceStatus
  extractedFacts?: string[]  // 提取的关键事实
  timestamp?: string
}

/** 研究进度状态 */
export interface ResearchProgress {
  /** 当前阶段 */
  phase: ResearchPhase
  /** 阶段进度 (0-100) */
  phaseProgress: number
  /** 总体进度 (0-100) */
  overallProgress: number
  /** 搜索查询列表 */
  queries: SearchQuery[]
  /** 信息来源列表 */
  sources: ResearchSource[]
  /** 当前操作描述 */
  currentAction?: string
  /** 开始时间 */
  startedAt?: string
  /** 预计剩余时间 (秒) */
  estimatedTimeRemaining?: number
}

/** 可信度配置 */
export const CREDIBILITY_CONFIG: Record<CredibilityLevel, {
  label: string
  color: string
  bgColor: string
  minScore: number
}> = {
  authoritative: {
    label: '权威',
    color: '#00c853',
    bgColor: 'rgba(0, 200, 83, 0.1)',
    minScore: 95,
  },
  reliable: {
    label: '可靠',
    color: '#0066ff',
    bgColor: 'rgba(0, 102, 255, 0.1)',
    minScore: 70,
  },
  moderate: {
    label: '一般',
    color: '#ff9500',
    bgColor: 'rgba(255, 149, 0, 0.1)',
    minScore: 40,
  },
  questionable: {
    label: '存疑',
    color: '#ff3b30',
    bgColor: 'rgba(255, 59, 48, 0.1)',
    minScore: 0,
  },
}

/** 来源类型配置 */
export const SOURCE_TYPE_CONFIG: Record<SourceType, {
  label: string
  icon: string
}> = {
  academic: { label: '学术论文', icon: 'AcademicCapIcon' },
  report: { label: '行业报告', icon: 'DocumentChartBarIcon' },
  news: { label: '新闻资讯', icon: 'NewspaperIcon' },
  blog: { label: '博客文章', icon: 'PencilSquareIcon' },
  official: { label: '官方文档', icon: 'BuildingOfficeIcon' },
  social: { label: '社交媒体', icon: 'ChatBubbleLeftRightIcon' },
  unknown: { label: '未知', icon: 'QuestionMarkCircleIcon' },
}

/** 根据分数获取可信度等级 */
export function getCredibilityLevel(score: number): CredibilityLevel {
  if (score >= 95) return 'authoritative'
  if (score >= 70) return 'reliable'
  if (score >= 40) return 'moderate'
  return 'questionable'
}

/** 获取域名的 favicon URL */
export function getFaviconUrl(domain: string): string {
  return `https://www.google.com/s2/favicons?domain=${domain}&sz=32`
}

// ========================================
// 干预类型定义 (Intervention Types)
// ========================================

/** 干预类型 */
export type InterventionType =
  | 'add_focus'      // 追加关注点: "多关注企业应用案例"
  | 'skip_source'    // 跳过来源: "不要看 medium.com"
  | 'change_depth'   // 调整深度: "快速出结果就行"
  | 'add_query'      // 追加关键词: "也搜一下 CrewAI"
  | 'stop_reading'   // 停止阅读: "已经够了，开始写报告"
  | 'custom'         // 自定义指令

/** 干预指令 */
export interface ResearchIntervention {
  type: InterventionType
  content: string  // 具体内容
  timestamp?: string
}

/** 快捷干预按钮配置 */
export interface QuickInterventionButton {
  id: string
  type: InterventionType
  label: string
  content: string
  icon?: string
  /** 根据研究状态动态显示 */
  showWhen?: (progress: ResearchProgress) => boolean
}

/** 预定义的快捷干预按钮 */
export const QUICK_INTERVENTION_BUTTONS: QuickInterventionButton[] = [
  {
    id: 'focus_china',
    type: 'add_focus',
    label: '更关注中国市场',
    content: '请更多关注中国市场的数据和案例',
    showWhen: (p) => p.phase === 'searching' || p.phase === 'reading',
  },
  {
    id: 'less_blog',
    type: 'skip_source',
    label: '减少博客来源',
    content: '请减少博客文章来源，更多使用权威资料',
    showWhen: (p) => p.sources.filter(s => s.type === 'blog').length >= 2,
  },
  {
    id: 'speed_up',
    type: 'change_depth',
    label: '加快速度',
    content: '请加快研究速度，快速出结果即可',
    showWhen: (p) => p.phase !== 'writing',
  },
  {
    id: 'go_deeper',
    type: 'change_depth',
    label: '更深入研究',
    content: '请更深入研究，查找更多来源',
    showWhen: (p) => p.phase === 'searching' && p.sources.length < 5,
  },
  {
    id: 'start_writing',
    type: 'stop_reading',
    label: '开始写报告',
    content: '已经收集足够信息，请开始撰写报告',
    showWhen: (p) => p.phase === 'reading' && p.sources.filter(s => s.status === 'done').length >= 5,
  },
]

/** 干预类型配置 */
export const INTERVENTION_TYPE_CONFIG: Record<InterventionType, {
  label: string
  placeholder: string
  icon: string
}> = {
  add_focus: {
    label: '追加关注点',
    placeholder: '例如：请多关注企业应用案例',
    icon: 'Target',
  },
  skip_source: {
    label: '跳过来源',
    placeholder: '例如：不要看 medium.com',
    icon: 'EyeOff',
  },
  change_depth: {
    label: '调整深度',
    placeholder: '例如：快速出结果 / 更深入研究',
    icon: 'Sliders',
  },
  add_query: {
    label: '追加关键词',
    placeholder: '例如：也搜一下 CrewAI',
    icon: 'Search',
  },
  stop_reading: {
    label: '停止阅读',
    placeholder: '开始撰写报告',
    icon: 'FileText',
  },
  custom: {
    label: '自定义指令',
    placeholder: '输入您的指令...',
    icon: 'MessageSquare',
  },
}

// ========================================
// 引用类型定义 (Citation Types)
// ========================================

/** 引用来源信息 */
export interface CitationSource {
  url: string
  title: string
  domain: string
  publishDate?: string
  credibility: number  // 0-100
  credibilityLevel: CredibilityLevel
  type?: SourceType
}

/** 引用详情 */
export interface Citation {
  /** 引用序号 (如 1, 2, 3) */
  id: number
  /** 来源信息 */
  source: CitationSource
  /** 原文摘录 (短) */
  excerpt: string
  /** 更大范围的上下文 */
  excerptContext?: string
  /** 报告中引用此来源的文本 */
  claimText?: string
}

/** 带引用的报告 */
export interface ReportWithCitations {
  /** Markdown 内容 (带 [1] [2] 等引用标记) */
  markdown: string
  /** 引用列表 */
  citations: Citation[]
}
