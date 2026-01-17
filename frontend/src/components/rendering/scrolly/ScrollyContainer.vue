<script setup lang="ts">
/**
 * 滚动叙事容器
 * Scrolly Container - Main container for scrollytelling
 * 
 * 支持:
 * - 粘性内容区域（如图表、图片）
 * - 滚动进度跟踪
 * - 章节切换事件
 */

import { ref, provide, computed, onMounted, onUnmounted } from 'vue'
import type { ScrollySectionConfig, ScrollyState } from '../types'
import ScrollyProgress from './ScrollyProgress.vue'

// Props
interface Props {
  stickyContent?: boolean
  progressBar?: boolean
  progressPosition?: 'left' | 'right'
  stickyWidth?: string
  contentWidth?: string
  debug?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  stickyContent: true,
  progressBar: true,
  progressPosition: 'left',
  stickyWidth: '45%',
  contentWidth: '50%',
  debug: false,
})

// Emits
const emit = defineEmits<{
  (e: 'sectionChange', data: { current: string; previous: string | null }): void
  (e: 'progress', data: { section: string; ratio: number }): void
  (e: 'scroll', data: { scrollY: number; direction: 'up' | 'down' }): void
}>()

// State
const activeSection = ref<string | null>(null)
const previousSection = ref<string | null>(null)
const overallProgress = ref(0)
const scrollDirection = ref<'up' | 'down'>('down')
const sections = ref<Map<string, { visible: boolean; ratio: number }>>(new Map())
const containerRef = ref<HTMLElement | null>(null)

// Track last scroll position
let lastScrollY = 0

// Provide state to children
const scrollyState: ScrollyState = {
  activeSection: null,
  progress: 0,
  direction: 'down',
  sections: new Map(),
}

provide('scrollyState', scrollyState)

// Computed styles
const containerStyle = computed(() => ({
  '--sticky-width': props.stickyWidth,
  '--content-width': props.contentWidth,
}))

// Handle section enter
function handleSectionEnter(data: { id: string; ratio: number }) {
  const oldActive = activeSection.value
  
  sections.value.set(data.id, { visible: true, ratio: data.ratio })
  activeSection.value = data.id
  
  if (oldActive !== data.id) {
    previousSection.value = oldActive
    emit('sectionChange', { current: data.id, previous: oldActive })
    
    if (props.debug) {
      console.log(`[ScrollyContainer] Active section: ${data.id}`)
    }
  }
}

// Handle section leave
function handleSectionLeave(data: { id: string; ratio: number }) {
  sections.value.set(data.id, { visible: false, ratio: data.ratio })
  
  // If the leaving section is the active one, find the next visible section
  if (activeSection.value === data.id) {
    const visibleSections = Array.from(sections.value.entries())
      .filter(([_, state]) => state.visible)
      .sort((a, b) => b[1].ratio - a[1].ratio)
    
    if (visibleSections.length > 0) {
      activeSection.value = visibleSections[0][0]
    }
  }
}

// Handle section progress
function handleSectionProgress(data: { id: string; ratio: number }) {
  sections.value.set(data.id, { 
    visible: sections.value.get(data.id)?.visible ?? false, 
    ratio: data.ratio 
  })
  emit('progress', { section: data.id, ratio: data.ratio })
}

// Handle scroll
function handleScroll() {
  const currentScrollY = window.scrollY
  scrollDirection.value = currentScrollY > lastScrollY ? 'down' : 'up'
  lastScrollY = currentScrollY
  
  // Calculate overall progress
  if (containerRef.value) {
    const rect = containerRef.value.getBoundingClientRect()
    const containerHeight = rect.height
    const viewportHeight = window.innerHeight
    const scrolled = -rect.top
    const maxScroll = containerHeight - viewportHeight
    
    if (maxScroll > 0) {
      overallProgress.value = Math.max(0, Math.min(1, scrolled / maxScroll))
    }
  }
  
  emit('scroll', { scrollY: currentScrollY, direction: scrollDirection.value })
}

// Lifecycle
onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  handleScroll() // Initial calculation
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Expose methods
defineExpose({
  activeSection,
  overallProgress,
  scrollToSection: (sectionId: string) => {
    const element = document.querySelector(`[data-section-id="${sectionId}"]`)
    element?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  },
})
</script>

<template>
  <div 
    ref="containerRef"
    class="scrolly-container"
    :class="{ 
      'has-sticky': stickyContent,
      'progress-left': progressPosition === 'left',
      'progress-right': progressPosition === 'right',
    }"
    :style="containerStyle"
  >
    <!-- Progress Bar -->
    <ScrollyProgress 
      v-if="progressBar"
      :progress="overallProgress"
      :position="progressPosition"
      :sections="Array.from(sections.entries()).map(([id, state]) => ({ id, ...state }))"
      :active-section="activeSection"
    />
    
    <!-- Sticky Content Area -->
    <div v-if="stickyContent" class="sticky-area">
      <div class="sticky-content">
        <slot 
          name="sticky" 
          :active-section="activeSection"
          :progress="overallProgress"
          :direction="scrollDirection"
        />
      </div>
    </div>
    
    <!-- Scrolling Content Area -->
    <div class="scroll-area">
      <slot 
        :active-section="activeSection"
        :progress="overallProgress"
        :on-section-enter="handleSectionEnter"
        :on-section-leave="handleSectionLeave"
        :on-section-progress="handleSectionProgress"
      />
    </div>
    
    <!-- Debug Panel -->
    <div v-if="debug" class="debug-panel">
      <div class="debug-item">
        <span class="debug-label">Active:</span>
        <span class="debug-value">{{ activeSection || 'none' }}</span>
      </div>
      <div class="debug-item">
        <span class="debug-label">Progress:</span>
        <span class="debug-value">{{ (overallProgress * 100).toFixed(0) }}%</span>
      </div>
      <div class="debug-item">
        <span class="debug-label">Direction:</span>
        <span class="debug-value">{{ scrollDirection }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrolly-container {
  position: relative;
  display: flex;
  gap: 2rem;
}

.scrolly-container.has-sticky {
  min-height: 100vh;
}

/* Sticky area */
.sticky-area {
  position: relative;
  width: var(--sticky-width, 45%);
  flex-shrink: 0;
}

.sticky-content {
  position: sticky;
  top: 2rem;
  max-height: calc(100vh - 4rem);
  overflow: hidden;
}

/* Scroll area */
.scroll-area {
  flex: 1;
  width: var(--content-width, 50%);
}

/* Progress bar positioning */
.scrolly-container.progress-left .sticky-area {
  order: 2;
}

.scrolly-container.progress-left .scroll-area {
  order: 1;
}

/* Debug panel */
.debug-panel {
  position: fixed;
  bottom: 16px;
  right: 16px;
  background: rgba(0, 0, 0, 0.85);
  color: #ffffff;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 0.75rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.debug-item {
  display: flex;
  gap: 8px;
}

.debug-label {
  color: #9ca3af;
}

.debug-value {
  color: #10b981;
  font-family: monospace;
}

/* Responsive */
@media (max-width: 1024px) {
  .scrolly-container.has-sticky {
    flex-direction: column;
  }
  
  .sticky-area {
    width: 100%;
    height: 50vh;
  }
  
  .sticky-content {
    position: relative;
    top: 0;
    max-height: 100%;
  }
  
  .scroll-area {
    width: 100%;
  }
}
</style>
