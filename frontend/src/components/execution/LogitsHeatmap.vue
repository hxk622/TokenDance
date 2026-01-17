<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { XMarkIcon, MagnifyingGlassMinusIcon, MagnifyingGlassPlusIcon } from '@heroicons/vue/24/outline'

interface TokenLogit {
  token: string
  probability: number
  logit: number
  isSelected?: boolean
}

interface Props {
  visible: boolean
  edgeId?: string
  position?: { x: number; y: number }
  tokens?: TokenLogit[]
  contextBefore?: string
  contextAfter?: string
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  tokens: () => [],
  contextBefore: '',
  contextAfter: ''
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'token-select', token: TokenLogit): void
}>()

// Zoom level
const zoomLevel = ref(1)
const minZoom = 0.5
const maxZoom = 2

function zoomIn() {
  zoomLevel.value = Math.min(zoomLevel.value + 0.25, maxZoom)
}

function zoomOut() {
  zoomLevel.value = Math.max(zoomLevel.value - 0.25, minZoom)
}

// Selected token for detail view
const selectedToken = ref<TokenLogit | null>(null)

function selectToken(token: TokenLogit) {
  selectedToken.value = token
  emit('token-select', token)
}

// Get color for probability (heatmap gradient)
function getProbabilityColor(prob: number): string {
  // Gradient from cool (low prob) to hot (high prob)
  if (prob > 0.8) return 'var(--vibe-color-success)' // Green - high confidence
  if (prob > 0.5) return 'var(--vibe-color-active)' // Cyan - medium-high
  if (prob > 0.3) return 'var(--vibe-color-pending)' // Amber - medium
  if (prob > 0.1) return '#FF6B6B' // Light red - low
  return 'var(--vibe-color-error)' // Red - very low
}

// Get bar width for visualization
function getBarWidth(prob: number): string {
  return `${Math.max(prob * 100, 2)}%`
}

