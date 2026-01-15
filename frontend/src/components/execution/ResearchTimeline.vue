<script setup lang="ts">
/**
 * Research Timeline Component - 研究时光长廊
 * 
 * 展示深度研究过程中的时间轴，包括：
 * - 搜索记录
 * - 页面阅读
 * - 截图快照
 * - 关键发现
 * - 里程碑事件
 */
import { ref, computed, onMounted, watch } from 'vue'
import { timelineApi, type TimelineEntry, type TimelineResponse } from '@/api/timeline'
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  CameraIcon,
  LightBulbIcon,
  FlagIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowDownTrayIcon,
} from '@heroicons/vue/24/outline'

// Props
const props = defineProps<{
  sessionId: string
  autoRefresh?: boolean
  refreshInterval?: number
}>()

// Emits
const emit = defineEmits<{
  (e: 'entry-click', entry: TimelineEntry): void
  (e: 'screenshot-click', index: number, entry: TimelineEntry): void
}>()

// State
const timeline = ref<TimelineResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const expandedEntries = ref<Set<number>>(new Set())
const filterType = ref<string | null>(null)
const showScreenshots = ref(true)

// Computed
const filteredEntries = computed(() => {
  if (!timeline.value) return []
  
  let entries = timeline.value.entries
  
  if (filterType.value) {
    entries = entries.filter(e => e.event_type === filterType.value)
  }
  
  return entries
})

const screenshotEntries = computed(() => {
  return filteredEntries.value
    .map((entry, index) => ({ entry, index }))
    .filter(({ entry }) => entry.event_type === 'screenshot')
})

const eventTypeStats = computed(() => {
  if (!timeline.value) return {}
  
  const stats: Record<string, number> = {}
  timeline.value.entries.forEach(entry => {
    stats[entry.event_type] = (stats[entry.event_type] || 0) + 1
  })
  return stats
})

// Methods
const fetchTimeline = async () => {
  if (!props.sessionId) return
  
  loading.value = true
  error.value = null
  
  try {
    timeline.value = await timelineApi.getTimeline(props.sessionId)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load timeline'
    console.error('Timeline fetch error:', err)
  } finally {
    loading.value = false
  }
}

const toggleEntry = (index: number) => {
  if (expandedEntries.value.has(index)) {
    expandedEntries.value.delete(index)
  } else {
    expandedEntries.value.add(index)
  }
}

const handleEntryClick = (entry: TimelineEntry) => {
  emit('entry-click', entry)
}

const handleScreenshotClick = (index: number, entry: TimelineEntry) => {
  emit('screenshot-click', index, entry)
}

const exportMarkdown = async () => {
  try {
    const markdown = await timelineApi.exportMarkdown(props.sessionId)
    
    // Download as file
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `research-timeline-${props.sessionId}.md`
    a.click()
    URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Export failed:', err)
  }
}

const getEventIcon = (type: string) => {
  switch (type) {
    case 'search': return MagnifyingGlassIcon
    case 'read': return DocumentTextIcon
    case 'screenshot': return CameraIcon
    case 'finding': return LightBulbIcon
    case 'milestone': return FlagIcon
    default: return DocumentTextIcon
  }
}

const getEventColor = (type: string) => {
  switch (type) {
    case 'search': return 'text-blue-500 bg-blue-50'
    case 'read': return 'text-green-500 bg-green-50'
    case 'screenshot': return 'text-purple-500 bg-purple-50'
    case 'finding': return 'text-amber-500 bg-amber-50'
    case 'milestone': return 'text-rose-500 bg-rose-50'
    default: return 'text-gray-500 bg-gray-50'
  }
}

const formatTime = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const formatDate = (isoString: string) => {
  const date = new Date(isoString)
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
  })
}

// Lifecycle
onMounted(() => {
  fetchTimeline()
})

// Auto refresh
let refreshTimer: number | null = null

watch(
  () => props.autoRefresh,
  (autoRefresh) => {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
    
    if (autoRefresh) {
      refreshTimer = window.setInterval(
        fetchTimeline,
        props.refreshInterval || 5000
      )
    }
  },
  { immediate: true }
)

