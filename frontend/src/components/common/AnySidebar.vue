<script setup lang="ts">
import { ref, computed, onMounted, watch, type Component } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSearchStore } from '@/stores/search'
import { useGlobalShortcut } from '@/composables/useGlobalShortcut'
import { EXTERNAL_LINKS } from '@/config/externalLinks'
import { trackEvent } from '@/utils/telemetry'
import { 
  Plus, Search, BookOpen, Clock,
  HelpCircle, MessageCircle, Smartphone, ChevronRight,
  PanelLeftClose, PanelLeft
} from 'lucide-vue-next'

// Constants
const SIDEBAR_STORAGE_KEY = 'tokendance-sidebar-expanded'

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
  newButtonTooltip: '新建任务',
  tokenUsed: 0,
  tokenTotal: 100
})

// Emits
const emit = defineEmits<{
  'new-click': []
  'nav-click': [item: NavItem]
  'recent-click': [item: RecentItem]
  'expand-change': [expanded: boolean]
  'token-click': []
  'help-click': []
  'community-click': []
  'mobile-click': []
  'projects-click': []
}>()

// Router
const router = useRouter()
const route = useRoute()
const searchStore = useSearchStore()

// State - restore from localStorage
const isExpanded = ref(false)
const isRecentsOpen = ref(true)

const applySidebarState = () => {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('sidebar-expanded', isExpanded.value)
}

// Initialize from localStorage
onMounted(() => {
  const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY)
  if (stored === 'true') {
    isExpanded.value = true
  }
  applySidebarState()
})

watch(isExpanded, () => {
  applySidebarState()
})

// Keyboard shortcut: Cmd+B to toggle sidebar
useGlobalShortcut('b', () => {
  toggleExpand()
}, { metaOrCtrl: true })

// Computed
const tokenPercentage = computed(() => {
  if (props.tokenTotal <= 0) return 0
  return Math.min(100, Math.round((props.tokenUsed / props.tokenTotal) * 100))
})

const strokeDashoffset = computed(() => {
  const circumference = 2 * Math.PI * 12 // r=12
  return circumference - (tokenPercentage.value / 100) * circumference
})

const tokenUsageClass = computed(() => {
  if (tokenPercentage.value >= 95) return 'danger'
  if (tokenPercentage.value >= 80) return 'warning'
  return 'normal'
})

