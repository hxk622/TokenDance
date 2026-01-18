<script setup lang="ts">
/**
 * PPT Create View - PPT 撰写页面
 *
 * 功能：
 * - 选择分层样式
 * - 编辑幻灯片内容
 * - 自定义颜色
 * - 预览效果
 * - 导出 PPTX 文件
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  PlusIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  SparklesIcon,
  SwatchIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  ChevronUpIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'
import {
  layeredPptApi,
  type LayeredStyleInfo,
  type LayeredSlideRequest,
  type LayeredSlideStyle,
} from '@/api/ppt'

const router = useRouter()

// State
const styles = ref<LayeredStyleInfo[]>([])
const slides = ref<LayeredSlideRequest[]>([])
const selectedSlideIndex = ref(0)
const loading = ref(false)
const generating = ref(false)
const previewUrl = ref<string | null>(null)
const previewLoading = ref(false)
const filename = ref('my_presentation')
const error = ref<string | null>(null)

// 预设颜色
const colorPresets = [
  { name: '蓝紫渐变', accent: '#6366f1', base: '#1a1a2e' },
  { name: '科技青', accent: '#00d4ff', base: '#0a0a1a' },
  { name: '热情红', accent: '#f43f5e', base: '#1f1f1f' },
  { name: '自然绿', accent: '#10b981', base: '#1a2e1a' },
  { name: '优雅金', accent: '#f59e0b', base: '#2e2a1a' },
  { name: '极简白', accent: '#333333', base: '#fafafa' },
]

// Computed
const currentSlide = computed(() => {
  if (!slides.value.length) return null
  return slides.value[selectedSlideIndex.value]
})

const canMoveUp = computed(() => selectedSlideIndex.value > 0)
const canMoveDown = computed(() => selectedSlideIndex.value < slides.value.length - 1)

// Methods
const fetchStyles = async () => {
  loading.value = true
  try {
    styles.value = await layeredPptApi.getStyles()
  } catch (err: any) {
    error.value = '加载样式失败'
    console.error(err)
  } finally {
    loading.value = false
  }
}

const addSlide = (style: LayeredSlideStyle = 'hero_title') => {
  const newSlide: LayeredSlideRequest = {
    style,
    title: '',
    subtitle: '',
    body: '',
    accent_color: '#6366f1',
    base_color: '#1a1a2e',
    title_color: '#ffffff',
    subtitle_color: '#cccccc',
  }
  slides.value.push(newSlide)
  selectedSlideIndex.value = slides.value.length - 1
  updatePreview()
}

const removeSlide = (index: number) => {
  if (slides.value.length <= 1) return
  slides.value.splice(index, 1)
  if (selectedSlideIndex.value >= slides.value.length) {
    selectedSlideIndex.value = slides.value.length - 1
  }
  updatePreview()
}

const moveSlide = (direction: 'up' | 'down') => {
  const index = selectedSlideIndex.value
  const newIndex = direction === 'up' ? index - 1 : index + 1
  
  if (newIndex < 0 || newIndex >= slides.value.length) return
  
  const temp = slides.value[index]
  slides.value[index] = slides.value[newIndex]
  slides.value[newIndex] = temp
  selectedSlideIndex.value = newIndex
}

const selectSlide = (index: number) => {
  selectedSlideIndex.value = index
  updatePreview()
}

const applyColorPreset = (preset: typeof colorPresets[0]) => {
  if (!currentSlide.value) return
  currentSlide.value.accent_color = preset.accent
  currentSlide.value.base_color = preset.base
  
  // 根据背景亮度调整文字颜色
  const isLightBg = preset.base.toLowerCase() === '#fafafa' || preset.base.toLowerCase() === '#ffffff'
  currentSlide.value.title_color = isLightBg ? '#1e293b' : '#ffffff'
  currentSlide.value.subtitle_color = isLightBg ? '#475569' : '#cccccc'
  
  updatePreview()
}

const updatePreview = async () => {
  if (!currentSlide.value) return
  
  previewLoading.value = true
  try {
    // 清理旧的 URL
    if (previewUrl.value) {
      URL.revokeObjectURL(previewUrl.value)
    }
    previewUrl.value = await layeredPptApi.previewSlide(currentSlide.value)
  } catch (err) {
    console.error('Preview failed:', err)
  } finally {
    previewLoading.value = false
  }
}

const generatePPT = async () => {
  if (!slides.value.length) {
    error.value = '请至少添加一张幻灯片'
    return
  }
  
  generating.value = true
  error.value = null
  
  try {
    await layeredPptApi.generateAndDownload({
      slides: slides.value,
      filename: filename.value + '.pptx',
    })
  } catch (err: any) {
    error.value = err.response?.data?.detail || '导出失败，请重试'
    console.error(err)
  } finally {
    generating.value = false
  }
}

const getStyleLabel = (style: LayeredSlideStyle): string => {
  const labels: Record<LayeredSlideStyle, string> = {
    hero_title: 'Hero 标题',
    section_header: '章节标题',
    visual_impact: '视觉冲击',
    minimal_clean: '极简风格',
    tech_modern: '科技现代',
  }
  return labels[style] || style
}

// Style icons now handled via Lucide components

// Watch for slide changes to update preview
watch(() => currentSlide.value, () => {
  if (currentSlide.value) {
    updatePreview()
  }
}, { deep: true })

// Initialize
onMounted(async () => {
  await fetchStyles()
  // 添加默认幻灯片
  addSlide('hero_title')
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-4">
            <button
              class="text-gray-500 hover:text-gray-700 transition-colors"
              @click="router.push('/')"
            >
              ← 返回
            </button>
            <h1 class="text-xl font-semibold text-gray-900">
              撰写演示文稿
            </h1>
          </div>
          
          <div class="flex items-center gap-4">
            <input
              v-model="filename"
              placeholder="文件名"
              class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 w-48"
            >
            <button
              :disabled="generating || !slides.length"
              class="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              @click="generatePPT"
            >
              <ArrowDownTrayIcon
                v-if="!generating"
                class="w-5 h-5"
              />
              <ArrowPathIcon
                v-else
                class="w-5 h-5 animate-spin"
              />
              {{ generating ? '导出中...' : '导出 PPTX' }}
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Error Alert -->
    <div
      v-if="error"
      class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4"
    >
      <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center justify-between">
        <span>{{ error }}</span>
        <button
          class="text-red-500 hover:text-red-700"
          @click="error = null"
        >
          ×
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="grid grid-cols-12 gap-6">
        <!-- Left: Slide List -->
        <div class="col-span-3">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-medium text-gray-900">
                幻灯片
              </h2>
              <span class="text-sm text-gray-500">{{ slides.length }} 张</span>
            </div>
            
            <!-- Slide Thumbnails -->
            <div class="space-y-2 max-h-[calc(100vh-300px)] overflow-y-auto">
              <div
                v-for="(slide, index) in slides"
                :key="index"
                :class="[
                  'relative p-3 rounded-lg cursor-pointer transition-all group',
                  selectedSlideIndex === index
                    ? 'bg-indigo-50 border-2 border-indigo-500'
                    : 'bg-gray-50 border-2 border-transparent hover:border-gray-300'
                ]"
                @click="selectSlide(index)"
              >
                <div class="flex items-center gap-2">
                  <span class="text-lg">{{ getStyleIcon(slide.style) }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">
                      {{ slide.title || '未命名' }}
                    </p>
                    <p class="text-xs text-gray-500">
                      {{ getStyleLabel(slide.style) }}
                    </p>
                  </div>
                  <span class="text-xs text-gray-400">{{ index + 1 }}</span>
                </div>
                
                <!-- Delete button -->
                <button
                  v-if="slides.length > 1"
                  class="absolute top-1 right-1 p-1 rounded-full bg-red-100 text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  @click.stop="removeSlide(index)"
                >
                  <TrashIcon class="w-3 h-3" />
                </button>
              </div>
            </div>
            
            <!-- Add Slide Button -->
            <div class="mt-4 pt-4 border-t border-gray-200">
              <div class="relative">
                <button
                  class="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-indigo-600 border border-indigo-200 rounded-lg hover:bg-indigo-50 transition-colors"
                  @click="addSlide()"
                >
                  <PlusIcon class="w-4 h-4" />
                  添加幻灯片
                </button>
              </div>
            </div>

            <!-- Move Buttons -->
            <div
              v-if="slides.length > 1"
              class="mt-2 flex gap-2"
            >
              <button
                :disabled="!canMoveUp"
                class="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="moveSlide('up')"
              >
                <ChevronUpIcon class="w-4 h-4" />
                上移
              </button>
              <button
                :disabled="!canMoveDown"
                class="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                @click="moveSlide('down')"
              >
                <ChevronDownIcon class="w-4 h-4" />
                下移
              </button>
            </div>
          </div>
        </div>

        <!-- Middle: Editor -->
        <div class="col-span-5">
          <div
            v-if="currentSlide"
            class="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
          >
            <h2 class="font-medium text-gray-900 mb-4 flex items-center gap-2">
              <DocumentTextIcon class="w-5 h-5 text-gray-400" />
              编辑幻灯片
            </h2>
            
            <!-- Style Selector -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-2">样式</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="style in styles"
                  :key="style.id"
                  :class="[
                    'p-3 rounded-lg border-2 text-left transition-all',
                    currentSlide.style === style.id
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                  @click="currentSlide.style = style.id; updatePreview()"
                >
                  <p class="text-sm font-medium text-gray-900">
                    {{ style.name }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    {{ style.description.slice(0, 30) }}...
                  </p>
                </button>
              </div>
            </div>

            <!-- Title -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
              <input
                v-model="currentSlide.title"
                placeholder="输入标题..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                @input="updatePreview"
              >
            </div>

            <!-- Subtitle -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">副标题</label>
              <input
                v-model="currentSlide.subtitle"
                placeholder="输入副标题..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                @input="updatePreview"
              >
            </div>

            <!-- Body -->
            <div class="mb-6">
              <label class="block text-sm font-medium text-gray-700 mb-1">正文内容</label>
              <textarea
                v-model="currentSlide.body"
                placeholder="输入正文内容（支持 • 开头的列表）..."
                rows="4"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                @input="updatePreview"
              />
            </div>

            <!-- Color Presets -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                <SwatchIcon class="w-4 h-4" />
                配色方案
              </label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="preset in colorPresets"
                  :key="preset.name"
                  class="flex items-center gap-2 p-2 rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                  @click="applyColorPreset(preset)"
                >
                  <div
                    class="w-6 h-6 rounded-full border border-gray-300"
                    :style="{ background: `linear-gradient(135deg, ${preset.accent} 0%, ${preset.base} 100%)` }"
                  />
                  <span class="text-xs text-gray-600">{{ preset.name }}</span>
                </button>
              </div>
            </div>

            <!-- Custom Colors -->
            <div class="mt-4 pt-4 border-t border-gray-200">
              <details class="group">
                <summary class="text-sm text-gray-500 cursor-pointer hover:text-gray-700">
                  自定义颜色
                </summary>
                <div class="mt-3 grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-xs text-gray-500 mb-1">强调色</label>
                    <div class="flex items-center gap-2">
                      <input
                        v-model="currentSlide.accent_color"
                        type="color"
                        class="w-8 h-8 rounded cursor-pointer"
                        @input="updatePreview"
                      >
                      <input
                        v-model="currentSlide.accent_color"
                        class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        @input="updatePreview"
                      >
                    </div>
                  </div>
                  <div>
                    <label class="block text-xs text-gray-500 mb-1">基础色</label>
                    <div class="flex items-center gap-2">
                      <input
                        v-model="currentSlide.base_color"
                        type="color"
                        class="w-8 h-8 rounded cursor-pointer"
                        @input="updatePreview"
                      >
                      <input
                        v-model="currentSlide.base_color"
                        class="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
                        @input="updatePreview"
                      >
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </div>

        <!-- Right: Preview -->
        <div class="col-span-4">
          <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sticky top-24">
            <div class="flex items-center justify-between mb-4">
              <h2 class="font-medium text-gray-900 flex items-center gap-2">
                <EyeIcon class="w-5 h-5 text-gray-400" />
                实时预览
              </h2>
              <button
                :disabled="previewLoading"
                class="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
                @click="updatePreview"
              >
                <ArrowPathIcon :class="['w-4 h-4', previewLoading && 'animate-spin']" />
              </button>
            </div>
            
            <!-- Preview Image -->
            <div class="aspect-video bg-gray-100 rounded-lg overflow-hidden relative">
              <img
                v-if="previewUrl"
                :src="previewUrl"
                alt="Slide Preview"
                class="w-full h-full object-cover"
              >
              <div
                v-else
                class="absolute inset-0 flex items-center justify-center text-gray-400"
              >
                <SparklesIcon class="w-12 h-12" />
              </div>
              
              <!-- Loading Overlay -->
              <div
                v-if="previewLoading"
                class="absolute inset-0 bg-white/80 flex items-center justify-center"
              >
                <ArrowPathIcon class="w-8 h-8 text-indigo-500 animate-spin" />
              </div>
            </div>

            <!-- Slide Info -->
            <div class="mt-4 p-3 bg-gray-50 rounded-lg">
              <p class="text-sm text-gray-600">
                <span class="font-medium">{{ currentSlide?.title || '未命名' }}</span>
              </p>
              <p class="text-xs text-gray-500 mt-1">
                {{ getStyleLabel(currentSlide?.style || 'hero_title') }} · 
                第 {{ selectedSlideIndex + 1 }}/{{ slides.length }} 张
              </p>
            </div>

            <!-- Quick Actions -->
            <div class="mt-4 flex gap-2">
              <button
                class="flex-1 text-xs px-3 py-2 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
                @click="addSlide('section_header')"
              >
                + 章节页
              </button>
              <button
                class="flex-1 text-xs px-3 py-2 text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50"
                @click="addSlide('tech_modern')"
              >
                + 内容页
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
