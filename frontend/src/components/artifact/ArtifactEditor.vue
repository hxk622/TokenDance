<script setup lang="ts">
/**
 * ArtifactEditor - Core editor component for Project-First architecture
 *
 * Features:
 * - Rich text display for artifacts (markdown, code, etc.)
 * - Text selection with floating toolbar
 * - "Ask AI" action on selected text
 * - Version indicator
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useProjectStore } from '@/stores/project'
import type { SelectionContext } from '@/types/project'
import { sanitizeHtml } from '@/utils/sanitize'
import {
  Wand2,
  Copy,
  Scissors,
  RefreshCw,
  ChevronDown,
  FileText,
  Code2,
  X,
} from 'lucide-vue-next'

// Props
interface Artifact {
  id: string
  name: string
  artifact_type: string
  content: string
  version: number
  is_latest: boolean
  content_preview?: string
  word_count?: number
}

const props = defineProps<{
  artifact: Artifact | null
  readonly?: boolean
}>()

const emit = defineEmits<{
  'ask-ai': [selection: SelectionContext, prompt?: string]
  'update': [content: string]
  'copy': [text: string]
}>()

const projectStore = useProjectStore()

// Refs
const editorRef = ref<HTMLDivElement | null>(null)
const contentRef = ref<HTMLDivElement | null>(null)

// Selection state
const selection = ref<SelectionContext | null>(null)
const showToolbar = ref(false)
const toolbarPosition = ref({ x: 0, y: 0 })

// Quick prompts for Ask AI
const quickPrompts = [
  { id: 'improve', label: '润色', icon: Wand2 },
  { id: 'simplify', label: '简化', icon: Scissors },
  { id: 'expand', label: '扩展', icon: RefreshCw },
  { id: 'translate', label: '翻译', icon: RefreshCw },
]

// Content type detection
const contentType = computed(() => {
  if (!props.artifact) return 'text'
  const type = props.artifact.artifact_type
  if (type === 'code') return 'code'
  if (type === 'markdown' || type === 'report') return 'markdown'
  return 'text'
})

const safeContent = computed(() => {
  if (!props.artifact) return ''
  return sanitizeHtml(props.artifact.content)
})

// Handle text selection
function handleSelectionChange() {
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed || !contentRef.value) {
    hideToolbar()
    return
  }

  const text = sel.toString().trim()
  if (!text || text.length < 2) {
    hideToolbar()
    return
  }

  // Check if selection is within our editor
  const range = sel.getRangeAt(0)
  if (!contentRef.value.contains(range.commonAncestorContainer)) {
    hideToolbar()
    return
  }

  // Get selection range
  const rect = range.getBoundingClientRect()
  const editorRect = editorRef.value?.getBoundingClientRect()

  if (!editorRect) return

  // Update selection context
  selection.value = {
    artifact_id: props.artifact?.id || '',
    selected_text: text,
    selection_range: {
      start: range.startOffset,
      end: range.endOffset,
    },
  }

  // Position toolbar above selection
  toolbarPosition.value = {
    x: rect.left + rect.width / 2 - editorRect.left,
    y: rect.top - editorRect.top - 8,
  }

  showToolbar.value = true
}

function hideToolbar() {
  showToolbar.value = false
  selection.value = null
}

// Handle Ask AI action
function handleAskAI(promptType?: string) {
  if (!selection.value) return

  let prompt: string | undefined
  if (promptType) {
    const prompts: Record<string, string> = {
      improve: '请润色这段文字，使其更加流畅专业',
      simplify: '请简化这段文字，保持核心意思',
      expand: '请扩展这段文字，添加更多细节',
      translate: '请将这段文字翻译成英文',
    }
    prompt = prompts[promptType]
  }

  emit('ask-ai', selection.value, prompt)
  hideToolbar()
}

// Handle copy
function handleCopy() {
  if (!selection.value?.selected_text) return
  navigator.clipboard.writeText(selection.value.selected_text)
  emit('copy', selection.value.selected_text)
  hideToolbar()
}

// Lifecycle
onMounted(() => {
  document.addEventListener('selectionchange', handleSelectionChange)
})

onUnmounted(() => {
  document.removeEventListener('selectionchange', handleSelectionChange)
})

// Click outside to hide toolbar
function handleEditorClick(e: MouseEvent) {
  // Don't hide if clicking on toolbar
  const target = e.target as HTMLElement
  if (target.closest('.selection-toolbar')) return

  // Check if there's still a valid selection
  const sel = window.getSelection()
  if (!sel || sel.isCollapsed) {
    hideToolbar()
  }
}
</script>

<template>
  <div
    ref="editorRef"
    class="artifact-editor"
    @click="handleEditorClick"
  >
    <!-- Header -->
    <div
      v-if="artifact"
      class="editor-header"
    >
      <div class="header-left">
        <component
          :is="contentType === 'code' ? Code2 : FileText"
          class="artifact-icon"
        />
        <span class="artifact-name">{{ artifact.name }}</span>
        <span
          v-if="artifact.version > 1"
          class="version-badge"
        >
          v{{ artifact.version }}
        </span>
      </div>
      <div class="header-right">
        <span
          v-if="artifact.word_count"
          class="word-count"
        >
          {{ artifact.word_count }} 字
        </span>
      </div>
    </div>

    <!-- Content Area -->
    <div
      ref="contentRef"
      class="editor-content"
      :class="{ readonly: readonly, [`type-${contentType}`]: true }"
    >
      <template v-if="artifact">
        <!-- Code content -->
        <pre
          v-if="contentType === 'code'"
          class="code-content"
        ><code>{{ artifact.content }}</code></pre>

        <!-- Markdown/text content -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div
          v-else
          class="text-content"
          v-html="safeContent"
        />
      </template>

      <!-- Empty state -->
      <div
        v-else
        class="empty-state"
      >
        <FileText class="empty-icon" />
        <p>选择一个 Artifact 开始编辑</p>
      </div>
    </div>

    <!-- Selection Toolbar -->
    <Transition name="toolbar">
      <div
        v-if="showToolbar && selection"
        class="selection-toolbar"
        :style="{
          left: `${toolbarPosition.x}px`,
          top: `${toolbarPosition.y}px`,
        }"
      >
        <!-- Quick prompts -->
        <button
          v-for="prompt in quickPrompts"
          :key="prompt.id"
          class="toolbar-btn"
          :title="prompt.label"
          @click="handleAskAI(prompt.id)"
        >
          <component
            :is="prompt.icon"
            class="btn-icon"
          />
          <span class="btn-label">{{ prompt.label }}</span>
        </button>

        <div class="toolbar-divider" />

        <!-- Copy -->
        <button
          class="toolbar-btn"
          title="复制"
          @click="handleCopy"
        >
          <Copy class="btn-icon" />
        </button>

        <!-- Ask AI with custom prompt -->
        <button
          class="toolbar-btn primary"
          title="Ask AI"
          @click="handleAskAI()"
        >
          <Wand2 class="btn-icon" />
          <span class="btn-label">Ask AI</span>
        </button>

        <!-- Close -->
        <button
          class="toolbar-btn close"
          title="关闭"
          @click="hideToolbar"
        >
          <X class="btn-icon" />
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.artifact-editor {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
}

/* Header */
.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.artifact-icon {
  width: 18px;
  height: 18px;
  color: var(--any-text-secondary);
}

