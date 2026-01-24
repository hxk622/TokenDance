<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthGuard } from '@/composables/useAuthGuard'
import { 
  Search, FileText, Presentation, BarChart3, 
  Users, Mic, ArrowUp, Sparkles, Globe, FileVideo,
  Languages, FolderOpen, MoreHorizontal, Code2, Zap,
  History, Settings, LayoutGrid, Plus, ChevronRight
} from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import AnyHeader from '@/components/common/AnyHeader.vue'
import type { NavItem } from '@/components/common/AnySidebar.vue'
import type { Project, ProjectType } from '@/types/project'

const router = useRouter()
const projectStore = useProjectStore()
const { requireAuth } = useAuthGuard()

const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)
const activeCategory = ref('all')
const errorMessage = ref('')

// 显示错误提示
const showError = (msg: string) => {
  errorMessage.value = msg
  setTimeout(() => {
    errorMessage.value = ''
  }, 4000)
}

// Project list
const recentProjects = computed(() => projectStore.activeProjects.slice(0, 6))
const hasProjects = computed(() => recentProjects.value.length > 0)

// Project type icons
const projectTypeIcons: Record<ProjectType, typeof FileText> = {
  research: Search,
  document: FileText,
  slides: Presentation,
  code: Code2,
  data_analysis: BarChart3,
  quick_task: Zap,
}

function getProjectIcon(type: ProjectType) {
  return projectTypeIcons[type] || FolderOpen
}

// Handle project click
function handleProjectClick(project: Project) {
  router.push(`/project/${project.id}`)
}

// Format time
function formatProjectTime(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// 快捷操作芯片 - AnyGen 风格
const quickChips = [
  { id: 'slides', label: '制作演示', icon: Presentation },
  { id: 'doc', label: '撰写文档', icon: FileText },
  { id: 'research', label: '深度调研', icon: Search },
  { id: 'analyze', label: '数据分析', icon: BarChart3 },
  { id: 'webpage', label: '网页制作', icon: Globe },
  { id: 'translate', label: '翻译 PDF', icon: Languages },
  { id: 'video', label: '视频总结', icon: FileVideo },
]

// 模板分类
const categories = [
  { id: 'all', label: '全部模板' },
  { id: 'hot', label: '热门推荐', badge: 'HOT' },
  { id: 'marketing', label: '市场增长' },
  { id: 'product', label: '产品研究' },
  { id: 'gtm', label: '市场进入' },
  { id: 'learning', label: '学习成长' },
  { id: 'career', label: '职业发展' },
  { id: 'my', label: '我的模板', icon: Sparkles },
]

// 模板卡片 - AnyGen 风格（预览图 + 标题 + 标签）
const templates = [
  { 
    id: 'ppt-upload', 
    title: 'Upload a PPTX as a template', 
    tag: null,
    uses: null,
    category: 'all',
    icon: Presentation,
    bgColor: '#FFF7ED',
    iconColor: '#EA580C'
  },
  { 
    id: 'blank-doc', 
    title: 'Create a blank doc', 
    tag: null,
    uses: null,
    category: 'all',
    icon: FileText,
    bgColor: '#F1F5F9',
    iconColor: '#475569'
  },
  { 
    id: 'okr-review', 
    title: 'Team OKR Retrospective', 
    tag: 'Slides',
    uses: '10,388 uses',
    category: 'career',
    icon: null,
    preview: 'okr'
  },
  { 
    id: 'news-digest', 
    title: 'AI Daily Digest', 
    tag: 'Doc',
    uses: '14,473 uses',
    category: 'hot',
    icon: null,
    preview: 'news'
  },
  { 
    id: 'marketing-plan', 
    title: 'Marketing Plan', 
    tag: 'Slides',
    uses: '2,545 uses',
    category: 'marketing',
    icon: null,
    preview: 'marketing'
  },
  { 
    id: 'quarterly-review', 
    title: 'Quarterly Business Review', 
    tag: 'Slides',
    uses: '8,234 uses',
    category: 'career',
    icon: null,
    preview: 'quarterly'
  },
]

// 过滤后的模板
const filteredTemplates = computed(() => {
  if (activeCategory.value === 'all') return templates
  return templates.filter(t => t.category === activeCategory.value || t.category === 'all')
})

// Placeholder 提示
const placeholderText = '描述你要完成的任务...'

// 处理提交 - 创建 Project 并跳转到项目执行页
const handleSubmit = async () => {
  if (!inputValue.value.trim() || isLoading.value) return
  
  // 需要登录才能提交任务
  const canProceed = await requireAuth('请先登录后发送请求')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    // 使用 Project-First 架构
    const project = await projectStore.quickCreate(inputValue.value)
    
    // 跳转到项目执行页
    router.push({
      path: `/project/${project.id}`,
      query: { task: inputValue.value }
    })
  } catch (error) {
    console.error('Failed to create project:', error)
    showError('哎呀，遇到了一点小问题，请稍后再试试看 😅')
  } finally {
    isLoading.value = false
  }
}

