<script setup lang="ts">
/**
 * ProjectContextPanel - 展示项目上下文信息
 *
 * 显示:
 * - Decisions: 决策历史
 * - Failures: 失败记录 (Keep the Failures)
 * - Key Findings: 关键发现
 */
import { computed, ref } from 'vue'
import { useProjectStore } from '@/stores/project'
import type { Decision, Failure, Finding } from '@/types/project'
import {
  ChevronDown,
  ChevronRight,
  Lightbulb,
  AlertTriangle,
  CheckCircle2,
  Clock,
  BookOpen,
} from 'lucide-vue-next'

const projectStore = useProjectStore()

// Computed
const context = computed(() => projectStore.projectContext)
const decisions = computed(() => context.value?.decisions || [])
const failures = computed(() => context.value?.failures || [])
const findings = computed(() => context.value?.key_findings || [])

// Collapsed state
const collapsedSections = ref({
  decisions: false,
  failures: false,
  findings: false,
})

function toggleSection(section: 'decisions' | 'failures' | 'findings') {
  collapsedSections.value[section] = !collapsedSections.value[section]
}

// Format time
function formatTime(timestamp: string) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

// Check if context is empty
const isEmpty = computed(() =>
  decisions.value.length === 0 &&
  failures.value.length === 0 &&
  findings.value.length === 0
)
</script>

<template>
  <div class="context-panel">
    <div class="panel-header">
      <BookOpen class="header-icon" />
      <span class="header-title">项目上下文</span>
    </div>

    <!-- Empty State -->
    <div
      v-if="isEmpty"
      class="empty-state"
    >
      <Lightbulb class="empty-icon" />
      <p>暂无上下文信息</p>
      <span class="empty-hint">AI 在执行过程中会自动记录决策、发现和失败</span>
    </div>

    <div
      v-else
      class="context-content"
    >
      <!-- Decisions Section -->
      <div
        v-if="decisions.length > 0"
        class="context-section"
      >
        <button
          class="section-header"
          @click="toggleSection('decisions')"
        >
          <component
            :is="collapsedSections.decisions ? ChevronRight : ChevronDown"
            class="chevron"
          />
          <CheckCircle2 class="section-icon decisions-icon" />
          <span class="section-title">决策记录</span>
          <span class="section-count">{{ decisions.length }}</span>
        </button>

        <div
          v-if="!collapsedSections.decisions"
          class="section-content"
        >
          <div
            v-for="(decision, index) in decisions"
            :key="index"
            class="context-item decision-item"
          >
            <div class="item-content">
              {{ decision.decision }}
            </div>
            <div
              v-if="decision.reason"
              class="item-reason"
            >
              {{ decision.reason }}
            </div>
            <div class="item-meta">
              <Clock class="meta-icon" />
              <span>{{ formatTime(decision.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Failures Section (Keep the Failures) -->
      <div
        v-if="failures.length > 0"
        class="context-section"
      >
        <button
          class="section-header"
          @click="toggleSection('failures')"
        >
          <component
            :is="collapsedSections.failures ? ChevronRight : ChevronDown"
            class="chevron"
          />
          <AlertTriangle class="section-icon failures-icon" />
          <span class="section-title">失败记录</span>
          <span class="section-count warning">{{ failures.length }}</span>
        </button>

        <div
          v-if="!collapsedSections.failures"
          class="section-content"
        >
          <div
            v-for="(failure, index) in failures"
            :key="index"
            class="context-item failure-item"
          >
            <div class="item-type">
              {{ failure.type }}
            </div>
            <div class="item-content">
              {{ failure.message }}
            </div>
            <div
              v-if="failure.learning"
              class="item-learning"
            >
              <Lightbulb class="learning-icon" />
              {{ failure.learning }}
            </div>
            <div class="item-meta">
              <Clock class="meta-icon" />
              <span>{{ formatTime(failure.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Findings Section -->
      <div
        v-if="findings.length > 0"
        class="context-section"
      >
        <button
          class="section-header"
          @click="toggleSection('findings')"
        >
          <component
            :is="collapsedSections.findings ? ChevronRight : ChevronDown"
            class="chevron"
          />
          <Lightbulb class="section-icon findings-icon" />
          <span class="section-title">关键发现</span>
          <span class="section-count">{{ findings.length }}</span>
        </button>

        <div
          v-if="!collapsedSections.findings"
          class="section-content"
        >
          <div
            v-for="(finding, index) in findings"
            :key="index"
            class="context-item finding-item"
          >
            <div class="item-content">
              {{ finding.finding }}
            </div>
            <div
              v-if="finding.source"
              class="item-source"
            >
              来源: {{ finding.source }}
            </div>
            <div class="item-meta">
              <Clock class="meta-icon" />
              <span>{{ formatTime(finding.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.context-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--any-bg-secondary);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-icon {
  width: 18px;
  height: 18px;
  color: var(--exec-accent);
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--any-text-tertiary);
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 14px;
  color: var(--any-text-secondary);
  margin-bottom: 8px;
}

.empty-hint {
  font-size: 12px;
  color: var(--any-text-tertiary);
}

/* Content */
.context-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* Section */
.context-section {
  margin-bottom: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: var(--any-radius-md);
  background: var(--any-bg-tertiary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.section-header:hover {
  background: var(--any-bg-hover);
}

.chevron {
  width: 14px;
  height: 14px;
  color: var(--any-text-tertiary);
}

.section-icon {
  width: 16px;
  height: 16px;
}

.decisions-icon {
  color: var(--exec-success);
}

.failures-icon {
  color: var(--exec-warning);
}

.findings-icon {
  color: var(--exec-accent);
}

.section-title {
  flex: 1;
  text-align: left;
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.section-count {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: var(--any-radius-sm);
  background: var(--any-bg-primary);
  color: var(--any-text-secondary);
}

.section-count.warning {
  background: rgba(255, 184, 0, 0.15);
  color: var(--exec-warning);
}

/* Section Content */
.section-content {
  padding: 8px 0 0 28px;
}

/* Context Item */
.context-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: var(--any-radius-md);
  background: var(--any-bg-primary);
  border-left: 3px solid transparent;
}

.decision-item {
  border-left-color: var(--exec-success);
}

.failure-item {
  border-left-color: var(--exec-warning);
}

.finding-item {
  border-left-color: var(--exec-accent);
}

.item-type {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--exec-warning);
  margin-bottom: 4px;
}

.item-content {
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.5;
}

.item-reason,
.item-source {
  font-size: 12px;
  color: var(--any-text-secondary);
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed var(--any-border);
}

.item-learning {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  color: var(--exec-accent);
  margin-top: 8px;
  padding: 8px;
  border-radius: var(--any-radius-sm);
  background: rgba(0, 217, 255, 0.08);
}

.learning-icon {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  margin-top: 1px;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--any-text-tertiary);
  margin-top: 8px;
}

.meta-icon {
  width: 12px;
  height: 12px;
}
</style>
