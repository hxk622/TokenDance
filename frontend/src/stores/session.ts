/**
 * Session store using Pinia
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sessionApi, type Session, type SessionCreate, type SessionUpdate } from '@/api/session'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const currentSession = ref<Session | null>(null)
  const currentWorkspaceId = ref<string | null>(localStorage.getItem('current_workspace_id'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)
  const limit = ref(20)
  const offset = ref(0)

  // Computed
  const activeSessions = computed(() => 
    sessions.value.filter(s => s.status === 'ACTIVE')
  )
  const completedSessions = computed(() => 
    sessions.value.filter(s => s.status === 'COMPLETED')
  )
  const hasMore = computed(() => 
    offset.value + limit.value < total.value
  )

  /**
   * Load sessions for current workspace
   */
  async function loadSessions(workspaceId: string, reset: boolean = true) {
    if (reset) {
      offset.value = 0
      sessions.value = []
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      const result = await sessionApi.listSessions(
        workspaceId,
        limit.value,
        offset.value
      )
      
      if (reset) {
        sessions.value = result.items
      } else {
        sessions.value = [...sessions.value, ...result.items]
      }
      
      total.value = result.total
      limit.value = result.limit
      offset.value = result.offset + result.items.length
      
      return result
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load sessions'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Create a new session
   */
  async function createSession(data: SessionCreate) {
    isLoading.value = true
    error.value = null
    
    try {
      const session = await sessionApi.createSession(data)
      sessions.value.unshift(session)
      total.value += 1
      
      // Set as current session
      currentSession.value = session
      
      return session
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to create session'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Update a session
   */
  async function updateSession(sessionId: string, data: SessionUpdate) {
    try {
      const updated = await sessionApi.updateSession(sessionId, data)
      
      // Update in list
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = updated
      }
      
      // Update current session if it's the one being updated
      if (currentSession.value?.id === sessionId) {
        currentSession.value = updated
      }
      
      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to update session'
      throw err
    }
  }

  /**
   * Delete a session
   */
  async function deleteSession(sessionId: string) {
    try {
      await sessionApi.deleteSession(sessionId)
      
      // Remove from list
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      total.value -= 1
      
      // Clear current session if it's the one being deleted
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
      }
      
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to delete session'
      throw err
    }
  }

  /**
   * Mark session as completed
   */
  async function completeSession(sessionId: string) {
    try {
      const completed = await sessionApi.completeSession(sessionId)
      
      // Update in list
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = completed
      }
      
      // Update current session if it's the one being completed
      if (currentSession.value?.id === sessionId) {
        currentSession.value = completed
      }
      
      return completed
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to complete session'
      throw err
    }
  }

  /**
   * Set current session
   */
  function setCurrentSession(session: Session | null) {
    currentSession.value = session
    if (session) {
      localStorage.setItem('current_session_id', session.id)
    } else {
      localStorage.removeItem('current_session_id')
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
    
    // Clear sessions when workspace changes
    sessions.value = []
    currentSession.value = null
    total.value = 0
    offset.value = 0
  }

  /**
   * Load more sessions (pagination)
   */
  async function loadMore() {
    if (isLoading.value || !hasMore.value || !currentWorkspaceId.value) {
      return
    }
    
    await loadSessions(currentWorkspaceId.value, false)
  }

  /**
   * Refresh current session
   */
  async function refreshCurrentSession() {
    if (!currentSession.value) {
      return
    }
    
    try {
      const updated = await sessionApi.getSession(currentSession.value.id, true)
      currentSession.value = updated
      
      // Update in list
      const index = sessions.value.findIndex(s => s.id === updated.id)
      if (index !== -1) {
        sessions.value[index] = updated
      }
      
      return updated
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to refresh session'
      throw err
    }
  }

  /**
   * Initialize from localStorage
   */
  function initialize() {
    const sessionId = localStorage.getItem('current_session_id')
    if (sessionId) {
      // Try to find session in list
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        currentSession.value = session
      }
    }
  }

  return {
    // State
    sessions,
    currentSession,
    currentWorkspaceId,
    isLoading,
    error,
    total,
    limit,
    offset,
    
    // Computed
    activeSessions,
    completedSessions,
    hasMore,
    
    // Actions
    loadSessions,
    createSession,
    updateSession,
    deleteSession,
    completeSession,
    setCurrentSession,
    setCurrentWorkspace,
    loadMore,
    refreshCurrentSession,
    initialize
  }
})
