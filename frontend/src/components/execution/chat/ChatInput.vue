<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { Send, Paperclip, Mic, X, Image as ImageIcon } from 'lucide-vue-next'
import type { QuoteInfo, SendMessagePayload, ImageAttachment, Attachment } from './types'

interface Props {
  disabled?: boolean
  placeholder?: string
  quote?: QuoteInfo | null
  maxLength?: number
  maxImages?: number
  maxImageSizeMB?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入消息...',
  quote: null,
  maxLength: 2000,
  maxImages: 5,
  maxImageSizeMB: 10
})

const emit = defineEmits<{
  send: [payload: SendMessagePayload]
  'clear-quote': []
}>()

// Input state
const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isFocused = ref(false)
const pendingImages = ref<ImageAttachment[]>([])
const isProcessingImage = ref(false)

// Supported image types
const SUPPORTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

// Computed
const canSend = computed(() => {
  const hasContent = inputText.value.trim().length > 0 || pendingImages.value.length > 0
  return hasContent && !props.disabled && !isProcessingImage.value
})

const charCount = computed(() => inputText.value.length)
const isNearLimit = computed(() => charCount.value > props.maxLength * 0.9)
const hasImages = computed(() => pendingImages.value.length > 0)
const canAddMoreImages = computed(() => pendingImages.value.length < props.maxImages)

// ============ Image Processing ============

/**
 * Read file as base64 data URL
 */
function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Failed to read file'))
    reader.readAsDataURL(file)
  })
}

/**
 * Validate image file
 */
function validateImage(file: File): string | null {
  if (!SUPPORTED_TYPES.includes(file.type)) {
    return `不支持的图片格式: ${file.type}`
  }
  const sizeMB = file.size / (1024 * 1024)
  if (sizeMB > props.maxImageSizeMB) {
    return `图片太大: ${sizeMB.toFixed(1)}MB (最大 ${props.maxImageSizeMB}MB)`
  }
  return null
}

/**
 * Add image to pending list
 */
