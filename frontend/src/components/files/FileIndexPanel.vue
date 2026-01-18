<script setup lang="ts">
/**
 * FileIndexPanel - 文件索引面板
 *
 * 整合文件树、语义搜索、索引状态的完整面板
 * Coworker 的核心 UI 组件
 */
import { ref, computed, onMounted, watch } from 'vue'
import { filesApi, type DirectoryTreeNode, type IndexStats, type SearchResult } from '@/api/files'
import FileTree from './FileTree.vue'
import SemanticSearch from './SemanticSearch.vue'
import {
  FolderPlusIcon,
  ArrowPathIcon,
  ChartBarIcon,
  DocumentMagnifyingGlassIcon,
  FolderIcon,
  CloudArrowUpIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps<{
  initialPath?: string
}>()

// Emits
const emit = defineEmits<{
  (e: 'file-select', path: string): void
  (e: 'search-select', result: SearchResult): void
}>()

// State
const currentPath = ref<string>('')
const tree = ref<DirectoryTreeNode | null>(null)
const stats = ref<IndexStats | null>(null)
const selectedFilePath = ref<string>('')
const loading = ref(false)
const indexing = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'tree' | 'search'>('tree')

// Drag and drop state
const isDragging = ref(false)
const dragCounter = ref(0)

// Computed
const formattedSize = computed(() => {
  if (!stats.value) return '0 B'
  const size = stats.value.total_size
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
})

const topLanguages = computed(() => {
  if (!stats.value?.languages) return []
  return Object.entries(stats.value.languages)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
})

// Methods
const loadDirectory = async (path: string) => {
  if (!path) return
  
  loading.value = true
  error.value = null
  
  try {
    currentPath.value = path
    
    // Load tree and stats in parallel
    const [treeData, statsData] = await Promise.all([
      filesApi.getDirectoryTree(path, 4),
      filesApi.getStats(path),
    ])
    
    tree.value = treeData
    stats.value = statsData
  } catch (err: any) {
    error.value = err.response?.data?.detail || '加载目录失败'
    console.error('Load directory error:', err)
  } finally {
    loading.value = false
  }
}

const indexDirectory = async () => {
  if (!currentPath.value || indexing.value) return
  
  indexing.value = true
  error.value = null
  
  try {
    stats.value = await filesApi.indexDirectory({
      path: currentPath.value,
    })
    
    // Reload tree after indexing
    tree.value = await filesApi.getDirectoryTree(currentPath.value, 4)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '索引失败'
    console.error('Index error:', err)
  } finally {
    indexing.value = false
  }
}

const refreshIndex = async () => {
  if (!currentPath.value || indexing.value) return
  
  indexing.value = true
  
  try {
    const result = await filesApi.incrementalIndex(currentPath.value)
    console.log(`Updated ${result.updated_count} files`)
    
    // Reload stats
    stats.value = await filesApi.getStats(currentPath.value)
  } catch (err: any) {
    console.error('Refresh error:', err)
  } finally {
    indexing.value = false
  }
}

const handleFileSelect = (node: DirectoryTreeNode, fullPath: string) => {
  selectedFilePath.value = fullPath
  if (node.type === 'file') {
    // Construct actual file path
    const actualPath = currentPath.value + '/' + fullPath.split('/').slice(1).join('/')
    emit('file-select', actualPath)
  }
}

const handleSearchSelect = (result: SearchResult) => {
  selectedFilePath.value = result.file_path
  emit('search-select', result)
}

// Drag and drop handlers
const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  dragCounter.value++
  isDragging.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  dragCounter.value--
  if (dragCounter.value === 0) {
    isDragging.value = false
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
  dragCounter.value = 0
  
  // Get dropped items
  const items = e.dataTransfer?.items
  if (!items) return
  
  for (const item of items) {
    // Check if it's a directory (webkitGetAsEntry is non-standard but widely supported)
    const entry = item.webkitGetAsEntry?.()
    if (entry?.isDirectory) {
      // For now, we can't get the full path from the browser
      // Show a message to use the path input instead
      error.value = '浏览器不支持直接拖入文件夹路径，请使用下方输入框'
      return
    }
  }
}

const handlePathInput = async () => {
  const path = prompt('请输入要索引的目录路径:')
  if (path) {
    await loadDirectory(path)
    await indexDirectory()
  }
}

// Lifecycle
onMounted(() => {
  if (props.initialPath) {
    loadDirectory(props.initialPath)
  }
})

watch(() => props.initialPath, (path) => {
  if (path) loadDirectory(path)
})
</script>

<template>
  <div
    class="file-index-panel h-full flex flex-col bg-white dark:bg-gray-900 rounded-lg overflow-hidden"
    @dragenter="handleDragEnter"
    @dragleave="handleDragLeave"
    @dragover="handleDragOver"
    @drop="handleDrop"
  >
    <!-- Header -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <FolderIcon class="w-5 h-5 text-amber-500" />
          <h3 class="text-sm font-medium text-gray-900 dark:text-white">
            文件索引
          </h3>
        </div>
        
        <div class="flex items-center gap-1">
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            title="选择目录"
            @click="handlePathInput"
          >
            <FolderPlusIcon class="w-4 h-4" />
          </button>
          <button
            class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
            :class="{ 'animate-spin': indexing }"
            title="刷新索引"
            :disabled="indexing || !currentPath"
            @click="refreshIndex"
          >
            <ArrowPathIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <!-- Current path -->
      <div
        v-if="currentPath"
        class="mt-2 text-xs text-gray-500 truncate"
      >
        {{ currentPath }}
      </div>
    </div>
    
    <!-- Stats bar -->
    <div
      v-if="stats"
      class="flex-shrink-0 px-4 py-2 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800"
    >
      <div class="flex items-center gap-4 text-xs">
        <div class="flex items-center gap-1">
          <DocumentMagnifyingGlassIcon class="w-4 h-4 text-gray-400" />
          <span class="text-gray-600 dark:text-gray-400">
            {{ stats.indexed_files }} 文件
          </span>
        </div>
        <div class="flex items-center gap-1">
          <ChartBarIcon class="w-4 h-4 text-gray-400" />
          <span class="text-gray-600 dark:text-gray-400">
            {{ formattedSize }}
          </span>
        </div>
        <!-- Top languages -->
        <div class="flex items-center gap-1 ml-auto">
          <span
            v-for="[lang, count] in topLanguages"
            :key="lang"
            class="px-1.5 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
          >
            {{ lang }}: {{ count }}
          </span>
        </div>
      </div>
    </div>
    
    <!-- Tabs -->
    <div class="flex-shrink-0 flex border-b border-gray-100 dark:border-gray-800">
      <button
        class="flex-1 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'tree'
          ? 'text-blue-600 border-b-2 border-blue-600'
          : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'tree'"
      >
        文件树
      </button>
      <button
        class="flex-1 px-4 py-2 text-sm font-medium transition-colors"
        :class="activeTab === 'search'
          ? 'text-blue-600 border-b-2 border-blue-600'
          : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'search'"
      >
        语义搜索
      </button>
    </div>
    
    <!-- Content -->
    <div class="flex-1 overflow-hidden">
      <!-- Loading -->
      <div
        v-if="loading"
        class="flex items-center justify-center h-full"
      >
        <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
      
      <!-- Error -->
      <div
        v-else-if="error"
        class="flex flex-col items-center justify-center h-full gap-2 p-4"
      >
        <ExclamationCircleIcon class="w-8 h-8 text-red-400" />
        <p class="text-sm text-red-500 text-center">
          {{ error }}
        </p>
        <button
          class="text-sm text-blue-500 hover:underline"
          @click="error = null"
        >
          关闭
        </button>
      </div>
      
      <!-- Empty state / Drop zone -->
      <div
        v-else-if="!currentPath"
        class="flex flex-col items-center justify-center h-full gap-4 p-6"
        :class="{ 'bg-blue-50 dark:bg-blue-900/20': isDragging }"
      >
        <div
          class="w-16 h-16 rounded-full flex items-center justify-center transition-all"
          :class="isDragging
            ? 'bg-blue-100 dark:bg-blue-800 scale-110'
            : 'bg-gray-100 dark:bg-gray-800'"
        >
          <CloudArrowUpIcon
            class="w-8 h-8"
            :class="isDragging ? 'text-blue-500' : 'text-gray-400'"
          />
        </div>
        <div class="text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            {{ isDragging ? '松开鼠标' : '拖入文件夹或' }}
          </p>
          <button
            class="text-sm text-blue-500 hover:underline mt-1"
            @click="handlePathInput"
          >
            选择目录
          </button>
        </div>
      </div>
      
      <!-- Tree view -->
      <div
        v-else-if="activeTab === 'tree'"
        class="h-full overflow-y-auto p-2"
      >
        <FileTree
          :tree="tree"
          :selected-path="selectedFilePath"
          @select="handleFileSelect"
        />
      </div>
      
      <!-- Search view -->
      <div
        v-else
        class="h-full p-4"
      >
        <SemanticSearch
          placeholder="搜索代码..."
          auto-focus
          @select="handleSearchSelect"
        />
      </div>
    </div>
    
    <!-- Indexing indicator -->
    <div
      v-if="indexing"
      class="flex-shrink-0 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 border-t border-blue-100 dark:border-blue-800"
    >
      <div class="flex items-center gap-2 text-sm text-blue-600 dark:text-blue-400">
        <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span>正在索引...</span>
      </div>
    </div>
    
    <!-- Drag overlay -->
    <div
      v-if="isDragging"
      class="absolute inset-0 bg-blue-500/10 border-2 border-dashed border-blue-500 rounded-lg pointer-events-none z-50"
    />
  </div>
</template>

<style scoped>
.file-index-panel {
  position: relative;
}
</style>
