<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  ChevronDownIcon, 
  ChevronRightIcon,
  LightBulbIcon,
  CpuChipIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

interface ThinkingStep {
  id: string
  type: 'observation' | 'reasoning' | 'conclusion' | 'action'
  content: string
  timestamp: number
  duration?: number
  isExpanded?: boolean
  keywords?: string[]
  confidence?: number
}

interface Props {
  steps?: ThinkingStep[]
  isStreaming?: boolean
  highlightKeywords?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  steps: () => [],
  isStreaming: false,
  highlightKeywords: true
})

const emit = defineEmits<{
  (e: 'step-click', stepId: string): void
  (e: 'keyword-click', keyword: string): void
}>()

// Local state for expansion
const expandedSteps = ref<Set<string>>(new Set())

// Toggle step expansion
function toggleStep(stepId: string) {
  if (expandedSteps.value.has(stepId)) {
    expandedSteps.value.delete(stepId)
  } else {
    expandedSteps.value.add(stepId)
  }
}

// Check if step is expanded
function isExpanded(stepId: string): boolean {
  return expandedSteps.value.has(stepId)
}

// Get icon for step type
function getStepIcon(type: ThinkingStep['type']) {
  switch (type) {
    case 'observation': return LightBulbIcon
    case 'reasoning': return CpuChipIcon
    case 'conclusion': return CheckCircleIcon
    case 'action': return ExclamationTriangleIcon
    default: return CpuChipIcon
  }
}

// Get color for step type
function getStepColor(type: ThinkingStep['type']): string {
  switch (type) {
    case 'observation': return 'var(--vibe-color-pending)'
    case 'reasoning': return 'var(--vibe-color-active)'
    case 'conclusion': return 'var(--vibe-color-success)'
    case 'action': return 'var(--vibe-color-error)'
    default: return 'var(--vibe-color-active)'
  }
}

// Get step type label
function getStepLabel(type: ThinkingStep['type']): string {
  switch (type) {
    case 'observation': return '观察'
    case 'reasoning': return '推理'
    case 'conclusion': return '结论'
    case 'action': return '行动'
    default: return '思考'
  }
}

