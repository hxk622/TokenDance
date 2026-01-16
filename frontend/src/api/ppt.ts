/**
 * PPT API Client - PPT 生成与编辑 API
 *
 * 提供 PPT 功能的 API 调用：
 * - 获取 PPT 大纲
 * - 更新幻灯片内容
 * - 渲染预览
 * - 导出 PDF/HTML/PPTX
 */
import axios from 'axios'

const API_BASE = '/api/v1/ppt'

// ==================== 类型定义 ====================

export type SlideType =
  | 'title'
  | 'toc'
  | 'section'
  | 'content'
  | 'data'
  | 'image'
  | 'quote'
  | 'comparison'
  | 'timeline'
  | 'conclusion'
  | 'qa'
  | 'thank_you'

export type PPTStyle = 'business' | 'tech' | 'minimal' | 'academic' | 'creative'

export type ChartType = 'bar' | 'line' | 'pie' | 'doughnut' | 'radar' | 'scatter'

export type ExportFormat = 'pdf' | 'html' | 'pptx'

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
  }[]
}

export interface SlideContent {
  id: string
  type: SlideType
  title: string
  subtitle?: string
  points?: string[]
  content?: string
  notes?: string
  chart_type?: ChartType
  chart_data?: ChartData
  mermaid_code?: string
  image_url?: string
  image_caption?: string
  layout?: string
}

export interface PPTOutline {
  id: string
  title: string
  subtitle?: string
  author?: string
  date: string
  style: PPTStyle
  theme: string
  slides: SlideContent[]
  source_content?: string
  estimated_duration?: string
  created_at: string
}

export interface UpdateSlideRequest {
  title?: string
  subtitle?: string
  points?: string[]
  content?: string
  notes?: string
  type?: SlideType
  layout?: string
}

export interface RenderRequest {
  format: 'html' | 'preview'
  theme?: string
}

export interface RenderResponse {
  html: string
  css?: string
}

export interface ExportRequest {
  format: ExportFormat
  filename?: string
}

export interface ExportResponse {
  download_url: string
  filename: string
  format: string
  size_bytes: number
}

export interface AddSlideRequest {
  type: SlideType
  title: string
  after_index?: number
}

// ==================== API 方法 ====================

export const pptApi = {
  /**
   * 获取 PPT 大纲
   */
  async getOutline(pptId: string): Promise<PPTOutline> {
    const response = await axios.get(`${API_BASE}/${pptId}`)
    return response.data
  },

  /**
   * 更新 PPT 元数据
   */
  async updateOutline(
    pptId: string,
    data: { title?: string; subtitle?: string; author?: string; style?: PPTStyle }
  ): Promise<PPTOutline> {
    const response = await axios.patch(`${API_BASE}/${pptId}`, data)
    return response.data
  },

  /**
   * 获取单个幻灯片
   */
  async getSlide(pptId: string, slideIndex: number): Promise<SlideContent> {
    const response = await axios.get(`${API_BASE}/${pptId}/slides/${slideIndex}`)
    return response.data
  },

  /**
   * 更新单个幻灯片
   */
  async updateSlide(
    pptId: string,
    slideIndex: number,
    data: UpdateSlideRequest
  ): Promise<SlideContent> {
    const response = await axios.patch(`${API_BASE}/${pptId}/slides/${slideIndex}`, data)
    return response.data
  },

  /**
   * 添加新幻灯片
   */
  async addSlide(pptId: string, data: AddSlideRequest): Promise<SlideContent> {
    const response = await axios.post(`${API_BASE}/${pptId}/slides`, data)
    return response.data
  },

  /**
   * 删除幻灯片
   */
  async deleteSlide(pptId: string, slideIndex: number): Promise<void> {
    await axios.delete(`${API_BASE}/${pptId}/slides/${slideIndex}`)
  },

  /**
   * 重新排序幻灯片
   */
  async reorderSlides(pptId: string, fromIndex: number, toIndex: number): Promise<PPTOutline> {
    const response = await axios.post(`${API_BASE}/${pptId}/slides/reorder`, {
      from_index: fromIndex,
      to_index: toIndex,
    })
    return response.data
  },

  /**
   * 渲染预览
   */
  async renderPreview(pptId: string, theme?: string): Promise<RenderResponse> {
    const response = await axios.post(`${API_BASE}/${pptId}/render`, {
      format: 'preview',
      theme,
    })
    return response.data
  },

  /**
   * 获取 Marp Markdown
   */
  async getMarpMarkdown(pptId: string): Promise<string> {
    const response = await axios.get(`${API_BASE}/${pptId}/markdown`)
    return response.data.markdown
  },

  /**
   * 导出 PPT
   */
  async exportPPT(pptId: string, format: ExportFormat, filename?: string): Promise<ExportResponse> {
    const response = await axios.post(`${API_BASE}/${pptId}/export`, {
      format,
      filename,
    })
    return response.data
  },

  /**
   * 获取可用主题列表
   */
  async getThemes(): Promise<{ id: string; name: string; preview_url: string }[]> {
    const response = await axios.get(`${API_BASE}/themes`)
    return response.data
  },

  /**
   * 从研究生成 PPT（快捷方法）
   */
  async generateFromResearch(
    taskId: string,
    options?: {
      style?: PPTStyle
      author?: string
      max_slides?: number
    }
  ): Promise<PPTOutline> {
    const response = await axios.post(`/api/v1/research/${taskId}/generate-ppt`, options || {})
    // 返回完整大纲
    const pptId = response.data.ppt_id
    return this.getOutline(pptId)
  },
}

// ==================== Layered PPT API (Phase 2) ====================

export type LayeredSlideStyle = 
  | 'hero_title' 
  | 'section_header' 
  | 'visual_impact' 
  | 'minimal_clean' 
  | 'tech_modern'

export interface LayeredStyleInfo {
  id: LayeredSlideStyle
  name: string
  description: string
  preview_url?: string
}

export interface LayeredSlideRequest {
  style: LayeredSlideStyle
  title: string
  subtitle?: string
  body?: string
  accent_color?: string
  base_color?: string
  title_color?: string
  subtitle_color?: string
}

export interface LayeredPresentationRequest {
  slides: LayeredSlideRequest[]
  filename?: string
}

export interface BackgroundStyleCategory {
  id: string
  name: string
}

export interface BackgroundStyles {
  gradient: BackgroundStyleCategory[]
  geometric: BackgroundStyleCategory[]
  abstract: BackgroundStyleCategory[]
}

export const layeredPptApi = {
  /**
   * 获取可用的分层样式列表
   */
  async getStyles(): Promise<LayeredStyleInfo[]> {
    const response = await axios.get(`${API_BASE}/layered/styles`)
    return response.data
  },

  /**
   * 获取所有背景样式
   */
  async getBackgroundStyles(): Promise<BackgroundStyles> {
    const response = await axios.get(`${API_BASE}/layered/backgrounds`)
    return response.data
  },

  /**
   * 生成分层 PPT 并下载
   */
  async generateAndDownload(request: LayeredPresentationRequest): Promise<void> {
    const response = await axios.post(`${API_BASE}/layered/generate`, request, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = request.filename || 'presentation.pptx'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  },

  /**
   * 预览单个幻灯片背景
   */
  async previewSlide(request: LayeredSlideRequest): Promise<string> {
    const response = await axios.post(`${API_BASE}/layered/preview`, request, {
      responseType: 'blob',
    })
    
    const blob = new Blob([response.data], { type: 'image/png' })
    return URL.createObjectURL(blob)
  },
}

export default pptApi
