<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="hitl-overlay"
        @click.self="handleCancel"
      >
        <div class="hitl-dialog">
          <!-- Header -->
          <div
            class="dialog-header"
            :class="headerClass"
          >
            <div
              class="header-icon"
              :class="iconClass"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <div class="header-content">
              <h3 class="dialog-title">
                操作确认
              </h3>
              <div
                class="risk-badge"
                :class="riskBadgeClass"
              >
                {{ riskLevelLabel }}
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="dialog-content">
            <div class="operation-info">
              <div class="operation-badge">
                <span class="badge-label">工具</span>
                <span class="badge-value">{{ request?.operation || request?.context?.tool }}</span>
              </div>
              <div
                v-if="operationCategories.length > 0"
                class="category-tags"
              >
                <span
                  v-for="category in operationCategories"
                  :key="category"
                  class="category-tag"
                >
                  {{ getCategoryLabel(category) }}
                </span>
              </div>
            </div>

            <p class="description">
              {{ request?.description }}
            </p>

            <!-- Risk Explanation -->
            <div
              v-if="riskLevel"
              class="risk-explanation"
            >
              <div
                class="risk-icon"
                :class="riskIconClass"
              >
                <svg
                  v-if="riskLevel === 'critical'"
                  class="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <svg
                  v-else
                  class="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <span class="risk-text">{{ riskExplanation }}</span>
            </div>

            <!-- Context Details -->
            <div
              v-if="hasContext"
              class="context-section"
            >
              <button
                class="context-toggle"
                @click="showContext = !showContext"
              >
                <span>详细信息</span>
                <svg
                  class="w-4 h-4 transition-transform"
                  :class="{ 'rotate-180': showContext }"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 9l-7 7-7-7"
                  />
                </svg>
              </button>

              <Transition name="slide">
                <div
                  v-if="showContext"
                  class="context-content"
                >
                  <pre>{{ JSON.stringify(request?.context, null, 2) }}</pre>
                </div>
              </Transition>
            </div>

            <!-- Remember Choice -->
            <div
              v-if="canRemember"
              class="remember-section"
            >
              <label class="remember-checkbox">
                <input
                  v-model="rememberChoice"
                  type="checkbox"
                  class="checkbox-input"
                >
                <span class="checkbox-label">
                  记住此选择（本次会话内有效）
                </span>
              </label>
              <p class="remember-hint">
                勾选后，同类操作将自动执行，无需再次确认
              </p>
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
              :disabled="loading"
              class="btn btn-reject"
              @click="handleReject"
            >
              <svg
                class="w-4 h-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              拒绝
            </button>
            <button
              :disabled="loading"
              class="btn btn-approve"
              @click="handleApprove"
            >
              <svg
                class="w-4 h-4 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
              {{ loading ? '处理中...' : '确认执行' }}
            </button>
          </div>

          <!-- Timeout Warning -->
          <div
            v-if="timeoutSeconds > 0"
            class="timeout-warning"
          >
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

interface ExtendedHITLRequest extends Omit<HITLRequest, 'context'> {
  operation?: string  // legacy alias for type
  request_id?: string  // legacy alias for id
  context: {
    tool?: string
    args?: Record<string, unknown>
    risk_level?: string
    operation_categories?: string[]
    can_remember?: boolean
    [key: string]: unknown
  }
}

const props = defineProps<{
  visible: boolean
  request: ExtendedHITLRequest | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirmed', approved: boolean, rememberChoice?: boolean): void
}>()

// State
const feedback = ref('')
const loading = ref(false)
const showContext = ref(false)
const rememberChoice = ref(false)
const timeoutSeconds = ref(0)
let timeoutInterval: ReturnType<typeof setInterval> | null = null

// Computed
const hasContext = computed(() => {
  return props.request?.context && Object.keys(props.request.context).length > 0
})

const riskLevel = computed(() => {
  return props.request?.context?.risk_level || 'low'
})

const operationCategories = computed(() => {
  return props.request?.context?.operation_categories || []
})

const canRemember = computed(() => {
  return props.request?.context?.can_remember !== false && riskLevel.value !== 'critical'
})

const riskLevelLabel = computed(() => {
  const labels: Record<string, string> = {
    none: '无风险',
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    critical: '极高风险'
  }
  return labels[riskLevel.value] || '未知'
})

const riskExplanation = computed(() => {
  const explanations: Record<string, string> = {
    none: '此操作为纯读取操作，不会产生任何副作用',
    low: '此操作可能创建新文件，但不会修改现有内容',
    medium: '此操作可能修改或删除现有文件',
    high: '此操作可能造成数据丢失或系统变更',
    critical: '此操作不可逆，请谨慎确认'
  }
  return explanations[riskLevel.value] || ''
})

const headerClass = computed(() => {
  const classes: Record<string, string> = {
    none: 'header-none',
    low: 'header-low',
    medium: 'header-medium',
    high: 'header-high',
    critical: 'header-critical'
  }
  return classes[riskLevel.value] || 'header-low'
})

