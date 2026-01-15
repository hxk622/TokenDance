<script setup lang="ts">
/**
 * FilesView - 文件索引视图
 *
 * Coworker 的核心页面，提供本地文件索引和语义搜索功能
 */
import { ref } from 'vue'
import { FileIndexPanel } from '@/components/files'
import type { SearchResult } from '@/api/files'
import { ArrowLeftIcon } from '@heroicons/vue/24/outline'
import { useRouter } from 'vue-router'

const router = useRouter()

// State
const selectedFilePath = ref<string>('')
const fileContent = ref<string>('')
const showPreview = ref(false)

// Methods
const handleFileSelect = async (path: string) => {
  selectedFilePath.value = path
  showPreview.value = true
  
  // In a real app, you would load file content here
  // For now, just show the path
  fileContent.value = `Selected: ${path}`
}

const handleSearchSelect = (result: SearchResult) => {
  selectedFilePath.value = result.file_path
  showPreview.value = true
  fileContent.value = result.content
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="files-view min-h-screen bg-gray-50 dark:bg-gray-950">
    <!-- Header -->
    <header class="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <div class="flex items-center gap-4">
            <button
              class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
              @click="goBack"
            >
              <ArrowLeftIcon class="w-5 h-5" />
            </button>
            <h1 class="text-lg font-semibold text-gray-900 dark:text-white">
              Coworker 文件索引
            </h1>
          </div>
          
          <div class="text-sm text-gray-500">
            本地文件深度理解
          </div>
        </div>
      </div>
    </header>
    
    <!-- Main content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex gap-6 h-[calc(100vh-8rem)]">
        <!-- File Index Panel -->
        <div class="w-80 flex-shrink-0">
          <FileIndexPanel
            @file-select="handleFileSelect"
            @search-select="handleSearchSelect"
          />
        </div>
        
        <!-- Preview Panel -->
        <div class="flex-1 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 overflow-hidden">
          <div v-if="showPreview" class="h-full flex flex-col">
            <!-- Preview header -->
            <div class="flex-shrink-0 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
              <p class="text-sm text-gray-600 dark:text-gray-400 truncate">
                {{ selectedFilePath }}
              </p>
            </div>
            
            <!-- Preview content -->
            <div class="flex-1 overflow-auto p-4">
              <pre class="text-sm text-gray-700 dark:text-gray-300 font-mono whitespace-pre-wrap">{{ fileContent }}</pre>
            </div>
          </div>
          
          <!-- Empty state -->
          <div v-else class="h-full flex items-center justify-center">
            <div class="text-center">
              <p class="text-gray-400 text-sm">
                选择文件或搜索结果查看内容
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.files-view {
  @apply antialiased;
}
</style>
