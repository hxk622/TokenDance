<script setup lang="ts">
/**
 * ProjectContextBar - Display project context (decisions, failures, findings)
 *
 * Implements "Keep the Failures" principle - failures are visible
 * across all conversations to prevent repeating mistakes.
 */
import { ref, computed } from 'vue'
import { useProjectStore } from '@/stores/project'
import type { Project } from '@/types/project'
import {
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Plus,
  Target,
} from 'lucide-vue-next'

const props = defineProps<{
  project: Project | null
}>()

const projectStore = useProjectStore()

// Expand/collapse state
const isExpanded = ref(false)
const expandedSection = ref<'decisions' | 'failures' | 'findings' | null>(null)

// Get context from store
const context = computed(() => projectStore.projectContext)

// Counts
const decisionsCount = computed(() => context.value?.decisions?.length || 0)
const failuresCount = computed(() => context.value?.failures?.length || 0)
const findingsCount = computed(() => context.value?.key_findings?.length || 0)

// Toggle main expand
function toggleExpand() {
  isExpanded.value = !isExpanded.value
  if (!isExpanded.value) {
    expandedSection.value = null
  }
}

// Toggle section
function toggleSection(section: 'decisions' | 'failures' | 'findings') {
  if (expandedSection.value === section) {
    expandedSection.value = null
  } else {
    expandedSection.value = section
    isExpanded.value = true
  }
}

// Format timestamp
function formatTime(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div
    v-if="project"
    class="context-bar"
    :class="{ expanded: isExpanded }"
  >
    <!-- Header -->
    <div
      class="context-header"
      @click="toggleExpand"
    >
      <div class="header-left">
        <Target class="context-icon" />
        <span class="context-title">项目上下文</span>
      </div>

      <div class="header-stats">
        <!-- Decisions count -->
        <button
          class="stat-badge decisions"
          :class="{ active: expandedSection === 'decisions' }"
          @click.stop="toggleSection('decisions')"
        >
          <CheckCircle2 class="stat-icon" />
          <span>{{ decisionsCount }}</span>
        </button>

        <!-- Failures count (highlighted if any) -->
        <button
          class="stat-badge failures"
          :class="{
            active: expandedSection === 'failures',
            'has-items': failuresCount > 0,
          }"
          @click.stop="toggleSection('failures')"
        >
          <XCircle class="stat-icon" />
          <span>{{ failuresCount }}</span>
        </button>

        <!-- Findings count -->
        <button
          class="stat-badge findings"
          :class="{ active: expandedSection === 'findings' }"
          @click.stop="toggleSection('findings')"
        >
          <Lightbulb class="stat-icon" />
          <span>{{ findingsCount }}</span>
        </button>

        <!-- Expand toggle -->
        <component
          :is="isExpanded ? ChevronUp : ChevronDown"
          class="expand-icon"
        />
      </div>
    </div>

    <!-- Intent (always visible when expanded) -->
    <div
      v-if="isExpanded && project.intent"
      class="context-intent"
    >
      <span class="intent-label">意图</span>
      <p class="intent-text">
        {{ project.intent }}
      </p>
    </div>

    <!-- Expanded sections -->
    <Transition name="slide">
      <div
        v-if="isExpanded"
        class="context-body"
      >
        <!-- Decisions section -->
        <div
          v-if="expandedSection === 'decisions' || expandedSection === null"
          class="context-section"
        >
          <div
            class="section-header"
            @click="toggleSection('decisions')"
          >
            <CheckCircle2 class="section-icon decisions" />
            <span>决策记录</span>
            <span class="section-count">{{ decisionsCount }}</span>
          </div>

          <div
            v-if="expandedSection === 'decisions'"
            class="section-content"
          >
            <div
              v-if="!context?.decisions?.length"
              class="empty-message"
            >
              暂无决策记录
            </div>
            <div
              v-for="(decision, idx) in context?.decisions"
              :key="idx"
              class="context-item"
            >
              <p class="item-text">
                {{ decision.decision }}
              </p>
              <p
                v-if="decision.reason"
                class="item-reason"
              >
                {{ decision.reason }}
              </p>
              <span class="item-time">{{ formatTime(decision.timestamp) }}</span>
            </div>
          </div>
        </div>

        <!-- Failures section (Keep the Failures) -->
        <div
          v-if="expandedSection === 'failures' || expandedSection === null"
          class="context-section failures"
        >
          <div
            class="section-header"
            @click="toggleSection('failures')"
          >
            <XCircle class="section-icon failures" />
            <span>失败记录</span>
            <span class="section-count">{{ failuresCount }}</span>
          </div>

          <div
            v-if="expandedSection === 'failures'"
            class="section-content"
          >
            <div
              v-if="!context?.failures?.length"
              class="empty-message"
            >
              暂无失败记录 (这是好事!)
            </div>
            <div
              v-for="(failure, idx) in context?.failures"
              :key="idx"
              class="context-item failure"
            >
              <div class="failure-type">
                {{ failure.type }}
              </div>
              <p class="item-text">
                {{ failure.message }}
              </p>
              <p
                v-if="failure.learning"
                class="item-learning"
              >
                💡 {{ failure.learning }}
              </p>
              <span class="item-time">{{ formatTime(failure.timestamp) }}</span>
            </div>
          </div>
        </div>

        <!-- Findings section -->
        <div
          v-if="expandedSection === 'findings' || expandedSection === null"
          class="context-section"
        >
          <div
            class="section-header"
            @click="toggleSection('findings')"
          >
            <Lightbulb class="section-icon findings" />
            <span>关键发现</span>
            <span class="section-count">{{ findingsCount }}</span>
          </div>

          <div
            v-if="expandedSection === 'findings'"
            class="section-content"
          >
            <div
              v-if="!context?.key_findings?.length"
              class="empty-message"
            >
              暂无关键发现
            </div>
            <div
              v-for="(finding, idx) in context?.key_findings"
              :key="idx"
              class="context-item"
            >
              <p class="item-text">
                {{ finding.finding }}
              </p>
              <p
                v-if="finding.source"
                class="item-source"
              >
                来源: {{ finding.source }}
              </p>
              <span class="item-time">{{ formatTime(finding.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.context-bar {
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
  transition: all var(--any-duration-normal) var(--any-ease-default);
}

.context-bar.expanded {
  background: var(--any-bg-primary);
}

/* Header */
.context-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background var(--any-duration-fast) var(--any-ease-default);
}

.context-header:hover {
  background: var(--any-bg-tertiary);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.context-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-secondary);
}

.context-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border: none;
  border-radius: var(--any-radius-sm);
  background: transparent;
  color: var(--any-text-tertiary);
  font-size: 12px;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-default);
}

