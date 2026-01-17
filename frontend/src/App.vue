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
import { ref, onMounted, computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LoginPromptModal from '@/components/common/LoginPromptModal.vue'

const route = useRoute()
const authStore = useAuthStore()

const loginPromptDismissed = ref(false)

// Pages that don't need login prompt
const excludedPaths = ['/login', '/register']

// Show login prompt if:
// 1. User is not authenticated
// 2. User hasn't dismissed the prompt in this session
// 3. Not on login/register page
const showLoginPrompt = computed(() => {
  return !authStore.isAuthenticated &&
         !loginPromptDismissed.value &&
         !excludedPaths.includes(route.path)
})

function handleCloseLoginPrompt() {
  loginPromptDismissed.value = true
  // Remember dismissal for this session
  sessionStorage.setItem('login_prompt_dismissed', 'true')
}

function handleLoginSuccess() {
  loginPromptDismissed.value = true
}

onMounted(async () => {
  // Initialize auth state
  await authStore.initialize()
  
  // Check if prompt was already dismissed in this session
  if (sessionStorage.getItem('login_prompt_dismissed') === 'true') {
    loginPromptDismissed.value = true
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
