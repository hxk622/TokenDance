<template>
  <div id="app" class="min-h-screen bg-bg-primary text-text-primary">
    <RouterView v-slot="{ Component, route }">
      <Transition :name="(route.meta.transition as string) || 'page-fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>

    <!-- Login Prompt Modal -->
    <LoginPromptModal
      :visible="showLoginPrompt"
      @close="handleCloseLoginPrompt"
      @success="handleLoginSuccess"
    />
  </div>
</template>

<script setup lang="ts">
console.log('[App.vue] Script setup start')

console.log('[App.vue] Importing vue...')
import { ref, onMounted, computed } from 'vue'
console.log('[App.vue] vue imported')

console.log('[App.vue] Importing vue-router...')
import { RouterView, useRoute } from 'vue-router'
console.log('[App.vue] vue-router imported')

console.log('[App.vue] Importing auth store...')
import { useAuthStore } from '@/stores/auth'
console.log('[App.vue] auth store imported')

console.log('[App.vue] Importing LoginPromptModal...')
import LoginPromptModal from '@/components/common/LoginPromptModal.vue'
console.log('[App.vue] LoginPromptModal imported')

console.log('[App.vue] Calling useRoute()...')
const route = useRoute()
console.log('[App.vue] useRoute() done')

console.log('[App.vue] Calling useAuthStore()...')
const authStore = useAuthStore()
console.log('[App.vue] useAuthStore() done')

console.log('[App.vue] Setting up reactive state...')
const loginPromptDismissed = ref(false)
console.log('[App.vue] loginPromptDismissed ref created')

// Pages that don't need login prompt
const excludedPaths = ['/login', '/register']

// Show login prompt if:
// 1. User is not authenticated
// 2. User hasn't dismissed the prompt in this session
// 3. Not on login/register page
console.log('[App.vue] Setting up showLoginPrompt computed...')
const showLoginPrompt = computed(() => {
  console.log('[App.vue] showLoginPrompt computed evaluating...')
  return !authStore.isAuthenticated &&
         !loginPromptDismissed.value &&
         !excludedPaths.includes(route.path)
})
console.log('[App.vue] showLoginPrompt computed created')

function handleCloseLoginPrompt() {
  console.log('[App.vue] handleCloseLoginPrompt called')
  loginPromptDismissed.value = true
  // Remember dismissal for this session
  sessionStorage.setItem('login_prompt_dismissed', 'true')
}

function handleLoginSuccess() {
  console.log('[App.vue] handleLoginSuccess called')
  loginPromptDismissed.value = true
}

console.log('[App.vue] Script setup complete')

onMounted(async () => {
  console.log('[App] onMounted start')
  try {
    // Initialize auth state
    console.log('[App] calling authStore.initialize()')
    await authStore.initialize()
    console.log('[App] authStore.initialize() completed')
    
    // Check if prompt was already dismissed in this session
    if (sessionStorage.getItem('login_prompt_dismissed') === 'true') {
      loginPromptDismissed.value = true
    }
    console.log('[App] onMounted completed successfully')
  } catch (error) {
    console.error('[App] onMounted error:', error)
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
