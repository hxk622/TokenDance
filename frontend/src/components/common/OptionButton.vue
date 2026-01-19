<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

// Props
interface Props {
  label: string
  value: string | number
  selected?: boolean
  disabled?: boolean
  icon?: Component
}

const props = withDefaults(defineProps<Props>(), {
  selected: false,
  disabled: false
})

// Emits
const emit = defineEmits<{
  select: [value: string | number]
}>()

// Computed classes
const buttonClasses = computed(() => {
  const classes = ['option-button']
  
  if (props.selected) {
    classes.push('selected')
  }
  
  if (props.disabled) {
    classes.push('disabled')
  }
  
  return classes
})

// Handle click
const handleClick = () => {
  if (props.disabled) return
  emit('select', props.value)
}
</script>

<template>
  <button
    :class="buttonClasses"
    :disabled="disabled"
    @click="handleClick"
  >
    <component
      :is="icon"
      v-if="icon"
      class="option-icon"
      :size="16"
    />
    <span class="option-label">{{ label }}</span>
  </button>
</template>

<style scoped>
.option-button {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
  white-space: nowrap;
  
  /* Unselected state */
  border: 1.5px solid var(--any-border);
  background: transparent;
  color: var(--any-text-tertiary);
}

.option-button:hover:not(.disabled):not(.selected) {
  border-color: var(--any-border-hover);
  transform: translateY(-1px);
}

.option-button.selected {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  border: none;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.option-button.selected:hover:not(.disabled) {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
}

.option-button.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

.option-icon {
  flex-shrink: 0;
}

.option-label {
  flex: 1;
}
</style>
