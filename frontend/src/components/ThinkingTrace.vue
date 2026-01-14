<script setup lang="ts">
// Props
interface Props {
  iteration: number
  reasoning: string
  visible: boolean
}

defineProps<Props>()
</script>

<template>
  <transition name="fade">
    <div v-if="visible" class="thinking-trace">
      <div class="thinking-header">
        <div class="thinking-icon-wrapper">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            class="thinking-icon animate-pulse"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"
            />
          </svg>
        </div>
        <span class="thinking-title">Agent 思考中...</span>
        <span class="iteration-badge">Iteration {{ iteration }}</span>
      </div>
      
      <div class="thinking-content">
        <p class="reasoning-text">{{ reasoning }}</p>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.thinking-trace {
  @apply mx-4 mb-4 rounded-lg border-l-4 border-yellow-400 bg-yellow-50 shadow-sm;
}

.thinking-header {
  @apply flex items-center gap-2 px-4 py-3 border-b border-yellow-100;
}

.thinking-icon-wrapper {
  @apply flex-shrink-0;
}

.thinking-icon {
  @apply w-5 h-5 text-yellow-600;
}

.thinking-title {
  @apply flex-1 text-sm font-medium text-yellow-800;
}

.iteration-badge {
  @apply px-2 py-1 text-xs font-medium bg-yellow-200 text-yellow-800 rounded;
}

.thinking-content {
  @apply px-4 py-3;
}

.reasoning-text {
  @apply text-sm text-yellow-900 leading-relaxed whitespace-pre-wrap;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  @apply transition-opacity duration-200;
}

.fade-enter-from,
.fade-leave-to {
  @apply opacity-0;
}
</style>
