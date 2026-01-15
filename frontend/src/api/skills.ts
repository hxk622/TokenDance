/**
 * Skill API 客户端
 *
 * 提供 Skill 发现、模板查询、场景预设等功能
 */

import { apiClient } from './client'

// ==================== 类型定义 ====================

export interface TemplateVariable {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select'
  required: boolean
  placeholder?: string
  options?: Array<{ label: string; value: string }>
  default?: string
}

export interface SkillTemplate {
  id: string
  skill_id: string
  name: string
  description: string
  prompt_template: string
  category: string
  tags: string[]
  variables: TemplateVariable[]
  example_input?: string
  example_output?: string
  icon: string
  popularity: number
  enabled: boolean
}

export interface ScenePreset {
  id: string
  name: string
  description: string
  template_ids: string[]
  recommended_skills: string[]
  category: string
  tags: string[]
  icon: string
  cover_image?: string
  color: string
  popularity: number
  enabled: boolean
}

export interface Skill {
  name: string
  display_name: string
  description: string
  version: string
  author: string
  tags: string[]
  allowed_tools: string[]
  max_iterations: number
  timeout: number
  enabled: boolean
  match_threshold: number
  priority: number
}

export interface SkillWithTemplates extends Skill {
  templates: SkillTemplate[]
}

export interface Category {
  id: string
  name: string
  template_count: number
  scene_count: number
}

export interface DiscoveryData {
  popular_templates: SkillTemplate[]
  popular_scenes: ScenePreset[]
  categories: Category[]
  total_templates: number
  total_scenes: number
}

export interface RenderTemplateResult {
  rendered_prompt: string
  skill_id: string
  template_id: string
}

// ==================== API 函数 ====================

export const skillsApi = {
  // ==================== Skill 相关 ====================

  /**
   * 获取所有 Skill 列表
   */
  async listSkills(params?: { tag?: string; enabled_only?: boolean }): Promise<Skill[]> {
    const response = await apiClient.get('/skills/skills', { params })
    return response.data
  },

  /**
   * 获取单个 Skill 详情（包含模板）
   */
  async getSkill(skillId: string): Promise<SkillWithTemplates> {
    const response = await apiClient.get(`/skills/skills/${skillId}`)
    return response.data
  },

  /**
   * 获取某个 Skill 的所有模板
   */
  async getSkillTemplates(skillId: string): Promise<SkillTemplate[]> {
    const response = await apiClient.get(`/skills/skills/${skillId}/templates`)
    return response.data
  },

  // ==================== 模板相关 ====================

  /**
   * 获取模板列表
   */
  async listTemplates(params?: {
    category?: string
    skill_id?: string
    search?: string
    limit?: number
  }): Promise<SkillTemplate[]> {
    const response = await apiClient.get('/skills/templates', { params })
    return response.data
  },

  /**
   * 获取热门模板
   */
  async getPopularTemplates(limit: number = 10): Promise<SkillTemplate[]> {
    const response = await apiClient.get('/skills/templates/popular', {
      params: { limit }
    })
    return response.data
  },

  /**
   * 获取单个模板详情
   */
  async getTemplate(templateId: string): Promise<SkillTemplate> {
    const response = await apiClient.get(`/skills/templates/${templateId}`)
    return response.data
  },

  /**
   * 渲染模板
   */
  async renderTemplate(
    templateId: string,
    variables: Record<string, string>
  ): Promise<RenderTemplateResult> {
    const response = await apiClient.post(`/skills/templates/${templateId}/render`, {
      variables
    })
    return response.data
  },

  // ==================== 场景预设相关 ====================

  /**
   * 获取场景预设列表
   */
  async listScenes(params?: {
    category?: string
    limit?: number
  }): Promise<ScenePreset[]> {
    const response = await apiClient.get('/skills/scenes', { params })
    return response.data
  },

  /**
   * 获取热门场景预设
   */
  async getPopularScenes(limit: number = 5): Promise<ScenePreset[]> {
    const response = await apiClient.get('/skills/scenes/popular', {
      params: { limit }
    })
    return response.data
  },

  /**
   * 获取单个场景预设详情
   */
  async getScene(sceneId: string): Promise<ScenePreset> {
    const response = await apiClient.get(`/skills/scenes/${sceneId}`)
    return response.data
  },

  /**
   * 获取场景预设包含的所有模板
   */
  async getSceneTemplates(sceneId: string): Promise<SkillTemplate[]> {
    const response = await apiClient.get(`/skills/scenes/${sceneId}/templates`)
    return response.data
  },

  // ==================== 发现页面 ====================

  /**
   * 获取发现页面数据
   */
  async getDiscoveryData(): Promise<DiscoveryData> {
    const response = await apiClient.get('/skills/discovery')
    return response.data
  },

  /**
   * 获取所有分类
   */
  async listCategories(): Promise<Category[]> {
    const response = await apiClient.get('/skills/categories')
    return response.data
  }
}

export default skillsApi
