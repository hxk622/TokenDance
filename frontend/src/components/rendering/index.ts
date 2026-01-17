/**
 * 下一代渲染引擎
 * Next-Gen Rendering Engine
 * 
 * 统一导出所有组件和工具函数
 */

// Types
export * from './types'

// Engine
export { default as ComponentRegistry, registerComponent, getComponent, hasComponent } from './engine/ComponentRegistry'
export { default as DynamicRenderer } from './engine/DynamicRenderer.vue'

// Charts
export { default as KLineChart } from './charts/KLineChart.vue'

// Widgets
export { default as MetricCard } from './widgets/MetricCard.vue'
export { default as ValuationTable } from './widgets/ValuationTable.vue'
export { default as SourceCitation } from './widgets/SourceCitation.vue'

// Scrollytelling
export { default as ScrollyContainer } from './scrolly/ScrollyContainer.vue'
export { default as ScrollySection } from './scrolly/ScrollySection.vue'
export { default as ScrollyProgress } from './scrolly/ScrollyProgress.vue'

// Component Registration Helper
import { registerComponent } from './engine/ComponentRegistry'
import KLineChart from './charts/KLineChart.vue'
import MetricCard from './widgets/MetricCard.vue'
import ValuationTable from './widgets/ValuationTable.vue'
import SourceCitation from './widgets/SourceCitation.vue'

/**
 * 注册所有内置组件到 ComponentRegistry
 * Register all built-in components to the registry
 */
export function registerBuiltInComponents(): void {
  registerComponent('KLineChart', KLineChart, { 
    category: 'chart', 
    description: '专业K线图表' 
  })
  
  registerComponent('MetricCard', MetricCard, { 
    category: 'widget', 
    description: '指标卡片' 
  })
  
  registerComponent('ValuationTable', ValuationTable, { 
    category: 'widget', 
    description: '估值表格' 
  })
  
  registerComponent('SourceCitation', SourceCitation, { 
    category: 'widget', 
    description: '来源引用' 
  })
}
