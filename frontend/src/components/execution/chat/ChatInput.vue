<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { Send, Paperclip, Mic, X, Image as ImageIcon, FileText, FileSpreadsheet, File } from 'lucide-vue-next'
import type { QuoteInfo, SendMessagePayload, ImageAttachment, FileAttachment, Attachment } from './types'
import { SUPPORTED_DOCUMENT_TYPES } from './types'

interface Props {
  disabled?: boolean
  placeholder?: string
  quote?: QuoteInfo | null
  maxLength?: number
  maxImages?: number
  maxFiles?: number
  maxImageSizeMB?: number
  maxFileSizeMB?: number
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  placeholder: '输入消息...',
  quote: null,
  maxLength: 2000,
  maxImages: 5,
  maxFiles: 5,
  maxImageSizeMB: 10,
  maxFileSizeMB: 20
})

const emit = defineEmits<{
  send: [payload: SendMessagePayload]
  'clear-quote': []
}>()

// Input state
const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const imageInputRef = ref<HTMLInputElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isFocused = ref(false)
const isDragging = ref(false)
const pendingImages = ref<ImageAttachment[]>([])
const pendingFiles = ref<FileAttachment[]>([])
const isProcessingFile = ref(false)

// Supported types
const SUPPORTED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']

// Computed
const canSend = computed(() => {
  const hasContent = inputText.value.trim().length > 0 || pendingImages.value.length > 0 || pendingFiles.value.length > 0
  return hasContent && !props.disabled && !isProcessingFile.value
})

const charCount = computed(() => inputText.value.length)
const isNearLimit = computed(() => charCount.value > props.maxLength * 0.9)
const hasImages = computed(() => pendingImages.value.length > 0)
const hasFiles = computed(() => pendingFiles.value.length > 0)
const hasAttachments = computed(() => hasImages.value || hasFiles.value)
const canAddMoreImages = computed(() => pendingImages.value.length < props.maxImages)
const canAddMoreFiles = computed(() => pendingFiles.value.length < props.maxFiles)

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
  if (!SUPPORTED_IMAGE_TYPES.includes(file.type)) {
    return `不支持的图片格式: ${file.type}`
  }
  const sizeMB = file.size / (1024 * 1024)
  if (sizeMB > props.maxImageSizeMB) {
    return `图片太大: ${sizeMB.toFixed(1)}MB (最大 ${props.maxImageSizeMB}MB)`
  }
  return null
}

/**
 * Validate document file
 */
function validateDocument(file: File): string | null {
  // Check MIME type first, fallback to extension if empty
  const mimeTypeValid = SUPPORTED_DOCUMENT_TYPES.includes(file.type as typeof SUPPORTED_DOCUMENT_TYPES[number])
  
  // Fallback: check by extension if MIME type is empty or not recognized
  let extensionValid = false
  if (!mimeTypeValid) {
    const ext = file.name.split('.').pop()?.toLowerCase()
    const validExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'md']
    extensionValid = ext ? validExtensions.includes(ext) : false
  }
  
  if (!mimeTypeValid && !extensionValid) {
    return `不支持的文档格式: ${file.type || file.name.split('.').pop()}`
  }
  const sizeMB = file.size / (1024 * 1024)
  if (sizeMB > props.maxFileSizeMB) {
    return `文档太大: ${sizeMB.toFixed(1)}MB (最大 ${props.maxFileSizeMB}MB)`
  }
  return null
}

/**
 * Check if file is an image
 */
function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

/**
 * Check if file is a document
 */
function isDocumentFile(file: File): boolean {
  // Check MIME type
  if (SUPPORTED_DOCUMENT_TYPES.includes(file.type as typeof SUPPORTED_DOCUMENT_TYPES[number])) {
    return true
  }
  // Fallback: check by extension
  const ext = file.name.split('.').pop()?.toLowerCase()
  const validExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'csv', 'md']
  return ext ? validExtensions.includes(ext) : false
}

/**
 * Get file icon component based on file type
 */
function getFileIcon(file: File): typeof FileText {
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (ext === 'xlsx' || ext === 'xls' || ext === 'csv') {
    return FileSpreadsheet
  }
  if (ext === 'pdf' || ext === 'doc' || ext === 'docx' || ext === 'txt' || ext === 'md') {
    return FileText
  }
  return File
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

  isProcessingFile.value = true

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
    isProcessingFile.value = false
  }
}

