/**
 * useKeyboardShortcuts - 全局键盘快捷键管理
 * 
 * 为专业用户提供高效的键盘操作支持
 */

import { onMounted, onUnmounted, ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'

export interface ShortcutConfig {
  /** 是否启用 */
  enabled?: boolean
  /** 是否在输入框中禁用 */
  disableInInput?: boolean
}

export interface ShortcutCallbacks {
  onTogglePause?: () => void
  onRequestIntervene?: () => void
  onStopExecution?: () => void
  onSwitchPanel?: (direction: 'next' | 'prev') => void
  onJumpToStep?: (step: number) => void
  onToggleHelp?: () => void
}

const defaultConfig: ShortcutConfig = {
  enabled: true,
  disableInInput: true,
}

export function useKeyboardShortcuts(
  callbacks: ShortcutCallbacks,
  config: ShortcutConfig = {}
) {
  const mergedConfig = { ...defaultConfig, ...config }
  const isHelpVisible = ref(false)
  const executionStore = useExecutionStore()
  
  // 检查是否在输入框中
  function isInputFocused(): boolean {
    const activeElement = document.activeElement
    if (!activeElement) return false
    
    const tagName = activeElement.tagName.toLowerCase()
    const isInput = tagName === 'input' || tagName === 'textarea'
    const isContentEditable = activeElement.getAttribute('contenteditable') === 'true'
    
    return isInput || isContentEditable
  }
  
  // 键盘事件处理
  function handleKeyDown(event: KeyboardEvent) {
    if (!mergedConfig.enabled) return
    if (mergedConfig.disableInInput && isInputFocused()) return
    
    const { key, code, ctrlKey, metaKey, shiftKey } = event
    
    // Space - 暂停/继续
    if (code === 'Space' && !ctrlKey && !metaKey) {
      event.preventDefault()
      if (callbacks.onTogglePause) {
        callbacks.onTogglePause()
      } else {
        // 默认行为：切换执行状态
        if (executionStore.isRunning) {
          executionStore.pause()
        } else if (executionStore.isPaused) {
          executionStore.resume()
        }
      }
      return
    }
    
    // Escape - 停止执行
    if (key === 'Escape') {
      event.preventDefault()
      if (callbacks.onStopExecution) {
        callbacks.onStopExecution()
      }
      return
    }
    
    // I - 请求介入
    if (key === 'i' || key === 'I') {
      if (!ctrlKey && !metaKey) {
        event.preventDefault()
        if (callbacks.onRequestIntervene) {
          callbacks.onRequestIntervene()
        }
        return
      }
    }
    
    // Tab - 切换面板
    if (key === 'Tab' && !ctrlKey && !metaKey) {
      event.preventDefault()
      if (callbacks.onSwitchPanel) {
        callbacks.onSwitchPanel(shiftKey ? 'prev' : 'next')
      }
      return
    }
    
    // 1-9 - 跳转步骤
    if (/^[1-9]$/.test(key) && !ctrlKey && !metaKey) {
      event.preventDefault()
      const step = parseInt(key, 10)
      if (callbacks.onJumpToStep) {
        callbacks.onJumpToStep(step)
      }
      return
    }
    
    // ? - 显示帮助
    if (key === '?' || (key === '/' && shiftKey)) {
      event.preventDefault()
      isHelpVisible.value = !isHelpVisible.value
      if (callbacks.onToggleHelp) {
        callbacks.onToggleHelp()
      }
      return
    }
  }
  
  // 生命周期
  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown)
  })
  
  onUnmounted(() => {
    window.removeEventListener('keydown', handleKeyDown)
  })
  
  return {
    isHelpVisible,
    /** 手动触发快捷键帮助 */
    toggleHelp: () => {
      isHelpVisible.value = !isHelpVisible.value
    }
  }
}

/**
 * 快捷键列表（用于帮助面板显示）
 */
export const SHORTCUT_LIST = [
  { key: 'Space', description: '暂停/继续执行', category: '执行控制' },
  { key: 'Esc', description: '停止执行', category: '执行控制' },
  { key: 'I', description: '请求人工介入', category: '执行控制' },
  { key: 'Tab', description: '切换面板', category: '导航' },
  { key: 'Shift+Tab', description: '反向切换面板', category: '导航' },
  { key: '1-9', description: '跳转到指定步骤', category: '导航' },
  { key: '?', description: '显示快捷键帮助', category: '帮助' },
] as const
