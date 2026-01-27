<script setup lang="ts">
/**
 * AssistantBubble - AI 消息气泡容器
 * 
 * 对标 AnyGen 的 Assistant Bubble:
 * - 左侧 Avatar (产品 Logo)
 * - PlanningCard (可折叠规划/思考卡片)
 * - ExecutionTimeline (执行步骤 Timeline)
 * - 消息内容 (支持流式渲染)
 * - 底部操作栏 (复制、点赞、重新生成)
 */
import { computed } from 'vue'
import { Loader2 } from 'lucide-vue-next'
import PlanningCard from './PlanningCard.vue'
import ExecutionTimeline from './ExecutionTimeline.vue'
import MessageActions from '@/components/chat/MessageActions.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'
import type { ChatMessage, Source, PlanningData, ExecutionStep } from './types'

interface Props {
  message: ChatMessage
  /** AI 头像 URL */
  avatarSrc?: string
  /** 是否是最后一条 AI 消息 */
  isLastMessage?: boolean
  /** 是否有任何消息正在流式输出 */
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  avatarSrc: '/logo.svg',
  isLastMessage: false,
  isStreaming: false
})

const emit = defineEmits<{
  'planning-toggle': [collapsed: boolean]
  'step-toggle': [stepId: string, collapsed: boolean]
  'source-click': [source: Source]
  'feedback': [feedback: 'like' | 'dislike' | null, onError?: () => void]
  'regenerate': []
}>()

// Status helpers
const isThinking = computed(() => props.message.status === 'thinking')
const isStreamingContent = computed(() => props.message.status === 'streaming')
const isComplete = computed(() => props.message.status === 'complete')

// Planning data
const planning = computed<PlanningData | undefined>(() => props.message.planning)

// Execution steps
const executionSteps = computed<ExecutionStep[]>(() => props.message.executionSteps || [])

// Has any structured content (planning or timeline)
const hasStructuredContent = computed(() => {
  return planning.value || executionSteps.value.length > 0
})

// Message content (text)
const messageContent = computed(() => props.message.content || '')

// Has text content to show
const hasTextContent = computed(() => {
  return messageContent.value.trim().length > 0
})

const showActions = computed(() => {
  return hasTextContent.value && isComplete.value
})

// Event handlers
function handlePlanningToggle(collapsed: boolean) {
  emit('planning-toggle', collapsed)
}

function handleStepToggle(stepId: string, collapsed: boolean) {
  emit('step-toggle', stepId, collapsed)
}

function handleSourceClick(source: Source) {
  emit('source-click', source)
}

function handleFeedback(feedback: 'like' | 'dislike' | null, onError?: () => void) {
  emit('feedback', feedback, onError)
}

function handleRegenerate() {
  emit('regenerate')
}

