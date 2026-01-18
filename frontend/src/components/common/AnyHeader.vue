<script setup lang="ts">
import { computed } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { Sun, Moon, Monitor } from 'lucide-vue-next'

// Props
interface Props {
  title?: string
  transparent?: boolean
  bordered?: boolean
  sticky?: boolean
  showThemeToggle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  transparent: false,
  bordered: false,
  sticky: false,
  showThemeToggle: false
})

// Theme
const themeStore = useThemeStore()

const themeIcon = computed(() => {
  switch (themeStore.mode) {
    case 'light': return Sun
    case 'dark': return Moon
    default: return Monitor
  }
})

const themeTooltip = computed(() => {
  switch (themeStore.mode) {
    case 'light': return '切换到深色模式'
    case 'dark': return '切换到系统模式'
    default: return '切换到浅色模式'
  }
})

function cycleTheme() {
  const modes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system']
  const currentIndex = modes.indexOf(themeStore.mode)
  const nextIndex = (currentIndex + 1) % modes.length
  themeStore.setMode(modes[nextIndex])
}

// Computed classes
const headerClasses = computed(() => {
  const classes = ['any-header']
  
  if (props.transparent) {
    classes.push('any-header-transparent')
  }
  if (props.bordered) {
    classes.push('any-header-bordered')
  }
  if (props.sticky) {
    classes.push('any-header-sticky')
  }
  
  return classes
})
</script>

<template>
  <header :class="headerClasses">
    <!-- Left section -->
    <div class="any-header-left">
      <slot name="left" />
    </div>
    
    <!-- Center section -->
    <div class="any-header-center">
      <slot name="center">
        <h1
          v-if="title"
          class="any-header-title"
        >
          {{ title }}
        </h1>
      </slot>
    </div>
    
    <!-- Right section -->
    <div class="any-header-right">
      <slot name="right" />
      
      <!-- Theme Toggle -->
      <button
        v-if="showThemeToggle"
        class="theme-toggle"
        :title="themeTooltip"
        @click="cycleTheme"
      >
        <component :is="themeIcon" class="w-4 h-4" />
      </button>
    </div>
  </header>
</template>

<style scoped>
.any-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 var(--any-space-6, 16px);
  background: var(--any-bg-primary, #fff);
  flex-shrink: 0;
}

.any-header-transparent {
  background: transparent;
}

.any-header-bordered {
  border-bottom: 1px solid var(--any-border, #E4E4E4);
}

.any-header-sticky {
  position: sticky;
  top: 0;
  z-index: var(--any-z-sticky, 200);
}

.any-header-left,
.any-header-right {
  display: flex;
  align-items: center;
  gap: var(--any-space-3, 8px);
  flex-shrink: 0;
}

.any-header-left {
  min-width: 0;
}

.any-header-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  padding: 0 var(--any-space-6, 16px);
}

.any-header-title {
  font-size: var(--any-text-md, 16px);
  font-weight: var(--any-font-medium, 500);
  color: var(--any-text-primary, #1a1a1a);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Theme Toggle Button */
.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: var(--any-radius-md, 8px);
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
}

.theme-toggle:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.theme-toggle:active {
  transform: scale(0.95);
}
</style>
