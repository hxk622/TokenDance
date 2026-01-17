<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'
import { chatApi } from '@/api/chat'
import { 
  Search, FileText, Presentation, BarChart3, Code, 
  Plus, Users, Mic, ArrowUp, Sparkles, Globe, FileVideo,
  Languages, MoreHorizontal
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const sessionStore = useSessionStore()

const inputValue = ref('')
const inputRef = ref<HTMLTextAreaElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const isLoading = ref(false)
const activeCategory = ref('all')

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
  { id: 'hot', label: '热门推荐', badge: '🔥' },
  { id: 'marketing', label: '市场增长' },
  { id: 'product', label: '产品研究' },
  { id: 'gtm', label: '市场进入' },
  { id: 'learning', label: '学习成长' },
  { id: 'career', label: '职业发展' },
  { id: 'my', label: '我的模板', icon: Sparkles },
]

// 模板卡片
const templates = [
  { 
    id: 'ppt-basic', 
    title: 'PPT 制作', 
    desc: '快速生成专业演示文稿',
    category: 'all',
    icon: Presentation,
    color: 'orange',
    image: null
  },
  { 
    id: 'market-research', 
    title: '市场调研报告', 
    desc: '竞品分析与行业洞察',
    category: 'product',
    icon: BarChart3,
    color: 'blue',
    image: null
  },
  { 
    id: 'okr-review', 
    title: 'OKR 回顾', 
    desc: '季度目标复盘与总结',
    category: 'career',
    icon: FileText,
    color: 'indigo',
    image: null
  },
  { 
    id: 'news-digest', 
    title: '新闻摘要', 
    desc: '自动整理行业资讯',
    category: 'hot',
    icon: Globe,
    color: 'cyan',
    image: null
  },
  { 
    id: 'meeting-agenda', 
    title: '会议议程', 
    desc: '结构化会议议程生成',
    category: 'all',
    icon: Users,
    color: 'purple',
    image: null
  },
  { 
    id: 'code-review', 
    title: '代码审查', 
    desc: '自动化代码质量检查',
    category: 'all',
    icon: Code,
    color: 'emerald',
    image: null
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
      { content: `请帮我${template.title}: ${template.desc}` },
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

onUnmounted(() => {
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<template>
  <div class="home-view">
    <!-- 背景 -->
    <div class="bg-layer">
      <div class="bg-gradient" />
      <div class="bg-pattern" />
    </div>
    
    <!-- Main Content - AnyGen 风格中央布局 -->
    <main class="home-main">
      <!-- Hero: 大标题 -->
      <section class="hero-section">
        <h1 class="hero-title">我能帮你做什么？</h1>
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
              <button class="tool-btn" @click="handleAttachClick" title="添加文件">
                <Plus class="w-5 h-5" />
              </button>
              <input type="file" ref="fileInputRef" class="hidden" multiple @change="handleFileSelect" />
              <button class="tool-btn" title="添加协作者">
                <Users class="w-5 h-5" />
              </button>
            </div>
            <div class="toolbar-right">
              <button class="tool-btn" title="语音输入">
                <Mic class="w-5 h-5" />
              </button>
              <button 
                class="submit-btn"
                :class="{ active: inputValue.trim() }"
                :disabled="!inputValue.trim()"
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
            :class="`template-card--${tpl.color}`"
            @click="handleTemplateClick(tpl)"
          >
            <div class="template-icon">
              <component :is="tpl.icon" class="w-8 h-8" />
            </div>
            <div class="template-content">
              <span class="template-title">{{ tpl.title }}</span>
              <span class="template-desc">{{ tpl.desc }}</span>
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
  background: #fafafa;
}

/* Background Layer */
.bg-layer {
  @apply absolute inset-0 -z-10 overflow-hidden;
}

.bg-gradient {
  @apply absolute inset-0;
  background: linear-gradient(180deg, #ffffff 0%, #f5f5f5 100%);
}

.bg-pattern {
  @apply absolute inset-0 opacity-[0.4];
  background-image: radial-gradient(circle at center, #e5e5e5 1px, transparent 1px);
  background-size: 24px 24px;
}

/* Main Content */
.home-main {
  @apply max-w-4xl w-full mx-auto px-6;
  padding-top: 12vh;
  padding-bottom: 4rem;
}

/* Hero Section */
.hero-section {
  @apply text-center mb-8;
}

.hero-title {
  @apply text-3xl md:text-4xl font-semibold text-gray-900;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ============================================
   Input Box - AnyGen Style
   ============================================ */
.input-section {
  @apply mb-6;
}

.input-box {
  @apply bg-white rounded-2xl border border-gray-200 shadow-sm;
  padding: 16px 20px;
  transition: all 0.2s ease;
}

.input-box:focus-within {
  @apply border-gray-300 shadow-md;
}

.main-textarea {
  @apply w-full text-base text-gray-900 placeholder-gray-400
         bg-transparent border-none resize-none;
  min-height: 24px;
  max-height: 120px;
  line-height: 1.5;
}

.main-textarea:focus {
  outline: none;
}

.input-toolbar {
  @apply flex items-center justify-between mt-3 pt-3 border-t border-gray-100;
}

.toolbar-left,
.toolbar-right {
  @apply flex items-center gap-2;
}

.tool-btn {
  @apply p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100
         rounded-lg cursor-pointer transition-all duration-150;
}

.submit-btn {
  @apply p-2.5 rounded-full cursor-pointer transition-all duration-150;
  background: #e5e5e5;
  color: #9ca3af;
}

.submit-btn.active {
  background: #111827;
  color: white;
}

.submit-btn:disabled {
  @apply cursor-not-allowed;
}

/* ============================================
   Quick Chips - AnyGen Style
   ============================================ */
.chips-section {
  @apply mb-8;
}

.chips-row {
  @apply flex flex-wrap items-center justify-center gap-2 mb-2;
}

.chip {
  @apply flex items-center gap-2 px-4 py-2
         text-sm text-gray-600
         bg-white border border-gray-200 rounded-full
         hover:border-gray-300 hover:bg-gray-50
         cursor-pointer transition-all duration-150;
}

.chip:hover {
  @apply shadow-sm;
}

.chip-more {
  @apply text-gray-500;
}

/* ============================================
   Categories Tabs - AnyGen Style
   ============================================ */
.categories-section {
  @apply mb-6 border-b border-gray-200;
}

.categories-scroll {
  @apply flex items-center gap-1 overflow-x-auto pb-0;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}

.categories-scroll::-webkit-scrollbar {
  display: none;
}

.category-tab {
  @apply flex items-center gap-1.5 px-4 py-3
         text-sm text-gray-500 whitespace-nowrap
         border-b-2 border-transparent
         hover:text-gray-700
         cursor-pointer transition-all duration-150;
}

.category-tab.active {
  @apply text-gray-900 border-gray-900 font-medium;
}

.category-badge {
  @apply text-xs;
}

/* ============================================
   Template Cards - AnyGen Style
   ============================================ */
.templates-section {
  @apply py-6;
}

.templates-grid {
  @apply grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4;
}

.template-card {
  @apply flex flex-col p-4 bg-white rounded-xl border border-gray-200
         hover:border-gray-300 hover:shadow-md
         cursor-pointer transition-all duration-200 text-left;
  min-height: 140px;
}

.template-card:hover {
  transform: translateY(-2px);
}

.template-icon {
  @apply w-12 h-12 rounded-xl flex items-center justify-center mb-3;
}

.template-card--orange .template-icon {
  @apply bg-orange-100 text-orange-600;
}

.template-card--blue .template-icon {
  @apply bg-blue-100 text-blue-600;
}

.template-card--indigo .template-icon {
  @apply bg-indigo-100 text-indigo-600;
}

.template-card--cyan .template-icon {
  @apply bg-cyan-100 text-cyan-600;
}

.template-card--purple .template-icon {
  @apply bg-purple-100 text-purple-600;
}

.template-card--emerald .template-icon {
  @apply bg-emerald-100 text-emerald-600;
}

.template-content {
  @apply flex flex-col gap-1;
}

.template-title {
  @apply text-sm font-medium text-gray-900;
}

.template-desc {
  @apply text-xs text-gray-500 line-clamp-2;
}

/* Hidden utility */
.hidden {
  display: none;
}

/* Suggestions Section - Dark Theme Default */
.suggestions-section {
  @apply mb-10;
}

.suggestions-list {
  @apply space-y-2;
}

.suggestion-item {
  @apply w-full flex items-center gap-3 px-4 py-3
         text-sm text-gray-300
         bg-gray-900/60 border border-gray-800 rounded-lg
         hover:bg-gray-900 hover:border-gray-700
         cursor-pointer transition-all duration-200 text-left;
}

/* Workflows Section - Dark Theme Default */
.workflows-section {
  @apply mb-10;
}

.workflows-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.workflow-card {
  @apply flex items-center gap-4 p-5
         bg-gray-900 border border-gray-800 rounded-xl
         hover:border-gray-700
         cursor-pointer transition-all duration-200 text-left;
}

.workflow-icon {
  @apply w-11 h-11 rounded-lg flex items-center justify-center flex-shrink-0;
}

.workflow-card--indigo .workflow-icon {
  @apply bg-indigo-900/50 text-indigo-400;
}

.workflow-card--amber .workflow-icon {
  @apply bg-amber-900/50 text-amber-400;
}

.workflow-card--emerald .workflow-icon {
  @apply bg-emerald-900/50 text-emerald-400;
}

.workflow-content {
  @apply flex-1 min-w-0;
}

.workflow-title {
  @apply block text-base font-medium text-white;
  font-family: 'Satoshi', sans-serif;
}

.workflow-subtitle {
  @apply block text-sm text-gray-400 truncate;
}

.workflow-arrow {
  @apply w-5 h-5 text-gray-600 flex-shrink-0 transition-colors duration-200;
}

.workflow-card:hover .workflow-arrow {
  @apply text-gray-400;
}

/* Recent Section - Dark Theme Default */
.recent-section {
  @apply mb-10;
}

.recent-list {
  @apply space-y-2;
}

.recent-item {
  @apply w-full flex items-center gap-3 px-4 py-3
         bg-gray-900 border border-gray-800 rounded-lg
         hover:border-gray-700
         cursor-pointer transition-all duration-200 text-left;
}

.recent-status {
  @apply w-2 h-2 rounded-full flex-shrink-0;
}

.recent-status--completed {
  @apply bg-emerald-500;
}

.recent-status--in-progress {
  @apply bg-amber-500;
}

.recent-name {
  @apply flex-1 text-sm text-gray-300;
}

.recent-time {
  @apply text-xs text-gray-500;
}

/* Footer - Dark Theme Default */
.home-footer {
  @apply py-6 text-center border-t border-gray-800/50;
  background: linear-gradient(180deg, transparent, rgba(20, 20, 21, 0.5));
}

.home-footer p {
  @apply text-sm text-gray-500;
}

/* ============================================
   Staggered Reveal Animation System
   ============================================ */
.stagger-item {
  opacity: 0;
  transform: translateY(20px);
  animation: stagger-reveal 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  animation-delay: calc(var(--stagger-delay, 0) * 0.1s);
}

@keyframes stagger-reveal {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Trinity cards have their own stagger within the section */
.trinity-card {
  opacity: 0;
  transform: translateY(15px);
  animation: card-reveal 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
  animation-delay: calc(0.3s + var(--card-delay, 0) * 0.1s);
}

@keyframes card-reveal {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ============================================
   Hover Surprise Effects
   ============================================ */

/* CTA Primary - Enhanced Glow Effect */
.cta-primary {
  position: relative;
  overflow: hidden;
}

.cta-primary::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  opacity: 0;
  transition: opacity 0.3s ease;
}

.cta-primary::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3) 0%, transparent 70%);
  transform: translate(-50%, -50%) scale(0);
  transition: transform 0.4s ease;
}

.cta-primary:hover::before {
  opacity: 1;
}

.cta-primary:hover::after {
  transform: translate(-50%, -50%) scale(1);
}

.cta-primary:hover {
  transform: translateY(-3px);
  box-shadow: 
    0 8px 25px rgba(255, 255, 255, 0.25),
    0 0 40px rgba(139, 92, 246, 0.2);
}

.cta-primary:active {
  transform: translateY(-1px);
}

/* CTA Secondary - Enhanced Border Glow */
.cta-secondary {
  position: relative;
  z-index: 1;
}

.cta-secondary::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 13px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
  opacity: 0;
  z-index: -1;
  transition: opacity 0.3s ease;
}

.cta-secondary::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #06b6d4);
  opacity: 0;
  z-index: -2;
  filter: blur(12px);
  transition: opacity 0.3s ease;
}

.cta-secondary:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: transparent;
  color: #ffffff;
  transform: translateY(-3px);
}

.cta-secondary:hover::before {
  opacity: 1;
}

.cta-secondary:hover::after {
  opacity: 0.5;
}

.cta-secondary:active {
  transform: translateY(-1px);
}

/* Trinity Card - Enhanced Lift, Glow and Spotlight Effect */
.trinity-card {
  --mouse-x: 50%;
  --mouse-y: 50%;
  position: relative;
}

.trinity-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: radial-gradient(
    circle at var(--mouse-x) var(--mouse-y),
    rgba(99, 102, 241, 0.15) 0%,
    transparent 60%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.trinity-card:hover::before {
  opacity: 1;
}

.trinity-card:hover {
  transform: translateY(-8px) !important;
  box-shadow: 
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 1px rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15) !important;
}

.trinity-card:hover .trinity-icon {
  transform: scale(1.15);
}

.trinity-card:hover .trinity-icon--manus {
  box-shadow: 
    0 0 24px rgba(99, 102, 241, 0.5),
    inset 0 0 12px rgba(99, 102, 241, 0.2);
}

.trinity-card:hover .trinity-icon--coworker {
  box-shadow: 
    0 0 24px rgba(16, 185, 129, 0.5),
    inset 0 0 12px rgba(16, 185, 129, 0.2);
}

.trinity-card:hover .trinity-icon--vibe {
  box-shadow: 
    0 0 24px rgba(6, 182, 212, 0.5),
    inset 0 0 12px rgba(6, 182, 212, 0.2);
}

/* Featured Card - Shimmer effect */
.featured-card {
  position: relative;
  overflow: hidden;
}

.featured-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.1),
    transparent
  );
  transition: left 0.5s ease;
}

