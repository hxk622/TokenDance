<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { 
  Play, Pause, Volume2, VolumeX, Download,
  SkipBack, SkipForward, Music
} from 'lucide-vue-next'

interface Props {
  /** Audio source URL */
  src: string
  /** Audio title */
  title?: string
  /** Auto play */
  autoplay?: boolean
  /** Loop playback */
  loop?: boolean
  /** Initial volume (0-1) */
  volume?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  autoplay: false,
  loop: false,
  volume: 1
})

const emit = defineEmits<{
  'play': []
  'pause': []
  'ended': []
  'timeupdate': [currentTime: number, duration: number]
}>()

// Refs
const audioRef = ref<HTMLAudioElement | null>(null)
const waveformRef = ref<HTMLCanvasElement | null>(null)
const progressRef = ref<HTMLDivElement | null>(null)

// State
const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volumeLevel = ref(props.volume)
const waveformData = ref<number[]>([])
const isLoading = ref(true)

// Audio context for waveform
let audioContext: AudioContext | null = null

// Computed
const progress = computed(() => 
  duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
)

const formattedCurrentTime = computed(() => formatTime(currentTime.value))
const formattedDuration = computed(() => formatTime(duration.value))

// Format time as MM:SS
function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

// Generate fake waveform data (for visual effect)
function generateWaveform() {
  const bars = 64
  waveformData.value = Array.from({ length: bars }, () => 
    0.2 + Math.random() * 0.8
  )
  drawWaveform()
}

// Draw waveform on canvas
function drawWaveform() {
  const canvas = waveformRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)
  
  const width = rect.width
  const height = rect.height
  const barWidth = width / waveformData.value.length
  const gap = 2
  
  ctx.clearRect(0, 0, width, height)
  
  waveformData.value.forEach((value, index) => {
    const barHeight = value * height * 0.8
    const x = index * barWidth
    const y = (height - barHeight) / 2
    
    // Progress color
    const progressPercent = progress.value / 100
    const barProgress = index / waveformData.value.length
    
    if (barProgress < progressPercent) {
      ctx.fillStyle = 'var(--td-state-thinking, #00D9FF)'
    } else {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
    }
    
    ctx.beginPath()
    ctx.roundRect(x + gap / 2, y, barWidth - gap, barHeight, 2)
    ctx.fill()
  })
}

// Audio controls
function togglePlay() {
  if (!audioRef.value) return
  
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

function toggleMute() {
  if (!audioRef.value) return
  isMuted.value = !isMuted.value
  audioRef.value.muted = isMuted.value
}

function setVolume(e: Event) {
  if (!audioRef.value) return
  const target = e.target as HTMLInputElement
  volumeLevel.value = parseFloat(target.value)
  audioRef.value.volume = volumeLevel.value
  isMuted.value = volumeLevel.value === 0
}

function seek(e: MouseEvent) {
  if (!audioRef.value || !duration.value || !progressRef.value) return
  
  const rect = progressRef.value.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  audioRef.value.currentTime = percent * duration.value
}

function skip(seconds: number) {
  if (!audioRef.value) return
  audioRef.value.currentTime = Math.max(0, Math.min(duration.value, currentTime.value + seconds))
}

function download() {
  const link = document.createElement('a')
  link.href = props.src
  link.download = props.title || 'audio'
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
  if (!audioRef.value) return
  currentTime.value = audioRef.value.currentTime
  emit('timeupdate', currentTime.value, duration.value)
  drawWaveform()
}

function handleLoadedMetadata() {
  if (!audioRef.value) return
  duration.value = audioRef.value.duration
  isLoading.value = false
  generateWaveform()
}

function handleCanPlay() {
  isLoading.value = false
}

// Watch source changes
watch(() => props.src, () => {
  isLoading.value = true
  currentTime.value = 0
  duration.value = 0
  generateWaveform()
})

// Lifecycle
onMounted(() => {
  if (props.autoplay && audioRef.value) {
    audioRef.value.play()
  }
  generateWaveform()
})
</script>

<template>
  <div class="audio-player">
    <!-- Hidden Audio Element -->
    <audio
      ref="audioRef"
      :src="src"
      :loop="loop"
      @play="handlePlay"
      @pause="handlePause"
      @ended="handleEnded"
      @timeupdate="handleTimeUpdate"
      @loadedmetadata="handleLoadedMetadata"
      @canplay="handleCanPlay"
    />

    <!-- Player Card -->
    <div class="player-card">
      <!-- Album Art / Icon -->
      <div class="album-art">
        <Music class="music-icon" />
      </div>

      <!-- Info & Controls -->
      <div class="player-content">
        <!-- Title -->
        <div class="audio-info">
          <span class="audio-title">{{ title || '音频文件' }}</span>
          <span class="audio-duration">{{ formattedDuration }}</span>
        </div>

        <!-- Waveform -->
        <div 
          ref="progressRef"
          class="waveform-container"
          @click="seek"
        >
          <canvas
            ref="waveformRef"
            class="waveform-canvas"
          />
          
          <!-- Progress Overlay -->
          <div class="progress-time">
            {{ formattedCurrentTime }}
          </div>
        </div>

        <!-- Controls -->
        <div class="player-controls">
          <div class="controls-left">
            <button
              class="ctrl-btn"
              title="后退 10s"
              @click="skip(-10)"
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
              title="前进 10s"
              @click="skip(10)"
            >
              <SkipForward class="w-4 h-4" />
            </button>
          </div>

          <div class="controls-right">
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

            <!-- Download -->
            <button
              class="ctrl-btn"
              title="下载"
              @click="download"
            >
              <Download class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.audio-player {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--any-bg-tertiary);
}

.player-card {
  display: flex;
  gap: 20px;
  max-width: 600px;
  width: 100%;
  padding: 20px;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2);
}

/* Album Art */
.album-art {
  flex-shrink: 0;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--td-state-thinking-bg), var(--any-bg-tertiary));
  border-radius: var(--any-radius-md);
}

.music-icon {
  width: 40px;
  height: 40px;
  color: var(--td-state-thinking, #00D9FF);
}

/* Content */
.player-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

/* Info */
.audio-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.audio-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.audio-duration {
  font-size: 12px;
  font-family: 'SF Mono', monospace;
  color: var(--any-text-muted);
}

/* Waveform */
.waveform-container {
  position: relative;
  height: 48px;
  cursor: pointer;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
}

.progress-time {
  position: absolute;
  bottom: -4px;
  left: 0;
  font-size: 11px;
  font-family: 'SF Mono', monospace;
  color: var(--any-text-muted);
}

/* Controls */
.player-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ctrl-btn {
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.ctrl-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.play-btn {
  padding: 10px;
  background: var(--td-state-thinking-bg);
  color: var(--td-state-thinking, #00D9FF);
  border-radius: 50%;
}

.play-btn:hover {
  background: var(--td-state-thinking);
  color: var(--any-bg-primary);
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
  background: var(--any-bg-tertiary);
  border-radius: 2px;
  cursor: pointer;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  background: var(--td-state-thinking, #00D9FF);
  border-radius: 50%;
}

/* Loading */
.audio-player.loading .waveform-canvas {
  opacity: 0.5;
}
</style>
