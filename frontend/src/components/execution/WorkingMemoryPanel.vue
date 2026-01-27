<template>
  <div class="working-memory-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        Working Memory
      </h3>
      <button 
        :disabled="loading" 
        class="refresh-btn"
        @click="refreshMemory"
      >
        <span v-if="loading">Refreshing...</span>
        <span v-else>Refresh</span>
      </button>
    </div>

    <div
      v-if="error"
      class="error-message"
    >
      {{ error }}
    </div>

    <div class="tabs">
      <button
        v-for="file in files"
        :key="file.key"
        :class="['tab', { active: activeTab === file.key }]"
        @click="activeTab = file.key"
      >
        {{ file.label }}
      </button>
    </div>

    <div class="tab-content">
      <div
        v-if="loading && !memory"
        class="loading-state"
      >
        Loading working memory...
      </div>
      
      <div
        v-else-if="memory"
        class="file-content"
      >
        <!-- Task Plan -->
        <div
          v-if="activeTab === 'task_plan'"
          class="memory-file"
        >
          <div class="file-header">
            <h4>{{ files[0].label }}</h4>
            <span class="file-description">{{ files[0].description }}</span>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            class="markdown-content"
            v-html="renderSafeMarkdown(memory.task_plan.content)"
          />
        </div>

        <!-- Findings -->
        <div
          v-if="activeTab === 'findings'"
          class="memory-file"
        >
          <div class="file-header">
            <h4>{{ files[1].label }}</h4>
            <span class="file-description">{{ files[1].description }}</span>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            class="markdown-content"
            v-html="renderSafeMarkdown(memory.findings.content)"
          />
        </div>

        <!-- Progress -->
        <div
          v-if="activeTab === 'progress'"
          class="memory-file"
        >
          <div class="file-header">
            <h4>{{ files[2].label }}</h4>
            <span class="file-description">{{ files[2].description }}</span>
          </div>
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div
            class="markdown-content"
            v-html="renderSafeMarkdown(memory.progress.content)"
          />
        </div>
      </div>

      <div
        v-else
        class="empty-state"
      >
        No working memory available yet.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { renderMarkdown } from '@/utils/sanitize'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'

const props = defineProps<{
  sessionId: string
}>()

const activeTab = ref<'task_plan' | 'findings' | 'progress'>('task_plan' as const)
const memory = ref<WorkingMemoryResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

type TabKey = 'task_plan' | 'findings' | 'progress'

const files: { key: TabKey; label: string; description: string }[] = [
  {
    key: 'task_plan',
    label: 'Task Plan',
    description: 'Task roadmap and objectives'
  },
  {
    key: 'findings',
    label: 'Findings',
    description: 'Research findings and technical decisions'
  },
  {
    key: 'progress',
    label: 'Progress',
    description: 'Execution logs and error tracking'
  }
]

const renderSafeMarkdown = (content: string): string => {
  if (!content || content.trim() === '') {
    return '<p class="empty-content">No content yet.</p>'
  }
  return renderMarkdown(content)
}

const fetchMemory = async () => {
  loading.value = true
  error.value = null
  
  try {
    memory.value = await workingMemoryApi.get(props.sessionId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load working memory'
    console.error('Error fetching working memory:', err)
  } finally {
    loading.value = false
  }
}

const refreshMemory = async () => {
  await fetchMemory()
}

onMounted(() => {
  fetchMemory()
})

// Auto-refresh every 10 seconds
setInterval(() => {
  if (!loading.value && props.sessionId) {
    fetchMemory()
  }
}, 10000)
</script>

<style scoped>
/* Working Memory Panel - 使用全局主题变量 */
.working-memory-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.refresh-btn {
  padding: 6px 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--td-state-thinking);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-normal) var(--any-ease-out);
}

.refresh-btn:hover:not(:disabled) {
  background: var(--any-bg-tertiary);
  border-color: var(--td-state-thinking);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  padding: 12px 20px;
  background: var(--td-state-error-bg);
  color: var(--td-state-error);
  font-size: 14px;
  border-bottom: 1px solid var(--td-state-error);
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 8px 20px 0;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.tab {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-tertiary);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.tab:hover {
  color: var(--any-text-primary);
}

.tab.active {
  color: var(--td-state-thinking);
  border-bottom-color: var(--td-state-thinking);
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--any-text-tertiary);
  font-size: 14px;
}

.memory-file {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.file-header h4 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.file-description {
  display: block;
  margin-top: 4px;
  font-size: 14px;
  color: var(--any-text-tertiary);
}

.markdown-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--any-text-secondary);
}

.markdown-content :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 24px 0 16px;
  color: var(--any-text-primary);
}

.markdown-content :deep(h2) {
  font-size: 20px;
  font-weight: 600;
  margin: 20px 0 12px;
  color: var(--any-text-primary);
}

.markdown-content :deep(h3) {
  font-size: 16px;
  font-weight: 600;
  margin: 16px 0 8px;
  color: var(--any-text-primary);
}

.markdown-content :deep(p) {
  margin: 8px 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
}

.markdown-content :deep(code) {
  padding: 2px 6px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  color: var(--any-text-primary);
}

.markdown-content :deep(pre) {
  padding: 12px;
  background: var(--any-bg-tertiary);
  border-radius: 6px;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #e5e7eb;
}

.empty-content {
  color: #9ca3af;
  font-style: italic;
}
</style>
