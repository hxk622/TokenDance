<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  disabled?: boolean
  isStreaming?: boolean
}>()

const emit = defineEmits<{
  (e: 'send', content: string): void
  (e: 'stop'): void
}>()

const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const canSend = computed(() => inputText.value.trim().length > 0 && !props.disabled)

function handleSend() {
  if (!canSend.value) return
  
  emit('send', inputText.value.trim())
  inputText.value = ''
  
  // Reset textarea height
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleInput() {
  // Auto-resize textarea
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

function handleStop() {
  emit('stop')
}
</script>

<template>
  <div class="border-t border-border-default bg-bg-secondary p-4">
    <div class="max-w-4xl mx-auto">
      <div class="relative flex items-end gap-3">
        <!-- Text Input -->
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            :disabled="disabled || isStreaming"
            @keydown="handleKeyDown"
            @input="handleInput"
            placeholder="Type your message..."
            rows="1"
            class="w-full resize-none rounded-2xl border border-border-default bg-bg-primary px-4 py-3 pr-12 text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary focus:outline-none focus:ring-1 focus:ring-accent-primary disabled:opacity-50 disabled:cursor-not-allowed"
            :class="{ 'animate-pulse': isStreaming }"
          />
        </div>

        <!-- Send/Stop Button -->
        <button
          v-if="!isStreaming"
          @click="handleSend"
          :disabled="!canSend"
          class="flex-shrink-0 w-10 h-10 rounded-full bg-accent-primary text-white flex items-center justify-center hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
        </button>

        <button
          v-else
          @click="handleStop"
          class="flex-shrink-0 w-10 h-10 rounded-full bg-red-500 text-white flex items-center justify-center hover:bg-red-600 transition-colors"
        >
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
      </div>

      <!-- Streaming indicator -->
      <div v-if="isStreaming" class="mt-2 text-xs text-text-tertiary flex items-center gap-2">
        <span class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce" style="animation-delay: 0ms"/>
          <span class="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce" style="animation-delay: 150ms"/>
          <span class="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce" style="animation-delay: 300ms"/>
        </span>
        Agent is thinking...
      </div>

      <!-- Hints -->
      <div v-else class="mt-2 text-xs text-text-tertiary">
        Press Enter to send, Shift + Enter for new line
      </div>
    </div>
  </div>
</template>
