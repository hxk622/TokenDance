<script setup lang="ts">
import { ref, computed } from 'vue'
import OptionGroup from '@/components/common/OptionGroup.vue'
import type { Option } from '@/components/common/OptionGroup.vue'
import AnyButton from '@/components/common/AnyButton.vue'
import { 
  AlertCircle, 
  CheckCircle2, 
  ArrowRight,
  Edit3,
  Sparkles
} from 'lucide-vue-next'

// Props
interface Props {
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
  proceed: [updatedInput?: string]
  cancel: []
}>()

// State
const selectedQuestions = ref<string[]>([])
const editedInput = ref(props.userInput)
const isEditing = ref(false)

// Convert suggested questions to options
const questionOptions = computed<Option[]>(() => {
  return props.suggestedQuestions.map((q) => ({
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
}

// Handle cancel
const handleCancel = () => {
  emit('cancel')
}

// Toggle edit mode
const toggleEdit = () => {
  isEditing.value = !isEditing.value
}
</script>

<template>
  <div class="info-collection-stage">
    <div class="stage-container">
      <!-- Loading state -->
      <div
        v-if="loading"
        class="loading-state"
      >
        <Sparkles
          class="loading-icon"
          :size="48"
        />
        <h2 class="loading-title">
          正在分析您的任务...
        </h2>
        <p class="loading-text">
          TokenDance 正在理解您的需求
        </p>
      </div>

      <!-- Content -->
      <div
        v-else
        class="collection-content"
      >
        <!-- Header -->
        <div class="stage-header">
          <h1 class="stage-title">
            {{ isComplete ? '任务确认' : '需要补充一些信息' }}
          </h1>
          <p class="stage-subtitle">
            {{ isComplete ? '我们已经准备好开始执行' : '为了更好地完成任务，请补充以下信息' }}
          </p>
        </div>

        <!-- Status indicator -->
        <div
          class="status-card"
          :class="{ complete: isComplete, incomplete: !isComplete }"
        >
          <div class="status-icon">
            <CheckCircle2
              v-if="isComplete"
              :size="32"
            />
            <AlertCircle
              v-else
              :size="32"
            />
          </div>
          <div class="status-content">
            <div class="status-label">
              {{ isComplete ? '任务清晰可执行' : '信息不完整' }}
            </div>
            <div class="confidence-bar">
              <span class="confidence-label">置信度</span>
              <div class="confidence-progress">
                <div
                  class="confidence-fill"
                  :style="{ 
                    width: `${confidenceScore * 100}%`,
                    background: confidenceDisplay.color
                  }"
                />
              </div>
              <span 
                class="confidence-value"
                :style="{ color: confidenceDisplay.color }"
              >
                {{ (confidenceScore * 100).toFixed(0) }}%
              </span>
            </div>
            <p
              v-if="reasoning"
              class="reasoning"
            >
              {{ reasoning }}
            </p>
          </div>
        </div>

        <!-- User input display/edit -->
        <div class="input-section">
          <div class="section-header">
            <h3>您的任务</h3>
            <button
              class="edit-toggle"
              @click="toggleEdit"
            >
              <Edit3 :size="16" />
              {{ isEditing ? '完成编辑' : '编辑' }}
            </button>
          </div>
          <textarea
            v-if="isEditing"
            v-model="editedInput"
            class="input-editor"
            rows="4"
          />
          <div
            v-else
            class="input-display"
          >
            {{ userInput }}
          </div>
        </div>

        <!-- Missing info -->
        <div
          v-if="missingInfo.length > 0"
          class="missing-section"
        >
          <h3>缺少的关键信息</h3>
          <ul class="missing-list">
            <li
              v-for="(info, index) in missingInfo"
              :key="index"
              class="missing-item"
            >
              <div class="missing-bullet" />
              <span>{{ info }}</span>
            </li>
          </ul>
        </div>

        <!-- Suggested questions -->
        <div
          v-if="suggestedQuestions.length > 0"
          class="questions-section"
        >
          <h3>建议补充（可多选）</h3>
          <OptionGroup
            v-model="selectedQuestions"
            :options="questionOptions"
            mode="multiple"
          />
        </div>

        <!-- Actions -->
        <div class="actions">
          <AnyButton
            variant="ghost"
            size="lg"
            @click="handleCancel"
          >
            返回修改
          </AnyButton>
          <AnyButton
            variant="primary"
            size="lg"
            :icon="ArrowRight"
            @click="handleProceed"
          >
            {{ isComplete ? '开始执行' : '继续执行' }}
          </AnyButton>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.info-collection-stage {
  position: fixed;
  inset: 0;
  background: var(--any-bg-primary);
  z-index: 100;
  overflow-y: auto;
}

.stage-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 24px;
}

/* Loading state */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  text-align: center;
}

.loading-icon {
  color: #6366f1;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { 
    opacity: 1; 
    transform: scale(1);
    filter: drop-shadow(0 0 20px rgba(99, 102, 241, 0.3));
  }
  50% { 
    opacity: 0.7; 
    transform: scale(0.95);
    filter: drop-shadow(0 0 30px rgba(99, 102, 241, 0.5));
  }
}

