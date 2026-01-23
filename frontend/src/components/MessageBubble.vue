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
      <div
        v-if="isUser"
        class="message-text"
      >
        {{ content }}
      </div>
      
      <!-- Assistant/Error message: markdown -->
      <div
        v-else
        class="message-text markdown-body"
        v-html="renderedContent"
      />
      
      <!-- Timestamp -->
      <div
        v-if="formattedTime"
        class="message-timestamp"
      >
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
  @apply max-w-[70%] rounded-2xl px-4 py-3;
}

.message-user .message-content-wrapper {
  background: linear-gradient(135deg, #00B8D9 0%, #00D9FF 100%);
  @apply text-white shadow-lg shadow-indigo-500/20;
}

.message-assistant .message-content-wrapper {
  @apply bg-bg-tertiary border border-border-default text-text-primary;
}

.message-error .message-content-wrapper {
  @apply bg-red-950/50 border border-red-800/50 text-red-200;
}

.message-text {
  @apply text-sm leading-relaxed;
}

.message-user .message-text {
  @apply whitespace-pre-wrap break-words;
}

.message-timestamp {
  @apply text-xs mt-1 opacity-60;
}

/* Markdown styling - Dark Theme */
.markdown-body {
  @apply text-text-primary;
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
  @apply font-semibold mt-4 mb-2 first:mt-0 text-white;
}

.markdown-body :deep(h1) { @apply text-2xl; }
.markdown-body :deep(h2) { @apply text-xl; }
.markdown-body :deep(h3) { @apply text-lg; }

.markdown-body :deep(code) {
  @apply px-1.5 py-0.5 bg-bg-elevated rounded text-sm font-mono text-accent-primary;
}

.markdown-body :deep(pre) {
  @apply my-2 p-4 bg-bg-primary rounded-lg overflow-x-auto border border-border-default;
}

.markdown-body :deep(pre code) {
  @apply p-0 bg-transparent text-text-primary;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  @apply ml-4 mb-2;
}

.markdown-body :deep(li) {
  @apply mb-1 text-text-secondary;
}

.markdown-body :deep(blockquote) {
  @apply border-l-4 border-accent-primary/50 pl-4 italic my-2 text-text-secondary;
}

.markdown-body :deep(a) {
  @apply text-accent-primary hover:text-accent-hover hover:underline;
}

.message-error .markdown-body {
  @apply text-red-200;
}

.message-error .markdown-body :deep(code) {
  @apply bg-red-900/50 text-red-300;
}
</style>
