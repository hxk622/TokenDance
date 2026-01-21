<script setup lang="ts">
/**
 * ResearchProgress - 研究进度面板
 * 
 * 实时展示深度研究过程，包括：
 * - 阶段进度指示器
 * - 搜索关键词列表
 * - 信息来源卡片
 * - 当前操作状态
 * 
 * 遵循透明化原则：让用户实时看到 AI 具体在做什么
 */
import { ref, computed, watch } from 'vue'
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'
import SearchQueryList from './SearchQueryList.vue'
import SourceCard from './SourceCard.vue'
import type { 
  ResearchProgress as ResearchProgressType, 
  ResearchPhase,
  ResearchSource,
} from './types'
import { PHASE_CONFIG } from './types'

// Props
const props = withDefaults(defineProps<{
  progress: ResearchProgressType | null
  collapsed?: boolean
}>(), {
  collapsed: false,
})

// Emits
const emit = defineEmits<{
  (e: 'toggle-collapse'): void
  (e: 'source-click', source: ResearchSource): void
  (e: 'open-url', url: string): void
}>()

// State
const isCollapsed = ref(props.collapsed)

// Watch for external collapse state changes
watch(() => props.collapsed, (val) => {
  isCollapsed.value = val
})

// Computed
const currentPhaseIndex = computed(() => {
  if (!props.progress) return 0
  return PHASE_CONFIG.findIndex(p => p.id === props.progress!.phase)
})

const phaseProgress = computed(() => {
  if (!props.progress) return 0
  // Calculate overall progress based on phase + phase progress
  const phaseWeight = 100 / PHASE_CONFIG.length
  const baseProgress = currentPhaseIndex.value * phaseWeight
  const currentPhaseContribution = (props.progress.phaseProgress / 100) * phaseWeight
  return Math.round(baseProgress + currentPhaseContribution)
})

const queryStats = computed(() => {
  if (!props.progress) return { done: 0, total: 0 }
  const done = props.progress.queries.filter(q => q.status === 'done').length
  return { done, total: props.progress.queries.length }
})

const sourceStats = computed(() => {
  if (!props.progress) return { done: 0, total: 0 }
  const done = props.progress.sources.filter(s => s.status === 'done').length
  return { done, total: props.progress.sources.length }
})

const estimatedTime = computed(() => {
  if (!props.progress?.estimatedTimeRemaining) return null
  const seconds = props.progress.estimatedTimeRemaining
  if (seconds < 60) return `${seconds}秒`
  const minutes = Math.ceil(seconds / 60)
  return `${minutes}分钟`
})

// Methods
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('toggle-collapse')
}

const handleSourceClick = (source: ResearchSource) => {
  emit('source-click', source)
}

const handleOpenUrl = (url: string) => {
  emit('open-url', url)
}

const getPhaseStatus = (index: number) => {
  if (index < currentPhaseIndex.value) return 'done'
  if (index === currentPhaseIndex.value) return 'active'
  return 'pending'
}
</script>

