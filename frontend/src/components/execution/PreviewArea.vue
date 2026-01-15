<template>
  <div class="preview-area">
    <!-- Timeline View (for Deep Research) -->
    <div v-if="currentTab === 'timeline'" class="timeline-container">
      <ResearchTimeline
        :session-id="sessionId"
        :auto-refresh="isExecuting"
        :refresh-interval="3000"
        @entry-click="handleEntryClick"
        @screenshot-click="handleScreenshotClick"
      />
    </div>

    <!-- Other tabs -->
    <div v-else class="preview-content">
      <div v-if="currentTab === 'report'" class="preview-placeholder">
        <DocumentTextIcon class="icon-svg" />
        <h3>研究报告预览</h3>
        <p>AI Deep Research 生成的研究报告将在这里显示</p>
      </div>

      <div v-else-if="currentTab === 'ppt'" class="preview-placeholder">
        <PresentationChartBarIcon class="icon-svg" />
        <h3>PPT 预览</h3>
        <p>AI PPT Generation 生成的演示文稿将在这里显示</p>
      </div>

      <div v-else-if="currentTab === 'file-diff'" class="preview-placeholder">
        <DocumentDuplicateIcon class="icon-svg" />
        <h3>文件变更预览</h3>
        <p>Coworker 修改的文件 Diff 将在这里显示</p>
        <div class="mock-diff">
          <div class="diff-line removed">- const oldValue = 'old'</div>
          <div class="diff-line added">+ const newValue = 'new'</div>
        </div>
      </div>
    </div>

    <!-- Screenshot Lightbox -->
    <Teleport to="body">
      <div v-if="showScreenshotLightbox" class="screenshot-lightbox" @click="closeLightbox">
        <div class="lightbox-content" @click.stop>
          <img :src="lightboxImageUrl" :alt="lightboxTitle" />
          <div class="lightbox-caption">
            <p class="lightbox-title">{{ lightboxTitle }}</p>
            <button class="lightbox-close" @click="closeLightbox">
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ResearchTimeline from './ResearchTimeline.vue'
import { timelineApi, type TimelineEntry } from '@/api/timeline'
import {
  DocumentTextIcon,
  PresentationChartBarIcon,
  DocumentDuplicateIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import type { TabType } from './ArtifactTabs.vue'

interface Props {
  sessionId: string
  currentTab: TabType
  isExecuting?: boolean
}

const props = defineProps<Props>()

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
  color: var(--text-secondary, rgba(255, 255, 255, 0.4));
}

h3 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 12px 0;
  color: var(--text-primary, #ffffff);
}

p {
  font-size: 16px;
  line-height: 1.6;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  margin: 0 0 24px 0;
}

.mock-diff {
  margin-top: 24px;
  text-align: left;
  background: rgba(0, 0, 0, 0.4);
  padding: 16px;
  border-radius: 8px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
}

.diff-line {
  padding: 4px 8px;
  border-radius: 4px;
}

.diff-line.removed {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

.diff-line.added {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
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
