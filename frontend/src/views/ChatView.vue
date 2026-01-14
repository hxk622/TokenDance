<script setup lang="ts">
import { ref } from 'vue'
import { useAgentStream } from '@/composables/useAgentStream'
import MessageList, { type Message } from '@/components/MessageList.vue'
import InputBox from '@/components/InputBox.vue'
import ThinkingTrace from '@/components/ThinkingTrace.vue'
import ToolCallCard, { type ToolCallStatus } from '@/components/ToolCallCard.vue'

// Types
interface ToolCall {
  id: string
  toolName: string
  parameters: Record<string, any>
  result?: string
  status: ToolCallStatus
}

// State
const messages = ref<Message[]>([])
const toolCalls = ref<ToolCall[]>([])
const currentReasoning = ref('')
const currentIteration = ref(0)
const showThinking = ref(false)

// Session ID (hardcoded for now - TODO: dynamic from route/user)
const sessionId = 'demo-session-123'

// API base URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// SSE Stream composable
const {
  sendMessage: streamMessage,
  isLoading,
  isConnected
} = useAgentStream({
  apiBase: API_BASE,
  onStart: () => {
    showThinking.value = true
    currentReasoning.value = '启动中...'
    currentIteration.value = 0
  },
  
  onIteration: (data) => {
    currentIteration.value = data.iteration
  },
  
  onReasoning: (data) => {
    currentReasoning.value = data.reasoning
  },
  
  onToolCall: (data) => {
    const toolCall: ToolCall = {
      id: `tool-${Date.now()}-${Math.random()}`,
      toolName: data.tool,
      parameters: data.args || {},
      status: 'running'
    }
    toolCalls.value.push(toolCall)
  },
  
  onToolResult: (data) => {
    // Find the matching tool call and update it
    const toolCall = toolCalls.value.find(t => t.toolName === data.tool && t.status === 'running')
    if (toolCall) {
      toolCall.result = data.result
      toolCall.status = data.success ? 'success' : 'error'
    }
  },
  
  onAnswer: (data) => {
    showThinking.value = false
    
    // Add assistant message
    const message: Message = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: data.answer,
      timestamp: new Date()
    }
    messages.value.push(message)
    
    // Clear tool calls after answer
    toolCalls.value = []
  },
  
  onError: (data) => {
    showThinking.value = false
    
    // Add error message
    const errorMessage: Message = {
      id: `err-${Date.now()}`,
      role: 'error',
      content: data.error,
      timestamp: new Date()
    }
    messages.value.push(errorMessage)
    
    // Clear tool calls
    toolCalls.value = []
  },
  
  onDone: () => {
    showThinking.value = false
  }
})

// Methods
const handleSendMessage = async (content: string) => {
  // Add user message
  const userMessage: Message = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  
  // Send to API
  await streamMessage(sessionId, content)
}
</script>

<template>
  <div class="chat-view">
    <!-- Header -->
    <header class="chat-header">
      <h1 class="chat-title">TokenDance</h1>
      <div class="status-indicator">
        <div v-if="isConnected" class="status-dot status-connected" />
        <div v-else class="status-dot status-disconnected" />
        <span class="status-text">
          {{ isConnected ? '已连接' : '未连接' }}
        </span>
      </div>
    </header>

    <!-- Messages Area -->
    <div class="messages-area">
      <MessageList :messages="messages" />
      
      <!-- Thinking Trace -->
      <ThinkingTrace
        :visible="showThinking"
        :iteration="currentIteration"
        :reasoning="currentReasoning"
      />
      
      <!-- Tool Calls -->
      <ToolCallCard
        v-for="toolCall in toolCalls"
        :key="toolCall.id"
        :tool-name="toolCall.toolName"
        :parameters="toolCall.parameters"
        :result="toolCall.result"
        :status="toolCall.status"
      />
    </div>

    <!-- Input Box -->
    <InputBox
      :disabled="isLoading"
      @send="handleSendMessage"
    />
  </div>
</template>

<style scoped>
.chat-view {
  @apply h-screen flex flex-col bg-gray-50;
}

.chat-header {
  @apply flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200;
}

.chat-title {
  @apply text-xl font-semibold text-gray-800;
}

.status-indicator {
  @apply flex items-center gap-2;
}

.status-dot {
  @apply w-2 h-2 rounded-full;
}

.status-connected {
  @apply bg-green-500;
}

.status-disconnected {
  @apply bg-gray-400;
}

.status-text {
  @apply text-sm text-gray-600;
}

.messages-area {
  @apply flex-1 flex flex-col overflow-hidden;
}
</style>