/**
 * Add document to pending list
 */
async function addDocument(file: File) {
  // Validate
  const error = validateDocument(file)
  if (error) {
    console.warn('[ChatInput] Document validation failed:', error)
    return
  }

  if (!canAddMoreFiles.value) {
    console.warn(`[ChatInput] Max files (${props.maxFiles}) reached`)
    return
  }

  isProcessingFile.value = true

  try {
    const dataUrl = await readFileAsDataUrl(file)

    const attachment: FileAttachment = {
      id: `file-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
      file,
      dataUrl
    }

    pendingFiles.value.push(attachment)
    console.log('[ChatInput] Document added:', file.name, `(${(file.size / 1024).toFixed(1)}KB)`)
  } catch (err) {
    console.error('[ChatInput] Failed to process document:', err)
  } finally {
    isProcessingFile.value = false
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
 * Remove file from pending list
 */
function removeFile(id: string) {
  const index = pendingFiles.value.findIndex(f => f.id === id)
  if (index !== -1) {
    pendingFiles.value.splice(index, 1)
  }
}

/**
 * Clear all pending images
 */
function clearImages() {
  pendingImages.value.forEach(img => URL.revokeObjectURL(img.previewUrl))
  pendingImages.value = []
}

/**
 * Clear all pending files
 */
function clearFiles() {
  pendingFiles.value = []
}

/**
 * Clear all attachments
 */
function clearAllAttachments() {
  clearImages()
  clearFiles()
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
 * Handle image input change
 */
function handleImageChange(e: Event) {
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
 * Handle document input change
 */
function handleDocumentChange(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files) return

  for (const file of files) {
    if (canAddMoreFiles.value) {
      addDocument(file)
    }
  }

  // Reset input for re-selection
  input.value = ''
}

/**
 * Open image picker
 */
function handleImageAttachment() {
  imageInputRef.value?.click()
}

/**
 * Open document picker
 */
function handleDocumentAttachment() {
  fileInputRef.value?.click()
}

// ============ Drag & Drop ============

/**
 * Handle drag enter
 */
function handleDragEnter(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = true
}

/**
 * Handle drag leave
 */
function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  // Only set to false if leaving the wrapper
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const x = e.clientX
  const y = e.clientY
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    isDragging.value = false
  }
}

/**
 * Handle drag over
 */
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
}

/**
 * Handle drop
 */
function handleDrop(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (!files) return

  for (const file of files) {
    if (isImageFile(file)) {
      if (canAddMoreImages.value) {
        addImage(file)
      }
    } else if (isDocumentFile(file)) {
      if (canAddMoreFiles.value) {
        addDocument(file)
      }
    } else {
      console.warn('[ChatInput] Unsupported file type:', file.type)
    }
  }
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

  // Convert pending attachments to API format
  const attachments: Attachment[] = [
    // Images
    ...pendingImages.value
      .filter(img => img.dataUrl)
      .map(img => ({
        type: 'image' as const,
        url: img.dataUrl!,
        name: img.file.name
      })),
    // Documents
    ...pendingFiles.value
      .filter(f => f.dataUrl)
      .map(f => ({
        type: 'document' as const,
        url: f.dataUrl!,
        name: f.file.name
      }))
  ]
  
  const payload: SendMessagePayload = {
    content: inputText.value.trim(),
    quote: props.quote || undefined,
    attachments: attachments.length > 0 ? attachments : undefined
  }
  
  emit('send', payload)
  inputText.value = ''
  clearAllAttachments()
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

// Cleanup attachments on unmount
onUnmounted(() => {
  clearAllAttachments()
})

// Expose methods
defineExpose({
  focus,
  clear: () => { inputText.value = ''; clearAllAttachments() }
})
</script>

<template>
  <div 
    :class="['chat-input-wrapper', { disabled, focused: isFocused, dragging: isDragging }]"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <!-- Hidden file inputs -->
    <input
      ref="imageInputRef"
      type="file"
      accept="image/png,image/jpeg,image/gif,image/webp"
      multiple
      class="hidden-file-input"
      @change="handleImageChange"
    >
    <input
      ref="fileInputRef"
      type="file"
      accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.csv,.md"
      multiple
      class="hidden-file-input"
      @change="handleDocumentChange"
    >

    <!-- Drag Overlay -->
    <Transition name="fade">
      <div
        v-if="isDragging"
        class="drag-overlay"
      >
        <div class="drag-content">
          <Paperclip class="w-8 h-8" />
          <span>拖放文件到此处</span>
          <span class="drag-hint">支持图片、PDF、Word、Excel 等</span>
        </div>
      </div>
    </Transition>

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

    <!-- Attachments Preview Area -->
    <Transition name="attachments">
      <div
        v-if="hasAttachments"
        class="attachments-preview"
      >
        <!-- Images Grid -->
        <div
          v-if="hasImages"
          class="images-grid"
        >
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
              class="item-remove"
              title="移除图片"
              @click="removeImage(img.id)"
            >
              <X class="w-3 h-3" />
            </button>
            <span class="image-name">{{ img.file.name }}</span>
          </div>
        </div>

        <!-- Files List -->
        <div
          v-if="hasFiles"
          class="files-list"
        >
          <div
            v-for="f in pendingFiles"
            :key="f.id"
            class="file-item"
          >
            <component
              :is="getFileIcon(f.file)"
              class="file-icon"
            />
            <div class="file-info">
              <span class="file-name">{{ f.file.name }}</span>
              <span class="file-size">{{ (f.file.size / 1024).toFixed(1) }} KB</span>
            </div>
            <button
              class="item-remove"
              title="移除文件"
              @click="removeFile(f.id)"
            >
              <X class="w-3 h-3" />
            </button>
          </div>
        </div>

        <div class="attachments-hint">
          <span v-if="hasImages">{{ pendingImages.length }}/{{ maxImages }} 张图片</span>
          <span v-if="hasImages && hasFiles"> · </span>
          <span v-if="hasFiles">{{ pendingFiles.length }}/{{ maxFiles }} 个文档</span>
          <span> · 支持拖拽上传</span>
        </div>
      </div>
    </Transition>
    
    <!-- Input Area -->
    <div class="input-area">
      <!-- Image Attachment Button -->
      <button
        class="input-btn attachment-btn"
        :class="{ 'has-items': hasImages }"
        title="添加图片 (支持粘贴截图)"
        @click="handleImageAttachment"
      >
        <ImageIcon class="w-4 h-4" />
      </button>

      <!-- Document Attachment Button -->
      <button
        class="input-btn attachment-btn"
        :class="{ 'has-items': hasFiles }"
        title="上传文档 (PDF/Word/Excel)"
        @click="handleDocumentAttachment"
      >
        <Paperclip class="w-4 h-4" />
      </button>
      
      <!-- Text Input -->
      <div class="textarea-wrapper">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          :placeholder="hasAttachments ? '添加描述（可选）...' : placeholder"
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
        :title="isProcessingFile ? '处理文件中...' : '发送'"
        @click="handleSend"
      >
        <Send class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.chat-input-wrapper {
  position: relative;
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

.chat-input-wrapper.dragging {
  border-color: var(--exec-accent, #00D9FF);
  border-style: dashed;
  background: rgba(0, 184, 217, 0.05);
}

/* Hidden file input */
.hidden-file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* Drag Overlay */
.drag-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 184, 217, 0.1);
  border-radius: 16px;
  z-index: 10;
  backdrop-filter: blur(2px);
}

.drag-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--exec-accent, #00D9FF);
  font-weight: 500;
}

.drag-hint {
  font-size: 12px;
  color: var(--any-text-muted);
  font-weight: normal;
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
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

/* Attachments Preview Area */
.attachments-preview {
  padding: 8px 12px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border);
}

.images-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
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

.item-remove {
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

.image-item:hover .item-remove,
.file-item:hover .item-remove {
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

/* Files List */
.files-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
}

.file-icon {
  width: 20px;
  height: 20px;
  color: var(--exec-accent, #00D9FF);
  flex-shrink: 0;
}

.file-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-name {
  font-size: 13px;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: var(--any-text-muted);
}

.file-item .item-remove {
  position: relative;
  top: auto;
  right: auto;
  opacity: 0.6;
  background: var(--any-bg-tertiary);
  color: var(--any-text-muted);
}

.file-item .item-remove:hover {
  opacity: 1;
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.attachments-hint {
  margin-top: 6px;
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Attachments Transition */
.attachments-enter-active,
.attachments-leave-active {
  transition: all 200ms ease;
}

.attachments-enter-from,
.attachments-leave-to {
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

.input-btn.has-items {
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
