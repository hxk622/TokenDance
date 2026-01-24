<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  Play, Pause, Volume2, VolumeX, Maximize2, Minimize2,
  SkipBack, SkipForward, Settings, Download
} from 'lucide-vue-next'

interface Props {
  /** Video source URL */
  src: string
  /** Poster image URL */
  poster?: string
  /** Auto play */
  autoplay?: boolean
  /** Loop playback */
  loop?: boolean
  /** Initial volume (0-1) */
  volume?: number
  /** Video title */
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  poster: '',
  autoplay: false,
  loop: false,
  volume: 1,
  title: ''
})

const emit = defineEmits<{
  'play': []
  'pause': []
  'ended': []
  'timeupdate': [currentTime: number, duration: number]
}>()

// Refs
const videoRef = ref<HTMLVideoElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)

// State
const isPlaying = ref(false)
const isMuted = ref(false)
const isFullscreen = ref(false)
const showControls = ref(true)
const currentTime = ref(0)
const duration = ref(0)
const buffered = ref(0)
const volumeLevel = ref(props.volume)
const playbackSpeed = ref(1)
const showSpeedMenu = ref(false)

// Speed options
const speedOptions = [0.5, 0.75, 1, 1.25, 1.5, 2]

// Computed
const progress = computed(() => 
  duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
)

const bufferedPercent = computed(() => 
  duration.value > 0 ? (buffered.value / duration.value) * 100 : 0
)

const formattedCurrentTime = computed(() => formatTime(currentTime.value))
const formattedDuration = computed(() => formatTime(duration.value))

// Format time as MM:SS or HH:MM:SS
function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }
  return `${m}:${s.toString().padStart(2, '0')}`
}

// Video controls
function togglePlay() {
  if (!videoRef.value) return
  
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play()
  }
}

