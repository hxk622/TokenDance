<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import * as monaco from 'monaco-editor'

interface FileDiff {
  path: string
  originalContent: string
  modifiedContent: string
  action: 'modified' | 'created' | 'deleted'
}

const props = defineProps<{
  filePath?: string
}>()

// Monaco Editor integration
const useMonaco = ref(true) // Toggle between Monaco and fallback view
const editorContainer = ref<HTMLElement | null>(null)
const diffEditor = shallowRef<monaco.editor.IStandaloneDiffEditor | null>(null)

// Mock diff data
const currentDiff = ref<FileDiff>({
  path: 'src/components/Button.vue',
  action: 'modified',
  originalContent: '<' + 'script setup lang="ts">\nimport { computed } from \'vue\'\n\nconst props = defineProps<{\n  label: string\n  disabled?: boolean\n}>()\n\nconst buttonClass = computed(() => ({\n  \'btn-disabled\': props.disabled\n}))\n<' + '/script>\n\n<' + 'template>\n  <button :class="buttonClass">\n    {{ label }}\n  </button>\n<' + '/template>',
  modifiedContent: '<' + 'script setup lang="ts">\nimport { computed } from \'vue\'\n\nconst props = defineProps<{\n  label: string\n  disabled?: boolean\n  variant?: \'primary\' | \'secondary\'\n}>()\n\nconst buttonClass = computed(() => ({\n  \'btn-disabled\': props.disabled,\n  \'btn-primary\': props.variant === \'primary\',\n  \'btn-secondary\': props.variant === \'secondary\'\n}))\n<' + '/script>\n\n<' + 'template>\n  <button :class="buttonClass">\n    {{ label }}\n  </button>\n<' + '/template>',
})

// Fallback diff lines (when Monaco is disabled or fails to load)
const diffLines = computed(() => {
  const original = currentDiff.value.originalContent.split('\n')
  const modified = currentDiff.value.modifiedContent.split('\n')
  const maxLines = Math.max(original.length, modified.length)

  return Array.from({ length: maxLines }, (_, i) => ({
    lineNumber: i + 1,
    original: original[i] || '',
    modified: modified[i] || '',
    status: getDiffStatus(original[i], modified[i]),
  }))
})

function getDiffStatus(original: string | undefined, modified: string | undefined): 'unchanged' | 'added' | 'removed' | 'modified' {
  if (original === undefined) return 'added'
  if (modified === undefined) return 'removed'
  if (original === modified) return 'unchanged'
  return 'modified'
}

// Monaco Editor initialization
function initMonacoEditor() {
  if (!editorContainer.value || diffEditor.value) return
  
  try {
    // Configure Monaco theme to match our dark UI
    monaco.editor.defineTheme('tokendance-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#1c1c1e',
        'editor.foreground': '#ffffff',
        'diffEditor.insertedTextBackground': '#00ff8820',
        'diffEditor.removedTextBackground': '#ff3b3020',
        'diffEditor.insertedLineBackground': '#00ff8815',
        'diffEditor.removedLineBackground': '#ff3b3015',
      }
    })
    monaco.editor.setTheme('tokendance-dark')
    
    // Create diff editor
    diffEditor.value = monaco.editor.createDiffEditor(editorContainer.value, {
      readOnly: true,
      renderSideBySide: true,
      automaticLayout: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 13,
      fontFamily: "'SF Mono', 'Monaco', 'Courier New', monospace",
      lineNumbers: 'on',
      renderLineHighlight: 'none',
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
        verticalScrollbarSize: 8,
        horizontalScrollbarSize: 8,
      },
    })
    
    updateDiffModel()
  } catch (error) {
    console.error('Failed to initialize Monaco Editor:', error)
    useMonaco.value = false
  }
}

function updateDiffModel() {
  if (!diffEditor.value) return
  
  // Detect language from file extension
  const ext = currentDiff.value.path.split('.').pop() || 'plaintext'
  const languageMap: Record<string, string> = {
    vue: 'html',
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    py: 'python',
    md: 'markdown',
    json: 'json',
    css: 'css',
    scss: 'scss',
    html: 'html',
  }
  const language: string = languageMap[ext] || 'plaintext'
  
  const originalModel = monaco.editor.createModel(currentDiff.value.originalContent, language)
  const modifiedModel = monaco.editor.createModel(currentDiff.value.modifiedContent, language)
  
  diffEditor.value.setModel({
    original: originalModel,
    modified: modifiedModel,
  })
}

// Navigation functions
function goToPrevChange() {
  if (!diffEditor.value) return
  const lineChanges = diffEditor.value.getLineChanges()
  if (!lineChanges || lineChanges.length === 0) return
  
  const currentLine = diffEditor.value.getModifiedEditor().getPosition()?.lineNumber || 0
  for (let i = lineChanges.length - 1; i >= 0; i--) {
    if (lineChanges[i].modifiedStartLineNumber < currentLine) {
      diffEditor.value.getModifiedEditor().revealLineInCenter(lineChanges[i].modifiedStartLineNumber)
      diffEditor.value.getModifiedEditor().setPosition({ lineNumber: lineChanges[i].modifiedStartLineNumber, column: 1 })
      break
    }
  }
}

