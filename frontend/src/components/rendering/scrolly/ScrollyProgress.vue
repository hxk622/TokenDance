<script setup lang="ts">
/**
 * 滚动进度指示器
 * Scrolly Progress - Visual progress indicator for scrollytelling
 */

import { computed } from 'vue'

// Props
interface Props {
  progress: number
  position?: 'left' | 'right'
  sections?: Array<{ id: string; visible: boolean; ratio: number }>
  activeSection?: string | null
  showLabels?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  position: 'left',
  sections: () => [],
  activeSection: null,
  showLabels: false,
})

// Progress bar height
const progressHeight = computed(() => `${props.progress * 100}%`)

// Section dots
const sectionDots = computed(() => {
  if (!props.sections.length) return []
  
  const total = props.sections.length
  return props.sections.map((section, index) => ({
    ...section,
    top: `${(index / Math.max(total - 1, 1)) * 100}%`,
    isActive: section.id === props.activeSection,
  }))
})
</script>

<template>
  <div 
    class="scrolly-progress"
    :class="[`position-${position}`]"
  >
    <!-- Track -->
    <div class="progress-track">
      <!-- Fill -->
      <div 
        class="progress-fill"
        :style="{ height: progressHeight }"
      />
      
      <!-- Section Dots -->
      <div 
        v-for="dot in sectionDots"
        :key="dot.id"
        class="section-dot"
        :class="{ 
          'is-active': dot.isActive,
          'is-visible': dot.visible,
        }"
        :style="{ top: dot.top }"
        :title="dot.id"
      >
        <span
          v-if="showLabels"
          class="dot-label"
        >{{ dot.id }}</span>
      </div>
    </div>
    
    <!-- Progress Percentage -->
    <div class="progress-label">
      {{ Math.round(progress * 100) }}%
    </div>
  </div>
</template>

<style scoped>
.scrolly-progress {
  position: fixed;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.position-left {
  left: 24px;
}

.position-right {
  right: 24px;
}

.progress-track {
  position: relative;
  width: 4px;
  height: 200px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: visible;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(180deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 2px;
  transition: height 100ms ease;
}

.section-dot {
  position: absolute;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: #ffffff;
  border: 2px solid #d1d5db;
  border-radius: 50%;
  transition: all 200ms ease;
  cursor: pointer;
}

.section-dot:hover {
  border-color: #9ca3af;
  transform: translate(-50%, -50%) scale(1.2);
}

.section-dot.is-visible {
  border-color: #a5b4fc;
}

.section-dot.is-active {
  background: #4f46e5;
  border-color: #4f46e5;
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.2);
}

.dot-label {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  font-size: 0.75rem;
  color: #6b7280;
  background: #ffffff;
  padding: 2px 6px;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  opacity: 0;
  transition: opacity 200ms ease;
}

.section-dot:hover .dot-label,
.section-dot.is-active .dot-label {
  opacity: 1;
}

.position-right .dot-label {
  left: auto;
  right: 20px;
}

.progress-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #6b7280;
  background: #ffffff;
  padding: 2px 8px;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Responsive - hide on mobile */
@media (max-width: 768px) {
  .scrolly-progress {
    display: none;
  }
}
</style>
