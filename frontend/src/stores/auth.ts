/**
 * Authentication store using Pinia
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  authApi, 
  type User, 
  type LoginRequest, 
  type RegisterRequest, 
  type WeChatAuthRequest,
  type GmailAuthRequest
} from '@/api/auth'
import { useSessionStore } from '@/stores/session'
import { getApiErrorMessage } from '@/utils/errorMessages'

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
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

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
      
      // Set default workspace if provided
      if (response.default_workspace_id) {
        const sessionStore = useSessionStore()
        sessionStore.setCurrentWorkspace(response.default_workspace_id)
      }
      
      return response
    } catch (err: any) {
      error.value = getApiErrorMessage(err, '登录失败')
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
      
      // Set default workspace from registration
      if (response.default_workspace_id) {
        const sessionStore = useSessionStore()
        sessionStore.setCurrentWorkspace(response.default_workspace_id)
      }
      
      return response
    } catch (err: any) {
      error.value = getApiErrorMessage(err, '注册失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Login with WeChat OAuth
   */
  async function loginWithWeChat(code: string, state?: string) {
    isLoading.value = true
    error.value = null
    
    try {
      const request: WeChatAuthRequest = { code, state }
      const response = await authApi.loginWithWeChat(request)
      
      // Update state
      user.value = response.user
      accessToken.value = response.tokens.access_token
      refreshToken.value = response.tokens.refresh_token
      
      // Persist tokens
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      
      // Set default workspace from WeChat login
      if (response.default_workspace_id) {
        const sessionStore = useSessionStore()
        sessionStore.setCurrentWorkspace(response.default_workspace_id)
      }
      
      return response
    } catch (err: any) {
      error.value = getApiErrorMessage(err, '微信登录失败')
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Login with Gmail OAuth
   */
  async function loginWithGmail(code: string, state?: string) {
    isLoading.value = true
    error.value = null
    
    try {
      const request: GmailAuthRequest = { code, state }
      const response = await authApi.loginWithGmail(request)
      
      // Update state
      user.value = response.user
      accessToken.value = response.tokens.access_token
      refreshToken.value = response.tokens.refresh_token
      
      // Persist tokens
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      
      // Set default workspace from Gmail login
      if (response.default_workspace_id) {
        const sessionStore = useSessionStore()
        sessionStore.setCurrentWorkspace(response.default_workspace_id)
      }
      
      return response
    } catch (err: any) {
      error.value = getApiErrorMessage(err, 'Google 登录失败')
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
    console.log('[AuthStore] fetchCurrentUser start, accessToken:', !!accessToken.value)
    if (!accessToken.value) {
      console.log('[AuthStore] fetchCurrentUser: no token, returning early')
      return
    }
    
    isLoading.value = true
    error.value = null
    
    try {
      console.log('[AuthStore] fetchCurrentUser: calling authApi.getCurrentUser()')
      const currentUser = await authApi.getCurrentUser()
      console.log('[AuthStore] fetchCurrentUser: got user', currentUser?.email)
      user.value = currentUser
      return currentUser
    } catch (err: any) {
      console.error('[AuthStore] fetchCurrentUser error:', err)
      error.value = getApiErrorMessage(err, '获取用户信息失败')
      // If 401, clear auth state
      if (err.response?.status === 401) {
        console.log('[AuthStore] fetchCurrentUser: 401, logging out')
        logout()
      }
      throw err
    } finally {
      isLoading.value = false
      console.log('[AuthStore] fetchCurrentUser: finally, isLoading=false')
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
    console.log('[AuthStore] initialize start')
    const storedToken = localStorage.getItem('access_token')
    console.log('[AuthStore] initialize: storedToken exists:', !!storedToken)
    if (storedToken) {
      accessToken.value = storedToken
      refreshToken.value = localStorage.getItem('refresh_token')
      console.log('[AuthStore] initialize: tokens set, calling fetchCurrentUser')
      try {
        await fetchCurrentUser()
      } catch (e) {
        console.error('[AuthStore] initialize: fetchCurrentUser failed', e)
      }
    }
    console.log('[AuthStore] initialize completed')
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
    displayName,
    
    // Actions
    login,
    register,
    loginWithWeChat,
    loginWithGmail,
    refreshAccessToken,
    fetchCurrentUser,
    logout,
    initialize
  }
})
