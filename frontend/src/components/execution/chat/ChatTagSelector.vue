<script setup lang="ts">
import { computed } from 'vue'
import type { FormFieldOption } from './types'

interface Props {
  options: FormFieldOption[]
  modelValue?: string[]
  disabled?: boolean
  readonly?: boolean
  label?: string
  description?: string
  multiple?: boolean  // Allow multiple selection
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  disabled: false,
  readonly: false,
  label: '',
  description: '',
  multiple: true
})

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const selectedValues = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function isSelected(value: string): boolean {
  return selectedValues.value.includes(value)
}

function toggleTag(value: string) {
  if (props.disabled || props.readonly) return
  
  if (props.multiple) {
    // Multiple selection mode
    const newValues = [...selectedValues.value]
    const index = newValues.indexOf(value)
    
    if (index >= 0) {
      newValues.splice(index, 1)
    } else {
      newValues.push(value)
    }
    
    selectedValues.value = newValues
  } else {
    // Single selection mode
    if (isSelected(value)) {
      selectedValues.value = []
    } else {
      selectedValues.value = [value]
    }
  }
}
</script>

<template>
  <div :class="['chat-tag-selector', { disabled, readonly }]">
    <div
      v-if="label"
      class="field-label"
    >
      {{ label }}
    </div>
    <div
      v-if="description"
      class="field-description"
    >
      {{ description }}
    </div>
    
    <div class="tags-container">
      <button
        v-for="option in options"
        :key="option.value"
        :class="['tag-item', { selected: isSelected(option.value) }]"
        :disabled="disabled"
        :title="option.description"
        @click="toggleTag(option.value)"
      >
        {{ option.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-tag-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-tag-selector.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.chat-tag-selector.readonly {
  pointer-events: none;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.field-description {
  font-size: 12px;
  color: var(--any-text-secondary);
  margin-top: -4px;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  padding: 6px 14px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 20px;
  font-size: 13px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.tag-item:hover:not(:disabled) {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

.tag-item.selected {
  background: rgba(0, 217, 255, 0.12);
  border-color: var(--td-state-thinking, #00D9FF);
  color: var(--td-state-thinking, #00D9FF);
}

.tag-item.selected:hover:not(:disabled) {
  background: rgba(0, 217, 255, 0.18);
}
</style>
