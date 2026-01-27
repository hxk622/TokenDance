<script setup lang="ts">
/**
 * InteractiveReportViewer - 可交互报告查看器
 * 
 * 支持:
 * - 章节局部修订
 * - 版本切换
 * - 修订历史
 */
import { ref, computed, watch } from 'vue'
import { sanitizeHtml } from '@/utils/sanitize'
import {
  FileText,
  ZoomIn,
  Minimize2,
  FilePlus,
  Edit3,
  Clock,
  ChevronDown,
  ChevronRight,
  Check,
  X,
  RotateCcw,
  Loader,
  BookOpen,
  ExternalLink,
} from 'lucide-vue-next'

// Types
interface ReportSection {
  id: string
  type: string
  title: string
  content: string
  sources: string[]
  version: number
}

interface ReportVersion {
  version: number
  sections: ReportSection[]
  created_at: string
  revision_note?: string
}

interface InteractiveReport {
  id: string
  session_id: string
  title: string
  query: string
  current_version: number
  versions: ReportVersion[]
}

interface QuickAction {
  id: string
  label: string
  icon: string
  revision_type: string
}

// Props
const props = withDefaults(defineProps<{
  report: InteractiveReport | null
  loading?: boolean
}>(), {
  loading: false,
})

// Emits
const emit = defineEmits<{
  (e: 'revise', sectionId: string, revisionType: string, instruction?: string): void
  (e: 'rollback', version: number): void
  (e: 'export'): void
}>()

// State
const selectedSectionId = ref<string | null>(null)
const showVersionHistory = ref(false)
const revisionInstruction = ref('')
const isRevising = ref(false)
const expandedSections = ref<Set<string>>(new Set())

// Quick actions mapping
const QUICK_ACTIONS: QuickAction[] = [
  { id: 'expand', label: '深入展开', icon: 'zoom-in', revision_type: 'expand' },
  { id: 'simplify', label: '简化说明', icon: 'minimize', revision_type: 'simplify' },
  { id: 'evidence', label: '增加论据', icon: 'file-plus', revision_type: 'evidence' },
  { id: 'rewrite', label: '重写段落', icon: 'edit', revision_type: 'rewrite' },
]

// Computed
const currentVersion = computed(() => {
  if (!props.report?.versions?.length) return null
  return props.report.versions[props.report.versions.length - 1]
})

const sections = computed(() => currentVersion.value?.sections || [])

const selectedSection = computed(() => {
  if (!selectedSectionId.value) return null
  return sections.value.find(s => s.id === selectedSectionId.value)
})

const versionList = computed(() => {
  return props.report?.versions?.slice().reverse() || []
})

// Methods
const selectSection = (sectionId: string) => {
  if (selectedSectionId.value === sectionId) {
    selectedSectionId.value = null
  } else {
    selectedSectionId.value = sectionId
  }
}

const toggleSectionExpand = (sectionId: string) => {
  if (expandedSections.value.has(sectionId)) {
    expandedSections.value.delete(sectionId)
  } else {
    expandedSections.value.add(sectionId)
  }
}

const handleQuickAction = async (action: QuickAction) => {
  if (!selectedSectionId.value) return
  
  isRevising.value = true
  emit('revise', selectedSectionId.value, action.revision_type, revisionInstruction.value || undefined)
  
  // 模拟延迟
  setTimeout(() => {
    isRevising.value = false
    revisionInstruction.value = ''
  }, 2000)
}

const handleRollback = (version: number) => {
  emit('rollback', version)
  showVersionHistory.value = false
}