// Highlight keywords in content
function highlightContent(content: string, keywords?: string[]): string {
  if (!props.highlightKeywords || !keywords?.length) return content
  
  let result = content
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${keyword})`, 'gi')
    result = result.replace(regex, '<mark class="keyword-highlight">$1</mark>')
  })
  return result
}

// Format duration
function formatDuration(ms?: number): string {
  if (!ms) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

// Computed: current step (last one if streaming)
const currentStepIndex = computed(() => {
  if (!props.isStreaming) return -1
  return props.steps.length - 1
})

// Default mock data for demo
const defaultSteps: ThinkingStep[] = [
  {
    id: '1',
    type: 'observation',
    content: '用户请求分析 AI Agent 市场趋势。需要收集多源数据并进行深度分析。',
    timestamp: Date.now() - 60000,
    duration: 1200,
    keywords: ['AI Agent', '市场趋势', '深度分析']
  },
  {
    id: '2',
    type: 'reasoning',
    content: '基于当前搜索结果，AI Agent 市场呈现以下特征：1) 2024年市场规模约50亿美元；2) 主要玩家包括 OpenAI、Anthropic、Google；3) 应用场景集中在客服、编程辅助、内容生成。',
    timestamp: Date.now() - 45000,
    duration: 3500,
    keywords: ['市场规模', 'OpenAI', 'Anthropic', '应用场景'],
    confidence: 0.85
  },
  {
    id: '3',
    type: 'reasoning',
    content: '进一步分析竞争格局：Manus 专注全自动任务执行，Coworker 强调本地文件操控，GenSpark 主打深度研究。TokenDance 的差异化在于 Vibe Workflow 的氛围感体验。',
    timestamp: Date.now() - 30000,
    duration: 2800,
    keywords: ['Manus', 'Coworker', 'GenSpark', 'Vibe Workflow'],
    confidence: 0.92
  },
  {
    id: '4',
    type: 'conclusion',
    content: '综合以上分析，建议报告聚焦：1) 市场规模与增长预测；2) 主要玩家对比；3) TokenDance 差异化定位；4) 未来趋势展望。',
    timestamp: Date.now() - 15000,
    duration: 1500,
    keywords: ['市场规模', '差异化定位', '趋势展望'],
    confidence: 0.88
  }
]

const displaySteps = computed(() => props.steps.length > 0 ? props.steps : defaultSteps)
</script>

<template>
  <div class="thinking-chain glass-panel-light">
    <div class="chain-header">
      <div class="header-title">
        <CpuChipIcon class="header-icon" />
        <span>推理过程</span>
      </div>
      <div class="header-meta">
        <span class="step-count">{{ displaySteps.length }} 步</span>
        <span
          v-if="isStreaming"
          class="streaming-badge"
        >
          <span class="streaming-dot" />
          思考中...
        </span>
      </div>
    </div>

    <div class="chain-timeline">
      <div 
        v-for="(step, index) in displaySteps" 
        :key="step.id"
        :class="[
          'timeline-step',
          step.type,
          { 
            expanded: isExpanded(step.id),
            current: index === currentStepIndex && isStreaming
          }
        ]"
      >
        <!-- Timeline connector -->
        <div class="timeline-connector">
          <div
            class="connector-line"
            :class="{ last: index === displaySteps.length - 1 }"
          />
          <div 
            class="connector-dot"
            :style="{ background: getStepColor(step.type) }"
          >
            <component
              :is="getStepIcon(step.type)"
              class="dot-icon"
            />
          </div>
        </div>

        <!-- Step content -->
        <div
          class="step-content"
          @click="toggleStep(step.id)"
        >
          <div class="step-header">
            <div class="step-meta">
              <span
                class="step-type"
                :style="{ color: getStepColor(step.type) }"
              >
                {{ getStepLabel(step.type) }}
              </span>
              <span
                v-if="step.duration"
                class="step-duration"
              >
                {{ formatDuration(step.duration) }}
              </span>
              <span
                v-if="step.confidence"
                class="step-confidence"
              >
                {{ Math.round(step.confidence * 100) }}%
              </span>
            </div>
            <button class="expand-btn">
              <ChevronDownIcon
                v-if="isExpanded(step.id)"
                class="expand-icon"
              />
              <ChevronRightIcon
                v-else
                class="expand-icon"
              />
            </button>
          </div>

          <!-- Collapsed preview -->
          <div
            v-if="!isExpanded(step.id)"
            class="step-preview"
          >
            {{ step.content.slice(0, 80) }}{{ step.content.length > 80 ? '...' : '' }}
          </div>

          <!-- Expanded content -->
          <Transition name="expand">
            <div
              v-if="isExpanded(step.id)"
              class="step-expanded"
            >
              <div 
                class="step-text"
                v-html="highlightContent(step.content, step.keywords)"
              />
              
              <!-- Keywords -->
              <div
                v-if="step.keywords?.length"
                class="step-keywords"
              >
                <span 
                  v-for="keyword in step.keywords" 
                  :key="keyword"
                  class="keyword-tag"
                  @click.stop="emit('keyword-click', keyword)"
                >
                  {{ keyword }}
                </span>
              </div>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <!-- Streaming indicator -->
    <div
      v-if="isStreaming"
      class="streaming-indicator"
    >
      <div class="streaming-dots">
        <span />
        <span />
        <span />
      </div>
    </div>
  </div>
</template>

<style scoped>
.thinking-chain {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.chain-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}

.header-icon {
  width: 18px;
  height: 18px;
  color: var(--vibe-color-active);
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.streaming-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(0, 217, 255, 0.15);
  border-radius: 12px;
  font-size: 12px;
  color: var(--vibe-color-active);
}

.streaming-dot {
  width: 6px;
  height: 6px;
  background: var(--vibe-color-active);
  border-radius: 50%;
  animation: vibe-pulse-breath 1s ease-in-out infinite;
}

/* Timeline */
.chain-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-step {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.timeline-step.current .connector-dot {
  animation: vibe-pulse-breath 1.5s ease-in-out infinite;
}

/* Timeline connector */
.timeline-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.connector-line {
  width: 2px;
  flex: 1;
  background: rgba(255, 255, 255, 0.1);
  margin-top: 4px;
}

.connector-line.last {
  background: transparent;
}

.connector-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 8px currentColor;
}

.dot-icon {
  width: 12px;
  height: 12px;
  color: rgba(0, 0, 0, 0.8);
}

/* Step content */
.step-content {
  flex: 1;
  padding: 12px;
  background: rgba(28, 28, 30, 0.5);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 150ms ease-out;
}

.step-content:hover {
  background: rgba(28, 28, 30, 0.7);
  border-color: rgba(255, 255, 255, 0.1);
}

.timeline-step.expanded .step-content {
  background: rgba(28, 28, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.1);
}

.step-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-type {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.step-duration {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  padding: 2px 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.step-confidence {
  font-size: 11px;
  color: var(--vibe-color-success);
  padding: 2px 6px;
  background: rgba(0, 255, 136, 0.1);
  border-radius: 4px;
}

.expand-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 120ms ease-out;
}

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.expand-icon {
  width: 14px;
  height: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.step-preview {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.step-expanded {
  overflow: hidden;
}

.step-text {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  white-space: pre-wrap;
}

.step-text :deep(.keyword-highlight) {
  background: rgba(0, 217, 255, 0.2);
  color: var(--vibe-color-active);
  padding: 1px 4px;
  border-radius: 3px;
}

.step-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.keyword-tag {
  padding: 4px 10px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  transition: all 120ms ease-out;
}

.keyword-tag:hover {
  background: rgba(0, 217, 255, 0.2);
  color: var(--vibe-color-active);
}

/* Streaming indicator */
.streaming-indicator {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.streaming-dots {
  display: flex;
  gap: 6px;
}

.streaming-dots span {
  width: 8px;
  height: 8px;
  background: var(--vibe-color-active);
  border-radius: 50%;
  animation: streaming-bounce 1.4s ease-in-out infinite;
}

.streaming-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.streaming-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes streaming-bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 200ms ease-out;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* Scrollbar */
.thinking-chain::-webkit-scrollbar {
  width: 6px;
}

.thinking-chain::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.thinking-chain::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
</style>
