<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { sessionService } from '@/api/services'
import { Clock, Search, Filter, ChevronRight } from 'lucide-vue-next'
import AnyButton from '@/components/common/AnyButton.vue'

const router = useRouter()

// 任务历史数据
const tasks = ref<any[]>([])
const isLoading = ref(true)
const searchQuery = ref('')
const filterStatus = ref<'all' | 'completed' | 'running' | 'error'>('all')

// 加载任务历史
async function loadTaskHistory() {
  isLoading.value = true
  try {
    // TODO: 需要从某处获取 workspace_id
    // 暂时使用空字符串，实际应该从用户状态或路由参数获取
    const response = await sessionService.listSessions({
      workspace_id: '', // TODO: 从用户状态获取实际的 workspace_id
      limit: 100
    })
    tasks.value = response.sessions || []
  } catch (error) {
    console.error('Failed to load task history:', error)
    tasks.value = []
  } finally {
    isLoading.value = false
  }
}

// 过滤后的任务列表
const filteredTasks = computed(() => {
  let result = tasks.value

  // 按状态过滤
  if (filterStatus.value !== 'all') {
    result = result.filter(task => task.status === filterStatus.value)
  }

  // 按搜索关键词过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(task =>
      task.title?.toLowerCase().includes(query) ||
      task.description?.toLowerCase().includes(query)
    )
  }

  return result
})

// 跳转到任务详情
function viewTask(taskId: string) {
  router.push(`/execution/${taskId}`)
}

// 格式化时间
function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 获取状态显示文本
function getStatusText(status: string) {
  const statusMap: Record<string, string> = {
    completed: '已完成',
    running: '执行中',
    error: '失败',
    pending: '等待中'
  }
  return statusMap[status] || status
}

// 获取状态颜色类
function getStatusClass(status: string) {
  return `status-${status}`
}

onMounted(() => {
  loadTaskHistory()
})
</script>

<template>
  <div class="task-history-page">
    <!-- Header -->
    <header class="history-header">
      <div class="header-left">
        <Clock class="header-icon" />
        <h1 class="header-title">
          任务历史
        </h1>
      </div>
      <AnyButton
        variant="primary"
        @click="router.push('/')"
      >
        <span>新建任务</span>
      </AnyButton>
    </header>

    <!-- Filters -->
    <div class="filters-bar">
      <!-- Search -->
      <div class="search-box">
        <Search class="search-icon" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索任务..."
          class="search-input"
        >
      </div>

      <!-- Status Filter -->
      <div class="filter-group">
        <Filter class="filter-icon" />
        <select
          v-model="filterStatus"
          class="filter-select"
        >
          <option value="all">
            全部状态
          </option>
          <option value="completed">
            已完成
          </option>
          <option value="running">
            执行中
          </option>
          <option value="error">
            失败
          </option>
        </select>
      </div>
    </div>

    <!-- Task List -->
    <div class="task-list">
      <!-- Loading State -->
      <div
        v-if="isLoading"
        class="loading-state"
      >
        <div class="spinner" />
        <p>加载任务历史...</p>
      </div>

      <!-- Empty State -->
      <div
        v-else-if="filteredTasks.length === 0"
        class="empty-state"
      >
        <Clock class="empty-icon" />
        <h3>暂无任务历史</h3>
        <p>{{ searchQuery ? '没有找到匹配的任务' : '开始创建你的第一个任务吧' }}</p>
        <AnyButton
          v-if="!searchQuery"
          variant="primary"
          @click="router.push('/')"
        >
          <span>创建任务</span>
        </AnyButton>
      </div>

      <!-- Task Cards -->
      <div
        v-else
        class="task-cards"
      >
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="task-card"
          @click="viewTask(task.id)"
        >
          <div class="task-card-header">
            <h3 class="task-title">
              {{ task.title || '未命名任务' }}
            </h3>
            <span
              class="task-status"
              :class="getStatusClass(task.status)"
            >
              {{ getStatusText(task.status) }}
            </span>
          </div>

          <p
            v-if="task.description"
            class="task-description"
          >
            {{ task.description }}
          </p>

          <div class="task-card-footer">
            <span class="task-time">{{ formatTime(task.created_at) }}</span>
            <ChevronRight class="task-arrow" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-history-page {
  width: 100%;
  min-height: 100vh;
  background: var(--any-bg-primary);
  display: flex;
  flex-direction: column;
}

/* Header */
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 32px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 28px;
  height: 28px;
  color: var(--any-text-primary);
}

.header-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: var(--any-text-primary);
}

/* Filters Bar */
.filters-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 32px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.search-box {
  flex: 1;
  max-width: 400px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  width: 18px;
  height: 18px;
  color: var(--any-text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 12px 10px 40px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-primary);
  font-size: 14px;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.search-input:focus {
  outline: none;
  border-color: var(--td-state-thinking);
  background: var(--any-bg-primary);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-icon {
  width: 18px;
  height: 18px;
  color: var(--any-text-secondary);
}

.filter-select {
  padding: 8px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.filter-select:hover {
  border-color: var(--any-border-hover);
}

.filter-select:focus {
  outline: none;
  border-color: var(--td-state-thinking);
}

/* Task List */
.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--any-border);
  border-top-color: var(--td-state-thinking);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-state p,
.empty-state p {
  color: var(--any-text-secondary);
  margin: 8px 0 16px 0;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--any-text-muted);
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0 0 8px 0;
}

/* Task Cards */
.task-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.task-card {
  padding: 20px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.task-card:hover {
  border-color: var(--td-state-thinking);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.task-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.task-title {
  flex: 1;
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-status {
  padding: 4px 10px;
  border-radius: var(--any-radius-full);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.task-status.status-completed {
  background: rgba(0, 255, 136, 0.2);
  color: var(--td-state-executing);
}

.task-status.status-running {
  background: rgba(0, 217, 255, 0.2);
  color: var(--td-state-thinking);
}

.task-status.status-error {
  background: rgba(255, 59, 48, 0.2);
  color: var(--td-state-error);
}

.task-status.status-pending {
  background: rgba(255, 184, 0, 0.2);
  color: var(--td-state-waiting);
}

.task-description {
  font-size: 14px;
  color: var(--any-text-secondary);
  margin: 0 0 16px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.task-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.task-time {
  font-size: 13px;
  color: var(--any-text-muted);
}

.task-arrow {
  width: 18px;
  height: 18px;
  color: var(--any-text-muted);
  transition: transform var(--any-duration-fast) var(--any-ease-out);
}

.task-card:hover .task-arrow {
  transform: translateX(4px);
  color: var(--td-state-thinking);
}

/* Responsive */
@media (max-width: 768px) {
  .history-header,
  .filters-bar,
  .task-list {
    padding-left: 16px;
    padding-right: 16px;
  }

  .task-cards {
    grid-template-columns: 1fr;
  }

  .filters-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-box {
    max-width: none;
  }
}
</style>
