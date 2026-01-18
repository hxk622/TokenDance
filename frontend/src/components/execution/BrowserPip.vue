<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  ArrowsPointingOutIcon,
  XMarkIcon,
  ArrowTopRightOnSquareIcon,
  ArrowsPointingInIcon,
} from '@heroicons/vue/24/outline'

interface Props {
  visible: boolean
  url?: string
  title?: string
  screenshot?: string  // Base64 encoded screenshot
}

interface Emits {
  (e: 'close'): void
  (e: 'expand'): void
  (e: 'open-url', url: string): void
}

const props = withDefaults(defineProps<Props>(), {
  url: '',
  title: '浏览器预览',
  screenshot: ''
})
const emit = defineEmits<Emits>()

const isMinimized = ref(false)
const isDragging = ref(false)
const position = ref({ x: 20, y: 20 })
const dragStart = ref({ x: 0, y: 0 })

const pipStyle = computed(() => ({
  right: `${position.value.x}px`,
  bottom: `${position.value.y}px`,
  width: isMinimized.value ? '200px' : '360px',
  height: isMinimized.value ? '40px' : '280px',
}))

const displayUrl = computed(() => {
  if (!props.url) return '无活动页面'
  try {
    const url = new URL(props.url)
    return url.hostname + url.pathname.slice(0, 30) + (url.pathname.length > 30 ? '...' : '')
  } catch {
    return props.url.slice(0, 40)
  }
})

function handleDragStart(e: MouseEvent) {
  isDragging.value = true
  dragStart.value = {
    x: e.clientX + position.value.x,
    y: e.clientY + position.value.y
  }
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', handleDragEnd)
}

function handleDragMove(e: MouseEvent) {
  if (!isDragging.value) return
  position.value = {
    x: dragStart.value.x - e.clientX,
    y: dragStart.value.y - e.clientY
  }
  // 边界限制
  position.value.x = Math.max(0, Math.min(window.innerWidth - 380, position.value.x))
  position.value.y = Math.max(0, Math.min(window.innerHeight - 300, position.value.y))
}

function handleDragEnd() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
}

function toggleMinimize() {
  isMinimized.value = !isMinimized.value
}

onUnmounted(() => {
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', handleDragEnd)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="pip-slide">
      <div 
        v-if="visible"
        class="browser-pip"
        :class="{ 'is-minimized': isMinimized, 'is-dragging': isDragging }"
        :style="pipStyle"
      >
        <!-- Header -->
        <div
          class="pip-header"
          @mousedown="handleDragStart"
        >
          <div class="pip-title">
            <div class="browser-dot green" />
            <span class="pip-label">{{ title }}</span>
          </div>
          <div class="pip-actions">
            <button 
              class="pip-btn" 
              :title="isMinimized ? '展开' : '最小化'"
              @click.stop="toggleMinimize"
            >
              <ArrowsPointingInIcon
                v-if="!isMinimized"
                class="w-3.5 h-3.5"
              />
              <ArrowsPointingOutIcon
                v-else
                class="w-3.5 h-3.5"
              />
            </button>
            <button 
              v-if="url"
              class="pip-btn" 
              title="在新窗口打开"
              @click.stop="emit('open-url', url)"
            >
              <ArrowTopRightOnSquareIcon class="w-3.5 h-3.5" />
            </button>
            <button
              class="pip-btn pip-btn-close"
              title="关闭"
              @click.stop="emit('close')"
            >
              <XMarkIcon class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <!-- Content -->
        <div
          v-if="!isMinimized"
          class="pip-content"
        >
          <!-- URL Bar -->
          <div class="pip-url-bar">
            <div class="url-text">
              {{ displayUrl }}
            </div>
          </div>
          
          <!-- Preview Area -->
          <div class="pip-preview">
            <img 
              v-if="screenshot" 
              :src="screenshot" 
              alt="Browser Preview"
              class="preview-image"
            >
            <div
              v-else
              class="preview-placeholder"
            >
              <div class="placeholder-icon">
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
                    d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418"
                  />
                </svg>
              </div>
              <span class="placeholder-text">等待浏览器截图...</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* BrowserPip - 使用全局主题变量 */
.browser-pip {
  position: fixed;
  z-index: 9000;
  background: var(--any-bg-secondary);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--any-border-hover);
  border-radius: var(--any-radius-xl);
  box-shadow: var(--any-shadow-xl);
  overflow: hidden;
  transition: width var(--any-duration-normal) var(--any-ease-out), height var(--any-duration-normal) var(--any-ease-out);
}

.browser-pip.is-dragging {
  transition: none;
  user-select: none;
}

.pip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 40px;
  padding: 0 12px;
  background: var(--any-bg-tertiary);
  cursor: grab;
}

.pip-header:active {
  cursor: grabbing;
}

.pip-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.browser-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.browser-dot.green {
  background: var(--td-state-executing);
  box-shadow: 0 0 6px var(--td-state-executing-bg);
}

.pip-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.pip-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pip-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--any-radius-md);
  border: none;
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.pip-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.pip-btn-close:hover {
  background: var(--td-state-error-bg);
  color: var(--td-state-error);
}

.pip-content {
  display: flex;
  flex-direction: column;
  height: calc(100% - 40px);
}

.pip-url-bar {
  display: flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border-light);
}

.url-text {
  font-size: 11px;
  color: var(--any-text-tertiary);
  font-family: 'SF Mono', Monaco, monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pip-preview {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--any-bg-tertiary);
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.preview-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.placeholder-icon {
  color: var(--any-text-muted);
}

.placeholder-text {
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Transition */
.pip-slide-enter-active,
.pip-slide-leave-active {
  transition: all 200ms ease;
}

.pip-slide-enter-from,
.pip-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* Minimized state */
.is-minimized .pip-label {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
