<template>
  <div class="preview-area">
    <!-- Timeline View (for Deep Research) -->
    <div
      v-if="currentTab === 'timeline'"
      class="timeline-container"
    >
      <ResearchTimeline
        :session-id="sessionId"
        :auto-refresh="isExecuting"
        :refresh-interval="3000"
        @entry-click="handleEntryClick"
        @screenshot-click="handleScreenshotClick"
      />
    </div>

    <!-- 实时进展 Tab - 中间产出 -->
    <div
      v-else-if="currentTab === 'live-progress'"
      class="live-progress-container"
    >
      <div class="live-progress-header">
        <SparklesIcon class="w-5 h-5" />
        <h3>实时进展</h3>
      </div>
      <div class="live-progress-list">
        <div 
          v-for="item in liveProgressItems" 
          :key="item.id" 
          class="progress-item"
          :class="`progress-item--${item.type}`"
        >
          <div class="progress-item-icon">
            <MagnifyingGlassIcon
              v-if="item.type === 'search'"
              class="w-4 h-4"
            />
            <GlobeAltIcon
              v-else-if="item.type === 'page'"
              class="w-4 h-4"
            />
            <DocumentTextIcon
              v-else
              class="w-4 h-4"
            />
          </div>
          <div class="progress-item-content">
            <span class="progress-item-title">{{ item.title }}</span>
            <span
              v-if="item.url"
              class="progress-item-url"
            >{{ item.url }}</span>
            <span
              v-else-if="item.subtitle"
              class="progress-item-subtitle"
            >{{ item.subtitle }}</span>
          </div>
        </div>
        <div
          v-if="liveProgressItems.length === 0"
          class="empty-state"
        >
          <SparklesIcon class="w-12 h-12" />
          <p>执行进展将实时显示在这里</p>
        </div>
      </div>
    </div>

    <!-- Working Memory Tab -->
    <div
      v-else-if="currentTab === 'working-memory'"
      class="working-memory-container"
    >
      <div
        v-if="isLoadingMemory"
        class="loading-state"
      >
        <div class="spinner" />
        <p>加载 Working Memory...</p>
      </div>
      <WorkingMemory
        v-else-if="workingMemoryData"
        :task-plan="workingMemoryData.task_plan.content"
        :findings="workingMemoryData.findings.content"
        :progress="workingMemoryData.progress.content"
      />
      <div
        v-else
        class="empty-state"
      >
        <CircleStackIcon class="w-12 h-12" />
        <p>暂无 Working Memory 数据</p>
        <button
          class="refresh-btn"
          @click="loadWorkingMemory"
        >
          刷新
        </button>
      </div>
    </div>

    <!-- Other tabs -->
    <div
      v-else
      class="preview-content"
    >
      <div
        v-if="currentTab === 'report'"
        class="preview-placeholder"
      >
        <DocumentTextIcon class="icon-svg" />
        <h3>研究报告预览</h3>
        <p>AI Deep Research 生成的研究报告将在这里显示</p>
      </div>

      <div
        v-else-if="currentTab === 'ppt'"
        class="preview-placeholder"
      >
        <PresentationChartBarIcon class="icon-svg" />
        <h3>PPT 预览</h3>
        <p>AI PPT Generation 生成的演示文稿将在这里显示</p>
      </div>

      <div
        v-else-if="currentTab === 'file-diff'"
        class="preview-placeholder"
      >
        <DocumentDuplicateIcon class="icon-svg" />
        <h3>文件变更预览</h3>
        <p>Coworker 修改的文件 Diff 将在这里显示</p>
        <div class="mock-diff">
          <div class="diff-line removed">
            - const oldValue = 'old'
          </div>
          <div class="diff-line added">
            + const newValue = 'new'
          </div>
        </div>
      </div>
    </div>

    <!-- Screenshot Lightbox -->
    <Teleport to="body">
      <div
        v-if="showScreenshotLightbox"
        class="screenshot-lightbox"
        @click="closeLightbox"
      >
        <div
          class="lightbox-content"
          @click.stop
        >
          <img
            :src="lightboxImageUrl"
            :alt="lightboxTitle"
          >
          <div class="lightbox-caption">
            <p class="lightbox-title">
              {{ lightboxTitle }}
            </p>
            <button
              class="lightbox-close"
              @click="closeLightbox"
            >
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import ResearchTimeline from './ResearchTimeline.vue'
import WorkingMemory from './WorkingMemory.vue'
import { timelineApi, type TimelineEntry } from '@/api/timeline'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'
import { useExecutionStore } from '@/stores/execution'
import {
  DocumentTextIcon,
  PresentationChartBarIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
  GlobeAltIcon,
  MagnifyingGlassIcon,
  CircleStackIcon,
  SparklesIcon,
} from '@heroicons/vue/24/outline'
import type { TabType } from './ArtifactTabs.vue'

interface Props {
  sessionId: string
  currentTab: TabType
  isExecuting?: boolean
}

const props = defineProps<Props>()
const executionStore = useExecutionStore()

// Working Memory 状态
const workingMemoryData = ref<WorkingMemoryResponse | null>(null)
const isLoadingMemory = ref(false)

