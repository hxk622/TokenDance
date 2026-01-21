<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { Lightbulb, ArrowRight, Loader2, Edit3, MessageSquareQuote, RotateCcw } from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'
import type { IntentValidationResponse } from '@/api/services/session'
import { ChatInput, ChatFormMessage } from '@/components/execution/chat'
import { ResearchProgress } from '@/components/execution/research'
import type { 
  ResearchProgress as ResearchProgressType,
  SearchQuery,
  ResearchSource,
  ResearchPhase,
} from '@/components/execution/research/types'
import { getCredibilityLevel } from '@/components/execution/research/types'
import type { 
  ChatMessage, 
  QuoteInfo, 
  SendMessagePayload,
  FormSubmitPayload,
  FormField,
  FormGroup,
  MessageStatus
} from '@/components/execution/chat/types'

// Re-export types for external use
export type { ChatMessage, QuoteInfo, FormField, FormGroup }
export type { MessageRole, MessageStatus, MessageContentType } from '@/components/execution/chat/types'

// Init phase types
export type InitPhase = 'idle' | 'analyzing' | 'needs-clarification' | 'ready' | 'executing'

interface Props {
  sessionId: string
  initPhase?: InitPhase
  preflightResult?: IntentValidationResponse | null
  userInput?: string
  userAvatar?: string  // URL or initial letter
  isDeepResearch?: boolean  // 是否为深度研究模式
}

const props = withDefaults(defineProps<Props>(), {
  initPhase: 'executing',
  preflightResult: null,
  userInput: '',
  userAvatar: 'U',
  isDeepResearch: false
})

// Emits
const emit = defineEmits<{
  proceed: [updatedInput?: string]
  'update-input': [input: string]
}>()

// Selected clarification options
const selectedOptions = ref<string[]>([])

// Handle proceed action
function handleProceed() {
  let finalInput = props.userInput
  if (selectedOptions.value.length > 0) {
    const context = selectedOptions.value.join(' | ')
    finalInput = `${finalInput}\n\n[补充信息: ${context}]`
  }
  emit('proceed', finalInput)
}

// Handle skip (proceed without clarification)
function handleSkip() {
  emit('proceed', props.userInput)
}

// Toggle option selection
function toggleOption(option: string) {
  const idx = selectedOptions.value.indexOf(option)
  if (idx >= 0) {
    selectedOptions.value.splice(idx, 1)
  } else {
    selectedOptions.value.push(option)
  }
}

// Reset selections when phase changes
watch(() => props.initPhase, () => {
  selectedOptions.value = []
})

// ========================================
// Research Progress State (深度研究进度)
// ========================================
const researchProgress = ref<ResearchProgressType | null>(null)
const isResearchProgressCollapsed = ref(false)

// Initialize research progress when in deep research mode
function initResearchProgress() {
  researchProgress.value = {
    phase: 'planning',
    phaseProgress: 0,
    overallProgress: 0,
    queries: [],
    sources: [],
    currentAction: '正在分析研究主题...',
  }
}

// Update research progress from SSE events
function updateResearchPhase(phase: ResearchPhase, phaseProgress: number = 0) {
  if (!researchProgress.value) initResearchProgress()
  researchProgress.value!.phase = phase
  researchProgress.value!.phaseProgress = phaseProgress
}

function addResearchQuery(queryId: string, text: string, status: 'pending' | 'running' | 'done' | 'failed' = 'running') {
  if (!researchProgress.value) initResearchProgress()
  const existing = researchProgress.value!.queries.find(q => q.id === queryId)
  if (existing) {
    existing.status = status
  } else {
    researchProgress.value!.queries.push({ id: queryId, text, status })
  }
}

function updateResearchQuery(queryId: string, resultCount: number) {
  if (!researchProgress.value) return
  const query = researchProgress.value.queries.find(q => q.id === queryId)
  if (query) {
    query.status = 'done'
    query.resultCount = resultCount
  }
}

function addResearchSource(
  sourceId: string,
  url: string,
  domain: string,
  title: string,
  status: 'pending' | 'reading' | 'done' | 'skipped' | 'failed' = 'reading'
) {
  if (!researchProgress.value) initResearchProgress()
  const existing = researchProgress.value!.sources.find(s => s.id === sourceId)
  if (existing) {
    existing.status = status
  } else {
    researchProgress.value!.sources.push({
      id: sourceId,
      url,
      domain,
      title,
      type: 'unknown',
      credibility: 50,
      credibilityLevel: 'moderate',
      status,
    })
  }
}