// 处理键盘事件
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSubmit()
  }
}

// 处理快捷芯片点击 - 创建 Project 并跳转到项目执行页面
const handleChipClick = async (chip: typeof quickChips[0]) => {
  if (isLoading.value) return
  
  // 需要登录才能使用快捷操作
  const canProceed = await requireAuth('请先登录后使用快捷操作')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    const intent = `我想要${chip.label}`
    const project = await projectStore.quickCreate(intent)
    
    router.push({
      path: `/project/${project.id}`,
      query: { task: intent }
    })
  } catch (error) {
    console.error('Failed to create project:', error)
    showError('系统开小差了，请稍等片刻再试 ☕')
  } finally {
    isLoading.value = false
  }
}

// 处理模板点击 - 创建 Project 并跳转到项目执行页面
const handleTemplateClick = async (template: typeof templates[0]) => {
  if (isLoading.value) return
  
  // 需要登录才能使用模板
  const canProceed = await requireAuth('请先登录后使用模板')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    const intent = `请帮我${template.title}`
    const project = await projectStore.quickCreate(intent)
    
    router.push({
      path: `/project/${project.id}`,
      query: { task: intent }
    })
  } catch (error) {
    console.error('Failed to create project:', error)
    showError('有点小状况，请稍后再试试 🙏')
  } finally {
    isLoading.value = false
  }
}

// 处理附件按钮点击
const handleAttachClick = () => {
  fileInputRef.value?.click()
}

// 处理文件选择 - 创建 Project 并跳转到项目执行页面
const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0 && !isLoading.value) {
    const fileNames = Array.from(input.files).map(f => f.name).join(', ')
    
    // 需要登录才能上传文件
    const canProceed = await requireAuth('请先登录后上传文件')
    if (!canProceed) {
      input.value = '' // 清空文件选择
      return
    }
    
    isLoading.value = true
    try {
      const intent = `请帮我处理这些文件: ${fileNames}`
      const project = await projectStore.quickCreate(intent)
      
      // TODO: 实际项目中应先上传文件
      router.push({
        path: `/project/${project.id}`,
        query: { task: intent }
      })
    } catch (error) {
      console.error('Failed to create project:', error)
      showError('文件处理遇到了麻烦，请稍后重试 📁')
    } finally {
      isLoading.value = false
    }
  }
}


// Sidebar navigation
const sidebarSections = [
  {
    id: 'main',
    items: [
      { id: 'search', label: '搜索', icon: Search },
      { id: 'templates', label: '模板', icon: LayoutGrid },
      { id: 'files', label: '文件', icon: FolderOpen },
      { id: 'history', label: '历史', icon: History },
    ] as NavItem[]
  }
]

const handleSidebarNavClick = (item: NavItem) => {
  switch (item.id) {
    case 'search':
      inputRef.value?.focus()
      break
    case 'history':
      router.push('/history')
      break
  }
}

