<template>
  <div
    ref="selectorRef"
    class="workspace-selector"
  >
    <!-- Trigger Button -->
    <button
      class="selector-trigger"
      :class="{ open: isOpen }"
      @click="toggleOpen"
    >
      <FolderIcon class="w-4 h-4 icon" />
      <span class="workspace-name">{{ currentWorkspaceName }}</span>
      <ChevronDownIcon
        class="w-4 h-4 chevron"
        :class="{ rotated: isOpen }"
      />
    </button>

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div
        v-if="isOpen"
        class="dropdown-panel"
      >
        <!-- Search -->
        <div class="search-section">
          <MagnifyingGlassIcon class="w-4 h-4 search-icon" />
          <input
            v-model="searchQuery"
            type="text"
            class="search-input"
            placeholder="搜索工作空间..."
            @keydown.esc="isOpen = false"
          >
        </div>

        <!-- Workspace List -->
        <div class="workspace-list">
          <div
            v-for="workspace in filteredWorkspaces"
            :key="workspace.id"
            class="workspace-item"
            :class="{ active: workspace.id === currentWorkspaceId }"
            @click="selectWorkspace(workspace)"
          >
            <div class="workspace-icon">
              {{ getInitial(workspace.name) }}
            </div>
            <div class="workspace-info">
              <span class="workspace-title">{{ workspace.name }}</span>
              <span class="workspace-meta">
                {{ workspace.session_count || 0 }} 个项目
              </span>
            </div>
            <CheckIcon
              v-if="workspace.id === currentWorkspaceId"
              class="w-4 h-4 check-icon"
            />
          </div>

          <!-- Empty State -->
          <div
            v-if="filteredWorkspaces.length === 0"
            class="empty-state"
          >
            <span v-if="searchQuery">未找到匹配的工作空间</span>
            <span v-else>暂无工作空间</span>
          </div>
        </div>

        <!-- Create New -->
        <div class="create-section">
          <button
            class="create-btn"
            @click="showCreateDialog = true"
          >
            <PlusIcon class="w-4 h-4" />
            <span>创建新工作空间</span>
          </button>
        </div>
      </div>
    </Transition>

    <!-- Create Dialog -->
    <Teleport to="body">
      <Transition name="modal">
        <div
          v-if="showCreateDialog"
          class="modal-overlay"
          @click="closeCreateDialog"
        >
          <div
            class="modal-content"
            @click.stop
          >
            <div class="modal-header">
              <h3>创建工作空间</h3>
              <button
                class="close-btn"
                @click="closeCreateDialog"
              >
                <XMarkIcon class="w-5 h-5" />
              </button>
            </div>
            <div class="modal-body">
              <div class="form-field">
                <label>名称</label>
                <input
                  v-model="newWorkspace.name"
                  type="text"
                  placeholder="我的工作空间"
                  class="form-input"
                  @input="autoGenerateSlug"
                >
              </div>
              <div class="form-field">
                <label>标识 (URL)</label>
                <input
                  v-model="newWorkspace.slug"
                  type="text"
                  placeholder="my-workspace"
                  class="form-input"
                >
                <span class="hint">用于 URL，只能包含小写字母、数字和连字符</span>
              </div>
              <div class="form-field">
                <label>描述 (可选)</label>
                <textarea
                  v-model="newWorkspace.description"
                  placeholder="简短描述这个工作空间的用途..."
                  class="form-textarea"
                  rows="3"
                />
              </div>
            </div>
            <div class="modal-footer">
              <button
                class="btn btn-secondary"
                @click="closeCreateDialog"
              >
                取消
              </button>
              <button
                class="btn btn-primary"
                :disabled="!isValidForm || isCreating"
                @click="handleCreate"
              >
                <span v-if="isCreating">创建中...</span>
                <span v-else>创建</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  FolderIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'
import { workspaceApi, type Workspace, type WorkspaceCreate } from '@/api/workspace'
import { useProjectStore } from '@/stores/project'

// Props & Emits
interface Emits {
  (e: 'change', workspace: Workspace): void
}
const emit = defineEmits<Emits>()

// State
const projectStore = useProjectStore()
const selectorRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const searchQuery = ref('')
const workspaces = ref<Workspace[]>([])
const isLoading = ref(false)
const showCreateDialog = ref(false)
const isCreating = ref(false)

// New workspace form
const newWorkspace = ref<WorkspaceCreate>({
  name: '',
  slug: '',
  description: '',
  workspace_type: 'PERSONAL',
})

// Computed
const currentWorkspaceId = computed(() => projectStore.currentWorkspaceId)

const currentWorkspaceName = computed(() => {
  const ws = workspaces.value.find(w => w.id === currentWorkspaceId.value)
  return ws?.name || '选择工作空间'
})

const filteredWorkspaces = computed(() => {
  if (!searchQuery.value) return workspaces.value
  const query = searchQuery.value.toLowerCase()
  return workspaces.value.filter(
    w => w.name.toLowerCase().includes(query) ||
         w.slug.toLowerCase().includes(query)
  )
})