function updateResearchSource(
  sourceId: string,
  credibility: number,
  sourceType: string = 'unknown',
  extractedFacts: string[] = []
) {
  if (!researchProgress.value) return
  const source = researchProgress.value.sources.find(s => s.id === sourceId)
  if (source) {
    source.status = 'done'
    source.credibility = credibility
    source.credibilityLevel = getCredibilityLevel(credibility)
    source.type = sourceType as ResearchSource['type']
    source.extractedFacts = extractedFacts
  }
}

function updateResearchProgressState(
  currentAction: string,
  overallProgress?: number,
  estimatedTime?: number
) {
  if (!researchProgress.value) initResearchProgress()
  researchProgress.value!.currentAction = currentAction
  if (overallProgress !== undefined) {
    researchProgress.value!.overallProgress = overallProgress
  }
  if (estimatedTime !== undefined) {
    researchProgress.value!.estimatedTimeRemaining = estimatedTime
  }
}

// Open URL in new tab
function openUrl(url: string) {
  window.open(url, '_blank')
}

// ========================================
// Chat Messages (replacing old LogEntry)
// ========================================

const messages = ref<ChatMessage[]>([])
const chatContainerRef = ref<HTMLElement | null>(null)
const isScrollLocked = ref(false)
const userScrollTimeout = ref<ReturnType<typeof setTimeout> | null>(null)
const isUserScrolling = ref(false)

// Initialize with user message when userInput changes
watch(() => props.userInput, (newInput) => {
  if (newInput && messages.value.length === 0) {
    // Add user's initial query as first message
    messages.value.push({
      id: 'user-query',
      role: 'user',
      content: newInput,
      status: 'complete',
      timestamp: Date.now()
    })
  }
}, { immediate: true })

// Mock: Simulate AI response stream (for demo)
function simulateAIResponse() {
  // Add thinking message
  const thinkingMsg: ChatMessage = {
    id: 'ai-1',
    role: 'assistant',
    content: '',
    status: 'thinking',
    timestamp: Date.now(),
    toolCalls: []
  }
  messages.value.push(thinkingMsg)
  
  // Simulate streaming content
  setTimeout(() => {
    const msg = messages.value.find(m => m.id === 'ai-1')
    if (msg) {
      msg.status = 'streaming'
      msg.content = '正在分析 AI Agent 市场数据...'
      msg.toolCalls = [{ name: 'web_search', args: '"AI Agent 市场规模"' }]
    }
    scrollToBottom()
  }, 1500)
  
  setTimeout(() => {
    const msg = messages.value.find(m => m.id === 'ai-1')
    if (msg) {
      msg.content = '正在分析 AI Agent 市场数据...\n\n找到了 3 篇相关行业报告，正在提取关键信息...'
      msg.toolCalls?.push({ name: 'analyze_competitors', args: '["Manus", "Coworker"]' })
    }
    scrollToBottom()
  }, 3000)
  
  setTimeout(() => {
    const msg = messages.value.find(m => m.id === 'ai-1')
    if (msg) {
      msg.status = 'complete'
      msg.content = `根据我的分析，AI Agent 市场呈现以下特点：

1. **市场规模**: 2024年全球 AI Agent 市场规模约 50 亿美元
2. **主要玩家**: Manus、Coworker、AutoGPT 等
3. **增长趋势**: 预计 2025 年增长 40%+

我已将详细报告保存到 report.md 文件中。`
    }
    scrollToBottom()
  }, 5000)
}

// Start demo when entering executing phase
watch(() => props.initPhase, (phase) => {
  if (phase === 'executing' && messages.value.length <= 1) {
    setTimeout(simulateAIResponse, 500)
  }
})

