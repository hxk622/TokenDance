<script setup lang="ts">
import { ref, computed, type Component } from 'vue'
import { 
  Plus, Search, BookOpen, FolderOpen, Clock,
  HelpCircle, MessageCircle, Smartphone, ChevronRight,
  PanelLeftClose, PanelLeft
} from 'lucide-vue-next'

// Types
export interface NavItem {
  id: string
  label: string
  icon?: Component
  href?: string
  active?: boolean
  onClick?: () => void
}

export interface RecentItem {
  id: string
  title: string
  type: 'task' | 'doc' | 'page'
  icon?: Component
}

export interface SidebarSection {
  id: string
  title?: string
  items: NavItem[]
}

// Props
interface Props {
  logoText?: string
  sections?: SidebarSection[]
  recentItems?: RecentItem[]
  showNewButton?: boolean
  newButtonTooltip?: string
  tokenUsed?: number
  tokenTotal?: number
}

const props = withDefaults(defineProps<Props>(), {
  logoText: 'TD',
  showNewButton: true,
  newButtonTooltip: 'New task',
  tokenUsed: 0,
  tokenTotal: 100
})

// Emits
const emit = defineEmits<{
  'new-click': []
  'nav-click': [item: NavItem]
  'recent-click': [item: RecentItem]
  'expand-change': [expanded: boolean]
}>()

// State
const isExpanded = ref(false)

// Computed
const tokenPercentage = computed(() => {
  if (props.tokenTotal <= 0) return 0
  return Math.min(100, Math.round((props.tokenUsed / props.tokenTotal) * 100))
})

const strokeDashoffset = computed(() => {
  const circumference = 2 * Math.PI * 12 // r=12
  return circumference - (tokenPercentage.value / 100) * circumference
})

// Methods
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
  emit('expand-change', isExpanded.value)
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

const handleRecentClick = (item: RecentItem) => {
  emit('recent-click', item)
}

// Default nav items (AnyGen style)
const defaultNavItems: NavItem[] = [
  { id: 'search', label: 'Search', icon: Search },
  { id: 'library', label: 'Library', icon: BookOpen },
]
</script>

<template>
  <aside 
    class="any-sidebar" 
    :class="{ expanded: isExpanded }"
  >
    <!-- Collapsed View -->
    <div 
      class="sidebar-collapsed"
      :class="{ hidden: isExpanded }"
    >
      <div class="collapsed-top">
        <!-- Expand Button -->
        <button
          class="sidebar-icon-btn"
          type="button"
          data-tooltip="Expand"
          @click="toggleExpand"
        >
          <PanelLeft class="icon" />
        </button>
        
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
        
        <!-- Default nav icons -->
        <button
          v-for="item in defaultNavItems"
          :key="item.id"
          class="sidebar-icon-btn"
          :class="{ active: item.active }"
          :data-tooltip="item.label"
          @click="handleNavClick(item)"
        >
          <component
            :is="item.icon"
            class="icon"
          />
        </button>
        
        <!-- Custom sections -->
        <template v-if="sections">
          <template
            v-for="section in sections"
            :key="section.id"
          >
            <button
              v-for="item in section.items"
              :key="item.id"
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
            </button>
          </template>
        </template>
      </div>
      
      <div class="collapsed-bottom">
        <!-- Token Progress Ring -->
        <div
          class="token-ring-mini"
          data-tooltip="Token usage"
        >
          <svg
            width="26"
            height="26"
            viewBox="0 0 26 26"
          >
            <circle 
              cx="13"
              cy="13"
              r="12" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              class="ring-bg"
            />
            <circle 
              cx="13"
              cy="13"
              r="12" 
              fill="none" 
              stroke="var(--token-ring-color, #9652DE)" 
              stroke-width="2" 
              stroke-linecap="round"
              :stroke-dasharray="2 * Math.PI * 12"
              :stroke-dashoffset="strokeDashoffset"
              class="ring-progress"
            />
          </svg>
          <span class="ring-text">{{ tokenPercentage }}%</span>
        </div>
        
        <!-- Help -->
        <button
          class="sidebar-icon-btn"
          data-tooltip="Help"
        >
          <HelpCircle class="icon" />
        </button>
        
        <slot name="footer" />
      </div>
    </div>
    
    <!-- Expanded View -->
    <div 
      class="sidebar-expanded"
      :class="{ hidden: !isExpanded }"
    >
      <div class="expanded-header">
        <div class="header-left">
          <button
            class="sidebar-icon-btn"
            type="button"
            @click="toggleExpand"
          >
            <PanelLeftClose class="icon" />
          </button>
        </div>
      </div>
      
      <div class="expanded-nav">
        <!-- New Task Button -->
        <button
          v-if="showNewButton"
          class="new-task-btn"
          @click="handleNewClick"
        >
          <Plus class="w-5 h-5" />
          <span>New task</span>
        </button>
        
        <!-- Nav Links -->
        <button
          v-for="item in defaultNavItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: item.active }"
          @click="handleNavClick(item)"
        >
          <component
            :is="item.icon"
            class="nav-icon"
          />
          <span class="nav-label">{{ item.label }}</span>
        </button>
      </div>
      
      <!-- Recents List -->
      <div class="expanded-list">
        <div class="list-section">
          <div class="section-header">
            <span class="section-title">Projects</span>
            <ChevronRight class="w-4 h-4 text-tertiary" />
          </div>
        </div>
        
        <div 
          v-if="recentItems && recentItems.length > 0" 
          class="list-section"
        >
          <div class="section-header">
            <span class="section-title">Recents</span>
            <ChevronRight class="w-4 h-4 text-tertiary" />
          </div>
          <div class="recent-list">
            <button
              v-for="item in recentItems.slice(0, 8)"
              :key="item.id"
              class="recent-item"
              @click="handleRecentClick(item)"
            >
              <div class="recent-icon">
                <component
                  :is="item.icon || Clock"
                  class="w-4 h-4"
                />
              </div>
              <span class="recent-title">{{ item.title }}</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Bottom Section -->
      <div class="expanded-bottom">
        <!-- Token Progress -->
        <div class="token-progress-card">
          <div class="token-ring-wrapper">
            <svg
              width="26"
              height="26"
              viewBox="0 0 26 26"
            >
              <circle 
                cx="13"
                cy="13"
                r="12" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2" 
                class="ring-bg"
              />
              <circle 
                cx="13"
                cy="13"
                r="12" 
                fill="none" 
                stroke="var(--token-ring-color, #9652DE)" 
                stroke-width="2" 
                stroke-linecap="round"
                :stroke-dasharray="2 * Math.PI * 12"
                :stroke-dashoffset="strokeDashoffset"
                class="ring-progress"
              />
            </svg>
            <span class="ring-text-sm">{{ tokenPercentage }}%</span>
          </div>
          <span class="token-label">Get started</span>
          <span class="token-pct">{{ tokenPercentage }}%</span>
        </div>
        
        <!-- Footer Links -->
        <div class="footer-links">
          <button
            class="footer-link"
            data-tooltip="Help"
          >
            <HelpCircle class="w-5 h-5" />
          </button>
          <button
            class="footer-link"
            data-tooltip="Community"
          >
            <MessageCircle class="w-5 h-5" />
          </button>
          <button
            class="footer-link"
            data-tooltip="Mobile App"
          >
            <Smartphone class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
