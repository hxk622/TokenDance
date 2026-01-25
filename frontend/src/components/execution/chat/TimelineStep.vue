<script setup lang="ts">
/**
 * TimelineStep - 单个 Timeline 步骤
 * 
 * 对标 AnyGen 的 Timeline.Item:
 * - 左侧状态圆点 (done: 黑色打勾, running: 动画, pending: 灰色)
 * - 垂直连线
 * - 可折叠内容
 * - 右侧来源 favicon 组
 */
import { computed } from 'vue'
import { Search, FileText, PenTool, Wrench, BookOpen, ListChecks, Check, ChevronDown, ClipboardCopy } from 'lucide-vue-next'
import SourceGroup from './SourceGroup.vue'
import type { ExecutionStep, StepIconType, Source, StepChild } from './types'

interface Props {
  step: ExecutionStep
  /** 是否是最后一个步骤 (控制连线显示) */
  isLast?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLast: false
})

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'source-click': [source: Source]
}>()

// Icon component mapping for steps
const iconMap: Record<StepIconType, any> = {
  search: Search,
  analyze: FileText,
  write: PenTool,
  tool: Wrench,
  read: BookOpen,
  plan: ListChecks
}

// Icon mapping for child types
const childIconMap: Record<StepChild['type'], any> = {
  search: Search,
  read: BookOpen,
  analyze: FileText,
  extract: ClipboardCopy
}

const IconComponent = computed(() => iconMap[props.step.icon] || Wrench)

const isRunning = computed(() => props.step.status === 'running')
const isDone = computed(() => props.step.status === 'done')
const isFailed = computed(() => props.step.status === 'failed')

function toggleCollapse() {
  emit('update:collapsed', !props.step.collapsed)
}

function handleSourceClick(source: Source) {
  emit('source-click', source)
}
</script>

<template>
  <div
    :class="[
      'timeline-step',
      `status-${step.status}`,
      { 'is-last': isLast }
    ]"
  >
    <!-- Bullet with status -->
    <div class="step-bullet">
      <!-- Done: checkmark -->
      <div
        v-if="isDone"
        class="bullet-inner done"
      >
        <Check class="check-icon" />
      </div>
      <!-- Running: animated dot -->
      <div
        v-else-if="isRunning"
        class="bullet-inner running"
      />
      <!-- Failed: red dot -->
      <div
        v-else-if="isFailed"
        class="bullet-inner failed"
      />
      <!-- Pending: gray dot -->
      <div
        v-else
        class="bullet-inner pending"
      />
    </div>

    <!-- Vertical line (hidden for last item) -->
    <div
      v-if="!isLast"
      class="step-line"
    />

    <!-- Step content -->
    <div class="step-body">
      <!-- Header row -->
      <div
        class="step-header"
        @click="toggleCollapse"
      >
        <span class="step-title-group">
          <span class="step-title">{{ step.title || step.label || '' }}</span>
        </span>
        
        <!-- Right side: sources + collapse button -->
        <div class="step-actions">
          <SourceGroup
            v-if="step.sources && step.sources.length > 0"
            :sources="step.sources"
            :max-visible="3"
            size="sm"
            @click="handleSourceClick"
          />
          <button
            class="collapse-btn"
            :aria-expanded="!step.collapsed"
          >
            <ChevronDown
              :class="['collapse-icon', { rotated: !step.collapsed }]"
            />
          </button>
        </div>
      </div>

      <!-- Collapsible content -->
      <Transition name="collapse">
        <div
          v-show="!step.collapsed"
          class="step-content"
        >
          <!-- Children (sub-steps like search results) -->
          <div
            v-if="step.children && step.children.length > 0"
            class="step-children"
          >
            <div
              v-for="child in step.children"
              :key="child.id"
              class="child-item"
            >
              <component
                :is="childIconMap[child.type] || Search"
                class="child-icon"
              />
              <span class="child-title">{{ child.title }}</span>
              <SourceGroup
                v-if="child.sources && child.sources.length > 0"
                :sources="child.sources"
                :max-visible="3"
                size="sm"
                class="child-sources"
                @click="handleSourceClick"
              />
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.timeline-step {
  position: relative;
  display: flex;
  flex-direction: column;
  padding-left: 22px;  /* Space for bullet + line */
}

