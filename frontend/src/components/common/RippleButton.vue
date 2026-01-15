<template>
  <button
    ref="buttonRef"
    :class="['ripple-button', variant, size, { loading, disabled }]"
    :disabled="disabled || loading"
    @click="handleClick"
    @mousedown="createRipple"
  >
    <span v-if="loading" class="spinner"></span>
    <span v-else class="button-content">
      <slot />
    </span>
    <span class="ripple-container">
      <span
        v-for="ripple in ripples"
        :key="ripple.id"
        class="ripple"
        :style="{
          left: ripple.x + 'px',
          top: ripple.y + 'px',
          width: ripple.size + 'px',
          height: ripple.size + 'px',
        }"
      />
    </span>
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

interface Ripple {
  id: number
  x: number
  y: number
  size: number
}

const buttonRef = ref<HTMLButtonElement | null>(null)
const ripples = ref<Ripple[]>([])
let rippleId = 0

function createRipple(e: MouseEvent) {
  const button = buttonRef.value
  if (!button) return

  const rect = button.getBoundingClientRect()
  const size = Math.max(rect.width, rect.height) * 2
  const x = e.clientX - rect.left - size / 2
  const y = e.clientY - rect.top - size / 2

  const ripple: Ripple = {
    id: rippleId++,
    x,
    y,
    size,
  }

  ripples.value.push(ripple)

  // Remove ripple after animation
  setTimeout(() => {
    ripples.value = ripples.value.filter(r => r.id !== ripple.id)
  }, 600)
}

function handleClick(e: MouseEvent) {
  emit('click', e)
}
</script>

<style scoped>
.ripple-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 500;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  overflow: hidden;
  transition: all 150ms ease-out;
  -webkit-tap-highlight-color: transparent;
}

/* Sizes */
.ripple-button.sm {
  padding: 6px 12px;
  font-size: 13px;
}

.ripple-button.md {
  padding: 10px 18px;
  font-size: 14px;
}

.ripple-button.lg {
  padding: 14px 24px;
  font-size: 16px;
}

/* Variants */
.ripple-button.primary {
  background: linear-gradient(135deg, #00D9FF 0%, #00B4D8 100%);
  color: #000;
  box-shadow: 0 2px 8px rgba(0, 217, 255, 0.3);
}

.ripple-button.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 217, 255, 0.4);
}

.ripple-button.primary:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(0, 217, 255, 0.3);
}

.ripple-button.secondary {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.ripple-button.secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.ripple-button.ghost {
  background: transparent;
  color: #fff;
}

.ripple-button.ghost:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.ripple-button.danger {
  background: linear-gradient(135deg, #FF3B30 0%, #D32F2F 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(255, 59, 48, 0.3);
}

.ripple-button.danger:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(255, 59, 48, 0.4);
}

/* States */
.ripple-button.disabled,
.ripple-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.ripple-button.loading {
  cursor: wait;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Spinner */
.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Ripple Effect */
.ripple-container {
  position: absolute;
  inset: 0;
  overflow: hidden;
  border-radius: inherit;
  pointer-events: none;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: scale(0);
  animation: ripple-expand 0.6s ease-out forwards;
}

@keyframes ripple-expand {
  to {
    transform: scale(1);
    opacity: 0;
  }
}
</style>
