<script setup lang="ts">
/**
 * GlobalSearch - 全局搜索命令面板
 * 
 * 功能:
 * - Command+K / Ctrl+K 触发
 * - 搜索任务、项目、文件
 * - 快捷操作入口
 */
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Search, FileText, FolderOpen, History, Settings,
  Sparkles, HelpCircle, MessageSquare, X, ArrowRight,
  Command, CornerDownLeft
} from 'lucide-vue-next'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()

// State
const searchQuery = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

// Search result types
interface SearchResult {
  id: string
  type: 'task' | 'project' | 'file' | 'action'
  title: string
  description?: string
  icon: any
  action?: () => void
  link?: string
  shortcut?: string
}

// Quick actions (always shown when query is empty)
const quickActions = computed<SearchResult[]>(() => [
  {
    id: 'new-task',
    type: 'action',
    title: '新建任务',
    description: '开始一个新的 AI 任务',
    icon: Sparkles,
    link: '/'
  },
  {
    id: 'history',
    type: 'action',
    title: '任务历史',
    description: '查看所有历史任务',
    icon: History,
    link: '/history'
  },
  {
    id: 'files',
    type: 'action',
    title: '文件管理',
    description: '管理上传的文件',
    icon: FolderOpen,
    link: '/files'
  },
  {
    id: 'settings',
    type: 'action',
    title: '设置',
    description: '账号和偏好设置',
    icon: Settings,
    link: '/settings',
    shortcut: '⌘,'
  },
  {
    id: 'help',
    type: 'action',
    title: '帮助中心',
    description: '查看使用文档',
    icon: HelpCircle,
    action: () => window.open('https://docs.tokendance.ai', '_blank')
  },
  {
    id: 'feedback',
    type: 'action',
    title: '反馈建议',
    description: '告诉我们您的想法',
    icon: MessageSquare,
    action: () => window.open('https://feedback.tokendance.ai', '_blank')
  }
])

// Mock search results (would be replaced with real API)
const mockSearchResults = computed<SearchResult[]>(() => {
  if (!searchQuery.value.trim()) return []
  
  const query = searchQuery.value.toLowerCase()
  
  // Mock tasks
  const tasks: SearchResult[] = [
    { id: 't1', type: 'task', title: '2024年新能源汽车市场分析', description: '深度研究 · 已完成', icon: FileText, link: '/execution/task-001' },
    { id: 't2', type: 'task', title: 'Q4 业绩汇报 PPT', description: 'PPT 生成 · 进行中', icon: FileText, link: '/ppt/edit/ppt-001' },
    { id: 't3', type: 'task', title: '竞品分析报告', description: '深度研究 · 已完成', icon: FileText, link: '/execution/task-002' },
  ]
  
  // Mock projects
  const projects: SearchResult[] = [
    { id: 'p1', type: 'project', title: '产品需求分析', description: '项目 · 3 个任务', icon: FolderOpen, link: '/project/proj-001' },
    { id: 'p2', type: 'project', title: '市场调研', description: '项目 · 5 个任务', icon: FolderOpen, link: '/project/proj-002' },
  ]
  
  // Filter by query
  const filtered = [...tasks, ...projects].filter(item => 
    item.title.toLowerCase().includes(query) ||
    item.description?.toLowerCase().includes(query)
  )
  
  return filtered.slice(0, 6)
})

// Combined results
const results = computed<SearchResult[]>(() => {
  if (!searchQuery.value.trim()) {
    return quickActions.value
  }
  
  // Show search results + matching quick actions
  const matchingActions = quickActions.value.filter(a => 
    a.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
  
  return [...mockSearchResults.value, ...matchingActions].slice(0, 8)
})

// Reset selection when results change
watch(results, () => {
  selectedIndex.value = 0
})

// Focus input when modal opens
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    searchQuery.value = ''
    selectedIndex.value = 0
    setTimeout(() => inputRef.value?.focus(), 100)
  }
})

// Handle keyboard navigation
function handleKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault()
      selectedIndex.value = Math.min(selectedIndex.value + 1, results.value.length - 1)
      break
    case 'ArrowUp':
      e.preventDefault()
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
      break
    case 'Enter':
      e.preventDefault()
      if (results.value[selectedIndex.value]) {
        handleSelect(results.value[selectedIndex.value])
      }
      break
    case 'Escape':
      close()
      break
  }
}

// Handle selection
function handleSelect(result: SearchResult) {
  if (result.action) {
    result.action()
  } else if (result.link) {
    router.push(result.link)
  }
  close()
}

// Close modal
function close() {
  emit('update:modelValue', false)
}