// 实时进展数据 - 中间产出
const liveProgressItems = computed(() => {
  // 从执行日志中提取关键信息
  const items: Array<{
    id: string
    type: 'search' | 'page' | 'finding'
    title: string
    subtitle?: string
    url?: string
    timestamp: number
  }> = []
  
  executionStore.logs.forEach((log, index) => {
    if (log.type === 'tool-call' && log.content.includes('web_search')) {
      items.push({
        id: `search-${index}`,
        type: 'search',
        title: '正在搜索...',
        subtitle: log.content.slice(0, 100),
        timestamp: log.timestamp
      })
    } else if (log.type === 'result' && log.content.includes('http')) {
      const urlMatch = log.content.match(/https?:\/\/[^\s]+/)
      if (urlMatch) {
        items.push({
          id: `page-${index}`,
          type: 'page',
          title: '已访问网页',
          url: urlMatch[0],
          timestamp: log.timestamp
        })
      }
    }
  })
  
  return items.slice(-10) // 只显示最近 10 条
})

// 加载 Working Memory
async function loadWorkingMemory() {
  if (isLoadingMemory.value) return
  isLoadingMemory.value = true
  try {
    const data = await workingMemoryApi.get(props.sessionId)
    workingMemoryData.value = data
  } catch (error) {
    console.error('Failed to load working memory:', error)
  } finally {
    isLoadingMemory.value = false
  }
}

// 当切换到 Working Memory Tab 时加载数据
watch(() => props.currentTab, (tab) => {
  if (tab === 'working-memory' && !workingMemoryData.value) {
    loadWorkingMemory()
  }
})

onMounted(() => {
  if (props.currentTab === 'working-memory') {
    loadWorkingMemory()
  }
})

// Screenshot lightbox state
const showScreenshotLightbox = ref(false)
const lightboxImageUrl = ref('')
const lightboxTitle = ref('')

const handleEntryClick = (entry: TimelineEntry) => {
  console.log('Entry clicked:', entry)
  // Could navigate to URL or show more details
  if (entry.url) {
    window.open(entry.url, '_blank')
  }
}

const handleScreenshotClick = (index: number, entry: TimelineEntry) => {
  lightboxImageUrl.value = timelineApi.getScreenshotUrl(props.sessionId, index)
  lightboxTitle.value = entry.title
  showScreenshotLightbox.value = true
}

const closeLightbox = () => {
  showScreenshotLightbox.value = false
}
</script>

<style scoped>
.preview-area {
  flex: 1;
  overflow-y: auto;
  background: rgba(18, 18, 18, 0.9);
  display: flex;
  flex-direction: column;
}

.timeline-container {
  flex: 1;
  overflow: hidden;
}

.preview-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.preview-placeholder {
  text-align: center;
  max-width: 500px;
}

.icon-svg {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: var(--any-text-muted);
}

h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--any-text-primary);
}

p {
  font-size: 16px;
  line-height: 1.6;
  color: var(--any-text-secondary);
  margin: 0 0 24px 0;
}

.mock-diff {
  margin-top: 24px;
  text-align: left;
  background: var(--any-bg-tertiary);
  padding: 16px;
  border-radius: var(--any-radius-md);
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.diff-line {
  padding: 4px 8px;
  border-radius: var(--any-radius-sm);
}

.diff-line.removed {
  background: var(--td-state-error-bg);
  color: var(--td-state-error);
}

.diff-line.added {
  background: var(--td-state-executing-bg);
  color: var(--td-state-executing);
}

/* Live Progress 实时进展 */
.live-progress-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.live-progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
  color: var(--td-state-thinking);
}

.live-progress-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.live-progress-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.progress-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: var(--any-radius-md);
  background: var(--any-bg-hover);
  border-left: 3px solid transparent;
}

.progress-item--search {
  border-left-color: var(--td-state-waiting);
}

.progress-item--page {
  border-left-color: var(--td-state-thinking);
}

.progress-item--finding {
  border-left-color: var(--td-state-executing);
}

.progress-item-icon {
  flex-shrink: 0;
  color: var(--any-text-secondary);
}

.progress-item-content {
  flex: 1;
  min-width: 0;
}

.progress-item-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  margin-bottom: 4px;
}

.progress-item-url,
.progress-item-subtitle {
  display: block;
  font-size: 12px;
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Working Memory */
.working-memory-container {
  flex: 1;
  overflow: hidden;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--any-text-secondary);
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--any-border);
  border-top-color: var(--td-state-thinking);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.refresh-btn {
  margin-top: 16px;
  padding: 8px 16px;
  background: var(--td-state-thinking-bg);
  border: 1px solid var(--td-state-thinking);
  border-radius: var(--any-radius-md);
  color: var(--td-state-thinking);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.refresh-btn:hover {
  background: var(--td-state-thinking);
  color: var(--any-text-inverse);
}

/* Screenshot Lightbox */
.screenshot-lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.9);
  backdrop-filter: blur(8px);
}

.lightbox-content {
  max-width: 90vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.lightbox-content img {
  max-width: 100%;
  max-height: calc(90vh - 60px);
  object-fit: contain;
  border-radius: 8px;
}

.lightbox-caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
}

.lightbox-title {
  color: var(--text-primary, #ffffff);
  font-size: 14px;
  margin: 0;
}

.lightbox-close {
  padding: 8px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 8px;
  color: var(--text-primary, #ffffff);
  cursor: pointer;
  transition: background 150ms ease;
}

.lightbox-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Scrollbar */
.preview-area::-webkit-scrollbar {
  width: 8px;
}

.preview-area::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

.preview-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.preview-area::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>
