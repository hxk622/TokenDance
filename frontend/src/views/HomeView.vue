<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useAuthStore } from '@/stores/auth'
import { useSearchStore } from '@/stores/search'
import { useAuthGuard } from '@/composables/useAuthGuard'
import { 
  Search, FileText, Presentation, BarChart3, 
  Mic, ArrowUp, Globe, FileVideo,
  Languages, FolderOpen, MoreHorizontal, Code2, Zap,
  History, ChevronRight, Paperclip, Sparkles
} from 'lucide-vue-next'
import AnySidebar from '@/components/common/AnySidebar.vue'
import AnyHeader from '@/components/common/AnyHeader.vue'
import type { NavItem, RecentItem, SidebarSection } from '@/components/common/AnySidebar.vue'
import type { Project, ProjectType } from '@/types/project'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()
const authStore = useAuthStore()
const searchStore = useSearchStore()
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

// Convert projects to sidebar recent items
const sidebarRecentItems = computed<RecentItem[]>(() => 
  projectStore.activeProjects.slice(0, 8).map(p => ({
    id: p.id,
    title: p.title,
    type: 'task' as const,
    icon: getProjectIcon(p.project_type)
  }))
)

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
const sidebarSections = computed<SidebarSection[]>(() => [
  {
    id: 'main',
    items: [
      { id: 'files', label: '文件', icon: FolderOpen, href: '/files', active: route.path.startsWith('/files') },
      { id: 'history', label: '历史', icon: History, href: '/history', active: route.path.startsWith('/history') },
    ] as NavItem[]
  }
])

const handleSidebarNavClick = (item: NavItem) => {
  switch (item.id) {
    case 'search':
      searchStore.open()
      break
    case 'history':
      router.push('/history')
      break
    case 'library':
      router.push('/files')
      break
    case 'files':
      router.push('/files')
      break
  }
}

// Handle recent item click
const handleRecentClick = (item: RecentItem) => {
  router.push(`/project/${item.id}`)
}

// New button handler
const handleNewClick = () => {
  inputRef.value?.focus()
}

// Token click handler - show usage details
const handleTokenClick = () => {
  // TODO: Open token usage modal or navigate to billing page
  showError('Token 用量详情功能即将上线')
}

// Mobile app click handler
const handleMobileClick = () => {
  showError('移动端 App 即将上线，敬请期待')
}


