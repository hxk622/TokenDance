<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

// Props
interface Props {
  variant?: 'default' | 'preview'
  active?: boolean
  disabled?: boolean
  icon?: Component
  label?: string
  // Preview variant props
  image?: string
  title?: string
  meta?: string
  tag?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  active: false,
  disabled: false,
  icon: undefined,
  label: '',
  image: '',
  title: '',
  meta: '',
  tag: ''
})

// Emits
const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// Computed classes
const cardClasses = computed(() => {
  const classes = ['any-card']
  
  if (props.variant === 'preview') {
    classes.push('any-card-preview')
  }
  
  if (props.active) {
    classes.push('active')
  }
  
  if (props.disabled) {
    classes.push('disabled')
  }
  
  return classes
})

// Handle click
const handleClick = (event: MouseEvent) => {
  if (props.disabled) return
  emit('click', event)
}
</script>

<template>
  <button
    :class="cardClasses"
    :aria-pressed="active"
    :disabled="disabled"
    type="button"
    @click="handleClick"
  >
    <!-- Default variant: icon + label -->
    <template v-if="variant === 'default'">
      <span
        v-if="icon"
        class="any-card-icon"
      >
        <component
          :is="icon"
          :size="16"
        />
      </span>
      <span
        v-if="$slots.icon"
        class="any-card-icon"
      >
        <slot name="icon" />
      </span>
      <span class="any-card-label">
        <slot>{{ label }}</slot>
      </span>
    </template>
    
    <!-- Preview variant: image + content -->
    <template v-else-if="variant === 'preview'">
      <div
        v-if="image"
        class="any-card-preview-image-wrapper"
      >
        <img
          :src="image"
          :alt="title"
          class="any-card-preview-image"
        >
        <span
          v-if="tag"
          class="any-card-preview-tag"
        >{{ tag }}</span>
      </div>
      <div
        v-else
        class="any-card-preview-placeholder"
      >
        <slot name="placeholder">
          <component
            :is="icon"
            v-if="icon"
            :size="32"
          />
        </slot>
      </div>
      <div class="any-card-preview-content">
        <div class="any-card-preview-title">
          <slot name="title">
            {{ title }}
          </slot>
        </div>
        <div
          v-if="meta || $slots.meta"
          class="any-card-preview-meta"
        >
          <slot name="meta">
            {{ meta }}
          </slot>
        </div>
      </div>
    </template>
  </button>
</template>

<style scoped>
.any-card {
  display: flex;
  align-items: center;
  gap: var(--any-space-3, 8px);
  padding: var(--any-space-3, 8px) var(--any-space-5, 12px);
  border-radius: var(--any-radius-md, 8px);
  border: 1px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: all var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out);
  text-align: left;
  width: 100%;
}

.any-card:hover:not(:disabled) {
  background: var(--any-bg-hover, rgba(0, 0, 0, 0.04));
  border-color: var(--any-border, #E4E4E4);
}

.any-card.active,
.any-card[aria-pressed="true"] {
  background: var(--any-bg-tertiary, #f5f5f5);
  border-color: var(--any-border-active, #1a1a1a);
}

.any-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.any-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: var(--any-text-secondary, #5D5D5D);
  flex-shrink: 0;
}

.any-card-label {
  font-size: var(--any-text-base, 14px);
  font-weight: var(--any-font-normal, 400);
  color: var(--any-text-primary, #1a1a1a);
}

/* Preview variant */
.any-card-preview {
  flex-direction: column;
  align-items: stretch;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--any-border, #E4E4E4);
}

.any-card-preview:hover:not(:disabled) {
  border-color: var(--any-border-hover, #999);
  box-shadow: var(--any-shadow-md, 0 4px 12px rgba(0, 0, 0, 0.08));
  transform: translateY(-2px);
}

.any-card-preview-image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.any-card-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: var(--any-bg-tertiary, #f5f5f5);
}

.any-card-preview-tag {
  position: absolute;
  top: var(--any-space-3, 8px);
  left: var(--any-space-3, 8px);
  padding: var(--any-space-1, 4px) var(--any-space-3, 8px);
  background: var(--any-bg-glass, rgba(26, 26, 26, 0.5));
  backdrop-filter: blur(8px);
  border-radius: var(--any-radius-sm, 4px);
  font-size: var(--any-text-xs, 12px);
  color: var(--any-text-inverse, #fff);
}

.any-card-preview-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary, #f5f5f5);
  color: var(--any-text-tertiary, #888);
}

.any-card-preview-content {
  padding: var(--any-space-5, 12px);
}

.any-card-preview-title {
  font-size: var(--any-text-base, 14px);
  font-weight: var(--any-font-medium, 500);
  color: var(--any-text-primary, #1a1a1a);
  margin-bottom: var(--any-space-1, 4px);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.any-card-preview-meta {
  font-size: var(--any-text-xs, 12px);
  color: var(--any-text-tertiary, #888);
}
</style>
