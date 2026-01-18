<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Session } from '@/api/session'

const props = defineProps<{
  session: Session
  active?: boolean
}>()

const emit = defineEmits<{
  (e: 'select'): void
  (e: 'delete'): void
}>()

const showMenu = ref(false)

const formattedDate = computed(() => {
  const date = new Date(props.session.updated_at)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' })
  } else {
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }
})

const statusIcon = computed(() => {
  switch (props.session.status) {
    case 'ACTIVE': return '🟢'
    case 'COMPLETED': return '✅'
    case 'FAILED': return '❌'
    case 'ARCHIVED': return '📦'
    default: return ''
  }
})

function handleDelete(e: Event) {
  e.stopPropagation()
  if (confirm('Are you sure you want to delete this session?')) {
    emit('delete')
  }
  showMenu.value = false
}
</script>

<template>
  <div
    class="group relative px-4 py-3 cursor-pointer hover:bg-bg-tertiary transition-colors"
    :class="{ 'bg-accent-primary/10': active }"
    @click="emit('select')"
  >
    <div class="flex items-start gap-3">
      <!-- Status Icon -->
      <span class="text-sm">{{ statusIcon }}</span>

      <!-- Content -->
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2">
          <h3 
            class="text-sm font-medium truncate"
            :class="active ? 'text-accent-primary' : 'text-text-primary'"
          >
            {{ session.title }}
          </h3>
        </div>
        
        <div class="flex items-center gap-2 mt-1 text-xs text-text-tertiary">
          <span>{{ session.message_count }} messages</span>
          <span>·</span>
          <span>{{ formattedDate }}</span>
        </div>

        <div
          v-if="session.skill_id"
          class="mt-1"
        >
          <span class="inline-block px-2 py-0.5 bg-accent-primary/20 text-accent-primary rounded text-xs">
            {{ session.skill_id }}
          </span>
        </div>
      </div>

      <!-- Menu Button -->
      <button
        class="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-bg-elevated transition-opacity"
        @click.stop="showMenu = !showMenu"
      >
        <svg
          class="w-4 h-4 text-text-tertiary"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <circle
            cx="12"
            cy="6"
            r="2"
          />
          <circle
            cx="12"
            cy="12"
            r="2"
          />
          <circle
            cx="12"
            cy="18"
            r="2"
          />
        </svg>
      </button>

      <!-- Dropdown Menu -->
      <div
        v-if="showMenu"
        class="absolute right-4 top-12 z-10 bg-bg-elevated rounded-lg shadow-lg border border-border-default py-1 min-w-[120px]"
        @click.stop
      >
        <button
          class="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/10"
          @click="handleDelete"
        >
          Delete
        </button>
      </div>
    </div>
  </div>

  <!-- Backdrop to close menu -->
  <div
    v-if="showMenu"
    class="fixed inset-0 z-0"
    @click="showMenu = false"
  />
</template>
