/**
 * Authentication store using Pinia
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type User, type LoginRequest, type RegisterRequest, type TokenResponse } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isAuthenticated = computed(() => !!user.value && !!accessToken.value)
  const userEmail = computed(() => user.value?.email || '')
  const userName = computed(() => user.value?.username || '')

  /**
   * Login with email and password
   */
  async function login(credentials: LoginRequest) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.login(credentials)
      
      // Update state
      user.value = response.user
      accessToken.value = response.tokens.access_token
      refreshToken.value = response.tokens.refresh_token
      
      // Persist tokens
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Register a new user
   */
  async function register(userData: RegisterRequest) {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await authApi.register(userData)
      
      // Update state
      user.value = response.user
      accessToken.value = response.tokens.access_token
      refreshToken.value = response.tokens.refresh_token
      
      // Persist tokens
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      
      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Refresh access token
   */
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }
    
    try {
      const tokens = await authApi.refreshToken(refreshToken.value)
      
      // Update tokens
      accessToken.value = tokens.access_token
      refreshToken.value = tokens.refresh_token
      
      // Persist tokens
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      
      return tokens
    } catch (err) {
      // Refresh failed, clear auth state
      logout()
      throw err
    }
  }

  /**
   * Fetch current user info
   */
  async function fetchCurrentUser() {
    if (!accessToken.value) {
      return
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      const currentUser = await authApi.getCurrentUser()
      user.value = currentUser
      return currentUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch user'
      // If 401, clear auth state
      if (err.response?.status === 401) {
        logout()
      }
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Logout
   */
  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    error.value = null
    
    // Clear tokens from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  /**
   * Initialize auth state from localStorage
   */
  async function initialize() {
    const storedToken = localStorage.getItem('access_token')
    if (storedToken) {
      accessToken.value = storedToken
      refreshToken.value = localStorage.getItem('refresh_token')
      await fetchCurrentUser()
    }
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    isLoading,
    error,
    
    // Computed
    isAuthenticated,
    userEmail,
    userName,
    
    // Actions
    login,
    register,
    refreshAccessToken,
    fetchCurrentUser,
    logout,
    initialize
  }
})