const getActionIcon = (iconName: string) => {
  const icons: Record<string, any> = {
    'zoom-in': ZoomIn,
    'minimize': Minimize2,
    'file-plus': FilePlus,
    'edit': Edit3,
  }
  return icons[iconName] || FileText
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getSectionContent = (content: string) => sanitizeHtml(content || '')
</script>

<template>
  <div class="interactive-report">
    <!-- Header -->
    <div class="report-header">
      <div class="header-info">
        <FileText class="w-5 h-5 text-[var(--exec-accent)]" />
        <div class="header-text">
          <h2 class="report-title">
            {{ report?.title || '研究报告' }}
          </h2>
          <span class="version-badge">v{{ report?.current_version || 1 }}</span>
        </div>
      </div>
      
      <div class="header-actions">
        <button 
          class="history-btn"
          @click="showVersionHistory = !showVersionHistory"
        >
          <Clock class="w-4 h-4" />
          历史版本
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <Loader class="w-6 h-6 animate-spin" />
      <span>加载中...</span>
    </div>

    <!-- Content -->
    <div
      v-else
      class="report-content"
    >
      <!-- Sections -->
      <div class="sections-container">
        <div
          v-for="section in sections"
          :key="section.id"
          class="section-card"
          :class="{ 
            'section-card--selected': selectedSectionId === section.id,
            'section-card--expanded': expandedSections.has(section.id),
          }"
        >
          <!-- Section Header -->
          <div 
            class="section-header"
            @click="selectSection(section.id)"
          >
            <button 
              class="expand-btn"
              @click.stop="toggleSectionExpand(section.id)"
            >
              <component 
                :is="expandedSections.has(section.id) ? ChevronDown : ChevronRight"
                class="w-4 h-4"
              />
            </button>
            <span class="section-type">{{ section.type }}</span>
            <h3 class="section-title">
              {{ section.title }}
            </h3>
            <span class="section-version">v{{ section.version }}</span>
          </div>

          <!-- Section Content -->
          <div 
            v-show="expandedSections.has(section.id)"
            class="section-content"
          >
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div
              class="content-text"
              v-html="getSectionContent(section.content)"
            />
            
            <!-- Sources -->
            <div
              v-if="section.sources?.length"
              class="section-sources"
            >
              <span class="sources-label">来源</span>
              <div class="sources-list">
                <a 
                  v-for="(source, idx) in section.sources"
                  :key="idx"
                  :href="source"
                  target="_blank"
                  class="source-link"
                >
                  <BookOpen class="w-3 h-3" />
                  {{ source }}
                  <ExternalLink class="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>

          <!-- Quick Actions (when selected) -->
          <Transition name="slide">
            <div 
              v-if="selectedSectionId === section.id"
              class="section-actions"
            >
              <div class="action-buttons">
                <button
                  v-for="action in QUICK_ACTIONS"
                  :key="action.id"
                  class="action-btn"
                  :disabled="isRevising"
                  @click="handleQuickAction(action)"
                >
                  <component
                    :is="getActionIcon(action.icon)"
                    class="w-4 h-4"
                  />
                  {{ action.label }}
                </button>
              </div>
              
              <!-- Custom Instruction -->
              <div class="custom-instruction">
                <input
                  v-model="revisionInstruction"
                  type="text"
                  placeholder="自定义修订指令（可选）"
                  class="instruction-input"
                  :disabled="isRevising"
                  @keyup.enter="handleQuickAction(QUICK_ACTIONS[3])"
                >
              </div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- Version History Panel -->
      <Transition name="slide-panel">
        <div
          v-if="showVersionHistory"
          class="version-panel"
        >
          <div class="panel-header">
            <span>版本历史</span>
            <button @click="showVersionHistory = false">
              <X class="w-4 h-4" />
            </button>
          </div>
          <div class="version-list">
            <div
              v-for="version in versionList"
              :key="version.version"
              class="version-item"
              :class="{ 'version-item--current': version.version === report?.current_version }"
            >
              <div class="version-info">
                <span class="version-number">v{{ version.version }}</span>
                <span class="version-time">{{ formatDate(version.created_at) }}</span>
              </div>
              <span class="version-note">{{ version.revision_note || '版本更新' }}</span>
              <button
                v-if="version.version !== report?.current_version"
                class="rollback-btn"
                @click="handleRollback(version.version)"
              >
                <RotateCcw class="w-3.5 h-3.5" />
                恢复
              </button>
              <span 
                v-else 
                class="current-badge"
              >
                <Check class="w-3 h-3" />
                当前
              </span>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Revision Loading Overlay -->
    <Transition name="fade">
      <div
        v-if="isRevising"
        class="revision-overlay"
      >
        <Loader class="w-6 h-6 animate-spin" />
        <span>正在修订...</span>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.interactive-report {
  position: relative;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.report-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.version-badge {
  padding: 2px 8px;
  background: var(--exec-accent);
  color: var(--any-bg-primary);
  border-radius: var(--any-radius-full);
  font-size: 11px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.history-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 13px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.history-btn:hover {
  border-color: var(--any-border-hover);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 48px;
  color: var(--any-text-muted);
}

.report-content {
  position: relative;
  padding: 16px;
}

.sections-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  overflow: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.section-card:hover {
  border-color: var(--any-border-hover);
}

.section-card--selected {
  border-color: var(--exec-accent);
  box-shadow: 0 0 0 1px var(--exec-accent);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  cursor: pointer;
}

.expand-btn {
  display: flex;
  padding: 4px;
  color: var(--any-text-muted);
  cursor: pointer;
}

.expand-btn:hover {
  color: var(--any-text-primary);
}

.section-type {
  padding: 2px 6px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  font-size: 10px;
  text-transform: uppercase;
  color: var(--any-text-muted);
}

.section-title {
  flex: 1;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  margin: 0;
}

.section-version {
  font-size: 11px;
  color: var(--any-text-muted);
}

.section-content {
  padding: 0 12px 12px;
}

.content-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--any-text-secondary);
}

