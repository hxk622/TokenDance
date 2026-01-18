<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgentStream } from '@/composables/useAgentStream'
import MessageList, { type Message } from '@/components/MessageList.vue'
import InputBox from '@/components/InputBox.vue'
import ThinkingTrace from '@/components/ThinkingTrace.vue'
import ToolCallCard, { type ToolCallStatus } from '@/components/ToolCallCard.vue'
import WorkingMemory from '@/components/execution/WorkingMemory.vue'
import HITLConfirmDialog from '@/components/execution/HITLConfirmDialog.vue'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'
import { hitlApi, type HITLRequest } from '@/api/hitl'
import { useSessionStore } from '@/stores/session'
import { sessionApi } from '@/api/session'

// Types
interface ToolCall {
  id: string
  toolName: string
  parameters: Record<string, any>
  result?: string
  status: ToolCallStatus
}

// Router
const route = useRoute()
const router = useRouter()

// Stores
const sessionStore = useSessionStore()

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

// HITL State
const pendingHITLRequests = ref<HITLRequest[]>([])
const currentHITLRequest = ref<HITLRequest | null>(null)
const showHITLDialog = ref(false)
let hitlPollingInterval: ReturnType<typeof setInterval> | null = null

// Session State
const currentSessionId = computed(() => route.params.sessionId as string | undefined)

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
    const toolCall = toolCalls.value.find(t => t.toolName === data.tool && t.status === 'running')
    if (toolCall) {
      toolCall.result = data.result
      toolCall.status = data.success ? 'success' : 'error'
    }
  },
  
  onAnswer: (data) => {
    showThinking.value = false
    
    const message: Message = {
      id: `msg-${Date.now()}`,
      role: 'assistant',
      content: data.answer,
      timestamp: new Date()
    }
    messages.value.push(message)
    
    toolCalls.value = []
  },
  
  onError: (data) => {
    showThinking.value = false
    
    const errorMessage: Message = {
      id: `err-${Date.now()}`,
      role: 'error',
      content: data.error,
      timestamp: new Date()
    }
    messages.value.push(errorMessage)
    
    toolCalls.value = []
  },
  
  onDone: () => {
    showThinking.value = false
    loadWorkingMemory()
  }
})

// Methods
const handleSendMessage = async (content: string) => {
  let sessionId = currentSessionId.value
  
  if (!sessionId || sessionId === 'new') {
    try {
      const newSession = await sessionApi.createSession({
        title: content.substring(0, 50),
        workspace_id: sessionStore.currentWorkspaceId || 'default'
      })
      sessionId = newSession.id
      sessionStore.setCurrentSession(newSession)
      router.replace(`/chat/${sessionId}`)
    } catch (error) {
      console.error('Failed to create session:', error)
      return
    }
  }
  
  const userMessage: Message = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content,
    timestamp: new Date()
  }
  messages.value.push(userMessage)
  
  await streamMessage(sessionId, content)
}

const toggleMemoryPanel = () => {
  showMemoryPanel.value = !showMemoryPanel.value
  if (showMemoryPanel.value && !memoryData.value) {
    loadWorkingMemory()
  }
}

