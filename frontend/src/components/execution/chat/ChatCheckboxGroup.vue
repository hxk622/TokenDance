<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import type { FormFieldOption } from './types'

interface Props {
  options: FormFieldOption[]
  modelValue?: string[]
  disabled?: boolean
  readonly?: boolean
  label?: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => [],
  disabled: false,
  readonly: false,
  label: '',
  description: ''
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

function toggleOption(value: string) {
  if (props.disabled || props.readonly) return
  
  const newValues = [...selectedValues.value]
  const index = newValues.indexOf(value)
  
  if (index >= 0) {
    newValues.splice(index, 1)
  } else {
    newValues.push(value)
  }
  
  selectedValues.value = newValues
}
</script>

<template>
  <div :class="['chat-checkbox-group', { disabled, readonly }]">
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
    
    <div class="options-list">
      <button
        v-for="option in options"
        :key="option.value"
        :class="['checkbox-option', { selected: isSelected(option.value) }]"
        :disabled="disabled"
        @click="toggleOption(option.value)"
      >
        <span class="checkbox-indicator">
          <Check
            v-if="isSelected(option.value)"
            class="check-icon"
          />
        </span>
        <div class="option-content">
          <span class="option-label">{{ option.label }}</span>
          <span
            v-if="option.description"
            class="option-desc"
          >{{ option.description }}</span>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-checkbox-group.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.chat-checkbox-group.readonly {
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

.options-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.checkbox-option {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 150ms ease;
}

.checkbox-option:hover:not(:disabled) {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.checkbox-option.selected {
  background: rgba(0, 217, 255, 0.08);
  border-color: var(--td-state-thinking, #00D9FF);
}

.checkbox-indicator {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 2px solid var(--any-border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 150ms ease;
  margin-top: 1px;
}

.checkbox-option.selected .checkbox-indicator {
  background: var(--td-state-thinking, #00D9FF);
  border-color: var(--td-state-thinking, #00D9FF);
}

.check-icon {
  width: 12px;
  height: 12px;
  color: var(--any-bg-primary);
}

.option-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-size: 14px;
  color: var(--any-text-primary);
  line-height: 1.4;
}

.option-desc {
  font-size: 12px;
  color: var(--any-text-secondary);
  line-height: 1.4;
}
</style>
