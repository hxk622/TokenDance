<template>
  <div class="preview-area">
    <!-- Working Memory Tab -->
    <div
      v-if="currentTab === 'working-memory'"
      class="working-memory-container"
    >
      <div
        v-if="isLoadingMemory"
        class="loading-state"
      >
        <div class="spinner" />
        <p>加载工作记忆...</p>
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
        <p>暂无工作记忆数据</p>
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
      <!-- 报告 Tab -->
      <div
        v-if="currentTab === 'report'"
        class="report-container"
      >
        <!-- 有报告内容时显示引用渲染器 -->
        <div
          v-if="reportContent"
          class="report-content"
        >
          <CitationRenderer
            :content="reportContent"
            :citations="citations"
            :is-html="isReportHtml"
            @open-url="handleOpenCitationUrl"
            @copy-citation="handleCopyCitation"
          />
        </div>
        
        <!-- 无报告内容时显示占位符 -->
        <div
          v-else
          class="preview-placeholder"
        >
          <div class="empty-icon-wrapper">
            <DocumentTextIcon class="icon-svg" />
          </div>
          <h3>研究报告生成中</h3>
          <p v-if="isExecuting">
            AI 正在深度调研并撰写报告,请稍候...
          </p>
          <p v-else>
            任务完成后,研究报告将在这里显示
          </p>
          <div
            v-if="isExecuting"
            class="progress-dots"
          >
            <span class="dot" />
            <span class="dot" />
            <span class="dot" />
          </div>
        </div>
      </div>

      <div
        v-else-if="currentTab === 'ppt'"
        class="preview-placeholder"
      >
        <div class="empty-icon-wrapper">
          <PresentationChartBarIcon class="icon-svg" />
        </div>
        <h3>PPT 生成中</h3>
        <p v-if="isExecuting">
          AI 正在设计演示文稿,请稍候...
        </p>
        <p v-else>
          任务完成后,演示文稿将在这里显示
        </p>
        <div
          v-if="isExecuting"
          class="progress-dots"
        >
          <span class="dot" />
          <span class="dot" />
          <span class="dot" />
        </div>
      </div>

      <div
        v-else-if="currentTab === 'file-diff'"
        class="preview-placeholder"
      >
        <div class="empty-icon-wrapper">
          <DocumentDuplicateIcon class="icon-svg" />
        </div>
        <h3>文件变更</h3>
        <p v-if="isExecuting">
          Coworker 正在修改文件,变更将实时显示...
        </p>
        <p v-else>
          暂无文件变更记录
        </p>
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
import { ref, onMounted, watch } from 'vue'
import WorkingMemory from './WorkingMemory.vue'
import { CitationRenderer } from './research'
import type { Citation, ReportWithCitations } from './research/types'
import { workingMemoryApi, type WorkingMemoryResponse } from '@/api/working-memory'
import {
  DocumentTextIcon,
  PresentationChartBarIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
  CircleStackIcon,
} from '@heroicons/vue/24/outline'
import type { TabType } from './ArtifactTabs.vue'

interface Props {
  sessionId: string
  currentTab: TabType
  isExecuting?: boolean
  /** 报告内容 (带引用标记的 Markdown/HTML) */
  reportContent?: string
  /** 引用列表 */
  citations?: Citation[]
  /** 报告内容是否为 HTML */
  isReportHtml?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  reportContent: '',
  citations: () => [],
  isReportHtml: true,
})

// Working Memory 状态
const workingMemoryData = ref<WorkingMemoryResponse | null>(null)
const isLoadingMemory = ref(false)

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

// Screenshot lightbox state (保留用于其他用途)
const showScreenshotLightbox = ref(false)
const lightboxImageUrl = ref('')
const lightboxTitle = ref('')

const closeLightbox = () => {
  showScreenshotLightbox.value = false
}

// 引用链接处理
function handleOpenCitationUrl(url: string) {
  window.open(url, '_blank', 'noopener,noreferrer')
}

function handleCopyCitation(citation: Citation) {
  console.log('Citation copied:', citation)
  // TODO: 显示 Toast 提示
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

.empty-icon-wrapper {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-hover);
  border-radius: var(--any-radius-xl);
  border: 1px solid var(--any-border);
}

.icon-svg {
  width: 40px;
  height: 40px;
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

/* Progress dots animation */
.progress-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
}

.progress-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--td-state-thinking);
  animation: dot-pulse 1.4s ease-in-out infinite;
}

.progress-dots .dot:nth-child(1) {
  animation-delay: 0s;
}

.progress-dots .dot:nth-child(2) {
  animation-delay: 0.2s;
}

.progress-dots .dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes dot-pulse {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1.2);
  }
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

/* Report Container */
.report-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px 48px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
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
