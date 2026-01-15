<script setup lang="ts">
/**
 * SemanticSearch Component - 语义搜索组件
 *
 * 提供代码语义搜索功能，支持自然语言查询
 */
import { ref, computed, watch } from 'vue'
import { filesApi, type SearchResult } from '@/api/files'
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  ArrowTopRightOnSquareIcon,
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps<{
  placeholder?: string
  autoFocus?: boolean
}>()

// Emits
const emit = defineEmits<{
  (e: 'select', result: SearchResult): void
  (e: 'search', query: string): void
}>()

// State
const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showResults = ref(false)
const selectedIndex = ref(-1)

// Debounce search
let searchTimeout: number | null = null

const doSearch = async () => {
  if (!query.value.trim()) {
    results.value = []
    showResults.value = false
    return
  }
  
  loading.value = true
  error.value = null
  
  try {
    const searchResults = await filesApi.search({
      query: query.value,
      top_k: 10,
    })
    results.value = searchResults
    showResults.value = true
    emit('search', query.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '搜索失败'
    console.error('Search error:', err)
  } finally {
    loading.value = false
  }
}

// Watch query changes with debounce
watch(query, (newQuery) => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  
  if (!newQuery.trim()) {
    results.value = []
    showResults.value = false
    return
  }
  
  searchTimeout = window.setTimeout(doSearch, 300)
})

// Methods
const handleSelect = (result: SearchResult) => {
  emit('select', result)
  showResults.value = false
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (!showResults.value || results.value.length === 0) return
  
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
      if (selectedIndex.value >= 0) {
        handleSelect(results.value[selectedIndex.value])
      }
      break
    case 'Escape':
      showResults.value = false
      break
  }
}

const clearSearch = () => {
  query.value = ''
  results.value = []
  showResults.value = false
  selectedIndex.value = -1
}

const formatScore = (score: number) => {
  return (score * 100).toFixed(0) + '%'
}

const getFileIcon = (language: string | null) => {
  // 根据语言返回不同图标颜色
  const colors: Record<string, string> = {
    python: 'text-yellow-500',
    javascript: 'text-yellow-400',
    typescript: 'text-blue-500',
    go: 'text-cyan-500',
    rust: 'text-orange-600',
  }
  return colors[language || ''] || 'text-gray-400'
}

const highlightMatch = (content: string, maxLength: number = 200) => {
  // 截取并高亮
  const trimmed = content.length > maxLength
    ? content.substring(0, maxLength) + '...'
    : content
  return trimmed
}

// Reset selected index when results change
watch(results, () => {
  selectedIndex.value = -1
})
</script>

<template>
  <div class="semantic-search relative">
    <!-- Search Input -->
    <div class="search-input-wrapper relative">
      <MagnifyingGlassIcon
        class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
      />
      <input
        v-model="query"
        type="text"
        :placeholder="placeholder || '搜索代码... (支持自然语言)'"
        class="w-full pl-10 pr-10 py-2.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-shadow"
        :autofocus="autoFocus"
        @keydown="handleKeyDown"
        @focus="showResults = results.length > 0"
      />
      
      <!-- Loading indicator -->
      <div
        v-if="loading"
        class="absolute right-3 top-1/2 -translate-y-1/2"
      >
        <div class="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
      
      <!-- Clear button -->
      <button
        v-else-if="query"
        class="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 text-gray-400 hover:text-gray-600 transition-colors"
        @click="clearSearch"
      >
        <XMarkIcon class="w-4 h-4" />
      </button>
    </div>
    
    <!-- Results Dropdown -->
    <div
      v-if="showResults && (results.length > 0 || error)"
      class="search-results absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto z-50"
    >
      <!-- Error -->
      <div v-if="error" class="p-4 text-red-500 text-sm text-center">
        {{ error }}
      </div>
      
      <!-- Results list -->
      <div v-else>
        <div
          v-for="(result, index) in results"
          :key="`${result.file_path}:${result.start_line}`"
          class="search-result-item p-3 border-b border-gray-100 dark:border-gray-700 last:border-b-0 cursor-pointer transition-colors"
          :class="{
            'bg-blue-50 dark:bg-blue-900/30': index === selectedIndex,
            'hover:bg-gray-50 dark:hover:bg-gray-700/50': index !== selectedIndex,
          }"
          @click="handleSelect(result)"
          @mouseenter="selectedIndex = index"
        >
          <!-- File info -->
          <div class="flex items-center gap-2 mb-1">
            <CodeBracketIcon
              class="w-4 h-4 flex-shrink-0"
              :class="getFileIcon(result.language)"
            />
            <span class="text-sm font-medium text-gray-700 dark:text-gray-300 truncate">
              {{ result.file_path.split('/').pop() }}
            </span>
            <span class="text-xs text-gray-400">
              L{{ result.start_line }}-{{ result.end_line }}
            </span>
            <span class="ml-auto text-xs font-medium px-1.5 py-0.5 rounded bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
              {{ formatScore(result.score) }}
            </span>
          </div>
          
          <!-- Content preview -->
          <div class="text-xs text-gray-500 dark:text-gray-400 font-mono whitespace-pre-wrap line-clamp-3">
            {{ highlightMatch(result.content) }}
          </div>
          
          <!-- Full path -->
          <div class="flex items-center gap-1 mt-1.5 text-xs text-gray-400">
            <span class="truncate">{{ result.file_path }}</span>
            <ArrowTopRightOnSquareIcon class="w-3 h-3 flex-shrink-0" />
          </div>
        </div>
      </div>
      
      <!-- No results -->
      <div
        v-if="results.length === 0 && !error && !loading"
        class="p-4 text-gray-400 text-sm text-center"
      >
        未找到匹配结果
      </div>
    </div>
    
    <!-- Backdrop -->
    <div
      v-if="showResults"
      class="fixed inset-0 z-40"
      @click="showResults = false"
    />
  </div>
</template>

<style scoped>
.search-results {
  backdrop-filter: blur(8px);
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
