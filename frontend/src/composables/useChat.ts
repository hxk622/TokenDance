/**
 * useChat composable - handles chat streaming with SSE
 */
import { useChatStore } from '@/stores/chat'
import { useSessionStore } from '@/stores/session'
import { chatApi, type ChatRequest, type SSEEvent, type SSEEventType, type Attachment } from '@/api/chat'
import type { Message } from '@/api/session'

export function useChat() {
  const chatStore = useChatStore()
  const sessionStore = useSessionStore()

  /**
   * Send a message and stream the response
   */
  async function sendMessage(content: string, attachments?: Attachment[]) {
    const session = sessionStore.currentSession
    if (!session) {
      throw new Error('No active session')
    }

    if (!chatStore.canSendMessage) {
      throw new Error('Cannot send message while streaming')
    }

    // Add user message
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      session_id: session.id,
      role: 'user',
      content,
      tokens_used: 0,
      created_at: new Date().toISOString(),
    }
    sessionStore.addMessage(userMessage)

    // Start streaming
    chatStore.startStreaming()

    // Add placeholder assistant message
    const assistantMessage: Message = {
      id: `temp-${Date.now() + 1}`,
      session_id: session.id,
      role: 'assistant',
      content: '',
      tokens_used: 0,
      created_at: new Date().toISOString(),
    }
    sessionStore.addMessage(assistantMessage)

    try {
      await streamResponse(session.id, { content, attachments })
    } catch (error) {
      if (error instanceof Error && error.name !== 'AbortError') {
        chatStore.setError(error.message)
      }
    }
  }

  /**
   * Stream response from API using fetch
   */
  async function streamResponse(sessionId: string, request: ChatRequest) {
    const token = localStorage.getItem('access_token')
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
    const url = `${baseUrl}/api/v1/chat/${sessionId}/message`

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      body: JSON.stringify(request),
      signal: chatStore.abortController?.signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('Response body is null')
    }

    const decoder = new TextDecoder()
    let buffer = ''
    let currentEventType: SSEEventType = 'content'

    let isReading = true
    while (isReading) {
      const { done, value } = await reader.read()
      
      if (done) {
        isReading = false
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event:')) {
          currentEventType = line.substring(6).trim() as SSEEventType
          continue
        }

        if (line.startsWith('data:')) {
          const data = line.substring(5).trim()
          if (data) {
            try {
              const parsedData = JSON.parse(data)
              handleSSEEvent({ type: currentEventType, data: parsedData })
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    }
  }

  /**
   * Handle SSE event
   */
  function handleSSEEvent(event: SSEEvent) {
    switch (event.type) {
      case 'thinking':
        chatStore.setThinking(event.data.content || '')
        // Update assistant message with thinking
        sessionStore.updateLastMessage({
          thinking: chatStore.thinkingContent,
        })
        break

      case 'tool_call':
        chatStore.addToolCall({
          id: event.data.id,
          name: event.data.name,
          args: event.data.args || {},
          status: event.data.status || 'pending',
        })
        // Update message with tool calls
        sessionStore.updateLastMessage({
          tool_calls: chatStore.pendingToolCalls.map(tc => ({
            id: tc.id,
            name: tc.name,
            args: tc.args,
            status: tc.status,
            result: tc.result,
            error: tc.error,
          })),
        })
        break

      case 'tool_result':
        chatStore.updateToolCall(event.data.id, {
          status: event.data.status,
          result: event.data.result,
          error: event.data.error,
        })
        // Update message
        sessionStore.updateLastMessage({
          tool_calls: chatStore.pendingToolCalls.map(tc => ({
            id: tc.id,
            name: tc.name,
            args: tc.args,
            status: tc.status,
            result: tc.result,
            error: tc.error,
          })),
        })
        break

      case 'content':
        chatStore.setContent(event.data.content || '')
        if (event.data.citations) {
          chatStore.setCitations(event.data.citations)
        }
        // Update message content
        sessionStore.updateLastMessage({
          content: chatStore.streamingContent,
          citations: chatStore.currentCitations,
        })
        break

      case 'confirm_required':
        chatStore.setConfirmRequired({
          action_id: event.data.action_id,
          tool: event.data.tool,
          args: event.data.args,
          description: event.data.description,
        })
        break

      case 'done':
        chatStore.setDone(event.data.tokens_used || 0)
        // Update final message
        sessionStore.updateLastMessage({
          id: event.data.message_id,
          content: chatStore.streamingContent,
          thinking: chatStore.thinkingContent,
          tool_calls: chatStore.pendingToolCalls.map(tc => ({
            id: tc.id,
            name: tc.name,
            args: tc.args,
            status: tc.status,
            result: tc.result,
            error: tc.error,
          })),
          citations: chatStore.currentCitations,
          tokens_used: event.data.tokens_used || 0,
        })
        break

      case 'error':
        chatStore.setError(event.data.message || 'An error occurred')
        break
    }
  }

  /**
   * Confirm HITL action
   */
  async function confirmAction(confirmed: boolean) {
    const session = sessionStore.currentSession
    if (!session || !chatStore.pendingConfirmation) return

    try {
      await chatApi.confirm(session.id, {
        action_id: chatStore.pendingConfirmation.action_id,
        confirmed,
      })
      chatStore.clearConfirmation()
    } catch (error) {
      chatStore.setError(error instanceof Error ? error.message : 'Failed to confirm action')
    }
  }

  /**
   * Stop current streaming
   */
  async function stopStreaming() {
    const session = sessionStore.currentSession
    if (!session) return

    chatStore.stopStreaming()

    try {
      await chatApi.stop(session.id)
    } catch (error) {
      console.error('Failed to stop streaming:', error)
    }
  }

  return {
    // State from stores
    status: chatStore.status,
    isStreaming: chatStore.isStreaming,
    canSendMessage: chatStore.canSendMessage,
    needsConfirmation: chatStore.needsConfirmation,
    pendingConfirmation: chatStore.pendingConfirmation,
    streamingContent: chatStore.streamingContent,
    thinkingContent: chatStore.thinkingContent,
    pendingToolCalls: chatStore.pendingToolCalls,
    error: chatStore.error,

    // Actions
    sendMessage,
    confirmAction,
    stopStreaming,
    reset: chatStore.reset,
  }
}
