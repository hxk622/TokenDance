/**
 * Project store - Project-First architecture state management
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectApi } from '@/api/project'
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  Conversation,
  ConversationCreate,
  ProjectStatus,
  ProjectType,
  SelectionContext,
  ProjectContextResponse,
} from '@/types/project'

export const useProjectStore = defineStore('project', () => {
  // ============ State ============

  // Project list
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const currentWorkspaceId = ref<string | null>(
    localStorage.getItem('current_workspace_id')
  )

  // Conversations in current project
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)

  // Loading & error states
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Pagination
  const total = ref(0)
  const limit = ref(20)
  const offset = ref(0)

  // Context (for display)
  const projectContext = ref<ProjectContextResponse | null>(null)

  // ============ Computed ============

  const activeProjects = computed(() =>
    projects.value.filter(
      (p) => p.status === 'draft' || p.status === 'in_progress'
    )
  )

  const completedProjects = computed(() =>
    projects.value.filter((p) => p.status === 'completed')
  )

  const hasMore = computed(() => offset.value + limit.value < total.value)

  const activeConversations = computed(() =>
    conversations.value.filter((c) => c.status === 'active')
  )

  // ============ Project Actions ============

  /**
   * Load projects for current workspace
   */
  async function loadProjects(
    workspaceId: string,
    reset: boolean = true,
    status?: ProjectStatus,
    projectType?: ProjectType
  ) {
    if (reset) {
      offset.value = 0
      projects.value = []
    }

    isLoading.value = true
    error.value = null

    try {
      const result = await projectApi.listProjects(
        workspaceId,
        limit.value,
        offset.value,
        status,
        projectType
      )

      if (reset) {
        projects.value = result.items
      } else {
        projects.value = [...projects.value, ...result.items]
      }

      total.value = result.total
      limit.value = result.limit
      offset.value = result.offset + result.items.length

      return result
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to load projects'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new project
   */
  async function createProject(data: ProjectCreate) {
    isLoading.value = true
    error.value = null

    try {
      const project = await projectApi.createProject(data)
      projects.value.unshift(project)
      total.value += 1

      // Set as current project
      setCurrentProject(project)

      return project
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to create project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a project
   */
  async function updateProject(projectId: string, data: ProjectUpdate) {
    try {
      const updated = await projectApi.updateProject(projectId, data)

      // Update in list
      const index = projects.value.findIndex((p) => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = updated
      }

      // Update current project if it's the one being updated
      if (currentProject.value?.id === projectId) {
        currentProject.value = updated
      }

      return updated
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to update project'
      throw err
    }
  }

  /**
   * Archive a project
   */
  async function archiveProject(projectId: string) {
    try {
      await projectApi.archiveProject(projectId)

      // Update status in list
      const index = projects.value.findIndex((p) => p.id === projectId)
      if (index !== -1) {
        projects.value[index].status = 'archived'
      }

      // Clear current project if it's the one being archived
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
        clearProjectState()
      }

      return true
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to archive project'
      throw err
    }
  }

  /**
   * Delete a project (hard delete)
   */
  async function deleteProject(projectId: string) {
    try {
      await projectApi.deleteProject(projectId)

      // Remove from list
      projects.value = projects.value.filter((p) => p.id !== projectId)
      total.value -= 1

      // Clear current project if it's the one being deleted
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
        clearProjectState()
      }

      return true
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to delete project'
      throw err
    }
  }

  // ============ Conversation Actions ============

  /**
   * Load conversations for current project
   */
  async function loadConversations(projectId: string) {
    try {
      const result = await projectApi.listConversations(projectId)
      conversations.value = result.items

      // Set the latest active conversation as current
      const active = result.items.find((c) => c.status === 'active')
      if (active) {
        currentConversation.value = active
      }

      return result
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to load conversations'
      throw err
    }
  }

  /**
   * Create a new conversation
   */
  async function createConversation(
    projectId: string,
    data?: ConversationCreate
  ) {
    try {
      const conversation = await projectApi.createConversation(projectId, data)
      conversations.value.unshift(conversation)
      currentConversation.value = conversation

      // Update project conversation count
      if (currentProject.value?.id === projectId) {
        currentProject.value.conversation_count += 1
      }

      return conversation
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to create conversation'
      throw err
    }
  }

  // ============ Context Actions ============

  /**
   * Load project context
   */
  async function loadContext(projectId: string) {
    try {
      const context = await projectApi.getContext(projectId)
      projectContext.value = context
      return context
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to load context'
      throw err
    }
  }

  /**
   * Add a decision to context
   */
  async function addDecision(decision: string, reason?: string) {
    if (!currentProject.value) return

    try {
      const result = await projectApi.addDecision(
        currentProject.value.id,
        decision,
        reason
      )
      // Refresh context
      await loadContext(currentProject.value.id)
      return result
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to add decision'
      throw err
    }
  }

  /**
   * Add a failure to context (Keep the Failures)
   */
  async function addFailure(
    failureType: string,
    message: string,
    learning?: string
  ) {
    if (!currentProject.value) return

    try {
      const result = await projectApi.addFailure(
        currentProject.value.id,
        failureType,
        message,
        learning
      )
      // Refresh context
      await loadContext(currentProject.value.id)
      return result
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to add failure'
      throw err
    }
  }

  /**
   * Add a finding to context
   */
  async function addFinding(finding: string, source?: string) {
    if (!currentProject.value) return

    try {
      const result = await projectApi.addFinding(
        currentProject.value.id,
        finding,
        source
      )
      // Refresh context
      await loadContext(currentProject.value.id)
      return result
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to add finding'
      throw err
    }
  }

  // ============ Chat Actions ============

  /**
   * Send a chat message
   * Note: This is a placeholder. Will integrate with SSE streaming later.
   */
  async function sendMessage(
    message: string,
    selection?: SelectionContext
  ) {
    if (!currentProject.value) {
      throw new Error('No current project')
    }

    try {
      const response = await projectApi.chat(currentProject.value.id, {
        message,
        conversation_id: currentConversation.value?.id,
        selection,
      })

      // Update current conversation if returned
      if (response.conversation_id && !currentConversation.value) {
        await loadConversations(currentProject.value.id)
      }

      return response
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } }
      error.value = e.response?.data?.detail || 'Failed to send message'
      throw err
    }
  }

  // ============ State Management ============

  /**
   * Set current project and load its data
   */
  async function setCurrentProject(project: Project | null) {
    currentProject.value = project

    if (project) {
      localStorage.setItem('current_project_id', project.id)

      // Load conversations and context
      await Promise.all([
        loadConversations(project.id),
        loadContext(project.id),
      ])
    } else {
      localStorage.removeItem('current_project_id')
      clearProjectState()
    }
  }

  /**
   * Set current workspace
   */
  function setCurrentWorkspace(workspaceId: string | null) {
    currentWorkspaceId.value = workspaceId
    if (workspaceId) {
      localStorage.setItem('current_workspace_id', workspaceId)
    } else {
      localStorage.removeItem('current_workspace_id')
    }

    // Clear project state when workspace changes
    projects.value = []
    currentProject.value = null
    total.value = 0
    offset.value = 0
    clearProjectState()
  }

  /**
   * Clear project-specific state
   */
  function clearProjectState() {
    conversations.value = []
    currentConversation.value = null
    projectContext.value = null
  }

  /**
   * Load more projects (pagination)
   */
  async function loadMore() {
    if (isLoading.value || !hasMore.value || !currentWorkspaceId.value) {
      return
    }

    await loadProjects(currentWorkspaceId.value, false)
  }

  /**
   * Initialize from localStorage
   */
  async function initialize() {
    const projectId = localStorage.getItem('current_project_id')
    if (projectId && currentWorkspaceId.value) {
      try {
        const project = await projectApi.getProject(projectId)
        await setCurrentProject(project)
      } catch {
        // Project not found, clear localStorage
        localStorage.removeItem('current_project_id')
      }
    }
  }

  /**
   * Quick create project from intent (for quick tasks)
   */
  async function quickCreate(intent: string) {
    if (!currentWorkspaceId.value) {
      throw new Error('No workspace selected')
    }

    return createProject({
      workspace_id: currentWorkspaceId.value,
      intent,
      project_type: 'quick_task',
    })
  }

  return {
    // State
    projects,
    currentProject,
    currentWorkspaceId,
    conversations,
    currentConversation,
    projectContext,
    isLoading,
    error,
    total,
    limit,
    offset,

    // Computed
    activeProjects,
    completedProjects,
    hasMore,
    activeConversations,

    // Project Actions
    loadProjects,
    createProject,
    updateProject,
    archiveProject,
    deleteProject,

    // Conversation Actions
    loadConversations,
    createConversation,

    // Context Actions
    loadContext,
    addDecision,
    addFailure,
    addFinding,

    // Chat Actions
    sendMessage,

    // State Management
    setCurrentProject,
    setCurrentWorkspace,
    clearProjectState,
    loadMore,
    initialize,
    quickCreate,
  }
})
