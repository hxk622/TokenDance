<script setup lang="ts">
import { computed } from 'vue'

// Props
interface Props {
  title?: string
  transparent?: boolean
  bordered?: boolean
  sticky?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  transparent: false,
  bordered: false,
  sticky: false
})

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
        <h1 v-if="title" class="any-header-title">{{ title }}</h1>
      </slot>
    </div>
    
    <!-- Right section -->
    <div class="any-header-right">
      <slot name="right" />
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
</style>
