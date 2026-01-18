<template>
  <div class="chat-input-container">
    <div class="max-w-4xl mx-auto">
      <div class="relative flex items-end gap-3">
        <!-- Text Input -->
        <div class="flex-1 relative input-glow-wrapper">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            :disabled="disabled || isStreaming"
            placeholder="Type your message..."
            rows="1"
            class="chat-textarea"
            :class="{ 'is-streaming': isStreaming }"
            @keydown="handleKeyDown"
            @input="handleInput"
          />
          <div class="input-glow" />
        </div>

        <!-- Send/Stop Button -->
        <button
          v-if="!isStreaming"
          :disabled="!canSend"
          class="send-button"
          @click="handleSend"
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
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </button>

        <button
          v-else
          class="stop-button"
          @click="handleStop"
        >
          <svg
            class="w-5 h-5"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <rect
              x="6"
              y="6"
              width="12"
              height="12"
              rx="2"
            />
          </svg>
        </button>
      </div>

      <!-- Streaming indicator -->
      <div
        v-if="isStreaming"
        class="mt-3 text-xs text-gray-400 flex items-center gap-2"
      >
        <span class="thinking-dots">
          <span class="dot" />
          <span class="dot" />
          <span class="dot" />
        </span>
        <span class="thinking-text">Agent is thinking...</span>
      </div>

      <!-- Hints -->
      <div
        v-else
        class="mt-2 text-xs text-gray-500"
      >
        Press <kbd class="kbd">Enter</kbd> to send, <kbd class="kbd">Shift + Enter</kbd> for new line
      </div>
    </div>
  </div>
</template>

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

<style scoped>
.chat-input-container {
  @apply border-t border-gray-800 p-4;
  background: rgba(10, 10, 11, 0.95);
  backdrop-filter: blur(12px);
}

.input-glow-wrapper {
  position: relative;
}

.chat-textarea {
  @apply w-full resize-none rounded-2xl px-5 py-3.5 pr-12
         text-sm text-white placeholder-gray-500
         bg-gray-900 border border-gray-700
         transition-all duration-200;
}

.chat-textarea:focus {
  @apply outline-none border-gray-600;
}

.chat-textarea:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.chat-textarea.is-streaming {
  @apply border-indigo-500/50;
}

/* Gradient glow effect on focus */
.input-glow {
  position: absolute;
  inset: -2px;
  border-radius: 18px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4, #6366f1);
  background-size: 300% 300%;
  opacity: 0;
  z-index: -1;
  transition: opacity 0.3s ease;
  filter: blur(8px);
}

.chat-textarea:focus ~ .input-glow {
  opacity: 0.4;
  animation: gradient-shift 3s ease infinite;
}

@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* Send Button */
.send-button {
  @apply flex-shrink-0 w-11 h-11 rounded-xl
         flex items-center justify-center
         transition-all duration-200;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.send-button:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
}

.send-button:disabled {
  @apply opacity-40 cursor-not-allowed;
  transform: none;
  box-shadow: none;
}

/* Stop Button */
.stop-button {
  @apply flex-shrink-0 w-11 h-11 rounded-xl
         flex items-center justify-center
         transition-all duration-200;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
  animation: pulse-stop 1.5s ease-in-out infinite;
}

.stop-button:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

@keyframes pulse-stop {
  0%, 100% { box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3); }
  50% { box-shadow: 0 4px 20px rgba(239, 68, 68, 0.5); }
}

/* Thinking Dots */
.thinking-dots {
  @apply flex gap-1;
}

.dot {
  @apply w-1.5 h-1.5 rounded-full;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0ms; }
.dot:nth-child(2) { animation-delay: 160ms; }
.dot:nth-child(3) { animation-delay: 320ms; }

@keyframes thinking-bounce {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-6px);
    opacity: 1;
  }
}

.thinking-text {
  animation: thinking-fade 2s ease-in-out infinite;
}

@keyframes thinking-fade {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* Keyboard hints */
.kbd {
  @apply px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 font-mono text-[10px];
}
</style>