.loading-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.loading-text {
  font-size: 16px;
  color: var(--any-text-secondary);
  margin: 0;
}

/* Content */
.collection-content {
  width: 100%;
  max-width: 800px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.stage-header {
  text-align: center;
}

.stage-title {
  font-size: 32px;
  font-weight: 700;
  color: var(--any-text-primary);
  margin: 0 0 12px 0;
}

.stage-subtitle {
  font-size: 18px;
  color: var(--any-text-secondary);
  margin: 0;
}

/* Status card */
.status-card {
  display: flex;
  gap: 20px;
  padding: 24px;
  border-radius: 16px;
  background: var(--any-bg-secondary);
  border: 2px solid transparent;
  transition: all 300ms ease;
}

.status-card.complete {
  border-color: #00FF88;
  background: rgba(0, 255, 136, 0.05);
}

.status-card.incomplete {
  border-color: #FFB800;
  background: rgba(255, 184, 0, 0.05);
}

.status-icon {
  flex-shrink: 0;
}

.status-card.complete .status-icon {
  color: #00FF88;
}

.status-card.incomplete .status-icon {
  color: #FFB800;
}

.status-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-label {
  font-size: 20px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.confidence-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.confidence-label {
  font-size: 14px;
  color: var(--any-text-tertiary);
  min-width: 60px;
}

.confidence-progress {
  flex: 1;
  height: 8px;
  background: var(--any-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  transition: width 600ms ease, background 300ms ease;
  border-radius: 4px;
}

.confidence-value {
  font-size: 16px;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
}

.reasoning {
  font-size: 15px;
  color: var(--any-text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Sections */
.input-section,
.missing-section,
.questions-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.edit-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #6366f1;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 8px;
  transition: background 150ms ease;
}

.edit-toggle:hover {
  background: var(--any-bg-hover);
}

.input-display {
  font-size: 16px;
  color: var(--any-text-primary);
  padding: 16px;
  background: var(--any-bg-secondary);
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.input-editor {
  font-size: 16px;
  color: var(--any-text-primary);
  padding: 16px;
  background: var(--any-bg-secondary);
  border-radius: 12px;
  border: 2px solid var(--any-border);
  resize: vertical;
  min-height: 120px;
  font-family: inherit;
  line-height: 1.6;
}

.input-editor:focus {
  outline: none;
  border-color: #6366f1;
}

.missing-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.missing-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 15px;
  color: var(--any-text-primary);
  padding: 14px 16px;
  background: rgba(255, 184, 0, 0.08);
  border-radius: 10px;
  border-left: 3px solid #FFB800;
}

.missing-bullet {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #FFB800;
  margin-top: 7px;
  flex-shrink: 0;
}

/* Actions */
.actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 16px;
}

/* Responsive */
@media (max-width: 768px) {
  .stage-title {
    font-size: 24px;
  }
  
  .stage-subtitle {
    font-size: 16px;
  }
  
  .status-card {
    flex-direction: column;
    gap: 16px;
  }
  
  .actions {
    flex-direction: column-reverse;
  }
}
</style>
