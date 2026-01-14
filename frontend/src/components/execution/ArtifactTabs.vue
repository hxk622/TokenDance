<template>
  <div class="artifact-tabs">
    <div 
      v-for="tab in tabs" 
      :key="tab.id"
      :class="['tab', { active: currentTab === tab.type }]"
      @click="selectTab(tab.type)"
    >
      <span class="icon">{{ tab.icon }}</span>
      <span class="title">{{ tab.title }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  sessionId: string
  currentTab: 'report' | 'ppt' | 'file-diff'
}

interface Emits {
  (e: 'update:currentTab', tab: 'report' | 'ppt' | 'file-diff'): void
  (e: 'tab-change', tab: 'report' | 'ppt' | 'file-diff'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const tabs = ref([
  { id: '1', type: 'report' as const, title: '研究报告', icon: '📄' },
  { id: '2', type: 'ppt' as const, title: 'PPT', icon: '📊' },
  { id: '3', type: 'file-diff' as const, title: '文件变更', icon: '📝' },
])

function selectTab(tab: 'report' | 'ppt' | 'file-diff') {
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

.icon {
  font-size: 16px;
}

.title {
  font-weight: 500;
}
</style>
