<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick, shallowRef } from 'vue'
import { 
  Copy, Check, FileCode, X, Plus, 
  Maximize2, Edit3, Eye, Download, MoreHorizontal
} from 'lucide-vue-next'
import * as monaco from 'monaco-editor'

interface CodeFile {
  id: string
  name: string
  language: string
  content: string
}

interface Props {
  /** Single file content (simple mode) */
  content?: string
  /** Language for single file mode */
  language?: string
  /** Multiple files (multi-tab mode) */
  files?: CodeFile[]
  /** Read-only mode */
  readOnly?: boolean
  /** Show line numbers */
  lineNumbers?: boolean
  /** Minimap visible */
  minimap?: boolean
  /** Theme */
  theme?: 'vs-dark' | 'vs-light'
  /** Word wrap */
  wordWrap?: 'on' | 'off'
}

const props = withDefaults(defineProps<Props>(), {
  content: '',
  language: 'typescript',
  files: () => [],
  readOnly: true,
  lineNumbers: true,
  minimap: false,
  theme: 'vs-dark',
  wordWrap: 'off'
})

const emit = defineEmits<{
  'content-change': [content: string, file?: CodeFile]
  'file-change': [file: CodeFile]
}>()

// State
const editorRef = ref<HTMLDivElement | null>(null)
const editor = shallowRef<monaco.editor.IStandaloneCodeEditor | null>(null)
const activeFileId = ref<string | null>(null)
const isCopied = ref(false)
const isFullscreen = ref(false)
const isEditing = ref(!props.readOnly)

// Computed
const isMultiFile = computed(() => props.files.length > 0)

const activeFile = computed(() => {
  if (!isMultiFile.value) return null
  return props.files.find(f => f.id === activeFileId.value) || props.files[0]
})

const currentContent = computed(() => {
  if (isMultiFile.value && activeFile.value) {
    return activeFile.value.content
  }
  return props.content
})

const currentLanguage = computed(() => {
  if (isMultiFile.value && activeFile.value) {
    return activeFile.value.language
  }
  return props.language
})

// Language detection from filename
function detectLanguage(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase()
  const langMap: Record<string, string> = {
    'ts': 'typescript',
    'tsx': 'typescript',
    'js': 'javascript',
    'jsx': 'javascript',
    'py': 'python',
    'json': 'json',
    'html': 'html',
    'css': 'css',
    'scss': 'scss',
    'md': 'markdown',
    'yaml': 'yaml',
    'yml': 'yaml',
    'sql': 'sql',
    'sh': 'shell',
    'bash': 'shell',
    'go': 'go',
    'rs': 'rust',
    'java': 'java',
    'c': 'c',
    'cpp': 'cpp',
    'h': 'c',
    'hpp': 'cpp'
  }
  return langMap[ext || ''] || 'plaintext'
}

// Initialize editor
function initEditor() {
  if (!editorRef.value) return
  
  // Dispose existing
  if (editor.value) {
    editor.value.dispose()
  }
  
  // Create editor
  editor.value = monaco.editor.create(editorRef.value, {
    value: currentContent.value,
    language: currentLanguage.value,
    theme: props.theme,
    readOnly: !isEditing.value,
    lineNumbers: props.lineNumbers ? 'on' : 'off',
    minimap: { enabled: props.minimap },
    wordWrap: props.wordWrap,
    fontSize: 13,
    fontFamily: "'SF Mono', 'Monaco', 'Menlo', monospace",
    automaticLayout: true,
    scrollBeyondLastLine: false,
    padding: { top: 12, bottom: 12 },
    renderLineHighlight: 'line',
    scrollbar: {
      verticalScrollbarSize: 8,
      horizontalScrollbarSize: 8
    }
  })
  
  // Content change handler
  editor.value.onDidChangeModelContent(() => {
    const newContent = editor.value?.getValue() || ''
    if (isMultiFile.value && activeFile.value) {
      emit('content-change', newContent, activeFile.value)
    } else {
      emit('content-change', newContent)
    }
  })
}

// Update editor content
function updateContent() {
  if (!editor.value) return
  
  const model = editor.value.getModel()
  if (model) {
    monaco.editor.setModelLanguage(model, currentLanguage.value)
    editor.value.setValue(currentContent.value)
  }
}

// Switch file
function switchFile(file: CodeFile) {
  activeFileId.value = file.id
  emit('file-change', file)
  nextTick(() => {
    updateContent()
  })
}

