<script setup lang="ts">
/**
 * ReasoningTimeline - AI 推理过程时间线
 * 
 * 展示 AI 在研究过程中的决策过程，提高透明度和用户信任。
 * 包含：
 * - 决策点列表
 * - 每个决策的推理说明
 * - 备选方案展示
 * - 用户反馈按钮
 */
import { ref, computed, watch } from 'vue'
import {
  ChevronDown,
  ChevronUp,
  Brain,
  Search,
  BookOpen,
  CheckCircle,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Lightbulb,
} from 'lucide-vue-next'

// Types
interface ReasoningEvidence {
  source: string
  content: string
}

interface ReasoningAlternative {
  description: string
  reason: string
}

interface ReasoningTrace {
  id: string
  timestamp: string
  phase: string
  action: string
  reasoning: string
  confidence: number
  alternatives: ReasoningAlternative[]
  evidence: ReasoningEvidence[]
  metadata?: Record<string, any>
}

// Props
const props = withDefaults(defineProps<{
  traces: ReasoningTrace[]
  collapsed?: boolean
  maxVisible?: number
}>(), {
  collapsed: true,
  maxVisible: 5,
})

// Emits
const emit = defineEmits<{
  (e: 'feedback', traceId: string, feedback: 'positive' | 'negative'): void
  (e: 'toggle-collapse'): void
}>()

// State
const isCollapsed = ref(props.collapsed)
const expandedTraceId = ref<string | null>(null)
const feedbackGiven = ref<Record<string, string>>({})

// Watch for prop changes
watch(() => props.collapsed, (val) => {
  isCollapsed.value = val
})

// Computed
const visibleTraces = computed(() => {
  if (isCollapsed.value) {
    return props.traces.slice(-1) // 折叠时只显示最新一条
  }
  return props.traces.slice(-props.maxVisible).reverse()
})

const hasMoreTraces = computed(() => {
  return props.traces.length > props.maxVisible
})

// Methods
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
  emit('toggle-collapse')
}

const toggleTraceDetail = (traceId: string) => {
  if (expandedTraceId.value === traceId) {
    expandedTraceId.value = null
  } else {
    expandedTraceId.value = traceId
  }
}

const handleFeedback = (traceId: string, feedback: 'positive' | 'negative') => {
  feedbackGiven.value[traceId] = feedback
  emit('feedback', traceId, feedback)
}

const getPhaseIcon = (phase: string) => {
  switch (phase) {
    case 'planning': return Lightbulb
    case 'searching': return Search
    case 'reading': return BookOpen
    case 'analyzing': return Brain
    case 'verifying': return CheckCircle
    case 'synthesizing': return Brain
    default: return Brain
  }
}

const getPhaseLabel = (phase: string) => {
  const labels: Record<string, string> = {
    planning: '规划',
    searching: '搜索',
    reading: '阅读',
    analyzing: '分析',
    verifying: '验证',
    synthesizing: '综合',
  }
  return labels[phase] || phase
}

const getActionLabel = (action: string) => {
  const labels: Record<string, string> = {
    expand_query: '扩展搜索词',
    select_source: '选择来源',
    skip_source: '跳过来源',
    deep_dive: '深入研究',
    cross_verify: '交叉验证',
    detect_contradiction: '检测矛盾',
    conclude: '得出结论',
    adjust_depth: '调整深度',
  }
  return labels[action] || action
}

const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'text-green-500'
  if (confidence >= 0.6) return 'text-amber-500'
  return 'text-red-500'
}
</script>

