/**
 * Token Manager - 管理 JWT Token 的自动刷新机制
 *
 * 滑动窗口策略：
 * - Access Token: 7 天有效期
 * - 当剩余时间 < 3 天时，自动刷新
 * - 用户持续活跃，token 永不过期
 */

import { jwtDecode } from 'jwt-decode'

interface TokenPayload {
  user_id: string
  email: string
  exp: number  // Unix timestamp (seconds)
  iat: number  // Issued at (seconds)
  type: 'access' | 'refresh'
}

// 从环境变量获取 API URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

class TokenManager {
  private refreshPromise: Promise<boolean> | null = null
  private readonly REFRESH_THRESHOLD_DAYS = 3  // 剩余 3 天时刷新
  private readonly CHECK_INTERVAL_MS = 60 * 1000  // 每分钟检查一次
  private checkTimer: ReturnType<typeof setInterval> | null = null
  private isInitialized = false  // 防止重复初始化

  /**
   * 初始化 Token 管理器
   * 启动定时检查
   */
  init() {
    // 防止重复初始化
    if (this.isInitialized) {
      console.log('[TokenManager] Already initialized, skipping...')
      return
    }

    console.log('[TokenManager] Initializing...')
    this.isInitialized = true

    // 立即检查一次
    this.checkAndRefreshToken()

    // 启动定时检查
    this.startPeriodicCheck()

    // 监听页面可见性变化
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        console.log('[TokenManager] Page became visible, checking token...')
        this.checkAndRefreshToken()
      }
    })
  }

  /**
   * 启动定时检查
   */
  private startPeriodicCheck() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer)
    }

    this.checkTimer = setInterval(() => {
      this.checkAndRefreshToken()
    }, this.CHECK_INTERVAL_MS)

    console.log('[TokenManager] Periodic check started (every 60s)')
  }

  /**
   * 停止定时检查
   */
  stop() {
    if (this.checkTimer) {
      clearInterval(this.checkTimer)
      this.checkTimer = null
      console.log('[TokenManager] Stopped')
    }
    this.isInitialized = false  // 允许重新初始化
  }

  /**
   * 检查并刷新 Token（如果需要）
   */
  async checkAndRefreshToken(): Promise<boolean> {
    const token = localStorage.getItem('access_token')

    if (!token) {
      console.log('[TokenManager] No token found')
      return false
    }

    try {
      const payload = jwtDecode<TokenPayload>(token)
      const now = Math.floor(Date.now() / 1000)  // Current time in seconds
      const expiresIn = payload.exp - now
      const daysRemaining = expiresIn / (24 * 60 * 60)

      console.log('[TokenManager] Token status:', {
        expiresAt: new Date(payload.exp * 1000).toISOString(),
        expiresInSeconds: expiresIn,
        daysRemaining: daysRemaining.toFixed(2),
        shouldRefresh: daysRemaining < this.REFRESH_THRESHOLD_DAYS
      })

      // Token 已过期
      if (expiresIn <= 0) {
        console.error('[TokenManager] Token expired, redirecting to login...')
        this.clearTokensAndRedirect()
        return false
      }

      // Token 剩余时间 < 3 天，需要刷新
      if (daysRemaining < this.REFRESH_THRESHOLD_DAYS) {
        console.log('[TokenManager] Token expires soon, refreshing...')
        return await this.refreshToken()
      }

      console.log('[TokenManager] Token is valid, no refresh needed')
      return true

    } catch (error) {
      console.error('[TokenManager] Failed to decode token:', error)
      this.clearTokensAndRedirect()
      return false
    }
  }

  /**
   * 刷新 Token
   * 使用单例模式，避免并发刷新
   */
  async refreshToken(): Promise<boolean> {
    // 如果已经有刷新请求在进行中，等待它完成
    if (this.refreshPromise) {
      console.log('[TokenManager] Refresh already in progress, waiting...')
      return this.refreshPromise
    }

    this.refreshPromise = this.doRefreshToken()

    try {
      const result = await this.refreshPromise
      return result
    } finally {
      this.refreshPromise = null
    }
  }

  /**
   * 执行 Token 刷新
   */
  private async doRefreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token')

    if (!refreshToken) {
      console.error('[TokenManager] No refresh token found')
      this.clearTokensAndRedirect()
      return false
    }

    try {
      console.log('[TokenManager] Calling refresh API...')

      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      })

      if (!response.ok) {
        throw new Error(`Refresh failed: ${response.status} ${response.statusText}`)
      }

      const data = await response.json()

      // 保存新的 tokens
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
      }

      console.log('[TokenManager] Token refreshed successfully')

      // 解码新 token 查看过期时间
      const payload = jwtDecode<TokenPayload>(data.access_token)
      const expiresAt = new Date(payload.exp * 1000)
      console.log('[TokenManager] New token expires at:', expiresAt.toISOString())

      return true

    } catch (error) {
      console.error('[TokenManager] Failed to refresh token:', error)
      this.clearTokensAndRedirect()
      return false
    }
  }

  /**
   * 清除 Tokens 并跳转到登录页
   */
  private clearTokensAndRedirect() {
    console.log('[TokenManager] Clearing tokens and redirecting to login...')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    // 避免在登录页重复跳转
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login'
    }
  }

  /**
   * 获取 Token 剩余天数
   */
  getTokenRemainingDays(): number | null {
    const token = localStorage.getItem('access_token')

    if (!token) {
      return null
    }

    try {
      const payload = jwtDecode<TokenPayload>(token)
      const now = Math.floor(Date.now() / 1000)
      const expiresIn = payload.exp - now
      return expiresIn / (24 * 60 * 60)
    } catch (error) {
      console.error('[TokenManager] Failed to decode token:', error)
      return null
    }
  }

  /**
   * 手动触发刷新（用于用户操作时）
   */
  async refreshIfNeeded(): Promise<boolean> {
    return this.checkAndRefreshToken()
  }
}

// 导出单例
export const tokenManager = new TokenManager()

// 注意：不要在这里自动初始化，应该在 main.ts 中统一初始化
// 避免重复初始化问题
