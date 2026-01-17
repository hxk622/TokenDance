/**
 * 下一代渲染引擎类型定义
 * Next-Gen Rendering Engine Type Definitions
 */

import type { Component } from 'vue'

// ============================================================================
// 组件注册表类型
// ============================================================================

export interface RegisteredComponent {
  name: string
  component: Component
  category: 'chart' | 'widget' | 'scrolly' | 'custom'
  description?: string
}

export interface ComponentRegistry {
  register: (name: string, component: Component, options?: Partial<RegisteredComponent>) => void
  get: (name: string) => RegisteredComponent | undefined
  getAll: () => Map<string, RegisteredComponent>
  has: (name: string) => boolean
}

// ============================================================================
// 动态渲染器类型
// ============================================================================

export interface ParsedBlock {
  type: 'markdown' | 'component'
  content: string
  componentName?: string
  props?: Record<string, unknown>
  rawText?: string
}

export interface RenderContext {
  data?: Record<string, unknown>
  theme?: 'light' | 'dark'
  interactive?: boolean
}

// ============================================================================
// K线图表类型
// ============================================================================

export interface KLineDataItem {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
  turnover?: number
}

export interface KLineIndicatorConfig {
  name: string
  params?: number[]
  styles?: Record<string, unknown>
}

export type KLineChartPeriod = '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w' | '1M'

export interface KLineChartProps {
  data: KLineDataItem[]
  symbol?: string
  period?: KLineChartPeriod
  indicators?: KLineIndicatorConfig[]
  theme?: 'light' | 'dark'
  height?: number | string
  showVolume?: boolean
  showGrid?: boolean
  showCrosshair?: boolean
  showTooltip?: boolean
  locale?: 'zh-CN' | 'en-US'
}

// ============================================================================
// Scrollytelling 类型
// ============================================================================

export interface ScrollySectionConfig {
  id: string
  title?: string
  threshold?: number
  offset?: number
  animation?: 'fade' | 'slide' | 'scale' | 'none'
  duration?: number
}

export interface ScrollyState {
  activeSection: string | null
  progress: number
  direction: 'up' | 'down'
  sections: Map<string, { visible: boolean; ratio: number }>
}

export interface ScrollyContainerProps {
  sections: ScrollySectionConfig[]
  stickyContent?: boolean
  progressBar?: boolean
  onSectionChange?: (sectionId: string) => void
}

// ============================================================================
// 业务组件类型
// ============================================================================

export interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  change?: number
  changeType?: 'positive' | 'negative' | 'neutral'
  trend?: number[]
  description?: string
  icon?: string
  size?: 'sm' | 'md' | 'lg'
}

export interface ValuationTableProps {
  data: ValuationRow[]
  title?: string
  showComparison?: boolean
  highlightBest?: boolean
}

export interface ValuationRow {
  metric: string
  current: number | string
  industry?: number | string
  historical?: number | string
  rating?: 'undervalued' | 'fair' | 'overvalued'
  description?: string
}

export interface SourceCitationProps {
  sources: SourceItem[]
  citationStyle?: 'inline' | 'footnote' | 'sidebar'
  showReliability?: boolean
}

export interface SourceItem {
  id: string
  title: string
  url?: string
  author?: string
  date?: string
  reliability?: 'high' | 'medium' | 'low'
  snippet?: string
}

export interface ComparisonWidgetProps {
  items: ComparisonItem[]
  metrics: string[]
  highlightBest?: boolean
  showChart?: boolean
}

export interface ComparisonItem {
  name: string
  symbol?: string
  values: Record<string, number | string>
  highlight?: boolean
}

// ============================================================================
// 报告渲染类型
// ============================================================================

export interface ReportSection {
  id: string
  title: string
  type: 'narrative' | 'data' | 'chart' | 'comparison' | 'conclusion'
  content: string
  components?: EmbeddedComponent[]
  scrolly?: boolean
}

export interface EmbeddedComponent {
  type: string
  props: Record<string, unknown>
  position: 'inline' | 'block' | 'floating'
}

export interface ReportConfig {
  id: string
  title: string
  type: 'deep-research' | 'financial-analysis'
  sections: ReportSection[]
  metadata?: {
    createdAt: string
    updatedAt: string
    author?: string
    sources?: SourceItem[]
  }
}

// ============================================================================
// 图表联动类型
// ============================================================================

export interface ChartSyncConfig {
  enabled: boolean
  charts: string[]
  syncType: 'crosshair' | 'zoom' | 'both'
}

export interface ChartEvent {
  type: 'crosshair' | 'zoom' | 'click' | 'hover'
  chartId: string
  data: {
    timestamp?: number
    value?: number
    range?: { start: number; end: number }
  }
}