// New button handler
const handleNewClick = () => {
  inputRef.value?.focus()
}

// Cmd+K 键盘快捷键
function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    inputRef.value?.focus()
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleGlobalKeydown)
  
  // Load recent projects if workspace is set
  // Note: WorkspaceSelector in AnyHeader will auto-load and set workspace if none selected
  const workspaceId = projectStore.currentWorkspaceId
  if (workspaceId) {
    try {
      await projectStore.loadProjects(workspaceId)
    } catch (e) {
      console.error('Failed to load projects:', e)
    }
  }
})

// Watch workspace changes to reload projects
watch(
  () => projectStore.currentWorkspaceId,
  async (newWorkspaceId) => {
    if (newWorkspaceId) {
      try {
        await projectStore.loadProjects(newWorkspaceId)
      } catch (e) {
        console.error('Failed to load projects after workspace change:', e)
      }
    }
  }
)

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="home-view">
    <!-- 左侧边栏 - 固定宽度图标栏 -->
    <AnySidebar
      :sections="sidebarSections"
      @new-click="handleNewClick"
      @nav-click="handleSidebarNavClick"
    >
      <template #footer>
        <button
          class="sidebar-footer-btn"
          data-tooltip="设置"
        >
          <Settings class="icon" />
        </button>
      </template>
    </AnySidebar>
    
    <!-- 右上角个人信息栏 - 固定定位 -->
    <AnyHeader />
    
    <!-- 错误提示 Toast -->
    <Transition name="toast">
      <div
        v-if="errorMessage"
        class="error-toast"
      >
        {{ errorMessage }}
      </div>
    </Transition>

    <!-- Main Content -->
    <main class="home-main">
      <!-- Hero: 大标题 -->
      <section class="hero-section">
        <h1 class="hero-title">
          How can I help you today?
        </h1>
      </section>

      <!-- 核心输入框 - AnyGen 风格 -->
      <section class="input-section">
        <div class="input-box">
          <!-- 输入区 -->
          <textarea
            ref="inputRef"
            v-model="inputValue"
            class="main-textarea"
            :placeholder="placeholderText"
            rows="1"
            @keydown="handleKeydown"
            @input="e => {
              const target = e.target as HTMLTextAreaElement
              target.style.height = 'auto'
              target.style.height = Math.min(target.scrollHeight, 120) + 'px'
            }"
          />
          
          <!-- 工具栏 -->
          <div class="input-toolbar">
            <div class="toolbar-left">
              <AnyButton
                variant="ghost"
                size="sm"
                title="添加文件"
                @click="handleAttachClick"
              >
                <Plus class="w-5 h-5" />
              </AnyButton>
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                multiple
                @change="handleFileSelect"
              >
              <AnyButton
                variant="ghost"
                size="sm"
                title="添加协作者"
              >
                <Users class="w-5 h-5" />
              </AnyButton>
            </div>
            <div class="toolbar-right">
              <AnyButton
                variant="ghost"
                size="sm"
                title="语音输入"
              >
                <Mic class="w-5 h-5" />
              </AnyButton>
              <button 
                class="submit-btn"
                :class="{ active: inputValue.trim() }"
                :disabled="!inputValue.trim() || isLoading"
                @click="handleSubmit"
              >
                <ArrowUp class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 快捷操作芯片 -->
      <section class="chips-section">
        <div class="chips-row">
          <button
            v-for="chip in quickChips.slice(0, 5)"
            :key="chip.id"
            class="chip"
            :disabled="isLoading"
            @click="handleChipClick(chip)"
          >
            <component
              :is="chip.icon"
              class="w-4 h-4"
            />
            <span>{{ chip.label }}</span>
          </button>
        </div>
        <div class="chips-row">
          <button
            v-for="chip in quickChips.slice(5)"
            :key="chip.id"
            class="chip"
            :disabled="isLoading"
            @click="handleChipClick(chip)"
          >
            <component
              :is="chip.icon"
              class="w-4 h-4"
            />
            <span>{{ chip.label }}</span>
          </button>
          <button class="chip chip-more">
            <MoreHorizontal class="w-4 h-4" />
            <span>更多</span>
          </button>
        </div>
      </section>

      <!-- 进行中的项目 -->
      <section
        v-if="hasProjects"
        class="projects-section"
      >
        <div class="section-header">
          <h2 class="section-title">
            进行中的项目
          </h2>
          <button
            class="see-all-btn"
            @click="router.push('/history')"
          >
            查看全部
            <ChevronRight class="w-4 h-4" />
          </button>
        </div>
        <div class="projects-grid">
          <button
            v-for="project in recentProjects"
            :key="project.id"
            class="project-card"
            @click="handleProjectClick(project)"
          >
            <div class="project-icon-wrapper">
              <component
                :is="getProjectIcon(project.project_type)"
                class="project-icon"
              />
            </div>
            <div class="project-info">
              <span class="project-title">{{ project.title }}</span>
              <span class="project-meta">{{ formatProjectTime(project.updated_at) }}</span>
            </div>
            <ChevronRight class="project-chevron" />
          </button>
        </div>
      </section>

      <!-- 模板分类标签 -->
      <section class="categories-section">
        <div class="categories-scroll">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="category-tab"
            :class="{ active: activeCategory === cat.id }"
            @click="activeCategory = cat.id"
          >
            <component
              :is="cat.icon"
              v-if="cat.icon"
              class="w-4 h-4"
            />
            <span>{{ cat.label }}</span>
            <span
              v-if="cat.badge"
              class="category-badge"
            >{{ cat.badge }}</span>
          </button>
        </div>
      </section>

      <!-- 模板卡片网格 -->
      <section class="templates-section">
        <div class="templates-grid">
          <button
            v-for="tpl in filteredTemplates"
            :key="tpl.id"
            class="template-card"
            :disabled="isLoading"
            @click="handleTemplateClick(tpl)"
          >
            <!-- 预览图区域 -->
            <div
              class="template-preview"
              :class="{ 'has-preview': tpl.preview }"
            >
              <!-- 图标类型（无预览图） -->
              <div
                v-if="tpl.icon"
                class="template-icon-wrapper"
                :style="{ background: tpl.bgColor }"
              >
                <component
                  :is="tpl.icon"
                  class="w-10 h-10"
                  :style="{ color: tpl.iconColor }"
                />
              </div>
              <!-- 预览图类型 -->
              <div
                v-else
                class="template-thumbnail"
                :class="`thumbnail--${tpl.preview}`"
              />
            </div>
            <!-- 文字信息 -->
            <div class="template-info">
              <span class="template-title">{{ tpl.title }}</span>
              <div
                v-if="tpl.tag"
                class="template-meta"
              >
                <span
                  class="template-tag"
                  :class="`tag--${tpl.tag.toLowerCase()}`"
                >{{ tpl.tag }}</span>
                <span class="template-uses">{{ tpl.uses }}</span>
              </div>
            </div>
          </button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ============================================
   AnyGen Style - Central Focus Layout
   ============================================ */

