<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { useAuthGuard } from '@/composables/useAuthGuard'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import { 
  Search, FileText, Presentation, BarChart3, 
  Plus, Users, Mic, ArrowUp, Sparkles, Globe, FileVideo,
  Languages, MoreHorizontal, Bell, FolderOpen,
  History, Settings, LayoutGrid, User, LogOut,
  Sun, Moon, Monitor
} from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()
const themeStore = useThemeStore()
const { requireAuth, showLogin } = useAuthGuard()

const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)
const activeCategory = ref('all')
const errorMessage = ref('')
const showUserMenu = ref(false)
const showThemeMenu = ref(false)

// 主题选项
const themeOptions: { mode: ThemeMode; label: string; icon: typeof Sun }[] = [
  { mode: 'light', label: '浅色', icon: Sun },
  { mode: 'dark', label: '深色', icon: Moon },
  { mode: 'system', label: '跟随系统', icon: Monitor },
]

// 显示错误提示
const showError = (msg: string) => {
  errorMessage.value = msg
  setTimeout(() => {
    errorMessage.value = ''
  }, 4000)
}

// 登出
const handleLogout = () => {
  showUserMenu.value = false
  authStore.logout()
  sessionStore.setCurrentWorkspace(null)
  router.push('/login')
}

// 点击外部关闭菜单
const closeMenus = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-container')) {
    showUserMenu.value = false
  }
  if (!target.closest('.theme-menu-container')) {
    showThemeMenu.value = false
  }
}

// 选择主题
const selectTheme = (mode: ThemeMode) => {
  themeStore.setMode(mode)
  showThemeMenu.value = false
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

// 处理提交 - 创建 session 并跳转到执行页面
const handleSubmit = async () => {
  if (!inputValue.value.trim() || isLoading.value) return
  
  // 需要登录才能提交任务
  const canProceed = await requireAuth('请先登录后发送请求')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    // 获取当前 workspace_id
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    
    // 创建新 session
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: inputValue.value.slice(0, 50) // 使用输入内容前50字符作为标题
    })
    
    // 跳转到执行页面，带上初始 query
    router.push({
      path: `/execution/${session.id}`,
      query: { task: inputValue.value }
    })
  } catch (error) {
    console.error('Failed to create session:', error)
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

// 处理快捷芯片点击 - 创建 session 并跳转到执行页面
const handleChipClick = async (chip: typeof quickChips[0]) => {
  if (isLoading.value) return
  
  // 需要登录才能使用快捷操作
  const canProceed = await requireAuth('请先登录后使用快捷操作')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: chip.label
    })
    
    router.push({
      path: `/execution/${session.id}`,
      query: { task: `我想要${chip.label}` }
    })
  } catch (error) {
    console.error('Failed to create session:', error)
    showError('系统开小差了，请稍等片刻再试 ☕')
  } finally {
    isLoading.value = false
  }
}

