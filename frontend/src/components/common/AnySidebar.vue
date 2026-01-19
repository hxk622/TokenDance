<script setup lang="ts">
import type { Component } from 'vue'
import { Plus } from 'lucide-vue-next'

// Types
export interface NavItem {
  id: string
  label: string
  icon?: Component
  href?: string
  active?: boolean
  onClick?: () => void
}

export interface SidebarSection {
  id: string
  items: NavItem[]
}

// Props
interface Props {
  logoText?: string
  sections?: SidebarSection[]
  showNewButton?: boolean
  newButtonTooltip?: string
}

withDefaults(defineProps<Props>(), {
  logoText: 'T',
  showNewButton: true,
  newButtonTooltip: '新建任务'
})

// Emits
const emit = defineEmits<{
  'new-click': []
  'nav-click': [item: NavItem]
}>()

const handleNewClick = () => {
  emit('new-click')
}

const handleNavClick = (item: NavItem) => {
  if (item.onClick) {
    item.onClick()
  }
  emit('nav-click', item)
}
</script>

<template>
  <aside class="any-sidebar">
    <!-- Top section -->
    <div class="sidebar-top">
      <!-- Logo -->
      <div class="sidebar-logo">
        <slot name="logo">
          <span class="logo-text">{{ logoText }}</span>
        </slot>
      </div>
      
      <!-- New button -->
      <button
        v-if="showNewButton"
        class="sidebar-icon-btn"
        type="button"
        :data-tooltip="newButtonTooltip"
        @click="handleNewClick"
      >
        <Plus class="icon" />
      </button>
      
      <!-- Custom content slot -->
      <slot name="nav-start" />
      
      <!-- Sections -->
      <template v-if="sections">
        <template
          v-for="section in sections"
          :key="section.id"
        >
          <template
            v-for="item in section.items"
            :key="item.id"
          >
            <component
              :is="item.href ? 'a' : 'button'"
              :href="item.href"
              class="sidebar-icon-btn"
              :class="{ active: item.active }"
              :data-tooltip="item.label"
              @click="handleNavClick(item)"
            >
              <component
                :is="item.icon"
                v-if="item.icon"
                class="icon"
              />
            </component>
          </template>
        </template>
      </template>
      
      <!-- Default slot for custom navigation -->
      <slot />
    </div>
    
    <!-- Bottom section -->
    <div class="sidebar-bottom">
      <slot name="footer" />
    </div>
  </aside>
</template>

<style scoped>
/* Fixed icon-only sidebar */
.any-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 56px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 8px;
  background: var(--any-bg-secondary);
  border-right: 1px solid var(--any-border);
  z-index: 100;
}

.sidebar-top,
.sidebar-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

/* Logo */
.sidebar-logo {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--any-text-primary);
  font-family: serif;
}

/* Icon button */
.sidebar-icon-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.sidebar-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.sidebar-icon-btn.active {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.sidebar-icon-btn .icon {
  width: 20px;
  height: 20px;
}

/* Tooltip - appears on hover */
.sidebar-icon-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 8px;
  padding: 6px 10px;
  background: var(--any-text-primary);
  color: var(--any-bg-primary);
  font-size: 12px;
  font-weight: 400;
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  pointer-events: none;
  z-index: 1000;
}

.sidebar-icon-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}
</style>