.home-view {
  @apply relative min-h-screen;
  background: var(--any-bg-secondary);
}

/* Sidebar footer button - reuses AnySidebar styling */
.sidebar-footer-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.sidebar-footer-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.sidebar-footer-btn .icon {
  width: 20px;
  height: 20px;
}

.sidebar-footer-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 100%;
  top: 50%;
  transform: translateY(-50%);
  margin-left: 8px;
  padding: 6px 10px;
  background: var(--any-text-primary);
  color: var(--any-bg-primary);
  font-size: 12px;
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  pointer-events: none;
  z-index: 1000;
}

.sidebar-footer-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}


.sign-in-btn:hover {
  background: var(--any-bg-tertiary);
  border-color: var(--any-border-hover);
}

/* Main Content */
.home-main {
  margin-left: 56px;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
  padding-top: max(15vh, 120px);
  padding-bottom: 4rem;
}

/* Hero Section */
.hero-section {
  @apply text-center mb-10;
  width: 100%;
  max-width: 720px;
}

.hero-title {
  @apply text-3xl md:text-4xl font-normal;
  color: var(--any-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  letter-spacing: -0.02em;
}

/* ============================================
   Input Box - AnyGen Style
   ============================================ */
.input-section {
  @apply mb-6;
  width: 100%;
  max-width: 720px;
}

.input-box {
  @apply rounded-2xl shadow-sm;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  width: 100%;
  padding: 16px 20px;
  transition: all var(--any-duration-normal) var(--any-ease-default);
}

.input-box:focus-within {
  border-color: var(--any-border-hover);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.main-textarea {
  @apply w-full text-base bg-transparent border-none resize-none;
  color: var(--any-text-primary);
  min-height: 24px;
  max-height: 120px;
  line-height: 1.5;
}

.main-textarea::placeholder {
  color: var(--any-text-muted);  /* 规范: placeholder 使用 muted 色，避免视觉疲劳 */
}

.main-textarea:focus {
  outline: none;
}

.input-toolbar {
  @apply flex items-center justify-between mt-4 pt-3;
}

.toolbar-left,
.toolbar-right {
  @apply flex items-center gap-2;
}

.submit-btn {
  @apply p-2.5 rounded-full cursor-pointer;
  background: var(--any-bg-tertiary);
  color: var(--any-text-tertiary);  /* 默认状态使用 tertiary 色，保证可见性 */
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.submit-btn.active {
  background: var(--any-text-primary);
  color: var(--any-text-inverse);  /* 使用 inverse 色确保在深色/浅色模式下箭头都可见 */
  border-color: var(--any-text-primary);
}

.submit-btn:disabled {
  @apply cursor-not-allowed;
  opacity: 0.7;  /* 提高 disabled 状态可见度 */
}

/* ============================================
   Projects Section
   ============================================ */
.projects-section {
  @apply mb-10;
  width: 100%;
  max-width: 720px;
}

.section-header {
  @apply flex items-center justify-between mb-4;
}

.section-title {
  @apply text-lg font-medium;
  color: var(--any-text-primary);
}

.see-all-btn {
  @apply flex items-center gap-1 px-3 py-1.5
         text-sm rounded-lg cursor-pointer;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.see-all-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.projects-grid {
  @apply grid gap-3;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
}

@media (min-width: 640px) {
  .projects-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 768px) {
  .projects-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

.project-card {
  @apply flex items-center gap-3 p-3
         rounded-xl cursor-pointer text-left;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.project-card:hover {
  border-color: var(--any-border-hover);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.project-icon-wrapper {
  @apply flex items-center justify-center w-10 h-10
         rounded-lg flex-shrink-0;
  background: var(--any-bg-tertiary);
}

.project-icon {
  @apply w-5 h-5;
  color: var(--any-text-secondary);
}

.project-info {
  @apply flex-1 min-w-0;
}

.project-title {
  @apply block text-sm font-medium truncate;
  color: var(--any-text-primary);
}

.project-meta {
  @apply block text-xs mt-0.5;
  color: var(--any-text-tertiary);
}

.project-chevron {
  @apply w-4 h-4 flex-shrink-0;
  color: var(--any-text-tertiary);
  opacity: 0;
  transition: opacity var(--any-duration-fast) var(--any-ease-default);
}

.project-card:hover .project-chevron {
  opacity: 1;
}

/* ============================================
   Quick Chips - AnyGen Style
   ============================================ */
.chips-section {
  @apply mb-12;
  width: 100%;
  max-width: 720px;
}

.chips-row {
  @apply flex flex-wrap items-center justify-center gap-2.5 mb-2.5;
}

.chip {
  @apply flex items-center gap-2 px-4 py-2
         text-sm rounded-full cursor-pointer;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.chip:hover:not(:disabled) {
  border-color: var(--any-border-hover);
  background: var(--any-bg-tertiary);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.chip:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.chip-more {
  color: var(--any-text-secondary);  /* 使用 secondary 色保证可见性 */
}

/* ============================================
   Categories Tabs - AnyGen Style
   ============================================ */
.categories-section {
  @apply mb-6;
  width: 100%;
  max-width: 960px;
  border-bottom: 1px solid var(--any-border);
}

.categories-scroll {
  @apply flex items-center gap-0 overflow-x-auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.categories-scroll::-webkit-scrollbar {
  display: none;
}

.category-tab {
  @apply flex items-center gap-1.5 px-5 py-3
         text-sm whitespace-nowrap
         border-b-2 border-transparent
         cursor-pointer;
  color: var(--any-text-tertiary);  /* 未激活状态使用 tertiary 色，保证可见性 */
  margin-bottom: -1px;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.category-tab:hover {
  color: var(--any-text-primary);
}

.category-tab.active {
  @apply font-medium;
  color: var(--any-text-primary);
  border-color: var(--any-text-primary);
}

.category-badge {
  @apply text-xs px-1.5 py-0.5 rounded;
  background: rgba(239, 68, 68, 0.15);
  color: var(--any-error);
}

/* ============================================
   Template Cards - AnyGen Style
   ============================================ */
.templates-section {
  @apply py-6;
  width: 100%;
  max-width: 960px;
}

.templates-grid {
  @apply grid gap-5;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

@media (min-width: 1400px) {
  .templates-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

.template-card {
  @apply flex flex-col bg-transparent
         cursor-pointer text-left;
  transition: all var(--any-duration-normal) var(--any-ease-default);
}

.template-card:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.template-card:hover:not(:disabled) .template-preview {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
}

/* 预览图区域 */
.template-preview {
  @apply w-full flex items-center justify-center overflow-hidden;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  aspect-ratio: 4 / 3;
  transition: all var(--any-duration-normal) var(--any-ease-bounce);
}

.template-preview.has-preview {
  @apply p-0;
}

/* 图标类型卡片 */
.template-icon-wrapper {
  @apply w-20 h-20 rounded-2xl flex items-center justify-center;
}

/* 缩略图类型卡片 */
.template-thumbnail {
  @apply w-full h-full;
  background-size: cover;
  background-position: center;
}

.thumbnail--okr {
  background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%);
}

.thumbnail--news {
  background: linear-gradient(135deg, #F1F5F9 0%, #E2E8F0 100%);
}

.thumbnail--marketing {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
}

.thumbnail--quarterly {
  background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
}

/* 文字信息 */
.template-info {
  @apply py-3;
}

.template-title {
  @apply text-sm font-medium block mb-1;
  color: var(--any-text-primary);
}

.template-meta {
  @apply flex items-center gap-2;
}

.template-tag {
  @apply text-xs px-2 py-0.5 rounded;
}

.tag--slides {
  background: rgba(59, 130, 246, 0.15);
  color: #3B82F6;
}

[data-theme="dark"] .tag--slides {
  background: rgba(59, 130, 246, 0.25);
  color: #60A5FA;
}

.tag--doc {
  background: rgba(0, 217, 255, 0.15);
  color: #8B5CF6;
}

[data-theme="dark"] .tag--doc {
  background: rgba(0, 217, 255, 0.25);
  color: #A78BFA;
}

.template-uses {
  @apply text-xs;
  color: var(--any-text-muted);
}

/* Hidden utility */
.hidden {
  display: none;
}

/* Error Toast */
.error-toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--any-error);
  font-size: 14px;
  border-radius: var(--any-radius-lg);
  box-shadow: var(--any-shadow-md);
  z-index: 1000;
}

[data-theme="dark"] .error-toast {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
