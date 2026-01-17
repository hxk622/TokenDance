/**
 * 组件注册表
 * Component Registry for Dynamic Rendering Engine
 * 
 * 支持在 Markdown 中动态嵌入 Vue 组件
 */

import { markRaw, type Component } from 'vue'
import type { RegisteredComponent } from '../types'

// 全局组件注册表
const registry = new Map<string, RegisteredComponent>()

/**
 * 注册组件
 */
export function registerComponent(
  name: string,
  component: Component,
  options: Partial<Omit<RegisteredComponent, 'name' | 'component'>> = {}
): void {
  if (registry.has(name)) {
    console.warn(`[ComponentRegistry] Component "${name}" is already registered. Overwriting.`)
  }
  
  registry.set(name, {
    name,
    component: markRaw(component),
    category: options.category || 'custom',
    description: options.description,
  })
}

/**
 * 获取已注册组件
 */
export function getComponent(name: string): RegisteredComponent | undefined {
  return registry.get(name)
}

/**
 * 检查组件是否已注册
 */
export function hasComponent(name: string): boolean {
  return registry.has(name)
}

/**
 * 获取所有已注册组件
 */
export function getAllComponents(): Map<string, RegisteredComponent> {
  return new Map(registry)
}

/**
 * 获取特定类别的组件
 */
export function getComponentsByCategory(category: RegisteredComponent['category']): RegisteredComponent[] {
  return Array.from(registry.values()).filter(c => c.category === category)
}

/**
 * 注销组件
 */
export function unregisterComponent(name: string): boolean {
  return registry.delete(name)
}

/**
 * 清空注册表
 */
export function clearRegistry(): void {
  registry.clear()
}

/**
 * 批量注册组件
 */
export function registerComponents(
  components: Array<{
    name: string
    component: Component
    options?: Partial<Omit<RegisteredComponent, 'name' | 'component'>>
  }>
): void {
  for (const { name, component, options } of components) {
    registerComponent(name, component, options)
  }
}

// 默认导出
export default {
  register: registerComponent,
  get: getComponent,
  has: hasComponent,
  getAll: getAllComponents,
  getByCategory: getComponentsByCategory,
  unregister: unregisterComponent,
  clear: clearRegistry,
  registerBatch: registerComponents,
}
