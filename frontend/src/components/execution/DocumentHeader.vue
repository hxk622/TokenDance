<script setup lang="ts">
/**
 * DocumentHeader - AnyGen 风格的文档工具栏
 * 
 * 功能:
 * - 可编辑的文档标题
 * - 版本历史下拉
 * - Create 下拉菜单 (导出为 PPT/Word 等)
 * - 分享/下载按钮
 */
import { ref, computed, watch } from 'vue'
import {
  ChevronDown,
  History,
  Download,
  Share2,
  FileText,
  Presentation,
  FileSpreadsheet,
  Maximize2,
  Copy,
  Check
} from 'lucide-vue-next'

interface Props {
  /** 文档标题 */
  title: string
  /** 是否已保存 */
  isSaved?: boolean
  /** 是否显示版本历史 */
  showVersionHistory?: boolean
  /** 是否正在执行 (流式输出中) */
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isSaved: true,
  showVersionHistory: false,
  isStreaming: false
})

const emit = defineEmits<{
  'update:title': [value: string]
  'download': [format: 'pdf' | 'docx' | 'md']
  'share': []
  'create': [type: 'ppt' | 'doc' | 'spreadsheet']
  'fullscreen': []
  'version-select': [versionId: string]
}>()

// Title editing state
const isEditingTitle = ref(false)
const editedTitle = ref(props.title)
const titleInputRef = ref<HTMLInputElement | null>(null)

// Dropdown states
const showVersionDropdown = ref(false)
const showCreateDropdown = ref(false)
const showDownloadDropdown = ref(false)

// Copy state
const isCopied = ref(false)

// Sync title
watch(() => props.title, (newTitle) => {
  if (!isEditingTitle.value) {
    editedTitle.value = newTitle
  }
})

// Title editing handlers
function startEditTitle() {
  if (props.isStreaming) return
  isEditingTitle.value = true
  editedTitle.value = props.title
  setTimeout(() => {
    titleInputRef.value?.focus()
    titleInputRef.value?.select()
  }, 10)
}

function saveTitle() {
  isEditingTitle.value = false
  if (editedTitle.value.trim() && editedTitle.value !== props.title) {
    emit('update:title', editedTitle.value.trim())
  } else {
    editedTitle.value = props.title
  }
}

function cancelEdit() {
  isEditingTitle.value = false
  editedTitle.value = props.title
}

function handleTitleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    saveTitle()
  } else if (e.key === 'Escape') {
    cancelEdit()
  }
}

// Action handlers
function handleDownload(format: 'pdf' | 'docx' | 'md') {
  emit('download', format)
  showDownloadDropdown.value = false
}

function handleCreate(type: 'ppt' | 'doc' | 'spreadsheet') {
  emit('create', type)
  showCreateDropdown.value = false
}

function handleShare() {
  emit('share')
}

function handleFullscreen() {
  emit('fullscreen')
}

async function handleCopyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// Close dropdowns when clicking outside
function closeDropdowns() {
  showVersionDropdown.value = false
  showCreateDropdown.value = false
  showDownloadDropdown.value = false
}
</script>

