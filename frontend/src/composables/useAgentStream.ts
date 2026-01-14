/**
 * useAgentStream - SSE 流式接收 Agent 响应
 * 
 * 处理 Server-Sent Events，实时接收 Agent 的思考过程和工具调用
 */

import { ref, onUnmounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface AgentStreamCallbacks {
  onStart?: () => void
  onIteration?: (data: { iteration: number; max_iterations: number }) => void
  onReasoning?: (data: { content: string; iteration: number }) => void
  onToolCall?: (data: { tool_name: string; parameters: any; iteration: number }) => void
  onToolResult?: (data: { tool_name: string; success: boolean; result?: string; error?: string; iteration: number }) => void
  onAnswer?: (data: { content: string; iteration: number; token_usage?: any }) => void
  onError?: (data: { message: string; type: string }) => void
  onDone?: (data?: { iterations?: number; token_usage?: any; error?: boolean }) => void
}

export function useAgentStream(sessionId: string, callbacks: AgentStreamCallbacks = {}) {
  const eventSource = ref<EventSource | null>(null)
  const isConnected = ref(false)
  const isLoading = ref(false)

  /**
   * 发送消息并建立 SSE 连接
   */
  const sendMessage = async (content: string) => {
    // 关闭之前的连接
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }

    isLoading.value = true
    isConnected.value = false

    try {
      // 先发送 POST 请求
      const response = await fetch(
        `${API_BASE}/api/v1/sessions/${sessionId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content,
            stream: true
          })
        }
      )

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      // 检查是否是 SSE 响应
      const contentType = response.headers.get('content-type')
      if (!contentType?.includes('text/event-stream')) {
        // 非流式响应，直接返回
        const data = await response.json()
        callbacks.onAnswer?.({
          content: data.content,
          iteration: data.iterations || 1,
          token_usage: data.token_usage
        })
        callbacks.onDone?.({
          iterations: data.iterations,
          token_usage: data.token_usage
        })
        isLoading.value = false
        return
      }

      // 读取 SSE 流
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is null')
      }

      isConnected.value = true

      // 读取流
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // 解码数据
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        let currentEvent = ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.substring(6).trim()
          } else if (line.startsWith('data:')) {
            const dataStr = line.substring(5).trim()
            
            try {
              const data = JSON.parse(dataStr)
              handleEvent(currentEvent, data)
            } catch (e) {
              console.error('Failed to parse SSE data:', dataStr, e)
            }
          }
        }
      }

    } catch (error: any) {
      console.error('SSE connection error:', error)
      callbacks.onError?.({
        message: error.message || 'Connection failed',
        type: 'ConnectionError'
      })
    } finally {
      isLoading.value = false
      isConnected.value = false
    }
  }

  /**
   * 处理 SSE 事件
   */
  const handleEvent = (eventType: string, data: any) => {
    switch (eventType) {
      case 'start':
        callbacks.onStart?.()
        break
      
      case 'iteration':
        callbacks.onIteration?.(data)
        break
      
      case 'reasoning':
        callbacks.onReasoning?.(data)
        break
      
      case 'tool_call':
        callbacks.onToolCall?.(data)
        break
      
      case 'tool_result':
        callbacks.onToolResult?.(data)
        break
      
      case 'answer':
        callbacks.onAnswer?.(data)
        break
      
      case 'error':
        callbacks.onError?.(data)
        break
      
      case 'done':
        callbacks.onDone?.(data)
        isLoading.value = false
        break
      
      default:
        console.warn('Unknown event type:', eventType, data)
    }
  }

  /**
   * 停止生成
   */
  const stopGeneration = () => {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isLoading.value = false
    isConnected.value = false
  }

  // 组件卸载时清理
  onUnmounted(() => {
    stopGeneration()
  })

  return {
    sendMessage,
    stopGeneration,
    isLoading,
    isConnected
  }
}