<template>
  <div class="reasoning-timeline">
    <!-- Header -->
    <div 
      class="timeline-header"
      @click="toggleCollapse"
    >
      <div class="flex items-center gap-2">
        <Brain class="w-4 h-4 text-[var(--exec-accent)]" />
        <span class="header-title">AI 思考过程</span>
        <span 
          v-if="traces.length > 0"
          class="trace-count"
        >
          {{ traces.length }}
        </span>
      </div>
      
      <button class="collapse-btn">
        <ChevronUp
          v-if="!isCollapsed"
          class="w-4 h-4"
        />
        <ChevronDown
          v-else
          class="w-4 h-4"
        />
      </button>
    </div>

    <!-- Content -->
    <div 
      v-show="!isCollapsed || traces.length > 0"
      class="timeline-content"
    >
      <!-- Empty State -->
      <div 
        v-if="traces.length === 0"
        class="empty-state"
      >
        <Brain class="w-8 h-8 text-[var(--any-text-muted)]" />
        <p>研究尚未开始，AI 思考过程将在这里显示</p>
      </div>

      <!-- Trace List -->
      <div 
        v-else
        class="trace-list"
      >
        <div
          v-for="trace in visibleTraces"
          :key="trace.id"
          class="trace-item"
          :class="{ 'trace-item--expanded': expandedTraceId === trace.id }"
        >
          <!-- Trace Header -->
          <div 
            class="trace-header"
            @click="toggleTraceDetail(trace.id)"
          >
            <div class="trace-icon">
              <component 
                :is="getPhaseIcon(trace.phase)" 
                class="w-4 h-4"
              />
            </div>
            
            <div class="trace-main">
              <div class="trace-meta">
                <span class="trace-time">{{ formatTime(trace.timestamp) }}</span>
                <span class="trace-phase">{{ getPhaseLabel(trace.phase) }}</span>
                <span class="trace-action">{{ getActionLabel(trace.action) }}</span>
              </div>
              <p class="trace-reasoning">
                {{ trace.reasoning }}
              </p>
            </div>

            <div
              class="trace-confidence"
              :class="getConfidenceColor(trace.confidence)"
            >
              {{ Math.round(trace.confidence * 100) }}%
            </div>
          </div>

          <!-- Trace Details (Expanded) -->
          <div 
            v-if="expandedTraceId === trace.id"
            class="trace-details"
          >
            <!-- Alternatives -->
            <div 
              v-if="trace.alternatives && trace.alternatives.length > 0"
              class="detail-section"
            >
              <h5 class="detail-title">
                <AlertTriangle class="w-3.5 h-3.5" />
                放弃的方案
              </h5>
              <ul class="alternatives-list">
                <li 
                  v-for="(alt, idx) in trace.alternatives"
                  :key="idx"
                  class="alternative-item"
                >
                  <span class="alt-desc">{{ alt.description }}</span>
                  <span class="alt-reason">{{ alt.reason }}</span>
                </li>
              </ul>
            </div>

            <!-- Evidence -->
            <div 
              v-if="trace.evidence && trace.evidence.length > 0"
              class="detail-section"
            >
              <h5 class="detail-title">
                <CheckCircle class="w-3.5 h-3.5" />
                支撑证据
              </h5>
              <ul class="evidence-list">
                <li 
                  v-for="(ev, idx) in trace.evidence"
                  :key="idx"
                  class="evidence-item"
                >
                  <span class="ev-source">{{ ev.source }}</span>
                  <span class="ev-content">{{ ev.content }}</span>
                </li>
              </ul>
            </div>

            <!-- Feedback -->
            <div class="feedback-section">
              <span class="feedback-label">这个决策有帮助吗？</span>
              <div class="feedback-buttons">
                <button
                  class="feedback-btn"
                  :class="{ 'feedback-btn--active': feedbackGiven[trace.id] === 'positive' }"
                  :disabled="!!feedbackGiven[trace.id]"
                  @click.stop="handleFeedback(trace.id, 'positive')"
                >
                  <ThumbsUp class="w-4 h-4" />
                </button>
                <button
                  class="feedback-btn"
                  :class="{ 'feedback-btn--active': feedbackGiven[trace.id] === 'negative' }"
                  :disabled="!!feedbackGiven[trace.id]"
                  @click.stop="handleFeedback(trace.id, 'negative')"
                >
                  <ThumbsDown class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Show More -->
        <div 
          v-if="hasMoreTraces && !isCollapsed"
          class="show-more"
        >
          还有 {{ traces.length - maxVisible }} 条思考记录
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.reasoning-timeline {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.timeline-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background var(--any-duration-fast) var(--any-ease-out);
}

.timeline-header:hover {
  background: var(--any-bg-hover);
}

.header-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-secondary);
}

.trace-count {
  font-size: 11px;
  padding: 2px 6px;
  background: var(--exec-accent);
  color: var(--any-bg-primary);
  border-radius: var(--any-radius-full);
}

.collapse-btn {
  padding: 4px;
  color: var(--any-text-tertiary);
  border-radius: var(--any-radius-sm);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.collapse-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.timeline-content {
  padding: 0 16px 16px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px;
  text-align: center;
  color: var(--any-text-muted);
  font-size: 13px;
}

.trace-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.trace-item {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  overflow: hidden;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.trace-item:hover {
  border-color: var(--any-border-hover);
}

.trace-item--expanded {
  border-color: var(--exec-accent);
}

.trace-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  cursor: pointer;
}

.trace-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
  color: var(--exec-accent);
}

.trace-main {
  flex: 1;
  min-width: 0;
}

.trace-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.trace-time {
  font-size: 11px;
  color: var(--any-text-muted);
}

.trace-phase,
.trace-action {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: var(--any-radius-sm);
}

.trace-phase {
  background: color-mix(in srgb, var(--exec-accent) 15%, transparent);
  color: var(--exec-accent);
}

.trace-action {
  background: var(--any-bg-tertiary);
  color: var(--any-text-secondary);
}

.trace-reasoning {
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.5;
  margin: 0;
}

.trace-confidence {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
}

.trace-details {
  padding: 12px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-primary);
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--any-text-secondary);
  margin: 0 0 8px 0;
}

.alternatives-list,
.evidence-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.alternative-item,
.evidence-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-sm);
}

.alt-desc,
.ev-source {
  font-size: 12px;
  color: var(--any-text-primary);
}

.alt-reason,
.ev-content {
  font-size: 11px;
  color: var(--any-text-muted);
}

.feedback-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--any-border);
}

.feedback-label {
  font-size: 12px;
  color: var(--any-text-muted);
}

.feedback-buttons {
  display: flex;
  gap: 8px;
}

.feedback-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  color: var(--any-text-tertiary);
  background: var(--any-bg-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.feedback-btn:hover:not(:disabled) {
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

.feedback-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.feedback-btn--active {
  background: var(--exec-accent);
  border-color: var(--exec-accent);
  color: var(--any-bg-primary);
}

.show-more {
  text-align: center;
  font-size: 12px;
  color: var(--any-text-muted);
  padding: 8px;
}
</style>
