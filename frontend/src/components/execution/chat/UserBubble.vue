<script setup lang="ts">
/**
 * UserBubble - 用户消息气泡
 * 
 * 对标 AnyGen 的 User Bubble:
 * - 右对齐
 * - 悬停显示编辑/复制按钮
 * - 支持附件展示
 */
import { ref, computed } from 'vue'
import { Edit2, Copy, Check, Paperclip } from 'lucide-vue-next'
import type { ChatMessage } from './types'

interface Attachment {
  id: string
  name: string
  type: 'file' | 'image'
  url?: string
  size?: number
}

interface Props {
  message: ChatMessage
  /** 附件列表 */
  attachments?: Attachment[]
  /** 是否允许编辑 */
  editable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  attachments: () => [],
  editable: true
})

const emit = defineEmits<{
  'edit': [content: string]
  'copy': []
}>()

// Hover state
const isHovered = ref(false)
const copied = ref(false)

// Content
const content = computed(() => props.message.content || '')

// Has attachments
const hasAttachments = computed(() => props.attachments.length > 0)

// Copy to clipboard
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(content.value)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
    emit('copy')
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// Edit message
function handleEdit() {
  emit('edit', content.value)
}

// Format file size
function formatSize(bytes?: number): string {
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
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
  <div class="user-bubble-wrapper">
    <!-- Timestamp -->
    <span class="message-time">{{ formatTime(message.timestamp) }}</span>

    <!-- Bubble container -->
    <div
      class="user-bubble"
      @mouseenter="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <!-- Hover actions (left side) -->
      <Transition name="fade">
        <div
          v-if="isHovered"
          class="hover-actions"
        >
          <button
            v-if="editable"
            class="action-btn"
            title="编辑"
            @click="handleEdit"
          >
            <Edit2 :size="14" />
          </button>
          <button
            class="action-btn"
            title="复制"
            @click="handleCopy"
          >
            <Check
              v-if="copied"
              :size="14"
            />
            <Copy
              v-else
              :size="14"
            />
          </button>
        </div>
      </Transition>

      <!-- Message content -->
      <div class="bubble-body">
        <!-- Attachments -->
        <div
          v-if="hasAttachments"
          class="attachments"
        >
          <div
            v-for="att in attachments"
            :key="att.id"
            class="attachment-item"
          >
            <Paperclip
              :size="14"
              class="att-icon"
            />
            <span class="att-name">{{ att.name }}</span>
            <span
              v-if="att.size"
              class="att-size"
            >{{ formatSize(att.size) }}</span>
          </div>
        </div>

        <!-- Text content -->
        <div class="message-text">
          {{ content }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.user-bubble-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

/* Timestamp */
.message-time {
  font-size: 11px;
  color: var(--any-text-muted);
  padding: 0 4px;
}

/* Bubble container */
.user-bubble {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  max-width: 85%;
}

/* Hover actions */
.hover-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: var(--any-bg-tertiary);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Fade transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Bubble body */
.bubble-body {
  padding: 12px 16px;
  background: var(--any-accent-bg, #E3F2FD);
  border-radius: 16px 16px 4px 16px;
  min-width: 40px;
}

/* Dark mode adjustment */
:root.dark .bubble-body,
.dark .bubble-body {
  background: var(--any-accent-bg-dark, #1E3A5F);
}

/* Attachments */
.attachments {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--any-border-light, rgba(0, 0, 0, 0.08));
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--any-text-secondary);
}

.att-icon {
  flex-shrink: 0;
  color: var(--any-text-muted);
}

.att-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.att-size {
  flex-shrink: 0;
  color: var(--any-text-muted);
}

/* Text content */
.message-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--any-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
