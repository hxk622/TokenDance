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
    <!-- Icon -->
    <div class="intent-icon">
      <span class="text-3xl">{{ intent.icon }}</span>
    </div>
    
    <!-- Content -->
    <div class="intent-content">
      <h3 class="intent-title">{{ intent.title }}</h3>
      <p class="intent-description">{{ intent.description }}</p>
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
  @apply -translate-y-1 scale-[1.02];
  background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.85) 100%);
}

.intent-icon {
  @apply w-16 h-16 rounded-xl flex items-center justify-center
         transition-transform duration-300;
  background: var(--card-gradient);
}

.intent-card:hover .intent-icon {
  @apply scale-110;
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
