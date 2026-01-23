<script setup lang="ts">
import { computed } from 'vue'
import OptionButton from './OptionButton.vue'
import { Check } from 'lucide-vue-next'
import type { Component } from 'vue'

// Types
export interface Option {
  label: string
  value: string | number
  icon?: Component
  disabled?: boolean
}

// Props
interface Props {
  options: Option[]
  mode?: 'single' | 'multiple'
  modelValue: string | number | (string | number)[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'single',
  disabled: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string | number | (string | number)[]]
}>()

// Check if an option is selected
const isSelected = (value: string | number): boolean => {
  if (props.mode === 'multiple') {
    return Array.isArray(props.modelValue) && props.modelValue.includes(value)
  }
  return props.modelValue === value
}

// Handle option selection
const handleSelect = (value: string | number) => {
  if (props.disabled) return

  if (props.mode === 'multiple') {
    const currentValues = Array.isArray(props.modelValue) ? props.modelValue : []
    
    if (currentValues.includes(value)) {
      // Remove from selection
      emit('update:modelValue', currentValues.filter(v => v !== value))
    } else {
      // Add to selection
      emit('update:modelValue', [...currentValues, value])
    }
  } else {
    // Single selection
    emit('update:modelValue', value)
  }
}
</script>

<template>
  <div class="option-group">
    <div
      v-for="option in options"
      :key="option.value"
      class="option-wrapper"
    >
      <OptionButton
        :label="option.label"
        :value="option.value"
        :selected="isSelected(option.value)"
        :disabled="disabled || option.disabled"
        :icon="option.icon"
        @select="handleSelect"
      />
      <div
        v-if="mode === 'multiple' && isSelected(option.value)"
        class="checkmark"
      >
        <Check :size="14" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.option-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  max-width: 100%;
}

/* Limit to 3 columns for readability */
@media (min-width: 768px) {
  .option-group {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
}

@media (min-width: 1024px) {
  .option-group {
    grid-template-columns: repeat(3, 1fr);
  }
}

.option-wrapper {
  position: relative;
}

.checkmark {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: white;
  color: #00B8D9;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  pointer-events: none;
  animation: checkmark-appear 200ms ease;
}

@keyframes checkmark-appear {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
