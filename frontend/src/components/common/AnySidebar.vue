<script setup lang="ts">
import { ref, computed, provide } from 'vue'
import type { Component } from 'vue'
import { 
  PanelLeftClose, PanelLeft, Plus, Library, FolderOpen, 
  Clock, MessageSquare, Settings
} from 'lucide-vue-next'

// Types
interface NavItem {
  id: string
  label: string
  icon?: Component
  href?: string
  active?: boolean
  badge?: string | number
  onClick?: () => void
}

interface SidebarSection {
  id: string
  title?: string
  items: NavItem[]
  collapsible?: boolean
}

// Props
interface Props {
  collapsed?: boolean
  logoSrc?: string
  logoText?: string
  sections?: SidebarSection[]
  showNewButton?: boolean
  newButtonText?: string
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  logoText: 'TokenDance',
  showNewButton: true,
  newButtonText: 'New task'
})

// Emits
const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'new-click': []
  'nav-click': [item: NavItem]
}>()

// State
const isCollapsed = computed({
  get: () => props.collapsed,
  set: (value) => emit('update:collapsed', value)
})

// Provide collapsed state to children
provide('sidebarCollapsed', isCollapsed)

// Methods
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

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
  <aside class="any-sidebar" :class="{ collapsed: isCollapsed }">
    <!-- Header -->
    <div class="any-sidebar-header">
      <!-- Toggle button -->
      <button
        class="any-btn-icon any-sidebar-toggle"
        type="button"
        :aria-label="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="toggleCollapse"
      >
        <PanelLeftClose v-if="!isCollapsed" :size="20" />
        <PanelLeft v-else :size="20" />
      </button>
      
      <!-- Logo -->
      <a v-if="!isCollapsed" href="/" class="any-sidebar-logo">
        <img v-if="logoSrc" :src="logoSrc" alt="Logo" class="any-sidebar-logo-image" />
        <span class="any-sidebar-logo-text">{{ logoText }}</span>
      </a>
    </div>
    
    <!-- Navigation -->
    <nav class="any-sidebar-nav any-scrollbar">
      <!-- New button -->
      <button
        v-if="showNewButton"
        class="any-sidebar-new-btn"
        type="button"
        @click="handleNewClick"
      >
        <Plus :size="20" />
        <span v-if="!isCollapsed">{{ newButtonText }}</span>
      </button>
      
      <!-- Custom content slot -->
      <slot name="nav-start" />
      
      <!-- Sections -->
      <template v-if="sections">
        <div
          v-for="section in sections"
          :key="section.id"
          class="any-sidebar-section"
        >
          <div v-if="section.title && !isCollapsed" class="any-sidebar-section-title">
            {{ section.title }}
          </div>
          
          <template v-for="item in section.items" :key="item.id">
            <component
              :is="item.href ? 'a' : 'button'"
              :href="item.href"
              class="any-nav-item"
              :class="{ active: item.active }"
              @click="handleNavClick(item)"
            >
              <span class="any-nav-item-icon">
                <component v-if="item.icon" :is="item.icon" :size="20" />
              </span>
              <span v-if="!isCollapsed" class="any-nav-item-label">
                {{ item.label }}
              </span>
              <span v-if="!isCollapsed && item.badge" class="any-nav-item-badge">
                {{ item.badge }}
              </span>
            </component>
          </template>
        </div>
      </template>
      
      <!-- Default slot for custom navigation -->
      <slot />
      
      <!-- Custom content slot -->
      <slot name="nav-end" />
    </nav>
    
    <!-- Footer -->
    <div v-if="$slots.footer" class="any-sidebar-footer">
      <slot name="footer" />
    </div>
  </aside>
</template>

