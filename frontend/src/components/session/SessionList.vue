<script setup lang="ts">
import { computed } from 'vue'
import type { Session } from '@/api/session'
import SessionItem from './SessionItem.vue'

const props = defineProps<{
  sessions: Session[]
  currentSessionId?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'select', sessionId: string): void
  (e: 'delete', sessionId: string): void
  (e: 'new'): void
}>()

const sortedSessions = computed(() => {
  return [...props.sessions].sort((a, b) => 
    new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )
})
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- Header -->
    <div class="p-4 border-b border-border-default">
      <button
        @click="emit('new')"
        class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-hover transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
        </svg>
        New Chat
      </button>
    </div>

    <!-- Session List -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="p-4 text-center text-text-tertiary">
        <svg class="w-6 h-6 animate-spin mx-auto text-accent-primary" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" opacity="0.25"/>
          <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <p class="mt-2 text-sm">Loading sessions...</p>
      </div>

      <div v-else-if="sortedSessions.length === 0" class="p-4 text-center text-text-tertiary">
        <p class="text-sm">No sessions yet</p>
        <p class="text-xs mt-1">Start a new chat to begin</p>
      </div>

      <div v-else class="divide-y divide-border-default">
        <SessionItem
          v-for="session in sortedSessions"
          :key="session.id"
          :session="session"
          :active="session.id === currentSessionId"
          @select="emit('select', session.id)"
          @delete="emit('delete', session.id)"
        />
      </div>
    </div>
  </div>
</template>
