<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Send, Paperclip, Mic, X } from 'lucide-vue-next'
import type { QuoteInfo, SendMessagePayload } from './types'

interface Props {
  disabled?: boolean
  placeholder?: string
  quote?: QuoteInfo | null
  maxLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入消息...',
  quote: null,
  maxLength: 2000
})

const emit = defineEmits<{
  send: [payload: SendMessagePayload]
  'clear-quote': []
}>()

// Input state
const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const isFocused = ref(false)

// Computed
const canSend = computed(() => {
  return inputText.value.trim().length > 0 && !props.disabled
})

const charCount = computed(() => inputText.value.length)
const isNearLimit = computed(() => charCount.value > props.maxLength * 0.9)

// Auto-resize textarea
function autoResize() {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  }
}

// Handle input
function handleInput() {
  autoResize()
}

// Handle key down
function handleKeyDown(e: KeyboardEvent) {
  // Enter to send (without shift)
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// Send message
function handleSend() {
  if (!canSend.value) return
  
  const payload: SendMessagePayload = {
    content: inputText.value.trim(),
    quote: props.quote || undefined
  }
  
  emit('send', payload)
  inputText.value = ''
  autoResize()
  
  // Clear quote after send
  if (props.quote) {
    emit('clear-quote')
  }
}

// Clear quote
function handleClearQuote() {
  emit('clear-quote')
}

// Attachment (placeholder)
function handleAttachment() {
  // TODO: Implement file attachment
  console.log('Attachment clicked')
}

// Voice input (placeholder)
function handleVoice() {
  // TODO: Implement voice input
  console.log('Voice clicked')
}

// Focus input
function focus() {
  textareaRef.value?.focus()
}

// Watch for quote changes to focus input
watch(() => props.quote, (newQuote) => {
  if (newQuote) {
    focus()
  }
})

// Expose methods
defineExpose({
  focus,
  clear: () => { inputText.value = '' }
})
</script>

<template>
  <div :class="['chat-input-wrapper', { disabled, focused: isFocused }]">
    <!-- Quote Preview -->
    <Transition name="quote">
      <div
        v-if="quote"
        class="quote-preview"
      >
        <div class="quote-content">
          <span class="quote-label">回复</span>
          <span class="quote-text">{{ quote.content.slice(0, 50) }}{{ quote.content.length > 50 ? '...' : '' }}</span>
        </div>
        <button
          class="quote-close"
          @click="handleClearQuote"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </Transition>
    
    <!-- Input Area -->
    <div class="input-area">
      <!-- Attachment Button (placeholder) -->
      <button
        class="input-btn attachment-btn"
        title="添加附件"
        @click="handleAttachment"
      >
        <Paperclip class="w-4 h-4" />
      </button>
      
      <!-- Text Input -->
      <div class="textarea-wrapper">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          :placeholder="placeholder"
          :disabled="disabled"
          :maxlength="maxLength"
          rows="1"
          class="input-textarea"
          @input="handleInput"
          @keydown="handleKeyDown"
          @focus="isFocused = true"
          @blur="isFocused = false"
        />
        
        <!-- Character count (near limit) -->
        <span
          v-if="isNearLimit"
          :class="['char-count', { warning: charCount >= maxLength }]"
        >
          {{ charCount }}/{{ maxLength }}
        </span>
      </div>
      
      <!-- Voice Button (placeholder) -->
      <button
        class="input-btn voice-btn"
        title="语音输入"
        @click="handleVoice"
      >
        <Mic class="w-4 h-4" />
      </button>
      
      <!-- Send Button -->
      <button
        :class="['send-btn', { active: canSend }]"
        :disabled="!canSend"
        title="发送"
        @click="handleSend"
      >
        <Send class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  transition: all 200ms ease;
}

.chat-input-wrapper.focused {
  border-color: var(--any-border-hover);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.chat-input-wrapper.disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* Quote Preview */
.quote-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border);
  border-radius: 16px 16px 0 0;
}

.quote-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.quote-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--td-state-thinking, #00D9FF);
  text-transform: uppercase;
  flex-shrink: 0;
}

.quote-text {
  font-size: 12px;
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quote-close {
  flex-shrink: 0;
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.quote-close:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Quote Transition */
.quote-enter-active,
.quote-leave-active {
  transition: all 200ms ease;
}

.quote-enter-from,
.quote-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Input Area */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px;
}

/* Input Buttons */
.input-btn {
  flex-shrink: 0;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.input-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-secondary);
}

/* Textarea Wrapper */
.textarea-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-end;
}

.input-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 150px;
  padding: 6px 0;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  color: var(--any-text-primary);
}

.input-textarea::placeholder {
  color: var(--any-text-muted);
}

.input-textarea:disabled {
  cursor: not-allowed;
}

/* Character Count */
.char-count {
  position: absolute;
  right: 4px;
  bottom: 4px;
  font-size: 10px;
  color: var(--any-text-muted);
}

.char-count.warning {
  color: var(--exec-warning, #FFB800);
}

/* Send Button */
.send-btn {
  flex-shrink: 0;
  padding: 8px;
  background: var(--any-bg-tertiary);
  border: none;
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: not-allowed;
  transition: all 150ms ease;
}

.send-btn.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  cursor: pointer;
}

.send-btn.active:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}

.send-btn:disabled {
  cursor: not-allowed;
}
</style>
