<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

// Props
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon'
  size?: 'sm' | 'md' | 'lg'
  block?: boolean
  disabled?: boolean
  loading?: boolean
  icon?: Component
  iconRight?: Component
  type?: 'button' | 'submit' | 'reset'
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  block: false,
  disabled: false,
  loading: false,
  icon: undefined,
  iconRight: undefined,
  type: 'button'
})

// Emits
const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// Computed classes
const buttonClasses = computed(() => {
  const classes = ['any-btn']
  
  // Variant
  classes.push(`any-btn-${props.variant}`)
  
  // Size
  if (props.size !== 'md') {
    classes.push(`any-btn-${props.size}`)
  }
  
  // Block
  if (props.block) {
    classes.push('any-btn-block')
  }
  
  return classes
})

// Handle click
const handleClick = (event: MouseEvent) => {
  if (props.disabled || props.loading) return
  emit('click', event)
}
</script>

<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="type"
    @click="handleClick"
  >
    <!-- Loading spinner -->
    <span
      v-if="loading"
      class="any-btn-spinner"
    >
      <svg
        class="animate-spin"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke-opacity="0.25"
        />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke-linecap="round"
        />
      </svg>
    </span>
    
    <!-- Left icon -->
    <component
      :is="icon"
      v-else-if="icon"
      class="any-btn-icon-left"
      :size="size === 'sm' ? 14 : size === 'lg' ? 18 : 16"
    />
    
    <!-- Slot content -->
    <span
      v-if="$slots.default && variant !== 'icon'"
      class="any-btn-label"
    >
      <slot />
    </span>
    
    <!-- Icon only for icon variant -->
    <slot v-if="variant === 'icon'" />
    
    <!-- Right icon -->
    <component
      :is="iconRight"
      v-if="iconRight && !loading"
      class="any-btn-icon-right"
      :size="size === 'sm' ? 14 : size === 'lg' ? 18 : 16"
    />
  </button>
</template>

<style scoped>
.any-btn-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
}

.any-btn-spinner svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.any-btn-icon-left,
.any-btn-icon-right {
  flex-shrink: 0;
}

.any-btn-label {
  flex: 1;
}
</style>