// Format probability as percentage
function formatProb(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`
}

// Format logit value
function formatLogit(logit: number): string {
  return logit.toFixed(3)
}

// Mock data for demo
const defaultTokens: TokenLogit[] = [
  { token: '市场', probability: 0.85, logit: 2.34, isSelected: true },
  { token: '行业', probability: 0.08, logit: 0.56 },
  { token: '领域', probability: 0.04, logit: -0.32 },
  { token: '趋势', probability: 0.02, logit: -1.15 },
  { token: '增长', probability: 0.01, logit: -2.08 },
]

const displayTokens = computed(() => props.tokens.length > 0 ? props.tokens : defaultTokens)

// Sort by probability
const sortedTokens = computed(() => {
  return [...displayTokens.value].sort((a, b) => b.probability - a.probability)
})

// Position style
const positionStyle = computed(() => {
  if (!props.position) return {}
  return {
    left: `${props.position.x}px`,
    top: `${props.position.y}px`
  }
})

// Reset on close
watch(() => props.visible, (newVal) => {
  if (!newVal) {
    selectedToken.value = null
    zoomLevel.value = 1
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="logits-backdrop" @click.self="emit('close')">
        <div 
          class="logits-modal glass-panel-heavy"
          :style="positionStyle"
        >
          <!-- Header -->
          <div class="modal-header">
            <div class="header-title">
              <span class="title-icon">🔥</span>
              <span>Logits 解码</span>
              <span v-if="edgeId" class="edge-id">Edge: {{ edgeId }}</span>
            </div>
            <div class="header-actions">
              <button class="zoom-btn" @click="zoomOut" :disabled="zoomLevel <= minZoom">
                <MagnifyingGlassMinusIcon class="btn-icon" />
              </button>
              <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
              <button class="zoom-btn" @click="zoomIn" :disabled="zoomLevel >= maxZoom">
                <MagnifyingGlassPlusIcon class="btn-icon" />
              </button>
              <button class="close-btn" @click="emit('close')">
                <XMarkIcon class="btn-icon" />
              </button>
            </div>
          </div>

          <!-- Context -->
          <div v-if="contextBefore || contextAfter" class="context-preview">
            <span class="context-before">{{ contextBefore || '...' }}</span>
            <span class="context-cursor">|</span>
            <span class="context-after">{{ contextAfter || '...' }}</span>
          </div>

          <!-- Heatmap Body -->
          <div class="modal-body" :style="{ transform: `scale(${zoomLevel})` }">
            <div class="token-list">
              <div 
                v-for="(token, index) in sortedTokens" 
                :key="token.token"
                :class="[
                  'token-row',
                  { 
                    selected: token.isSelected || selectedToken?.token === token.token,
                    top: index === 0
                  }
                ]"
                @click="selectToken(token)"
              >
                <!-- Rank -->
                <div class="token-rank">
                  <span class="rank-number">{{ index + 1 }}</span>
                </div>

                <!-- Token display -->
                <div class="token-display">
                  <span class="token-text">{{ token.token }}</span>
                </div>

                <!-- Probability bar -->
                <div class="prob-bar-container">
                  <div 
                    class="prob-bar"
                    :style="{ 
                      width: getBarWidth(token.probability),
                      background: getProbabilityColor(token.probability)
                    }"
                  >
                    <span class="prob-bar-glow"></span>
                  </div>
                </div>

                <!-- Probability value -->
                <div class="prob-value" :style="{ color: getProbabilityColor(token.probability) }">
                  {{ formatProb(token.probability) }}
                </div>

                <!-- Logit value -->
                <div class="logit-value">
                  {{ formatLogit(token.logit) }}
                </div>
              </div>
            </div>

            <!-- Legend -->
            <div class="heatmap-legend">
              <div class="legend-title">置信度</div>
              <div class="legend-gradient">
                <div class="gradient-bar"></div>
                <div class="gradient-labels">
                  <span>低</span>
                  <span>高</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Selected token detail -->
          <Transition name="slide-up">
            <div v-if="selectedToken" class="token-detail">
              <div class="detail-header">
                <span class="detail-token">{{ selectedToken.token }}</span>
                <span class="detail-badge" :style="{ background: getProbabilityColor(selectedToken.probability) }">
                  {{ formatProb(selectedToken.probability) }}
                </span>
              </div>
              <div class="detail-stats">
                <div class="stat">
                  <span class="stat-label">Logit</span>
                  <span class="stat-value">{{ formatLogit(selectedToken.logit) }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Entropy</span>
                  <span class="stat-value">{{ (-selectedToken.probability * Math.log2(selectedToken.probability)).toFixed(3) }}</span>
                </div>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.logits-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logits-modal {
  width: 480px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
}

.title-icon {
  font-size: 18px;
}

.edge-id {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-family: 'SF Mono', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-btn,
.close-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.zoom-btn:hover,
.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.zoom-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
  color: rgba(255, 255, 255, 0.7);
}

.zoom-level {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  min-width: 40px;
  text-align: center;
}

/* Context preview */
.context-preview {
  padding: 12px 20px;
  background: rgba(0, 0, 0, 0.2);
  font-size: 13px;
  font-family: 'SF Mono', monospace;
  color: rgba(255, 255, 255, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.context-before {
  color: rgba(255, 255, 255, 0.5);
}

.context-cursor {
  color: var(--vibe-color-active);
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.context-after {
  color: rgba(255, 255, 255, 0.3);
}

/* Body */
.modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  transform-origin: top center;
  transition: transform 200ms ease-out;
}

.token-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.token-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: rgba(28, 28, 30, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease-out;
}

.token-row:hover {
  background: rgba(28, 28, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.token-row.selected {
  background: rgba(0, 217, 255, 0.1);
  border-color: rgba(0, 217, 255, 0.3);
}

.token-row.top {
  background: rgba(0, 255, 136, 0.1);
  border-color: rgba(0, 255, 136, 0.3);
}

.token-row.top .token-text {
  color: var(--vibe-color-success);
}

.token-rank {
  width: 24px;
  text-align: center;
}

.rank-number {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.4);
}

.token-row.top .rank-number {
  color: var(--vibe-color-success);
}

.token-display {
  width: 80px;
  flex-shrink: 0;
}

.token-text {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  font-family: 'SF Mono', monospace;
}

.prob-bar-container {
  flex: 1;
  height: 20px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.prob-bar {
  height: 100%;
  border-radius: 4px;
  position: relative;
  transition: width 300ms ease-out;
}

.prob-bar-glow {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
  animation: bar-shimmer 2s infinite;
}

@keyframes bar-shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.prob-value {
  width: 50px;
  font-size: 13px;
  font-weight: 600;
  text-align: right;
}

.logit-value {
  width: 50px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  text-align: right;
  font-family: 'SF Mono', monospace;
}

/* Legend */
.heatmap-legend {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.legend-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
}

.legend-gradient {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.gradient-bar {
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    var(--vibe-color-error) 0%,
    #FF6B6B 25%,
    var(--vibe-color-pending) 50%,
    var(--vibe-color-active) 75%,
    var(--vibe-color-success) 100%
  );
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

/* Token detail */
.token-detail {
  padding: 16px 20px;
  background: rgba(0, 217, 255, 0.05);
  border-top: 1px solid rgba(0, 217, 255, 0.2);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.detail-token {
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  font-family: 'SF Mono', monospace;
}

.detail-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.8);
}

.detail-stats {
  display: flex;
  gap: 24px;
}

.stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  font-family: 'SF Mono', monospace;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 200ms ease-out;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .logits-modal,
.modal-leave-to .logits-modal {
  transform: scale(0.95);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 200ms ease-out;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* Scrollbar */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
</style>