// Auto scroll to bottom
function scrollToBottom() {
  if (isScrollLocked.value || isUserScrolling.value) return
  
  nextTick(() => {
    const container = chatContainerRef.value
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

function toggleScrollLock() {
  isScrollLocked.value = !isScrollLocked.value
}

// Detect user scroll
function handleUserScroll() {
  isUserScrolling.value = true
  
  if (userScrollTimeout.value) {
    clearTimeout(userScrollTimeout.value)
  }
  
  userScrollTimeout.value = setTimeout(() => {
    isUserScrolling.value = false
  }, 3000)
}

// Format timestamp (relative time)
function formatTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (seconds < 60) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
}

// Get user avatar display (initial or image)
const userAvatarDisplay = computed(() => {
  if (props.userAvatar.startsWith('http') || props.userAvatar.startsWith('/')) {
    return { type: 'image', src: props.userAvatar }
  }
  return { type: 'initial', text: props.userAvatar.charAt(0).toUpperCase() }
})

// ========================================
// Quote & Edit Features
// ========================================
const currentQuote = ref<QuoteInfo | null>(null)
const editingMessageId = ref<string | null>(null)
const editingContent = ref('')
const chatInputRef = ref<InstanceType<typeof ChatInput> | null>(null)
const hoveredMessageId = ref<string | null>(null)

// Handle quote message
function handleQuoteMessage(msg: ChatMessage) {
  currentQuote.value = {
    messageId: msg.id,
    content: msg.content.slice(0, 100),
    role: msg.role
  }
  chatInputRef.value?.focus()
}

// Clear quote
function handleClearQuote() {
  currentQuote.value = null
}

// Handle send message from input
function handleSendMessage(payload: SendMessagePayload) {
  const newMsg: ChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: payload.content,
    status: 'complete',
    timestamp: Date.now(),
    quotedMessageId: payload.quote?.messageId,
    quotedContent: payload.quote?.content
  }
  messages.value.push(newMsg)
  scrollToBottom()
  
  // Clear quote
  currentQuote.value = null
  
  // TODO: Emit to parent to handle the message
}

// Start editing a message
function startEditMessage(msg: ChatMessage) {
  editingMessageId.value = msg.id
  editingContent.value = msg.content
}

// Cancel editing
function cancelEditMessage() {
  editingMessageId.value = null
  editingContent.value = ''
}

// Save edited message (creates branch)
function saveEditMessage(msgId: string) {
  const msgIndex = messages.value.findIndex(m => m.id === msgId)
  if (msgIndex < 0) return
  
  // Mark subsequent messages as deprecated
  for (let i = msgIndex + 1; i < messages.value.length; i++) {
    messages.value[i].deprecated = true
  }
  
  // Update the message
  const msg = messages.value[msgIndex]
  msg.content = editingContent.value
  msg.edited = true
  msg.editedAt = Date.now()
  
  // Reset editing state
  editingMessageId.value = null
  editingContent.value = ''
  
  // TODO: Emit to parent to re-execute from this point
}

// Handle form submit from ChatFormMessage
function handleFormSubmit(msgId: string, values: Record<string, unknown>) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg) {
    msg.formSubmitted = true
    msg.formValues = values
    msg.isInteractive = false
  }
  // TODO: Emit to parent
}

// Handle form edit request
function handleFormEdit(msgId: string) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg) {
    msg.formSubmitted = false
    msg.isInteractive = true
  }
}

// Filter visible messages (hide deprecated unless expanded)
const visibleMessages = computed(() => {
  return messages.value.filter(m => !m.deprecated)
})

// ========================================
// Legacy methods for compatibility
// ========================================
const focusNodeId = ref<string | null>(null)

function scrollToNode(nodeId: string) {
  // Legacy: now just scroll to bottom
  scrollToBottom()
}

function enterFocusMode(nodeId: string) {
  focusNodeId.value = nodeId
}

function exitFocusMode() {
  focusNodeId.value = null
}

// Expose methods for parent component
defineExpose({
  scrollToNode,
  enterFocusMode,
  exitFocusMode,
  messages,
  // New method to add messages from parent
  addMessage: (msg: ChatMessage) => {
    messages.value.push(msg)
    scrollToBottom()
  },
  // Update the last AI message (for streaming)
  updateLastAIMessage: (content: string, status?: MessageStatus, statusText?: string) => {
    const lastAI = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAI) {
      lastAI.content = content
      if (status) lastAI.status = status
      if (statusText) lastAI.statusText = statusText
      scrollToBottom()
    }
  },
  // Add form message
  addFormMessage: (title: string, fields?: FormField[], groups?: FormGroup[]) => {
    const msg: ChatMessage = {
      id: `form-${Date.now()}`,
      role: 'assistant',
      content: title,
      status: 'complete',
      timestamp: Date.now(),
      contentType: 'form',
      formFields: fields,
      formGroups: groups,
      isInteractive: true
    }
    messages.value.push(msg)
    scrollToBottom()
  },
  // Research progress methods (深度研究进度透明化)
  researchProgress,
  initResearchProgress,
  updateResearchPhase,
  addResearchQuery,
  updateResearchQuery,
  addResearchSource,
  updateResearchSource,
  updateResearchProgressState,
})
</script>