const loadWorkingMemory = async () => {
  if (!showMemoryPanel.value || !currentSessionId.value || currentSessionId.value === 'new') return
  
  isLoadingMemory.value = true
  try {
    const data = await workingMemoryApi.get(currentSessionId.value)
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

// HITL Methods
const pollHITLRequests = async () => {
  if (!currentSessionId.value || currentSessionId.value === 'new') return
  
  try {
    const requests = await hitlApi.listPending(currentSessionId.value)
    pendingHITLRequests.value = requests
    
    if (requests.length > 0 && !showHITLDialog.value) {
      currentHITLRequest.value = requests[0]
      showHITLDialog.value = true
    }
  } catch (error) {
    console.debug('HITL polling error:', error)
  }
}

const startHITLPolling = () => {
  hitlPollingInterval = setInterval(pollHITLRequests, 2000)
  pollHITLRequests()
}

const stopHITLPolling = () => {
  if (hitlPollingInterval) {
    clearInterval(hitlPollingInterval)
    hitlPollingInterval = null
  }
}

const handleHITLClose = () => {
  showHITLDialog.value = false
  currentHITLRequest.value = null
}

const handleHITLConfirmed = (approved: boolean) => {
  showHITLDialog.value = false
  currentHITLRequest.value = null
  
  const systemMessage: Message = {
    id: `sys-${Date.now()}`,
    role: 'assistant',
    content: approved 
      ? '✅ 操作已确认执行' 
      : '❌ 操作已拒绝',
    timestamp: new Date()
  }
  messages.value.push(systemMessage)
  
  pollHITLRequests()
}

// Session Management
const loadSession = async (sessionId: string) => {
  if (sessionId === 'new') {
    messages.value = []
    return
  }
  
  try {
    const session = await sessionApi.getSession(sessionId, true)
    sessionStore.setCurrentSession(session)
    
    messages.value = (session.messages || []).map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: new Date(msg.created_at)
    }))
  } catch (error) {
    console.error('Failed to load session:', error)
    messages.value = []
  }
}

// Watch for session changes
watch(currentSessionId, async (newSessionId) => {
  if (newSessionId) {
    await loadSession(newSessionId)
    loadWorkingMemory()
  }
}, { immediate: true })

// Lifecycle
onMounted(() => {
  if (showMemoryPanel.value) {
    loadWorkingMemory()
  }
  startHITLPolling()
})

onUnmounted(() => {
  stopHITLPolling()
})
</script>

<template>
  <div class="chat-view">
    <!-- Header -->
    <header class="chat-header">
      <div class="header-left">
        <h1 class="chat-title">
          TokenDance
        </h1>
        <span
          v-if="sessionStore.currentSession"
          class="session-title"
        >
          {{ sessionStore.currentSession.title }}
        </span>
      </div>
      <div class="header-actions">
        <div class="status-indicator">
          <div
            v-if="isConnected"
            class="status-dot status-connected"
          />
          <div
            v-else
            class="status-dot status-disconnected"
          />
          <span class="status-text">
            {{ isConnected ? '已连接' : '未连接' }}
          </span>
        </div>
        <button
          class="memory-button"
          :class="{ 'memory-button-active': showMemoryPanel }"
          @click="toggleMemoryPanel"
        >
          <svg
            class="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span class="ml-2">Memory</span>
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Messages Area -->
      <div
        class="messages-area"
        :class="{ 'with-sidebar': showMemoryPanel }"
      >
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
        <div
          v-if="showMemoryPanel"
          class="memory-sidebar"
        >
          <div class="memory-header">
            <h2 class="memory-title">
              Working Memory
            </h2>
            <button
              class="refresh-button"
              :class="{ 'refresh-button-loading': isLoadingMemory }"
              :disabled="isLoadingMemory"
              @click="refreshMemory"
            >
              <svg
                class="w-4 h-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
            </button>
          </div>
          
          <div
            v-if="isLoadingMemory"
            class="loading-spinner"
          >
            <div class="spinner" />
            <p class="text-sm text-gray-500 mt-2">
              加载中...
            </p>
          </div>
          
          <WorkingMemory
            v-else-if="memoryData"
            :task-plan="memoryData.task_plan.content"
            :findings="memoryData.findings.content"
            :progress="memoryData.progress.content"
          />
          
          <div
            v-else
            class="empty-state"
          >
            <p class="text-sm text-gray-500">
              暂无Working Memory数据
            </p>
          </div>
        </div>
      </Transition>
    </div>

    <!-- HITL Confirm Dialog -->
    <HITLConfirmDialog
      :visible="showHITLDialog"
      :request="currentHITLRequest"
      @close="handleHITLClose"
      @confirmed="handleHITLConfirmed"
    />

    <!-- HITL Pending Badge -->
    <Transition name="bounce">
      <button
        v-if="pendingHITLRequests.length > 0 && !showHITLDialog"
        class="hitl-badge"
        @click="showHITLDialog = true; currentHITLRequest = pendingHITLRequests[0]"
      >
        <svg
          class="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2" 
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span>{{ pendingHITLRequests.length }} 待确认</span>
      </button>
    </Transition>
  </div>
