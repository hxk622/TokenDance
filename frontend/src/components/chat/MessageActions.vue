<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Copy, ThumbsUp, ThumbsDown, Share2, RefreshCw, Check } from 'lucide-vue-next'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  messageId: string
  content: string
  feedback?: 'like' | 'dislike' | null
  isLastMessage?: boolean
  isStreaming?: boolean
}>()

const emit = defineEmits<{
  (e: 'feedback', feedback: 'like' | 'dislike' | null, onError?: () => void): void
  (e: 'regenerate'): void
}>()

const { showToast } = useToast()
const copied = ref(false)
const localFeedback = ref<'like' | 'dislike' | null>(props.feedback ?? null)

// Sync localFeedback when props.feedback changes (e.g., from server refresh)
watch(() => props.feedback, (newVal) => {
  localFeedback.value = newVal ?? null
})

const currentFeedback = computed(() => localFeedback.value)

// Copy to clipboard
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(props.content)
    copied.value = true
    showToast('已复制到剪贴板', 'success')
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch {
    showToast('复制失败', 'error')
  }
}

// Handle feedback (optimistic update with rollback on failure)
function handleFeedback(type: 'like' | 'dislike') {
  // Toggle: if clicking same feedback, clear it
  const newFeedback = localFeedback.value === type ? null : type
  const oldFeedback = localFeedback.value
  
  // Optimistic update - UI responds immediately
  localFeedback.value = newFeedback
  
  // Emit with rollback callback for error handling
  emit('feedback', newFeedback, () => {
    // Rollback on failure
    localFeedback.value = oldFeedback
  })
}

// Handle share (copy content for now)
async function handleShare() {
  try {
    await navigator.clipboard.writeText(props.content)
    showToast('内容已复制，可粘贴分享', 'success')
  } catch {
    showToast('复制失败', 'error')
  }
}

// Handle regenerate
function handleRegenerate() {
  emit('regenerate')
}
</script>

<template>
  <div class="flex items-center gap-1 mt-2">
    <!-- Copy -->
    <button
      class="action-btn"
      :class="{ 'text-accent-primary': copied }"
      title="复制"
      @click="handleCopy"
    >
      <Check
        v-if="copied"
        class="w-3.5 h-3.5"
      />
      <Copy
        v-else
        class="w-3.5 h-3.5"
      />
    </button>

    <!-- Like -->
    <button
      class="action-btn"
      :class="{ 'text-accent-primary bg-accent-primary/10': currentFeedback === 'like' }"
      title="有帮助"
      @click="handleFeedback('like')"
    >
      <ThumbsUp class="w-3.5 h-3.5" />
    </button>

    <!-- Dislike -->
    <button
      class="action-btn"
      :class="{ 'text-red-400 bg-red-400/10': currentFeedback === 'dislike' }"
      title="无帮助"
      @click="handleFeedback('dislike')"
    >
      <ThumbsDown class="w-3.5 h-3.5" />
    </button>

    <!-- Share -->
    <button
      class="action-btn"
      title="分享"
      @click="handleShare"
    >
      <Share2 class="w-3.5 h-3.5" />
    </button>

    <!-- Regenerate (only for last message and not streaming) -->
    <button
      v-if="isLastMessage && !isStreaming"
      class="action-btn"
      title="重新生成"
      @click="handleRegenerate"
    >
      <RefreshCw class="w-3.5 h-3.5" />
    </button>
  </div>
</template>

<style scoped>
.action-btn {
  @apply p-1.5 rounded-md text-text-tertiary 
         hover:text-text-secondary hover:bg-bg-tertiary
         transition-colors duration-150 cursor-pointer;
}
</style>
