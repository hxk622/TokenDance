<script setup lang="ts">
/**
 * Research Completion Card - 研究完成卡片
 *
 * 研究任务完成后展示的卡片，包含：
 * - 研究摘要
 * - 关键发现列表
 * - 数据统计
 * - 「导出报告」按钮
 * - 「撰写汇报 PPT」按钮 (核心功能)
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  DocumentTextIcon,
  PresentationChartBarIcon,
  LightBulbIcon,
  ClockIcon,
  GlobeAltIcon,
  ArrowDownTrayIcon,
  SparklesIcon,
  CheckCircleIcon,
} from '@heroicons/vue/24/outline'
import { researchApi, type FindingsResponse, type GeneratePPTResponse, type PPTStyle } from '@/api/research'

// Props
const props = defineProps<{
  taskId: string
  topic: string
}>()

// Emits
const emit = defineEmits<{
  (e: 'ppt-generated', response: GeneratePPTResponse): void
  (e: 'export-report'): void
}>()

const router = useRouter()

// State
const findings = ref<FindingsResponse | null>(null)
const loading = ref(false)
const generating = ref(false)
const error = ref<string | null>(null)
const selectedStyle = ref<PPTStyle>('business')

// PPT 风格选项
const styleOptions: { value: PPTStyle; label: string }[] = [
  { value: 'business', label: '商务风' },
  { value: 'tech', label: '科技风' },
  { value: 'minimal', label: '简约风' },
  { value: 'academic', label: '学术风' },
]

// Computed - importance badges
const getImportanceClass = (importance: string): string => {
  switch (importance) {
    case 'high':
      return 'importance-high'
    case 'medium':
      return 'importance-medium'
    case 'low':
      return 'importance-low'
    default:
      return 'importance-default'
  }
}

const researchDurationText = computed(() => {
  if (!findings.value) return ''
  const seconds = findings.value.research_duration_seconds
  const minutes = Math.floor(seconds / 60)
  if (minutes > 0) {
    return `${minutes} 分钟`
  }
  return `${seconds} 秒`
})

// Methods
const fetchFindings = async () => {
  loading.value = true
  error.value = null

  try {
    findings.value = await researchApi.getFindings(props.taskId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '获取研究发现失败'
    console.error('Failed to fetch findings:', err)
  } finally {
    loading.value = false
  }
}

const generatePPT = async () => {
  if (!findings.value?.can_generate_ppt) return

  generating.value = true
  error.value = null

  try {
    const response = await researchApi.generatePPT(props.taskId, {
      style: selectedStyle.value,
      include_sources: true,
      include_qa: true,
      max_slides: 15,
    })

    emit('ppt-generated', response)

    // 跳转到 PPT 预览/编辑页面
    if (response.edit_url) {
      router.push(response.edit_url)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'PPT 撰写失败'
    console.error('Failed to generate PPT:', err)
  } finally {
    generating.value = false
  }
}

const exportReport = () => {
  emit('export-report')
}

// Lifecycle
onMounted(() => {
  fetchFindings()
})
</script>

<template>
  <div class="research-completion-card">
    <!-- Header -->
    <div class="card-header">
      <div class="header-icon">
        <CheckCircleIcon class="w-6 h-6 text-green-500" />
      </div>
      <div class="header-content">
        <h3 class="header-title">
          研究完成
        </h3>
        <p class="header-subtitle">
          {{ topic }}
        </p>
      </div>
    </div>

    <!-- Loading State -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <div class="spinner" />
      <p>正在提取研究发现...</p>
    </div>

    <!-- Error State -->
    <div
      v-else-if="error"
      class="error-state"
    >
      <p>{{ error }}</p>
      <button
        class="retry-btn"
        @click="fetchFindings"
      >
        重试
      </button>
    </div>

    <!-- Content -->
    <div
      v-else-if="findings"
      class="card-content"
    >
      <!-- Summary -->
      <div class="section summary-section">
        <h4 class="section-title">
          <DocumentTextIcon class="w-4 h-4" />
          研究摘要
        </h4>
        <p class="summary-text">
          {{ findings.summary || '暂无摘要' }}
        </p>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-item">
          <LightBulbIcon class="w-5 h-5 text-amber-500" />
          <span class="stat-value">{{ findings.key_findings.length }}</span>
          <span class="stat-label">关键发现</span>
        </div>
        <div class="stat-item">
          <GlobeAltIcon class="w-5 h-5 text-blue-500" />
          <span class="stat-value">{{ findings.sources_count }}</span>
          <span class="stat-label">信息来源</span>
        </div>
        <div class="stat-item">
          <ClockIcon class="w-5 h-5 text-purple-500" />
          <span class="stat-value">{{ researchDurationText }}</span>
          <span class="stat-label">研究时长</span>
        </div>
      </div>

      <!-- Key Findings -->
      <div class="section findings-section">
        <h4 class="section-title">
          <LightBulbIcon class="w-4 h-4" />
          关键发现
        </h4>
        <div class="findings-list">
          <div
            v-for="(finding, index) in findings.key_findings.slice(0, 5)"
            :key="index"
            class="finding-item"
          >
            <span class="finding-importance">{{ importanceIcon(finding.importance) }}</span>
            <span class="finding-title">{{ finding.title }}</span>
          </div>
          <div
            v-if="findings.key_findings.length > 5"
            class="more-findings"
          >
            +{{ findings.key_findings.length - 5 }} 更多发现
          </div>
        </div>
      </div>

      <!-- PPT Style Selector -->
      <div class="section style-section">
        <h4 class="section-title">
          <SparklesIcon class="w-4 h-4" />
          PPT 风格
        </h4>
        <div class="style-options">
          <button
            v-for="option in styleOptions"
            :key="option.value"
            :class="['style-option', { active: selectedStyle === option.value }]"
            @click="selectedStyle = option.value"
          >
            <span class="style-icon">{{ option.icon }}</span>
            <span class="style-label">{{ option.label }}</span>
          </button>
        </div>
      </div>

      <!-- Actions -->
      <div class="actions">
        <button
          class="btn-secondary"
          @click="exportReport"
        >
          <ArrowDownTrayIcon class="w-5 h-5" />
          导出报告
        </button>
        <button
          class="btn-primary"
          :disabled="!findings.can_generate_ppt || generating"
          @click="generatePPT"
        >
          <template v-if="generating">
            <div class="spinner-small" />
            生成中...
          </template>
          <template v-else>
            <PresentationChartBarIcon class="w-5 h-5" />
            生成汇报 PPT
          </template>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.research-completion-card {
  background: rgba(28, 28, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  overflow: hidden;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(0, 255, 136, 0.1) 100%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 255, 136, 0.2);
  border-radius: 12px;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary, #ffffff);
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  margin: 4px 0 0 0;
}

/* Loading & Error */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: var(--text-secondary);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.retry-btn {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 150ms ease;
}

.retry-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* Content */
.card-content {
  padding: 20px;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 12px 0;
}

/* Summary */
.summary-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  margin: 0;
}

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary);
}

/* Findings */
.findings-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.finding-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.finding-importance {
  font-size: 12px;
}

.finding-title {
  font-size: 14px;
  color: var(--text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-findings {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  padding: 8px;
}

/* Style Options */
.style-options {
  display: flex;
  gap: 8px;
}

.style-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  border-radius: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.style-option:hover {
  background: rgba(255, 255, 255, 0.08);
}

.style-option.active {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
  color: #00D9FF;
}

.style-icon {
  font-size: 20px;
}

.style-label {
  font-size: 12px;
  font-weight: 500;
}

/* Actions */
.actions {
  display: flex;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary,
.btn-primary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 20px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-primary {
  background: linear-gradient(135deg, #00D9FF 0%, #00FF88 100%);
  border: none;
  color: #000000;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