const formatTokens = (value: number) => {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`
  return value.toString()
}

const tokenUsageText = computed(() => {
  return `${formatTokens(props.tokenUsed)} / ${formatTokens(props.tokenTotal)}`
})

const tokenRingStyle = computed(() => {
  if (tokenUsageClass.value === 'danger') return { '--token-ring-color': '#EF4444' }
  if (tokenUsageClass.value === 'warning') return { '--token-ring-color': '#F59E0B' }
  return { '--token-ring-color': '#9652DE' }
})

// Methods
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
  localStorage.setItem(SIDEBAR_STORAGE_KEY, String(isExpanded.value))
  emit('expand-change', isExpanded.value)
}

const handleNewClick = () => {
  emit('new-click')
}

const handleNavClick = (item: NavItem) => {
  // Built-in navigation handling
  let handled = false
  switch (item.id) {
    case 'search':
      searchStore.open()
      trackEvent('sidebar_search_open', { source: 'sidebar' })
      handled = true
      break
    case 'files':
      router.push('/files')
      trackEvent('sidebar_files_open', { source: 'sidebar' })
      handled = true
      break
    case 'history':
      router.push('/history')
      trackEvent('sidebar_history_open', { source: 'sidebar' })
      handled = true
      break
    case 'library':
      router.push('/files')
      trackEvent('sidebar_library_open', { source: 'sidebar' })
      handled = true
      break
  }
  
  if (item.href && !handled) {
    router.push(item.href)
  }
  if (item.onClick) {
    item.onClick()
  }
  emit('nav-click', item)
}

const handleRecentClick = (item: RecentItem) => {
  emit('recent-click', item)
}

const handleProjectsClick = () => {
  router.push('/history')
  emit('projects-click')
  trackEvent('sidebar_projects_open', { source: 'sidebar' })
}

const handleTokenClick = () => {
  emit('token-click')
  trackEvent('sidebar_token_open', { source: 'sidebar' })
}

const handleHelpClick = () => {
  // Open help docs in new tab
  window.open(EXTERNAL_LINKS.docs, '_blank')
  emit('help-click')
  trackEvent('sidebar_help_open', { source: 'sidebar' })
}

const handleCommunityClick = () => {
  // Open Discord/community in new tab
  window.open(EXTERNAL_LINKS.community, '_blank')
  emit('community-click')
  trackEvent('sidebar_community_open', { source: 'sidebar' })
}

const handleMobileClick = () => {
  // Parent can show modal or toast
  emit('mobile-click')
  trackEvent('sidebar_mobile_open', { source: 'sidebar' })
}

const toggleRecents = () => {
  isRecentsOpen.value = !isRecentsOpen.value
}

// Default nav items (AnyGen style)
const defaultNavItems = computed<NavItem[]>(() => [
  { id: 'search', label: '搜索', icon: Search },
  { id: 'library', label: '文件库', icon: BookOpen, active: route.path.startsWith('/files') },
])

const isItemActive = (item: NavItem) => {
  if (item.active) return true
  if (item.href) return route.path.startsWith(item.href)
  return false
}
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
          data-tooltip="展开侧边栏"
          :aria-label="isExpanded ? '收起侧边栏' : '展开侧边栏'"
          :aria-expanded="isExpanded"
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
          :aria-label="newButtonTooltip"
          @click="handleNewClick"
        >
          <Plus class="icon" />
        </button>
        
        <!-- Default nav icons -->
        <button
          v-for="item in defaultNavItems"
          :key="item.id"
          class="sidebar-icon-btn"
          :class="{ active: isItemActive(item) }"
          :data-tooltip="item.label"
          :aria-label="item.label"
          :aria-current="isItemActive(item) ? 'page' : undefined"
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
              :class="{ active: isItemActive(item) }"
              :data-tooltip="item.label"
              :aria-label="item.label"
              :aria-current="isItemActive(item) ? 'page' : undefined"
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
        <button
          class="token-ring-mini"
          :class="tokenUsageClass"
          :style="tokenRingStyle"
          :data-tooltip="`Token 用量 ${tokenUsageText}`"
          aria-label="Token 用量"
          @click="handleTokenClick"
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
        </button>
        
        <!-- Help -->
        <button
          class="sidebar-icon-btn"
          data-tooltip="帮助"
          aria-label="帮助"
          @click="handleHelpClick"
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
            aria-label="收起侧边栏"
            :aria-expanded="isExpanded"
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
          <span>新建任务</span>
        </button>
        
        <!-- Nav Links -->
        <button
          v-for="item in defaultNavItems"
          :key="item.id"
          class="nav-item"
          :class="{ active: isItemActive(item) }"
          :aria-current="isItemActive(item) ? 'page' : undefined"
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
          <button 
            class="section-header clickable"
            aria-label="查看所有项目"
            @click="handleProjectsClick"
          >
            <span class="section-title">项目</span>
            <ChevronRight class="w-4 h-4 text-tertiary" />
          </button>
        </div>
        
        <div class="list-section">
          <button
            class="section-header"
            :aria-expanded="isRecentsOpen"
            aria-label="展开或收起最近"
            @click="toggleRecents"
          >
            <span class="section-title">最近</span>
            <ChevronRight
              class="w-4 h-4 text-tertiary"
              :class="{ rotated: isRecentsOpen }"
            />
          </button>
          <div v-if="isRecentsOpen">
            <div
              v-if="recentItems && recentItems.length > 0"
              class="recent-list"
            >
              <button
                v-for="item in recentItems"
                :key="item.id"
                class="recent-item"
                :title="item.title"
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
            <div
              v-else
              class="empty-recents"
            >
              <span>暂无最近项目</span>
              <button
                class="empty-cta"
                @click="handleNewClick"
              >
                新建任务
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Bottom Section -->
      <div class="expanded-bottom">
        <!-- Token Progress -->
        <button
          class="token-progress-card"
          :class="tokenUsageClass"
          :style="tokenRingStyle"
          aria-label="Token 用量"
          @click="handleTokenClick"
        >
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
          <span class="token-label">Token 用量</span>
          <span class="token-pct">{{ tokenUsageText }}</span>
          <span class="token-percent">{{ tokenPercentage }}%</span>
        </button>
        
        <!-- Footer Links -->
        <div class="footer-links">
          <button
            class="footer-link"
            data-tooltip="帮助"
            aria-label="帮助"
            @click="handleHelpClick"
          >
            <HelpCircle class="w-5 h-5" />
          </button>
          <button
            class="footer-link"
            data-tooltip="社区"
            aria-label="社区"
            @click="handleCommunityClick"
          >
            <MessageCircle class="w-5 h-5" />
          </button>
          <button
            class="footer-link"
            data-tooltip="移动端"
            aria-label="移动端"
            @click="handleMobileClick"
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
  width: var(--sidebar-collapsed-width);
  display: flex;
  flex-direction: column;
  background: var(--any-bg-primary);
  border-right: 1px solid var(--any-border);
  z-index: 100;
  transition: width var(--any-duration-normal) var(--any-ease-out);
}

.any-sidebar.expanded {
  width: var(--sidebar-expanded-width);
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

.token-ring-mini.warning .ring-text {
  color: #F59E0B;
}

.token-ring-mini.danger .ring-text {
  color: #EF4444;
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
  width: 100%;
  padding: 8px 0;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: opacity var(--any-duration-fast) var(--any-ease-out);
}

.section-header.clickable:hover {
  opacity: 0.7;
}
.section-header .rotated {
  transform: rotate(90deg);
  transition: transform var(--any-duration-fast) var(--any-ease-out);
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

.empty-recents {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 10px;
  color: var(--any-text-tertiary);
  font-size: 13px;
}

.empty-cta {
  align-self: flex-start;
  padding: 6px 10px;
  font-size: 12px;
  border-radius: var(--any-radius-sm);
  border: 1px solid var(--any-border);
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.empty-cta:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
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

.token-progress-card.warning {
  border-color: rgba(245, 158, 11, 0.4);
}

.token-progress-card.danger {
  border-color: rgba(239, 68, 68, 0.5);
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

.token-percent {
  font-size: 11px;
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