<template>
  <div class="streaming-info">
    <!-- Init Phase UI (analyzing / needs-clarification) -->
    <Transition name="init-phase">
      <div
        v-if="initPhase === 'analyzing' || initPhase === 'needs-clarification'"
        class="init-phase-container"
      >
        <!-- Analyzing State -->
        <div
          v-if="initPhase === 'analyzing'"
          class="analyzing-card"
        >
          <div class="analyzing-icon">
            <Loader2 class="spin-icon" />
          </div>
          <div class="analyzing-content">
            <h3 class="analyzing-title">
              正在理解您的任务...
            </h3>
            <p class="analyzing-desc">
              {{ userInput?.slice(0, 60) }}{{ (userInput?.length || 0) > 60 ? '...' : '' }}
            </p>
            <div class="analyzing-progress">
              <div class="progress-bar" />
            </div>
          </div>
        </div>

        <!-- Needs Clarification State -->
        <div
          v-else-if="initPhase === 'needs-clarification' && preflightResult"
          class="clarification-card"
        >
          <div class="clarification-header">
            <Lightbulb class="clarification-icon" />
            <div class="clarification-title-wrap">
              <h3 class="clarification-title">
                为了更好地完成任务
              </h3>
              <p class="clarification-subtitle">
                建议补充以下信息（可选）
              </p>
            </div>
          </div>

          <!-- Reasoning -->
          <p
            v-if="preflightResult.reasoning"
            class="clarification-reasoning"
          >
            {{ preflightResult.reasoning }}
          </p>

          <!-- Missing Info List -->
          <div
            v-if="preflightResult.missing_info?.length"
            class="missing-info-list"
          >
            <div
              v-for="(info, idx) in preflightResult.missing_info"
              :key="idx"
              class="missing-info-item"
            >
              <span class="missing-bullet" />
              <span>{{ info }}</span>
            </div>
          </div>

          <!-- Suggested Questions (Selectable) -->
          <div
            v-if="preflightResult.suggested_questions?.length"
            class="suggested-options"
          >
            <button
              v-for="(q, idx) in preflightResult.suggested_questions"
              :key="idx"
              :class="['option-btn', { selected: selectedOptions.includes(q) }]"
              @click="toggleOption(q)"
            >
              <span class="option-checkbox">
                <svg
                  v-if="selectedOptions.includes(q)"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </span>
              <span class="option-text">{{ q }}</span>
            </button>
          </div>

          <!-- Actions -->
          <div class="clarification-actions">
            <AnyButton
              variant="ghost"
              size="sm"
              @click="handleSkip"
            >
              跳过补充
            </AnyButton>
            <AnyButton
              variant="primary"
              size="sm"
              :icon="ArrowRight"
              @click="handleProceed"
            >
              确认并继续
            </AnyButton>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Chat Header (only show when executing) -->
    <div
      v-if="initPhase === 'executing' || initPhase === 'ready'"
      class="chat-header"
    >
      <span class="chat-title">对话</span>
      <button 
        :class="['btn-lock', { locked: isScrollLocked }]"
        :title="isScrollLocked ? '解锁自动滚动' : '固定视图'"
        @click="toggleScrollLock"
      >
        <svg
          v-if="isScrollLocked"
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect
            x="3"
            y="11"
            width="18"
            height="11"
            rx="2"
            ry="2"
          />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect
            x="3"
            y="11"
            width="18"
            height="11"
            rx="2"
            ry="2"
          />
          <path d="M7 11V7a5 5 0 0 1 9.9-1" />
        </svg>
      </button>
    </div>

    <!-- Research Progress Panel (深度研究进度面板) -->
    <div
      v-if="(initPhase === 'executing' || initPhase === 'ready') && isDeepResearch && researchProgress"
      class="research-progress-container"
    >
      <ResearchProgress
        :progress="researchProgress"
        :collapsed="isResearchProgressCollapsed"
        @toggle-collapse="isResearchProgressCollapsed = !isResearchProgressCollapsed"
        @source-click="(source) => console.log('Source clicked:', source)"
        @open-url="openUrl"
      />
    </div>

    <!-- Chat Messages (Dialog Style) -->
    <div
      v-if="initPhase === 'executing' || initPhase === 'ready'"
      ref="chatContainerRef"
      class="chat-container"
      @scroll="handleUserScroll"
    >
      <div
        v-for="msg in visibleMessages"
        :key="msg.id"
        :class="['chat-message', msg.role, { editing: editingMessageId === msg.id }]"
        @mouseenter="hoveredMessageId = msg.id"
        @mouseleave="hoveredMessageId = null"
      >
        <!-- User Message (Right side) -->
        <template v-if="msg.role === 'user'">
          <div class="message-content user-message">
            <!-- Quoted message preview -->
            <div
              v-if="msg.quotedContent"
              class="quoted-preview"
            >
              <span class="quoted-label">回复:</span>
              <span class="quoted-text">{{ msg.quotedContent }}</span>
            </div>
            
            <!-- Editing mode -->
            <div
              v-if="editingMessageId === msg.id"
              class="edit-container"
            >
              <textarea
                v-model="editingContent"
                class="edit-textarea"
                rows="3"
              />
              <div class="edit-actions">
                <button
                  class="edit-btn-cancel"
                  @click="cancelEditMessage"
                >
                  取消
                </button>
                <button
                  class="edit-btn-save"
                  @click="saveEditMessage(msg.id)"
                >
                  <RotateCcw class="w-3.5 h-3.5" />
                  重新发送
                </button>
              </div>
            </div>
            
            <!-- Normal message bubble -->
            <div
              v-else
              class="message-bubble"
            >
              {{ msg.content }}
              <span
                v-if="msg.edited"
                class="edited-badge"
              >(已编辑)</span>
            </div>
            
            <!-- Message actions (hover) -->
            <div
              v-if="hoveredMessageId === msg.id && editingMessageId !== msg.id"
              class="message-actions"
            >
              <button
                class="action-btn"
                title="编辑"
                @click="startEditMessage(msg)"
              >
                <Edit3 class="w-3.5 h-3.5" />
              </button>
              <button
                class="action-btn"
                title="引用"
                @click="handleQuoteMessage(msg)"
              >
                <MessageSquareQuote class="w-3.5 h-3.5" />
              </button>
            </div>
            
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
          <div class="avatar user-avatar">
            <img
              v-if="userAvatarDisplay.type === 'image'"
              :src="userAvatarDisplay.src"
              alt="User"
            >
            <span v-else>{{ userAvatarDisplay.text }}</span>
          </div>
        </template>

        <!-- AI Message (Left side) -->
        <template v-else>
          <div class="avatar ai-avatar">
            <img
              src="/logo.svg"
              alt="AI"
            >
          </div>
          <div class="message-content ai-message">
            <!-- Thinking indicator with statusText -->
            <div
              v-if="msg.status === 'thinking'"
              class="thinking-indicator"
            >
              <Loader2 class="thinking-spinner" />
              <span>{{ msg.statusText || '正在思考...' }}</span>
            </div>
            
            <!-- Form message -->
            <ChatFormMessage
              v-else-if="msg.contentType === 'form'"
              :title="msg.content"
              :fields="msg.formFields"
              :groups="msg.formGroups"
              :interactive="msg.isInteractive !== false"
              :submitted="msg.formSubmitted"
              :submitted-values="msg.formValues"
              @submit="(values) => handleFormSubmit(msg.id, values)"
              @edit="handleFormEdit(msg.id)"
            />
            
            <!-- Message bubble with content -->
            <div
              v-else
              class="message-bubble"
            >
              <!-- Tool calls badge -->
              <div
                v-if="msg.toolCalls && msg.toolCalls.length > 0"
                class="tool-calls"
              >
                <div
                  v-for="(tool, idx) in msg.toolCalls"
                  :key="idx"
                  class="tool-call-badge"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                  </svg>
                  <span>{{ tool.name }}</span>
                </div>
              </div>
              
              <!-- Message text (supports markdown-like formatting) -->
              <div class="message-text">
                {{ msg.content }}
              </div>
              
              <!-- Streaming indicator -->
              <span
                v-if="msg.status === 'streaming'"
                class="streaming-cursor"
              />
            </div>
            
            <!-- Message actions (hover) -->
            <div
              v-if="hoveredMessageId === msg.id && msg.status === 'complete'"
              class="message-actions ai-actions"
            >
              <button
                class="action-btn"
                title="引用"
                @click="handleQuoteMessage(msg)"
              >
                <MessageSquareQuote class="w-3.5 h-3.5" />
              </button>
            </div>
            
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </template>
      </div>
      
      <!-- Empty state -->
      <div
        v-if="visibleMessages.length === 0"
        class="empty-chat"
      >
        <p>等待对话开始...</p>
      </div>
    </div>
    
    <!-- Bottom Chat Input -->
    <div
      v-if="initPhase === 'executing' || initPhase === 'ready'"
      class="chat-input-area"
    >
      <ChatInput
        ref="chatInputRef"
        :quote="currentQuote"
        placeholder="输入追加消息..."
        @send="handleSendMessage"
        @clear-quote="handleClearQuote"
      />
    </div>
  </div>
