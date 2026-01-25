<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useAuthGuard } from '@/composables/useAuthGuard'
import NotificationPanel from './NotificationPanel.vue'
import GlobalSearch from './GlobalSearch.vue'
import { 
  Sun, Moon, Monitor, Bell, Sparkles, User, LogOut, Settings,
  Search, HelpCircle, MessageSquare, CreditCard, Shield, Crown
} from 'lucide-vue-next'

// Stores
const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const { showLogin } = useAuthGuard()

// Props
interface Props {
  transparent?: boolean
}

withDefaults(defineProps<Props>(), {
  transparent: true
})

// State
const showThemeMenu = ref(false)
const showUserMenu = ref(false)
const showNotifications = ref(false)
const showSearchModal = ref(false)

// Theme options
const themeOptions: { mode: ThemeMode; label: string; icon: typeof Sun }[] = [
  { mode: 'light', label: 'Light', icon: Sun },
  { mode: 'dark', label: 'Dark', icon: Moon },
  { mode: 'system', label: 'System', icon: Monitor },
]

// Computed
const themeIcon = computed(() => {
  return themeStore.resolvedTheme === 'light' ? Sun : Moon
})

// Format token display (e.g., 1,234,567 -> 1.23M)
const formattedTokens = computed(() => {
  const remaining = authStore.maxMonthlyTokens - authStore.monthlyTokensUsed
  if (remaining >= 1_000_000) {
    return `${(remaining / 1_000_000).toFixed(1)}M`
  } else if (remaining >= 1_000) {
    return `${(remaining / 1_000).toFixed(0)}K`
  }
  return remaining.toString()
})

// Token usage percentage
const tokenUsagePercent = computed(() => {
  if (authStore.maxMonthlyTokens === 0) return 0
  return Math.round((authStore.monthlyTokensUsed / authStore.maxMonthlyTokens) * 100)
})

// User subscription tier (mock for now)
const subscriptionTier = computed(() => {
  // TODO: Get from user data
  return authStore.user?.subscription_tier || 'free'
})

const tierLabel = computed(() => {
  const labels: Record<string, string> = {
    free: '免费版',
    pro: 'Pro',
    team: 'Team',
    enterprise: 'Enterprise'
  }
  return labels[subscriptionTier.value] || '免费版'
})

// Methods
const selectTheme = (mode: ThemeMode) => {
  themeStore.setMode(mode)
  showThemeMenu.value = false
}

const handleLogout = () => {
  showUserMenu.value = false
  authStore.logout()
  router.push('/login')
}

const navigateTo = (path: string) => {
  showUserMenu.value = false
  router.push(path)
}

const openHelp = () => {
  window.open('https://docs.tokendance.ai', '_blank')
}

const openFeedback = () => {
  window.open('https://feedback.tokendance.ai', '_blank')
}

const closeMenus = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
  if (!target.closest('.theme-menu-container')) {
    showThemeMenu.value = false
  }
  if (!target.closest('.notification-container')) {
    showNotifications.value = false
  }
}

// Fetch notifications on mount
onMounted(() => {
  window.addEventListener('click', closeMenus)
  if (authStore.isAuthenticated) {
    notificationStore.fetchUnreadCount()
  }
})

onUnmounted(() => {
  window.removeEventListener('click', closeMenus)
})
</script>

