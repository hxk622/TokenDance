<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ArrowRight, Edit3 } from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'
import ChatRadioGroup from './ChatRadioGroup.vue'
import ChatCheckboxGroup from './ChatCheckboxGroup.vue'
import ChatTagSelector from './ChatTagSelector.vue'
import ChatCollapsible from './ChatCollapsible.vue'
import type { FormField, FormGroup, FormFieldOption } from './types'

interface Props {
  // Form title (optional header)
  title?: string
  description?: string
  
  // Form fields (flat list)
  fields?: FormField[]
  
  // Form groups (collapsible sections)
  groups?: FormGroup[]
  
  // Is the form interactive or read-only
  interactive?: boolean
  
  // Has the form been submitted
  submitted?: boolean
  
  // Submitted values (for read-only display)
  submittedValues?: Record<string, unknown>
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  fields: () => [],
  groups: () => [],
  interactive: true,
  submitted: false,
  submittedValues: () => ({})
})

const emit = defineEmits<{
  submit: [values: Record<string, unknown>]
  edit: []
}>()

// Form values state
const formValues = ref<Record<string, unknown>>({})

// Initialize form values from fields
function initFormValues() {
  const values: Record<string, unknown> = {}
  
  // From flat fields
  for (const field of props.fields) {
    values[field.id] = field.value ?? (field.type === 'checkbox' || field.type === 'tags' ? [] : '')
  }
  
  // From groups
  for (const group of props.groups) {
    for (const field of group.fields) {
      values[field.id] = field.value ?? (field.type === 'checkbox' || field.type === 'tags' ? [] : '')
    }
  }
  
  formValues.value = values
}

// Initialize on mount
initFormValues()

// Watch for field changes
watch(() => [props.fields, props.groups], initFormValues, { deep: true })

// Get field options
function getOptions(field: FormField): FormFieldOption[] {
  return field.options || []
}

// Handle submit
function handleSubmit() {
  emit('submit', { ...formValues.value })
}

// Handle edit (when in submitted state)
function handleEdit() {
  emit('edit')
}

// Get summary of submitted values
const submittedSummary = computed(() => {
  if (!props.submitted) return ''
  
  const values = props.submittedValues
  const parts: string[] = []
  
  // Collect all fields
  const allFields = [
    ...props.fields,
    ...props.groups.flatMap(g => g.fields)
  ]
  
  for (const field of allFields) {
    const value = values[field.id]
    if (!value) continue
    
    if (Array.isArray(value) && value.length > 0) {
      // Multiple selection - find labels
      const labels = value.map(v => {
        const opt = field.options?.find(o => o.value === v)
        return opt?.label || v
      })
      parts.push(`${field.label}: ${labels.join(', ')}`)
    } else if (typeof value === 'string' && value) {
      // Single value - find label
      const opt = field.options?.find(o => o.value === value)
      parts.push(`${field.label}: ${opt?.label || value}`)
    }
  }
  
  return parts.join(' · ')
})

// Check if can submit
const canSubmit = computed(() => {
  // Check required fields
  const allFields = [
    ...props.fields,
    ...props.groups.flatMap(g => g.fields)
  ]
  
  for (const field of allFields) {
    if (!field.required) continue
    
    const value = formValues.value[field.id]
    if (Array.isArray(value)) {
      if (value.length === 0) return false
    } else if (!value) {
      return false
    }
  }
  
  return true
})
</script>

