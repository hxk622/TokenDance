/**
 * 信任配置 API 客户端
 */
import apiClient from './client'

// ==================== 类型定义 ====================

export interface TrustConfig {
  id: string
  workspace_id: string
  auto_approve_level: string
  pre_authorized_operations: string[]
  blacklisted_operations: string[]
  enabled: boolean
  total_auto_approved: number
  total_manual_approved: number
  total_rejected: number
  created_at: string
  updated_at: string
}

export interface TrustConfigUpdate {
  auto_approve_level?: string
  pre_authorized_operations?: string[]
  blacklisted_operations?: string[]
  enabled?: boolean
}

export interface SessionGrantRequest {
  operation_category: string
}

export interface TrustAuditLog {
  id: string
  workspace_id: string
  session_id: string | null
  tool_name: string
  operation_category: string
  risk_level: string
  decision: string
  decision_reason: string | null
  operation_summary: string | null
  user_feedback: string | null
  remember_choice: boolean
  created_at: string
}

export interface TrustAuditLogList {
  items: TrustAuditLog[]
  total: number
  page: number
  page_size: number
}

export interface RiskLevelInfo {
  level: string
  description: string
  default_behavior: string
}

export interface OperationCategoryInfo {
  category: string
  description: string
  default_risk_level: string
}

export interface TrustMetadata {
  risk_levels: RiskLevelInfo[]
  operation_categories: OperationCategoryInfo[]
}

// ==================== API 方法 ====================

export const trustApi = {
  /**
   * 获取工作空间的信任配置
   */
  async getConfig(workspaceId: string): Promise<TrustConfig> {
    const response = await apiClient.get<TrustConfig>(
      `/api/v1/trust/workspaces/${workspaceId}`
    )
    return response.data
  },

  /**
   * 更新工作空间的信任配置
   */
  async updateConfig(
    workspaceId: string,
    update: TrustConfigUpdate
  ): Promise<TrustConfig> {
    const response = await apiClient.put<TrustConfig>(
      `/api/v1/trust/workspaces/${workspaceId}`,
      update
    )
    return response.data
  },

  /**
   * 授予会话级临时权限
   */
  async grantSessionPermission(
    sessionId: string,
    workspaceId: string,
    operationCategory: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post(
      `/api/v1/trust/sessions/${sessionId}/grant`,
      { operation_category: operationCategory },
      { params: { workspace_id: workspaceId } }
    )
    return response.data
  },

  /**
   * 清除会话级授权
   */
  async clearSessionGrants(
    sessionId: string,
    workspaceId: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.delete(
      `/api/v1/trust/sessions/${sessionId}/grants`,
      { params: { workspace_id: workspaceId } }
    )
    return response.data
  },

  /**
   * 获取审计日志列表
   */
  async getAuditLogs(
    workspaceId: string,
    options?: {
      page?: number
      page_size?: number
      session_id?: string
      decision?: string
    }
  ): Promise<TrustAuditLogList> {
    const response = await apiClient.get<TrustAuditLogList>(
      `/api/v1/trust/workspaces/${workspaceId}/audit`,
      { params: options }
    )
    return response.data
  },

  /**
   * 获取信任系统元数据
   */
  async getMetadata(): Promise<TrustMetadata> {
    const response = await apiClient.get<TrustMetadata>(
      '/api/v1/trust/metadata'
    )
    return response.data
  },
}

export default trustApi
