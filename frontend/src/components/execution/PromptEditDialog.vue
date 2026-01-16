<script setup lang="ts">
import { ref, watch } from 'vue'
import { XMarkIcon, PencilSquareIcon, ArrowPathIcon } from '@heroicons/vue/24/outline'

interface Props {
  visible: boolean
  nodeId: string
  nodeLabel: string
  originalPrompt: string
}

interface Emits {
  (e: 'close'): void
  (e: 'confirm', nodeId: string, newPrompt: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const editedPrompt = ref('')
const isSubmitting = ref(false)

// 同步原始 prompt
watch(() => props.originalPrompt, (val) => {
  editedPrompt.value = val
}, { immediate: true })

// 重置为原始
function handleReset() {
  editedPrompt.value = props.originalPrompt
}

// 确认修改
async function handleConfirm() {
  if (!editedPrompt.value.trim()) return
  
  isSubmitting.value = true
  try {
    emit('confirm', props.nodeId, editedPrompt.value)
  } finally {
    isSubmitting.value = false
  }
}

// 关闭弹窗
function handleClose() {
  emit('close')
}

// 快捷键
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    handleClose()
  } else if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
    handleConfirm()
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div 
        v-if="visible" 
        class="dialog-backdrop"
        @click.self="handleClose"
        @keydown="handleKeydown"
      >
        <div class="dialog-container">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-title">
              <PencilSquareIcon class="w-5 h-5" />
              <span>修改执行指令</span>
            </div>
            <button class="close-btn" @click="handleClose">
              <XMarkIcon class="w-5 h-5" />
            </button>
          </div>
          
          <!-- Node Info -->
          <div class="node-info">
            <span class="node-badge">节点 {{ nodeId }}</span>
            <span class="node-label">{{ nodeLabel }}</span>
          </div>
          
          <!-- Prompt Editor -->
          <div class="editor-section">
            <label class="editor-label">执行指令</label>
            <textarea
              v-model="editedPrompt"
              class="prompt-textarea"
              placeholder="输入新的执行指令..."
              rows="6"
            />
            <div class="editor-hint">
              <span>修改后将从当前节点重新执行</span>
              <button class="reset-btn" @click="handleReset">
                <ArrowPathIcon class="w-4 h-4" />
                <span>重置</span>
              </button>
            </div>
          </div>
          
          <!-- Actions -->
          <div class="dialog-actions">
            <button class="btn-cancel" @click="handleClose">
              取消
            </button>
            <button 
              class="btn-confirm"
              :disabled="!editedPrompt.trim() || isSubmitting"
              @click="handleConfirm"
            >
              <svg v-if="isSubmitting" class="w-4 h-4 animate-spin\" fill=\"none\" viewBox=\"0 0 24 24\">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              {{ isSubmitting ? '执行中...' : '确认并继续' }}
              <kbd v-if="!isSubmitting">⌘↵</kbd>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.dialog-container {
  width: 100%;
  max-width: 560px;
  margin: 16px;
  background: rgba(28, 28, 30, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 150ms ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.node-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.2);
}

.node-badge {
  padding: 4px 10px;
  background: rgba(0, 217, 255, 0.15);
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #00D9FF;
}

.node-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.editor-section {
  padding: 20px;
}

.editor-label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
}

.prompt-textarea {
  width: 100%;
  padding: 14px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: #ffffff;
  resize: vertical;
  transition: all 150ms ease;
}

.prompt-textarea:focus {
  outline: none;
  border-color: rgba(0, 217, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.1);
}

.prompt-textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.editor-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

.reset-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 150ms ease;
}

.reset-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  color: #ffffff;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-cancel {
  padding: 10px 20px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.btn-confirm {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #00D9FF;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #000000;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-confirm:hover:not(:disabled) {
  background: #33E1FF;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-confirm kbd {
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  font-size: 11px;
  font-family: inherit;
}

/* Dialog Transition */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: all 200ms ease-out;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .dialog-container,
.dialog-fade-leave-to .dialog-container {
  transform: scale(0.95) translateY(10px);
}
</style>