<style scoped>
.any-sidebar {
  display: flex;
  flex-direction: column;
  width: 280px;
  height: 100%;
  background: var(--any-bg-secondary, #fafafa);
  border-right: 1px solid var(--any-border, #E4E4E4);
  transition: width var(--any-duration-normal, 200ms) var(--any-ease-out, ease-out);
  overflow: hidden;
}

.any-sidebar.collapsed {
  width: 60px;
}

/* Header */
.any-sidebar-header {
  display: flex;
  align-items: center;
  gap: var(--any-space-3, 8px);
  height: 52px;
  padding: 0 var(--any-space-4, 10px);
  flex-shrink: 0;
}

.any-sidebar-toggle {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md, 8px);
  background: transparent;
  border: none;
  color: var(--any-text-secondary, #5D5D5D);
  cursor: pointer;
  transition: all var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
  flex-shrink: 0;
}

.any-sidebar-toggle:hover {
  background: var(--any-bg-hover, rgba(0, 0, 0, 0.04));
  color: var(--any-text-primary, #1a1a1a);
}

.any-sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--any-space-2, 6px);
  text-decoration: none;
}

.any-sidebar-logo-image {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
}

.any-sidebar-logo-text {
  font-size: var(--any-text-md, 16px);
  font-weight: var(--any-font-semibold, 600);
  color: var(--any-text-primary, #1a1a1a);
  white-space: nowrap;
}

/* Navigation */
.any-sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--any-space-3, 8px);
}

/* New button */
.any-sidebar-new-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--any-space-3, 8px);
  width: 100%;
  height: 40px;
  margin-bottom: var(--any-space-5, 12px);
  background: var(--any-bg-hover, rgba(0, 0, 0, 0.04));
  border: 1px dashed var(--any-border, #E4E4E4);
  border-radius: var(--any-radius-md, 8px);
  color: var(--any-text-secondary, #5D5D5D);
  font-size: var(--any-text-base, 14px);
  cursor: pointer;
  transition: all var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
}

.any-sidebar-new-btn:hover {
  background: var(--any-bg-active, rgba(0, 0, 0, 0.06));
  border-color: var(--any-border-hover, #999);
  color: var(--any-text-primary, #1a1a1a);
}

.collapsed .any-sidebar-new-btn {
  padding: 0;
}

.collapsed .any-sidebar-new-btn span {
  display: none;
}

/* Sections */
.any-sidebar-section {
  margin-bottom: var(--any-space-5, 12px);
}

.any-sidebar-section-title {
  padding: var(--any-space-3, 8px) var(--any-space-5, 12px);
  font-size: var(--any-text-xs, 12px);
  font-weight: var(--any-font-medium, 500);
  color: var(--any-text-tertiary, #888);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Nav item */
.any-nav-item {
  display: flex;
  align-items: center;
  gap: var(--any-space-5, 12px);
  width: 100%;
  padding: var(--any-space-3, 8px) var(--any-space-5, 12px);
  border-radius: var(--any-radius-md, 8px);
  color: var(--any-text-secondary, #5D5D5D);
  text-decoration: none;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast, 150ms) var(--any-ease-out, ease-out);
  text-align: left;
}

.any-nav-item:hover {
  background: var(--any-bg-hover, rgba(0, 0, 0, 0.04));
  color: var(--any-text-primary, #1a1a1a);
}

.any-nav-item.active {
  background: var(--any-bg-active, rgba(0, 0, 0, 0.06));
  color: var(--any-text-primary, #1a1a1a);
}

.any-nav-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.any-nav-item-label {
  flex: 1;
  font-size: var(--any-text-base, 14px);
  font-weight: var(--any-font-normal, 400);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed .any-nav-item-label {
  display: none;
}

.any-nav-item-badge {
  padding: var(--any-space-1, 4px) var(--any-space-2, 6px);
  font-size: var(--any-text-xs, 12px);
  background: var(--any-bg-tertiary, #f5f5f5);
  border-radius: var(--any-radius-full, 9999px);
  color: var(--any-text-tertiary, #888);
}

.collapsed .any-nav-item-badge {
  display: none;
}

/* Footer */
.any-sidebar-footer {
  padding: var(--any-space-5, 12px);
  border-top: 1px solid var(--any-border, #E4E4E4);
  flex-shrink: 0;
}
</style>