.featured-card:hover::before {
  left: 100%;
}

.featured-card:hover {
  transform: translateY(-4px);
}

.featured-card:hover .featured-icon {
  transform: scale(1.1) rotate(5deg);
}

.featured-card:hover .featured-action {
  transform: translateX(4px);
}

/* Suggestion Items - Slide and highlight */
.suggestion-item {
  position: relative;
  overflow: hidden;
}

.suggestion-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  transform: scaleY(0);
  transition: transform 0.2s ease;
}

.suggestion-item:hover::before {
  transform: scaleY(1);
}

.suggestion-item:hover {
  transform: translateX(8px);
  background: rgba(99, 102, 241, 0.1) !important;
  border-color: rgba(99, 102, 241, 0.3) !important;
}

/* Workflow Card - Icon bounce */
.workflow-card:hover .workflow-icon {
  animation: icon-bounce 0.4s ease;
}

@keyframes icon-bounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

.workflow-card:hover {
  transform: translateX(4px);
}

/* Quick Action Button - Pop effect */
.quick-action-btn:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.quick-action-btn:active {
  transform: translateY(0) scale(0.98);
}

/* Session Sidebar - Dark Theme Default */
.session-sidebar {
  @apply fixed left-0 top-16 bottom-0 w-80 bg-gray-900 border-r border-gray-800
         overflow-y-auto z-20 transition-transform duration-300;
}

