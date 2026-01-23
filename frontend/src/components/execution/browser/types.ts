/**
 * Browser Operation & TimeLapse Types
 * 
 * 用于浏览器操作日志和时光长廊组件
 */

export type FrameType = 
  | 'page_load'      // 页面加载
  | 'interaction'    // 交互操作
  | 'extract'        // 内容提取
  | 'error'          // 错误
  | 'search'         // 搜索结果
  | 'milestone'      // 里程碑

export interface BrowserOperation {
  id: string
  type: 'open' | 'navigate' | 'click' | 'fill' | 'snapshot' | 'screenshot' | 'close'
  url?: string           // 导航 URL
  target?: string        // URL 或 ref
  value?: string         // 填充的值
  status: 'pending' | 'running' | 'success' | 'error'
  result?: string
  error?: string
  duration?: number
  timestamp: string
  screenshotPath?: string
}

export interface TimeLapseFrame {
  id: string
  sessionId: string
  frameType: FrameType
  timestamp: string
  timestampMs: number    // 相对会话开始的毫秒数
  
  // 描述
  title: string
  description: string
  
  // 视觉数据
  screenshotPath?: string
  snapshotSummary?: string
  
  // 上下文
  url?: string
  action?: string
}

export interface TimeLapseSession {
  sessionId: string
  taskId: string
  title: string
  createdAt: string
  totalDurationMs: number
  frameCount: number
  frames: TimeLapseFrame[]
}

export interface TimeLapsePlayback {
  sessionId: string
  title: string
  totalDurationMs: number
  frames: TimeLapseFrame[]
}

// 操作类型配置
export const OPERATION_CONFIG: Record<string, {
  icon: string
  label: string
  color: string
}> = {
  open: {
    icon: 'globe',
    label: '打开页面',
    color: 'text-blue-400',
  },
  navigate: {
    icon: 'arrow-right',
    label: '导航',
    color: 'text-cyan-400',
  },
  click: {
    icon: 'cursor-click',
    label: '点击',
    color: 'text-green-400',
  },
  fill: {
    icon: 'pencil',
    label: '填写',
    color: 'text-cyan-400',
  },
  snapshot: {
    icon: 'camera',
    label: '快照',
    color: 'text-amber-400',
  },
  screenshot: {
    icon: 'photo',
    label: '截图',
    color: 'text-pink-400',
  },
  close: {
    icon: 'x-circle',
    label: '关闭',
    color: 'text-gray-400',
  },
}

// 帧类型配置
export const FRAME_TYPE_CONFIG: Record<FrameType, {
  icon: string
  label: string
  bgColor: string
}> = {
  page_load: {
    icon: 'globe',
    label: '页面加载',
    bgColor: 'bg-blue-500/20',
  },
  interaction: {
    icon: 'cursor-click',
    label: '交互操作',
    bgColor: 'bg-green-500/20',
  },
  extract: {
    icon: 'document-text',
    label: '内容提取',
    bgColor: 'bg-cyan-500/20',
  },
  error: {
    icon: 'exclamation-circle',
    label: '错误',
    bgColor: 'bg-red-500/20',
  },
  search: {
    icon: 'search',
    label: '搜索结果',
    bgColor: 'bg-amber-500/20',
  },
  milestone: {
    icon: 'flag',
    label: '里程碑',
    bgColor: 'bg-emerald-500/20',
  },
}
