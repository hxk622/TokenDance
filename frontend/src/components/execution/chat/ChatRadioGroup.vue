<script setup lang="ts">
import { computed } from 'vue'
import type { FormFieldOption } from './types'

interface Props {
  options: FormFieldOption[]
  modelValue?: string
  disabled?: boolean
  readonly?: boolean
  label?: string
  description?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  disabled: false,
  readonly: false,
  label: '',
  description: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const selectedValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function selectOption(value: string) {
  if (props.disabled || props.readonly) return
  selectedValue.value = value
}
</script>

<template>
  <div :class="['chat-radio-group', { disabled, readonly }]">
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
        :class="['radio-option', { selected: selectedValue === option.value }]"
        :disabled="disabled"
        @click="selectOption(option.value)"
      >
        <span class="radio-indicator">
          <span
            v-if="selectedValue === option.value"
            class="radio-dot"
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
.chat-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chat-radio-group.disabled {
  opacity: 0.6;
  pointer-events: none;
}

.chat-radio-group.readonly {
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

.radio-option {
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

.radio-option:hover:not(:disabled) {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.radio-option.selected {
  background: rgba(99, 102, 241, 0.08);
  border-color: #6366f1;
}

.radio-indicator {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  border: 2px solid var(--any-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 150ms ease;
  margin-top: 1px;
}

.radio-option.selected .radio-indicator {
  border-color: #6366f1;
}

.radio-dot {
  width: 10px;
  height: 10px;
  background: #6366f1;
  border-radius: 50%;
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
