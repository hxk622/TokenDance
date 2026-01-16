<script setup lang="ts">
/**
 * PPT Edit View - PPT 编辑页面
 *
 * 三栏布局：
 * - 左侧：幻灯片缩略图列表
 * - 中间：当前幻灯片编辑区
 * - 右侧：实时预览区
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  PlusIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  PencilSquareIcon,
  DocumentDuplicateIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Bars3Icon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { pptApi, type PPTOutline, type SlideContent, type SlideType, type ExportFormat } from '@/api/ppt'

const route = useRoute()
const router = useRouter()

// State
const pptId = ref(route.params.id as string)
const outline = ref<PPTOutline | null>(null)
const currentSlideIndex = ref(0)
const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const previewHtml = ref('')
const showExportMenu = ref(false)
const editMode = ref<'visual' | 'markdown'>('visual')

// Computed
const currentSlide = computed(() => {
  if (!outline.value || !outline.value.slides.length) return null
  return outline.value.slides[currentSlideIndex.value]
})

const totalSlides = computed(() => outline.value?.slides.length || 0)

const slideTypeLabel = (type: SlideType): string => {
  const labels: Record<SlideType, string> = {
    title: '标题页',
    toc: '目录页',
    section: '章节页',
    content: '内容页',
    data: '数据页',
    image: '图片页',
    quote: '引用页',
    comparison: '对比页',
    timeline: '时间线',
    conclusion: '结论页',
    qa: 'Q&A',
    thank_you: '感谢页',
  }
  return labels[type] || type
}

const slideTypeIcon = (type: SlideType): string => {
  const icons: Record<SlideType, string> = {
    title: '📋',
    toc: '📑',
    section: '📌',
    content: '📝',
    data: '📊',
    image: '🖼️',
    quote: '💬',
    comparison: '⚖️',
    timeline: '📅',
    conclusion: '✅',
    qa: '❓',
    thank_you: '🙏',
  }
  return icons[type] || '📄'
}

// Methods
const fetchOutline = async () => {
  loading.value = true
  error.value = null

  try {
    // 模拟数据 - 实际应从 API 获取
    // outline.value = await pptApi.getOutline(pptId.value)
    
    // 临时：使用 localStorage 中缓存的数据或模拟数据
    const cached = localStorage.getItem(`ppt_outline_${pptId.value}`)
    if (cached) {
      outline.value = JSON.parse(cached)
    } else {
      // 模拟数据
      outline.value = {
        id: pptId.value,
        title: 'AI Agent 市场分析报告',
        subtitle: '深度研究报告',
        author: '研究团队',
        date: new Date().toISOString().split('T')[0],
        style: 'business',
        theme: 'default',
        created_at: new Date().toISOString(),
        slides: [
          {
            id: '1',
            type: 'title',
            title: 'AI Agent 市场分析报告',
            subtitle: '2024年度深度调研 | 研究团队',
          },
          {
            id: '2',
            type: 'toc',
            title: '目录',
            points: ['市场规模与增长', '主要玩家分析', '技术趋势', '投资建议'],
          },
          {
            id: '3',
            type: 'content',
            title: '市场规模与增长',
            points: [
              '2024年全球 AI Agent 市场规模达 150 亿美元',
              '年复合增长率（CAGR）约 35%',
              '企业级应用占比最高，达 60%',
              '消费级市场增速最快，年增长超 50%',
            ],
            notes: '数据来源：Gartner, IDC 2024报告',
          },
          {
            id: '4',
            type: 'data',
            title: '市场份额分布',
            chart_type: 'pie',
            chart_data: {
              labels: ['OpenAI', 'Anthropic', 'Google', '其他'],
              datasets: [{ label: '市场份额', data: [35, 20, 25, 20] }],
            },
          },
          {
            id: '5',
            type: 'conclusion',
            title: '投资建议',
            points: [
              '重点关注企业级 AI Agent 解决方案',
              '垂直领域（医疗、金融）有较大机会',
              '关注开源生态的发展',
            ],
          },
          {
            id: '6',
            type: 'thank_you',
            title: '谢谢',
            subtitle: '欢迎交流讨论',
          },
        ],
      }
    }

    // 生成初始预览
    updatePreview()
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载失败'
    console.error('Failed to load PPT:', err)
  } finally {
    loading.value = false
  }
}

const selectSlide = (index: number) => {
  currentSlideIndex.value = index
}

const updateSlideContent = async (field: string, value: any) => {
  if (!outline.value || !currentSlide.value) return

  // 更新本地状态
  const slide = outline.value.slides[currentSlideIndex.value]
  ;(slide as any)[field] = value

  // 保存到 localStorage
  localStorage.setItem(`ppt_outline_${pptId.value}`, JSON.stringify(outline.value))

  // 更新预览
  updatePreview()

  // TODO: 调用 API 保存
  // saving.value = true
  // try {
  //   await pptApi.updateSlide(pptId.value, currentSlideIndex.value, { [field]: value })
  // } finally {
  //   saving.value = false
  // }
}

const updatePoints = (index: number, value: string) => {
  if (!currentSlide.value?.points) return
  const newPoints = [...currentSlide.value.points]
  newPoints[index] = value
  updateSlideContent('points', newPoints)
}

const addPoint = () => {
  if (!currentSlide.value) return
  const newPoints = [...(currentSlide.value.points || []), '新要点']
  updateSlideContent('points', newPoints)
}

const removePoint = (index: number) => {
  if (!currentSlide.value?.points) return
  const newPoints = currentSlide.value.points.filter((_, i) => i !== index)
  updateSlideContent('points', newPoints)
}

const addSlide = async (type: SlideType = 'content') => {
  if (!outline.value) return

  const newSlide: SlideContent = {
    id: Date.now().toString(),
    type,
    title: '新幻灯片',
    points: type === 'content' ? ['要点 1', '要点 2', '要点 3'] : undefined,
  }

  outline.value.slides.splice(currentSlideIndex.value + 1, 0, newSlide)
  currentSlideIndex.value += 1
  localStorage.setItem(`ppt_outline_${pptId.value}`, JSON.stringify(outline.value))
  updatePreview()
}

const deleteSlide = async () => {
  if (!outline.value || outline.value.slides.length <= 1) return

  outline.value.slides.splice(currentSlideIndex.value, 1)
  if (currentSlideIndex.value >= outline.value.slides.length) {
    currentSlideIndex.value = outline.value.slides.length - 1
  }
  localStorage.setItem(`ppt_outline_${pptId.value}`, JSON.stringify(outline.value))
  updatePreview()
}

const duplicateSlide = () => {
  if (!outline.value || !currentSlide.value) return

  const duplicate: SlideContent = {
    ...JSON.parse(JSON.stringify(currentSlide.value)),
    id: Date.now().toString(),
  }

  outline.value.slides.splice(currentSlideIndex.value + 1, 0, duplicate)
  currentSlideIndex.value += 1
  localStorage.setItem(`ppt_outline_${pptId.value}`, JSON.stringify(outline.value))
  updatePreview()
}

const updatePreview = () => {
  if (!currentSlide.value) return

  // 简单的 HTML 预览生成
  const slide = currentSlide.value
  let html = '<div class="slide-preview-content">'

  if (slide.type === 'title') {
    html += `<h1 class="slide-title">${slide.title}</h1>`
    if (slide.subtitle) {
      html += `<p class="slide-subtitle">${slide.subtitle}</p>`
    }
  } else if (slide.type === 'toc') {
    html += `<h2 class="slide-heading">${slide.title}</h2>`
    html += '<ol class="slide-list">'
    slide.points?.forEach((point) => {
      html += `<li>${point}</li>`
    })
    html += '</ol>'
  } else if (slide.type === 'content' || slide.type === 'conclusion') {
    html += `<h2 class="slide-heading">${slide.title}</h2>`
    if (slide.subtitle) {
      html += `<h3 class="slide-subheading">${slide.subtitle}</h3>`
    }
    if (slide.points?.length) {
      html += '<ul class="slide-list">'
      slide.points.forEach((point) => {
        html += `<li>${point}</li>`
      })
      html += '</ul>'
    }
  } else if (slide.type === 'quote') {
    html += `<h2 class="slide-heading">${slide.title}</h2>`
    if (slide.content) {
      html += `<blockquote class="slide-quote">"${slide.content}"</blockquote>`
    }
    if (slide.subtitle) {
      html += `<p class="slide-attribution">— ${slide.subtitle}</p>`
    }
  } else if (slide.type === 'data') {
    html += `<h2 class="slide-heading">${slide.title}</h2>`
    html += '<div class="slide-chart-placeholder">[图表预览]</div>'
  } else if (slide.type === 'thank_you' || slide.type === 'qa') {
    html += `<h1 class="slide-title-center">${slide.title}</h1>`
    if (slide.subtitle) {
      html += `<p class="slide-subtitle-center">${slide.subtitle}</p>`
    }
  } else {
    html += `<h2 class="slide-heading">${slide.title}</h2>`
    if (slide.content) {
      html += `<p class="slide-content">${slide.content}</p>`
    }
  }

  html += '</div>'
  previewHtml.value = html
}

const exportPPT = async (format: ExportFormat) => {
  showExportMenu.value = false

  try {
    // TODO: 实际导出
    // const result = await pptApi.exportPPT(pptId.value, format)
    // window.open(result.download_url, '_blank')

    alert(`导出 ${format.toUpperCase()} 功能即将上线`)
  } catch (err) {
    console.error('Export failed:', err)
  }
}

const goBack = () => {
  router.back()
}

const prevSlide = () => {
  if (currentSlideIndex.value > 0) {
    currentSlideIndex.value--
  }
}

const nextSlide = () => {
  if (currentSlideIndex.value < totalSlides.value - 1) {
    currentSlideIndex.value++
  }
}

// Watch for slide changes
watch(currentSlideIndex, () => {
  updatePreview()
})

// Lifecycle
onMounted(() => {
  fetchOutline()
})
</script>

<template>
  <div class="ppt-edit-page">
    <!-- Header -->
    <header class="edit-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <ChevronLeftIcon class="w-5 h-5" />
          返回
        </button>
        <div class="title-section">
          <h1 class="ppt-title">{{ outline?.title || '加载中...' }}</h1>
          <span class="ppt-meta">{{ totalSlides }} 页幻灯片</span>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-icon" title="预览模式">
          <EyeIcon class="w-5 h-5" />
        </button>
        <div class="export-dropdown">
          <button class="btn-primary" @click="showExportMenu = !showExportMenu">
            <ArrowDownTrayIcon class="w-5 h-5" />
            导出
          </button>
          <div v-if="showExportMenu" class="dropdown-menu">
            <button @click="exportPPT('pdf')">导出 PDF</button>
            <button @click="exportPPT('html')">导出 HTML</button>
            <button @click="exportPPT('pptx')">导出 PPTX</button>
          </div>
        </div>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="spinner" />
      <p>加载中...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="fetchOutline">重试</button>
    </div>

    <!-- Main Content -->
    <main v-else-if="outline" class="edit-main">
      <!-- Left Panel: Slide List -->
      <aside class="slide-list-panel">
        <div class="slide-list-header">
          <span>幻灯片</span>
          <button class="add-slide-btn" @click="addSlide('content')" title="添加幻灯片">
            <PlusIcon class="w-4 h-4" />
          </button>
        </div>
        <div class="slide-list">
          <div
            v-for="(slide, index) in outline.slides"
            :key="slide.id"
            :class="['slide-thumbnail', { active: index === currentSlideIndex }]"
            @click="selectSlide(index)"
          >
            <span class="slide-number">{{ index + 1 }}</span>
            <div class="slide-thumb-content">
              <span class="slide-type-icon">{{ slideTypeIcon(slide.type) }}</span>
              <span class="slide-thumb-title">{{ slide.title }}</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Center Panel: Editor -->
      <section class="slide-editor-panel">
        <div v-if="currentSlide" class="editor-content">
          <!-- Slide Type Badge -->
          <div class="slide-type-badge">
            {{ slideTypeIcon(currentSlide.type) }} {{ slideTypeLabel(currentSlide.type) }}
          </div>

          <!-- Title -->
          <div class="editor-field">
            <label>标题</label>
            <input
              type="text"
              :value="currentSlide.title"
              @input="(e) => updateSlideContent('title', (e.target as HTMLInputElement).value)"
              class="field-input"
            />
          </div>

          <!-- Subtitle -->
          <div v-if="['title', 'quote', 'thank_you', 'qa', 'section'].includes(currentSlide.type)" class="editor-field">
            <label>副标题</label>
            <input
              type="text"
              :value="currentSlide.subtitle || ''"
              @input="(e) => updateSlideContent('subtitle', (e.target as HTMLInputElement).value)"
              class="field-input"
            />
          </div>

          <!-- Points (for content slides) -->
          <div v-if="currentSlide.points" class="editor-field">
            <label>要点</label>
            <div class="points-list">
              <div v-for="(point, index) in currentSlide.points" :key="index" class="point-item">
                <span class="point-number">{{ index + 1 }}</span>
                <input
                  type="text"
                  :value="point"
                  @input="(e) => updatePoints(index, (e.target as HTMLInputElement).value)"
                  class="point-input"
                />
                <button class="point-delete" @click="removePoint(index)" title="删除">
                  <XMarkIcon class="w-4 h-4" />
                </button>
              </div>
              <button class="add-point-btn" @click="addPoint">
                <PlusIcon class="w-4 h-4" />
                添加要点
              </button>
            </div>
          </div>

          <!-- Content (for quote slides) -->
          <div v-if="currentSlide.type === 'quote'" class="editor-field">
            <label>引用内容</label>
            <textarea
              :value="currentSlide.content || ''"
              @input="(e) => updateSlideContent('content', (e.target as HTMLTextAreaElement).value)"
              class="field-textarea"
              rows="3"
            />
          </div>

          <!-- Notes -->
          <div class="editor-field">
            <label>演讲者备注</label>
            <textarea
              :value="currentSlide.notes || ''"
              @input="(e) => updateSlideContent('notes', (e.target as HTMLTextAreaElement).value)"
              class="field-textarea"
              rows="2"
              placeholder="添加备注..."
            />
          </div>

          <!-- Actions -->
          <div class="editor-actions">
            <button class="action-btn" @click="duplicateSlide">
              <DocumentDuplicateIcon class="w-4 h-4" />
              复制
            </button>
            <button class="action-btn danger" @click="deleteSlide" :disabled="totalSlides <= 1">
              <TrashIcon class="w-4 h-4" />
              删除
            </button>
          </div>
        </div>
      </section>

      <!-- Right Panel: Preview -->
      <aside class="slide-preview-panel">
        <div class="preview-header">
          <span>预览</span>
          <div class="preview-nav">
            <button @click="prevSlide" :disabled="currentSlideIndex === 0">
              <ChevronLeftIcon class="w-4 h-4" />
            </button>
            <span>{{ currentSlideIndex + 1 }} / {{ totalSlides }}</span>
            <button @click="nextSlide" :disabled="currentSlideIndex === totalSlides - 1">
              <ChevronRightIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
        <div class="preview-container">
          <div class="preview-slide" v-html="previewHtml" />
        </div>
      </aside>
    </main>
  </div>
</template>

<style scoped>
.ppt-edit-page {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary, #121212);
  color: var(--text-primary, #ffffff);
}

/* Header */
.edit-header {
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(28, 28, 30, 0.9);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.title-section {
  display: flex;
  flex-direction: column;
}

.ppt-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.ppt-meta {
  font-size: 12px;
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-icon {
  padding: 8px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-icon:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, #00D9FF 0%, #00FF88 100%);
  border: none;
  border-radius: 8px;
  color: #000000;
  font-weight: 600;
  cursor: pointer;
  transition: all 150ms ease;
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.4);
}

.export-dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: rgba(28, 28, 30, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  overflow: hidden;
  z-index: 100;
}

.dropdown-menu button {
  display: block;
  width: 100%;
  padding: 10px 16px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: background 150ms ease;
}

.dropdown-menu button:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Loading & Error */
.loading-state,
.error-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Main Content */
.edit-main {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Slide List Panel */
.slide-list-panel {
  width: 200px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  background: rgba(18, 18, 18, 0.5);
}

.slide-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.add-slide-btn {
  padding: 4px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.add-slide-btn:hover {
  background: rgba(0, 217, 255, 0.3);
  color: #00D9FF;
}

.slide-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.slide-thumbnail {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.slide-thumbnail:hover {
  background: rgba(255, 255, 255, 0.08);
}

.slide-thumbnail.active {
  background: rgba(0, 217, 255, 0.15);
  border-color: rgba(0, 217, 255, 0.5);
}

.slide-number {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-secondary);
}

.slide-thumb-content {
  flex: 1;
  min-width: 0;
}

.slide-type-icon {
  font-size: 12px;
  margin-right: 4px;
}

.slide-thumb-title {
  font-size: 12px;
  color: var(--text-primary);
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Editor Panel */
.slide-editor-panel {
  flex: 1;
  min-width: 400px;
  overflow-y: auto;
  padding: 24px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.editor-content {
  max-width: 600px;
  margin: 0 auto;
}

.slide-type-badge {
  display: inline-block;
  padding: 6px 12px;
  background: rgba(0, 217, 255, 0.15);
  border-radius: 20px;
  font-size: 13px;
  color: #00D9FF;
  margin-bottom: 24px;
}

.editor-field {
  margin-bottom: 20px;
}

.editor-field label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.field-input,
.field-textarea {
  width: 100%;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 14px;
  transition: all 150ms ease;
}

.field-input:focus,
.field-textarea:focus {
  outline: none;
  border-color: rgba(0, 217, 255, 0.5);
  background: rgba(255, 255, 255, 0.08);
}

.field-textarea {
  resize: vertical;
  min-height: 60px;
}

.points-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.point-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.point-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.point-input {
  flex: 1;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 14px;
}

.point-input:focus {
  outline: none;
  border-color: rgba(0, 217, 255, 0.5);
}

.point-delete {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  opacity: 0.5;
  transition: all 150ms ease;
}

.point-delete:hover {
  color: #ff4757;
  opacity: 1;
}

.add-point-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 150ms ease;
}

.add-point-btn:hover {
  background: rgba(0, 217, 255, 0.1);
  border-color: rgba(0, 217, 255, 0.5);
  color: #00D9FF;
}

.editor-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
}

.action-btn.danger:hover {
  background: rgba(255, 71, 87, 0.2);
  border-color: rgba(255, 71, 87, 0.5);
  color: #ff4757;
}

.action-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* Preview Panel */
.slide-preview-panel {
  width: 45%;
  min-width: 400px;
  display: flex;
  flex-direction: column;
  background: rgba(18, 18, 18, 0.5);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.preview-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preview-nav button {
  padding: 4px;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 4px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.preview-nav button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
}

.preview-nav button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.preview-container {
  flex: 1;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-slide {
  width: 100%;
  max-width: 640px;
  aspect-ratio: 16 / 9;
  background: #ffffff;
  border-radius: 8px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

/* Preview Content Styles */
:deep(.slide-preview-content) {
  color: #1a1a2e;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.slide-title) {
  font-size: 32px;
  font-weight: 700;
  text-align: center;
  margin: auto 0;
}

:deep(.slide-title-center) {
  font-size: 36px;
  font-weight: 700;
  text-align: center;
  margin: auto 0;
}

:deep(.slide-subtitle) {
  font-size: 18px;
  color: #666;
  text-align: center;
  margin-top: 16px;
}

:deep(.slide-subtitle-center) {
  font-size: 16px;
  color: #666;
  text-align: center;
}

:deep(.slide-heading) {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 20px;
  color: #00D9FF;
}

:deep(.slide-subheading) {
  font-size: 16px;
  color: #666;
  margin-bottom: 16px;
}

:deep(.slide-list) {
  font-size: 16px;
  line-height: 1.8;
  padding-left: 24px;
}

:deep(.slide-list li) {
  margin-bottom: 8px;
}

:deep(.slide-quote) {
  font-size: 20px;
  font-style: italic;
  color: #333;
  border-left: 4px solid #00D9FF;
  padding-left: 20px;
  margin: 20px 0;
}

:deep(.slide-attribution) {
  font-size: 14px;
  color: #666;
  text-align: right;
}

:deep(.slide-chart-placeholder) {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 8px;
  color: #999;
  font-size: 14px;
}
</style>
