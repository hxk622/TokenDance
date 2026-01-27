<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { X } from 'lucide-vue-next'

// Props
interface Props {
  modelValue?: boolean
  title?: string
  image?: string
  imageAlt?: string
  showClose?: boolean
  closeOnOverlay?: boolean
  closeOnEsc?: boolean
  width?: string
  persistent?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: false,
  title: '',
  image: '',
  imageAlt: '',
  showClose: true,
  closeOnOverlay: true,
  closeOnEsc: true,
  width: '480px',
  persistent: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  close: []
  open: []
}>()

// Refs
const isVisible = ref(false)
const isAnimating = ref(false)

// Methods
const open = () => {
  isVisible.value = true
  isAnimating.value = true
  document.body.style.overflow = 'hidden'
  emit('open')
  
  // Allow animation to complete
  setTimeout(() => {
    isAnimating.value = false
  }, 250)
}

const close = () => {
  if (props.persistent) return
  
  isAnimating.value = true
  
  setTimeout(() => {
    isVisible.value = false
    isAnimating.value = false
    document.body.style.overflow = ''
    emit('update:modelValue', false)
    emit('close')
  }, 200)
}
// Watch modelValue
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    open()
  } else {
    close()
  }
}, { immediate: true })

const handleOverlayClick = () => {
  if (props.closeOnOverlay && !props.persistent) {
    close()
  }
}

const handleEsc = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.closeOnEsc && !props.persistent && isVisible.value) {
    close()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleEsc)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEsc)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="any-modal">
      <div
        v-if="isVisible"
        class="any-modal-overlay"
        :class="{ visible: modelValue && !isAnimating }"
        @click.self="handleOverlayClick"
      >
        <div
          class="any-modal"
          :style="{ maxWidth: width }"
          role="dialog"
          aria-modal="true"
        >
          <!-- Image header -->
          <img
            v-if="image"
            :src="image"
            :alt="imageAlt || title"
            class="any-modal-image"
          >
          
          <!-- Close button -->
          <button
            v-if="showClose"
            class="any-modal-close"
            type="button"
            aria-label="Close"
            @click="close"
          >
            <X :size="16" />
          </button>
          
          <!-- Header -->
          <div
            v-if="title || $slots.header"
            class="any-modal-header"
          >
            <slot name="header">
              <h2 class="any-modal-title">
                {{ title }}
              </h2>
            </slot>
          </div>
          
          <!-- Body -->
          <div class="any-modal-body">
            <slot />
          </div>
          
          <!-- Footer -->
          <div
            v-if="$slots.footer"
            class="any-modal-footer"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.any-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--any-z-modal, 300);
  padding: var(--any-space-6, 16px);
}

.any-modal {
  position: relative;
  width: 100%;
  max-height: calc(100vh - 32px);
  background: var(--any-bg-primary, #fff);
  border-radius: var(--any-radius-xl, 16px);
  overflow: hidden;
  box-shadow: var(--any-shadow-xl, 0 16px 48px rgba(0, 0, 0, 0.16));
  display: flex;
  flex-direction: column;
}

.any-modal-image {
  width: 100%;
  aspect-ratio: 480 / 276;
  object-fit: cover;
  background: var(--any-bg-tertiary, #f5f5f5);
  flex-shrink: 0;
}

.any-modal-close {
  position: absolute;
  top: var(--any-space-5, 12px);
  right: var(--any-space-5, 12px);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md, 8px);
  background: transparent;
  border: none;
  color: var(--any-text-tertiary, #888);
  cursor: pointer;
  transition: all var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
  z-index: 1;
}

.any-modal-close:hover {
  background: var(--any-bg-hover, rgba(0, 0, 0, 0.04));
  color: var(--any-text-primary, #1a1a1a);
}

/* When modal has image, close button should be white */
.any-modal:has(.any-modal-image) .any-modal-close {
  color: var(--any-text-inverse, #fff);
}

.any-modal:has(.any-modal-image) .any-modal-close:hover {
  background: rgba(0, 0, 0, 0.2);
  color: var(--any-text-inverse, #fff);
}

.any-modal-header {
  padding: var(--any-space-7, 20px);
  padding-bottom: 0;
  flex-shrink: 0;
}

.any-modal-title {
  font-size: var(--any-text-2xl, 22px);
  font-weight: var(--any-font-medium, 500);
  line-height: 30px;
  color: var(--any-text-primary, #1a1a1a);
  margin: 0;
}

.any-modal-body {
  padding: var(--any-space-5, 12px) var(--any-space-7, 20px);
  font-size: var(--any-text-md, 16px);
  font-weight: var(--any-font-normal, 400);
  line-height: 28px;
  letter-spacing: -0.48px;
  color: var(--any-text-secondary, #5D5D5D);
  overflow-y: auto;
  flex: 1;
}

.any-modal-footer {
  padding: var(--any-space-4, 10px) var(--any-space-7, 20px) var(--any-space-7, 20px);
  display: flex;
  justify-content: flex-end;
  gap: var(--any-space-3, 8px);
  flex-shrink: 0;
}

/* Transitions */
.any-modal-enter-active {
  transition: opacity var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out);
}

.any-modal-enter-active .any-modal {
  transition: transform var(--any-duration-slow, 250ms) var(--any-ease-bounce, cubic-bezier(0.34, 1.56, 0.64, 1)),
              opacity var(--any-duration-slow, 250ms) var(--any-ease-bounce, cubic-bezier(0.34, 1.56, 0.64, 1));
}

.any-modal-leave-active {
  transition: opacity var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
}

.any-modal-leave-active .any-modal {
  transition: transform var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out),
              opacity var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
}

.any-modal-enter-from,
.any-modal-leave-to {
  opacity: 0;
}

.any-modal-enter-from .any-modal,
.any-modal-leave-to .any-modal {
  opacity: 0;
  transform: scale(0.95);
}
</style>