</template>

<style scoped>
.streaming-info {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
  overflow: hidden;
}

/* ========================================
   Chat Header
   ======================================== */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
}

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.btn-lock {
  padding: 6px 10px;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 120ms ease-out;
}

.btn-lock:hover {
  background: var(--any-bg-tertiary);
}

.btn-lock.locked {
  background: var(--td-state-waiting-bg, rgba(255, 184, 0, 0.1));
  border-color: var(--td-state-waiting, #FFB800);
  color: var(--td-state-waiting, #FFB800);
}

/* ========================================
   Research Progress Container
   ======================================== */
.research-progress-container {
  flex-shrink: 0;
  padding: 12px 16px 0;
}

/* ========================================
   Chat Container (Dialog Style)
   ======================================== */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chat-container::-webkit-scrollbar {
  width: 6px;
}

.chat-container::-webkit-scrollbar-track {
  background: transparent;
}

.chat-container::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 3px;
}

.chat-container::-webkit-scrollbar-thumb:hover {
  background: var(--any-text-muted);
}

/* ========================================
   Chat Message
   ======================================== */
.chat-message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

/* User message: right aligned */
.chat-message.user {
  flex-direction: row-reverse;
}

/* Avatar */
.avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-avatar {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-avatar {
  background: var(--any-bg-tertiary);
  padding: 6px;
}

.ai-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Message Content */
.message-content {
  max-width: 75%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-message {
  align-items: flex-end;
}

.ai-message {
  align-items: flex-start;
}

/* Message Bubble */
.message-bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.user-message .message-bubble {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-bubble {
  background: var(--any-bg-secondary);
  color: var(--any-text-primary);
  border: 1px solid var(--any-border);
  border-bottom-left-radius: 4px;
}

/* Message Time */
.message-time {
  font-size: 11px;
  color: var(--any-text-muted);
  padding: 0 4px;
}

/* ========================================
   Thinking Indicator
   ======================================== */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  color: var(--any-text-secondary);
  font-size: 14px;
}

.thinking-spinner {
  width: 18px;
  height: 18px;
  color: var(--td-state-thinking, #00D9FF);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ========================================
   Tool Calls Badge
   ======================================== */
.tool-calls {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.tool-call-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--td-state-thinking-bg, rgba(0, 217, 255, 0.1));
  border: 1px solid var(--td-state-thinking, #00D9FF);
  border-radius: 12px;
  font-size: 11px;
  color: var(--td-state-thinking, #00D9FF);
}

.tool-call-badge svg {
  opacity: 0.8;
}

/* ========================================
   Message Text
   ======================================== */
.message-text {
  white-space: pre-wrap;
}

/* Streaming Cursor */
.streaming-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: var(--td-state-thinking, #00D9FF);
  margin-left: 2px;
  animation: blink 1s ease-in-out infinite;
  vertical-align: text-bottom;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Empty Chat State */
.empty-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--any-text-muted);
  font-size: 14px;
}

.empty-chat p {
  margin: 0;
}

/* ========================================
   Init Phase Styles
   ======================================== */

.init-phase-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 8px 0;
}

/* Analyzing Card */
.analyzing-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--any-bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--any-border);
}

.analyzing-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--td-state-thinking-bg, rgba(0, 217, 255, 0.1));
  border-radius: 10px;
  color: var(--td-state-thinking, #00D9FF);
}

.spin-icon {
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.analyzing-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.analyzing-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.analyzing-desc {
  font-size: 13px;
  color: var(--any-text-secondary);
  margin: 0;
  line-height: 1.5;
}

.analyzing-progress {
  height: 4px;
  background: var(--any-bg-tertiary);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 4px;
}

.progress-bar {
  height: 100%;
  width: 30%;
  background: linear-gradient(90deg, var(--td-state-thinking, #00D9FF), var(--td-state-executing, #00FF88));
  border-radius: 2px;
  animation: progress-indeterminate 1.5s ease-in-out infinite;
}

@keyframes progress-indeterminate {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(200%); }
  100% { transform: translateX(-100%); }
}

/* Clarification Card */
.clarification-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: var(--any-bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--any-border);
}

.clarification-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.clarification-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  color: var(--td-state-waiting, #FFB800);
}

.clarification-title-wrap {
  flex: 1;
}

.clarification-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.clarification-subtitle {
  font-size: 13px;
  color: var(--any-text-secondary);
  margin: 4px 0 0 0;
}

.clarification-reasoning {
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.6;
  margin: 0;
  padding: 12px;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
}

.missing-info-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.missing-info-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: var(--any-text-primary);
  padding: 10px 12px;
  background: rgba(255, 184, 0, 0.08);
  border-radius: 8px;
  border-left: 3px solid var(--td-state-waiting, #FFB800);
}

.missing-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--td-state-waiting, #FFB800);
  margin-top: 6px;
  flex-shrink: 0;
}

.suggested-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
  text-align: left;
}

