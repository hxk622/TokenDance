<script setup lang="ts">
/**
 * DocumentUploader - 文档上传组件
 * 
 * 支持拖拽上传、多文件选择，并显示上传进度
 */
import { ref, computed } from 'vue'
import {
  Upload,
  File,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader,
} from 'lucide-vue-next'

// Types
interface UploadFile {
  id: string
  file: File
  name: string
  size: number
  type: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  progress: number
  error?: string
}

// Props
const props = withDefaults(defineProps<{
  accept?: string
  maxSize?: number  // MB
  maxFiles?: number
  disabled?: boolean
}>(), {
  accept: '.pdf,.txt,.md,.docx',
  maxSize: 50,
  maxFiles: 5,
  disabled: false,
})

// Emits
const emit = defineEmits<{
  (e: 'upload', files: File[]): void
  (e: 'remove', fileId: string): void
  (e: 'upload-complete', results: any[]): void
}>()

// State
const files = ref<UploadFile[]>([])
const isDragging = ref(false)

// Computed
const canAddMore = computed(() => files.value.length < props.maxFiles)

const uploadingSummary = computed(() => {
  const total = files.value.length
  const completed = files.value.filter(f => f.status === 'success').length
  const failed = files.value.filter(f => f.status === 'error').length
  return { total, completed, failed }
})

// Methods
const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  
  if (props.disabled) return
  
  const droppedFiles = Array.from(e.dataTransfer?.files || [])
  addFiles(droppedFiles)
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  if (!props.disabled) {
    isDragging.value = true
  }
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  const selectedFiles = Array.from(input.files || [])
  addFiles(selectedFiles)
  input.value = '' // Reset input
}

const addFiles = (newFiles: File[]) => {
  const maxSizeBytes = props.maxSize * 1024 * 1024
  
  for (const file of newFiles) {
    if (!canAddMore.value) {
      break
    }
    
    // 验证文件大小
    if (file.size > maxSizeBytes) {
      files.value.push({
        id: generateId(),
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'error',
        progress: 0,
        error: `文件大小超过 ${props.maxSize}MB 限制`,
      })
      continue
    }
    
    // 验证文件类型
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!props.accept.includes(ext)) {
      files.value.push({
        id: generateId(),
        file,
        name: file.name,
        size: file.size,
        type: file.type,
        status: 'error',
        progress: 0,
        error: `不支持的文件格式`,
      })
      continue
    }
    
    // 添加文件
    const uploadFile: UploadFile = {
      id: generateId(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
    }
    
    files.value.push(uploadFile)
  }
  
  // 开始上传
  const pendingFiles = files.value.filter(f => f.status === 'pending')
  if (pendingFiles.length > 0) {
    emit('upload', pendingFiles.map(f => f.file))
    simulateUpload(pendingFiles)
  }
}

const simulateUpload = async (uploadFiles: UploadFile[]) => {
  for (const uploadFile of uploadFiles) {
    uploadFile.status = 'uploading'
    
    // 模拟上传进度
    for (let progress = 0; progress <= 100; progress += 10) {
      await new Promise(resolve => setTimeout(resolve, 100))
      uploadFile.progress = progress
    }
    
    uploadFile.status = 'success'
  }
  
  emit('upload-complete', uploadFiles.filter(f => f.status === 'success'))
}

const removeFile = (fileId: string) => {
  const index = files.value.findIndex(f => f.id === fileId)
  if (index !== -1) {
    files.value.splice(index, 1)
    emit('remove', fileId)
  }
}

const generateId = () => {
  return Math.random().toString(36).substring(2, 11)
}

const formatSize = (bytes: number) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileIcon = (type: string) => {
  if (type.includes('pdf')) return FileText
  return File
}
</script>