function toggleMute() {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

function setVolume(e: Event) {
  if (!videoRef.value) return
  const target = e.target as HTMLInputElement
  volumeLevel.value = parseFloat(target.value)
  videoRef.value.volume = volumeLevel.value
  isMuted.value = volumeLevel.value === 0
}

function seek(e: MouseEvent) {
  if (!videoRef.value || !duration.value) return
  
  const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * duration.value
}

function skip(seconds: number) {
  if (!videoRef.value) return
  videoRef.value.currentTime = Math.max(0, Math.min(duration.value, currentTime.value + seconds))
}

function setSpeed(speed: number) {
  if (!videoRef.value) return
  playbackSpeed.value = speed
  videoRef.value.playbackRate = speed
  showSpeedMenu.value = false
}

function toggleFullscreen() {
  if (!containerRef.value) return
  
  if (!document.fullscreenElement) {
    containerRef.value.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

function download() {
  const link = document.createElement('a')
  link.href = props.src
  link.download = props.title || 'video'
  link.click()
}

// Event handlers
function handlePlay() {
  isPlaying.value = true
  emit('play')
}

function handlePause() {
  isPlaying.value = false
  emit('pause')
}

function handleEnded() {
  isPlaying.value = false
  emit('ended')
}

function handleTimeUpdate() {
  if (!videoRef.value) return
  currentTime.value = videoRef.value.currentTime
  emit('timeupdate', currentTime.value, duration.value)
}

function handleLoadedMetadata() {
  if (!videoRef.value) return
  duration.value = videoRef.value.duration
}

function handleProgress() {
  if (!videoRef.value) return
  const buf = videoRef.value.buffered
  if (buf.length > 0) {
    buffered.value = buf.end(buf.length - 1)
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

// Controls auto-hide
let controlsTimeout: ReturnType<typeof setTimeout> | null = null

function showControlsTemporarily() {
  showControls.value = true
  if (controlsTimeout) clearTimeout(controlsTimeout)
  
  if (isPlaying.value) {
    controlsTimeout = setTimeout(() => {
      showControls.value = false
    }, 3000)
  }
}

// Keyboard shortcuts
function handleKeydown(e: KeyboardEvent) {
  if (e.key === ' ' || e.key === 'k') {
    e.preventDefault()
    togglePlay()
  } else if (e.key === 'ArrowLeft') {
    skip(-5)
  } else if (e.key === 'ArrowRight') {
    skip(5)
  } else if (e.key === 'm') {
    toggleMute()
  } else if (e.key === 'f') {
    toggleFullscreen()
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  
  if (props.autoplay && videoRef.value) {
    videoRef.value.play()
  }
})

onUnmounted(() => {
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  if (controlsTimeout) clearTimeout(controlsTimeout)
})
</script>

<template>
  <div 
    ref="containerRef"
    class="video-player"
    tabindex="0"
    @mousemove="showControlsTemporarily"
    @mouseleave="isPlaying && (showControls = false)"
    @keydown="handleKeydown"
  >
    <!-- Video Element -->
    <video
      ref="videoRef"
      class="video-element"
      :src="src"
      :poster="poster"
      :loop="loop"
      playsinline
      @play="handlePlay"
      @pause="handlePause"
      @ended="handleEnded"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleLoadedMetadata"
      @progress="handleProgress"
      @click="togglePlay"
    />

    <!-- Play Button Overlay -->
    <Transition name="fade">
      <button 
        v-if="!isPlaying" 
        class="play-overlay"
        @click="togglePlay"
      >
        <Play class="play-icon" />
      </button>
    </Transition>

    <!-- Controls -->
    <Transition name="slide-up">
      <div
        v-show="showControls"
        class="controls"
      >
        <!-- Progress Bar -->
        <div
          class="progress-bar"
          @click="seek"
        >
          <div
            class="progress-buffered"
            :style="{ width: `${bufferedPercent}%` }"
          />
          <div
            class="progress-played"
            :style="{ width: `${progress}%` }"
          />
          <div
            class="progress-handle"
            :style="{ left: `${progress}%` }"
          />
        </div>

        <!-- Control Buttons -->
        <div class="controls-row">
          <div class="controls-left">
            <button
              class="ctrl-btn"
              title="后退 5s"
              @click="skip(-5)"
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
              title="前进 5s"
              @click="skip(5)"
            >
              <SkipForward class="w-4 h-4" />
            </button>

            <!-- Volume -->
            <div class="volume-control">
              <button
                class="ctrl-btn"
                @click="toggleMute"
              >
                <VolumeX
                  v-if="isMuted || volumeLevel === 0"
                  class="w-4 h-4"
                />
                <Volume2
                  v-else
                  class="w-4 h-4"
                />
              </button>
              <input 
                type="range"
                class="volume-slider"
                min="0"
                max="1"
                step="0.05"
                :value="volumeLevel"
                @input="setVolume"
              >
            </div>

            <!-- Time -->
            <span class="time-display">
              {{ formattedCurrentTime }} / {{ formattedDuration }}
            </span>
          </div>

          <div class="controls-right">
            <!-- Speed -->
            <div class="speed-control">
              <button 
                class="ctrl-btn"
                :title="`播放速度: ${playbackSpeed}x`"
                @click="showSpeedMenu = !showSpeedMenu"
              >
                <Settings class="w-4 h-4" />
                <span class="speed-label">{{ playbackSpeed }}x</span>
              </button>
              
              <Transition name="fade">
                <div
                  v-if="showSpeedMenu"
                  class="speed-menu"
                >
                  <button 
                    v-for="speed in speedOptions"
                    :key="speed"
                    :class="['speed-option', { active: playbackSpeed === speed }]"
                    @click="setSpeed(speed)"
                  >
                    {{ speed }}x
                  </button>
                </div>
              </Transition>
            </div>

            <button
              class="ctrl-btn"
              title="下载"
              @click="download"
            >
              <Download class="w-4 h-4" />
            </button>

            <button
              class="ctrl-btn"
              title="全屏"
              @click="toggleFullscreen"
            >
              <Minimize2
                v-if="isFullscreen"
                class="w-4 h-4"
              />
              <Maximize2
                v-else
                class="w-4 h-4"
              />
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.video-player {
  position: relative;
  width: 100%;
  height: 100%;
  background: #000;
  border-radius: var(--any-radius-lg);
  overflow: hidden;
  outline: none;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Play Overlay */
.play-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 200ms ease;
}

.play-overlay:hover {
  background: rgba(0, 0, 0, 0.8);
  transform: translate(-50%, -50%) scale(1.1);
}

.play-icon {
  width: 32px;
  height: 32px;
  color: white;
  margin-left: 4px;
}

/* Controls */
.controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
}

.progress-bar {
  position: relative;
  height: 4px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
  cursor: pointer;
  margin-bottom: 12px;
}

.progress-bar:hover {
  height: 6px;
}

.progress-buffered {
  position: absolute;
  height: 100%;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.progress-played {
  position: absolute;
  height: 100%;
  background: var(--td-state-thinking, #00D9FF);
  border-radius: 2px;
}

.progress-handle {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 150ms ease;
}

.progress-bar:hover .progress-handle {
  opacity: 1;
}

.controls-row {
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
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: white;
  cursor: pointer;
  transition: all 150ms ease;
}

.ctrl-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.play-btn {
  padding: 8px;
}

/* Volume */
.volume-control {
  display: flex;
  align-items: center;
  gap: 4px;
}

.volume-slider {
  width: 60px;
  height: 4px;
  -webkit-appearance: none;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
}

/* Time Display */
.time-display {
  font-size: 12px;
  font-family: 'SF Mono', monospace;
  color: rgba(255, 255, 255, 0.8);
  margin-left: 8px;
}

/* Speed Control */
.speed-control {
  position: relative;
}

.speed-label {
  font-size: 11px;
}

.speed-menu {
  position: absolute;
  bottom: 100%;
  right: 0;
  margin-bottom: 8px;
  padding: 4px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.speed-option {
  display: block;
  width: 100%;
  padding: 6px 16px;
  background: transparent;
  border: none;
  font-size: 12px;
  color: var(--any-text-secondary);
  text-align: left;
  cursor: pointer;
  transition: all 150ms ease;
}

.speed-option:hover {
  background: var(--any-bg-hover);
}

.speed-option.active {
  color: var(--td-state-thinking, #00D9FF);
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 200ms ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Fullscreen */
.video-player:fullscreen {
  border-radius: 0;
}
</style>
