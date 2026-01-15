<script setup lang="ts">
import { ref, computed } from 'vue'
import type { TimeLapseFrame, TimeLapsePlayback } from './types'
import { FRAME_TYPE_CONFIG } from './types'

export interface TimeLapseGalleryProps {
  playback: TimeLapsePlayback | null
  loading?: boolean
}

const props = withDefaults(defineProps<TimeLapseGalleryProps>(), {
  loading: false,
})

const emit = defineEmits<{
  close: []
}>()

const selectedFrame = ref<TimeLapseFrame | null>(null)

const formatDuration = (ms: number) => {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  if (minutes > 0) {
    return `${minutes}分${seconds % 60}秒`
  }
  return `${seconds}秒`
}

const formatTimestamp = (ms: number) => {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

const truncateUrl = (url?: string, maxLen = 50) => {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    const path = parsed.pathname.length > 30 
      ? parsed.pathname.slice(0, 30) + '...'
      : parsed.pathname
    return `${parsed.hostname}${path}`
  } catch {
    return url.length > maxLen ? url.slice(0, maxLen) + '...' : url
  }
}

const getFrameConfig = (type: string) => {
  return FRAME_TYPE_CONFIG[type as keyof typeof FRAME_TYPE_CONFIG] || {
    icon: 'circle',
    label: type,
    bgColor: 'bg-gray-500/20',
  }
}

const framesWithScreenshots = computed(() => {
  if (!props.playback) return []
  return props.playback.frames.filter(f => f.screenshotPath)
})

const selectFrame = (frame: TimeLapseFrame) => {
  selectedFrame.value = frame
}

const closeDetail = () => {
  selectedFrame.value = null
}
</script>

<template>
  <div class="time-lapse-gallery fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-8">
    <div class="bg-bg-primary rounded-xl border border-border-default max-w-5xl w-full max-h-[90vh] flex flex-col overflow-hidden">
      <!-- 头部 -->
      <div class="px-6 py-4 border-b border-border-default flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-text-primary">研究过程回溯</h2>
          <p v-if="playback" class="text-sm text-text-tertiary mt-0.5">
            {{ playback.title }} · {{ formatDuration(playback.totalDurationMs) }} · {{ playback.frames.length }} 个关键帧
          </p>
        </div>
        <button 
          @click="emit('close')"
          class="p-2 hover:bg-bg-tertiary rounded-lg transition-colors"
        >
          <svg class="w-5 h-5 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <svg class="w-8 h-8 animate-spin text-accent-primary" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span class="text-text-secondary">加载研究记录...</span>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="!playback || playback.frames.length === 0" class="flex-1 flex items-center justify-center">
        <div class="text-center">
          <svg class="w-16 h-16 mx-auto text-text-tertiary mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="text-text-secondary">暂无研究记录</p>
        </div>
      </div>
      
      <!-- 画廊网格 -->
      <div v-else class="flex-1 overflow-y-auto p-6">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div 
            v-for="frame in playback.frames"
            :key="frame.id"
            class="group relative rounded-lg overflow-hidden border border-border-default hover:border-accent-primary/50 transition-all cursor-pointer"
            :class="getFrameConfig(frame.frameType).bgColor"
            @click="selectFrame(frame)"
          >
            <!-- 截图 -->
            <div class="aspect-video bg-bg-tertiary">
              <img 
                v-if="frame.screenshotPath"
                :src="frame.screenshotPath"
                :alt="frame.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg class="w-8 h-8 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            
            <!-- 信息覆盖层 -->
            <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="absolute bottom-0 left-0 right-0 p-3">
                <div class="flex items-center gap-1.5 mb-1">
                  <span class="px-1.5 py-0.5 text-xs rounded bg-white/20 text-white">
                    {{ getFrameConfig(frame.frameType).label }}
                  </span>
                  <span class="text-xs text-white/70">
                    {{ formatTimestamp(frame.timestampMs) }}
                  </span>
                </div>
                <p class="text-sm text-white font-medium truncate">{{ frame.title }}</p>
              </div>
            </div>
            
            <!-- 时间戳角标 -->
            <div class="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-black/50 text-xs text-white">
              {{ formatTimestamp(frame.timestampMs) }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- 帧详情弹窗 -->
      <div 
        v-if="selectedFrame"
        class="fixed inset-0 z-60 bg-black/90 flex items-center justify-center p-8"
        @click.self="closeDetail"
      >
        <div class="bg-bg-primary rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          <!-- 大图 -->
          <div class="relative bg-bg-tertiary">
            <img 
              v-if="selectedFrame.screenshotPath"
              :src="selectedFrame.screenshotPath"
              :alt="selectedFrame.title"
              class="w-full max-h-[60vh] object-contain"
            />
            <div v-else class="h-64 flex items-center justify-center">
              <span class="text-text-tertiary">无截图</span>
            </div>
            <button 
              @click="closeDetail"
              class="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 transition-colors"
            >
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- 详情 -->
          <div class="p-6">
            <div class="flex items-center gap-2 mb-2">
              <span 
                class="px-2 py-1 text-xs rounded"
                :class="getFrameConfig(selectedFrame.frameType).bgColor"
              >
                {{ getFrameConfig(selectedFrame.frameType).label }}
              </span>
              <span class="text-sm text-text-tertiary">
                {{ formatTimestamp(selectedFrame.timestampMs) }}
              </span>
            </div>
            <h3 class="text-lg font-semibold text-text-primary mb-2">{{ selectedFrame.title }}</h3>
            <p class="text-sm text-text-secondary mb-4">{{ selectedFrame.description }}</p>
            
            <div v-if="selectedFrame.url" class="flex items-center gap-2 text-sm">
              <svg class="w-4 h-4 text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
              <a 
                :href="selectedFrame.url"
                target="_blank"
                class="text-accent-primary hover:underline truncate"
              >
                {{ truncateUrl(selectedFrame.url) }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.time-lapse-gallery {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>
