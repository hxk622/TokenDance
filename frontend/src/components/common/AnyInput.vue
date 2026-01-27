<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Component } from 'vue'

// Props
interface Props {
  modelValue?: string | number
  type?: 'text' | 'password' | 'email' | 'number' | 'search' | 'tel' | 'url'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  icon?: Component
  iconRight?: Component
  size?: 'sm' | 'md' | 'lg'
  error?: boolean
  errorMessage?: string
  maxlength?: number
  autofocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  type: 'text',
  placeholder: '',
  disabled: false,
  readonly: false,
  icon: undefined,
  iconRight: undefined,
  size: 'md',
  error: false,
  errorMessage: '',
  maxlength: undefined,
  autofocus: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
  enter: [event: KeyboardEvent]
}>()

// Refs
const inputRef = ref<HTMLInputElement | null>(null)
const isFocused = ref(false)

// Computed classes
const wrapperClasses = computed(() => {
  const classes = ['any-input-wrapper']
  
  if (props.icon) {
    classes.push('has-icon-left')
  }
  if (props.iconRight) {
    classes.push('has-icon-right')
  }
  if (isFocused.value) {
    classes.push('focused')
  }
  if (props.error) {
    classes.push('error')
  }
  if (props.disabled) {
    classes.push('disabled')
  }
  
  return classes
})

const inputClasses = computed(() => {
  const classes = ['any-input']
  
  if (props.size !== 'md') {
    classes.push(`any-input-${props.size}`)
  }
  
  return classes
})

// Methods
const focus = () => {
  inputRef.value?.focus()
}

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

const handleFocus = (event: FocusEvent) => {
  isFocused.value = true
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  isFocused.value = false
  emit('blur', event)
}

const handleKeydown = (event: KeyboardEvent) => {
  emit('keydown', event)
  if (event.key === 'Enter') {
    emit('enter', event)
  }
}

// Expose
defineExpose({ focus, inputRef })
</script>

<template>
  <div class="any-input-container">
    <div :class="wrapperClasses">
      <!-- Left icon -->
      <span
        v-if="icon"
        class="any-input-icon any-input-icon-left"
      >
        <component
          :is="icon"
          :size="16"
        />
      </span>
      
      <!-- Input -->
      <input
        ref="inputRef"
        :class="inputClasses"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :maxlength="maxlength"
        :autofocus="autofocus"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="handleKeydown"
      >
      
      <!-- Right icon -->
      <span
        v-if="iconRight"
        class="any-input-icon any-input-icon-right"
      >
        <component
          :is="iconRight"
          :size="16"
        />
      </span>
    </div>
    
    <!-- Error message -->
    <div
      v-if="error && errorMessage"
      class="any-input-error"
    >
      {{ errorMessage }}
    </div>
  </div>
</template>

<style scoped>
.any-input-container {
  width: 100%;
}

.any-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.any-input {
  width: 100%;
  height: 40px;
  padding: 0 var(--any-space-5, 12px);
  font-size: var(--any-text-base, 14px);
  color: var(--any-text-primary, #1a1a1a);
  background: var(--any-bg-primary, #fff);
  border: 1px solid var(--any-border, #E4E4E4);
  border-radius: var(--any-radius-md, 8px);
  outline: none;
  transition: border-color var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out),
              box-shadow var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out);
}

.any-input::placeholder {
  color: var(--any-text-quaternary, #ADADAD);
}

.any-input:hover:not(:disabled):not(:focus) {
  border-color: var(--any-border-hover, #999);
}

.any-input:focus {
  border-color: var(--any-border-active, #1a1a1a);
  box-shadow: 0 0 0 3px rgba(26, 26, 26, 0.08);
}

.any-input:disabled {
  background: var(--any-bg-tertiary, #f5f5f5);
  color: var(--any-text-tertiary, #888);
  cursor: not-allowed;
}

/* Size variants */
.any-input-sm {
  height: 32px;
  padding: 0 var(--any-space-4, 10px);
  font-size: var(--any-text-sm, 13px);
}

.any-input-lg {
  height: 48px;
  padding: 0 var(--any-space-6, 16px);
  font-size: var(--any-text-md, 16px);
}

/* With icons */
.any-input-icon {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--any-text-tertiary, #888);
  pointer-events: none;
  z-index: 1;
}

.any-input-icon-left {
  left: var(--any-space-5, 12px);
}

.any-input-icon-right {
  right: var(--any-space-5, 12px);
}

.has-icon-left .any-input {
  padding-left: 40px;
}

.has-icon-right .any-input {
  padding-right: 40px;
}

/* Error state */
.error .any-input {
  border-color: var(--any-error, #FF3B30);
}

.error .any-input:focus {
  border-color: var(--any-error, #FF3B30);
  box-shadow: 0 0 0 3px rgba(255, 59, 48, 0.1);
}

.any-input-error {
  margin-top: var(--any-space-2, 6px);
  font-size: var(--any-text-xs, 12px);
  color: var(--any-error, #FF3B30);
}
</style>
