/**
 * Authentication API service
 */
import apiClient from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface User {
  id: string
  email: string
  username: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
  last_login_at?: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginResponse {
  user: User
  tokens: TokenResponse
}

export interface RegisterResponse {
  user: User
  tokens: TokenResponse
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export const authApi = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials)
    return response.data
  },

  /**
   * Register a new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await apiClient.post<RegisterResponse>('/api/v1/auth/register', userData)
    return response.data
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await apiClient.post<TokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  }
}
