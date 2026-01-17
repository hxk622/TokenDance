import { ref, computed, watch, onMounted, onUnmounted, type Ref } from 'vue'

interface ScrollSyncOptions {
  /**
   * 滚动模式
   * - 'instant': 立即滚动
   * - 'smooth': 平滑滚动
   * - 'manual': 手动控制
   */
  mode?: 'instant' | 'smooth' | 'manual'
  
  /**
   * 平滑滚动持续时间 (ms)
   */
  duration?: number
  
  /**
   * 用户阅读时锁定滚动
   */
  lockWhileReading?: boolean
  
  /**
   * 阅读锁定超时时间 (ms) - 用户停止滚动后多久恢复自动滚动
   */
  readingLockTimeout?: number
  
  /**
   * 只高亮不滚动
   */
  highlightOnly?: boolean
  
  /**
   * 底部阈值 (px) - 距离底部多少像素内认为是在底部
   */
  bottomThreshold?: number
}

const defaultOptions: Required<ScrollSyncOptions> = {
  mode: 'smooth',
  duration: 300,
  lockWhileReading: true,
  readingLockTimeout: 5000,
  highlightOnly: false,
  bottomThreshold: 50
}

/**
 * 智能滚动联动 composable
 * 
 * 功能：
 * 1. 检测用户阅读状态（滚动后 5s 内锁定）
 * 2. 新日志到达时智能决策是否滚动
 * 3. 提供"跳转到最新"按钮状态
 */
