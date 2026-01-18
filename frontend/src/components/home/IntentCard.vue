<script setup lang="ts">
import { computed } from 'vue'

export interface IntentType {
  id: 'research' | 'ppt' | 'code'
  icon: string
  title: string
  description: string
  color: string
  gradient: string
}

const props = defineProps<{
  intent: IntentType
}>()

const emit = defineEmits<{
  (e: 'select', intent: IntentType): void
}>()

const cardStyle = computed(() => ({
  '--card-color': props.intent.color,
  '--card-gradient': props.intent.gradient
}))
</script>

<template>
  <button
    class="intent-card group"
    :style="cardStyle"
    @click="emit('select', intent)"
  >
    <!-- Icon - 使用 SVG 图标而非 Emoji -->
    <div class="intent-icon">
      <svg
        v-if="intent.icon === 'research' || intent.id === 'research'"
        class="w-8 h-8"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <svg
        v-else-if="intent.icon === 'ppt' || intent.id === 'ppt'"
        class="w-8 h-8"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
      <svg
        v-else
        class="w-8 h-8"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="1.5"
          d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
        />
      </svg>
    </div>
    
    <!-- Content -->
    <div class="intent-content">
      <h3 class="intent-title">
        {{ intent.title }}
      </h3>
      <p class="intent-description">
        {{ intent.description }}
      </p>
    </div>
    
    <!-- Hover Glow -->
    <div class="intent-glow" />
  </button>
</template>

<style scoped>
.intent-card {
  @apply relative flex flex-col items-center gap-4 p-6 rounded-2xl
         bg-white/80 backdrop-blur-sm border border-white/50
         shadow-lg hover:shadow-xl
         transition-all duration-300 ease-out
         cursor-pointer overflow-hidden
         w-44 h-48;
}

.intent-card:hover {
  @apply -translate-y-1;
  background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.85) 100%);
}

.intent-icon {
  @apply w-16 h-16 rounded-xl flex items-center justify-center
         text-white transition-colors duration-300;
  background: var(--card-gradient);
}

.intent-card:hover .intent-icon {
  @apply text-white;
}

.intent-content {
  @apply text-center;
}

.intent-title {
  @apply text-base font-semibold text-gray-800 mb-1;
}

.intent-description {
  @apply text-xs text-gray-500 line-clamp-2;
}

.intent-glow {
  @apply absolute inset-0 opacity-0 transition-opacity duration-300 pointer-events-none;
  background: radial-gradient(circle at center, var(--card-color) 0%, transparent 70%);
}

.intent-card:hover .intent-glow {
  @apply opacity-10;
}
</style>
