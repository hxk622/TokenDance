/**
 * API Client configuration with axios
 * Handles authentication, error handling, and request/response interceptors
 */
import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token and logging
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add request ID for tracing
    const requestId = crypto.randomUUID()
    config.headers['X-Request-ID'] = requestId
    
    // Log full request details
    console.log('[API Request]', {
      requestId,
      method: config.method?.toUpperCase(),
      url: config.url,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      headers: { ...config.headers },
      params: config.params,
      data: config.data,
      timeout: config.timeout,
    })
    
    return config
  },
  (error: AxiosError) => {
    console.error('[API Request Error]', {
      message: error.message,
      code: error.code,
      config: error.config,
    })
    return Promise.reject(error)
  }
)

// Response interceptor - log and handle errors
apiClient.interceptors.response.use(
  (response) => {
    // Log full response details
    const requestId = response.config.headers?.['X-Request-ID']
    console.log('[API Response Success]', {
      requestId,
      status: response.status,
      statusText: response.statusText,
      url: response.config.url,
      method: response.config.method?.toUpperCase(),
      responseHeaders: { ...response.headers },
      data: response.data,
    })
    return response
  },
  async (error: AxiosError) => {
    const requestId = error.config?.headers?.['X-Request-ID']
    
    // Log full error details
    console.error('[API Response Error]', {
      requestId,
      url: error.config?.url,
      method: error.config?.method?.toUpperCase(),
      status: error.response?.status,
      statusText: error.response?.statusText,
      responseHeaders: error.response?.headers,
      responseData: error.response?.data,
      errorMessage: error.message,
      errorCode: error.code,
    })
    
    // Handle 401 Unauthorized - refresh token or redirect to login
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url || ''
      const isAuthRequest = requestUrl.includes('/auth/login') ||
                           requestUrl.includes('/auth/register') ||
                           requestUrl.includes('/auth/wechat') ||
                           requestUrl.includes('/auth/gmail')
      
      // Don't redirect for auth requests - let the component handle the error
      if (!isAuthRequest) {
        // Clear tokens and redirect for other 401 errors
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
      // For auth requests, just pass the error through to be handled by the component
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
