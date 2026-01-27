<script setup lang="ts">
/**
 * ArtifactCard - 可折叠的产物卡片
 * 
 * 在对话区域内联展示 Artifact：
 * - 完成后自动折叠为卡片形式
 * - 点击可展开预览或同步到右侧 PreviewArea
 * - 支持不同类型的 artifact (报告、PPT、代码等)
 */
import { ref, computed, watch, onMounted } from 'vue'
import { 
  FileText, 
  Presentation, 
  FileCode, 
  ChevronDown, 
  ChevronRight,
  ExternalLink,
  Check,
  Loader2,
  File
} from 'lucide-vue-next'

export type ArtifactType = 'report' | 'ppt' | 'code' | 'file' | 'data'
export type ArtifactStatus = 'pending' | 'generating' | 'complete' | 'error'

interface Props {
  /** Artifact ID */
  id: string
  /** Artifact 类型 */
  type: ArtifactType
  /** 标题 */
  title: string
  /** 状态 */
  status: ArtifactStatus
  /** 简要描述/预览文本 */
  summary?: string
  /** 是否默认折叠 (完成后默认折叠) */
  defaultCollapsed?: boolean
  /** 完成后自动折叠延迟 (ms) */
  autoCollapseDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  summary: '',
  defaultCollapsed: false,
  autoCollapseDelay: 1500
})

const emit = defineEmits<{
  /** 点击查看时触发，用于同步到 PreviewArea */
  'view': [artifactId: string, type: ArtifactType]
  /** 展开/折叠状态变化 */
  'toggle': [collapsed: boolean]
}>()

// 折叠状态
const isCollapsed = ref(props.defaultCollapsed)

// 获取类型图标
const iconComponent = computed(() => {
  switch (props.type) {
    case 'report':
      return FileText
    case 'ppt':
      return Presentation
    case 'code':
      return FileCode
    case 'file':
      return File
    default:
      return FileText
  }
})

// 获取类型标签
const typeLabel = computed(() => {
  switch (props.type) {
    case 'report':
      return '研究报告'
    case 'ppt':
      return '演示文稿'
    case 'code':
      return '代码文件'
    case 'file':
      return '文件'
    case 'data':
      return '数据'
    default:
      return '产物'
  }
})

// 状态样式类
const statusClass = computed(() => {
  return `status-${props.status}`
})

// 是否显示加载动画
const isLoading = computed(() => props.status === 'generating' || props.status === 'pending')

// 是否已完成
const isComplete = computed(() => props.status === 'complete')

// 切换折叠状态
function toggleCollapse() {
  isCollapsed.value = !isCollapsed.value
  emit('toggle', isCollapsed.value)
}

// 查看产物 (同步到 PreviewArea)
function handleView() {
  emit('view', props.id, props.type)
}

// 自动折叠：完成后延迟折叠
watch(() => props.status, (newStatus, oldStatus) => {
  if (newStatus === 'complete' && oldStatus !== 'complete') {
    setTimeout(() => {
      if (props.status === 'complete') {
        isCollapsed.value = true
        emit('toggle', true)
      }
    }, props.autoCollapseDelay)
  }
})

// 初始化
onMounted(() => {
  if (props.status === 'complete' && props.defaultCollapsed) {
    isCollapsed.value = true
  }
})
</script>

<template>
  <div :class="['artifact-card', statusClass, { collapsed: isCollapsed }]">
    <!-- 卡片头部 (始终显示) -->
    <div
      class="card-header"
      @click="toggleCollapse"
    >
      <div class="header-left">
        <!-- 类型图标 -->
        <div :class="['type-icon', `type-${type}`]">
          <component
            :is="isLoading ? Loader2 : iconComponent"
            :class="['icon', { spinning: isLoading }]"
          />
        </div>
        
        <!-- 标题和类型 -->
        <div class="header-info">
          <span class="card-title">{{ title }}</span>
          <span class="card-type">{{ typeLabel }}</span>
        </div>
      </div>
      
      <div class="header-right">
        <!-- 状态指示 -->
        <span
          v-if="isComplete"
          class="status-badge complete"
        >
          <Check class="w-3 h-3" />
          <span>已完成</span>
        </span>
        <span
          v-else-if="isLoading"
          class="status-badge loading"
        >
          生成中...
        </span>
        
        <!-- 折叠图标 -->
        <component
          :is="isCollapsed ? ChevronRight : ChevronDown"
          class="collapse-icon"
        />
      </div>
    </div>
    
    <!-- 展开内容 -->
    <Transition name="collapse">
      <div
        v-show="!isCollapsed"
        class="card-content"
      >
        <!-- 摘要/预览 -->
        <p
          v-if="summary"
          class="card-summary"
        >
          {{ summary }}
        </p>
        
        <!-- 操作按钮 -->
        <div class="card-actions">
          <button
            class="action-btn primary"
            :disabled="!isComplete"
            @click.stop="handleView"
          >
            <ExternalLink class="w-4 h-4" />
            <span>查看详情</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.artifact-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  overflow: hidden;
  transition: all 200ms ease;
}

.artifact-card:hover {
  border-color: var(--any-border-hover);
}

.artifact-card.collapsed {
  /* 折叠时更紧凑 */
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.type-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: var(--any-bg-tertiary);
}

.type-icon.type-report {
  background: rgba(0, 217, 255, 0.1);
  color: var(--td-state-thinking, #00D9FF);
}

.type-icon.type-ppt {
  background: rgba(255, 184, 0, 0.1);
  color: var(--exec-warning, #FFB800);
}

.type-icon.type-code {
  background: rgba(0, 255, 136, 0.1);
  color: var(--td-state-success, #00FF88);
}

.type-icon .icon {
  width: 20px;
  height: 20px;
}

.type-icon .icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.card-type {
  font-size: 12px;
  color: var(--any-text-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Status badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
}

.status-badge.complete {
  background: rgba(0, 255, 136, 0.1);
  color: var(--td-state-success, #00FF88);
}

.status-badge.loading {
  background: rgba(0, 217, 255, 0.1);
  color: var(--td-state-thinking, #00D9FF);
}

.collapse-icon {
  width: 18px;
  height: 18px;
  color: var(--any-text-muted);
  transition: transform 200ms ease;
}

/* Content */
.card-content {
  padding: 0 16px 16px;
}

.card-summary {
  font-size: 13px;
  color: var(--any-text-secondary);
  line-height: 1.5;
  margin: 0 0 12px;
}

.card-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms ease;
  border: none;
}

.action-btn.primary {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.action-btn.primary:hover:not(:disabled) {
  background: var(--any-bg-hover);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Collapse transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 200ms ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
}

/* Status-specific card styles */
.artifact-card.status-complete {
  border-color: rgba(0, 255, 136, 0.3);
}

.artifact-card.status-generating {
  border-color: rgba(0, 217, 255, 0.3);
}

.artifact-card.status-error {
  border-color: rgba(255, 59, 48, 0.3);
}
</style>
