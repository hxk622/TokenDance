<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import AnyModal from '@/components/common/AnyModal.vue'
import AnyButton from '@/components/common/AnyButton.vue'
import OptionGroup from '@/components/common/OptionGroup.vue'
import type { Option } from '@/components/common/OptionGroup.vue'
import { 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight,
  Edit3,
  Sparkles
} from 'lucide-vue-next'

// Props
interface Props {
  modelValue: boolean
  userInput: string
  isComplete: boolean
  confidenceScore: number
  missingInfo: string[]
  suggestedQuestions: string[]
  reasoning?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  proceed: [updatedInput?: string]
  cancel: []
}>()

// State
const selectedQuestions = ref<string[]>([])
const editedInput = ref('')
const isEditing = ref(false)

// Reset state when dialog opens
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    selectedQuestions.value = []
    editedInput.value = props.userInput
    isEditing.value = false
  }
})

// Convert suggested questions to options
const questionOptions = computed<Option[]>(() => {
  return props.suggestedQuestions.map((q, index) => ({
    label: q,
    value: q
  }))
})

// Confidence display
const confidenceDisplay = computed(() => {
  const score = props.confidenceScore
  if (score >= 0.8) return { label: '高', color: '#00FF88' }
  if (score >= 0.5) return { label: '中', color: '#FFB800' }
  return { label: '低', color: '#FF3B30' }
})

// Handle proceed
const handleProceed = () => {
  // Build updated input with selected questions
  let finalInput = isEditing.value ? editedInput.value : props.userInput
  
  if (selectedQuestions.value.length > 0) {
    // Append selected questions as context
    const context = selectedQuestions.value.join(' | ')
    finalInput = `${finalInput}\n\n[补充信息: ${context}]`
  }
  
  emit('proceed', finalInput)
  emit('update:modelValue', false)
}

// Handle cancel
const handleCancel = () => {
  emit('cancel')
  emit('update:modelValue', false)
}

// Toggle edit mode
const toggleEdit = () => {
  isEditing.value = !isEditing.value
}
</script>

<template>
  <AnyModal
    :model-value="modelValue"
    :title="isComplete ? '任务确认' : '需要更多信息'"
    width="560px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <!-- Loading state -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <Sparkles
        class="loading-icon"
        :size="32"
      />
      <p class="loading-text">
        正在分析您的请求...
      </p>
    </div>

    <!-- Content -->
    <div
      v-else
      class="preflight-content"
    >
      <!-- Status indicator -->
      <div
        class="status-indicator"
        :class="{ complete: isComplete, incomplete: !isComplete }"
      >
        <CheckCircle2
          v-if="isComplete"
          :size="24"
        />
        <AlertCircle
          v-else
          :size="24"
        />
        <div class="status-text">
          <span class="status-label">
            {{ isComplete ? '任务清晰' : '信息不完整' }}
          </span>
          <span class="confidence">
            置信度: 
            <span :style="{ color: confidenceDisplay.color }">
              {{ (confidenceScore * 100).toFixed(0) }}%
            </span>
          </span>
        </div>
      </div>

      <!-- Reasoning -->
      <p
        v-if="reasoning"
        class="reasoning"
      >
        {{ reasoning }}
      </p>

      <!-- User input display/edit -->
      <div class="user-input-section">
        <div class="section-header">
          <h4>您的输入</h4>
          <button
            class="edit-toggle"
            @click="toggleEdit"
          >
            <Edit3 :size="14" />
            {{ isEditing ? '完成' : '编辑' }}
          </button>
        </div>
        <textarea
          v-if="isEditing"
          v-model="editedInput"
          class="input-editor"
          rows="3"
        />
        <p
          v-else
          class="input-display"
        >
          {{ userInput }}
        </p>
      </div>

      <!-- Missing info -->
      <div
        v-if="missingInfo.length > 0"
        class="missing-info-section"
      >
        <h4>缺少的信息</h4>
        <ul class="missing-list">
          <li
            v-for="(info, index) in missingInfo"
            :key="index"
          >
            {{ info }}
          </li>
        </ul>
      </div>

      <!-- Suggested questions -->
      <div
        v-if="suggestedQuestions.length > 0"
        class="questions-section"
      >
        <h4>建议选择（可多选）</h4>
        <OptionGroup
          v-model="selectedQuestions"
          :options="questionOptions"
          mode="multiple"
        />
      </div>
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="dialog-footer">
        <AnyButton
          variant="ghost"
          @click="handleCancel"
        >
          取消
        </AnyButton>
        <AnyButton
          variant="primary"
          :icon="ArrowRight"
          :disabled="loading"
          @click="handleProceed"
        >
          {{ isComplete ? '继续执行' : '仍然执行' }}
        </AnyButton>
      </div>
    </template>
  </AnyModal>
</template>

<style scoped>
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  gap: 16px;
}

.loading-icon {
  color: #00B8D9;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.95); }
}

.loading-text {
  color: var(--any-text-secondary);
  font-size: 14px;
}

.preflight-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
  background: var(--any-bg-tertiary);
}

.status-indicator.complete {
  color: #00FF88;
}

.status-indicator.incomplete {
  color: #FFB800;
}

.status-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.status-label {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.confidence {
  font-size: 12px;
  color: var(--any-text-secondary);
}

.reasoning {
  font-size: 14px;
  color: var(--any-text-secondary);
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border-radius: 8px;
  margin: 0;
}

.user-input-section,
.missing-info-section,
.questions-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-tertiary);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.edit-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #00B8D9;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 150ms ease;
}

.edit-toggle:hover {
  background: var(--any-bg-hover);
}

.input-display {
  font-size: 14px;
  color: var(--any-text-primary);
  padding: 12px;
  background: var(--any-bg-secondary);
  border-radius: 8px;
  margin: 0;
  white-space: pre-wrap;
}

.input-editor {
  font-size: 14px;
  color: var(--any-text-primary);
  padding: 12px;
  background: var(--any-bg-secondary);
  border-radius: 8px;
  border: 1.5px solid var(--any-border);
  resize: vertical;
  min-height: 80px;
  font-family: inherit;
}

.input-editor:focus {
  outline: none;
  border-color: #00B8D9;
}

.missing-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.missing-list li {
  font-size: 14px;
  color: var(--any-text-secondary);
  padding: 8px 12px;
  background: rgba(255, 184, 0, 0.1);
  border-radius: 6px;
  border-left: 3px solid #FFB800;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
