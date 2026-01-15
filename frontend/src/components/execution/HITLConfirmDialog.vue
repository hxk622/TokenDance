<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="visible" class="hitl-overlay" @click.self="handleCancel">
        <div class="hitl-dialog">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-icon">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 class="dialog-title">操作确认</h3>
          </div>

          <!-- Content -->
          <div class="dialog-content">
            <div class="operation-badge">
              <span class="badge-label">操作类型</span>
              <span class="badge-value">{{ request?.operation }}</span>
            </div>

            <p class="description">{{ request?.description }}</p>

            <!-- Context Details -->
            <div v-if="hasContext" class="context-section">
              <button 
                @click="showContext = !showContext"
                class="context-toggle"
              >
                <span>详细信息</span>
                <svg 
                  class="w-4 h-4 transition-transform" 
                  :class="{ 'rotate-180': showContext }"
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              <Transition name="slide">
                <div v-if="showContext" class="context-content">
                  <pre>{{ JSON.stringify(request?.context, null, 2) }}</pre>
                </div>
              </Transition>
            </div>

            <!-- Feedback Input -->
            <div class="feedback-section">
              <label class="feedback-label">反馈（可选）</label>
              <textarea
                v-model="feedback"
                placeholder="添加备注或修改建议..."
                class="feedback-input"
                rows="2"
              />
            </div>
          </div>

          <!-- Actions -->
          <div class="dialog-actions">
            <button 
              @click="handleReject"
              :disabled="loading"
              class="btn btn-reject"
            >
              <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              拒绝
            </button>
            <button 
              @click="handleApprove"
              :disabled="loading"
              class="btn btn-approve"
            >
              <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ loading ? '处理中...' : '确认执行' }}
            </button>
          </div>

          <!-- Timeout Warning -->
          <div v-if="timeoutSeconds > 0" class="timeout-warning">
            <span class="timeout-text">
              请在 {{ timeoutSeconds }} 秒内响应，否则将自动取消
            </span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { hitlApi, type HITLRequest } from '@/api/hitl'

const props = defineProps<{
  visible: boolean
  request: HITLRequest | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirmed', approved: boolean): void
}>()

// State
const feedback = ref('')
const loading = ref(false)
const showContext = ref(false)
const timeoutSeconds = ref(0)
let timeoutInterval: ReturnType<typeof setInterval> | null = null

// Computed
const hasContext = computed(() => {
  return props.request?.context && Object.keys(props.request.context).length > 0
})

// Methods
const handleApprove = async () => {
  if (!props.request) return
  
  loading.value = true
  try {
    await hitlApi.confirm(props.request.request_id, {
      approved: true,
      user_feedback: feedback.value || null,
    })
    emit('confirmed', true)
    resetState()
  } catch (error) {
    console.error('Failed to approve:', error)
  } finally {
    loading.value = false
  }
}

const handleReject = async () => {
  if (!props.request) return
  
  loading.value = true
  try {
    await hitlApi.confirm(props.request.request_id, {
      approved: false,
      user_feedback: feedback.value || null,
    })
    emit('confirmed', false)
    resetState()
  } catch (error) {
    console.error('Failed to reject:', error)
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  emit('close')
  resetState()
}

const resetState = () => {
  feedback.value = ''
  showContext.value = false
  timeoutSeconds.value = 0
  if (timeoutInterval) {
    clearInterval(timeoutInterval)
    timeoutInterval = null
  }
}

// Timeout countdown
const startTimeout = () => {
  timeoutSeconds.value = 300 // 5 minutes
  timeoutInterval = setInterval(() => {
    timeoutSeconds.value--
    if (timeoutSeconds.value <= 0) {
      handleCancel()
    }
  }, 1000)
}

// Watch visibility
watch(() => props.visible, (visible) => {
  if (visible) {
    startTimeout()
  } else {
    resetState()
  }
})

// Cleanup
onUnmounted(() => {
  if (timeoutInterval) {
    clearInterval(timeoutInterval)
  }
})
</script>

<style scoped>
.hitl-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 1000;
}

.hitl-dialog {
  width: 100%;
  max-width: 480px;
  margin: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  background: #fffbeb;
  border-bottom: 1px solid #fef3c7;
}

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: #fef3c7;
  border-radius: 10px;
  color: #d97706;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #92400e;
}

.dialog-content {
  padding: 24px;
}

.operation-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  margin-bottom: 16px;
}

.badge-label {
  font-size: 12px;
  color: #6b7280;
}

.badge-value {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.description {
  margin: 0 0 20px;
  font-size: 15px;
  line-height: 1.6;
  color: #374151;
}

.context-section {
  margin-bottom: 20px;
}

.context-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  width: 100%;
  font-size: 14px;
  font-weight: 500;
  color: #6366f1;
  background: #f5f3ff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.context-toggle:hover {
  background: #ede9fe;
}

.context-content {
  margin-top: 8px;
  padding: 12px;
  background: #1f2937;
  border-radius: 6px;
  overflow-x: auto;
}

.context-content pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Monaco', 'Courier New', monospace;
  color: #e5e7eb;
  white-space: pre-wrap;
  word-break: break-all;
}

.feedback-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.feedback-label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.feedback-input {
  padding: 10px 12px;
  font-size: 14px;
  color: #111827;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  resize: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.feedback-input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.dialog-actions {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 12px 20px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-reject {
  color: #dc2626;
  background: white;
  border: 1px solid #fecaca;
}

.btn-reject:hover:not(:disabled) {
  background: #fef2f2;
  border-color: #dc2626;
}

.btn-approve {
  color: white;
  background: #10b981;
}

.btn-approve:hover:not(:disabled) {
  background: #059669;
}

.timeout-warning {
  padding: 12px 24px;
  background: #fef3c7;
  text-align: center;
}

.timeout-text {
  font-size: 13px;
  color: #92400e;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
