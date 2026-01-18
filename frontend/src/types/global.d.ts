/// <reference types="node" />

/**
 * 全局类型定义
 * 用于解决 TypeScript 类型缺失问题
 */

// DOM API 类型
declare global {
  // Intersection Observer
  type IntersectionObserverInit = {
    root?: Element | null
    rootMargin?: string
    threshold?: number | number[]
  }

  // Scroll 相关类型
  type ScrollBehavior = 'auto' | 'smooth'
  type ScrollLogicalPosition = 'start' | 'center' | 'end' | 'nearest'

  interface ScrollIntoViewOptions {
    behavior?: ScrollBehavior
    block?: ScrollLogicalPosition
    inline?: ScrollLogicalPosition
  }

  // Fetch API
  type RequestInit = {
    method?: string
    headers?: HeadersInit
    body?: BodyInit | null
    mode?: RequestMode
    credentials?: RequestCredentials
    cache?: RequestCache
    redirect?: RequestRedirect
    referrer?: string
    referrerPolicy?: ReferrerPolicy
    integrity?: string
    keepalive?: boolean
    signal?: AbortSignal | null
  }
}

export {}