function goToNextChange() {
  if (!diffEditor.value) return
  const lineChanges = diffEditor.value.getLineChanges()
  if (!lineChanges || lineChanges.length === 0) return
  
  const currentLine = diffEditor.value.getModifiedEditor().getPosition()?.lineNumber || 0
  for (const change of lineChanges) {
    if (change.modifiedStartLineNumber > currentLine) {
      diffEditor.value.getModifiedEditor().revealLineInCenter(change.modifiedStartLineNumber)
      diffEditor.value.getModifiedEditor().setPosition({ lineNumber: change.modifiedStartLineNumber, column: 1 })
      break
    }
  }
}

// Lifecycle
onMounted(() => {
  if (useMonaco.value) {
    // Delay initialization to ensure container is rendered
    setTimeout(initMonacoEditor, 100)
  }
})

onUnmounted(() => {
  if (diffEditor.value) {
    diffEditor.value.dispose()
    diffEditor.value = null
  }
})

// Watch for diff changes
watch(() => currentDiff.value, () => {
  if (useMonaco.value && diffEditor.value) {
    updateDiffModel()
  }
}, { deep: true })

// Watch for file path changes from props
watch(() => props.filePath, (newPath) => {
  if (newPath) {
    // In real implementation, fetch diff for this file
    console.log('File path changed:', newPath)
  }
})

defineExpose({
  editorContainer,
  diffLines,
  currentDiff,
  goToPrevChange,
  goToNextChange,
})
</script>

<template>
  <div class="live-diff">
    <div class="diff-header">
      <div class="file-path">
        <span class="path-text">{{ currentDiff.path }}</span>
        <span :class="['action-tag', currentDiff.action]">
          {{ currentDiff.action }}
        </span>
      </div>
      <div class="diff-controls">
        <button class="control-btn" title="上一处修改" @click="goToPrevChange">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="18 15 12 9 6 15"/>
          </svg>
        </button>
        <button class="control-btn" title="下一处修改" @click="goToNextChange">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </button>
        <button class="control-btn accept" title="接受修改">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </button>
        <button class="control-btn reject" title="拒绝修改">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Monaco Editor Diff View -->
    <div v-if="useMonaco" ref="editorContainer" class="monaco-container"></div>
    
    <!-- Fallback Diff Display (when Monaco fails or disabled) -->
    <div v-else class="diff-container">
      <div class="diff-side original">
        <div class="side-header">原始文件</div>
        <div class="code-view">
          <div
            v-for="line in diffLines"
            :key="'original-' + line.lineNumber"
            :class="['code-line', line.status]"
          >
            <span class="line-number">{{ line.lineNumber }}</span>
            <span class="line-content">{{ line.original }}</span>
          </div>
        </div>
      </div>

      <div class="diff-divider"></div>

      <div class="diff-side modified">
        <div class="side-header">修改后</div>
        <div class="code-view">
          <div
            v-for="line in diffLines"
            :key="'modified-' + line.lineNumber"
            :class="['code-line', line.status]"
          >
            <span class="line-number">{{ line.lineNumber }}</span>
            <span class="line-content">{{ line.modified }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.live-diff {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.diff-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--divider-color);
  background: rgba(28, 28, 30, 0.6);
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-icon {
  font-size: 16px;
}

.path-text {
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: 13px;
  color: var(--text-primary);
}

.action-tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 600;
}

.action-tag.modified {
  background: rgba(0, 217, 255, 0.2);
  color: #00D9FF;
}

.action-tag.created {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.action-tag.deleted {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

.diff-controls {
  display: flex;
  gap: 8px;
}

.control-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 120ms ease-out;
  font-size: 12px;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.diff-container {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.diff-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.side-header {
  padding: 8px 16px;
  background: rgba(28, 28, 30, 0.4);
  font-size: 12px;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--divider-color);
}

.code-view {
  flex: 1;
  overflow-y: auto;
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: 13px;
  line-height: 20px;
}

.code-view::-webkit-scrollbar {
  width: 8px;
}

.code-view::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
}

.code-view::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.code-line {
  display: flex;
  padding: 0 16px;
  transition: background 120ms ease-out;
}

.code-line.unchanged {
  background: transparent;
}

.code-line.added {
  background: rgba(0, 255, 136, 0.15);
}

.code-line.removed {
  background: rgba(255, 59, 48, 0.15);
}

.code-line.modified {
  background: rgba(0, 217, 255, 0.15);
}

.line-number {
  width: 40px;
  flex-shrink: 0;
  color: var(--text-secondary);
  text-align: right;
  padding-right: 12px;
  user-select: none;
}

.line-content {
  flex: 1;
  color: var(--text-primary);
  white-space: pre;
  overflow-x: auto;
}

.diff-divider {
  width: 1px;
  background: var(--divider-color);
}

.monaco-container {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 300px;
}

.control-btn.accept:hover {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.control-btn.reject:hover {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
}
</style>