/* ============================================
   Sidebar - AnyGen Style
   ============================================ */
.any-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 56px;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
  border-right: 1px solid var(--any-border);
  z-index: 100;
  transition: width var(--any-duration-normal) var(--any-ease-out);
}

.any-sidebar.expanded {
  width: 280px;
}

/* Hidden state */
.hidden {
  opacity: 0;
  pointer-events: none;
  position: absolute;
}

/* ============================================
   Collapsed View
   ============================================ */
.sidebar-collapsed {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  padding: 12px 8px;
  transition: opacity var(--any-duration-fast) var(--any-ease-out);
}

.collapsed-top,
.collapsed-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
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
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.sidebar-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.sidebar-icon-btn.active {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.sidebar-icon-btn .icon {
  width: 20px;
  height: 20px;
}

/* Tooltip */
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
  transition: all var(--any-duration-fast) var(--any-ease-out);
  pointer-events: none;
  z-index: 1000;
}

.sidebar-icon-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

/* Token Ring Mini */
.token-ring-mini {
  position: relative;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.token-ring-mini[data-tooltip]::after {
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
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-out);
  pointer-events: none;
  z-index: 1000;
}

.token-ring-mini:hover[data-tooltip]::after {
  opacity: 1;
  visibility: visible;
}

.ring-bg {
  color: var(--any-border);
}

.ring-progress {
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 0.3s ease-out;
}

.ring-text {
  position: absolute;
  font-size: 8px;
  font-weight: 500;
  color: var(--any-text-secondary);
}

/* ============================================
   Expanded View
   ============================================ */
.sidebar-expanded {
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: opacity var(--any-duration-fast) var(--any-ease-out);
}

.expanded-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border-bottom: 1px solid var(--any-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expanded-nav {
  padding: 12px;
}

/* New Task Button */
.new-task-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  height: 40px;
  margin-bottom: 12px;
  background: var(--any-bg-hover);
  border: 1px dashed var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.new-task-btn:hover {
  background: var(--any-bg-tertiary);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

/* Nav Item */
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.nav-item:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.nav-item.active {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
}

/* List Section */
.expanded-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.list-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  cursor: pointer;
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-tertiary);
}

.text-tertiary {
  color: var(--any-text-tertiary);
}

/* Recent List */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.recent-item:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.recent-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-sm);
  background: var(--any-bg-tertiary);
  color: var(--any-text-tertiary);
  flex-shrink: 0;
}

.recent-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ============================================
   Expanded Bottom
   ============================================ */
.expanded-bottom {
  padding: 12px;
  border-top: 1px solid var(--any-border);
}

/* Token Progress Card */
.token-progress-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  margin-bottom: 12px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.token-progress-card:hover {
  background: var(--any-bg-hover);
}

.token-ring-wrapper {
  position: relative;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ring-text-sm {
  position: absolute;
  font-size: 7px;
  font-weight: 500;
  color: var(--any-text-tertiary);
}

.token-label {
  flex: 1;
  font-size: 14px;
  color: var(--any-text-primary);
}

.token-pct {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

/* Footer Links */
.footer-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.footer-link {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md);
  color: var(--any-text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.footer-link:hover {
  color: var(--any-text-secondary);
  background: var(--any-bg-hover);
}
</style>
