<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useSessionStore } from '@/stores/session'
import { useChatStore } from '@/stores/chat'
import { useChat } from '@/composables/useChat'
import SessionList from '@/components/session/SessionList.vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import WorkingMemory from '@/components/execution/WorkingMemory.vue'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'

// Stores
const sessionStore = useSessionStore()
const chatStore = useChatStore()

// Composable
const chat = useChat()

// Local state
const messagesContainer = ref<HTMLElement | null>(null)
const workspaceId = ref('default-workspace') // TODO: Get from route or user context
const showWorkingMemory = ref(false)
const workingMemoryData = ref<WorkingMemoryResponse | null>(null)
const workingMemoryLoading = ref(false)

// Computed
const messages = computed(() => sessionStore.messages)
const currentSession = computed(() => sessionStore.currentSession)
const isStreaming = computed(() => chatStore.isStreaming)

// Methods
async function handleNewSession() {
  await sessionStore.createSession(workspaceId.value)
}

async function handleSelectSession(sessionId: string) {
  await sessionStore.selectSession(sessionId)
  scrollToBottom()
}

async function handleDeleteSession(sessionId: string) {
  await sessionStore.deleteSession(sessionId)
}

async function handleSendMessage(content: string) {
  await chat.sendMessage(content)
  scrollToBottom()
  // Refresh working memory after sending message
  if (currentSession.value) {
    await fetchWorkingMemory(currentSession.value.id)
  }
}

