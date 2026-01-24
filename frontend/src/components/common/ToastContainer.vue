<script setup lang="ts">
import { useToast, type Toast } from '@/composables/useToast'
import { CheckCircle, XCircle, Info, AlertTriangle, X } from 'lucide-vue-next'

const { toasts, removeToast } = useToast()

function getIcon(type: Toast['type']) {
  switch (type) {
    case 'success': return CheckCircle
    case 'error': return XCircle
    case 'warning': return AlertTriangle
    default: return Info
  }
}

function getColorClass(type: Toast['type']) {
  switch (type) {
    case 'success': return 'bg-green-500/10 border-green-500/30 text-green-400'
    case 'error': return 'bg-red-500/10 border-red-500/30 text-red-400'
    case 'warning': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
    default: return 'bg-accent-primary/10 border-accent-primary/30 text-accent-primary'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-sm shadow-lg min-w-[200px] max-w-[400px]"
          :class="getColorClass(toast.type)"
        >
          <component
            :is="getIcon(toast.type)"
            class="w-5 h-5 flex-shrink-0"
          />
          <span class="flex-1 text-sm">{{ toast.message }}</span>
          <button
            class="p-0.5 hover:bg-white/10 rounded transition-colors cursor-pointer"
            @click="removeToast(toast.id)"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>
