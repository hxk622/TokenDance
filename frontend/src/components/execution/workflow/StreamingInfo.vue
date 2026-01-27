<script setup lang="ts">
import { ref, computed, nextTick, watch, toRef } from 'vue'
import { Lightbulb, ArrowRight, Loader2, Edit3, MessageSquareQuote, RotateCcw, ChevronDown } from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'
import type { IntentValidationResponse } from '@/api/services/session'
import { ChatInput, ChatFormMessage, BrowserPreviewCard, AssistantBubble, UserBubble } from '@/components/execution/chat'
import { ResearchProgress, InterventionPanel } from '@/components/execution/research'
import MessageActions from '@/components/chat/MessageActions.vue'
import { messageApi } from '@/api/message'
import ResearchBlockList from '@/components/execution/research/blocks/ResearchBlockList.vue'
import type { BlockEvent } from '@/composables/useResearchBlocks'
import type { 
  ResearchProgress as ResearchProgressType,
  SearchQuery,
  ResearchSource,
  ResearchPhase,
  ResearchIntervention,
} from '@/components/execution/research/types'
import { getCredibilityLevel } from '@/components/execution/research/types'
import type { 
  ChatMessage, 
  QuoteInfo, 
  SendMessagePayload,
  FormSubmitPayload,
  FormField,
  FormGroup,
  MessageStatus,
  BrowserEvent,
  BrowserAction
} from '@/components/execution/chat/types'
import { useExecutionStore } from '@/stores/execution'

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
  /** 是否使用 Block 模式展示研究进度 (v2.0) */
  useBlockMode?: boolean
  /** 任务是否正在运行 */
  isRunning?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  initPhase: 'executing',
  preflightResult: null,
  userInput: '',
  userAvatar: 'U',
  isDeepResearch: false,
  useBlockMode: true,  // 默认启用 Block 模式
  isRunning: false,
})