function handleStopStreaming() {
  chat.stopStreaming()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function toggleWorkingMemory() {
  showWorkingMemory.value = !showWorkingMemory.value
}

async function fetchWorkingMemory(sessionId: string) {
  workingMemoryLoading.value = true
  try {
    workingMemoryData.value = await workingMemoryApi.get(sessionId)
  } catch (error) {
    console.error('Failed to fetch working memory:', error)
    workingMemoryData.value = null
  } finally {
    workingMemoryLoading.value = false
  }
}

// Watch for session changes to load working memory
watch(currentSession, async (newSession) => {
  if (newSession && showWorkingMemory.value) {
    await fetchWorkingMemory(newSession.id)
  }
})

// Lifecycle
onMounted(async () => {
  await sessionStore.fetchSessions(workspaceId.value)
})
</script>

<template>
  <div class="h-screen flex bg-bg-primary">
    <!-- Sidebar -->
    <aside class="w-72 bg-bg-secondary border-r border-border-default flex-shrink-0">
      <SessionList
        :sessions="sessionStore.sessions"
        :current-session-id="currentSession?.id"
        :loading="sessionStore.loading"
        @select="handleSelectSession"
        @delete="handleDeleteSession"
        @new="handleNewSession"
      />
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0">
      <!-- Header -->
      <header class="h-14 bg-bg-secondary border-b border-border-default flex items-center px-6">
        <div class="flex-1">
          <h1 class="text-lg font-semibold text-text-primary">
            {{ currentSession?.title || 'TokenDance' }}
          </h1>
          <p v-if="currentSession" class="text-xs text-text-tertiary">
            {{ currentSession.message_count }} messages · {{ currentSession.total_tokens_used }} tokens
          </p>
        </div>

        <!-- Session Actions -->
        <div v-if="currentSession" class="flex items-center gap-2">
          <!-- Working Memory Toggle -->
          <button
            @click="toggleWorkingMemory"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors"
            :class="showWorkingMemory 
              ? 'bg-accent-primary/20 text-accent-primary' 
              : 'bg-bg-tertiary text-text-secondary hover:text-text-primary'"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <span>Memory</span>
          </button>
          
          <span 
            class="px-2 py-1 rounded text-xs"
            :class="{
              'bg-green-500/20 text-green-400': currentSession.status === 'active',
              'bg-bg-tertiary text-text-secondary': currentSession.status === 'completed',
              'bg-red-500/20 text-red-400': currentSession.status === 'failed',
            }"
          >
            {{ currentSession.status }}
          </span>
        </div>
      </header>

      <!-- Main Content Area -->
      <div class="flex-1 flex min-h-0">
        <!-- Messages Area -->
        <div 
          ref="messagesContainer"
          class="flex-1 overflow-y-auto px-6"
          :class="showWorkingMemory ? 'w-2/3' : 'w-full'"
        >
        <!-- Empty State -->
        <div 
          v-if="!currentSession" 
          class="h-full flex flex-col items-center justify-center"
        >
          <div class="w-16 h-16 rounded-full bg-accent-gradient flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>
          <h2 class="text-xl font-semibold text-text-primary mb-2">Welcome to TokenDance</h2>
          <p class="text-sm text-center max-w-md mb-6 text-text-secondary">
            Your AI Agent assistant for deep research, PPT generation, and more.
            Start a new chat to begin.
          </p>
          <button
            @click="handleNewSession"
            class="flex items-center gap-2 px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-hover transition-colors"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
            </svg>
            Start New Chat
          </button>
        </div>

        <!-- Messages -->
        <div v-else class="max-w-4xl mx-auto py-4">
          <ChatMessage
            v-for="(message, index) in messages"
            :key="message.id"
            :message="message"
            :is-streaming="isStreaming && index === messages.length - 1 && message.role === 'assistant'"
          />

          <!-- Confirmation Dialog -->
          <div 
            v-if="chatStore.needsConfirmation" 
            class="fixed inset-0 bg-black/70 flex items-center justify-center z-50"
          >
            <div class="bg-bg-elevated rounded-xl p-6 max-w-md shadow-xl border border-border-default">
              <h3 class="text-lg font-semibold text-text-primary mb-2">Confirmation Required</h3>
              <p class="text-text-secondary mb-4">{{ chatStore.pendingConfirmation?.description }}</p>
              
              <div class="bg-bg-primary rounded-lg p-3 mb-4 border border-border-default">
                <div class="text-sm font-medium text-text-primary">
                  Tool: {{ chatStore.pendingConfirmation?.tool }}
                </div>
                <pre class="text-xs text-text-tertiary mt-1 overflow-auto max-h-32">{{ JSON.stringify(chatStore.pendingConfirmation?.args, null, 2) }}</pre>
              </div>

              <div class="flex gap-3">
                <button
                  @click="chat.confirmAction(false)"
                  class="flex-1 px-4 py-2 border border-border-default rounded-lg text-text-secondary hover:bg-bg-tertiary transition-colors"
                >
                  Reject
                </button>
                <button
                  @click="chat.confirmAction(true)"
                  class="flex-1 px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-hover transition-colors"
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        </div>
        </div>

        <!-- Working Memory Panel -->
        <aside 
          v-if="showWorkingMemory && currentSession"
          class="w-1/3 border-l border-border-default bg-bg-secondary overflow-y-auto p-4"
        >
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-text-primary">Working Memory</h3>
            <button
              @click="fetchWorkingMemory(currentSession.id)"
              :disabled="workingMemoryLoading"
              class="p-1.5 rounded hover:bg-bg-tertiary transition-colors"
            >
              <svg 
                class="w-4 h-4 text-text-secondary" 
                :class="{ 'animate-spin': workingMemoryLoading }"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
            </button>
          </div>
          
          <WorkingMemory
            v-if="workingMemoryData"
            :taskPlan="workingMemoryData.task_plan.content"
            :findings="workingMemoryData.findings.content"
            :progress="workingMemoryData.progress.content"
          />
          
          <div v-else-if="workingMemoryLoading" class="flex items-center justify-center py-8">
            <svg class="w-6 h-6 text-accent-primary animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
            </svg>
          </div>
          
          <div v-else class="text-center py-8">
            <p class="text-sm text-text-tertiary">Click refresh to load working memory</p>
          </div>
        </aside>
      </div>

      <!-- Input Area -->
      <ChatInput
        v-if="currentSession"
        :disabled="!sessionStore.hasCurrentSession"
        :is-streaming="isStreaming"
        @send="handleSendMessage"
        @stop="handleStopStreaming"
      />
    </main>
  </div>
</template>
