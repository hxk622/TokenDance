<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { Lightbulb, ArrowRight, Loader2 } from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'
import type { IntentValidationResponse } from '@/api/services/session'

// Init phase types
export type InitPhase = 'idle' | 'analyzing' | 'needs-clarification' | 'ready' | 'executing'

// Chat message types
export type MessageRole = 'user' | 'assistant'
export type MessageStatus = 'thinking' | 'streaming' | 'complete' | 'error'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  status: MessageStatus
  timestamp: number
  // For tool calls display
  toolCalls?: { name: string; args?: string }[]
}

interface Props {
  sessionId: string
  initPhase?: InitPhase
  preflightResult?: IntentValidationResponse | null
  userInput?: string
  userAvatar?: string  // URL or initial letter
}

const props = withDefaults(defineProps<Props>(), {
  initPhase: 'executing',
  preflightResult: null,
  userInput: '',
  userAvatar: 'U'
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

// Format timestamp
function formatTime(timestamp: number): string {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// Get user avatar display (initial or image)
const userAvatarDisplay = computed(() => {
  if (props.userAvatar.startsWith('http') || props.userAvatar.startsWith('/')) {
    return { type: 'image', src: props.userAvatar }
  }
  return { type: 'initial', text: props.userAvatar.charAt(0).toUpperCase() }
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
  // New method to add messages from parent
  addMessage: (msg: ChatMessage) => {
    messages.value.push(msg)
    scrollToBottom()
  },
  // Update the last AI message (for streaming)
  updateLastAIMessage: (content: string, status?: MessageStatus) => {
    const lastAI = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAI) {
      lastAI.content = content
      if (status) lastAI.status = status
      scrollToBottom()
    }
  }
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

    <!-- Chat Messages (Dialog Style) -->
    <div
      v-if="initPhase === 'executing' || initPhase === 'ready'"
      ref="chatContainerRef"
      class="chat-container"
      @scroll="handleUserScroll"
    >
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['chat-message', msg.role]"
      >
        <!-- User Message (Right side) -->
        <template v-if="msg.role === 'user'">
          <div class="message-content user-message">
            <div class="message-bubble">
              {{ msg.content }}
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
            <!-- Thinking indicator -->
            <div
              v-if="msg.status === 'thinking'"
              class="thinking-indicator"
            >
              <Loader2 class="thinking-spinner" />
              <span>正在思考...</span>
            </div>
            
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
            
            <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
          </div>
        </template>
      </div>
      
      <!-- Empty state -->
      <div
        v-if="messages.length === 0"
        class="empty-chat"
      >
        <p>等待对话开始...</p>
      </div>
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

</style>