// Emits
const emit = defineEmits<{
  proceed: [updatedInput?: string]
  'update-input': [input: string]
  /** 研究干预事件 */
  'research-intervene': [intervention: ResearchIntervention]
  /** 用户发送消息事件 (Chat Mode 下触发执行) - 传递完整 payload 包括附件 */
  'send-message': [payload: SendMessagePayload]
  /** 终止任务执行 */
  'stop': []
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
// Research Progress State (深度研究进度 - 从 execution store 读取)
// ========================================
const executionStore = useExecutionStore()
// 使用 store 的 researchProgress 作为数据源 (单一数据源原则)
const researchProgress = toRef(executionStore, 'researchProgress')
const chatPhase = toRef(executionStore, 'chatPhase')
const isResearchProgressCollapsed = ref(false)
const isInterventionPanelCollapsed = ref(false)
const isInterventionSending = ref(false)

// Block 模式相关 ref
const researchBlockListRef = ref<InstanceType<typeof ResearchBlockList> | null>(null)

// 以下方法保留为向后兼容 (legacy API)
// 实际数据更新现在通过 SSE 事件 -> executionStore -> researchProgress 流动
// 这些方法现在为空操作，保留接口以便将来可能的手动更新场景
function initResearchProgress() {
  // Store 会在接收到 RESEARCH_PHASE_CHANGE 等事件时自动初始化
  console.log('[StreamingInfo] initResearchProgress called (now handled by store)')
}

function updateResearchPhase(_phase: ResearchPhase, _phaseProgress: number = 0) {
  // Store 会在接收到 RESEARCH_PHASE_CHANGE 事件时自动更新
  console.log('[StreamingInfo] updateResearchPhase called (now handled by store)')
}

function addResearchQuery(_queryId: string, _text: string, _status: 'pending' | 'running' | 'done' | 'failed' = 'running') {
  // Store 会在接收到 RESEARCH_QUERY_START 事件时自动更新
  console.log('[StreamingInfo] addResearchQuery called (now handled by store)')
}

function updateResearchQuery(_queryId: string, _resultCount: number) {
  // Store 会在接收到 RESEARCH_QUERY_RESULT 事件时自动更新
  console.log('[StreamingInfo] updateResearchQuery called (now handled by store)')
}

function addResearchSource(
  _sourceId: string,
  _url: string,
  _domain: string,
  _title: string,
  _status: 'pending' | 'reading' | 'done' | 'skipped' | 'failed' = 'reading'
) {
  // Store 会在接收到 RESEARCH_SOURCE_START 事件时自动更新
  console.log('[StreamingInfo] addResearchSource called (now handled by store)')
}

function updateResearchSource(
  _sourceId: string,
  _credibility: number,
  _sourceType: string = 'unknown',
  _extractedFacts: string[] = []
) {
  // Store 会在接收到 RESEARCH_SOURCE_DONE 事件时自动更新
  console.log('[StreamingInfo] updateResearchSource called (now handled by store)')
}

function updateResearchProgressState(
  _currentAction: string,
  _overallProgress?: number,
  _estimatedTime?: number
) {
  // Store 会在接收到 RESEARCH_PROGRESS_UPDATE 事件时自动更新
  console.log('[StreamingInfo] updateResearchProgressState called (now handled by store)')
}

// ========================================
// Block 模式方法
// ========================================

/** 发送事件到 Block 列表 (用于 Block 模式) */
function sendBlockEvent(event: BlockEvent) {
  researchBlockListRef.value?.handleEvent(event)
}

// Open URL in new tab
function openUrl(url: string) {
  window.open(url, '_blank')
}

// ========================================
// Browser Events (内联浏览器截图卡片)
// ========================================

/** 添加浏览器事件 (用于内联展示浏览器操作) */
function addBrowserEvent(
  url: string,
  action: BrowserAction = 'navigate',
  actionDescription?: string,
  screenshot?: string,
  title?: string
) {
  const event: BrowserEvent = {
    id: `browser-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    url,
    action,
    actionDescription,
    screenshot,
    title,
    timestamp: Date.now(),
    loading: !screenshot
  }
  browserEvents.value.push(event)
  scrollToBottom()
  return event.id
}

/** 更新浏览器事件截图 */
function updateBrowserScreenshot(eventId: string, screenshot: string, title?: string) {
  const event = browserEvents.value.find(e => e.id === eventId)
  if (event) {
    event.screenshot = screenshot
    event.loading = false
    if (title) event.title = title
  }
}

/** 清除所有浏览器事件 */
function clearBrowserEvents() {
  browserEvents.value = []
}

// 研究干预处理
function handleResearchIntervene(intervention: ResearchIntervention) {
  emit('research-intervene', intervention)
}

// 设置干预发送状态（供父组件调用）
function setInterventionSending(sending: boolean) {
  isInterventionSending.value = sending
}

// ========================================
// Chat Messages (replacing old LogEntry)
// 使用 store 的 chatMessages 作为单一数据源
// SSE 事件处理会自动更新 store 的 chatMessages
// ========================================

// 注意: messages 现在直接引用 store 的 chatMessages
// 任何对 messages.value 的修改都会直接影响 store
const messages = toRef(executionStore, 'chatMessages')
const browserEvents = ref<BrowserEvent[]>([])
const chatContainerRef = ref<HTMLElement | null>(null)
const isScrollLocked = ref(false)
const userScrollTimeout = ref<ReturnType<typeof setTimeout> | null>(null)
const isUserScrolling = ref(false)
const unreadCount = ref(0)
const visibleItemLimit = ref(120)
const loadMoreStep = 60

const chatPhaseLabel = computed(() => {
  switch (chatPhase.value) {
    case 'planning':
      return '规划中'
    case 'executing':
      return '执行中'
    case 'answering':
      return '汇总中'
    case 'done':
      return '已完成'
    default:
      return ''
  }
})

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

// Demo helper: Simulate AI response stream (demo sessions only)
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

const isDemoSession = computed(() => props.sessionId === 'demo' || props.sessionId.startsWith('demo-'))

// Start demo when entering executing phase (demo sessions only)
watch(() => props.initPhase, (phase) => {
  if (phase === 'executing' && isDemoSession.value && messages.value.length <= 1) {
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
      unreadCount.value = 0
    }
  })
}
function isNearBottom() {
  const container = chatContainerRef.value
  if (!container) return true
  const threshold = 80
  return container.scrollHeight - container.scrollTop - container.clientHeight < threshold
}

function handleJumpToBottom() {
  unreadCount.value = 0
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

  if (isNearBottom()) {
    unreadCount.value = 0
  }
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
  
  // Clear quote and input (explicit clear as safety measure)
  currentQuote.value = null
  chatInputRef.value?.clear()
  
  // Emit full payload to parent (including attachments) for message service
  emit('send-message', payload)
}

// Start editing a message
function startEditMessage(msg: ChatMessage) {
  // TODO: Implement inline edit UI
  // For now, show alert that this feature is coming soon
  alert('消息编辑功能即将上线...')
  // editingMessageId.value = msg.id
  // editingContent.value = msg.content
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

// Handle message feedback (fire-and-forget with rollback on error)
function handleMessageFeedback(msgId: string, feedback: 'like' | 'dislike' | null, onError?: () => void) {
  messageApi.submitFeedback(msgId, feedback).catch((error) => {
    console.error('Failed to submit feedback:', error)
    onError?.()
  })
}

// Handle regenerate last AI message
function handleRegenerateMessage() {
  // TODO: Implement regenerate logic - re-run agent from last user message
  console.log('Regenerate message requested')
}

// Handle message intervention (pause button on AI message)
function handleMessageIntervene() {
  // Emit stop event to parent to pause execution
  emit('stop')
  console.log('User intervention requested from message')
}

// Handle planning card toggle (AnyGen style)
function handlePlanningToggle(msgId: string, collapsed: boolean) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg?.planning) {
    msg.planning.collapsed = collapsed
  }
}

// Handle timeline step toggle (AnyGen style)
function handleStepToggle(msgId: string, stepId: string, collapsed: boolean) {
  const msg = messages.value.find(m => m.id === msgId)
  if (msg?.executionSteps) {
    const step = msg.executionSteps.find(s => s.id === stepId)
    if (step) {
      step.collapsed = collapsed
    }
  }
}

// Handle source click from timeline (AnyGen style)
function handleSourceClick(source: { url: string; favicon?: string; domain: string }) {
  window.open(source.url, '_blank')
}

// Check if a message is the last assistant message
function isLastAssistantMessage(msgId: string): boolean {
  const assistantMessages = visibleMessages.value.filter(m => m.role === 'assistant')
  return assistantMessages.length > 0 && assistantMessages[assistantMessages.length - 1].id === msgId
}

// Check if any message is currently streaming
const isAnyMessageStreaming = computed(() => {
  return messages.value.some(m => m.status === 'streaming' || m.status === 'thinking')
})

// Filter visible messages (hide deprecated unless expanded)
const visibleMessages = computed(() => {
  return messages.value.filter(m => !m.deprecated)
})

// Combined timeline: messages + browser events, sorted by timestamp
type TimelineItem = 
  | { type: 'message'; data: ChatMessage }
  | { type: 'browser'; data: BrowserEvent }

const timelineItemsAll = computed<TimelineItem[]>(() => {
  const items: TimelineItem[] = []
  
  // Add visible messages
  visibleMessages.value.forEach(msg => {
    items.push({ type: 'message', data: msg })
  })
  
  // Add browser events
  browserEvents.value.forEach(event => {
    items.push({ type: 'browser', data: event })
  })
  
  // Sort by timestamp
  return items.sort((a, b) => a.data.timestamp - b.data.timestamp)
})

const timelineItems = computed<TimelineItem[]>(() => {
  const items = timelineItemsAll.value
  if (items.length <= visibleItemLimit.value) return items
  return items.slice(-visibleItemLimit.value)
})

const hiddenItemCount = computed(() => {
  return Math.max(0, timelineItemsAll.value.length - timelineItems.value.length)
})

function loadEarlier() {
  visibleItemLimit.value = Math.min(
    visibleItemLimit.value + loadMoreStep,
    timelineItemsAll.value.length
  )
}

watch(
  () => timelineItemsAll.value.length,
  (next, prev) => {
    if (next <= prev) return
    const delta = next - prev
    if (!isNearBottom() || isScrollLocked.value || isUserScrolling.value) {
      unreadCount.value += delta
      return
    }
    scrollToBottom()
  }
)

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
  // Research progress methods - Legacy Mode (深度研究进度透明化 - 旧版)
  researchProgress,
  initResearchProgress,
  updateResearchPhase,
  addResearchQuery,
  updateResearchQuery,
  addResearchSource,
  updateResearchSource,
  updateResearchProgressState,
  // Research progress methods - Block Mode (Block 模式 v2.0)
  sendBlockEvent,
  researchBlockListRef,
  // Research intervention methods (研究干预)
  setInterventionSending,
  // Browser events (内联浏览器截图卡片 - Flatten 原则)
  browserEvents,
  addBrowserEvent,
  updateBrowserScreenshot,
  clearBrowserEvents,
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

          <!-- Clarification Options (Selectable) -->
          <div
            v-if="preflightResult.clarification_options?.length || preflightResult.suggested_questions?.length"
            class="suggested-options"
          >
            <!-- New format: clarification_options with label/value -->
            <button
              v-for="(opt, idx) in preflightResult.clarification_options"
              :key="'opt-' + idx"
              :class="['option-btn', { selected: selectedOptions.includes(opt.value) }]"
              @click="toggleOption(opt.value)"
            >
              <span class="option-checkbox">
                <svg
                  v-if="selectedOptions.includes(opt.value)"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="3"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </span>
              <span class="option-text">{{ opt.label }}</span>
            </button>
            <!-- Legacy fallback: suggested_questions (string array) -->
            <button
              v-for="(q, idx) in (preflightResult.clarification_options?.length ? [] : preflightResult.suggested_questions)"
              :key="'q-' + idx"
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
      <div class="chat-title-group">
        <span class="chat-title">对话</span>
        <span
          v-if="chatPhaseLabel"
          class="chat-phase-badge"
        >
          {{ chatPhaseLabel }}
        </span>
      </div>
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

    <!-- Research Progress - Block Mode (v2.0 Block 化进度面板) -->
    <div
      v-if="(initPhase === 'executing' || initPhase === 'ready') && isDeepResearch && useBlockMode"
      class="research-blocks-container streaming-section"
    >
      <ResearchBlockList
        ref="researchBlockListRef"
        :topic="userInput"
        :show-summary="true"
        @block-expand="(blockId) => console.log('Block expanded:', blockId)"
        @source-click="(source) => console.log('Source clicked:', source)"
        @open-url="openUrl"
        @intervention="handleResearchIntervene"
      />
    </div>

    <!-- Research Progress Panel - Legacy Mode (旧版深度研究进度面板) -->
    <div
      v-if="(initPhase === 'executing' || initPhase === 'ready') && isDeepResearch && !useBlockMode && researchProgress"
      class="research-progress-container streaming-section"
    >
      <ResearchProgress
        :progress="researchProgress"
        :collapsed="isResearchProgressCollapsed"
        @toggle-collapse="isResearchProgressCollapsed = !isResearchProgressCollapsed"
        @source-click="(source) => console.log('Source clicked:', source)"
        @open-url="openUrl"
      />
    </div>

    <!-- Research Intervention Panel (研究干预面板 - 两种模式共用) -->
    <div
      v-if="initPhase === 'executing' && isDeepResearch && (researchProgress || useBlockMode)"
      class="streaming-section"
    >
      <InterventionPanel
        :progress="researchProgress"
        :collapsed="isInterventionPanelCollapsed"
        :sending="isInterventionSending"
        @intervene="handleResearchIntervene"
        @toggle-collapse="isInterventionPanelCollapsed = !isInterventionPanelCollapsed"
      />
    </div>

    <!-- Chat Messages & Browser Events (Dialog Style - Flatten principle) -->
    <div
      v-if="initPhase === 'executing' || initPhase === 'ready'"
      ref="chatContainerRef"
      class="chat-container"
      @scroll="handleUserScroll"
    >
      <div
        v-if="hiddenItemCount > 0"
        class="load-earlier"
      >
        <button
          class="load-earlier-btn"
          @click="loadEarlier"
        >
          <ChevronDown class="load-earlier-icon" />
          <span>加载更早内容 ({{ hiddenItemCount }})</span>
        </button>
      </div>
      <template
        v-for="item in timelineItems"
        :key="item.data.id"
      >
        <!-- Browser Preview Card (inline) -->
        <BrowserPreviewCard
          v-if="item.type === 'browser'"
          :url="item.data.url"
          :screenshot="item.data.screenshot"
          :title="item.data.title"
          :timestamp="item.data.timestamp"
          :action="item.data.action"
          :action-description="item.data.actionDescription"
          :loading="item.data.loading"
          class="browser-card-item"
          @open-url="openUrl"
        />

        <!-- Chat Message -->
        <div
          v-else
          class="chat-message-wrapper"
        >
          <!-- User Message (Right side) - AnyGen Style -->
          <UserBubble
            v-if="(item.data as ChatMessage).role === 'user'"
            :message="item.data as ChatMessage"
            :avatar="userAvatar"
            :editable="editingMessageId !== item.data.id"
            @edit="startEditMessage(item.data as ChatMessage)"
            @copy="() => {}"
          />

          <!-- AI Message (Left side) - AnyGen Style -->
          <template v-else>
            <!-- Form message (special case) -->
            <div
              v-if="(item.data as ChatMessage).contentType === 'form'"
              class="chat-message assistant"
            >
              <div class="avatar ai-avatar">
                <img
                  src="/logo.svg"
                  alt="AI"
                >
              </div>
              <div class="message-content ai-message">
                <ChatFormMessage
                  :title="(item.data as ChatMessage).content"
                  :fields="(item.data as ChatMessage).formFields"
                  :groups="(item.data as ChatMessage).formGroups"
                  :interactive="(item.data as ChatMessage).isInteractive !== false"
                  :submitted="(item.data as ChatMessage).formSubmitted"
                  :submitted-values="(item.data as ChatMessage).formValues"
                  @submit="(values) => handleFormSubmit(item.data.id, values)"
                  @edit="handleFormEdit(item.data.id)"
                />
                <span class="message-time">{{ formatTime(item.data.timestamp) }}</span>
              </div>
            </div>

            <!-- Normal AI message - AssistantBubble -->
            <AssistantBubble
              v-else
              :message="item.data as ChatMessage"
              :is-last-message="isLastAssistantMessage(item.data.id)"
              :is-streaming="isAnyMessageStreaming"
              :is-running="isRunning"
              @planning-toggle="(collapsed) => handlePlanningToggle(item.data.id, collapsed)"
              @step-toggle="(stepId, collapsed) => handleStepToggle(item.data.id, stepId, collapsed)"
              @source-click="handleSourceClick"
              @feedback="(fb, onError) => handleMessageFeedback(item.data.id, fb, onError)"
              @regenerate="handleRegenerateMessage"
              @intervene="handleMessageIntervene"
            />
          </template>
        </div>
      </template>
      
      <!-- Empty state -->
      <div
        v-if="timelineItems.length === 0"
        class="empty-chat"
      >
        <p>等待对话开始...</p>
      </div>

      <div
        v-if="unreadCount > 0"
        class="new-message-indicator"
      >
        <button
          class="new-message-btn"
          @click="handleJumpToBottom"
        >
          <ChevronDown class="new-message-icon" />
          <span>有 {{ unreadCount }} 条新消息</span>
        </button>
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
        :is-running="isRunning"
        placeholder="输入追加消息..."
        @send="handleSendMessage"
        @clear-quote="handleClearQuote"
        @stop="emit('stop')"
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
  overflow: visible;
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
  background: var(--any-bg-primary);
  position: sticky;
  top: 0;
  z-index: 5;
}
.chat-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}
.chat-phase-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--any-text-secondary);
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
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
   Research Progress Container (Legacy & Block)
   ======================================== */
.research-progress-container {
  flex-shrink: 0;
  padding: 12px 16px 0;
}

.research-blocks-container {
  flex-shrink: 0;
  padding: 12px 16px;
  max-height: 50vh;
  overflow-y: auto;
}

.streaming-section {
  border-bottom: 1px solid var(--any-border);
}

.research-blocks-container::-webkit-scrollbar {
  width: 6px;
}

.research-blocks-container::-webkit-scrollbar-track {
  background: transparent;
}

.research-blocks-container::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 3px;
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
  position: relative;
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
   Browser Preview Card (Inline)
   ======================================== */
.browser-card-item {
  margin: 0;
  max-width: 100%;
}

/* Load earlier */
.load-earlier {
  display: flex;
  justify-content: center;
}

.load-earlier-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
  color: var(--any-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 150ms ease;
}

.load-earlier-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.load-earlier-icon {
  width: 14px;
  height: 14px;
  transform: rotate(180deg);
}

/* New message indicator */
.new-message-indicator {
  position: sticky;
  bottom: 8px;
  display: flex;
  justify-content: center;
  pointer-events: none;
}

.new-message-btn {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
  color: var(--any-text-primary);
  font-size: 12px;
  cursor: pointer;
  transition: all 150ms ease;
}

.new-message-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.new-message-icon {
  width: 14px;
  height: 14px;
}

/* ========================================
   Chat Message
   ======================================== */
.chat-message-wrapper {
  width: 100%;
}

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
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.user-avatar {
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
  color: white;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-avatar {
  background: var(--any-bg-tertiary);
  padding: 4px;
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
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
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
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(var(--any-bg-primary-rgb, 255, 255, 255), 0.92);
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
  background: rgba(0, 184, 217, 0.1);
  border-radius: 8px;
  font-size: 12px;
  margin-bottom: 4px;
  max-width: 100%;
}

.quoted-label {
  color: #00B8D9;
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
  background: rgba(0, 184, 217, 0.05);
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
  border-color: #00B8D9;
  box-shadow: 0 0 0 3px rgba(0, 184, 217, 0.1);
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
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
  border: none;
  color: white;
}

.edit-btn-save:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 184, 217, 0.4);
}

/* Edited Badge */
.edited-badge {
  font-size: 11px;
  opacity: 0.7;
  margin-left: 4px;
}

</style>
