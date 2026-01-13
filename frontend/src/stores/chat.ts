/**
 * Chat Store - manages chat streaming state
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Citation } from '@/api/session'

export type ChatStatus = 'idle' | 'thinking' | 'tool_calling' | 'streaming' | 'waiting_confirm' | 'error'

export interface PendingToolCall {
  id: string
  name: string
  args: Record<string, any>
  status: 'pending' | 'running' | 'success' | 'error' | 'cancelled'
  result?: string
  error?: string
}

export interface PendingConfirmation {
  action_id: string
  tool: string
  args: Record<string, any>
  description: string
}

export const useChatStore = defineStore('chat', () => {
  // State
  const status = ref<ChatStatus>('idle')
  const streamingContent = ref('')
  const thinkingContent = ref('')
  const pendingToolCalls = ref<PendingToolCall[]>([])
  const pendingConfirmation = ref<PendingConfirmation | null>(null)
  const currentCitations = ref<Citation[]>([])
  const error = ref<string | null>(null)
  const abortController = ref<AbortController | null>(null)
  const tokensUsed = ref(0)

  // Getters
  const isStreaming = computed(() => 
    ['thinking', 'tool_calling', 'streaming'].includes(status.value)
  )

  const canSendMessage = computed(() => 
    status.value === 'idle' || status.value === 'error'
  )

  const needsConfirmation = computed(() =>
    status.value === 'waiting_confirm' && pendingConfirmation.value !== null
  )

  // Actions
  function startStreaming() {
    status.value = 'thinking'
    streamingContent.value = ''
    thinkingContent.value = ''
    pendingToolCalls.value = []
    currentCitations.value = []
    error.value = null
    abortController.value = new AbortController()
  }

  function setThinking(content: string) {
    status.value = 'thinking'
    thinkingContent.value += content
  }

  function setContent(content: string) {
    status.value = 'streaming'
    streamingContent.value += content
  }

  function addToolCall(toolCall: PendingToolCall) {
    status.value = 'tool_calling'
    pendingToolCalls.value.push(toolCall)
  }

  function updateToolCall(id: string, updates: Partial<PendingToolCall>) {
    const index = pendingToolCalls.value.findIndex(tc => tc.id === id)
    if (index !== -1) {
      pendingToolCalls.value[index] = {
        ...pendingToolCalls.value[index],
        ...updates,
      }
    }
  }

  function setConfirmRequired(confirmation: PendingConfirmation) {
    status.value = 'waiting_confirm'
    pendingConfirmation.value = confirmation
  }

  function clearConfirmation() {
    pendingConfirmation.value = null
    if (status.value === 'waiting_confirm') {
      status.value = 'streaming'
    }
  }

  function setCitations(citations: Citation[]) {
    currentCitations.value = citations
  }

  function setError(message: string) {
    status.value = 'error'
    error.value = message
  }

  function setDone(tokens: number) {
    status.value = 'idle'
    tokensUsed.value = tokens
  }

  function stopStreaming() {
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
    status.value = 'idle'
  }

  function reset() {
    status.value = 'idle'
    streamingContent.value = ''
    thinkingContent.value = ''
    pendingToolCalls.value = []
    pendingConfirmation.value = null
    currentCitations.value = []
    error.value = null
    tokensUsed.value = 0
    
    if (abortController.value) {
      abortController.value.abort()
      abortController.value = null
    }
  }

  // Get current streaming state for message building
  function getCurrentStreamState() {
    return {
      content: streamingContent.value,
      thinking: thinkingContent.value,
      toolCalls: pendingToolCalls.value.map(tc => ({
        id: tc.id,
        name: tc.name,
        args: tc.args,
        status: tc.status,
        result: tc.result,
        error: tc.error,
      })),
      citations: currentCitations.value,
    }
  }

  return {
    // State
    status,
    streamingContent,
    thinkingContent,
    pendingToolCalls,
    pendingConfirmation,
    currentCitations,
    error,
    abortController,
    tokensUsed,
    
    // Getters
    isStreaming,
    canSendMessage,
    needsConfirmation,
    
    // Actions
    startStreaming,
    setThinking,
    setContent,
    addToolCall,
    updateToolCall,
    setConfirmRequired,
    clearConfirmation,
    setCitations,
    setError,
    setDone,
    stopStreaming,
    reset,
    getCurrentStreamState,
  }
})
