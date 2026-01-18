/**
 * Auth Guard Composable
 * 
 * Provides a way to require authentication before performing protected actions.
 * If user is not authenticated, shows the login modal and waits for completion.
 */
import { inject } from 'vue'
import { useAuthStore } from '@/stores/auth'

// Type for the showLoginModal function provided by App.vue
type ShowLoginModalFn = (message?: string) => Promise<boolean>

/**
 * Auth guard composable for protecting actions that require authentication
 * 
 * Usage:
 * ```ts
 * const { requireAuth, isAuthenticated } = useAuthGuard()
 * 
 * async function handleSubmit() {
 *   // This will show login modal if not authenticated
 *   const canProceed = await requireAuth('请先登录后发送请求')
 *   if (!canProceed) return // User cancelled login
 *   
 *   // Proceed with the action
 *   await submitTask()
 * }
 * ```
 */
export function useAuthGuard() {
  const authStore = useAuthStore()
  const showLoginModal = inject<ShowLoginModalFn>('showLoginModal')
  
  /**
   * Check if user is authenticated
   */
  const isAuthenticated = () => authStore.isAuthenticated
  
  /**
   * Require authentication before proceeding
   * 
   * @param message - Optional message to show in the login modal
   * @returns Promise<boolean> - true if user is authenticated (or just logged in), false if cancelled
   */
  async function requireAuth(message?: string): Promise<boolean> {
    // Already authenticated, proceed immediately
    if (authStore.isAuthenticated) {
      return true
    }
    
    // Not authenticated, show login modal
    if (!showLoginModal) {
      console.error('[useAuthGuard] showLoginModal not provided. Make sure App.vue provides it.')
      return false
    }
    
    // Show modal and wait for result
    const loginSuccess = await showLoginModal(message)
    return loginSuccess
  }
  
  /**
   * Show login modal without checking authentication status
   * Useful for "Sign in" button clicks
   * 
   * @param message - Optional message to show in the login modal
   * @returns Promise<boolean> - true if login succeeded, false if cancelled
   */
  async function showLogin(message?: string): Promise<boolean> {
    if (!showLoginModal) {
      console.error('[useAuthGuard] showLoginModal not provided.')
      return false
    }
    return showLoginModal(message)
  }
  
  return {
    isAuthenticated,
    requireAuth,
    showLogin,
  }
}