/* Vibe Background */
.bg-vibe {
  @apply absolute inset-0 -z-10 overflow-hidden;
}

.bg-gradient {
  @apply absolute inset-0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.12), transparent),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(139, 92, 246, 0.08), transparent),
    radial-gradient(ellipse 50% 30% at 20% 80%, rgba(6, 182, 212, 0.06), transparent);
}

.bg-pattern {
  @apply absolute inset-0 opacity-[0.02];
  background-image:
    radial-gradient(circle at center, #fff 1px, transparent 1px);
  background-size: 32px 32px;
}

/* Main */
.home-main {
  @apply flex-1 max-w-3xl w-full mx-auto px-6 py-12;
}

/* 动态色球 - 差异化动画 */
.orb-container {
  @apply absolute inset-0 pointer-events-none;
}

.orb {
  @apply absolute w-24 h-24 rounded-full opacity-30;
  filter: blur(40px);
  transition: all 0.8s ease-in-out;
}

/* Manus: 执行大脑 - 脉冲式呼吸，模拟"思考" */
.orb-manus {
  @apply bg-indigo-500;
  top: 15%;
  left: 20%;
}

.orb-manus.orb-active {
  @apply opacity-70;
  animation: orb-manus-think 2s ease-in-out infinite;
}

@keyframes orb-manus-think {
  0%, 100% {
    opacity: 0.7;
    transform: scale(1.2);
    filter: blur(40px) brightness(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.4);
    filter: blur(50px) brightness(1.2);
  }
}

/* Coworker: 执行双手 - 轻微旋转+缩放，模拟"操作" */
.orb-coworker {
  @apply bg-emerald-500;
  top: 25%;
  left: 50%;
  transform: translateX(-50%);
}

.orb-coworker.orb-active {
  @apply opacity-60;
  animation: orb-coworker-work 3s ease-in-out infinite;
}

@keyframes orb-coworker-work {
  0%, 100% {
    opacity: 0.6;
    transform: translateX(-50%) scale(1.2) rotate(0deg);
  }
  25% {
    opacity: 0.5;
    transform: translateX(-50%) scale(1.35) rotate(5deg);
  }
  50% {
    opacity: 0.7;
    transform: translateX(-50%) scale(1.3) rotate(0deg);
  }
  75% {
    opacity: 0.5;
    transform: translateX(-50%) scale(1.35) rotate(-5deg);
  }
}

/* Vibe: 生命气息 - 不规则漂浮，模拟"灵动" */
.orb-vibe {
  @apply bg-cyan-500;
  top: 15%;
  right: 20%;
}

.orb-vibe.orb-active {
  @apply opacity-60;
  animation: orb-vibe-float 4s ease-in-out infinite;
}

@keyframes orb-vibe-float {
  0%, 100% {
    opacity: 0.6;
    transform: translate(0, 0) scale(1.2);
  }
  25% {
    opacity: 0.5;
    transform: translate(10px, -15px) scale(1.35);
  }
  50% {
    opacity: 0.7;
    transform: translate(-5px, 5px) scale(1.25);
  }
  75% {
    opacity: 0.5;
    transform: translate(-10px, -10px) scale(1.4);
  }
}

/* 能量连线 */
.energy-lines {
  @apply absolute w-full h-24 top-1/4 left-0 opacity-30;
}

.energy-line {
  fill: none;
  stroke: url(#energy-gradient);
  stroke-width: 2;
  stroke-dasharray: 8 4;
  animation: energy-flow 3s linear infinite;
}

@keyframes energy-flow {
  from { stroke-dashoffset: 0; }
  to { stroke-dashoffset: -24; }
}

/* Drop Section */
.drop-section {
  @apply mb-8;
}

/* Hidden utility */
.hidden {
  display: none;
}
</style>
