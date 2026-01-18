<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { chatApi } from '@/api/chat'
import { 
  Search, FileText, Presentation, BarChart3, 
  Plus, Users, Mic, ArrowUp, Sparkles, Globe, FileVideo,
  Languages, MoreHorizontal, Bell, PlusCircle, FolderOpen,
  History, Settings, LayoutGrid
} from 'lucide-vue-next'
import AnySidebar from '@/components/common/AnySidebar.vue'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnyButton from '@/components/common/AnyButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()

const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)
const activeCategory = ref('all')
const sidebarCollapsed = ref(false)

// Sidebar navigation sections
const sidebarSections = [
  {
    id: 'main',
    items: [
      { id: 'search', label: '搜索', icon: Search },
      { id: 'templates', label: '模板', icon: LayoutGrid },
      { id: 'files', label: '文件', icon: FolderOpen },
      { id: 'history', label: '历史', icon: History },
    ]
  }
]

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

// 处理提交 - 创建 session 并跳转到执行页面
const handleSubmit = async () => {
  if (!inputValue.value.trim() || isLoading.value) return
  
  isLoading.value = true
  try {
    // 获取当前 workspace_id
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    
    // 创建新 session
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: inputValue.value.slice(0, 50) // 使用输入内容前50字符作为标题
    })
    
    // 发送初始消息（异步，不等待完成）
    chatApi.sendMessageStream(
      session.id,
      { content: inputValue.value },
      () => {}, // SSE 事件由执行页面处理
      (err) => console.error('Initial message error:', err)
    )
    
    // 跳转到执行页面
    router.push(`/execution/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
    // 如果创建失败，fallback 到 chat 页面
    router.push({
      path: '/chat',
      query: { q: inputValue.value }
    })
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

// 处理快捷芯片点击 - 创建 session 并跳转到执行页面
const handleChipClick = async (chip: typeof quickChips[0]) => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: chip.label
    })
    
    // 发送初始消息，带上模式指令
    chatApi.sendMessageStream(
      session.id,
      { content: `我想要${chip.label}` },
      () => {},
      (err) => console.error('Initial message error:', err)
    )
    
    router.push(`/execution/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
    router.push({ path: '/chat', query: { mode: chip.id } })
  } finally {
    isLoading.value = false
  }
}

// 处理模板点击 - 创建 session 并跳转到执行页面
const handleTemplateClick = async (template: typeof templates[0]) => {
  if (isLoading.value) return
  
  isLoading.value = true
  try {
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: template.title
    })
    
    // 发送初始消息，带上模板指令
      chatApi.sendMessageStream(
        session.id,
        { content: `请帮我${template.title}` },
      () => {},
      (err) => console.error('Initial message error:', err)
    )
    
    router.push(`/execution/${session.id}`)
  } catch (error) {
    console.error('Failed to create session:', error)
    router.push({ path: '/chat', query: { template: template.id } })
  } finally {
    isLoading.value = false
  }
}

// 处理附件按钮点击
const handleAttachClick = () => {
  fileInputRef.value?.click()
}

// 处理文件选择 - 创建 session 并跳转到执行页面
const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0 && !isLoading.value) {
    const fileNames = Array.from(input.files).map(f => f.name).join(', ')
    
    isLoading.value = true
    try {
      const workspaceId = sessionStore.currentWorkspaceId || 'default'
      const session = await sessionStore.createSession({
        workspace_id: workspaceId,
        title: `处理文件: ${fileNames.slice(0, 30)}`
      })
      
      // TODO: 实际项目中应先上传文件，然后发送带 attachments 的消息
      chatApi.sendMessageStream(
        session.id,
        { content: `请帮我处理这些文件: ${fileNames}` },
        () => {},
        (err) => console.error('Initial message error:', err)
      )
      
      router.push(`/execution/${session.id}`)
    } catch (error) {
      console.error('Failed to create session:', error)
      router.push({ path: '/chat', query: { files: fileNames } })
    } finally {
      isLoading.value = false
    }
  }
}

// 处理登出
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Sidebar navigation handler
const handleNavClick = (item: { id: string }) => {
  switch (item.id) {
    case 'search':
      inputRef.value?.focus()
      break
    case 'history':
      router.push('/chat')
      break
    case 'settings':
      // TODO: Open settings
      break
  }
}