<template>
  <div 
    class="research-progress"
    :class="{ 'research-progress--collapsed': isCollapsed }"
  >
    <!-- Header -->
    <div 
      class="progress-header"
      @click="toggleCollapse"
    >
      <div class="flex items-center gap-3">
        <!-- Progress Ring -->
        <div class="progress-ring">
          <svg viewBox="0 0 36 36" class="w-9 h-9">
            <!-- Background circle -->
            <circle
              cx="18"
              cy="18"
              r="16"
              fill="none"
              stroke="var(--any-border)"
              stroke-width="2"
            />
            <!-- Progress circle -->
            <circle
              cx="18"
              cy="18"
              r="16"
              fill="none"
              stroke="var(--exec-accent)"
              stroke-width="2"
              stroke-linecap="round"
              :stroke-dasharray="`${phaseProgress}, 100`"
              transform="rotate(-90 18 18)"
              class="progress-circle"
            />
          </svg>
          <span class="progress-text">{{ phaseProgress }}%</span>
        </div>

        <div class="flex-1 min-w-0">
          <h3 class="text-sm font-medium text-[var(--any-text-primary)]">
            研究进度
          </h3>
          <p 
            v-if="progress?.currentAction"
            class="text-xs text-[var(--any-text-secondary)] truncate"
          >
            {{ progress.currentAction }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- Estimated time -->
        <div 
          v-if="estimatedTime"
          class="flex items-center gap-1 text-xs text-[var(--any-text-muted)]"
        >
          <ClockIcon class="w-3.5 h-3.5" />
          <span>约 {{ estimatedTime }}</span>
        </div>

        <!-- Collapse toggle -->
        <button class="collapse-btn">
          <ChevronUpIcon v-if="!isCollapsed" class="w-4 h-4" />
          <ChevronDownIcon v-else class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Content (collapsible) -->
    <div v-show="!isCollapsed" class="progress-content">
      <!-- Phase Indicator -->
      <div class="phase-indicator">
        <div
          v-for="(phase, index) in PHASE_CONFIG"
          :key="phase.id"
          class="phase-item"
          :class="{
            'phase-item--done': getPhaseStatus(index) === 'done',
            'phase-item--active': getPhaseStatus(index) === 'active',
            'phase-item--pending': getPhaseStatus(index) === 'pending',
          }"
        >
          <div class="phase-dot" />
          <span class="phase-label">{{ phase.name }}</span>
          <div 
            v-if="index < PHASE_CONFIG.length - 1" 
            class="phase-line"
            :class="{ 'phase-line--done': getPhaseStatus(index) === 'done' }"
          />
        </div>
      </div>

      <!-- Two Column Layout -->
      <div class="progress-grid">
        <!-- Left: Search Queries -->
        <div v-if="progress && progress.queries.length > 0">
          <SearchQueryList 
            :queries="progress.queries"
            :max-visible="5"
          />
        </div>

        <!-- Right: Sources -->
        <div v-if="progress && progress.sources.length > 0" class="sources-section">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-[var(--any-text-primary)]">
              信息来源
            </span>
            <span class="text-xs text-[var(--any-text-muted)]">
              {{ sourceStats.done }}/{{ sourceStats.total }}
            </span>
          </div>
          
          <div class="sources-list">
            <SourceCard
              v-for="source in progress.sources.slice(0, 6)"
              :key="source.id"
              :source="source"
              compact
              @click="handleSourceClick"
              @open-url="handleOpenUrl"
            />
            
            <div
              v-if="progress.sources.length > 6"
              class="text-xs text-[var(--any-text-muted)] text-center py-2"
            >
              还有 {{ progress.sources.length - 6 }} 个来源
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div 
        v-if="!progress || (progress.queries.length === 0 && progress.sources.length === 0)"
        class="empty-state"
      >
        <p class="text-sm text-[var(--any-text-muted)]">
          研究尚未开始
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.research-progress {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  overflow: hidden;
  transition: all 200ms ease;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 150ms ease;
}

.progress-header:hover {
  background: var(--any-bg-hover);
}

.progress-ring {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-circle {
  transition: stroke-dasharray 300ms ease;
}

.progress-text {
  position: absolute;
  font-size: 10px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  color: var(--any-text-secondary);
  border-radius: 6px;
  transition: all 150ms ease;
}

.collapse-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.progress-content {
  padding: 0 16px 16px;
}

/* Phase Indicator */
.phase-indicator {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--any-border);
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.phase-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--any-border);
  transition: all 200ms ease;
}

.phase-item--done .phase-dot {
  background: var(--exec-success);
}

.phase-item--active .phase-dot {
  background: var(--exec-accent);
  animation: pulse-dot 1.5s ease-in-out infinite;
}

.phase-label {
  font-size: 12px;
  color: var(--any-text-muted);
  transition: color 200ms ease;
}

.phase-item--done .phase-label {
  color: var(--exec-success);
}

.phase-item--active .phase-label {
  color: var(--exec-accent);
  font-weight: 500;
}

.phase-line {
  position: absolute;
  left: calc(100% + 4px);
  width: 20px;
  height: 2px;
  background: var(--any-border);
  transition: background 200ms ease;
}

.phase-line--done {
  background: var(--exec-success);
}

@keyframes pulse-dot {
  0%, 100% {
    opacity: 1;
    box-shadow: 0 0 0 0 var(--exec-accent);
  }
  50% {
    opacity: 0.8;
    box-shadow: 0 0 0 4px rgba(0, 217, 255, 0.2);
  }
}

/* Grid Layout */
.progress-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .progress-grid {
    grid-template-columns: 1fr;
  }
}

.sources-section {
  padding: 12px;
  background: var(--any-bg-primary);
  border-radius: 8px;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

/* Collapsed state */
.research-progress--collapsed .progress-header {
  border-bottom: none;
}
</style>
