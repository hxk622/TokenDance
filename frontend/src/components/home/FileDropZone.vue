<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'drop', files: FileList): void
}>()

const isDragging = ref(false)
const dragCounter = ref(0)

const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  dragCounter.value++
  isDragging.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  dragCounter.value--
  if (dragCounter.value === 0) {
    isDragging.value = false
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  dragCounter.value = 0
  
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    emit('drop', e.dataTransfer.files)
  }
}
</script>

<template>
  <div
    class="file-drop-zone"
    :class="{ 'is-dragging': isDragging }"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <div class="drop-content">
      <div
        class="drop-icon"
        :class="{ 'drop-icon-active': isDragging }"
      >
        <svg
          class="w-8 h-8"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5" 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
      </div>
      <p class="drop-text">
        <span
          v-if="isDragging"
          class="text-cyan-600 font-medium"
        >松开鼠标上传</span>
        <span v-else>
          拖入文件或文件夹，启动 
          <span class="text-cyan-600 font-medium">Coworker</span>
        </span>
      </p>
      <p class="drop-hint">
        支持代码、文档、图片等多种格式
      </p>
    </div>
    
    <!-- Animated Border -->
    <div class="drop-border" />
  </div>
</template>

<style scoped>
.file-drop-zone {
  @apply relative w-full max-w-md mx-auto p-8
         rounded-2xl bg-white/40 backdrop-blur-sm
         border-2 border-dashed border-gray-200
         transition-all duration-300 cursor-pointer;
}

.file-drop-zone:hover {
  @apply border-cyan-300 bg-white/60;
}

.file-drop-zone.is-dragging {
  @apply border-cyan-500 bg-cyan-50/50 shadow-lg;
}

.drop-content {
  @apply flex flex-col items-center gap-3 text-center;
}

.drop-icon {
  @apply w-16 h-16 rounded-full bg-gray-100
         flex items-center justify-center text-gray-400
         transition-all duration-300;
}

.drop-icon-active {
  @apply bg-cyan-100 text-cyan-600 scale-110;
}

.file-drop-zone:hover .drop-icon {
  @apply bg-cyan-50 text-cyan-500;
}

.drop-text {
  @apply text-sm text-gray-600;
}

.drop-hint {
  @apply text-xs text-gray-400;
}

.drop-border {
  @apply absolute inset-0 rounded-2xl pointer-events-none
         opacity-0 transition-opacity duration-300;
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.3), transparent);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

.file-drop-zone.is-dragging .drop-border {
  @apply opacity-100;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
</style>