</template>

<style scoped>
/* ============================================
   ChatView - Dark Theme (TokenDance Design System)
   ============================================ */

.chat-view {
  @apply h-screen flex flex-col;
  background: #0a0a0b;
}

.chat-header {
  @apply flex items-center justify-between px-6 py-4;
  background: rgba(20, 20, 21, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-left {
  @apply flex items-center gap-3;
}

.chat-title {
  @apply text-xl font-semibold text-white;
  font-family: 'Space Grotesk', sans-serif;
}

.session-title {
  @apply text-sm;
  color: rgba(255, 255, 255, 0.5);
}

.header-actions {
  @apply flex items-center gap-4;
}

.status-indicator {
  @apply flex items-center gap-2;
}

.status-dot {
  @apply w-2 h-2 rounded-full;
}

.status-connected {
  background: #00FF88;
  box-shadow: 0 0 8px rgba(0, 255, 136, 0.5);
}

.status-disconnected {
  @apply bg-gray-500;
}

.status-text {
  @apply text-sm;
  color: rgba(255, 255, 255, 0.6);
}

.memory-button {
  @apply flex items-center px-4 py-2 rounded-lg transition-all duration-200;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.memory-button:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.memory-button-active {
  background: rgba(0, 217, 255, 0.15) !important;
  border-color: rgba(0, 217, 255, 0.5) !important;
  color: #00D9FF !important;
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

/* Memory Sidebar - Dark Theme */
.memory-sidebar {
  @apply w-1/3 flex flex-col overflow-hidden;
  background: linear-gradient(180deg, 
    rgba(28, 28, 30, 0.95) 0%, 
    rgba(20, 20, 21, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}

.memory-header {
  @apply flex items-center justify-between px-4 py-3;
  background: rgba(28, 28, 30, 0.9);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.memory-title {
  @apply text-lg font-semibold text-white;
}

.refresh-button {
  @apply p-2 rounded-lg transition-all duration-200;
  color: rgba(255, 255, 255, 0.6);
}

.refresh-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.refresh-button-loading svg {
  @apply animate-spin;
  color: #00D9FF;
}

.loading-spinner {
  @apply flex flex-col items-center justify-center h-full;
}

.spinner {
  @apply w-8 h-8 rounded-full animate-spin;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
}

.loading-spinner p {
  @apply mt-3 text-sm;
  color: rgba(255, 255, 255, 0.5);
}

.empty-state {
  @apply flex items-center justify-center h-full text-center px-4;
  color: rgba(255, 255, 255, 0.4);
}

/* Transitions */
.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-left-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* HITL Badge */
.hitl-badge {
  @apply fixed bottom-24 right-6 flex items-center gap-2 px-4 py-3 rounded-full shadow-lg cursor-pointer transition-all duration-200;
  background: linear-gradient(135deg, #FFB800 0%, #FF8C00 100%);
  color: #000;
  font-weight: 600;
  animation: hitl-pulse 2s infinite;
}

.hitl-badge:hover {
  transform: scale(1.05);
  box-shadow: 0 8px 24px rgba(255, 184, 0, 0.4);
}

@keyframes hitl-pulse {
  0%, 100% {
    box-shadow: 0 4px 16px rgba(255, 184, 0, 0.4);
  }
  50% {
    box-shadow: 0 4px 24px rgba(255, 184, 0, 0.6), 0 0 0 8px rgba(255, 184, 0, 0.1);
  }
}

/* Bounce Animation */
.bounce-enter-active {
  animation: bounce-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.bounce-leave-active {
  animation: bounce-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1) reverse;
}

@keyframes bounce-in {
  0% {
    transform: scale(0);
    opacity: 0;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
