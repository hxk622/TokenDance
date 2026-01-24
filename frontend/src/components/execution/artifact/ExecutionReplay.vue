<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { 
  Play, Pause, SkipBack, SkipForward, 
  ChevronLeft, ChevronRight, Clock, Image,
  FileText, Code2, Terminal, AlertCircle
} from 'lucide-vue-next'

interface ReplayStep {
  id: string
  timestamp: number
  type: 'screenshot' | 'log' | 'action' | 'error' | 'result'
  title: string
  description?: string
  screenshot?: string
  data?: any
}

interface Props {
  /** Replay steps */
  steps: ReplayStep[]
  /** Auto play speed (ms per step) */
  playSpeed?: number
  /** Show thumbnails */
  showThumbnails?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  playSpeed: 2000,
  showThumbnails: true
})

const emit = defineEmits<{
  'step-change': [step: ReplayStep, index: number]
}>()

// State
const currentIndex = ref(0)
const isPlaying = ref(false)
const playbackSpeed = ref(1)

// Timer
let playTimer: ReturnType<typeof setInterval> | null = null

// Computed
const currentStep = computed(() => props.steps[currentIndex.value])

const progress = computed(() => 
  props.steps.length > 0 ? ((currentIndex.value + 1) / props.steps.length) * 100 : 0
)

const totalDuration = computed(() => {
  if (props.steps.length === 0) return 0
  const first = props.steps[0].timestamp
  const last = props.steps[props.steps.length - 1].timestamp
  return last - first
})

const currentTimestamp = computed(() => {
  if (!currentStep.value || props.steps.length === 0) return 0
  return currentStep.value.timestamp - props.steps[0].timestamp
})

// Step type icons
function getStepIcon(type: ReplayStep['type']) {
  switch (type) {
    case 'screenshot': return Image
    case 'log': return FileText
    case 'action': return Terminal
    case 'error': return AlertCircle
    case 'result': return Code2
    default: return Clock
  }
}

// Format duration
function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

// Playback controls
function togglePlay() {
  if (isPlaying.value) {
    pause()
  } else {
    play()
  }
}

function play() {
  if (currentIndex.value >= props.steps.length - 1) {
    currentIndex.value = 0
  }
  
  isPlaying.value = true
  
  playTimer = setInterval(() => {
    if (currentIndex.value < props.steps.length - 1) {
      currentIndex.value++
    } else {
      pause()
    }
  }, props.playSpeed / playbackSpeed.value)
}

function pause() {
  isPlaying.value = false
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

function goToStep(index: number) {
  currentIndex.value = Math.max(0, Math.min(index, props.steps.length - 1))
  emit('step-change', currentStep.value, currentIndex.value)
}

function prevStep() {
  goToStep(currentIndex.value - 1)
}

function nextStep() {
  goToStep(currentIndex.value + 1)
}

function setSpeed(speed: number) {
  playbackSpeed.value = speed
  if (isPlaying.value) {
    pause()
    play()
  }
}

// Timeline click
function handleTimelineClick(e: MouseEvent) {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  const index = Math.floor(percent * props.steps.length)
  goToStep(index)
}

// Watch step changes
watch(currentIndex, () => {
  emit('step-change', currentStep.value, currentIndex.value)
})

// Cleanup
onUnmounted(() => {
  if (playTimer) {
    clearInterval(playTimer)
  }
})
</script>

<template>
  <div class="execution-replay">
    <!-- Main Preview -->
    <div class="preview-area">
      <!-- Screenshot -->
      <div
        v-if="currentStep?.screenshot"
        class="screenshot-view"
      >
        <img
          :src="currentStep.screenshot"
          :alt="currentStep.title"
        >
      </div>
      
      <!-- Log/Data View -->
      <div
        v-else-if="currentStep?.data"
        class="data-view"
      >
        <pre><code>{{ JSON.stringify(currentStep.data, null, 2) }}</code></pre>
      </div>
      
      <!-- Empty State -->
      <div
        v-else
        class="empty-preview"
      >
        <component
          :is="getStepIcon(currentStep?.type || 'log')"
          class="w-12 h-12"
        />
        <span>{{ currentStep?.title || '无预览内容' }}</span>
      </div>

      <!-- Step Info Overlay -->
      <div
        v-if="currentStep"
        class="step-info-overlay"
      >
        <component
          :is="getStepIcon(currentStep.type)"
          class="w-4 h-4"
        />
        <span class="step-title">{{ currentStep.title }}</span>
        <span class="step-time">{{ formatDuration(currentTimestamp) }}</span>
      </div>
    </div>

    <!-- Timeline -->
    <div class="timeline-area">
      <!-- Progress Bar -->
      <div
        class="timeline-bar"
        @click="handleTimelineClick"
      >
        <div
          class="timeline-progress"
          :style="{ width: `${progress}%` }"
        />
        <div
          class="timeline-handle"
          :style="{ left: `${progress}%` }"
        />
        
        <!-- Step Markers -->
        <div 
          v-for="(step, index) in steps"
          :key="step.id"
          :class="['step-marker', step.type, { active: index === currentIndex }]"
          :style="{ left: `${(index / steps.length) * 100}%` }"
          :title="step.title"
          @click.stop="goToStep(index)"
        />
      </div>

      <!-- Controls -->
      <div class="timeline-controls">
        <div class="controls-left">
          <button
            class="ctrl-btn"
            :disabled="currentIndex === 0"
            @click="prevStep"
          >
            <SkipBack class="w-4 h-4" />
          </button>
          
          <button
            class="ctrl-btn play-btn"
            @click="togglePlay"
          >
            <Pause
              v-if="isPlaying"
              class="w-5 h-5"
            />
            <Play
              v-else
              class="w-5 h-5"
            />
          </button>
          
          <button 
            class="ctrl-btn" 
            :disabled="currentIndex >= steps.length - 1"
            @click="nextStep"
          >
            <SkipForward class="w-4 h-4" />
          </button>

          <!-- Speed -->
          <div class="speed-selector">
            <button 
              v-for="speed in [0.5, 1, 2]"
              :key="speed"
              :class="['speed-btn', { active: playbackSpeed === speed }]"
              @click="setSpeed(speed)"
            >
              {{ speed }}x
            </button>
          </div>
        </div>

        <div class="controls-right">
          <span class="step-counter">
            {{ currentIndex + 1 }} / {{ steps.length }}
          </span>
          <span class="time-display">
            {{ formatDuration(currentTimestamp) }} / {{ formatDuration(totalDuration) }}
          </span>
        </div>
      </div>

      <!-- Thumbnails -->
      <div
        v-if="showThumbnails && steps.length > 0"
        class="thumbnails"
      >
        <button
          v-for="(step, index) in steps"
          :key="step.id"
          :class="['thumbnail', { active: index === currentIndex }]"
          @click="goToStep(index)"
        >
          <img
            v-if="step.screenshot"
            :src="step.screenshot"
            :alt="step.title"
          >
          <div
            v-else
            class="thumbnail-placeholder"
          >
            <component
              :is="getStepIcon(step.type)"
              class="w-4 h-4"
            />
          </div>
          <span class="thumbnail-index">{{ index + 1 }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.execution-replay {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

/* Preview Area */
.preview-area {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-tertiary);
  overflow: hidden;
}

.screenshot-view {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.screenshot-view img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: var(--any-radius-sm);
}

.data-view {
  width: 100%;
  height: 100%;
  padding: 16px;
  overflow: auto;
}

.data-view pre {
  margin: 0;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 12px;
  color: var(--any-text-primary);
}

.empty-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--any-text-muted);
}