const iconClass = computed(() => {
  const classes: Record<string, string> = {
    none: 'icon-none',
    low: 'icon-low',
    medium: 'icon-medium',
    high: 'icon-high',
    critical: 'icon-critical'
  }
  return classes[riskLevel.value] || 'icon-low'
})

const riskBadgeClass = computed(() => {
  const classes: Record<string, string> = {
    none: 'badge-none',
    low: 'badge-low',
    medium: 'badge-medium',
    high: 'badge-high',
    critical: 'badge-critical'
  }
  return classes[riskLevel.value] || 'badge-low'
})

const riskIconClass = computed(() => {
  const classes: Record<string, string> = {
    none: 'risk-icon-none',
    low: 'risk-icon-low',
    medium: 'risk-icon-medium',
    high: 'risk-icon-high',
    critical: 'risk-icon-critical'
  }
  return classes[riskLevel.value] || 'risk-icon-low'
})

// Methods
const getCategoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    web_search: '网页搜索',
    web_read: '读取网页',
    file_read: '读取文件',
    file_create: '创建文件',
    file_modify: '修改文件',
    file_delete: '删除文件',
    shell_safe: '安全命令',
    shell_write: '写入命令',
    shell_dangerous: '危险命令',
    document_create: '创建文档'
  }
  return labels[category] || category
}

const handleApprove = async () => {
  if (!props.request) return

  loading.value = true
  try {
    // 如果选择了"记住"，在反馈中添加标记
    const feedbackText = rememberChoice.value
      ? `[remember] ${feedback.value || ''}`.trim()
      : feedback.value || null

    await hitlApi.confirm(props.request.request_id || props.request.id, {
      approved: true,
      user_feedback: feedbackText,
    })
    emit('confirmed', true, rememberChoice.value)
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
    await hitlApi.confirm(props.request.request_id || props.request.id, {
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
  rememberChoice.value = false
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
/* HITLConfirmDialog - 使用全局主题变量 */
.hitl-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-glass);
  backdrop-filter: blur(8px);
  z-index: 1000;
}

.hitl-dialog {
  width: 100%;
  max-width: 480px;
  margin: 16px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-xl);
  box-shadow: var(--any-shadow-xl);
  overflow: hidden;
}

/* Header styles by risk level */
.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid;
}

.header-none { background: #f0fdf4; border-color: #bbf7d0; }
.header-low { background: #fffbeb; border-color: #fef3c7; }
.header-medium { background: #fff7ed; border-color: #fed7aa; }
.header-high { background: #fef2f2; border-color: #fecaca; }
.header-critical { background: #fef2f2; border-color: #fca5a5; }

.header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
}

.icon-none { background: #bbf7d0; color: #16a34a; }
.icon-low { background: #fef3c7; color: #d97706; }
.icon-medium { background: #fed7aa; color: #ea580c; }
.icon-high { background: #fecaca; color: #dc2626; }
.icon-critical { background: #fca5a5; color: #b91c1c; }

.header-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dialog-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--any-text-primary);
}

/* Risk badge */
.risk-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  width: fit-content;
}

.badge-none { background: #dcfce7; color: #16a34a; }
.badge-low { background: #fef3c7; color: #d97706; }
.badge-medium { background: #fed7aa; color: #ea580c; }
.badge-high { background: #fecaca; color: #dc2626; }
.badge-critical { background: #fca5a5; color: #b91c1c; }

.dialog-content {
  padding: 24px;
}

.operation-info {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.operation-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-md);
}

.badge-label {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

.badge-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.category-tag {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  color: var(--td-state-thinking);
  background: var(--td-state-thinking-bg);
  border-radius: var(--any-radius-sm);
}

.description {
  margin: 0 0 16px;
  font-size: 15px;
  line-height: 1.6;
  color: var(--any-text-secondary);
}

/* Risk explanation */
.risk-explanation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  margin-bottom: 16px;
  border-radius: 8px;
  background: #f9fafb;
}

.risk-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
}

.risk-icon-none { color: #16a34a; }
.risk-icon-low { color: #d97706; }
.risk-icon-medium { color: #ea580c; }
.risk-icon-high { color: #dc2626; }
.risk-icon-critical { color: #b91c1c; }

.risk-text {
  font-size: 13px;
  line-height: 1.5;
  color: #4b5563;
}

.context-section {
  margin-bottom: 16px;
}

.context-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  width: 100%;
  font-size: 14px;
  font-weight: 500;
  color: #00B8D9;
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

/* Remember choice */
.remember-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 8px;
}

.remember-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-input {
  width: 16px;
  height: 16px;
  accent-color: #16a34a;
  cursor: pointer;
}

.checkbox-label {
  font-size: 14px;
  font-weight: 500;
  color: #166534;
}

.remember-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #4ade80;
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
  border-color: #00B8D9;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
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