// 处理模板点击 - 创建 session 并跳转到执行页面
const handleTemplateClick = async (template: typeof templates[0]) => {
  if (isLoading.value) return
  
  // 需要登录才能使用模板
  const canProceed = await requireAuth('请先登录后使用模板')
  if (!canProceed) return
  
  isLoading.value = true
  try {
    const workspaceId = sessionStore.currentWorkspaceId || 'default'
    const session = await sessionStore.createSession({
      workspace_id: workspaceId,
      title: template.title
    })
    
    router.push({
      path: `/execution/${session.id}`,
      query: { task: `请帮我${template.title}` }
    })
  } catch (error) {
    console.error('Failed to create session:', error)
    showError('有点小状况，请稍后再试试 🙏')
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
    
    // 需要登录才能上传文件
    const canProceed = await requireAuth('请先登录后上传文件')
    if (!canProceed) {
      input.value = '' // 清空文件选择
      return
    }
    
    isLoading.value = true
    try {
      const workspaceId = sessionStore.currentWorkspaceId || 'default'
      const session = await sessionStore.createSession({
        workspace_id: workspaceId,
        title: `处理文件: ${fileNames.slice(0, 30)}`
      })
      
      // TODO: 实际项目中应先上传文件
      router.push({
        path: `/execution/${session.id}`,
        query: { task: `请帮我处理这些文件: ${fileNames}` }
      })
    } catch (error) {
      console.error('Failed to create session:', error)
      showError('文件处理遇到了麻烦，请稍后重试 📁')
    } finally {
      isLoading.value = false
    }
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

onMounted(() => {
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('click', closeMenus)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('click', closeMenus)
})
</script>

<template>
  <div class="home-view">
    <!-- 左侧边栏 - 固定宽度图标栏 -->
    <aside class="icon-sidebar">
      <div class="sidebar-top">
        <!-- Logo -->
        <div class="sidebar-logo">
          <span class="logo-text">T</span>
        </div>
        <!-- New -->
        <button
          class="sidebar-icon-btn"
          data-tooltip="新建任务"
          @click="handleNewClick"
        >
          <Plus class="w-5 h-5" />
        </button>
        <!-- Nav items -->
        <button
          class="sidebar-icon-btn"
          data-tooltip="搜索"
          @click="inputRef?.focus()"
        >
          <Search class="w-5 h-5" />
        </button>
        <button
          class="sidebar-icon-btn"
          data-tooltip="模板"
        >
          <LayoutGrid class="w-5 h-5" />
        </button>
        <button
          class="sidebar-icon-btn"
          data-tooltip="文件"
        >
          <FolderOpen class="w-5 h-5" />
        </button>
        <button
          class="sidebar-icon-btn"
          data-tooltip="历史"
        >
          <History class="w-5 h-5" />
        </button>
      </div>
      <div class="sidebar-bottom">
        <button
          class="sidebar-icon-btn"
          data-tooltip="设置"
        >
          <Settings class="w-5 h-5" />
        </button>
      </div>
    </aside>
    
    <!-- 右上角个人信息栏 - 固定定位 -->
    <header class="top-header">
      <!-- 主题切换 -->
      <div class="theme-menu-container">
        <button
          class="header-icon-btn"
          data-tooltip="主题"
          @click="showThemeMenu = !showThemeMenu"
        >
          <Sun
            v-if="themeStore.resolvedTheme === 'light'"
            class="w-4 h-4"
          />
          <Moon
            v-else
            class="w-4 h-4"
          />
        </button>
        <!-- 主题下拉菜单 -->
        <Transition name="dropdown">
          <div
            v-if="showThemeMenu"
            class="theme-dropdown"
          >
            <button
              v-for="opt in themeOptions"
              :key="opt.mode"
              class="dropdown-item"
              :class="{ active: themeStore.mode === opt.mode }"
              @click="selectTheme(opt.mode)"
            >
              <component
                :is="opt.icon"
                class="w-4 h-4"
              />
              <span>{{ opt.label }}</span>
              <span
                v-if="themeStore.mode === opt.mode"
                class="check-mark"
              >✓</span>
            </button>
          </div>
        </Transition>
      </div>
      
      <!-- 游客模式：显示登录按钮 -->
      <template v-if="!authStore.isAuthenticated">
        <button 
          class="sign-in-btn"
          @click="showLogin()"
        >
          <User class="w-4 h-4" />
          <span>Sign in</span>
        </button>
      </template>
      
      <!-- 已登录：显示通知、积分、头像 -->
      <template v-else>
        <!-- 通知铃铛 -->
        <button
          class="header-icon-btn"
          data-tooltip="通知"
        >
          <Bell class="w-4 h-4" />
          <span class="notification-badge">4</span>
        </button>
        <!-- 积分/Token -->
        <div class="credits-badge">
          <Sparkles class="w-3 h-3" />
          <span>1,200</span>
        </div>
        <!-- 用户头像和下拉菜单 -->
        <div class="user-menu-container">
          <button 
            class="avatar-btn"
            @click="showUserMenu = !showUserMenu"
          >
            <span>{{ authStore.user?.display_name?.charAt(0) || authStore.user?.username?.charAt(0) || 'U' }}</span>
          </button>
          <!-- 下拉菜单 -->
          <Transition name="dropdown">
            <div
              v-if="showUserMenu"
              class="user-dropdown"
            >
              <div class="dropdown-header">
                <span class="user-name">{{ authStore.user?.display_name || authStore.user?.username }}</span>
                <span class="user-email">{{ authStore.user?.email }}</span>
              </div>
              <div class="dropdown-divider" />
              <button
                class="dropdown-item"
                @click="handleLogout"
              >
                <LogOut class="w-4 h-4" />
                <span>退出登录</span>
              </button>
            </div>
          </Transition>
        </div>
      </template>
    </header>
    
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

/* 固定左侧图标栏 */
.icon-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 56px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 12px 8px;
  background: var(--any-bg-secondary);
  border-right: 1px solid var(--any-border);
  z-index: 100;
}

.sidebar-top,
.sidebar-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.sidebar-logo {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: var(--any-text-primary);
  font-family: serif;
}

.sidebar-icon-btn {
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

.sidebar-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

/* Custom Tooltip */
.sidebar-icon-btn[data-tooltip] {
  position: relative;
}

.sidebar-icon-btn[data-tooltip]::after {
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

.sidebar-icon-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

/* 右上角固定 Header */
.top-header {
  position: fixed;
  top: 12px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 100;
}

/* Header icon buttons */
.header-icon-btn {
  @apply relative p-1.5 rounded-full cursor-pointer;
  color: var(--any-text-secondary);
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.header-icon-btn:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

/* Header tooltip */
.header-icon-btn[data-tooltip] {
  position: relative;
}

.header-icon-btn[data-tooltip]::after {
  content: attr(data-tooltip);
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-top: 6px;
  padding: 4px 8px;
  background: var(--any-text-primary);
  color: var(--any-bg-primary);
  font-size: 11px;
  white-space: nowrap;
  border-radius: var(--any-radius-sm);
  opacity: 0;
  visibility: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-default);
  pointer-events: none;
  z-index: 1000;
}

.header-icon-btn[data-tooltip]:hover::after {
  opacity: 1;
  visibility: visible;
}

.notification-badge {
  @apply absolute -top-0.5 -right-0.5
         min-w-[14px] h-[14px] px-0.5
         flex items-center justify-center
         text-[10px] font-medium text-white
         bg-red-500 rounded-full;
}

.credits-badge {
  @apply flex items-center gap-1 px-2 py-1
         text-xs rounded-full;
  color: var(--any-text-secondary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
}

.avatar-btn {
  @apply w-7 h-7 flex items-center justify-center
         text-xs font-medium text-white
         bg-purple-500 rounded-full
         cursor-pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.avatar-btn:hover {
  @apply bg-purple-600;
}

/* Theme menu dropdown */
.theme-menu-container {
  position: relative;
}

.theme-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 140px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg, 12px);
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
  z-index: 1000;
  padding: 4px;
}

.theme-dropdown .dropdown-item {
  border-radius: var(--any-radius-md);
  padding: 8px 12px;
}

.theme-dropdown .dropdown-item.active {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.check-mark {
  margin-left: auto;
  color: var(--any-success);
  font-weight: 600;
}

/* User menu dropdown */
.user-menu-container {
  position: relative;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 8px;
  min-width: 200px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg, 12px);
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
  z-index: 1000;
}

.dropdown-header {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.user-email {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

.dropdown-divider {
  height: 1px;
  background: var(--any-border);
}

.dropdown-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.dropdown-item:hover {
  color: var(--any-text-primary);
  background: var(--any-bg-tertiary);
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Sign in button for guest mode */
.sign-in-btn {
  @apply flex items-center gap-1.5 px-4 py-2
         text-sm font-medium rounded-full
         cursor-pointer;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  transition: all var(--any-duration-fast) var(--any-ease-default);
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
  color: white;
  border-color: var(--any-text-primary);
}

.submit-btn:disabled {
  @apply cursor-not-allowed;
  opacity: 0.7;  /* 提高 disabled 状态可见度 */
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
  background: rgba(139, 92, 246, 0.15);
  color: #8B5CF6;
}

[data-theme="dark"] .tag--doc {
  background: rgba(139, 92, 246, 0.25);
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