.artifact-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.version-badge {
  padding: 2px 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--exec-accent);
  background: rgba(0, 217, 255, 0.1);
  border-radius: var(--any-radius-sm);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.word-count {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

/* Content */
.editor-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.editor-content.readonly {
  user-select: text;
}

.text-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--any-text-primary);
}

.text-content :deep(h1),
.text-content :deep(h2),
.text-content :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
  color: var(--any-text-primary);
}

.text-content :deep(p) {
  margin-bottom: 1em;
}

.text-content :deep(ul),
.text-content :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 1em;
}

.code-content {
  margin: 0;
  padding: 16px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-md);
  overflow-x: auto;
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.5;
  color: var(--any-text-primary);
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--any-text-tertiary);
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 14px;
}

/* Selection Toolbar */
.selection-toolbar {
  position: absolute;
  transform: translateX(-50%) translateY(-100%);
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 8px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: none;
  background: transparent;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  white-space: nowrap;
}

.toolbar-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.toolbar-btn.primary {
  background: var(--exec-accent);
  color: var(--any-bg-primary);
}

.toolbar-btn.primary:hover {
  opacity: 0.9;
}

.toolbar-btn.close {
  padding: 6px;
}

.toolbar-btn.close:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--any-error);
}

.btn-icon {
  width: 14px;
  height: 14px;
}

.btn-label {
  display: none;
}

@media (min-width: 768px) {
  .btn-label {
    display: inline;
  }
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  background: var(--any-border);
  margin: 0 4px;
}

/* Toolbar animation */
.toolbar-enter-active,
.toolbar-leave-active {
  transition: all 0.15s ease;
}

.toolbar-enter-from,
.toolbar-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-100%) scale(0.95);
}
</style>
