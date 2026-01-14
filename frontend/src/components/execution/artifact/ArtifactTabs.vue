<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  sessionId: string
  currentTab?: 'report' | 'ppt' | 'file-diff'
}

const props = withDefaults(defineProps<Props>(), {
  currentTab: 'report'
})

const emit = defineEmits<{
  (e: 'update:currentTab', value: 'report' | 'ppt' | 'file-diff'): void
  (e: 'tab-change', value: 'report' | 'ppt' | 'file-diff'): void
}>()

interface ArtifactTab {
  id: 'report' | 'ppt' | 'file-diff'
  type: 'report' | 'ppt' | 'file-diff'
  title: string
  icon: string
  isPinned?: boolean
}

const tabs = ref<ArtifactTab[]>([
  { id: 'report', type: 'report', title: '研究报告', icon: '📄' },
  { id: 'ppt', type: 'ppt', title: 'PPT', icon: '📊' },
  { id: 'file-diff', type: 'file-diff', title: '文件变更', icon: '🧩' },
])

const current = computed({
  get: () => props.currentTab,
  set: (v: 'report' | 'ppt' | 'file-diff') => emit('update:currentTab', v)
})

function switchTab(id: 'report' | 'ppt' | 'file-diff') {
  if (current.value !== id) {
    current.value = id
    emit('tab-change', id)
  }
}

function togglePin(id: ArtifactTab['id']) {
  const t = tabs.value.find(t => t.id === id)
  if (t) t.isPinned = !t.isPinned
}
</script>

<template>
  <div class="artifact-tabs">
    <div
      v-for="tab in tabs"
      :key="tab.id"
      :class="['tab', { active: current === tab.id, pinned: tab.isPinned }]"
      @click="switchTab(tab.id)"
      @contextmenu.prevent="togglePin(tab.id)"
    >
      <span class="icon">{{ tab.icon }}</span>
      <span class="title">{{ tab.title }}</span>
      <span v-if="tab.isPinned" class="pin">📌</span>
    </div>
  </div>
</template>

<style scoped>
.artifact-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 12px 0 12px;
  border-bottom: 1px solid var(--divider-color);
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(28, 28, 30, 0.8);
  border: 1px solid var(--divider-color);
  border-radius: 6px 6px 0 0;
  cursor: pointer;
  color: var(--text-secondary);
}

.tab.active {
  background: rgba(0, 217, 255, 0.2);
  border-color: var(--color-node-active);
  color: var(--color-node-active);
}

.pin {
  margin-left: 4px;
}

:root {
  --divider-color: rgba(255, 255, 255, 0.1);
  --color-node-active: #00D9FF;
  --text-secondary: rgba(255, 255, 255, 0.6);
}
</style>