async function addImage(file: File) {
  // Validate
  const error = validateImage(file)
  if (error) {
    console.warn('[ChatInput] Image validation failed:', error)
    return
  }

  if (!canAddMoreImages.value) {
    console.warn(`[ChatInput] Max images (${props.maxImages}) reached`)
    return
  }

  isProcessingImage.value = true

  try {
    const previewUrl = URL.createObjectURL(file)
    const dataUrl = await readFileAsDataUrl(file)

    const attachment: ImageAttachment = {
      id: `img-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      file,
      previewUrl,
      dataUrl
    }

    pendingImages.value.push(attachment)
    console.log('[ChatInput] Image added:', file.name, `(${(file.size / 1024).toFixed(1)}KB)`)
  } catch (err) {
    console.error('[ChatInput] Failed to process image:', err)
  } finally {
    isProcessingImage.value = false
  }
}

/**
 * Remove image from pending list
 */
function removeImage(id: string) {
  const index = pendingImages.value.findIndex(img => img.id === id)
  if (index !== -1) {
    const img = pendingImages.value[index]
    URL.revokeObjectURL(img.previewUrl)
    pendingImages.value.splice(index, 1)
  }
}

/**
 * Clear all pending images
 */
function clearImages() {
  pendingImages.value.forEach(img => URL.revokeObjectURL(img.previewUrl))
  pendingImages.value = []
}

// ============ Event Handlers ============

/**
 * Handle paste event (for clipboard images)
 */
function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault()
      const file = item.getAsFile()
      if (file) {
        addImage(file)
      }
      return // Only handle first image
    }
  }
}

/**
 * Handle file input change
 */
function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files) return

  for (const file of files) {
    if (canAddMoreImages.value) {
      addImage(file)
    }
  }

  // Reset input for re-selection
  input.value = ''
}

/**
 * Open file picker
 */
function handleAttachment() {
  fileInputRef.value?.click()
}

// Auto-resize textarea
function autoResize() {
  const textarea = textareaRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px'
  }
}

// Handle input
function handleInput() {
  autoResize()
}

// Handle key down
function handleKeyDown(e: KeyboardEvent) {
  // Enter to send (without shift)
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

// Send message
async function handleSend() {
  if (!canSend.value) return

  // Convert pending images to API format
  const attachments: Attachment[] = pendingImages.value
    .filter(img => img.dataUrl)
    .map(img => ({
      type: 'image' as const,
      url: img.dataUrl!,
      name: img.file.name
    }))
  
  const payload: SendMessagePayload = {
    content: inputText.value.trim(),
    quote: props.quote || undefined,
    attachments: attachments.length > 0 ? attachments : undefined
  }
  
  emit('send', payload)
  inputText.value = ''
  clearImages()
  autoResize()
  
  // Clear quote after send
  if (props.quote) {
    emit('clear-quote')
  }
}

// Clear quote
function handleClearQuote() {
  emit('clear-quote')
}

// Voice input (placeholder)
function handleVoice() {
  // TODO: Implement voice input
  console.log('Voice clicked')
}

// Focus input
function focus() {
  textareaRef.value?.focus()
}

// Watch for quote changes to focus input
watch(() => props.quote, (newQuote) => {
  if (newQuote) {
    focus()
  }
})

// Cleanup blob URLs on unmount
onUnmounted(() => {
  clearImages()
})

// Expose methods
defineExpose({
  focus,
  clear: () => { inputText.value = ''; clearImages() }
})
</script>

<template>
  <div :class="['chat-input-wrapper', { disabled, focused: isFocused }]">
    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/png,image/jpeg,image/gif,image/webp"
      multiple
      class="hidden-file-input"
      @change="handleFileChange"
    >

    <!-- Quote Preview -->
    <Transition name="quote">
      <div
        v-if="quote"
        class="quote-preview"
      >
        <div class="quote-content">
          <span class="quote-label">回复</span>
          <span class="quote-text">{{ quote.content.slice(0, 50) }}{{ quote.content.length > 50 ? '...' : '' }}</span>
        </div>
        <button
          class="quote-close"
          @click="handleClearQuote"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </Transition>

    <!-- Image Preview Area -->
    <Transition name="images">
      <div
        v-if="hasImages"
        class="images-preview"
      >
        <div class="images-grid">
          <div
            v-for="img in pendingImages"
            :key="img.id"
            class="image-item"
          >
            <img
              :src="img.previewUrl"
              :alt="img.file.name"
              class="image-thumbnail"
            >
            <button
              class="image-remove"
              title="移除图片"
              @click="removeImage(img.id)"
            >
              <X class="w-3 h-3" />
            </button>
            <span class="image-name">{{ img.file.name }}</span>
          </div>
          <!-- Add more images button -->
          <button
            v-if="canAddMoreImages"
            class="image-add-btn"
            title="添加更多图片"
            @click="handleAttachment"
          >
            <ImageIcon class="w-5 h-5" />
            <span class="add-text">添加</span>
          </button>
        </div>
        <div class="images-hint">
          {{ pendingImages.length }}/{{ maxImages }} 张图片 · 支持粘贴截图
        </div>
      </div>
    </Transition>
    
    <!-- Input Area -->
    <div class="input-area">
      <!-- Attachment Button -->
      <button
        class="input-btn attachment-btn"
        :class="{ 'has-images': hasImages }"
        title="添加图片 (支持粘贴截图)"
        @click="handleAttachment"
      >
        <ImageIcon class="w-4 h-4" />
      </button>
      
      <!-- Text Input -->
      <div class="textarea-wrapper">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          :placeholder="hasImages ? '添加描述（可选）...' : placeholder"
          :disabled="disabled"
          :maxlength="maxLength"
          rows="1"
          class="input-textarea"
          @input="handleInput"
          @keydown="handleKeyDown"
          @paste="handlePaste"
          @focus="isFocused = true"
          @blur="isFocused = false"
        />
        
        <!-- Character count (near limit) -->
        <span
          v-if="isNearLimit"
          :class="['char-count', { warning: charCount >= maxLength }]"
        >
          {{ charCount }}/{{ maxLength }}
        </span>
      </div>
      
      <!-- Voice Button (placeholder) -->
      <button
        class="input-btn voice-btn"
        title="语音输入"
        @click="handleVoice"
      >
        <Mic class="w-4 h-4" />
      </button>
      
      <!-- Send Button -->
      <button
        :class="['send-btn', { active: canSend }]"
        :disabled="!canSend"
        :title="isProcessingImage ? '处理图片中...' : '发送'"
        @click="handleSend"
      >
        <Send class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input-wrapper {
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  transition: all 200ms ease;
}

.chat-input-wrapper.focused {
  border-color: var(--any-border-hover);
  box-shadow: 0 0 0 3px rgba(0, 184, 217, 0.1);
}

.chat-input-wrapper.disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* Hidden file input */
.hidden-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* Quote Preview */
.quote-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border);
  border-radius: 16px 16px 0 0;
}

.quote-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.quote-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--td-state-thinking, #00D9FF);
  text-transform: uppercase;
  flex-shrink: 0;
}

.quote-text {
  font-size: 12px;
  color: var(--any-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quote-close {
  flex-shrink: 0;
  padding: 4px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.quote-close:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Quote Transition */
.quote-enter-active,
.quote-leave-active {
  transition: all 200ms ease;
}

.quote-enter-from,
.quote-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Images Preview Area */
.images-preview {
  padding: 8px 12px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border);
}

.images-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.image-item {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
}

.image-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  opacity: 0;
  transition: opacity 150ms ease;
}

.image-item:hover .image-remove {
  opacity: 1;
}

.image-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 2px 4px;
  font-size: 9px;
  color: white;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  text-overflow: ellipsis;
  white-space: nowrap;
  overflow: hidden;
}

.image-add-btn {
  width: 64px;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: transparent;
  border: 2px dashed var(--any-border);
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.image-add-btn:hover {
  border-color: var(--any-border-hover);
  color: var(--any-text-secondary);
  background: var(--any-bg-hover);
}

.add-text {
  font-size: 10px;
}

.images-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Images Transition */
.images-enter-active,
.images-leave-active {
  transition: all 200ms ease;
}

.images-enter-from,
.images-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* Input Area */
.input-area {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px;
}

/* Input Buttons */
.input-btn {
  flex-shrink: 0;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.input-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-secondary);
}

.input-btn.has-images {
  color: var(--exec-accent, #00D9FF);
}

/* Textarea Wrapper */
.textarea-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-end;
}

.input-textarea {
  width: 100%;
  min-height: 24px;
  max-height: 150px;
  padding: 6px 0;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  color: var(--any-text-primary);
}

.input-textarea::placeholder {
  color: var(--any-text-muted);
}

.input-textarea:disabled {
  cursor: not-allowed;
}

/* Character Count */
.char-count {
  position: absolute;
  right: 4px;
  bottom: 4px;
  font-size: 10px;
  color: var(--any-text-muted);
}

.char-count.warning {
  color: var(--exec-warning, #FFB800);
}

/* Send Button */
.send-btn {
  flex-shrink: 0;
  padding: 8px;
  background: var(--any-bg-tertiary);
  border: none;
  border-radius: 8px;
  color: var(--any-text-muted);
  cursor: not-allowed;
  transition: all 150ms ease;
}

.send-btn.active {
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
  color: white;
  cursor: pointer;
}

.send-btn.active:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 184, 217, 0.4);
}

.send-btn:disabled {
  cursor: not-allowed;
}
</style>
