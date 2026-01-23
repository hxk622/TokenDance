<script setup lang="ts">
import { ref, computed, type Component } from 'vue'
import type { SkillTemplate, TemplateVariable } from '@/api/skills'
import { getCategoryIcon } from '@/components/icons'

const props = defineProps<{
  template: SkillTemplate
  showVariables?: boolean
}>()

const emit = defineEmits<{
  (e: 'use', template: SkillTemplate, variables: Record<string, string>): void
  (e: 'preview', template: SkillTemplate): void
}>()

// 状态
const isExpanded = ref(false)
const variableValues = ref<Record<string, string>>({})

// 分类颜色映射
const categoryColors: Record<string, string> = {
  research: '#00B8D9',
  writing: '#ec4899',
  data: '#14b8a6',
  visualization: '#f59e0b',
  coding: '#10b981',
  document: '#3b82f6',
  other: '#6b7280'
}

// 计算属性
const categoryColor = computed(() => categoryColors[props.template.category] || '#6b7280')
const categoryIconComponent = computed(() => getCategoryIcon(props.template.category))

const hasVariables = computed(() => props.template.variables.length > 0)

const requiredVariables = computed(() =>
  props.template.variables.filter(v => v.required)
)

const optionalVariables = computed(() =>
  props.template.variables.filter(v => !v.required)
)

const isValid = computed(() => {
  return requiredVariables.value.every(v => {
    const value = variableValues.value[v.name]
    return value && value.trim().length > 0
  })
})

const previewPrompt = computed(() => {
  let result = props.template.prompt_template
  for (const [name, value] of Object.entries(variableValues.value)) {
    result = result.replace(new RegExp(`\\{${name}\\}`, 'g'), value || `{${name}}`)
  }
  return result
})

// 方法
const toggleExpand = () => {
  isExpanded.value = !isExpanded.value
}

const handleUse = () => {
  if (!isValid.value && hasVariables.value) {
    isExpanded.value = true
    return
  }
  emit('use', props.template, variableValues.value)
}

const handlePreview = () => {
  emit('preview', props.template)
}

const getVariableType = (variable: TemplateVariable): string => {
  return variable.type || 'text'
}

const initializeDefaults = () => {
  props.template.variables.forEach(v => {
    if (v.default && !variableValues.value[v.name]) {
      variableValues.value[v.name] = v.default
    }
  })
}

// 初始化默认值
initializeDefaults()
</script>