.section-sources {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--any-border);
}

.sources-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--any-text-muted);
  text-transform: uppercase;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 8px;
}

.source-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-muted);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-link:hover {
  color: var(--exec-accent);
}

.section-actions {
  padding: 12px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-tertiary);
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 12px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--exec-accent);
  color: var(--exec-accent);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.custom-instruction {
  margin-top: 12px;
}

.instruction-input {
  width: 100%;
  padding: 8px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 13px;
  color: var(--any-text-primary);
  outline: none;
}

.instruction-input:focus {
  border-color: var(--exec-accent);
}

.instruction-input:disabled {
  opacity: 0.5;
}

/* Version Panel */
.version-panel {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 280px;
  background: var(--any-bg-primary);
  border-left: 1px solid var(--any-border);
  box-shadow: var(--any-shadow-lg);
  z-index: 10;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.panel-header button {
  display: flex;
  padding: 4px;
  color: var(--any-text-muted);
  cursor: pointer;
}

.panel-header button:hover {
  color: var(--any-text-primary);
}

.version-list {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: calc(100% - 50px);
  overflow-y: auto;
}

.version-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
}

.version-item--current {
  border-color: var(--exec-accent);
}

.version-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.version-number {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.version-time {
  font-size: 11px;
  color: var(--any-text-muted);
}

.version-note {
  font-size: 12px;
  color: var(--any-text-secondary);
}

.rollback-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 8px;
  margin-top: 4px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 11px;
  color: var(--any-text-secondary);
  cursor: pointer;
}

.rollback-btn:hover {
  border-color: var(--exec-accent);
  color: var(--exec-accent);
}

.current-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 8px;
  margin-top: 4px;
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-radius: var(--any-radius-sm);
  font-size: 11px;
  color: var(--exec-accent);
}

/* Revision Overlay */
.revision-overlay {
  position: absolute;
  inset: 0;
  background: rgba(var(--any-bg-primary-rgb), 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--any-text-secondary);
  backdrop-filter: blur(4px);
  z-index: 20;
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.25s ease;
}

.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