// Cleanup
import { onUnmounted } from 'vue'
onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<template>
  <div class="research-timeline h-full flex flex-col bg-white dark:bg-gray-900 rounded-lg overflow-hidden">
    <!-- Header -->
    <div class="flex-shrink-0 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-medium text-gray-900 dark:text-white">
            研究时光长廊
          </h3>
          <p v-if="timeline" class="text-xs text-gray-500 mt-0.5">
            {{ timeline.topic }} · {{ timeline.total_entries }} 条记录
          </p>
        </div>
        
        <div class="flex items-center gap-2">
          <!-- Filter buttons -->
          <div class="flex items-center gap-1 text-xs">
            <button
              v-for="(count, type) in eventTypeStats"
              :key="type"
              @click="filterType = filterType === type ? null : (type as string)"
              :class="[
                'px-2 py-1 rounded-full transition-colors',
                filterType === type
                  ? getEventColor(type as string)
                  : 'text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
              ]"
            >
              {{ count }}
            </button>
          </div>
          
          <!-- Export button -->
          <button
            @click="exportMarkdown"
            class="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors"
            title="导出 Markdown"
          >
            <ArrowDownTrayIcon class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
    
    <!-- Timeline content -->
    <div class="flex-1 overflow-y-auto">
      <!-- Loading -->
      <div v-if="loading && !timeline" class="flex items-center justify-center h-32">
        <div class="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
      
      <!-- Error -->
      <div v-else-if="error" class="p-4 text-center text-red-500 text-sm">
        {{ error }}
      </div>
      
      <!-- Empty -->
      <div v-else-if="!timeline || filteredEntries.length === 0" class="p-4 text-center text-gray-400 text-sm">
        暂无研究记录
      </div>
      
      <!-- Timeline entries -->
      <div v-else class="p-4">
        <div class="relative">
          <!-- Vertical line -->
          <div class="absolute left-4 top-0 bottom-0 w-px bg-gray-200 dark:bg-gray-700" />
          
          <!-- Entries -->
          <div class="space-y-4">
            <div
              v-for="(entry, index) in filteredEntries"
              :key="index"
              class="relative pl-10"
            >
              <!-- Icon node -->
              <div
                :class="[
                  'absolute left-0 w-8 h-8 rounded-full flex items-center justify-center',
                  getEventColor(entry.event_type)
                ]"
              >
                <component :is="getEventIcon(entry.event_type)" class="w-4 h-4" />
              </div>
              
              <!-- Entry card -->
              <div
                class="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                @click="handleEntryClick(entry)"
              >
                <!-- Header -->
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {{ entry.title }}
                    </p>
                    <p class="text-xs text-gray-500 mt-0.5">
                      {{ formatTime(entry.timestamp) }}
                    </p>
                  </div>
                  
                  <button
                    @click.stop="toggleEntry(index)"
                    class="p-1 text-gray-400 hover:text-gray-600"
                  >
                    <ChevronDownIcon
                      v-if="!expandedEntries.has(index)"
                      class="w-4 h-4"
                    />
                    <ChevronUpIcon v-else class="w-4 h-4" />
                  </button>
                </div>
                
                <!-- Expanded content -->
                <div
                  v-if="expandedEntries.has(index)"
                  class="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600"
                >
                  <p class="text-sm text-gray-600 dark:text-gray-300">
                    {{ entry.description }}
                  </p>
                  
                  <!-- URL link -->
                  <a
                    v-if="entry.url"
                    :href="entry.url"
                    target="_blank"
                    rel="noopener"
                    class="inline-block mt-2 text-xs text-blue-500 hover:underline truncate max-w-full"
                    @click.stop
                  >
                    {{ entry.url }}
                  </a>
                  
                  <!-- Screenshot preview -->
                  <div
                    v-if="entry.event_type === 'screenshot' && entry.screenshot_path"
                    class="mt-2"
                  >
                    <img
                      :src="timelineApi.getScreenshotUrl(sessionId, screenshotEntries.findIndex(s => s.entry === entry))"
                      :alt="entry.title"
                      class="rounded border border-gray-200 dark:border-gray-600 max-h-48 cursor-zoom-in"
                      @click.stop="handleScreenshotClick(screenshotEntries.findIndex(s => s.entry === entry), entry)"
                    />
                  </div>
                  
                  <!-- Metadata -->
                  <div
                    v-if="Object.keys(entry.metadata).length > 0"
                    class="mt-2 text-xs text-gray-400"
                  >
                    <pre class="whitespace-pre-wrap">{{ JSON.stringify(entry.metadata, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Screenshots gallery (optional) -->
    <div
      v-if="showScreenshots && screenshotEntries.length > 0"
      class="flex-shrink-0 border-t border-gray-100 dark:border-gray-800 p-3"
    >
      <p class="text-xs text-gray-500 mb-2">截图预览</p>
      <div class="flex gap-2 overflow-x-auto pb-1">
        <div
          v-for="({ entry, index }, i) in screenshotEntries"
          :key="i"
          class="flex-shrink-0 w-20 h-14 rounded overflow-hidden cursor-pointer hover:ring-2 hover:ring-blue-500 transition-shadow"
          @click="handleScreenshotClick(i, entry)"
        >
          <img
            :src="timelineApi.getScreenshotUrl(sessionId, i)"
            :alt="entry.title"
            class="w-full h-full object-cover"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.research-timeline {
  --timeline-line-color: theme('colors.gray.200');
}

.dark .research-timeline {
  --timeline-line-color: theme('colors.gray.700');
}
</style>
