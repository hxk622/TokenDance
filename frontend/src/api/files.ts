/**
 * Files API Client - 文件索引与搜索
 *
 * 提供文件索引、语义搜索、目录树等功能的 API 封装
 */
import apiClient from './client'

// ==================== Types ====================

export interface IndexRequest {
  path: string
  extensions?: string[]
}

export interface SearchRequest {
  query: string
  top_k?: number
  language?: string
}

export interface FileInfo {
  path: string
  name: string
  extension: string
  size: number
  language: string | null
  modified_at: string
}

export interface SearchResult {
  content: string
  file_path: string
  start_line: number
  end_line: number
  score: number
  language: string | null
}

export interface IndexStats {
  indexed_files: number
  total_size: number
  languages: Record<string, number>
  indexed_at: string | null
}

export interface DirectoryTreeNode {
  name: string
  type: 'directory' | 'file'
  language?: string | null
  size?: number | null
  children?: DirectoryTreeNode[]
  truncated?: boolean
}

export interface SymbolInfo {
  name: string
  type: string
  line: number
  end_line?: number
  signature?: string
  docstring?: string
}

export interface FileAnalysis {
  path: string
  language: string
  line_count: number
  complexity: number
  symbols: SymbolInfo[]
  imports: string[]
}

export interface SymbolSearchResult {
  file_path: string
  symbol: {
    name: string
    type: string
    line: number
    signature?: string
  }
}

// ==================== API Functions ====================

export const filesApi = {
  /**
   * 索引目录
   */
  async indexDirectory(request: IndexRequest): Promise<IndexStats> {
    const response = await apiClient.post<IndexStats>('/api/v1/files/index', request)
    return response.data
  },

  /**
   * 增量索引
   */
  async incrementalIndex(path: string): Promise<{ updated_count: number; files: string[] }> {
    const response = await apiClient.post<{ updated_count: number; files: string[] }>(
      `/api/v1/files/index/incremental?path=${encodeURIComponent(path)}`
    )
    return response.data
  },

  /**
   * 语义搜索
   */
  async search(request: SearchRequest): Promise<SearchResult[]> {
    const response = await apiClient.post<SearchResult[]>('/api/v1/files/search', request)
    return response.data
  },

  /**
   * 获取目录树
   */
  async getDirectoryTree(path: string, maxDepth: number = 3): Promise<DirectoryTreeNode> {
    const params = new URLSearchParams({
      path,
      max_depth: maxDepth.toString(),
    })
    const response = await apiClient.get<DirectoryTreeNode>(`/api/v1/files/tree?${params}`)
    return response.data
  },

  /**
   * 获取索引统计
   */
  async getStats(path: string): Promise<IndexStats> {
    const response = await apiClient.get<IndexStats>(
      `/api/v1/files/stats?path=${encodeURIComponent(path)}`
    )
    return response.data
  },

  /**
   * 分析单个文件
   */
  async analyzeFile(filePath: string): Promise<FileAnalysis> {
    const response = await apiClient.get<FileAnalysis>(
      `/api/v1/files/analyze/${encodeURIComponent(filePath)}`
    )
    return response.data
  },

  /**
   * 搜索符号
   */
  async searchSymbol(name: string, path: string): Promise<SymbolSearchResult[]> {
    const params = new URLSearchParams({ name, path })
    const response = await apiClient.get<SymbolSearchResult[]>(
      `/api/v1/files/search/symbol?${params}`
    )
    return response.data
  },

  /**
   * 获取语言统计
   */
  async getLanguageStats(path: string): Promise<Record<string, number>> {
    const response = await apiClient.get<Record<string, number>>(
      `/api/v1/files/languages?path=${encodeURIComponent(path)}`
    )
    return response.data
  },
}

export default filesApi
