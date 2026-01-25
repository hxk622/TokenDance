<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { useAuthStore } from '@/stores/auth'
import { useAuthGuard } from '@/composables/useAuthGuard'
import { Sun, Moon, Monitor, Bell, Sparkles, User, LogOut, Settings } from 'lucide-vue-next'

// Stores
const router = useRouter()
const themeStore = useThemeStore()
const authStore = useAuthStore()
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

onMounted(() => {
  window.addEventListener('click', closeMenus)
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
      <!-- Theme toggle -->
      <div class="theme-menu-container">
        <button
          class="header-icon-btn"
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
        <button class="header-icon-btn notification-btn">
          <Bell class="icon" />
          <span class="notification-badge">5</span>
        </button>
        
        <!-- Credits/Token Badge -->
        <button class="credits-badge">
          <Sparkles class="icon-xs" />
          <span>1,431</span>
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
              <div class="dropdown-header">
                <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
                <span class="user-email">{{ authStore.user?.email }}</span>
              </div>
              <div class="dropdown-divider" />
              <button
                class="dropdown-item"
                @click="router.push('/settings')"
              >
                <Settings class="icon-sm" />
                <span>Settings</span>
              </button>
              <button
                class="dropdown-item"
                @click="handleLogout"
              >
                <LogOut class="icon-sm" />
                <span>Sign out</span>
              </button>
            </div>
          </Transition>
        </div>
      </template>
    </div>
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
