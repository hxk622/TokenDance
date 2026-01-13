<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '@/api/session'
import ThinkingBlock from '@/components/execution/ThinkingBlock.vue'
import ToolCallBlock from '@/components/execution/ToolCallBlock.vue'
import MarkdownRenderer from '@/components/common/MarkdownRenderer.vue'

const props = defineProps<{
  message: Message
  isStreaming?: boolean
}>()

const isUser = computed(() => props.message.role === 'user')
const hasThinking = computed(() => !!props.message.thinking)
const hasToolCalls = computed(() => props.message.tool_calls && props.message.tool_calls.length > 0)
const hasCitations = computed(() => props.message.citations && props.message.citations.length > 0)

// Transform tool_calls to match ToolCallBlock interface
const formattedToolCalls = computed(() => {
  if (!props.message.tool_calls) return []
  return props.message.tool_calls.map(tc => ({
    id: tc.id,
    name: tc.name,
    params: tc.args || {},
    status: tc.status as 'pending' | 'running' | 'success' | 'error',
    result: tc.result ? JSON.stringify(tc.result) : undefined,
    error: tc.error,
  }))
})
</script>

<template>
  <div 
    class="flex gap-3 py-4"
    :class="isUser ? 'justify-end' : 'justify-start'"
  >
    <!-- Agent Avatar -->
    <div 
      v-if="!isUser"
      class="w-8 h-8 rounded-full bg-accent-gradient flex items-center justify-center flex-shrink-0"
    >
      <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    </div>

    <!-- Message Content -->
    <div class="max-w-[85%] min-w-0">
      <!-- User Message -->
      <div 
        v-if="isUser"
        class="rounded-2xl rounded-br-md px-4 py-3 bg-accent-primary text-white"
      >
        <div class="whitespace-pre-wrap">{{ message.content }}</div>
      </div>

      <!-- Assistant Message -->
      <div v-else class="space-y-3">
        <!-- Thinking Block -->
        <ThinkingBlock
          v-if="hasThinking"
          :content="message.thinking || ''"
          :isStreaming="isStreaming"
        />

        <!-- Tool Calls -->
        <ToolCallBlock
          v-for="toolCall in formattedToolCalls"
          :key="toolCall.id"
          :toolCall="toolCall"
        />

        <!-- Message Content -->
        <div 
          v-if="message.content"
          class="rounded-2xl rounded-bl-md px-4 py-3 bg-bg-secondary border border-border-default"
        >
          <MarkdownRenderer :content="message.content" />
          
          <!-- Streaming cursor -->
          <span 
            v-if="isStreaming" 
            class="inline-block w-1.5 h-4 bg-accent-primary ml-1 animate-pulse"
          />
        </div>

        <!-- Empty streaming state -->
        <div 
          v-if="isStreaming && !message.content && !hasThinking && !hasToolCalls"
          class="rounded-2xl rounded-bl-md px-4 py-3 bg-bg-secondary border border-border-default"
        >
          <span class="inline-block w-1.5 h-4 bg-accent-primary animate-pulse" />
        </div>

        <!-- Citations -->
        <div 
          v-if="hasCitations" 
          class="px-4 py-3 rounded-lg bg-bg-tertiary/30 border border-border-default"
        >
          <div class="text-xs text-text-tertiary mb-2">Sources:</div>
          <div class="flex flex-wrap gap-2">
            <a 
              v-for="citation in message.citations" 
              :key="citation.index"
              :href="citation.url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1.5 px-2 py-1 bg-bg-secondary rounded-md text-xs text-text-secondary hover:text-accent-primary hover:bg-bg-tertiary transition-colors"
            >
              <span class="w-4 h-4 bg-accent-primary/20 text-accent-primary rounded-full flex items-center justify-center text-[10px] font-medium">
                {{ citation.index }}
              </span>
              <span class="truncate max-w-[150px]">{{ citation.title || citation.domain || 'Source' }}</span>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- User Avatar -->
    <div 
      v-if="isUser"
      class="w-8 h-8 rounded-full bg-bg-tertiary flex items-center justify-center flex-shrink-0"
    >
      <svg class="w-4 h-4 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    </div>
  </div>
</template>
