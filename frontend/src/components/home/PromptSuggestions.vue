<script setup lang="ts">
export interface PromptSuggestion {
  id: string
  text: string
  icon: string
}

defineProps<{
  suggestions: PromptSuggestion[]
}>()

const emit = defineEmits<{
  (e: 'select', text: string): void
}>()
</script>

<template>
  <div class="prompt-suggestions">
    <div class="suggestions-header">
      <span class="suggestions-line" />
      <span class="suggestions-label">试试这些</span>
      <span class="suggestions-line" />
    </div>
    
    <div class="suggestions-list">
      <button
        v-for="suggestion in suggestions"
        :key="suggestion.id"
        class="suggestion-item group"
        @click="emit('select', suggestion.text)"
      >
        <span class="suggestion-icon">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </span>
        <span class="suggestion-text">{{ suggestion.text }}</span>
        <svg 
          class="suggestion-arrow" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.prompt-suggestions {
  @apply w-full max-w-2xl mx-auto;
}

.suggestions-header {
  @apply flex items-center gap-4 mb-6;
}

.suggestions-line {
  @apply flex-1 h-px bg-gradient-to-r from-transparent via-gray-300 to-transparent;
}

.suggestions-label {
  @apply text-sm text-gray-400 font-medium;
}

.suggestions-list {
  @apply space-y-3;
}

.suggestion-item {
  @apply w-full flex items-center gap-3 px-5 py-4
         rounded-xl bg-white/60 backdrop-blur-sm
         border border-white/50 shadow-sm
         hover:bg-white/80 hover:shadow-md hover:border-cyan-200/50
         transition-all duration-200 text-left;
}

.suggestion-icon {
  @apply flex items-center justify-center w-5 h-5 text-slate-400 flex-shrink-0;
}

.suggestion-text {
  @apply flex-1 text-sm text-gray-600 group-hover:text-gray-800
         transition-colors line-clamp-1;
}

.suggestion-arrow {
  @apply w-4 h-4 text-gray-400 opacity-0 -translate-x-2
         group-hover:opacity-100 group-hover:translate-x-0 group-hover:text-cyan-500
         transition-all duration-200 flex-shrink-0;
}
</style>
