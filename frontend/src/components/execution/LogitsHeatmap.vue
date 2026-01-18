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
  if (prob > 0.8) return 'var(--td-state-executing)' // Green - high confidence
  if (prob > 0.5) return 'var(--td-state-thinking)' // Cyan - medium-high
  if (prob > 0.3) return 'var(--td-state-waiting)' // Amber - medium
  if (prob > 0.1) return '#FF6B6B' // Light red - low
  return 'var(--td-state-error)' // Red - very low
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
      <div
        v-if="visible"
        class="logits-backdrop"
        @click.self="emit('close')"
      >
        <div 
          class="logits-modal glass-panel-heavy"
          :style="positionStyle"
        >
          <!-- Header -->
          <div class="modal-header">
            <div class="header-title">
              <span class="title-icon">🔥</span>
              <span>Logits 解码</span>
              <span
                v-if="edgeId"
                class="edge-id"
              >Edge: {{ edgeId }}</span>
            </div>
            <div class="header-actions">
              <button
                class="zoom-btn"
                :disabled="zoomLevel <= minZoom"
                @click="zoomOut"
              >
                <MagnifyingGlassMinusIcon class="btn-icon" />
              </button>
              <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
              <button
                class="zoom-btn"
                :disabled="zoomLevel >= maxZoom"
                @click="zoomIn"
              >
                <MagnifyingGlassPlusIcon class="btn-icon" />
              </button>
              <button
                class="close-btn"
                @click="emit('close')"
              >
                <XMarkIcon class="btn-icon" />
              </button>
            </div>
          </div>

          <!-- Context -->
          <div
            v-if="contextBefore || contextAfter"
            class="context-preview"
          >
            <span class="context-before">{{ contextBefore || '...' }}</span>
            <span class="context-cursor">|</span>
            <span class="context-after">{{ contextAfter || '...' }}</span>
          </div>

          <!-- Heatmap Body -->
          <div
            class="modal-body"
            :style="{ transform: `scale(${zoomLevel})` }"
          >
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
                    <span class="prob-bar-glow" />
                  </div>
                </div>

                <!-- Probability value -->
                <div
                  class="prob-value"
                  :style="{ color: getProbabilityColor(token.probability) }"
                >
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
              <div class="legend-title">
                置信度
              </div>
              <div class="legend-gradient">
                <div class="gradient-bar" />
                <div class="gradient-labels">
                  <span>低</span>
                  <span>高</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Selected token detail -->
          <Transition name="slide-up">
            <div
              v-if="selectedToken"
              class="token-detail"
            >
              <div class="detail-header">
                <span class="detail-token">{{ selectedToken.token }}</span>
                <span
                  class="detail-badge"
                  :style="{ background: getProbabilityColor(selectedToken.probability) }"
                >
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
  background: color-mix(in srgb, var(--any-bg-primary) 60%, transparent);
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
  border-bottom: 1px solid var(--any-border);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.title-icon {
  font-size: 18px;
}

.edge-id {
  font-size: 12px;
  color: var(--any-text-muted);
  padding: 2px 8px;
  background: var(--any-bg-tertiary);
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
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.zoom-btn:hover,
.close-btn:hover {
  background: var(--any-bg-hover);
}

.zoom-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.btn-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-secondary);
}

.zoom-level {
  font-size: 12px;
  color: var(--any-text-tertiary);
  min-width: 40px;
  text-align: center;
}

/* Context preview */
.context-preview {
  padding: 12px 20px;
  background: var(--any-bg-tertiary);
  font-size: 13px;
  font-family: 'SF Mono', monospace;
  color: var(--any-text-secondary);
  border-bottom: 1px solid var(--any-border);
}

.context-before {
  color: var(--any-text-tertiary);
}

.context-cursor {
  color: var(--td-state-thinking);
  animation: cursor-blink 1s step-end infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.context-after {
  color: var(--any-text-muted);
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
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease-out;
}

.token-row:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
}

.token-row.selected {
  background: var(--td-state-thinking-bg);
  border-color: color-mix(in srgb, var(--td-state-thinking) 30%, transparent);
}

.token-row.top {
  background: var(--td-state-executing-bg);
  border-color: color-mix(in srgb, var(--td-state-executing) 30%, transparent);
}

.token-row.top .token-text {
  color: var(--td-state-executing);
}

.token-rank {
  width: 24px;
  text-align: center;
}

.rank-number {
  font-size: 12px;
  font-weight: 600;
  color: var(--any-text-muted);
}

.token-row.top .rank-number {
  color: var(--td-state-executing);
}

.token-display {
  width: 80px;
  flex-shrink: 0;
}

.token-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  font-family: 'SF Mono', monospace;
}

.prob-bar-container {
  flex: 1;
  height: 20px;
  background: var(--any-bg-tertiary);
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
  color: var(--any-text-muted);
  text-align: right;
  font-family: 'SF Mono', monospace;
}

/* Legend */
.heatmap-legend {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--any-border);
}

.legend-title {
  font-size: 11px;
  color: var(--any-text-tertiary);
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
    var(--td-state-error) 0%,
    #FF6B6B 25%,
    var(--td-state-waiting) 50%,
    var(--td-state-thinking) 75%,
    var(--td-state-executing) 100%
  );
}

.gradient-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: var(--any-text-muted);
}

/* Token detail */
.token-detail {
  padding: 16px 20px;
  background: var(--td-state-thinking-bg);
  border-top: 1px solid color-mix(in srgb, var(--td-state-thinking) 20%, transparent);
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
  color: var(--any-text-primary);
  font-family: 'SF Mono', monospace;
}

.detail-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--any-text-inverse);
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
  color: var(--any-text-tertiary);
  text-transform: uppercase;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
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
  background: var(--any-bg-tertiary);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: var(--any-border-hover);
  border-radius: 3px;
}
</style>