onMounted(async () => {
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

</script>

<template>
  <div class="home-view">
    <!-- Sidebar with collapse/expand -->
    <AnySidebar
      :sections="sidebarSections"
      :recent-items="sidebarRecentItems"
      :token-used="authStore.monthlyTokensUsed"
      :token-total="authStore.maxMonthlyTokens"
      @new-click="handleNewClick"
      @nav-click="handleSidebarNavClick"
      @recent-click="handleRecentClick"
      @token-click="handleTokenClick"
      @mobile-click="handleMobileClick"
    />
    
    <!-- Header -->
    <AnyHeader :transparent="true" />
    
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
      <!-- Hero Title -->
      <section class="hero-section">
        <h1 class="hero-title">
          今天我能帮你做什么？
        </h1>
      </section>

      <!-- Input Box - AnyGen Style -->
      <section class="input-section">
        <div class="input-box">
          <!-- Textarea -->
          <div class="input-content">
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
          </div>
          
          <!-- Toolbar -->
          <div class="input-toolbar">
            <div class="toolbar-left">
              <button
                class="toolbar-btn"
                title="添加附件"
                @click="handleAttachClick"
              >
                <Paperclip class="w-5 h-5" />
              </button>
              <input
                ref="fileInputRef"
                type="file"
                class="hidden"
                multiple
                @change="handleFileSelect"
              >
            </div>
            <div class="toolbar-right">
              <button
                class="toolbar-btn"
                title="语音输入"
              >
                <Mic class="w-5 h-5" />
              </button>
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
  position: relative;
  min-height: 100vh;
  background: var(--any-bg-primary);
}

/* Main Content */
.home-main {
  margin-left: var(--sidebar-width);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 16px;
  padding-top: 70px;
  padding-bottom: 4rem;
  overflow-y: auto;
  scrollbar-gutter: stable;
}

@media (min-width: 768px) {
  .home-main {
    padding-top: max(12vh, 100px);
  }
}

/* Hero Section */
.hero-section {
  text-align: center;
  margin-bottom: 24px;
  width: 100%;
  max-width: 720px;
}

@media (min-width: 768px) {
  .hero-section {
    margin-bottom: 40px;
  }
}

.hero-title {
  font-size: 24px;
  font-weight: 500;
  color: var(--any-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  letter-spacing: -0.02em;
  margin: 0;
}

@media (min-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
}

/* ============================================
   Input Box - AnyGen Style
   ============================================ */
.input-section {
  margin-bottom: 12px;
  width: 100%;
  max-width: 720px;
}

.input-box {
  position: relative;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 20px;
  box-shadow: 0 12px 20px 0 rgba(28, 28, 32, 0.05);
  overflow: hidden;
  transition: all var(--any-duration-normal) var(--any-ease-out);
}

.input-box:focus-within {
  border-color: var(--any-border-hover);
  box-shadow: 0 12px 24px 0 rgba(28, 28, 32, 0.08);
}

.input-content {
  min-height: 52px;
  max-height: 200px;
  padding: 14px 16px;
  padding-bottom: 0;
}

.main-textarea {
  width: 100%;
  min-height: 26px;
  max-height: 120px;
  font-size: 16px;
  line-height: 26px;
  color: var(--any-text-primary);
  background: transparent;
  border: none;
  resize: none;
  outline: none;
}

.main-textarea::placeholder {
  color: var(--any-text-muted);
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-top: none;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  color: var(--any-text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.toolbar-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.submit-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  background: var(--any-bg-tertiary);
  color: var(--any-text-tertiary);
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.submit-btn.active {
  background: var(--any-text-primary);
  color: var(--any-text-inverse);
}

.submit-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

/* ============================================
   Projects Section
   ============================================ */
.projects-section {
  margin-bottom: 40px;
  width: 100%;
  max-width: 720px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.see-all-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  font-size: 14px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.see-all-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-hover);
}

.projects-grid {
  display: grid;
  gap: 12px;
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
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  text-align: left;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.project-card:hover {
  border-color: var(--any-border-hover);
  background: var(--any-bg-tertiary);
}

.project-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  flex-shrink: 0;
  background: var(--any-bg-tertiary);
}

.project-icon {
  width: 20px;
  height: 20px;
  color: var(--any-text-secondary);
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-meta {
  display: block;
  font-size: 12px;
  margin-top: 2px;
  color: var(--any-text-tertiary);
}

.project-chevron {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--any-text-tertiary);
  opacity: 0;
  transition: opacity var(--any-duration-fast) var(--any-ease-out);
}

.project-card:hover .project-chevron {
  opacity: 1;
}

/* ============================================
   Quick Chips - AnyGen Style
   ============================================ */
.chips-section {
  margin-bottom: 32px;
  width: 100%;
  max-width: 720px;
}

.chips-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 10px;
}

.chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 14px;
  border-radius: 9999px;
  cursor: pointer;
  color: var(--any-text-secondary);
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.chip:hover:not(:disabled) {
  border-color: var(--any-border-hover);
  background: var(--any-bg-tertiary);
}

.chip:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chip-more {
  color: var(--any-text-secondary);
}

/* ============================================
   Categories Tabs - AnyGen Style
   ============================================ */
.categories-section {
  margin-bottom: 24px;
  width: 100%;
  max-width: 960px;
  border-bottom: 1px solid var(--any-border);
}

.categories-scroll {
  display: flex;
  align-items: center;
  gap: 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.categories-scroll::-webkit-scrollbar {
  display: none;
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  font-size: 14px;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: var(--any-text-tertiary);
  background: transparent;
  border-left: none;
  border-right: none;
  border-top: none;
  margin-bottom: -1px;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.category-tab:hover {
  color: var(--any-text-primary);
}

.category-tab.active {
  font-weight: 500;
  color: var(--any-text-primary);
  border-bottom-color: var(--any-text-primary);
}

.category-badge {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(239, 68, 68, 0.15);
  color: var(--any-error);
}

/* ============================================
   Template Cards - AnyGen Style
   ============================================ */
.templates-section {
  padding: 24px 0;
  width: 100%;
  max-width: 960px;
}

.templates-grid {
  display: grid;
  gap: 20px;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
}

@media (min-width: 1400px) {
  .templates-grid {
    grid-template-columns: repeat(5, 1fr);
  }
}

.template-card {
  display: flex;
  flex-direction: column;
  background: transparent;
  cursor: pointer;
  text-align: left;
  border: none;
  transition: all var(--any-duration-normal) var(--any-ease-out);
}

.template-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.template-card:hover:not(:disabled) .template-preview {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  transform: translateY(-4px);
}

/* Preview area */
.template-preview {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  aspect-ratio: 4 / 3;
  transition: all var(--any-duration-normal) cubic-bezier(0.34, 1.56, 0.64, 1);
}

.template-preview.has-preview {
  padding: 0;
}

/* Icon type card */
.template-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Thumbnail type card */
.template-thumbnail {
  width: 100%;
  height: 100%;
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

/* Text info */
.template-info {
  padding: 12px 0;
}

.template-title {
  font-size: 14px;
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
  color: var(--any-text-primary);
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
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
  background: rgba(139, 92, 246, 0.15);
  color: #8B5CF6;
}

[data-theme="dark"] .tag--doc {
  background: rgba(139, 92, 246, 0.25);
  color: #A78BFA;
}

.template-uses {
  font-size: 12px;
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