const isValidForm = computed(() => {
  return newWorkspace.value.name.trim().length > 0 &&
         newWorkspace.value.slug.trim().length > 0 &&
         /^[a-z0-9-]+$/.test(newWorkspace.value.slug)
})

// Methods
function toggleOpen() {
  isOpen.value = !isOpen.value
}

function getInitial(name: string): string {
  return name.charAt(0).toUpperCase()
}

async function loadWorkspaces() {
  isLoading.value = true
  try {
    const result = await workspaceApi.listWorkspaces(100, 0)
    workspaces.value = result.items

    // Auto-select first workspace if none selected
    if (!currentWorkspaceId.value && result.items.length > 0) {
      selectWorkspace(result.items[0])
    }
  } catch (error) {
    console.error('Failed to load workspaces:', error)
  } finally {
    isLoading.value = false
  }
}

function selectWorkspace(workspace: Workspace) {
  projectStore.setCurrentWorkspace(workspace.id)
  emit('change', workspace)
  isOpen.value = false
}

function autoGenerateSlug() {
  // Auto-generate slug from name
  newWorkspace.value.slug = newWorkspace.value.name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

async function handleCreate() {
  if (!isValidForm.value || isCreating.value) return

  isCreating.value = true
  try {
    const workspace = await workspaceApi.createWorkspace(newWorkspace.value)
    workspaces.value.unshift(workspace)
    selectWorkspace(workspace)
    closeCreateDialog()
  } catch (error) {
    console.error('Failed to create workspace:', error)
  } finally {
    isCreating.value = false
  }
}

function closeCreateDialog() {
  showCreateDialog.value = false
  newWorkspace.value = {
    name: '',
    slug: '',
    description: '',
    workspace_type: 'PERSONAL',
  }
}

// Click outside to close
function handleClickOutside(e: MouseEvent) {
  if (selectorRef.value && !selectorRef.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadWorkspaces()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.workspace-selector {
  position: relative;
}

.selector-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
  min-width: 160px;
}

.selector-trigger:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.selector-trigger.open {
  border-color: var(--td-state-thinking);
}

.icon {
  color: var(--any-text-secondary);
}

.workspace-name {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  color: var(--any-text-muted);
  transition: transform var(--any-duration-fast) var(--any-ease-out);
}

.chevron.rotated {
  transform: rotate(180deg);
}

/* Dropdown Panel */
.dropdown-panel {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 280px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  box-shadow: var(--any-shadow-lg);
  z-index: 1000;
  overflow: hidden;
}

/* Search */
.search-section {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--any-border);
}

.search-icon {
  color: var(--any-text-muted);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--any-text-primary);
  font-size: 14px;
  outline: none;
}

.search-input::placeholder {
  color: var(--any-text-muted);
}

/* Workspace List */
.workspace-list {
  max-height: 240px;
  overflow-y: auto;
  padding: 8px;
}

.workspace-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.workspace-item:hover {
  background: var(--any-bg-hover);
}

.workspace-item.active {
  background: var(--td-state-thinking-bg);
}

.workspace-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-md);
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-secondary);
}

.workspace-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.workspace-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-meta {
  font-size: 12px;
  color: var(--any-text-muted);
}

.check-icon {
  color: var(--td-state-thinking);
  flex-shrink: 0;
}

/* Empty State */
.empty-state {
  padding: 24px;
  text-align: center;
  color: var(--any-text-muted);
  font-size: 14px;
}

/* Create Section */
.create-section {
  padding: 8px;
  border-top: 1px solid var(--any-border);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px dashed var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-secondary);
  font-size: 14px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.create-btn:hover {
  background: var(--any-bg-hover);
  border-color: var(--td-state-thinking);
  color: var(--td-state-thinking);
}

/* Dropdown Transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.modal-content {
  width: 400px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-xl);
  box-shadow: var(--any-shadow-xl);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--any-border);
}

.modal-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.close-btn {
  padding: 4px;
  background: transparent;
  border: none;
  color: var(--any-text-muted);
  cursor: pointer;
  border-radius: var(--any-radius-sm);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.close-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field label {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.form-input,
.form-textarea {
  padding: 10px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  color: var(--any-text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color var(--any-duration-fast) var(--any-ease-out);
}

.form-input:focus,
.form-textarea:focus {
  border-color: var(--td-state-thinking);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--any-text-muted);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.hint {
  font-size: 12px;
  color: var(--any-text-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid var(--any-border);
}

.btn {
  padding: 10px 20px;
  border-radius: var(--any-radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.btn-secondary {
  background: transparent;
  border: 1px solid var(--any-border);
  color: var(--any-text-secondary);
}

.btn-secondary:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.btn-primary {
  background: var(--td-state-thinking);
  border: none;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--td-state-thinking-hover, #0099cc);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: all var(--any-duration-normal) var(--any-ease-out);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95);
}

/* Scrollbar */
.workspace-list::-webkit-scrollbar {
  width: 6px;
}

.workspace-list::-webkit-scrollbar-track {
  background: transparent;
}

.workspace-list::-webkit-scrollbar-thumb {
  background: var(--any-border);
  border-radius: 3px;
}

.workspace-list::-webkit-scrollbar-thumb:hover {
  background: var(--any-border-hover);
}
</style>
