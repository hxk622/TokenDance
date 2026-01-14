<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import MessageBubble from './MessageBubble.vue'

// Types
export interface Message {
  id: string
  role: 'user' | 'assistant' | 'error'
  content: string
  timestamp: Date
}

// Props
interface Props {
  messages: Message[]
}

const props = defineProps<Props>()

// Refs
const scrollContainer = ref<HTMLDivElement>()

// Methods
const scrollToBottom = (smooth = true) => {
  if (!scrollContainer.value) return
  
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTo({
        top: scrollContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      })
    }
  })
}

// Auto-scroll when messages change
watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  }
)
</script>

<template>
  <div ref="scrollContainer" class="message-list">
    <div v-if="messages.length === 0" class="empty-state">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="1.5"
        stroke="currentColor"
        class="empty-icon"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
        />
      </svg>
      <p class="empty-text">开始对话</p>
      <p class="empty-hint">发送消息与 AI Agent 互动</p>
    </div>

    <div v-else class="messages-container">
      <MessageBubble
        v-for="message in messages"
        :key="message.id"
        :role="message.role"
        :content="message.content"
        :timestamp="message.timestamp"
      />
    </div>
  </div>
</template>

<style scoped>
.message-list {
  @apply flex-1 overflow-y-auto bg-gray-50;
}

.empty-state {
  @apply flex flex-col items-center justify-center h-full text-center px-4;
}

.empty-icon {
  @apply w-16 h-16 text-gray-300 mb-4;
}

.empty-text {
  @apply text-xl font-medium text-gray-600 mb-1;
}

.empty-hint {
  @apply text-sm text-gray-400;
}

.messages-container {
  @apply py-4;
}
</style>