<template>
  <div class="document-uploader">
    <!-- Drop Zone -->
    <div
      class="drop-zone"
      :class="{
        'drop-zone--dragging': isDragging,
        'drop-zone--disabled': disabled,
      }"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
    >
      <Upload class="drop-icon" />
      <div class="drop-text">
        <span class="drop-main">拖拽文件到此处</span>
        <span class="drop-sub">或点击选择文件</span>
      </div>
      <input
        type="file"
        :accept="accept"
        :disabled="disabled || !canAddMore"
        multiple
        class="file-input"
        @change="handleFileSelect"
      >
    </div>

    <!-- Upload Info -->
    <div class="upload-info">
      <span>支持 {{ accept }} 格式，单个文件最大 {{ maxSize }}MB</span>
      <span v-if="maxFiles > 1">最多上传 {{ maxFiles }} 个文件</span>
    </div>

    <!-- File List -->
    <div
      v-if="files.length"
      class="file-list"
    >
      <div
        v-for="file in files"
        :key="file.id"
        class="file-item"
        :class="`file-item--${file.status}`"
      >
        <component
          :is="getFileIcon(file.type)"
          class="file-icon"
        />
        
        <div class="file-info">
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ formatSize(file.size) }}</span>
        </div>

        <!-- Status -->
        <div class="file-status">
          <template v-if="file.status === 'uploading'">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :style="{ width: `${file.progress}%` }"
              />
            </div>
            <span class="progress-text">{{ file.progress }}%</span>
          </template>
          
          <template v-else-if="file.status === 'success'">
            <CheckCircle class="status-icon status-icon--success" />
          </template>
          
          <template v-else-if="file.status === 'error'">
            <AlertCircle class="status-icon status-icon--error" />
            <span class="error-text">{{ file.error }}</span>
          </template>
          
          <template v-else>
            <Loader class="status-icon status-icon--pending animate-spin" />
          </template>
        </div>

        <!-- Remove Button -->
        <button
          class="remove-btn"
          @click="removeFile(file.id)"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div
      v-if="files.length"
      class="upload-summary"
    >
      <span>{{ uploadingSummary.completed }}/{{ uploadingSummary.total }} 已完成</span>
      <span
        v-if="uploadingSummary.failed"
        class="failed-count"
      >
        {{ uploadingSummary.failed }} 个失败
      </span>
    </div>
  </div>
</template>

<style scoped>
.document-uploader {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drop-zone {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  background: var(--any-bg-secondary);
  border: 2px dashed var(--any-border);
  border-radius: var(--any-radius-lg);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.drop-zone:hover {
  border-color: var(--exec-accent);
  background: color-mix(in srgb, var(--exec-accent) 5%, transparent);
}

.drop-zone--dragging {
  border-color: var(--exec-accent);
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
}

.drop-zone--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.drop-icon {
  width: 40px;
  height: 40px;
  color: var(--any-text-muted);
}

.drop-zone:hover .drop-icon,
.drop-zone--dragging .drop-icon {
  color: var(--exec-accent);
}

.drop-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.drop-main {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.drop-sub {
  font-size: 12px;
  color: var(--any-text-muted);
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.drop-zone--disabled .file-input {
  cursor: not-allowed;
}

.upload-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--any-text-muted);
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
}

.file-item--error {
  border-color: #ff3b30;
  background: color-mix(in srgb, #ff3b30 5%, transparent);
}

.file-item--success {
  border-color: #00c853;
}

.file-icon {
  width: 20px;
  height: 20px;
  color: var(--any-text-muted);
}

.file-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: var(--any-text-muted);
}

.file-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  width: 60px;
  height: 4px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--exec-accent);
  border-radius: var(--any-radius-full);
  transition: width 0.2s ease;
}

.progress-text {
  font-size: 11px;
  color: var(--any-text-muted);
  min-width: 32px;
}

.status-icon {
  width: 18px;
  height: 18px;
}

.status-icon--success {
  color: #00c853;
}

.status-icon--error {
  color: #ff3b30;
}

.status-icon--pending {
  color: var(--any-text-muted);
}

.error-text {
  font-size: 11px;
  color: #ff3b30;
}

.remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--any-radius-md);
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.remove-btn:hover {
  background: var(--any-bg-tertiary);
  color: #ff3b30;
}

.upload-summary {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--any-text-secondary);
}

.failed-count {
  color: #ff3b30;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
