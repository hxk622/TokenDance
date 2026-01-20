<script setup lang="ts">
import { ref, watch } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

interface Props {
  title: string
  description?: string
  defaultOpen?: boolean
  icon?: string
}

const props = withDefaults(defineProps<Props>(), {
  description: '',
  defaultOpen: true,
  icon: ''
})

const isOpen = ref(props.defaultOpen)

function toggle() {
  isOpen.value = !isOpen.value
}

// Watch for external changes
watch(() => props.defaultOpen, (newValue) => {
  isOpen.value = newValue
})
</script>

<template>
  <div :class="['chat-collapsible', { open: isOpen }]">
    <button
      class="collapsible-header"
      @click="toggle"
    >
      <div class="header-content">
        <span
          v-if="icon"
          class="header-icon"
        >{{ icon }}</span>
        <div class="header-text">
          <span class="header-title">{{ title }}</span>
          <span
            v-if="description"
            class="header-desc"
          >{{ description }}</span>
        </div>
      </div>
      <ChevronDown :class="['chevron', { rotated: isOpen }]" />
    </button>
    
    <Transition name="collapse">
      <div
        v-show="isOpen"
        class="collapsible-content"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.chat-collapsible {
  border: 1px solid var(--any-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--any-bg-secondary);
}

.collapsible-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 12px 14px;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 150ms ease;
}

.collapsible-header:hover {
  background: var(--any-bg-hover);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 18px;
}

.header-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.header-desc {
  font-size: 12px;
  color: var(--any-text-secondary);
}

.chevron {
  width: 18px;
  height: 18px;
  color: var(--any-text-muted);
  transition: transform 200ms ease;
  flex-shrink: 0;
}

.chevron.rotated {
  transform: rotate(180deg);
}

.collapsible-content {
  padding: 0 14px 14px;
}

/* Collapse Transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 200ms ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