/* Step Info Overlay */
.step-info-overlay {
  position: absolute;
  top: 12px;
  left: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: var(--any-radius-md);
  color: white;
}

.step-title {
  font-size: 13px;
  font-weight: 500;
}

.step-time {
  font-size: 12px;
  font-family: 'SF Mono', monospace;
  opacity: 0.7;
}

/* Timeline Area */
.timeline-area {
  padding: 12px 16px;
  background: var(--any-bg-secondary);
  border-top: 1px solid var(--any-border);
}

/* Timeline Bar */
.timeline-bar {
  position: relative;
  height: 8px;
  background: var(--any-bg-tertiary);
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 12px;
}

.timeline-progress {
  position: absolute;
  height: 100%;
  background: var(--td-state-thinking, #00D9FF);
  border-radius: 4px;
  transition: width 150ms ease;
}

.timeline-handle {
  position: absolute;
  top: 50%;
  width: 14px;
  height: 14px;
  background: white;
  border: 2px solid var(--td-state-thinking, #00D9FF);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  transition: left 150ms ease;
}

/* Step Markers */
.step-marker {
  position: absolute;
  top: 50%;
  width: 6px;
  height: 6px;
  background: var(--any-text-muted);
  border-radius: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: all 150ms ease;
}

.step-marker:hover,
.step-marker.active {
  transform: translate(-50%, -50%) scale(1.5);
}

.step-marker.screenshot {
  background: var(--td-state-executing, #FFD93D);
}

.step-marker.action {
  background: var(--td-state-success, #00E5A0);
}

.step-marker.error {
  background: var(--td-state-error, #FF4D6A);
}

/* Controls */
.timeline-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ctrl-btn {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.ctrl-btn:hover:not(:disabled) {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.ctrl-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.play-btn {
  padding: 8px;
  background: var(--td-state-thinking-bg);
  color: var(--td-state-thinking, #00D9FF);
  border-radius: 50%;
}

.play-btn:hover {
  background: var(--td-state-thinking);
  color: var(--any-bg-primary);
}

/* Speed Selector */
.speed-selector {
  display: flex;
  gap: 2px;
  padding: 2px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  margin-left: 8px;
}

.speed-btn {
  padding: 4px 8px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  font-size: 11px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all 150ms ease;
}

.speed-btn:hover {
  color: var(--any-text-secondary);
}

.speed-btn.active {
  background: var(--any-bg-primary);
  color: var(--td-state-thinking, #00D9FF);
}

/* Time Display */
.step-counter,
.time-display {
  font-size: 12px;
  font-family: 'SF Mono', monospace;
  color: var(--any-text-muted);
}

/* Thumbnails */
.thumbnails {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--any-border);
  overflow-x: auto;
  scrollbar-width: none;
}

.thumbnails::-webkit-scrollbar {
  display: none;
}

.thumbnail {
  position: relative;
  flex-shrink: 0;
  width: 64px;
  height: 48px;
  padding: 0;
  background: var(--any-bg-tertiary);
  border: 2px solid transparent;
  border-radius: var(--any-radius-sm);
  overflow: hidden;
  cursor: pointer;
  transition: all 150ms ease;
}

.thumbnail:hover {
  border-color: var(--any-border);
}

.thumbnail.active {
  border-color: var(--td-state-thinking, #00D9FF);
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--any-text-muted);
}

.thumbnail-index {
  position: absolute;
  bottom: 2px;
  right: 2px;
  padding: 1px 4px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 2px;
  font-size: 10px;
  color: white;
}
</style>
