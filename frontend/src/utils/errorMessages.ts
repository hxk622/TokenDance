/**
 * Error message localization utility
 * Translates backend error messages to user-friendly Chinese messages
 */

// Error code to Chinese message mapping
const ERROR_MESSAGES: Record<string, string> = {
  // Authentication errors
  'Invalid credentials': '邮箱或密码错误',
  'Account is inactive': '账号已被禁用',
  'Email already registered': '该邮箱已被注册',
  'Username already taken': '该用户名已被使用',
  'Invalid refresh token': '登录已过期，请重新登录',
  'User not found or inactive': '用户不存在或已被禁用',
  
  // Password validation errors
  'Password must be at least 8 characters long': '密码至少需要8个字符',
  'Password must contain at least one uppercase letter': '密码必须包含至少一个大写字母',
  'Password must contain at least one lowercase letter': '密码必须包含至少一个小写字母',
  'Password must contain at least one digit': '密码必须包含至少一个数字',
  'Password must contain at least one special character': '密码必须包含至少一个特殊字符',
  
  // Username validation errors
  'Username must be 4-20 characters, letters, numbers, and underscores only': '用户名需要4-20个字符，只能包含字母、数字和下划线',
  
  // OAuth errors
  'Failed to get WeChat access token': '获取微信授权失败',
  'Failed to get WeChat user info': '获取微信用户信息失败',
  'Failed to get Gmail access token': '获取 Google 授权失败',
  'Failed to get Gmail user info': '获取 Google 用户信息失败',
  
  // Generic errors
  'An unexpected error occurred': '服务器发生错误，请稍后重试',
  'internal_server_error': '服务器内部错误',
  'Login failed': '登录失败',
  'Login failed. Please try again.': '登录失败，请重试',
  'Registration failed': '注册失败',
}

/**
 * Translate a backend error message to Chinese
 * @param message The error message from the backend
 * @param fallback Optional fallback message if no translation is found
 * @returns The translated Chinese message
 */
export function translateErrorMessage(message: string, fallback?: string): string {
  // Check for exact match first
  if (ERROR_MESSAGES[message]) {
    return ERROR_MESSAGES[message]
  }
  
  // Check for partial matches (for messages with variable parts)
  for (const [key, value] of Object.entries(ERROR_MESSAGES)) {
    if (message.includes(key)) {
      return value
    }
  }
  
  // Return fallback or the original message
  return fallback || message
}

/**
 * Get error message from an API error response
 * @param error The error object from axios
 * @param defaultMessage Default message if no specific error is found
 * @returns The translated error message
 */
export function getApiErrorMessage(error: any, defaultMessage = '操作失败，请重试'): string {
  // Try to get the detail from the response
  const detail = error?.response?.data?.detail
  if (detail) {
    return translateErrorMessage(detail, defaultMessage)
  }
  
  // Try to get the message from the response
  const message = error?.response?.data?.message
  if (message) {
    return translateErrorMessage(message, defaultMessage)
  }
  
  // Try to get the error field from the response
  const errorField = error?.response?.data?.error
  if (errorField) {
    return translateErrorMessage(errorField, defaultMessage)
  }
  
  // Check for network errors
  if (error?.code === 'ECONNABORTED' || error?.message?.includes('timeout')) {
    return '请求超时，请检查网络连接'
  }
  
  if (error?.message === 'Network Error' || !error?.response) {
    return '网络连接失败，请检查网络'
  }
  
  // Return default message
  return defaultMessage
}
