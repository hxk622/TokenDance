/**
 * Simple toast notification composable
 * 
 * Uses a global event system to show toast notifications
 */
import { ref, readonly } from 'vue'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: number
  message: string
  type: ToastType
  duration: number
}

// Global toast state
const toasts = ref<Toast[]>([])
let toastId = 0

export function useToast() {
  /**
   * Show a toast notification
   */
  function showToast(message: string, type: ToastType = 'info', duration = 3000) {
    const id = ++toastId
    const toast: Toast = { id, message, type, duration }
    
    toasts.value.push(toast)
    
    // Auto remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
    
    return id
  }

  /**
   * Remove a toast by id
   */
  function removeToast(id: number) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) {
      toasts.value.splice(index, 1)
    }
  }

  /**
   * Clear all toasts
   */
  function clearToasts() {
    toasts.value = []
  }

  return {
    toasts: readonly(toasts),
    showToast,
    removeToast,
    clearToasts
  }
}
