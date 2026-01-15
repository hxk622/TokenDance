<template>
  <div class="artifact-tabs">
    <div 
      v-for="tab in tabs" 
      :key="tab.id"
      :class="['tab', { active: currentTab === tab.type }]"
      @click="selectTab(tab.type)"
    >
      <component :is="tab.icon" class="icon-svg" />
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
  ClockIcon,
} from '@heroicons/vue/24/outline'

export type TabType = 'report' | 'ppt' | 'file-diff' | 'timeline'

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
  { id: '1', type: 'timeline' as const, title: '研究时间轴', icon: ClockIcon, showFor: ['deep-research'] },
  { id: '2', type: 'report' as const, title: '研究报告', icon: DocumentTextIcon, showFor: ['deep-research', 'default'] },
  { id: '3', type: 'ppt' as const, title: 'PPT', icon: PresentationChartBarIcon, showFor: ['ppt-generation', 'default'] },
  { id: '4', type: 'file-diff' as const, title: '文件变更', icon: DocumentDuplicateIcon, showFor: ['code-refactor', 'file-operations', 'default'] },
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
.artifact-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--divider-color, rgba(255, 255, 255, 0.1));
  background: rgba(28, 28, 30, 0.7);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  font-size: 14px;
  cursor: pointer;
  transition: all 150ms ease-in-out;
  border: 1px solid transparent;
}

.tab:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #ffffff);
}

.tab.active {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
  color: #00D9FF;
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
