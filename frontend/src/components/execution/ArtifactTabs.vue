<template>
  <div class="artifact-tabs">
    <div 
      v-for="tab in tabs" 
      :key="tab.id"
      :class="['tab', { active: currentTab === tab.type }]"
      @click="selectTab(tab.type)"
    >
      <component
        :is="tab.icon"
        class="icon-svg"
      />
      <span class="title">{{ tab.title }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  DocumentTextIcon,
  PresentationChartBarIcon,
  DocumentDuplicateIcon,
  CircleStackIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'

export type TabType = 'report' | 'ppt' | 'file-diff' | 'timeline' | 'working-memory'

interface Props {
  sessionId: string
  currentTab: TabType
  taskType?: 'deep-research' | 'ppt-generation' | 'code-refactor' | 'file-operations' | 'default'
}

interface Emits {
  (e: 'update:currentTab', tab: TabType): void
  (e: 'tab-change', tab: TabType): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const allTabs = [
  // 实时进展 - 合并了时间轴和中间产出
  { id: '0', type: 'timeline' as const, title: '实时进展', icon: SparklesIcon, showFor: ['deep-research', 'ppt-generation', 'default'] },
  // 最终成果
  { id: '1', type: 'report' as const, title: '研究报告', icon: DocumentTextIcon, showFor: ['deep-research', 'default'] },
  { id: '2', type: 'ppt' as const, title: 'PPT', icon: PresentationChartBarIcon, showFor: ['ppt-generation', 'default'] },
  { id: '3', type: 'file-diff' as const, title: '文件变更', icon: DocumentDuplicateIcon, showFor: ['code-refactor', 'file-operations', 'default'] },
  // 工作记忆 - 统一使用中文
  { id: '4', type: 'working-memory' as const, title: '工作记忆', icon: CircleStackIcon, showFor: ['deep-research', 'ppt-generation', 'code-refactor', 'file-operations', 'default'] },
]

const tabs = computed(() => {
  const taskType = props.taskType || 'default'
  return allTabs.filter(tab => 
    tab.showFor.includes(taskType) || tab.showFor.includes('default')
  )
})

function selectTab(tab: TabType) {
  emit('update:currentTab', tab)
  emit('tab-change', tab)
}
</script>

<style scoped>
/* ArtifactTabs - 使用全局主题变量 */
.artifact-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--any-radius-md);
  background: transparent;
  color: var(--any-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
  border: 1px solid transparent;
}

.tab:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.tab.active {
  background: var(--td-state-thinking-bg);
  border-color: var(--td-state-thinking);
  color: var(--td-state-thinking);
}

.icon-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.title {
  font-weight: 500;
}
</style>