.option-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.option-btn.selected {
  background: rgba(0, 217, 255, 0.08);
  border-color: var(--td-state-thinking, #00D9FF);
}

.option-checkbox {
  width: 18px;
  height: 18px;
  border: 2px solid var(--any-border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 150ms ease;
}

.option-btn.selected .option-checkbox {
  background: var(--td-state-thinking, #00D9FF);
  border-color: var(--td-state-thinking, #00D9FF);
}

.option-checkbox svg {
  width: 12px;
  height: 12px;
  color: var(--any-bg-primary);
}

.option-text {
  font-size: 14px;
  color: var(--any-text-primary);
  line-height: 1.4;
}

.clarification-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--any-border);
}

/* Init Phase Transition */
.init-phase-enter-active,
.init-phase-leave-active {
  transition: all 300ms ease;
}

.init-phase-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.init-phase-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ========================================
   Bottom Chat Input Area
   ======================================== */
.chat-input-area {
  flex-shrink: 0;
  padding: 12px 16px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-primary);
}

/* ========================================
   Message Actions (Hover)
   ======================================== */
.message-actions {
  display: flex;
  gap: 4px;
  margin-top: 4px;
}

.message-actions.ai-actions {
  margin-top: 4px;
}

.action-btn {
  padding: 4px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 6px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.action-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-secondary);
}

/* ========================================
   Quoted Preview
   ======================================== */
.quoted-preview {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 8px;
  font-size: 12px;
  margin-bottom: 4px;
  max-width: 100%;
}

.quoted-label {
  color: #6366f1;
  font-weight: 500;
  flex-shrink: 0;
}

.quoted-text {
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ========================================
   Edit Mode
   ======================================== */
.chat-message.editing {
  background: rgba(99, 102, 241, 0.05);
  padding: 8px;
  margin: -8px;
  border-radius: 12px;
}

.edit-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 300px;
}

.edit-textarea {
  width: 100%;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border-hover);
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  color: var(--any-text-primary);
  resize: none;
  outline: none;
}

.edit-textarea:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.edit-btn-cancel,
.edit-btn-save {
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  transition: all 150ms ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.edit-btn-cancel {
  background: transparent;
  border: 1px solid var(--any-border);
  color: var(--any-text-secondary);
}

.edit-btn-cancel:hover {
  background: var(--any-bg-hover);
}

.edit-btn-save {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: white;
}

.edit-btn-save:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}

/* Edited Badge */
.edited-badge {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 4px;
}

</style>
