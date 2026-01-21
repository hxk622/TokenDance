/**
 * Research API Client - 深度研究 API
 *
 * 提供深度研究功能的 API 调用：
 * - 启动研究任务
 * - 获取研究状态
 * - 获取研究报告
 * - 获取结构化发现
 * - 一键生成 PPT
 */
import axios from 'axios'

const API_BASE = '/api/v1/research'

// ==================== 类型定义 ====================

export type PPTStyle = 'business' | 'tech' | 'minimal' | 'academic' | 'creative'

export interface ResearchRequest {
  topic: string
  max_sources?: number
  include_screenshots?: boolean
}

export interface ResearchStatus {
  task_id: string
  status: 'pending' | 'searching' | 'reading' | 'synthesizing' | 'completed' | 'failed' | 'cancelled'
  progress: number
  phase: string
  sources_collected: number
  message?: string
}

export interface ResearchSource {
  url: string
  title: string
  snippet: string
  credibility: string
  key_findings: string[]
}

export interface ResearchReport {
  task_id: string
  topic: string
  report_markdown: string
  sources: ResearchSource[]
  generated_at: string
}

export interface ResearchFinding {
  title: string
  content: string
  importance: 'high' | 'medium' | 'low'
  source_urls: string[]
  tags: string[]
  sub_points: string[]
}

export interface DataPoint {
  label: string
  value: number | string
  type: string
  unit?: string
  context?: string
}

export interface Quote {
  text: string
  author?: string
  context?: string
}

export interface FindingsResponse {
  task_id: string
  topic: string
  summary: string
  key_findings: ResearchFinding[]
  data_points: DataPoint[]
  quotes: Quote[]
  sources_count: number
  research_duration_seconds: number
  can_generate_ppt: boolean
}

export interface GeneratePPTRequest {
  style?: PPTStyle
  author?: string
  include_sources?: boolean
  include_qa?: boolean
  max_slides?: number
}

export interface SlidePreview {
  index: number
  type: string
  title: string
  content_preview?: string
}

export interface GeneratePPTResponse {
  task_id: string
  ppt_id: string
  title: string
  slide_count: number
  estimated_duration: string
  style: string
  slides_preview: SlidePreview[]
  marp_markdown: string
  edit_url?: string
  preview_url?: string
}

// ==================== API 方法 ====================

export const researchApi = {
  /**
   * 启动研究任务
   */
  async startResearch(request: ResearchRequest): Promise<ResearchStatus> {
    const response = await axios.post(`${API_BASE}/start`, request)
    return response.data
  },

  /**
   * 获取研究状态
   */
  async getStatus(taskId: string): Promise<ResearchStatus> {
    const response = await axios.get(`${API_BASE}/${taskId}`)
    return response.data
  },

  /**
   * 获取研究报告
   */
  async getReport(taskId: string): Promise<ResearchReport> {
    const response = await axios.get(`${API_BASE}/${taskId}/report`)
    return response.data
  },

  /**
   * 获取结构化发现
   */
  async getFindings(taskId: string): Promise<FindingsResponse> {
    const response = await axios.get(`${API_BASE}/${taskId}/findings`)
    return response.data
  },

  /**
   * 一键生成 PPT
   */
  async generatePPT(taskId: string, options?: GeneratePPTRequest): Promise<GeneratePPTResponse> {
    const response = await axios.post(`${API_BASE}/${taskId}/generate-ppt`, options || {})
    return response.data
  },

  /**
   * 取消研究任务
   */
  async cancelResearch(taskId: string): Promise<{ message: string; task_id: string }> {
    const response = await axios.delete(`${API_BASE}/${taskId}`)
    return response.data
  },

  /**
   * 列出研究任务
   */
  async listTasks(status?: string, limit?: number): Promise<ResearchStatus[]> {
    const params = new URLSearchParams()
    if (status) params.append('status', status)
    if (limit) params.append('limit', limit.toString())
    const response = await axios.get(`${API_BASE}/?${params.toString()}`)
    return response.data
  },
}

export default researchApi
