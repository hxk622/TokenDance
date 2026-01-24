<script setup lang="ts">
/**
 * ProjectSidebar - Project-First architecture sidebar
 *
 * Displays:
 * - Project list with type icons
 * - Quick create button
 * - Project context summary
 */
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import type { Project, ProjectType } from '@/types/project'
import {
  Plus,
  Home,
  Search,
  FileText,
  Presentation,
  Code2,
  BarChart3,
  Zap,
  FolderOpen,
  ChevronRight,
  MoreHorizontal,
  FileStack,
  MessageSquare,
} from 'lucide-vue-next'

const router = useRouter()
const projectStore = useProjectStore()

// Computed
const projects = computed(() => projectStore.activeProjects)
const currentProject = computed(() => projectStore.currentProject)
const isLoading = computed(() => projectStore.isLoading)

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

// Project type labels
const projectTypeLabels: Record<ProjectType, string> = {
  research: '研究',
  document: '文档',
  slides: '幻灯片',
  code: '代码',
  data_analysis: '数据分析',
  quick_task: '快速任务',
}

function getProjectTypeLabel(type: ProjectType) {
  return projectTypeLabels[type] || type
}

// Format time
function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// Actions
async function handleSelectProject(project: Project) {
  await projectStore.setCurrentProject(project)
  // Navigate to project page
  router.push(`/project/${project.id}`)
}

function handleNewProject() {
  // Open new project dialog or navigate to create page
  router.push('/')
}

function handleHomeClick() {
  router.push('/')
}

// Load projects on mount
onMounted(async () => {
  if (projectStore.currentWorkspaceId) {
    await projectStore.loadProjects(projectStore.currentWorkspaceId)
  }
})
</script>

<template>
  <aside class="project-sidebar">
    <!-- Header -->
    <div class="sidebar-header">
      <button
        class="header-btn logo-btn"
        title="首页"
        @click="handleHomeClick"
      >
        <Home class="icon" />
      </button>
      <button
        class="header-btn new-btn"
        title="新建项目"
        @click="handleNewProject"
      >
        <Plus class="icon" />
      </button>
    </div>

    <!-- Project List -->
    <div class="project-list">
      <div
        v-if="isLoading"
        class="loading-state"
      >
        <div class="loading-spinner" />
      </div>

      <template v-else-if="projects.length > 0">
        <button
          v-for="project in projects"
          :key="project.id"
          class="project-item"
          :class="{ active: currentProject?.id === project.id }"
          @click="handleSelectProject(project)"
        >
          <div class="project-icon">
            <component
              :is="getProjectIcon(project.project_type)"
              class="icon"
            />
          </div>
          <div class="project-info">
            <div class="project-title">
              {{ project.title }}
            </div>
            <div class="project-meta">
              <span class="project-type">{{
                getProjectTypeLabel(project.project_type)
              }}</span>
              <span class="project-stats">
                <span
                  v-if="project.artifact_count > 0"
                  class="stat-item"
                  title="Artifacts"
                >
                  <FileStack class="stat-icon" />
                  {{ project.artifact_count }}
                </span>
                <span
                  v-if="project.conversation_count > 0"
                  class="stat-item"
                  title="Conversations"
                >
                  <MessageSquare class="stat-icon" />
                  {{ project.conversation_count }}
                </span>
              </span>
              <span class="project-time">{{
                formatTime(project.updated_at)
              }}</span>
            </div>
          </div>
          <ChevronRight class="chevron" />
        </button>
      </template>

      <div
        v-else
        class="empty-state"
      >
        <FolderOpen class="empty-icon" />
        <p>暂无项目</p>
        <button
          class="create-btn"
          @click="handleNewProject"
        >
          <Plus class="icon" />
          新建项目
        </button>
      </div>
    </div>

    <!-- Footer -->
    <div class="sidebar-footer">
      <button
        class="footer-btn"
        title="更多"
      >
        <MoreHorizontal class="icon" />
      </button>
    </div>
  </aside>
</template>

<style scoped>
.project-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 280px;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary);
  border-right: 1px solid var(--any-border);
  z-index: 100;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--any-radius-md);
  border: none;
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.header-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.header-btn .icon {
  width: 20px;
  height: 20px;
}

.new-btn {
  background: var(--exec-accent);
  color: var(--any-bg-primary);
}

.new-btn:hover {
  background: var(--exec-accent);
  opacity: 0.9;
}

/* Project List */
.project-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.project-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border-radius: var(--any-radius-md);
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.project-item:hover {
  background: var(--any-bg-tertiary);
}

.project-item.active {
  background: var(--any-bg-tertiary);
  border-left: 2px solid var(--exec-accent);
}

.project-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--any-radius-md);
  background: var(--any-bg-primary);
  color: var(--any-text-secondary);
  flex-shrink: 0;
}

.project-icon .icon {
  width: 18px;
  height: 18px;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
  font-size: 12px;
  color: var(--any-text-tertiary);
}

.project-type {
  padding: 1px 6px;
  border-radius: var(--any-radius-sm);
  background: var(--any-bg-primary);
}

.project-stats {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 2px;
  color: var(--any-text-muted);
}

.stat-icon {
  width: 12px;
  height: 12px;
}

.chevron {
  width: 16px;
  height: 16px;
  color: var(--any-text-tertiary);
  opacity: 0;
  transition: opacity var(--any-duration-fast) var(--any-ease-default);
}

.project-item:hover .chevron {
  opacity: 1;
}

/* Loading State */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--any-border);
  border-top-color: var(--exec-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--any-text-tertiary);
  margin-bottom: 16px;
}

.empty-state p {
  color: var(--any-text-secondary);
  margin-bottom: 16px;
}

.create-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--any-radius-md);
  border: 1px solid var(--any-border);
  background: transparent;
  color: var(--any-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.create-btn:hover {
  background: var(--any-bg-tertiary);
  border-color: var(--exec-accent);
}

.create-btn .icon {
  width: 16px;
  height: 16px;
}

/* Footer */
.sidebar-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border-top: 1px solid var(--any-border);
}

.footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--any-radius-md);
  border: none;
  background: transparent;
  color: var(--any-text-tertiary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.footer-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-secondary);
}

.footer-btn .icon {
  width: 20px;
  height: 20px;
}

/* Responsive - hide on small screens */
@media (max-width: 768px) {
  .project-sidebar {
    width: 56px;
  }

  .sidebar-header {
    flex-direction: column;
    gap: 8px;
  }

  .project-info,
  .project-meta,
  .chevron {
    display: none;
  }

  .project-item {
    justify-content: center;
    padding: 8px;
  }

  .empty-state p,
  .create-btn span {
    display: none;
  }
}
</style>