<template>
  <div
    class="template-card"
    :class="{ expanded: isExpanded }"
  >
    <!-- Card Header -->
    <div
      class="card-header"
      @click="toggleExpand"
    >
      <div class="header-left">
        <span class="template-icon">{{ template.icon }}</span>
        <div class="header-info">
          <h3 class="template-name">
            {{ template.name }}
          </h3>
          <span
            class="template-category"
            :style="{
              backgroundColor: categoryColor + '15',
              color: categoryColor
            }"
          >
            <component
              :is="categoryIconComponent"
              class="w-3 h-3 inline-block mr-1"
            />
            {{ template.category }}
          </span>
        </div>
      </div>
      <div class="header-right">
        <span
          v-if="hasVariables"
          class="vars-badge"
        >
          {{ template.variables.length }} 参数
        </span>
        <svg
          class="expand-icon"
          :class="{ rotated: isExpanded }"
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
      </div>
    </div>

    <!-- Card Body -->
    <div class="card-body">
      <p class="template-desc">
        {{ template.description }}
      </p>

      <!-- Tags -->
      <div
        v-if="template.tags.length > 0"
        class="template-tags"
      >
        <span
          v-for="tag in template.tags.slice(0, 5)"
          :key="tag"
          class="tag"
        >
          {{ tag }}
        </span>
      </div>

      <!-- Example -->
      <div
        v-if="template.example_input"
        class="template-example"
      >
        <span class="example-label">示例输入：</span>
        <span class="example-text">{{ template.example_input }}</span>
      </div>
    </div>

    <!-- Expanded Content -->
    <div
      v-if="isExpanded && hasVariables"
      class="card-expanded"
    >
      <!-- Variables Form -->
      <div class="variables-form">
        <h4 class="form-title">
          填写参数
        </h4>

        <!-- Required Variables -->
        <div
          v-if="requiredVariables.length > 0"
          class="variables-group"
        >
          <span class="group-label">必填</span>
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

            <!-- Text Input -->
            <input
              v-if="getVariableType(variable) === 'text'"
              :id="variable.name"
              v-model="variableValues[variable.name]"
              type="text"
              class="field-input"
              :placeholder="variable.placeholder"
            >

            <!-- Textarea -->
            <textarea
              v-else-if="getVariableType(variable) === 'textarea'"
              :id="variable.name"
              v-model="variableValues[variable.name]"
              class="field-textarea"
              :placeholder="variable.placeholder"
              rows="3"
            />

            <!-- Select -->
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

        <!-- Optional Variables -->
        <div
          v-if="optionalVariables.length > 0"
          class="variables-group"
        >
          <span class="group-label">选填</span>
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

            <!-- Text Input -->
            <input
              v-if="getVariableType(variable) === 'text'"
              :id="variable.name"
              v-model="variableValues[variable.name]"
              type="text"
              class="field-input"
              :placeholder="variable.placeholder"
            >

            <!-- Textarea -->
            <textarea
              v-else-if="getVariableType(variable) === 'textarea'"
              :id="variable.name"
              v-model="variableValues[variable.name]"
              class="field-textarea"
              :placeholder="variable.placeholder"
              rows="2"
            />

            <!-- Select -->
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
      <div class="prompt-preview">
        <h4 class="preview-title">
          预览
        </h4>
        <pre class="preview-content">{{ previewPrompt }}</pre>
      </div>
    </div>

    <!-- Card Footer -->
    <div class="card-footer">
      <button
        class="btn-secondary"
        @click="handlePreview"
      >
        <svg
          class="btn-icon"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
          />
        </svg>
        预览
      </button>
      <button
        class="btn-primary"
        :disabled="hasVariables && !isValid && isExpanded"
        @click="handleUse"
      >
        <svg
          class="btn-icon"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M13 10V3L4 14h7v7l9-11h-7z"
          />
        </svg>
        {{ hasVariables && !isExpanded ? '填写参数' : '使用模板' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.template-card {
  @apply bg-white border border-gray-200 rounded-xl overflow-hidden
         transition-all duration-200;
}

.template-card:hover {
  @apply border-gray-300 shadow-sm;
}

.template-card.expanded {
  @apply border-gray-300 shadow-md;
}

/* Header */
.card-header {
  @apply flex items-center justify-between p-4 cursor-pointer
         hover:bg-gray-50 transition-colors;
}

.header-left {
  @apply flex items-center gap-3;
}

.template-icon {
  @apply text-2xl;
}

.header-info {
  @apply flex flex-col gap-1;
}

.template-name {
  @apply text-base font-medium text-gray-900;
}

.template-category {
  @apply text-xs px-2 py-0.5 rounded-full inline-flex items-center gap-1 w-fit;
}

.header-right {
  @apply flex items-center gap-2;
}

.vars-badge {
  @apply text-xs px-2 py-1 bg-gray-100 text-gray-500 rounded-full;
}

.expand-icon {
  @apply w-5 h-5 text-gray-400 transition-transform duration-200;
}

.expand-icon.rotated {
  @apply rotate-180;
}

/* Body */
.card-body {
  @apply px-4 pb-4;
}

.template-desc {
  @apply text-sm text-gray-600 mb-3;
}

.template-tags {
  @apply flex flex-wrap gap-1 mb-3;
}

.tag {
  @apply text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded;
}

.template-example {
  @apply text-xs p-2 bg-gray-50 rounded-lg;
}

.example-label {
  @apply text-gray-400;
}

.example-text {
  @apply text-gray-600;
}

/* Expanded */
.card-expanded {
  @apply px-4 pb-4 border-t border-gray-100 pt-4;
}

/* Variables Form */
.variables-form {
  @apply mb-4;
}

.form-title {
  @apply text-sm font-medium text-gray-700 mb-3;
}

.variables-group {
  @apply mb-4;
}

.group-label {
  @apply text-xs text-gray-400 uppercase tracking-wider mb-2 block;
}

.variable-field {
  @apply mb-3;
}

.field-label {
  @apply block text-sm text-gray-600 mb-1;
}

.required-mark {
  @apply text-red-500 ml-0.5;
}

.field-input,
.field-textarea,
.field-select {
  @apply w-full px-3 py-2 text-sm
         bg-gray-50 border border-gray-200 rounded-lg
         focus:outline-none focus:border-gray-400 focus:bg-white
         transition-colors;
}

.field-textarea {
  @apply resize-none;
}

/* Preview */
.prompt-preview {
  @apply bg-gray-50 rounded-lg p-3;
}

.preview-title {
  @apply text-xs text-gray-400 uppercase tracking-wider mb-2;
}

.preview-content {
  @apply text-sm text-gray-700 whitespace-pre-wrap font-mono;
  max-height: 200px;
  overflow-y: auto;
}

/* Footer */
.card-footer {
  @apply flex items-center justify-end gap-2 px-4 py-3 bg-gray-50 border-t border-gray-100;
}

.btn-secondary,
.btn-primary {
  @apply inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg
         transition-colors;
}

.btn-secondary {
  @apply text-gray-600 hover:text-gray-900 hover:bg-gray-100;
}

.btn-primary {
  @apply bg-gray-900 text-white hover:bg-gray-800
         disabled:bg-gray-300 disabled:cursor-not-allowed;
}

.btn-icon {
  @apply w-4 h-4;
}
</style>
