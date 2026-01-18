<template>
  <div
    id="app"
    class="min-h-screen bg-bg-primary text-text-primary"
  >
    <RouterView v-slot="{ Component, route }">
      <Transition
        :name="(route.meta.transition as string) || 'page-fade'"
        mode="out-in"
      >
        <component
          :is="Component"
          :key="route.path"
        />
      </Transition>
    </RouterView>

    <!-- Login Prompt Modal - triggered manually via useAuthGuard -->
    <LoginPromptModal
      :visible="showLoginModal"
      :message="loginModalMessage"
      @close="handleCloseLoginModal"
      @success="handleLoginSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginPromptModal from '@/components/common/LoginPromptModal.vue'

const authStore = useAuthStore()

// Login modal state - controlled by useAuthGuard composable
const showLoginModal = ref(false)
const loginModalMessage = ref('')
let loginModalResolve: ((success: boolean) => void) | null = null

/**
 * Show login modal with optional custom message
 * Returns a promise that resolves to true if login succeeds, false if cancelled
 */
function showLogin(message?: string): Promise<boolean> {
  return new Promise((resolve) => {
    loginModalMessage.value = message || ''
    showLoginModal.value = true
    loginModalResolve = resolve
  })
}

function handleCloseLoginModal() {
  showLoginModal.value = false
  loginModalMessage.value = ''
  if (loginModalResolve) {
    loginModalResolve(false)
    loginModalResolve = null
  }
}

function handleLoginSuccess() {
  showLoginModal.value = false
  loginModalMessage.value = ''
  if (loginModalResolve) {
    loginModalResolve(true)
    loginModalResolve = null
  }
}

// Provide the showLogin function globally for useAuthGuard
provide('showLoginModal', showLogin)

onMounted(async () => {
  console.log('[App] onMounted - initializing auth')
  try {
    await authStore.initialize()
    console.log('[App] Auth initialized, isAuthenticated:', authStore.isAuthenticated)
  } catch (error) {
    console.error('[App] Auth initialization error:', error)
  }
})
</script>

<style>
/* Page Transition Animations */

/* Fade transition (default) */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease-out;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* Slide up transition */
.page-slide-up-enter-active,
.page-slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.page-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Scale transition */
.page-scale-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.page-scale-leave-active {
  transition: all 0.2s ease-out;
}

.page-scale-enter-from,
.page-scale-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

/* Slide left transition (for forward navigation) */
.page-slide-left-enter-active,
.page-slide-left-leave-active {
  transition: all 0.3s ease-out;
}

.page-slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
