<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

// Types
interface SelectOption {
  value: string | number
  label: string
  disabled?: boolean
}

// Props
interface Props {
  modelValue?: string | number
  options: SelectOption[]
  placeholder?: string
  disabled?: boolean
  variant?: 'default' | 'pill'
  icon?: Component
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: '请选择',
  disabled: false,
  variant: 'default',
  size: 'md',
  icon: undefined
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  change: [value: string | number]
}>()

// Computed classes
const wrapperClasses = computed(() => {
  const classes = ['any-select-wrapper']
  
  if (props.variant === 'pill') {
    classes.push('any-select-wrapper-pill')
  }
  if (props.icon) {
    classes.push('has-icon')
  }
  
  return classes
})

const selectClasses = computed(() => {
  const classes = ['any-select']
  
  if (props.variant === 'pill') {
    classes.push('any-select-pill')
  }
  
  if (props.size !== 'md') {
    classes.push(`any-select-${props.size}`)
  }
  
  return classes
})

// Methods
const handleChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const value = target.value
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<template>
  <div :class="wrapperClasses">
    <!-- Left icon -->
    <span
      v-if="icon"
      class="any-select-icon-left"
    >
      <component
        :is="icon"
        :size="16"
      />
    </span>
    
    <!-- Select -->
    <select
      :class="selectClasses"
      :value="modelValue"
      :disabled="disabled"
      @change="handleChange"
    >
      <option
        v-if="placeholder"
        value=""
        disabled
      >
        {{ placeholder }}
      </option>
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
        :disabled="option.disabled"
      >
        {{ option.label }}
      </option>
    </select>
    
    <!-- Right icon (chevron) -->
    <span class="any-select-icon-right">
      <ChevronDown :size="16" />
    </span>
  </div>
</template>

<style scoped>
.any-select-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
  width: 100%;
}

.any-select-wrapper-pill {
  width: auto;
}

.any-select {
  appearance: none;
  width: 100%;
  height: 40px;
  padding: 0 36px 0 var(--any-space-5, 12px);
  font-size: var(--any-text-base, 14px);
  color: var(--any-text-primary, #1a1a1a);
  background: var(--any-bg-primary, #fff);
  border: 1px solid var(--any-border, #E4E4E4);
  border-radius: var(--any-radius-md, 8px);
  cursor: pointer;
  outline: none;
  transition: all var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out);
}

.any-select:hover:not(:disabled) {
  border-color: var(--any-border-hover, #999);
}

.any-select:focus {
  border-color: var(--any-border-active, #1a1a1a);
  box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.08);
}

.any-select:disabled {
  background: var(--any-bg-tertiary, #f5f5f5);
  color: var(--any-text-tertiary, #888);
  cursor: not-allowed;
}

/* Pill variant */
.any-select-pill {
  height: 36px;
  padding: 0 32px 0 var(--any-space-5, 12px);
  border-radius: var(--any-radius-full, 9999px);
  font-size: var(--any-text-sm, 13px);
}

.has-icon .any-select {
  padding-left: 36px;
}

.has-icon .any-select-pill {
  padding-left: 36px;
}

/* Size variants */
.any-select-sm {
  height: 32px;
  font-size: var(--any-text-sm, 13px);
}

.any-select-lg {
  height: 48px;
  font-size: var(--any-text-md, 16px);
}

/* Icons */
.any-select-icon-left,
.any-select-icon-right {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--any-text-tertiary, #888);
  pointer-events: none;
  transition: color var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
}

.any-select-icon-left {
  left: var(--any-space-4, 10px);
}

.any-select-icon-right {
  right: var(--any-space-4, 10px);
}

.any-select-wrapper:hover .any-select-icon-left,
.any-select-wrapper:hover .any-select-icon-right {
  color: var(--any-text-primary, #1a1a1a);
}
</style>
