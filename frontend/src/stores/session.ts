/**
 * Session Store - manages session state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sessionApi, type Session, type SessionDetail, type Message, type Artifact } from '@/api/session'

export const useSessionStore = defineStore('session', () => {
  // State
  const sessions = ref<Session[]>([])
  const currentSession = ref<SessionDetail | null>(null)
  const messages = ref<Message[]>([])
  const artifacts = ref<Artifact[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const activeSessions = computed(() => 
    sessions.value.filter(s => s.status === 'active')
  )

  const hasCurrentSession = computed(() => currentSession.value !== null)

  // Actions
  async function fetchSessions(workspaceId: string) {
    loading.value = true
    error.value = null
    
    try {
      const result = await sessionApi.list({ workspace_id: workspaceId })
      sessions.value = result.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch sessions'
    } finally {
      loading.value = false
    }
  }

  async function createSession(workspaceId: string, title?: string, skillId?: string) {
    loading.value = true
    error.value = null
    
    try {
      const session = await sessionApi.create({
        workspace_id: workspaceId,
        title,
        skill_id: skillId,
      })
      sessions.value.unshift(session)
      await selectSession(session.id)
      return session
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create session'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectSession(sessionId: string) {
    loading.value = true
    error.value = null
    
    try {
      const session = await sessionApi.get(sessionId, true) as SessionDetail
      currentSession.value = session
      
      // Fetch messages and artifacts
      const [msgResult, artResult] = await Promise.all([
        sessionApi.getMessages(sessionId),
        sessionApi.getArtifacts(sessionId),
      ])
      
      messages.value = msgResult.items
      artifacts.value = artResult.items
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to load session'
    } finally {
      loading.value = false
    }
  }

  async function updateSessionTitle(sessionId: string, title: string) {
    try {
      const updated = await sessionApi.update(sessionId, { title })
      
      // Update in list
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = updated
      }
      
      // Update current if same
      if (currentSession.value?.id === sessionId) {
        currentSession.value = { ...currentSession.value, title }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update session'
    }
  }

  async function deleteSession(sessionId: string) {
    try {
      await sessionApi.delete(sessionId)
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value = null
        messages.value = []
        artifacts.value = []
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete session'
    }
  }

  async function completeSession(sessionId: string) {
    try {
      const updated = await sessionApi.complete(sessionId)
      
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        sessions.value[index] = updated
      }
      
      if (currentSession.value?.id === sessionId) {
        currentSession.value = { ...currentSession.value, status: 'completed' }
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to complete session'
    }
  }

  // Message helpers
  function addMessage(message: Message) {
    messages.value.push(message)
    
    // Update current session message count
    if (currentSession.value) {
      currentSession.value.message_count = messages.value.length
    }
  }

  function updateLastMessage(updates: Partial<Message>) {
    const lastIndex = messages.value.length - 1
    if (lastIndex >= 0) {
      messages.value[lastIndex] = {
        ...messages.value[lastIndex],
        ...updates,
      }
    }
  }

  function clearMessages() {
    messages.value = []
  }

  // Artifact helpers
  function addArtifact(artifact: Artifact) {
    artifacts.value.unshift(artifact)
  }

  function clearCurrentSession() {
    currentSession.value = null
    messages.value = []
    artifacts.value = []
  }

  return {
    // State
    sessions,
    currentSession,
    messages,
    artifacts,
    loading,
    error,
    
    // Getters
    activeSessions,
    hasCurrentSession,
    
    // Actions
    fetchSessions,
    createSession,
    selectSession,
    updateSessionTitle,
    deleteSession,
    completeSession,
    addMessage,
    updateLastMessage,
    clearMessages,
    addArtifact,
    clearCurrentSession,
  }
})
