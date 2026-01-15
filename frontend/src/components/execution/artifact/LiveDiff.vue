<script setup lang="ts">
import { ref, computed } from 'vue'
// computed is used for diffLines below

// Monaco Editor integration will be added later
// For now, we'll use a mock diff display

interface FileDiff {
  path: string
  originalContent: string
  modifiedContent: string
  action: 'modified' | 'created' | 'deleted'
}

defineProps<{
  filePath?: string
}>()

// Mock diff data
const currentDiff = ref<FileDiff>({
  path: 'src/components/Button.vue',
  action: 'modified',
  originalContent: `<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  disabled?: boolean
}>()

const buttonClass = computed(() => ({
  'btn-disabled': props.disabled
}))
</script>

<template>
  <button :class="buttonClass">
    {{ label }}
  </button>
</template>`,
  modifiedContent: `<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  disabled?: boolean
  variant?: 'primary' | 'secondary'
}>()

const buttonClass = computed(() => ({
  'btn-disabled': props.disabled,
  'btn-primary': props.variant === 'primary',
  'btn-secondary': props.variant === 'secondary'
}))
</script>

<template>
  <button :class="buttonClass">
    {{ label }}
  </button>
</template>`,
})

// For Phase2 MVP, we'll show side-by-side text comparison
// In Phase3, we'll integrate Monaco Editor Diff

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

function getDiffStatus(original: string, modified: string): 'unchanged' | 'added' | 'removed' | 'modified' {
  if (original === undefined) return 'added'
  if (modified === undefined) return 'removed'
  if (original === modified) return 'unchanged'
  return 'modified'
}

// Monaco Editor integration placeholder
const editorContainer = ref<HTMLElement | null>(null)

defineExpose({
  editorContainer,
  diffLines,
  currentDiff
})
</script>

<template>
  <div class="live-diff">
    <div class="diff-header">
      <div class="file-path">
        <span class="path-icon">📄</span>
        <span class="path-text">{{ currentDiff.path }}</span>
        <span :class="['action-tag', currentDiff.action]">
          {{ currentDiff.action }}
        </span>
      </div>
      <div class="diff-controls">
        <button class="control-btn" title="上一处修改">⬆</button>
        <button class="control-btn" title="下一处修改">⬇</button>
        <button class="control-btn" title="接受修改">✓</button>
        <button class="control-btn" title="拒绝修改">✕</button>
      </div>
    </div>

    <!-- Mock Diff Display (Phase2 MVP) -->
    <div class="diff-container">
      <div class="diff-side original">
        <div class="side-header">原始文件</div>
        <div class="code-view">
          <div
            v-for="line in diffLines"
            :key="`original-${line.lineNumber}`"
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
            :key="`modified-${line.lineNumber}`"
            :class="['code-line', line.status]"
          >
            <span class="line-number">{{ line.lineNumber }}</span>
            <span class="line-content">{{ line.modified }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Monaco Editor Container (Phase3) -->
    <div ref="editorContainer" class="monaco-container" style="display: none;"></div>
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
}

:root {
  --bg-primary: rgba(18, 18, 18, 0.95);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.6);
  --divider-color: rgba(255, 255, 255, 0.1);
}
</style>
