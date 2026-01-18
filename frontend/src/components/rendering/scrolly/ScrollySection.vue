<script setup lang="ts">
/**
 * 滚动章节组件
 * Scrolly Section - Individual section for scrollytelling
 * 
 * 使用 IntersectionObserver 检测可见性
 */

import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import type { ScrollySectionConfig } from '../types'

// Props
interface Props {
  id: string
  title?: string
  threshold?: number
  offset?: number
  animation?: 'fade' | 'slide' | 'scale' | 'none'
  duration?: number
  debug?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  threshold: 0.5,
  offset: 0,
  animation: 'fade',
  duration: 300,
  debug: false,
})

// Emits
const emit = defineEmits<{
  (e: 'enter', data: { id: string; ratio: number }): void
  (e: 'leave', data: { id: string; ratio: number }): void
  (e: 'progress', data: { id: string; ratio: number }): void
}>()

// Refs
const sectionRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const visibilityRatio = ref(0)

// Observer
let observer: IntersectionObserver | null = null

// Animation styles
const animationStyles = computed(() => {
  if (props.animation === 'none') return {}
  
  const baseTransition = `opacity ${props.duration}ms ease, transform ${props.duration}ms ease`
  
  if (!isVisible.value) {
    switch (props.animation) {
      case 'fade':
        return { opacity: 0, transition: baseTransition }
      case 'slide':
        return { 
          opacity: 0, 
          transform: 'translateY(30px)', 
          transition: baseTransition 
        }
      case 'scale':
        return { 
          opacity: 0, 
          transform: 'scale(0.95)', 
          transition: baseTransition 
        }
      default:
        return { opacity: 0, transition: baseTransition }
    }
  }
  
  return { 
    opacity: 1, 
    transform: 'translateY(0) scale(1)', 
    transition: baseTransition 
  }
})

// Setup observer
function setupObserver() {
  if (!sectionRef.value) return
  
  const options: IntersectionObserverInit = {
    threshold: Array.from({ length: 101 }, (_, i) => i / 100), // 0, 0.01, 0.02, ..., 1
    rootMargin: `${-props.offset}px 0px ${-props.offset}px 0px`,
  }
  
  observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const ratio = entry.intersectionRatio
      visibilityRatio.value = ratio
      
      // Emit progress
      emit('progress', { id: props.id, ratio })
      
      // Check enter/leave based on threshold
      if (ratio >= props.threshold && !isVisible.value) {
        isVisible.value = true
        emit('enter', { id: props.id, ratio })
        
        if (props.debug) {
          console.log(`[ScrollySection] "${props.id}" entered (ratio: ${ratio.toFixed(2)})`)
        }
      } else if (ratio < props.threshold && isVisible.value) {
        isVisible.value = false
        emit('leave', { id: props.id, ratio })
        
        if (props.debug) {
          console.log(`[ScrollySection] "${props.id}" left (ratio: ${ratio.toFixed(2)})`)
        }
      }
    })
  }, options)
  
  observer.observe(sectionRef.value)
}

// Lifecycle
onMounted(() => {
  setupObserver()
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
    observer = null
  }
})

// Expose state
defineExpose({
  isVisible,
  visibilityRatio,
  scrollIntoView: (options?: ScrollIntoViewOptions) => {
    sectionRef.value?.scrollIntoView(options ?? { behavior: 'smooth', block: 'center' })
  },
})
</script>

<template>
  <section
    ref="sectionRef"
    class="scrolly-section"
    :class="{ 'is-visible': isVisible }"
    :data-section-id="id"
    :style="animationStyles"
  >
    <!-- Section Title -->
    <h2
      v-if="title"
      class="section-title"
    >
      {{ title }}
    </h2>
    
    <!-- Section Content -->
    <div class="section-content">
      <slot
        :is-visible="isVisible"
        :ratio="visibilityRatio"
      />
    </div>
    
    <!-- Debug Info -->
    <div
      v-if="debug"
      class="debug-info"
    >
      <span>ID: {{ id }}</span>
      <span>Visible: {{ isVisible }}</span>
      <span>Ratio: {{ visibilityRatio.toFixed(2) }}</span>
    </div>
  </section>
</template>

<style scoped>
.scrolly-section {
  position: relative;
  min-height: 60vh;
  padding: 2rem;
  margin-bottom: 2rem;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
  margin-bottom: 1.5rem;
}

.section-content {
  position: relative;
}

/* Debug info */
.debug-info {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 12px;
  font-size: 0.75rem;
  color: #6b7280;
  background: #f9fafb;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}
</style>
