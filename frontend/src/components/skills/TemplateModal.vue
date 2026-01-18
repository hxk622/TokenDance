<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { SkillTemplate, TemplateVariable } from '@/api/skills'
import { skillsApi } from '@/api/skills'

const props = defineProps<{
  templateId: string
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', prompt: string, skillId: string): void
}>()

// 状态
const loading = ref(true)
const template = ref<SkillTemplate | null>(null)
const variableValues = ref<Record<string, string>>({})
const submitting = ref(false)

// 计算属性
const requiredVariables = computed(() =>
  template.value?.variables.filter(v => v.required) || []
)

const optionalVariables = computed(() =>
  template.value?.variables.filter(v => !v.required) || []
)

const isValid = computed(() => {
  if (!template.value) return false
  return requiredVariables.value.every(v => {
    const value = variableValues.value[v.name]
    return value && value.trim().length > 0
  })
})

const previewPrompt = computed(() => {
  if (!template.value) return ''
  let result = template.value.prompt_template
  for (const [name, value] of Object.entries(variableValues.value)) {
    result = result.replace(new RegExp(`\\{${name}\\}`, 'g'), value || `{${name}}`)
  }
  return result
})

// 方法
const loadTemplate = async () => {
  try {
    loading.value = true
    template.value = await skillsApi.getTemplate(props.templateId)

    // 初始化默认值
    template.value.variables.forEach(v => {
      if (v.default) {
        variableValues.value[v.name] = v.default
      }
    })
  } catch (e) {
    console.error('Failed to load template:', e)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!isValid.value || !template.value) return

  try {
    submitting.value = true
    const result = await skillsApi.renderTemplate(props.templateId, variableValues.value)
    emit('submit', result.rendered_prompt, result.skill_id)
  } catch (e) {
    console.error('Failed to render template:', e)
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  emit('close')
}

const getVariableType = (variable: TemplateVariable): string => {
  return variable.type || 'text'
}

// 监听 visible 变化
onMounted(() => {
  if (props.visible) {
    loadTemplate()
  }
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="modal-overlay"
      @click.self="handleClose"
    >
      <div class="modal-container">
        <!-- Loading -->
        <div
          v-if="loading"
          class="modal-loading"
        >
          <div class="loading-spinner" />
          <p>加载模板...</p>
        </div>

        <!-- Content -->
        <template v-else-if="template">
          <!-- Header -->
          <div class="modal-header">
            <div class="header-info">
              <span class="template-icon">{{ template.icon }}</span>
              <div>
                <h2 class="modal-title">
                  {{ template.name }}
                </h2>
                <p class="modal-desc">
                  {{ template.description }}
                </p>
              </div>
            </div>
            <button
              class="close-btn"
              @click="handleClose"
            >
              <svg
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
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <!-- Variables Form -->
            <div
              v-if="template.variables.length > 0"
              class="variables-section"
            >
              <h3 class="section-title">
                填写参数
              </h3>

              <!-- Required -->
              <div
                v-if="requiredVariables.length > 0"
                class="variables-group"
              >
                <span class="group-label">必填参数</span>
                <div
                  v-for="variable in requiredVariables"
                  :key="variable.name"
                  class="variable-field"
                >
                  <label
                    :for="variable.name"
                    class="field-label"
                  >
                    {{ variable.label }}
                    <span class="required-mark">*</span>
                  </label>

                  <input
                    v-if="getVariableType(variable) === 'text'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    type="text"
                    class="field-input"
                    :placeholder="variable.placeholder"
                  >

                  <textarea
                    v-else-if="getVariableType(variable) === 'textarea'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    class="field-textarea"
                    :placeholder="variable.placeholder"
                    rows="3"
                  />

                  <select
                    v-else-if="getVariableType(variable) === 'select'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    class="field-select"
                  >
                    <option
                      value=""
                      disabled
                    >
                      请选择...
                    </option>
                    <option
                      v-for="opt in variable.options"
                      :key="opt.value"
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Optional -->
              <div
                v-if="optionalVariables.length > 0"
                class="variables-group"
              >
                <span class="group-label">选填参数</span>
                <div
                  v-for="variable in optionalVariables"
                  :key="variable.name"
                  class="variable-field"
                >
                  <label
                    :for="variable.name"
                    class="field-label"
                  >
                    {{ variable.label }}
                  </label>

                  <input
                    v-if="getVariableType(variable) === 'text'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    type="text"
                    class="field-input"
                    :placeholder="variable.placeholder"
                  >

                  <textarea
                    v-else-if="getVariableType(variable) === 'textarea'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    class="field-textarea"
                    :placeholder="variable.placeholder"
                    rows="2"
                  />

                  <select
                    v-else-if="getVariableType(variable) === 'select'"
                    :id="variable.name"
                    v-model="variableValues[variable.name]"
                    class="field-select"
                  >
                    <option value="">
                      请选择...
                    </option>
                    <option
                      v-for="opt in variable.options"
                      :key="opt.value"
                      :value="opt.value"
                    >
                      {{ opt.label }}
                    </option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Preview -->
            <div class="preview-section">
              <h3 class="section-title">
                提示词预览
              </h3>
              <pre class="preview-content">{{ previewPrompt }}</pre>
            </div>

            <!-- Example -->
            <div
              v-if="template.example_output"
              class="example-section"
            >
              <h3 class="section-title">
                示例输出
              </h3>
              <pre class="example-content">{{ template.example_output }}</pre>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <button
              class="btn-secondary"
              @click="handleClose"
            >
              取消
            </button>
            <button
              class="btn-primary"
              :disabled="!isValid || submitting"
              @click="handleSubmit"
            >
              <span v-if="submitting">处理中...</span>
              <span v-else>开始任务</span>
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  @apply fixed inset-0 z-50 flex items-center justify-center
         bg-black/50 backdrop-blur-sm;
}

.modal-container {
  @apply w-full max-w-2xl max-h-[90vh] bg-white rounded-2xl shadow-2xl
         flex flex-col overflow-hidden;
  margin: 1rem;
}

/* Loading */
.modal-loading {
  @apply flex flex-col items-center justify-center py-20 text-gray-500;
}

.loading-spinner {
  @apply w-8 h-8 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin mb-4;
}

/* Header */
.modal-header {
  @apply flex items-start justify-between p-6 border-b border-gray-100;
}

.header-info {
  @apply flex items-start gap-4;
}

.template-icon {
  @apply text-3xl;
}

.modal-title {
  @apply text-xl font-semibold text-gray-900 mb-1;
}

.modal-desc {
  @apply text-sm text-gray-500;
}

.close-btn {
  @apply p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg
         transition-colors;
}

.close-btn svg {
  @apply w-5 h-5;
}

/* Body */
.modal-body {
  @apply flex-1 overflow-y-auto p-6 space-y-6;
}

.section-title {
  @apply text-sm font-medium text-gray-700 mb-3;
}

/* Variables */
.variables-section {
  @apply space-y-4;
}

.variables-group {
  @apply space-y-3;
}

.group-label {
  @apply text-xs text-gray-400 uppercase tracking-wider block mb-2;
}

.variable-field {
  @apply space-y-1;
}

.field-label {
  @apply block text-sm text-gray-600;
}

.required-mark {
  @apply text-red-500 ml-0.5;
}

.field-input,
.field-textarea,
.field-select {
  @apply w-full px-4 py-2.5 text-sm
         bg-gray-50 border border-gray-200 rounded-lg
         focus:outline-none focus:border-gray-400 focus:bg-white
         transition-colors;
}

.field-textarea {
  @apply resize-none;
}

/* Preview */
.preview-section {
  @apply bg-gray-50 rounded-xl p-4;
}

.preview-content {
  @apply text-sm text-gray-700 whitespace-pre-wrap font-mono
         max-h-48 overflow-y-auto;
}

/* Example */
.example-section {
  @apply bg-blue-50 rounded-xl p-4;
}

.example-content {
  @apply text-sm text-blue-700 whitespace-pre-wrap
         max-h-32 overflow-y-auto;
}

/* Footer */
.modal-footer {
  @apply flex items-center justify-end gap-3 p-6 border-t border-gray-100 bg-gray-50;
}

.btn-secondary,
.btn-primary {
  @apply px-5 py-2.5 text-sm font-medium rounded-lg transition-colors;
}

.btn-secondary {
  @apply text-gray-600 hover:text-gray-900 hover:bg-gray-200;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800
         disabled:bg-gray-300 disabled:cursor-not-allowed;
}
</style>