.timeline-step:not(:first-child) {
  margin-top: 8px;
}

/* Bullet */
.step-bullet {
  position: absolute;
  left: 0;
  top: 3.5px;
  width: 16px;
  height: 16px;
  z-index: 2;
}

.bullet-inner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Done state: black with white checkmark + completion animation */
.bullet-inner.done {
  background: #1A1A1A;
  outline: white solid 6px;
  outline-offset: -6px;
  animation: checkmark-pop 400ms cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

.bullet-inner.done .check-icon {
  width: 12px;
  height: 12px;
  color: white;
  animation: checkmark-draw 300ms ease-out 100ms forwards;
  stroke-dasharray: 16;
  stroke-dashoffset: 16;
}

@keyframes checkmark-pop {
  0% {
    transform: scale(0.8);
    opacity: 0;
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes checkmark-draw {
  to {
    stroke-dashoffset: 0;
  }
}

/* Running state: cyan with ripple effect */
.bullet-inner.running {
  background: var(--td-state-thinking, #00D9FF);
  animation: pulse-bullet 1.5s ease-in-out infinite;
  position: relative;
}

.bullet-inner.running::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid var(--td-state-thinking, #00D9FF);
  animation: ripple-out 1.5s ease-out infinite;
}

.bullet-inner.running::after {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 1px solid var(--td-state-thinking, #00D9FF);
  animation: ripple-out 1.5s ease-out infinite 0.5s;
  opacity: 0.5;
}

@keyframes pulse-bullet {
  0%, 100% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(0, 217, 255, 0.4);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 0 8px 2px rgba(0, 217, 255, 0.3);
  }
}

@keyframes ripple-out {
  0% {
    transform: scale(0.8);
    opacity: 0.6;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

/* Failed state: red with subtle pulse */
.bullet-inner.failed {
  background: var(--td-state-error, #FF3B30);
  animation: failed-pulse 2s ease-in-out infinite;
}

@keyframes failed-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0);
  }
  50% {
    box-shadow: 0 0 8px 2px rgba(255, 59, 48, 0.4);
  }
}

/* Pending state: gray */
.bullet-inner.pending {
  background: var(--any-text-muted);
  opacity: 0.5;
}

/* Vertical line */
.step-line {
  position: absolute;
  left: 7px;  /* Center of bullet */
  top: 20px;
  bottom: -8px;
  width: 1px;
  background: var(--any-border);
  z-index: 1;
}

/* Step body */
.step-body {
  margin-left: 6px;
}

/* Header */
.step-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-right: 0;
  line-height: 1.5;
  font-size: 14px;
  cursor: pointer;
}

.step-header:hover {
  background: var(--any-bg-hover);
  margin: -2px -4px;
  padding: 2px 4px;
  border-radius: 6px;
}

.step-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.step-title {
  font-weight: 400;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Finished step: slightly muted */
.timeline-step.status-done .step-title {
  color: var(--any-text-secondary);
}

/* Actions */
.step-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
  opacity: 0;
}

.step-header:hover .collapse-btn {
  opacity: 1;
}

.collapse-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.collapse-icon {
  width: 16px;
  height: 16px;
  transition: transform 200ms ease;
}

.collapse-icon.rotated {
  transform: rotate(180deg);
}

/* Content area */
.step-content {
  padding-top: 8px;
}

/* Children */
.step-children {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.child-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
}

.child-icon {
  width: 16px;
  height: 16px;
  color: var(--any-text-muted);
  flex-shrink: 0;
}

.child-title {
  flex: 1;
  font-size: 14px;
  color: var(--any-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.child-sources {
  margin-left: auto;
}

/* Collapse transition */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 200ms ease-out;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