// Sidebar new button handler
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

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="home-view">
    <!-- 左侧边栏 - AnyGen 风格 -->
    <AnySidebar
      v-model:collapsed="sidebarCollapsed"
      :sections="sidebarSections"
      :show-footer="true"
      @nav-click="handleNavClick"
      @new-click="handleNewClick"
    >
      <template #footer>
        <button class="any-sidebar__footer-btn" @click="handleLogout" title="退出登录">
          <Settings class="w-5 h-5" />
        </button>
      </template>
    </AnySidebar>
    
    <!-- Header - AnyGen 风格右上角 -->
    <AnyHeader :sidebar-collapsed="sidebarCollapsed">
      <template #right>
        <!-- 通知铃铛 -->
        <button class="header-icon-btn" title="通知">
          <Bell class="w-5 h-5" />
          <span class="notification-badge">4</span>
        </button>
        <!-- 积分/Token -->
        <div class="credits-badge">
          <Sparkles class="w-4 h-4" />
          <span>1,200</span>
        </div>
        <!-- 用户头像 -->
        <button class="avatar-btn">
          <span>{{ authStore.user?.display_name?.charAt(0) || authStore.user?.username?.charAt(0) || 'U' }}</span>
        </button>
      </template>
    </AnyHeader>
    
    <!-- Main Content -->
    <main class="home-main" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <!-- Hero: 大标题 -->
      <section class="hero-section">
        <h1 class="hero-title">How can I help you today?</h1>
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
              <AnyButton variant="ghost" size="sm" @click="handleAttachClick" title="添加文件">
                <Plus class="w-5 h-5" />
              </AnyButton>
              <input type="file" ref="fileInputRef" class="hidden" multiple @change="handleFileSelect" />
              <AnyButton variant="ghost" size="sm" title="添加协作者">
                <Users class="w-5 h-5" />
              </AnyButton>
            </div>
            <div class="toolbar-right">
              <AnyButton variant="ghost" size="sm" title="语音输入">
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
            <component :is="chip.icon" class="w-4 h-4" />
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
            <component :is="chip.icon" class="w-4 h-4" />
            <span>{{ chip.label }}</span>
          </button>
          <button class="chip chip-more">
            <MoreHorizontal class="w-4 h-4" />
            <span>更多</span>
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
            <component v-if="cat.icon" :is="cat.icon" class="w-4 h-4" />
            <span>{{ cat.label }}</span>
            <span v-if="cat.badge" class="category-badge">{{ cat.badge }}</span>
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
            <div class="template-preview" :class="{ 'has-preview': tpl.preview }">
              <!-- 图标类型（无预览图） -->
              <div v-if="tpl.icon" class="template-icon-wrapper" :style="{ background: tpl.bgColor }">
                <component :is="tpl.icon" class="w-10 h-10" :style="{ color: tpl.iconColor }" />
              </div>
              <!-- 预览图类型 -->
              <div v-else class="template-thumbnail" :class="`thumbnail--${tpl.preview}`"></div>
            </div>
            <!-- 文字信息 -->
            <div class="template-info">
              <span class="template-title">{{ tpl.title }}</span>
              <div v-if="tpl.tag" class="template-meta">
                <span class="template-tag" :class="`tag--${tpl.tag.toLowerCase()}`">{{ tpl.tag }}</span>
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
  display: flex;
}

/* Header icon buttons */
.header-icon-btn {
  @apply relative p-2 rounded-full cursor-pointer;
  color: var(--any-text-secondary);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.header-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

.notification-badge {
  @apply absolute -top-0.5 -right-0.5
         min-w-[18px] h-[18px] px-1
         flex items-center justify-center
         text-xs font-medium text-white
         bg-red-500 rounded-full;
}

.credits-badge {
  @apply flex items-center gap-1.5 px-3 py-1.5
         text-sm rounded-full;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
}

.avatar-btn {
  @apply w-9 h-9 flex items-center justify-center
         text-sm font-medium text-white
         bg-purple-500 rounded-full
         cursor-pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.avatar-btn:hover {
  @apply bg-purple-600;
}

/* Main Content - 整个右侧主区域 */
.home-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
  padding-top: max(15vh, 120px);
  padding-bottom: 4rem;
  overflow-y: auto;
  min-height: 100vh;
}

/* Hero Section */
.hero-section {
  @apply text-center mb-10;
  width: 100%;
  max-width: 720px;
}

.hero-title {
  @apply text-3xl md:text-4xl font-semibold;
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
  color: var(--any-text-muted);
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
  color: var(--any-text-muted);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.submit-btn.active {
  background: var(--any-text-primary);
  color: white;
}

.submit-btn:disabled {
  @apply cursor-not-allowed opacity-50;
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
  color: var(--any-text-muted);
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
  color: var(--any-text-muted);
  margin-bottom: -1px;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.category-tab:hover {
  color: var(--any-text-secondary);
}

.category-tab.active {
  @apply font-medium;
  color: var(--any-text-primary);
  border-color: var(--any-text-primary);
}

.category-badge {
  @apply text-xs px-1.5 py-0.5 rounded;
  background: #FEE2E2;
  color: #DC2626;
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
  @apply bg-blue-100 text-blue-600;
}

.tag--doc {
  @apply bg-purple-100 text-purple-600;
}

.template-uses {
  @apply text-xs;
  color: var(--any-text-muted);
}

/* Hidden utility */
.hidden {
  display: none;
}
</style>
