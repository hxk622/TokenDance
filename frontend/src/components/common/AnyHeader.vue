<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { useAuthGuard } from '@/composables/useAuthGuard'
import { Sun, Moon, Monitor, Bell, Sparkles, User, LogOut } from 'lucide-vue-next'
import WorkspaceSelector from '@/components/workspace/WorkspaceSelector.vue'
import type { Workspace } from '@/api/workspace'

// Stores
const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()
const { showLogin } = useAuthGuard()

// State
const showThemeMenu = ref(false)
const showUserMenu = ref(false)

// Theme options
const themeOptions: { mode: ThemeMode; label: string; icon: typeof Sun }[] = [
  { mode: 'light', label: '浅色', icon: Sun },
  { mode: 'dark', label: '深色', icon: Moon },
  { mode: 'system', label: '跟随系统', icon: Monitor },
]

// Computed
const themeIcon = computed(() => {
  return themeStore.resolvedTheme === 'light' ? Sun : Moon
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

const closeMenus = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
  if (!target.closest('.theme-menu-container')) {
    showThemeMenu.value = false
  }
}

// Workspace change handler
const handleWorkspaceChange = (workspace: Workspace) => {
  console.log('[AnyHeader] Workspace changed:', workspace.name)
}

onMounted(() => {
  window.addEventListener('click', closeMenus)
})

onUnmounted(() => {
  window.removeEventListener('click', closeMenus)
})
</script>

<template>
  <header class="any-header">
    <!-- Workspace Selector (only when authenticated) -->
    <WorkspaceSelector
      v-if="authStore.isAuthenticated"
      @change="handleWorkspaceChange"
    />

    <!-- Spacer -->
    <div class="header-spacer" />

    <!-- Theme toggle -->
    <div class="theme-menu-container">
      <button
        class="header-icon-btn"
        data-tooltip="主题"
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
      <button
        class="header-icon-btn"
        data-tooltip="通知"
      >
        <Bell class="icon" />
        <span class="notification-badge">4</span>
      </button>
      
      <!-- Credits -->
      <div class="credits-badge">
        <Sparkles class="icon-xs" />
        <span>1,200</span>
      </div>
      
      <!-- User avatar and menu -->
      <div class="user-menu-container">
        <button 
          class="avatar-btn"
          @click.stop="showUserMenu = !showUserMenu"
        >
          <span>{{ authStore.user?.display_name?.charAt(0) || authStore.user?.username?.charAt(0) || 'U' }}</span>
        </button>
        <!-- User dropdown -->
        <Transition name="dropdown">
          <div
            v-if="showUserMenu"
            class="user-dropdown"
          >
            <div class="dropdown-header">
              <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
              <span class="user-email">{{ authStore.user?.email }}</span>
            </div>
            <div class="dropdown-divider" />
            <button
              class="dropdown-item"
              @click="handleLogout"
            >
              <LogOut class="icon-sm" />
              <span>退出登录</span>
            </button>
          </div>
        </Transition>
      </div>
    </template>
  </header>
</template>

<style scoped>
/* Fixed top-right header */
.any-header {
  position: fixed;
  top: 12px;
  left: 280px; /* After sidebar */
  right: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 100;
}

/* Spacer to push right-side items */
.header-spacer {
  flex: 1;
}

/* Icon sizes */
.icon {
  width: 16px;
  height: 16px;
}

.icon-sm {
  width: 16px;
  height: 16px;
}

.icon-xs {
  width: 12px;
  height: 12px;
}

/* Header icon button */
.header-icon-btn {
  position: relative;
  padding: 6px;
  border-radius: 9999px;
  cursor: pointer;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.header-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

/* Header tooltip */
.header-icon-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 6px;
  padding: 4px 8px;
  background: var(--any-text-primary);
  color: var(--any-bg-primary);
  font-size: 11px;
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  pointer-events: none;
  z-index: 1000;
}

.header-icon-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

/* Notification badge */
.notification-badge {
  position: absolute;
  top: -2px;
  right: -2px;
  min-width: 14px;
  height: 14px;
  padding: 0 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 500;
  color: white;
  background: #ef4444;
  border-radius: 9999px;
}

/* Credits badge */
.credits-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  font-size: 12px;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 9999px;
}

/* Avatar button */
.avatar-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  color: white;
  background: #00B8D9;
  border: none;
  border-radius: 9999px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.avatar-btn:hover {
  background: #00D9FF;
}

/* Sign in button */
.sign-in-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 9999px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.sign-in-btn:hover {
  background: var(--any-bg-tertiary);
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
}

.dropdown-header {
  padding: 12px 16px;
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
  background: var(--any-border);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.dropdown-item:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.theme-dropdown .dropdown-item {
  border-radius: 8px;
  padding: 8px 12px;
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
</style>