// Copy content
async function copyContent() {
  try {
    await navigator.clipboard.writeText(currentContent.value)
    isCopied.value = true
    setTimeout(() => {
      isCopied.value = false
    }, 2000)
  } catch (e) {
    console.error('Copy failed:', e)
  }
}

// Toggle edit mode
function toggleEditMode() {
  isEditing.value = !isEditing.value
  if (editor.value) {
    editor.value.updateOptions({ readOnly: !isEditing.value })
  }
}

// Toggle fullscreen
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => {
    editor.value?.layout()
  })
}

// Download file
function downloadFile() {
  const filename = activeFile.value?.name || 'code.txt'
  const blob = new Blob([currentContent.value], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  
  URL.revokeObjectURL(url)
}

// Watch for changes
watch(() => props.content, () => {
  if (!isMultiFile.value) {
    updateContent()
  }
})

watch(() => props.files, () => {
  if (isMultiFile.value && !activeFileId.value && props.files.length > 0) {
    activeFileId.value = props.files[0].id
    updateContent()
  }
}, { immediate: true })

watch(() => props.readOnly, (newVal) => {
  isEditing.value = !newVal
  if (editor.value) {
    editor.value.updateOptions({ readOnly: newVal })
  }
})

// Lifecycle
onMounted(() => {
  nextTick(() => {
    initEditor()
  })
})

onUnmounted(() => {
  if (editor.value) {
    editor.value.dispose()
  }
})
</script>

<template>
  <div :class="['code-editor', { fullscreen: isFullscreen }]">
    <!-- Toolbar -->
    <div class="editor-toolbar">
      <!-- File Tabs (multi-file mode) -->
      <div v-if="isMultiFile" class="file-tabs">
        <button
          v-for="file in files"
          :key="file.id"
          :class="['file-tab', { active: file.id === activeFileId }]"
          @click="switchFile(file)"
        >
          <FileCode class="w-3.5 h-3.5" />
          <span class="file-name">{{ file.name }}</span>
        </button>
      </div>
      
      <!-- Language Badge (single file mode) -->
      <div v-else class="language-badge">
        <FileCode class="w-4 h-4" />
        <span>{{ language }}</span>
      </div>

      <!-- Actions -->
      <div class="editor-actions">
        <button 
          :class="['action-btn', { active: isEditing }]"
          :title="isEditing ? '查看模式' : '编辑模式'"
          @click="toggleEditMode"
        >
          <Edit3 v-if="!isEditing" class="w-4 h-4" />
          <Eye v-else class="w-4 h-4" />
        </button>
        <button 
          class="action-btn"
          :title="isCopied ? '已复制' : '复制代码'"
          @click="copyContent"
        >
          <Check v-if="isCopied" class="w-4 h-4 text-green-500" />
          <Copy v-else class="w-4 h-4" />
        </button>
        <button 
          class="action-btn"
          title="下载"
          @click="downloadFile"
        >
          <Download class="w-4 h-4" />
        </button>
        <button 
          class="action-btn"
          title="全屏"
          @click="toggleFullscreen"
        >
          <Maximize2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Editor Container -->
    <div class="editor-container">
      <div ref="editorRef" class="monaco-container" />
    </div>
  </div>
</template>

<style scoped>
.code-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.code-editor.fullscreen {
  position: fixed;
  inset: 0;
  z-index: 9999;
  border-radius: 0;
}

/* Toolbar */
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  height: 40px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

/* File Tabs */
.file-tabs {
  display: flex;
  gap: 2px;
  overflow-x: auto;
  scrollbar-width: none;
}

.file-tabs::-webkit-scrollbar {
  display: none;
}

.file-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
  white-space: nowrap;
}

.file-tab:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-secondary);
}

.file-tab.active {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.file-name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Language Badge */
.language-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-secondary);
}

/* Actions */
.editor-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.action-btn.active {
  background: var(--td-state-thinking-bg);
  color: var(--td-state-thinking, #00D9FF);
}

/* Editor Container */
.editor-container {
  flex: 1;
  overflow: hidden;
}

.monaco-container {
  width: 100%;
  height: 100%;
}

/* Monaco overrides */
:deep(.monaco-editor) {
  --vscode-editor-background: var(--any-bg-primary);
}

:deep(.monaco-editor .margin) {
  background: var(--any-bg-primary) !important;
}
</style>