<template>
  <div :class="['chat-form-message', { submitted, interactive }]">
    <!-- Header -->
    <div
      v-if="title"
      class="form-header"
    >
      <h4 class="form-title">
        {{ title }}
      </h4>
      <p
        v-if="description"
        class="form-desc"
      >
        {{ description }}
      </p>
    </div>
    
    <!-- Submitted State (Read-only summary) -->
    <div
      v-if="submitted"
      class="submitted-summary"
    >
      <p class="summary-text">
        {{ submittedSummary || '已提交' }}
      </p>
      <button
        class="edit-btn"
        @click="handleEdit"
      >
        <Edit3 class="w-3.5 h-3.5" />
        <span>修改</span>
      </button>
    </div>
    
    <!-- Interactive Form -->
    <template v-else>
      <!-- Flat Fields -->
      <div
        v-if="fields.length > 0"
        class="form-fields"
      >
        <template
          v-for="field in fields"
          :key="field.id"
        >
          <ChatRadioGroup
            v-if="field.type === 'radio'"
            v-model="formValues[field.id] as string"
            :options="getOptions(field)"
            :label="field.label"
            :description="field.description"
            :disabled="!interactive"
            :readonly="!interactive"
          />
          
          <ChatCheckboxGroup
            v-else-if="field.type === 'checkbox'"
            v-model="formValues[field.id] as string[]"
            :options="getOptions(field)"
            :label="field.label"
            :description="field.description"
            :disabled="!interactive"
            :readonly="!interactive"
          />
          
          <ChatTagSelector
            v-else-if="field.type === 'tags'"
            v-model="formValues[field.id] as string[]"
            :options="getOptions(field)"
            :label="field.label"
            :description="field.description"
            :disabled="!interactive"
            :readonly="!interactive"
          />
          
          <!-- Text input (basic) -->
          <div
            v-else-if="field.type === 'input' || field.type === 'textarea'"
            class="text-field"
          >
            <label class="field-label">{{ field.label }}</label>
            <input
              v-if="field.type === 'input'"
              :value="formValues[field.id] as string"
              type="text"
              :placeholder="field.placeholder"
              :disabled="!interactive"
              class="text-input"
              @input="(e) => formValues[field.id] = (e.target as HTMLInputElement).value"
            >
            <textarea
              v-else
              :value="formValues[field.id] as string"
              :placeholder="field.placeholder"
              :disabled="!interactive"
              rows="3"
              class="text-textarea"
              @input="(e) => formValues[field.id] = (e.target as HTMLTextAreaElement).value"
            />
          </div>
        </template>
      </div>
      
      <!-- Grouped Fields (Collapsible) -->
      <div
        v-if="groups.length > 0"
        class="form-groups"
      >
        <ChatCollapsible
          v-for="group in groups"
          :key="group.id"
          :title="group.title"
          :description="group.description"
          :default-open="!group.collapsed"
        >
          <div class="group-fields">
            <template
              v-for="field in group.fields"
              :key="field.id"
            >
              <ChatRadioGroup
                v-if="field.type === 'radio'"
                v-model="formValues[field.id] as string"
                :options="getOptions(field)"
                :label="field.label"
                :description="field.description"
                :disabled="!interactive"
              />
              
              <ChatCheckboxGroup
                v-else-if="field.type === 'checkbox'"
                v-model="formValues[field.id] as string[]"
                :options="getOptions(field)"
                :label="field.label"
                :description="field.description"
                :disabled="!interactive"
              />
              
              <ChatTagSelector
                v-else-if="field.type === 'tags'"
                v-model="formValues[field.id] as string[]"
                :options="getOptions(field)"
                :label="field.label"
                :description="field.description"
                :disabled="!interactive"
              />
            </template>
          </div>
        </ChatCollapsible>
      </div>
      
      <!-- Submit Button -->
      <div
        v-if="interactive"
        class="form-actions"
      >
        <AnyButton
          variant="primary"
          size="sm"
          :icon="ArrowRight"
          :disabled="!canSubmit"
          @click="handleSubmit"
        >
          确认
        </AnyButton>
      </div>
    </template>
  </div>
</template>

<style scoped>
.chat-form-message {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.form-desc {
  font-size: 13px;
  color: var(--any-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* Submitted Summary */
.submitted-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  gap: 12px;
}

.summary-text {
  font-size: 13px;
  color: var(--any-text-secondary);
  margin: 0;
  flex: 1;
  line-height: 1.4;
}

.edit-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--any-border);
  border-radius: 6px;
  font-size: 12px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
  flex-shrink: 0;
}

.edit-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

/* Form Fields */
.form-fields,
.group-fields {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-groups {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Text Field */
.text-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.text-input,
.text-textarea {
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  font-family: inherit;
  font-size: 14px;
  color: var(--any-text-primary);
  transition: all 150ms ease;
}

.text-input:focus,
.text-textarea:focus {
  outline: none;
  border-color: var(--any-border-hover);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.text-input::placeholder,
.text-textarea::placeholder {
  color: var(--any-text-muted);
}

.text-textarea {
  resize: vertical;
  min-height: 80px;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid var(--any-border);
}
</style>
