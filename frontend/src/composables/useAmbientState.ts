/**
 * useAmbientState - Living Interface 状态管理
 * 
 * 根据 AI 执行状态返回相应的 CSS 类名，实现界面"呼吸感"
 */

import { computed, type ComputedRef } from 'vue'
import { useExecutionStore } from '@/stores/execution'

export type AmbientState = 'idle' | 'thinking' | 'executing' | 'waiting' | 'error' | 'completed'

export interface AmbientStateResult {
  /** 当前状态 */
  state: ComputedRef<AmbientState>
  /** CSS 类名对象 */
  ambientClass: ComputedRef<Record<string, boolean>>
  /** 边框动画类名 */
  borderClass: ComputedRef<string>
  /** 状态颜色 CSS 变量名 */
  stateColor: ComputedRef<string>
  /** 状态背景色 CSS 变量名 */
  stateBgColor: ComputedRef<string>
  /** 是否处于活跃状态 */
  isActive: ComputedRef<boolean>
}

export function useAmbientState(): AmbientStateResult {
  const executionStore = useExecutionStore()
  
  // 计算当前状态
  const state = computed<AmbientState>(() => {
    if (!executionStore.session) return 'idle'
    
    const status = executionStore.session.status
    
    // 检查是否有等待用户介入的请求 (HITL)
    if (executionStore.pendingHITL) {
      return 'waiting'
    }
    
    switch (status) {
      case 'running':
        // 检查是否在思考阶段 - manus 节点通常是思考/决策
        const activeNode = executionStore.nodes.find(n => n.status === 'active')
        if (activeNode?.type === 'manus') {
          return 'thinking'
        }
        return 'executing'
      case 'completed':
        return 'completed'
      case 'failed':
      case 'cancelled':
        return 'error'
      case 'pending':
        return 'idle'
      default:
        return 'idle'
    }
  })
  
  // CSS 类名对象
  const ambientClass = computed(() => ({
    'ambient-idle': state.value === 'idle',
    'ambient-thinking': state.value === 'thinking',
    'ambient-executing': state.value === 'executing',
    'ambient-waiting': state.value === 'waiting',
    'ambient-error': state.value === 'error',
    'ambient-completed': state.value === 'completed',
    'ambient-breathing': state.value === 'thinking',
    'ambient-pulsing': state.value === 'executing',
  }))
  
  // 边框动画类名
  const borderClass = computed(() => {
    switch (state.value) {
      case 'thinking':
        return 'state-border-thinking'
      case 'executing':
        return 'state-border-executing'
      case 'waiting':
        return 'state-border-waiting'
      default:
        return ''
    }
  })
  
  // 状态颜色 CSS 变量
  const stateColor = computed(() => {
    switch (state.value) {
      case 'thinking':
        return 'var(--td-state-thinking)'
      case 'executing':
        return 'var(--td-state-executing)'
      case 'waiting':
        return 'var(--td-state-waiting)'
      case 'error':
        return 'var(--td-state-error)'
      default:
        return 'var(--td-state-idle)'
    }
  })
  
  // 状态背景色 CSS 变量
  const stateBgColor = computed(() => {
    switch (state.value) {
      case 'thinking':
        return 'var(--td-state-thinking-bg)'
      case 'executing':
        return 'var(--td-state-executing-bg)'
      case 'waiting':
        return 'var(--td-state-waiting-bg)'
      case 'error':
        return 'var(--td-state-error-bg)'
      default:
        return 'transparent'
    }
  })
  
  // 是否活跃
  const isActive = computed(() => 
    ['thinking', 'executing', 'waiting'].includes(state.value)
  )
  
  return {
    state,
    ambientClass,
    borderClass,
    stateColor,
    stateBgColor,
    isActive
  }
}

/**
 * 独立的状态到样式映射函数
 * 用于不依赖 store 的场景
 */
export function getStateStyles(status: AmbientState) {
  const colorMap: Record<AmbientState, string> = {
    idle: 'var(--td-state-idle)',
    thinking: 'var(--td-state-thinking)',
    executing: 'var(--td-state-executing)',
    waiting: 'var(--td-state-waiting)',
    error: 'var(--td-state-error)',
    completed: 'var(--td-state-executing)'
  }
  
  const bgColorMap: Record<AmbientState, string> = {
    idle: 'transparent',
    thinking: 'var(--td-state-thinking-bg)',
    executing: 'var(--td-state-executing-bg)',
    waiting: 'var(--td-state-waiting-bg)',
    error: 'var(--td-state-error-bg)',
    completed: 'var(--td-state-executing-bg)'
  }
  
  const animationMap: Record<AmbientState, string> = {
    idle: '',
    thinking: 'ambient-breathing',
    executing: 'ambient-pulsing',
    waiting: 'ambient-breathing',
    error: '',
    completed: ''
  }
  
  return {
    color: colorMap[status],
    bgColor: bgColorMap[status],
    animation: animationMap[status]
  }
}