export function useScrollSync(
  containerRef: Ref<HTMLElement | null>,
  options: ScrollSyncOptions = {}
) {
  const opts = { ...defaultOptions, ...options }
  
  // === State ===
  
  /** 是否启用自动滚动 */
  const autoScroll = ref(true)
  
  /** 用户是否正在阅读（手动滚动后锁定） */
  const isUserReading = ref(false)
  
  /** 是否在底部 */
  const isAtBottom = ref(true)
  
  /** 是否有新内容（用于显示"跳转到最新"按钮） */
  const hasNewContent = ref(false)
  
  /** 新内容计数 */
  const newContentCount = ref(0)
  
  /** 滚动锁定计时器 */
  let readingLockTimer: ReturnType<typeof setTimeout> | null = null
  
  /** 上次滚动时间 */
  let lastScrollTime = 0
  
  /** 快速点击检测 */
  let rapidClickCount = 0
  let rapidClickTimer: ReturnType<typeof setTimeout> | null = null
  
  // === Computed ===
  
  /** 是否应该自动滚动 */
  const shouldAutoScroll = computed(() => {
    if (opts.mode === 'manual') return false
    if (opts.highlightOnly) return false
    if (isUserReading.value && opts.lockWhileReading) return false
    return autoScroll.value && isAtBottom.value
  })
  
  /** 是否显示"跳转到最新"按钮 */
  const showJumpToLatest = computed(() => {
    return hasNewContent.value && !isAtBottom.value
  })
  
  // === Methods ===
  
  /**
   * 检查是否在底部
   */
  function checkIsAtBottom(): boolean {
    const el = containerRef.value
    if (!el) return true
    
    const { scrollTop, scrollHeight, clientHeight } = el
    return scrollHeight - scrollTop - clientHeight < opts.bottomThreshold
  }
  
  /**
   * 滚动到底部
   */
  function scrollToBottom(behavior: ScrollBehavior = 'smooth') {
    const el = containerRef.value
    if (!el) return
    
    const targetScroll = el.scrollHeight - el.clientHeight
    
    if (opts.mode === 'instant' || behavior === 'auto') {
      el.scrollTop = targetScroll
    } else {
      el.scrollTo({
        top: targetScroll,
        behavior: 'smooth'
      })
    }
    
    // 重置新内容状态
    hasNewContent.value = false
    newContentCount.value = 0
    isAtBottom.value = true
  }
  
  /**
   * 滚动到指定元素
   */
  function scrollToElement(
    selector: string, 
    options?: { behavior?: ScrollBehavior; block?: ScrollLogicalPosition }
  ) {
    const el = containerRef.value
    if (!el) return
    
    const target = el.querySelector(selector)
    if (!target) return
    
    // 检测快速点击
    const now = Date.now()
    if (now - lastScrollTime < 5000) {
      rapidClickCount++
      
      // 如果 5 秒内连续点击，只高亮不滚动
      if (rapidClickCount >= 2 && opts.highlightOnly !== true) {
        console.log('[ScrollSync] Rapid click detected, highlight only')
        return
      }
    } else {
      rapidClickCount = 1
    }
    lastScrollTime = now
    
    // 清除之前的快速点击计时器
    if (rapidClickTimer) {
      clearTimeout(rapidClickTimer)
    }
    rapidClickTimer = setTimeout(() => {
      rapidClickCount = 0
    }, 5000)
    
    // 执行滚动
    target.scrollIntoView({
      behavior: options?.behavior || (opts.mode === 'instant' ? 'auto' : 'smooth'),
      block: options?.block || 'start'
    })
  }
  
  /**
   * 处理用户滚动事件
   */
  function handleScroll() {
    const wasAtBottom = isAtBottom.value
    isAtBottom.value = checkIsAtBottom()
    
    // 如果用户从底部滚动离开，标记为阅读状态
    if (wasAtBottom && !isAtBottom.value) {
      enterReadingMode()
    }
    
    // 如果滚动回底部，退出阅读模式
    if (!wasAtBottom && isAtBottom.value) {
      exitReadingMode()
      hasNewContent.value = false
      newContentCount.value = 0
    }
  }
  
  /**
   * 进入阅读模式
   */
  function enterReadingMode() {
    if (!opts.lockWhileReading) return
    
    isUserReading.value = true
    autoScroll.value = false
    
    // 设置阅读锁定超时
    if (readingLockTimer) {
      clearTimeout(readingLockTimer)
    }
    
    readingLockTimer = setTimeout(() => {
      // 如果仍然不在底部，保持锁定
      if (!checkIsAtBottom()) {
        // 继续锁定，等待用户主动滚动到底部
      } else {
        exitReadingMode()
      }
    }, opts.readingLockTimeout)
  }
  
  /**
   * 退出阅读模式
   */
  function exitReadingMode() {
    isUserReading.value = false
    autoScroll.value = true
    
    if (readingLockTimer) {
      clearTimeout(readingLockTimer)
      readingLockTimer = null
    }
  }
  
  /**
   * 通知有新内容到达
   */
  function notifyNewContent() {
    if (shouldAutoScroll.value) {
      // 自动滚动到底部
      requestAnimationFrame(() => {
        scrollToBottom(opts.mode === 'instant' ? 'auto' : 'smooth')
      })
    } else {
      // 标记有新内容
      hasNewContent.value = true
      newContentCount.value++
    }
  }
  
  /**
   * 强制滚动到底部（忽略阅读模式）
   */
  function forceScrollToBottom() {
    exitReadingMode()
    scrollToBottom()
  }
  
  /**
   * 暂停自动滚动
   */
  function pauseAutoScroll() {
    autoScroll.value = false
  }
  
  /**
   * 恢复自动滚动
   */
  function resumeAutoScroll() {
    autoScroll.value = true
  }
  
  /**
   * 锁定滚动（用户点击"固定视图"）
   */
  function lockScroll() {
    autoScroll.value = false
    isUserReading.value = true
    
    // 清除超时，保持锁定
    if (readingLockTimer) {
      clearTimeout(readingLockTimer)
      readingLockTimer = null
    }
  }
  
  /**
   * 解锁滚动
   */
  function unlockScroll() {
    exitReadingMode()
  }
  
  // === Lifecycle ===
  
  onMounted(() => {
    const el = containerRef.value
    if (el) {
      el.addEventListener('scroll', handleScroll, { passive: true })
      // 初始检查
      isAtBottom.value = checkIsAtBottom()
    }
  })
  
  onUnmounted(() => {
    const el = containerRef.value
    if (el) {
      el.removeEventListener('scroll', handleScroll)
    }
    
    if (readingLockTimer) {
      clearTimeout(readingLockTimer)
    }
    
    if (rapidClickTimer) {
      clearTimeout(rapidClickTimer)
    }
  })
  
  // 监听容器变化
  watch(containerRef, (newEl, oldEl) => {
    if (oldEl) {
      oldEl.removeEventListener('scroll', handleScroll)
    }
    if (newEl) {
      newEl.addEventListener('scroll', handleScroll, { passive: true })
      isAtBottom.value = checkIsAtBottom()
    }
  })
  
  return {
    // State
    autoScroll,
    isUserReading,
    isAtBottom,
    hasNewContent,
    newContentCount,
    
    // Computed
    shouldAutoScroll,
    showJumpToLatest,
    
    // Methods
    scrollToBottom,
    scrollToElement,
    notifyNewContent,
    forceScrollToBottom,
    pauseAutoScroll,
    resumeAutoScroll,
    lockScroll,
    unlockScroll,
    checkIsAtBottom
  }
}

export type UseScrollSyncReturn = ReturnType<typeof useScrollSync>
