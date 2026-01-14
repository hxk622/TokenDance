<script setup lang="ts">
import { ref, watch } from 'vue'

// Props
interface Props {
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入消息... (Enter 发送, Shift+Enter 换行)'
})

// Emits
const emit = defineEmits<{
  send: [message: string]
}>()

// State
const message = ref('')
const textarea = ref<HTMLTextAreaElement>()

// Methods
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const sendMessage = () => {
  const content = message.value.trim()
  if (content && !props.disabled) {
    emit('send', content)
    message.value = ''
    // Reset textarea height
    if (textarea.value) {
      textarea.value.style.height = 'auto'
    }
  }
}

// Auto-resize textarea
const autoResize = () => {
  if (textarea.value) {
    textarea.value.style.height = 'auto'
    textarea.value.style.height = `${textarea.value.scrollHeight}px`
  }
}

// Watch message changes to auto-resize
watch(message, () => {
  autoResize()
})
</script>

<template>
  <div class="input-box">
    <div class="input-container">
      <textarea
        ref="textarea"
        v-model="message"
        :disabled="disabled"
        :placeholder="placeholder"
        class="input-textarea"
        rows="1"
        @keydown="handleKeyDown"
      />
      <button
        :disabled="disabled || !message.trim()"
        class="send-button"
        @click="sendMessage"
      >
        <svg
          v-if="!disabled"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="send-icon"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
          />
        </svg>
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke-width="2"
          stroke="currentColor"
          class="send-icon animate-spin"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
          />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input-box {
  @apply border-t border-gray-200 bg-white p-4;
}

.input-container {
  @apply flex items-end gap-2 max-w-4xl mx-auto;
}

.input-textarea {
  @apply flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 
         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
         disabled:bg-gray-100 disabled:cursor-not-allowed
         min-h-[44px] max-h-[200px] overflow-y-auto;
}

.send-button {
  @apply flex-shrink-0 w-10 h-10 rounded-lg bg-blue-600 text-white
         hover:bg-blue-700 active:bg-blue-800
         disabled:bg-gray-300 disabled:cursor-not-allowed
         flex items-center justify-center
         transition-colors duration-150;
}

.send-icon {
  @apply w-5 h-5;
}
</style>
