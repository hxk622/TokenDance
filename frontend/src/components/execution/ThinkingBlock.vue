<script setup lang="ts">
import { ref, computed } from 'vue'

export interface ThinkingBlockProps {
  content: string
  isStreaming?: boolean
  defaultExpanded?: boolean
}

const props = withDefaults(defineProps<ThinkingBlockProps>(), {
  isStreaming: false,
  defaultExpanded: false,
})

const expanded = ref(props.defaultExpanded)

const toggleExpanded = () => {
  expanded.value = !expanded.value
}

const displayText = computed(() => {
  if (props.isStreaming) {
    return '正在思考...'
  }
  return '思考过程'
})
</script>

<template>
  <div class="mb-3 rounded-lg bg-bg-tertiary/50 overflow-hidden border border-border-default">
    <!-- 折叠头部 -->
    <button
      class="w-full px-4 py-2.5 flex items-center justify-between text-sm hover:bg-bg-tertiary transition-colors"
      @click="toggleExpanded"
    >
      <span class="flex items-center gap-2">
        <!-- 思考图标 -->
        <svg
          v-if="isStreaming"
          class="w-4 h-4 text-accent-primary animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="2"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <svg
          v-else
          class="w-4 h-4 text-text-secondary"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
          />
        </svg>
        <span class="font-medium text-text-primary">{{ displayText }}</span>
      </span>
      
      <!-- 展开/折叠图标 -->
      <svg
        class="w-4 h-4 text-text-secondary transition-transform duration-200"
        :class="{ 'rotate-180': expanded }"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 9l-7 7-7-7"
        />
      </svg>
    </button>
    
    <!-- 展开内容 -->
    <div
      v-show="expanded"
      class="px-4 py-3 text-sm text-text-secondary border-t border-border-default animate-slideDown"
    >
      <div class="whitespace-pre-wrap leading-relaxed">
        {{ content }}
        <span
          v-if="isStreaming && content"
          class="inline-block w-1 h-4 bg-accent-primary ml-1 animate-pulse"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-slideDown {
  animation: slideDown 0.2s ease-out;
}
</style>
