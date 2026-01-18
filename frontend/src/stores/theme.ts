import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'tokendance-theme'

export const useThemeStore = defineStore('theme', () => {
  // 用户选择的主题模式
  const mode = ref<ThemeMode>('system')
  
  // 系统偏好
  const systemPrefersDark = ref(false)
  
  // 实际应用的主题
  const resolvedTheme = computed<'light' | 'dark'>(() => {
    if (mode.value === 'system') {
      return systemPrefersDark.value ? 'dark' : 'light'
    }
    return mode.value
  })
  
  // 是否为 dark 模式
  const isDark = computed(() => resolvedTheme.value === 'dark')
  
  // 监听系统主题变化
  let mediaQuery: MediaQueryList | null = null
  
  function setupSystemListener() {
    if (typeof window === 'undefined') return
    
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    systemPrefersDark.value = mediaQuery.matches
    
    const handler = (e: MediaQueryListEvent) => {
      systemPrefersDark.value = e.matches
    }
    
    mediaQuery.addEventListener('change', handler)
  }
  
  // 应用主题到 DOM
  function applyTheme() {
    if (typeof document === 'undefined') return
    
    const html = document.documentElement
    
    if (resolvedTheme.value === 'dark') {
      html.setAttribute('data-theme', 'dark')
      html.classList.add('dark')
    } else {
      html.setAttribute('data-theme', 'light')
      html.classList.remove('dark')
    }
  }
  
  // 设置主题模式
  function setMode(newMode: ThemeMode) {
    mode.value = newMode
    localStorage.setItem(STORAGE_KEY, newMode)
  }
  
  // 切换 light/dark（忽略 system）
  function toggle() {
    const newMode = resolvedTheme.value === 'dark' ? 'light' : 'dark'
    setMode(newMode)
  }
  
  // 初始化
  function initialize() {
    // 从 localStorage 读取
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeMode | null
    if (stored && ['light', 'dark', 'system'].includes(stored)) {
      mode.value = stored
    } else {
      // 默认跟随系统（首次访问检测系统偏好）
      mode.value = 'system'
    }
    
    // 设置系统监听
    setupSystemListener()
    
    // 应用主题
    applyTheme()
  }
  
  // 监听变化自动应用
  watch(resolvedTheme, () => {
    applyTheme()
  })
  
  return {
    mode,
    resolvedTheme,
    isDark,
    setMode,
    toggle,
    initialize
  }
})