// Global keyboard shortcut
function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    emit('update:modelValue', !props.modelValue)
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
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="search-overlay"
        @click.self="close"
      >
        <div
          class="search-modal"
          @keydown="handleKeydown"
        >
          <!-- Search input -->
          <div class="search-input-wrapper">
            <Search class="search-icon" />
            <input
              ref="inputRef"
              v-model="searchQuery"
              type="text"
              class="search-input"
              placeholder="搜索任务、项目或操作..."
              autocomplete="off"
            >
            <div class="search-shortcut">
              <kbd>ESC</kbd>
            </div>
          </div>

          <!-- Results -->
          <div class="search-results">
            <!-- Section label -->
            <div
              v-if="!searchQuery.trim()"
              class="results-label"
            >
              快捷操作
            </div>
            <div
              v-else-if="results.length > 0"
              class="results-label"
            >
              搜索结果
            </div>

            <!-- Result items -->
            <div
              v-for="(result, index) in results"
              :key="result.id"
              :class="['result-item', { selected: index === selectedIndex }]"
              @click="handleSelect(result)"
              @mouseenter="selectedIndex = index"
            >
              <div class="result-icon">
                <component
                  :is="result.icon"
                  class="w-4 h-4"
                />
              </div>
              <div class="result-content">
                <div class="result-title">
                  {{ result.title }}
                </div>
                <div
                  v-if="result.description"
                  class="result-desc"
                >
                  {{ result.description }}
                </div>
              </div>
              <div
                v-if="result.shortcut"
                class="result-shortcut"
              >
                <kbd>{{ result.shortcut }}</kbd>
              </div>
              <ArrowRight
                v-else
                class="result-arrow"
              />
            </div>

            <!-- Empty state -->
            <div
              v-if="searchQuery.trim() && results.length === 0"
              class="empty-state"
            >
              <span>没有找到 "{{ searchQuery }}" 相关结果</span>
            </div>
          </div>

          <!-- Footer -->
          <div class="search-footer">
            <div class="footer-item">
              <CornerDownLeft class="w-3 h-3" />
              <span>选择</span>
            </div>
            <div class="footer-item">
              <span class="arrow-keys">↑↓</span>
              <span>导航</span>
            </div>
            <div class="footer-item">
              <kbd>ESC</kbd>
              <span>关闭</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.search-modal {
  width: 100%;
  max-width: 560px;
  margin: 0 16px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

/* Input */
.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--any-border);
}

.search-icon {
  width: 20px;
  height: 20px;
  color: var(--any-text-muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  font-size: 16px;
  color: var(--any-text-primary);
  background: transparent;
  border: none;
  outline: none;
}

.search-input::placeholder {
  color: var(--any-text-muted);
}

.search-shortcut kbd {
  padding: 2px 6px;
  font-size: 11px;
  font-family: inherit;
  color: var(--any-text-muted);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 4px;
}

/* Results */
.search-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.results-label {
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  color: var(--any-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 100ms ease;
}

.result-item:hover,
.result-item.selected {
  background: var(--any-bg-hover);
}

.result-item.selected {
  background: var(--any-bg-tertiary);
}

.result-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  color: var(--any-text-secondary);
  flex-shrink: 0;
}

.result-item.selected .result-icon {
  background: rgba(0, 217, 255, 0.15);
  color: var(--td-state-thinking);
}

.result-content {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.result-desc {
  font-size: 12px;
  color: var(--any-text-muted);
  margin-top: 1px;
}

.result-shortcut kbd {
  padding: 2px 6px;
  font-size: 11px;
  font-family: inherit;
  color: var(--any-text-muted);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 4px;
}

.result-arrow {
  width: 14px;
  height: 14px;
  color: var(--any-text-muted);
  opacity: 0;
  transition: opacity 100ms ease;
}

.result-item.selected .result-arrow {
  opacity: 1;
}

/* Empty state */
.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: var(--any-text-muted);
  font-size: 13px;
}

/* Footer */
.search-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--any-text-muted);
}

.footer-item kbd {
  padding: 1px 4px;
  font-size: 10px;
  font-family: inherit;
  color: var(--any-text-muted);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 3px;
}

.arrow-keys {
  font-size: 10px;
  padding: 1px 4px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 3px;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 150ms ease;
}

.modal-enter-active .search-modal,
.modal-leave-active .search-modal {
  transition: transform 150ms ease, opacity 150ms ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .search-modal,
.modal-leave-to .search-modal {
  opacity: 0;
  transform: scale(0.96) translateY(-10px);
}

/* Scrollbar */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}

.search-results::-webkit-scrollbar-thumb {
  background: var(--any-border);
  border-radius: 3px;
}
</style>
