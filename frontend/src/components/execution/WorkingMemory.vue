<script setup lang="ts">
import { ref } from 'vue'

export interface WorkingMemoryFile {
  name: string
  title: string
  content: string
  icon: string
}

export interface WorkingMemoryProps {
  taskPlan?: string
  findings?: string
  progress?: string
}

const props = withDefaults(defineProps<WorkingMemoryProps>(), {
  taskPlan: '',
  findings: '',
  progress: '',
})

const files: WorkingMemoryFile[] = [
  {
    name: 'task_plan',
    title: 'Task Plan',
    content: props.taskPlan || 'No task plan available',
    icon: 'plan',
  },
  {
    name: 'findings',
    title: 'Findings',
    content: props.findings || 'No findings recorded yet',
    icon: 'findings',
  },
  {
    name: 'progress',
    title: 'Progress',
    content: props.progress || 'No progress recorded yet',
    icon: 'progress',
  },
]

const activeTab = ref('task_plan')

function setActiveTab(name: string) {
  activeTab.value = name
}

function getActiveFile() {
  return files.find(f => f.name === activeTab.value) || files[0]
}
</script>

<template>
  <div class="rounded-lg border border-border-default bg-bg-secondary overflow-hidden">
    <!-- Tab 头部 -->
    <div class="flex border-b border-border-default bg-bg-tertiary/30">
      <button
        v-for="file in files"
        :key="file.name"
        class="flex-1 px-4 py-3 text-sm font-medium transition-colors relative"
        :class="
          activeTab === file.name
            ? 'text-accent-primary bg-bg-secondary'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
        "
        @click="setActiveTab(file.name)"
      >
        <div class="flex items-center justify-center gap-2">
          <!-- Plan Icon -->
          <svg
            v-if="file.icon === 'plan'"
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
            />
          </svg>
          
          <!-- Findings Icon -->
          <svg
            v-else-if="file.icon === 'findings'"
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          
          <!-- Progress Icon -->
          <svg
            v-else
            class="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          
          <span>{{ file.title }}</span>
        </div>
        
        <!-- Active Indicator -->
        <div
          v-if="activeTab === file.name"
          class="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-primary"
        />
      </button>
    </div>
    
    <!-- Tab 内容 -->
    <div class="p-4">
      <div class="bg-bg-primary rounded-lg p-4 max-h-96 overflow-y-auto">
        <div class="prose prose-invert max-w-none">
          <pre class="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">{{ getActiveFile().content }}</pre>
        </div>
      </div>
      
      <!-- 文件元信息 -->
      <div class="mt-3 flex items-center justify-between text-xs text-text-tertiary">
        <span>{{ getActiveFile().name }}.md</span>
        <span>Manus Working Memory Pattern</span>
      </div>
    </div>
  </div>
</template>