<template>
  <header 
    class="any-header" 
    :class="{ 'header-transparent': transparent }"
  >
    <!-- Left section (empty or breadcrumb) -->
    <div class="header-left">
      <slot name="left" />
    </div>
    
    <!-- Center section -->
    <div class="header-center">
      <slot name="center" />
    </div>
    
    <!-- Right section -->
    <div class="header-right">
      <!-- Search button (Command+K) -->
      <button
        class="search-btn"
        title="搜索 (⌘K)"
        @click="showSearchModal = true"
      >
        <Search class="icon-sm" />
        <span class="search-label">搜索</span>
        <kbd class="search-shortcut">⌘K</kbd>
      </button>

      <!-- Theme toggle -->
      <div class="theme-menu-container">
        <button
          class="header-icon-btn"
          title="切换主题"
          @click.stop="showThemeMenu = !showThemeMenu"
        >
          <component
            :is="themeIcon"
            class="icon"
          />
        </button>
        <!-- Theme dropdown -->
        <Transition name="dropdown">
          <div
            v-if="showThemeMenu"
            class="theme-dropdown"
          >
            <button
              v-for="opt in themeOptions"
              :key="opt.mode"
              class="dropdown-item"
              :class="{ active: themeStore.mode === opt.mode }"
              @click="selectTheme(opt.mode)"
            >
              <component
                :is="opt.icon"
                class="icon-sm"
              />
              <span>{{ opt.label }}</span>
              <span
                v-if="themeStore.mode === opt.mode"
                class="check-mark"
              >✓</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Help button -->
      <button
        class="header-icon-btn"
        title="帮助文档"
        @click="openHelp"
      >
        <HelpCircle class="icon" />
      </button>
      
      <!-- Guest mode: Sign in button -->
      <template v-if="!authStore.isAuthenticated">
        <button
          class="sign-in-btn"
          @click="showLogin()"
        >
          <User class="icon-sm" />
          <span>Sign in</span>
        </button>
      </template>
      
      <!-- Authenticated: notifications, credits, avatar -->
      <template v-else>
        <!-- Notifications -->
        <div class="notification-container">
          <button
            class="header-icon-btn notification-btn"
            title="通知"
            @click.stop="showNotifications = !showNotifications"
          >
            <Bell class="icon" />
            <span
              v-if="notificationStore.unreadCount > 0"
              class="notification-badge"
            >
              {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
            </span>
          </button>
          <!-- Notification dropdown -->
          <Transition name="dropdown">
            <NotificationPanel
              v-if="showNotifications"
              class="notification-dropdown"
              @close="showNotifications = false"
            />
          </Transition>
        </div>
        
        <!-- Credits/Token Badge -->
        <button
          class="credits-badge"
          title="Token 余额 - 点击充值"
          @click="navigateTo('/billing')"
        >
          <Sparkles class="icon-xs" />
          <span>{{ formattedTokens }}</span>
          <div
            v-if="tokenUsagePercent > 80"
            class="usage-warning"
          />
        </button>
        
        <!-- User avatar and menu -->
        <div class="user-menu-container">
          <button 
            class="avatar-btn"
            @click.stop="showUserMenu = !showUserMenu"
          >
            <span v-if="!authStore.user?.avatar_url">
              {{ authStore.user?.display_name?.charAt(0) || authStore.user?.username?.charAt(0) || 'U' }}
            </span>
            <img 
              v-else 
              :src="authStore.user.avatar_url" 
              alt="avatar"
              class="avatar-img"
            >
          </button>
          <!-- User dropdown -->
          <Transition name="dropdown">
            <div
              v-if="showUserMenu"
              class="user-dropdown"
            >
              <!-- User info header -->
              <div class="dropdown-header">
                <div class="user-info-row">
                  <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
                  <span
                    v-if="subscriptionTier !== 'free'"
                    class="tier-badge"
                  >
                    <Crown class="w-3 h-3" />
                    {{ tierLabel }}
                  </span>
                </div>
                <span class="user-email">{{ authStore.user?.email }}</span>
              </div>
              
              <div class="dropdown-divider" />
              
              <!-- Account section -->
              <div class="dropdown-section-label">账户</div>
              <button
                class="dropdown-item"
                @click="navigateTo('/profile')"
              >
                <User class="icon-sm" />
                <span>个人资料</span>
              </button>
              <button
                class="dropdown-item"
                @click="navigateTo('/billing')"
              >
                <CreditCard class="icon-sm" />
                <span>订阅与账单</span>
                <span
                  v-if="subscriptionTier === 'free'"
                  class="upgrade-hint"
                >升级</span>
              </button>
              <button
                class="dropdown-item"
                @click="navigateTo('/settings/security')"
              >
                <Shield class="icon-sm" />
                <span>账号安全</span>
              </button>
              
              <div class="dropdown-divider" />
              
              <!-- Settings section -->
              <button
                class="dropdown-item"
                @click="navigateTo('/settings')"
              >
                <Settings class="icon-sm" />
                <span>设置</span>
              </button>
              <button
                class="dropdown-item"
                @click="openFeedback"
              >
                <MessageSquare class="icon-sm" />
                <span>反馈建议</span>
              </button>
              
              <div class="dropdown-divider" />
              
              <button
                class="dropdown-item logout-item"
                @click="handleLogout"
              >
                <LogOut class="icon-sm" />
                <span>退出登录</span>
              </button>
            </div>
          </Transition>
        </div>
      </template>
    </div>

    <!-- Global Search Modal -->
    <GlobalSearch v-model="showSearchModal" />
  </header>
</template>

<style scoped>
/* ============================================
   Header - AnyGen Style (Transparent)
   ============================================ */
.any-header {
  position: fixed;
  top: 0;
  left: 56px; /* After sidebar */
  right: 0;
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 90;
  background: var(--any-bg-secondary);
  transition: background var(--any-duration-normal) var(--any-ease-out);
}

.any-header.header-transparent {
  background: transparent;
  backdrop-filter: none;
}

/* Header sections */
.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-left {
  flex: 0 0 auto;
}

.header-center {
  flex: 1;
  justify-content: center;
}

.header-right {
  flex: 0 0 auto;
}

/* Icon sizes */
.icon {
  width: 20px;
  height: 20px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

.icon-xs {
  width: 14px;
  height: 14px;
}

/* Header icon button */
.header-icon-btn {
  position: relative;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  cursor: pointer;
  color: var(--any-text-tertiary);
  background: transparent;
  border: none;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.header-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

/* Notification button */
.notification-btn {
  position: relative;
}

/* Notification badge */
.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
  color: white;
  background: #E95151;
  border-radius: 9999px;
}

/* Credits/Token badge */
.credits-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 400;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 9999px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.credits-badge:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

/* Avatar button */
.avatar-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: white;
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  overflow: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.avatar-btn:hover {
  transform: scale(1.05);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Sign in button */
.sign-in-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 9999px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.sign-in-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

/* Dropdown containers */
.theme-menu-container,
.user-menu-container {
  position: relative;
}

/* Theme dropdown */
.theme-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 140px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
  z-index: 1000;
  padding: 4px;
}

/* User dropdown */
.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 200px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
  z-index: 1000;
  padding: 4px;
}

.dropdown-header {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.user-email {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

.dropdown-divider {
  height: 1px;
  margin: 4px 0;
  background: var(--any-border);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.dropdown-item:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.theme-dropdown .dropdown-item.active {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.check-mark {
  margin-left: auto;
  color: var(--any-success, #22c55e);
  font-weight: 600;
}

/* Search button */
.search-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  font-size: 13px;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.search-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

.search-label {
  font-size: 13px;
}

.search-shortcut {
  padding: 2px 5px;
  font-size: 10px;
  font-family: inherit;
  color: var(--any-text-muted);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 4px;
}

/* Notification container */
.notification-container {
  position: relative;
}

.notification-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  z-index: 1000;
}

/* Usage warning dot */
.usage-warning {
  width: 6px;
  height: 6px;
  background: #FFB800;
  border-radius: 50%;
  margin-left: 4px;
}

/* User dropdown enhancements */
.user-dropdown {
  min-width: 240px;
}

.user-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  color: #FFB800;
  background: rgba(255, 184, 0, 0.15);
  border-radius: 4px;
}

.dropdown-section-label {
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--any-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.upgrade-hint {
  margin-left: auto;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  color: var(--td-state-thinking);
  background: rgba(0, 217, 255, 0.15);
  border-radius: 4px;
}

.logout-item {
  color: var(--td-state-error, #FF3B30);
}

.logout-item:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--td-state-error, #FF3B30);
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Responsive */
@media (max-width: 768px) {
  .search-btn {
    padding: 0 8px;
  }
  
  .search-label,
  .search-shortcut {
    display: none;
  }
}

@media (max-width: 640px) {
  .any-header {
    left: 0;
    padding: 0 12px;
  }
  
  .credits-badge span {
    display: none;
  }
}
</style>
