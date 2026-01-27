/**
 * useAgentStream - SSE 流式接收 Agent 响应
 * 
 * 处理 Server-Sent Events，实时接收 Agent 的思考过程和工具调用
 */

import { ref, onUnmounted } from 'vue'


export interface UseAgentStreamOptions {
  apiBase?: string
  onStart?: () => void
  onIteration?: (data: { iteration: number }) => void
  onReasoning?: (data: { reasoning: string }) => void
  onToolCall?: (data: { tool: string; args: Record<string, any> }) => void
  onToolResult?: (data: { tool: string; success: boolean; result: string }) => void
  onAnswer?: (data: { answer: string }) => void
  onError?: (data: { error: string }) => void
  onDone?: () => void
}

export function useAgentStream(options: UseAgentStreamOptions = {}) {
  const API_BASE = options.apiBase || 'http://127.0.0.1:8000'
  const eventSource = ref<EventSource | null>(null)
  const isConnected = ref(false)
  const isLoading = ref(false)

  /**
   * 发送消息并建立 SSE 连接
   */
  const sendMessage = async (sessionId: string, content: string) => {
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
            content
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
        options.onAnswer?.({
          answer: data.content
        })
        options.onDone?.()
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
      let isReading = true
      while (isReading) {
        const { done, value } = await reader.read()
        
        if (done) {
          isReading = false
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
      options.onError?.({
        error: error.message || 'Connection failed'
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
        options.onStart?.()
        break
      
      case 'iteration':
        options.onIteration?.(data)
        break
      
      case 'reasoning':
        options.onReasoning?.(data)
        break
      
      case 'tool_call':
        options.onToolCall?.(data)
        break
      
      case 'tool_result':
        options.onToolResult?.(data)
        break
      
      case 'answer':
        options.onAnswer?.(data)
        break
      
      case 'error':
        options.onError?.(data)
        break
      
      case 'done':
        options.onDone?.()
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