<template>
  <div
    class="document-header"
    @click="closeDropdowns"
  >
    <!-- Left: Title and status -->
    <div class="header-left">
      <!-- Editable Title -->
      <div class="title-container">
        <input
          v-if="isEditingTitle"
          ref="titleInputRef"
          v-model="editedTitle"
          class="title-input"
          maxlength="255"
          @blur="saveTitle"
          @keydown="handleTitleKeydown"
          @click.stop
        >
        <h1
          v-else
          class="title-display"
          :class="{ 'clickable': !isStreaming }"
          :title="title"
          @click="startEditTitle"
        >
          {{ title || '未命名文档' }}
        </h1>
      </div>

      <!-- Save status -->
      <div class="status-badge">
        <span
          v-if="isStreaming"
          class="status streaming"
        >
          <span class="dot" />
          生成中...
        </span>
        <span
          v-else-if="isSaved"
          class="status saved"
        >
          <Check class="w-3 h-3" />
          已保存
        </span>
        <span
          v-else
          class="status unsaved"
        >
          未保存
        </span>
      </div>
    </div>

    <!-- Right: Actions -->
    <div class="header-right">
      <!-- Version History (optional) -->
      <div
        v-if="showVersionHistory"
        class="dropdown-wrapper"
      >
        <button
          class="header-btn secondary"
          :class="{ active: showVersionDropdown }"
          @click.stop="showVersionDropdown = !showVersionDropdown"
        >
          <History class="w-4 h-4" />
          <span>版本历史</span>
          <ChevronDown class="w-4 h-4 chevron" />
        </button>
        <Transition name="dropdown">
          <div
            v-if="showVersionDropdown"
            class="dropdown-menu"
            @click.stop
          >
            <div class="dropdown-item">
              <span>当前版本</span>
              <span class="version-time">刚刚</span>
            </div>
            <div class="dropdown-item">
              <span>版本 2</span>
              <span class="version-time">5分钟前</span>
            </div>
            <div class="dropdown-item">
              <span>版本 1</span>
              <span class="version-time">10分钟前</span>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Create Menu -->
      <div class="dropdown-wrapper">
        <button
          class="header-btn primary"
          :class="{ active: showCreateDropdown }"
          @click.stop="showCreateDropdown = !showCreateDropdown"
        >
          <span>Create</span>
          <ChevronDown class="w-4 h-4 chevron" />
        </button>
        <Transition name="dropdown">
          <div
            v-if="showCreateDropdown"
            class="dropdown-menu"
            @click.stop
          >
            <button
              class="dropdown-item"
              @click="handleCreate('ppt')"
            >
              <Presentation class="w-4 h-4" />
              <span>生成 PPT</span>
            </button>
            <button
              class="dropdown-item"
              @click="handleCreate('doc')"
            >
              <FileText class="w-4 h-4" />
              <span>导出 Word</span>
            </button>
            <button
              class="dropdown-item"
              @click="handleCreate('spreadsheet')"
            >
              <FileSpreadsheet class="w-4 h-4" />
              <span>生成表格</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Share -->
      <button
        class="header-btn icon-only"
        title="分享"
        @click="handleShare"
      >
        <Share2 class="w-4 h-4" />
      </button>

      <!-- Download -->
      <div class="dropdown-wrapper">
        <button
          class="header-btn icon-only"
          :class="{ active: showDownloadDropdown }"
          title="下载"
          @click.stop="showDownloadDropdown = !showDownloadDropdown"
        >
          <Download class="w-4 h-4" />
        </button>
        <Transition name="dropdown">
          <div
            v-if="showDownloadDropdown"
            class="dropdown-menu right"
            @click.stop
          >
            <button
              class="dropdown-item"
              @click="handleDownload('pdf')"
            >
              <span>下载 PDF</span>
            </button>
            <button
              class="dropdown-item"
              @click="handleDownload('docx')"
            >
              <span>下载 Word</span>
            </button>
            <button
              class="dropdown-item"
              @click="handleDownload('md')"
            >
              <span>下载 Markdown</span>
            </button>
            <div class="dropdown-divider" />
            <button
              class="dropdown-item"
              @click="handleCopyLink"
            >
              <Copy class="w-4 h-4" />
              <span>{{ isCopied ? '已复制!' : '复制链接' }}</span>
            </button>
          </div>
        </Transition>
      </div>

      <!-- Fullscreen -->
      <button
        class="header-btn icon-only"
        title="全屏"
        @click="handleFullscreen"
      >
        <Maximize2 class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.document-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--any-bg-primary);
  border-bottom: 1px solid var(--any-border);
  min-height: 48px;
  gap: 16px;
}

/* Left section */
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.title-container {
  flex: 1;
  min-width: 0;
}

.title-display {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 24px;
}

.title-display.clickable {
  cursor: pointer;
  padding: 4px 8px;
  margin: -4px -8px;
  border-radius: var(--any-radius-sm);
  transition: background var(--any-duration-fast) var(--any-ease-default);
}

.title-display.clickable:hover {
  background: var(--any-bg-hover);
}

.title-input {
  width: 100%;
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  padding: 4px 8px;
  outline: none;
  line-height: 24px;
}

.title-input:focus {
  border-color: var(--td-state-thinking);
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.2);
}

/* Status badge */
.status-badge {
  flex-shrink: 0;
}

.status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: var(--any-radius-full);
}

.status.saved {
  color: var(--any-text-muted);
  background: var(--any-bg-secondary);
}

.status.unsaved {
  color: var(--td-state-warning, #FFB800);
  background: rgba(255, 184, 0, 0.1);
}

.status.streaming {
  color: var(--td-state-thinking);
  background: rgba(0, 217, 255, 0.1);
}

.status .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-dot 1s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Right section */
.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* Buttons */
.header-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  background: var(--any-bg-primary);
  color: var(--any-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  white-space: nowrap;
}

.header-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

.header-btn.active {
  background: var(--any-bg-tertiary);
  border-color: var(--any-border-hover);
}

.header-btn.primary {
  background: #1A1A1A;
  border-color: #1A1A1A;
  color: white;
}

.header-btn.primary:hover {
  background: #333;
  border-color: #333;
}

.header-btn.secondary {
  background: var(--any-bg-primary);
}

.header-btn.icon-only {
  padding: 6px;
  width: 32px;
  height: 32px;
  justify-content: center;
}

.chevron {
  transition: transform var(--any-duration-fast) var(--any-ease-default);
}

.header-btn.active .chevron {
  transform: rotate(180deg);
}

/* Dropdown */
.dropdown-wrapper {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  min-width: 160px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.dropdown-menu.right {
  left: auto;
  right: 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  color: var(--any-text-primary);
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: background var(--any-duration-fast) var(--any-ease-default);
}

.dropdown-item:hover {
  background: var(--any-bg-hover);
}

.dropdown-item .version-time {
  margin-left: auto;
  color: var(--any-text-muted);
  font-size: 12px;
}

.dropdown-divider {
  height: 1px;
  background: var(--any-border);
  margin: 4px 0;
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 150ms ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Responsive */
@media (max-width: 768px) {
  .document-header {
    padding: 8px 12px;
    gap: 8px;
  }

  .header-btn span:not(.status) {
    display: none;
  }

  .header-btn {
    padding: 6px;
    width: 32px;
    height: 32px;
    justify-content: center;
  }

  .header-btn .chevron {
    display: none;
  }
}
</style>
