<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAgentStream } from '@/composables/useAgentStream'
import MessageList, { type Message } from '@/components/MessageList.vue'
import InputBox from '@/components/InputBox.vue'
import ThinkingTrace from '@/components/ThinkingTrace.vue'
import ToolCallCard, { type ToolCallStatus } from '@/components/ToolCallCard.vue'
import WorkingMemory from '@/components/execution/WorkingMemory.vue'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'

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

// Working Memory State
const showMemoryPanel = ref(false)
const memoryData = ref<WorkingMemoryResponse | null>(null)
const isLoadingMemory = ref(false)

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
    // Auto-refresh Working Memory after task completion
    loadWorkingMemory()
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

const toggleMemoryPanel = () => {
  showMemoryPanel.value = !showMemoryPanel.value
  if (showMemoryPanel.value && !memoryData.value) {
    loadWorkingMemory()
  }
}

const loadWorkingMemory = async () => {
  if (!showMemoryPanel.value) return
  
  isLoadingMemory.value = true
  try {
    const data = await workingMemoryApi.get(sessionId)
    memoryData.value = data
  } catch (error) {
    console.error('Failed to load working memory:', error)
  } finally {
    isLoadingMemory.value = false
  }
}

const refreshMemory = async () => {
  await loadWorkingMemory()
}

// Lifecycle
onMounted(() => {
  // Initial load if panel is open by default
  if (showMemoryPanel.value) {
    loadWorkingMemory()
  }
})
</script>

<template>
  <div class="chat-view">
    <!-- Header -->
    <header class="chat-header">
      <h1 class="chat-title">TokenDance</h1>
      <div class="header-actions">
        <div class="status-indicator">
          <div v-if="isConnected" class="status-dot status-connected" />
          <div v-else class="status-dot status-disconnected" />
          <span class="status-text">
            {{ isConnected ? '已连接' : '未连接' }}
          </span>
        </div>
        <button
          @click="toggleMemoryPanel"
          class="memory-button"
          :class="{ 'memory-button-active': showMemoryPanel }"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span class="ml-2">Memory</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Messages Area -->
      <div class="messages-area" :class="{ 'with-sidebar': showMemoryPanel }">
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
        
        <!-- Input Box -->
        <InputBox
          :disabled="isLoading"
          @send="handleSendMessage"
        />
      </div>

      <!-- Working Memory Sidebar -->
      <Transition name="slide-left">
        <div v-if="showMemoryPanel" class="memory-sidebar">
          <div class="memory-header">
            <h2 class="memory-title">Working Memory</h2>
            <button
              @click="refreshMemory"
              class="refresh-button"
              :class="{ 'refresh-button-loading': isLoadingMemory }"
              :disabled="isLoadingMemory"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
          
          <div v-if="isLoadingMemory" class="loading-spinner">
            <div class="spinner"></div>
            <p class="text-sm text-gray-500 mt-2">加载中...</p>
          </div>
          
          <WorkingMemory
            v-else-if="memoryData"
            :task-plan="memoryData.task_plan.content"
            :findings="memoryData.findings.content"
            :progress="memoryData.progress.content"
          />
          
          <div v-else class="empty-state">
            <p class="text-sm text-gray-500">暂无Working Memory数据</p>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  @apply h-screen flex flex-col bg-gray-50;
}

.chat-header {
  @apply flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200;
}

.header-actions {
  @apply flex items-center gap-4;
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

.memory-button {
  @apply flex items-center px-4 py-2 rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors;
}

.memory-button-active {
  @apply bg-blue-50 border-blue-500 text-blue-700;
}

.main-content {
  @apply flex-1 flex overflow-hidden;
}

.messages-area {
  @apply flex-1 flex flex-col overflow-hidden transition-all duration-300;
}

.messages-area.with-sidebar {
  @apply w-2/3;
}

.memory-sidebar {
  @apply w-1/3 border-l border-gray-200 bg-gray-50 flex flex-col overflow-hidden;
}

.memory-header {
  @apply flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white;
}

.memory-title {
  @apply text-lg font-semibold text-gray-800;
}

.refresh-button {
  @apply p-2 rounded-lg hover:bg-gray-100 transition-colors;
}

.refresh-button-loading svg {
  @apply animate-spin;
}

.loading-spinner {
  @apply flex flex-col items-center justify-center h-full;
}

.spinner {
  @apply w-8 h-8 border-4 border-gray-200 border-t-blue-500 rounded-full animate-spin;
}

.empty-state {
  @apply flex items-center justify-center h-full text-center px-4;
}

/* Slide transition */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>
