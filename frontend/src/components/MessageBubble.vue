<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import 'highlight.js/styles/github-dark.css'

// Configure marked
marked.use({
  breaks: true,
  gfm: true
})

// Props
interface Props {
  role: 'user' | 'assistant' | 'error'
  content: string
  timestamp?: Date
}

const props = defineProps<Props>()

// Computed
const isUser = computed(() => props.role === 'user')
const isError = computed(() => props.role === 'error')

const renderedContent = computed(() => {
  if (props.role === 'user') {
    return props.content // Plain text for user messages
  }
  // Markdown for assistant and error messages
  return marked.parse(props.content)
})

const formattedTime = computed(() => {
  if (!props.timestamp) return ''
  const hours = props.timestamp.getHours().toString().padStart(2, '0')
  const minutes = props.timestamp.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
})
</script>

<template>
  <div
    class="message-bubble"
    :class="{
      'message-user': isUser,
      'message-assistant': role === 'assistant',
      'message-error': isError
    }"
  >
    <div class="message-content-wrapper">
      <!-- User message: plain text -->
      <div v-if="isUser" class="message-text">
        {{ content }}
      </div>
      
      <!-- Assistant/Error message: markdown -->
      <div
        v-else
        class="message-text markdown-body"
        v-html="renderedContent"
      />
      
      <!-- Timestamp -->
      <div v-if="formattedTime" class="message-timestamp">
        {{ formattedTime }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-bubble {
  @apply flex mb-4 px-4;
}

.message-user {
  @apply justify-end;
}

.message-assistant,
.message-error {
  @apply justify-start;
}

.message-content-wrapper {
  @apply max-w-[70%] rounded-lg px-4 py-3 shadow-sm;
}

.message-user .message-content-wrapper {
  @apply bg-blue-600 text-white;
}

.message-assistant .message-content-wrapper {
  @apply bg-white border border-gray-200;
}

.message-error .message-content-wrapper {
  @apply bg-red-50 border border-red-200;
}

.message-text {
  @apply text-sm leading-relaxed;
}

.message-user .message-text {
  @apply whitespace-pre-wrap break-words;
}

.message-timestamp {
  @apply text-xs mt-1 opacity-70;
}

/* Markdown styling */
.markdown-body {
  @apply text-gray-800;
}

.markdown-body :deep(p) {
  @apply mb-2 last:mb-0;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  @apply font-semibold mt-4 mb-2 first:mt-0;
}

.markdown-body :deep(h1) { @apply text-2xl; }
.markdown-body :deep(h2) { @apply text-xl; }
.markdown-body :deep(h3) { @apply text-lg; }

.markdown-body :deep(code) {
  @apply px-1.5 py-0.5 bg-gray-100 rounded text-sm font-mono;
}

.markdown-body :deep(pre) {
  @apply my-2 p-4 bg-gray-900 rounded-lg overflow-x-auto;
}

.markdown-body :deep(pre code) {
  @apply p-0 bg-transparent text-gray-100;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  @apply ml-4 mb-2;
}

.markdown-body :deep(li) {
  @apply mb-1;
}

.markdown-body :deep(blockquote) {
  @apply border-l-4 border-gray-300 pl-4 italic my-2;
}

.markdown-body :deep(a) {
  @apply text-blue-600 hover:underline;
}

.message-error .markdown-body {
  @apply text-red-800;
}

.message-error .markdown-body :deep(code) {
  @apply bg-red-100;
}
</style>
