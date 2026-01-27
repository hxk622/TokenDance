<script setup lang="ts">
/**
 * UnifiedChatInput - 统一输入框组件
 * 
 * 用于首页和执行页的复用，统一设计风格：
 * - 高度 116px (含 toolbar)
 * - 居中自适应宽度 (max-width: 720px)
 * - padding 16px
 * - 支持附件、语音输入
 * - 运行时显示停止按钮
 */
import { ref, computed, onMounted } from 'vue'
import { Send, Paperclip, Mic, ArrowUp, Square, X, Image as ImageIcon } from 'lucide-vue-next'

interface Props {
  /** 禁用输入 */
  disabled?: boolean
  /** 占位符文字 */
  placeholder?: string
  /** 最大字符数 */
  maxLength?: number
  /** 任务是否正在运行 (显示停止按钮) */
  isRunning?: boolean
  /** 是否自动聚焦 */
  autoFocus?: boolean
  /** 容器样式变体 */
  variant?: 'home' | 'execution'
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入你的任务...',
  maxLength: 2000,
  isRunning: false,
  autoFocus: false,
  variant: 'home'
})

const emit = defineEmits<{
  /** 发送消息 */
  send: [content: string]
  /** 终止执行 */
  stop: []
}>()

// Refs
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const inputValue = ref('')
const isFocused = ref(false)

// Computed
const canSend = computed(() => {
  return inputValue.value.trim().length > 0 && !props.disabled
})

const charCount = computed(() => inputValue.value.length)
const isNearLimit = computed(() => charCount.value > props.maxLength * 0.9)

// Methods
function handleSubmit() {
  if (!canSend.value) return
  emit('send', inputValue.value.trim())
  inputValue.value = ''
  // Reset textarea height
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}

function handleStop() {
  emit('stop')
}

function handleKeydown(e: KeyboardEvent) {
  // Cmd/Ctrl + Enter to submit
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
    e.preventDefault()
    handleSubmit()
  }
  // Shift + Enter for new line (default behavior)
}

function handleInput(e: Event) {
  const target = e.target as HTMLTextAreaElement
  // Auto-resize
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

function handleAttachClick() {
  fileInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (files && files.length > 0) {
    // TODO: Handle file upload
    console.log('Files selected:', files)
  }
  // Reset input
  target.value = ''
}

function focus() {
  inputRef.value?.focus()
}

function clear() {
  inputValue.value = ''
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}

// Lifecycle
onMounted(() => {
  if (props.autoFocus) {
    focus()
  }
})

// Expose
defineExpose({
  focus,
  clear,
  inputRef
})
</script>

<template>
  <div
    :class="['unified-input', `variant-${variant}`, { focused: isFocused, disabled }]"
  >
    <!-- Input Content -->
    <div class="input-content">
      <textarea
        ref="inputRef"
        v-model="inputValue"
        class="main-textarea"
        :placeholder="placeholder"
        :disabled="disabled"
        :maxlength="maxLength"
        rows="1"
        @keydown="handleKeydown"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
      />
    </div>
    
    <!-- Toolbar -->
    <div class="input-toolbar">
      <div class="toolbar-left">
        <button
          class="toolbar-btn"
          title="添加附件"
          :disabled="disabled"
          @click="handleAttachClick"
        >
          <Paperclip class="w-5 h-5" />
        </button>
        <input
          ref="fileInputRef"
          type="file"
          class="hidden"
          multiple
          @change="handleFileSelect"
        >
      </div>
      <div class="toolbar-right">
        <!-- Character count -->
        <span
          v-if="isNearLimit"
          :class="['char-count', { warning: charCount >= maxLength }]"
        >
          {{ charCount }}/{{ maxLength }}
        </span>
        
        <button
          class="toolbar-btn"
          title="语音输入"
          :disabled="disabled"
        >
          <Mic class="w-5 h-5" />
        </button>
        
        <!-- Stop button (when running) -->
        <button
          v-if="isRunning"
          class="submit-btn stop"
          title="终止执行"
          @click="handleStop"
        >
          <Square class="w-5 h-5" />
        </button>
        <!-- Send button -->
        <button
          v-else
          class="submit-btn"
          :class="{ active: canSend }"
          :disabled="!canSend"
          title="发送 (Cmd+Enter)"
          @click="handleSubmit"
        >
          <ArrowUp class="w-5 h-5" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.unified-input {
  position: relative;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 20px;
  box-shadow: 0 12px 20px 0 rgba(28, 28, 32, 0.05);
  overflow: hidden;
  transition: all 200ms ease;
  width: 100%;
  max-width: 720px;
}

.unified-input.focused {
  border-color: var(--any-border-hover);
  box-shadow: 0 12px 24px 0 rgba(28, 28, 32, 0.08);
}

.unified-input.disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* Variant: execution - smaller max-width */
.unified-input.variant-execution {
  max-width: 100%;
  border-radius: 16px;
}

/* Input Content */
.input-content {
  min-height: 52px;
  max-height: 200px;
  padding: 14px 16px;
  padding-bottom: 0;
}

.main-textarea {
  width: 100%;
  min-height: 26px;
  max-height: 120px;
  font-size: 16px;
  line-height: 26px;
  color: var(--any-text-primary);
  background: transparent;
  border: none;
  resize: none;
  outline: none;
  font-family: inherit;
}

.main-textarea::placeholder {
  color: var(--any-text-muted);
}

.main-textarea:disabled {
  cursor: not-allowed;
}

/* Toolbar */
.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: none;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  color: var(--any-text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.toolbar-btn:hover:not(:disabled) {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.toolbar-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* Character count */
.char-count {
  font-size: 12px;
  color: var(--any-text-muted);
  margin-right: 4px;
}

.char-count.warning {
  color: var(--exec-warning, #FFB800);
}

/* Submit Button */
.submit-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: var(--any-bg-tertiary);
  color: var(--any-text-tertiary);
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.submit-btn.active {
  background: var(--any-text-primary);
  color: var(--any-text-inverse);
}

.submit-btn.active:hover {
  transform: scale(1.05);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* Stop button */
.submit-btn.stop {
  background: linear-gradient(135deg, #FF6B6B, #FF3B30);
  color: white;
  cursor: pointer;
}

.submit-btn.stop:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(255, 59, 48, 0.4);
}

/* Hidden elements */
.hidden {
  display: none;
}
</style>