// Format timestamp
function formatTime(timestamp: number): string {
  const now = Date.now()
  const diff = now - timestamp
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="assistant-bubble">
    <!-- Avatar -->
    <div class="bubble-avatar">
      <img
        :src="avatarSrc"
        alt="AI"
      >
    </div>

    <!-- Content area -->
    <div class="bubble-content">
      <!-- Thinking indicator (when no content yet) -->
      <div
        v-if="isThinking && !hasStructuredContent && !hasTextContent"
        class="thinking-indicator"
      >
        <Loader2 class="thinking-spinner" />
        <span>{{ message.statusText || '正在思考...' }}</span>
      </div>

      <!-- Structured content -->
      <div
        v-if="hasStructuredContent"
        class="structured-content"
      >
        <!-- Planning Card -->
        <PlanningCard
          v-if="planning"
          :data="planning"
          class="planning-section"
          @update:collapsed="handlePlanningToggle"
        />

        <!-- Execution Timeline -->
        <ExecutionTimeline
          v-if="executionSteps.length > 0"
          :steps="executionSteps"
          class="timeline-section"
          @step-toggle="handleStepToggle"
          @source-click="handleSourceClick"
        />
      </div>

      <!-- Text content -->
      <div
        v-if="hasTextContent || isStreamingContent"
        :class="['text-content', { 'is-final': isComplete, 'is-streaming': isStreamingContent, 'is-draft': !isComplete && !isStreamingContent }]"
      >
        <div class="message-text">
          <MarkdownRenderer :content="messageContent" />
          <!-- Streaming cursor -->
          <span
            v-if="isStreamingContent && isLastMessage"
            class="streaming-cursor"
          />
        </div>
        <!-- Message actions (as widget under content) -->
        <div
          v-if="showActions"
          class="bubble-actions"
        >
          <MessageActions
            :message-id="message.id"
            :content="messageContent"
            :feedback="(message as any).feedback"
            :is-last-message="isLastMessage"
            :is-streaming="isStreaming"
            class="bubble-actions-inner"
            @feedback="handleFeedback"
            @regenerate="handleRegenerate"
          />
        </div>
      </div>

      <!-- Timestamp -->
      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
    </div>
  </div>
</template>

<style scoped>
.assistant-bubble {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

/* Avatar */
.bubble-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--any-bg-tertiary);
  padding: 0;
  overflow: hidden;
}

.bubble-avatar img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Content area */
.bubble-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Thinking indicator */
.thinking-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
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

/* Structured content */
.structured-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.planning-section {
  /* PlanningCard styles handled by the component */
}

.timeline-section {
  /* ExecutionTimeline styles handled by the component */
}

/* Text content */
.text-content {
  padding: 12px 16px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}
.text-content.is-final,
.text-content.is-streaming {
  color: var(--any-text-primary);
}

.text-content.is-draft {
  color: var(--any-text-tertiary);
}

.text-content.is-final .message-text :deep(.markdown-content),
.text-content.is-final .message-text :deep(.markdown-content p),
.text-content.is-final .message-text :deep(.markdown-content li),
.text-content.is-final .message-text :deep(.markdown-content blockquote),
.text-content.is-streaming .message-text :deep(.markdown-content),
.text-content.is-streaming .message-text :deep(.markdown-content p),
.text-content.is-streaming .message-text :deep(.markdown-content li),
.text-content.is-streaming .message-text :deep(.markdown-content blockquote) {
  color: var(--any-text-primary);
}

.text-content.is-draft .message-text :deep(.markdown-content),
.text-content.is-draft .message-text :deep(.markdown-content p),
.text-content.is-draft .message-text :deep(.markdown-content li),
.text-content.is-draft .message-text :deep(.markdown-content blockquote) {
  color: var(--any-text-tertiary);
}

.message-text :deep(.markdown-content p) {
  margin: 0 0 0.6em;
}

.message-text :deep(.markdown-content p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(.markdown-content h1),
.message-text :deep(.markdown-content h2),
.message-text :deep(.markdown-content h3),
.message-text :deep(.markdown-content h4),
.message-text :deep(.markdown-content h5),
.message-text :deep(.markdown-content h6) {
  margin: 0.8em 0 0.4em;
  color: inherit;
}

.message-text :deep(.markdown-content ul),
.message-text :deep(.markdown-content ol) {
  margin: 0.4em 0 0.6em 1.25em;
}

.message-text :deep(.markdown-content li) {
  margin-bottom: 0.25em;
}

.message-text :deep(.markdown-content code) {
  background: var(--any-bg-tertiary);
  color: inherit;
}

.message-text :deep(.markdown-content pre) {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
}

/* Streaming cursor */
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

/* Actions */
.bubble-actions {
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--any-border);
  display: flex;
}

.bubble-actions :deep(.bubble-actions-inner) {
  margin-top: 0 !important;
}

/* Timestamp */
.message-time {
  font-size: 11px;
  color: var(--any-text-muted);
  padding: 0 4px;
}
</style>