.stat-badge:hover,
.stat-badge.active {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.stat-badge.failures.has-items {
  color: var(--any-error);
  background: rgba(239, 68, 68, 0.1);
}

.stat-icon {
  width: 14px;
  height: 14px;
}

.expand-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-tertiary);
}

/* Intent */
.context-intent {
  padding: 12px 16px;
  border-bottom: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.intent-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--any-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.intent-text {
  margin-top: 4px;
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.4;
}

/* Body */
.context-body {
  padding: 8px 0;
}

/* Section */
.context-section {
  margin: 0 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: background var(--any-duration-fast) var(--any-ease-default);
}

.section-header:hover {
  background: var(--any-bg-tertiary);
}

.section-icon {
  width: 14px;
  height: 14px;
}

.section-icon.decisions {
  color: var(--exec-success);
}

.section-icon.failures {
  color: var(--any-error);
}

.section-icon.findings {
  color: var(--exec-warning);
}

.section-header span {
  font-size: 13px;
  color: var(--any-text-primary);
}

.section-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--any-text-tertiary);
}

/* Content */
.section-content {
  padding: 8px 12px;
}

.empty-message {
  font-size: 12px;
  color: var(--any-text-tertiary);
  font-style: italic;
  padding: 8px 0;
}

.context-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: var(--any-bg-secondary);
  border-radius: var(--any-radius-md);
  border-left: 3px solid var(--any-border);
}

.context-item.failure {
  border-left-color: var(--any-error);
  background: rgba(239, 68, 68, 0.05);
}

.failure-type {
  font-size: 11px;
  font-weight: 600;
  color: var(--any-error);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.item-text {
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.4;
  margin: 0;
}

.item-reason,
.item-learning,
.item-source {
  font-size: 12px;
  color: var(--any-text-secondary);
  margin-top: 6px;
  margin-bottom: 0;
}

.item-learning {
  color: var(--exec-warning);
}

.item-time {
  display: block;
  font-size: 11px;
  color: var(--any-text-tertiary);
  margin-top: 6px;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
