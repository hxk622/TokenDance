<script setup lang="ts">
/**
 * InterventionPanel - 研究干预面板
 * 
 * 在研究进行中显示，允许用户：
 * - 追加方向/关注点
 * - 点击快捷操作按钮
 * - 发送自定义指令
 */
import { ref, computed } from 'vue'
import { Lightbulb, Send, ChevronDown, ChevronUp } from 'lucide-vue-next'
import type { 
  ResearchProgress, 
  ResearchIntervention,
  QuickInterventionButton 
} from './types'
import { QUICK_INTERVENTION_BUTTONS } from './types'

interface Props {
  /** 研究进度 */
  progress: ResearchProgress | null
  /** 是否折叠 */
  collapsed?: boolean
  /** 是否正在发送干预 */
  sending?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  collapsed: false,
  sending: false,
})

const emit = defineEmits<{
  /** 发送干预指令 */
  intervene: [intervention: ResearchIntervention]
  /** 切换折叠状态 */
  toggleCollapse: []
}>()

// 自定义输入内容
const customInput = ref('')
const isExpanded = ref(false)

// 根据当前研究状态过滤可显示的快捷按钮
const visibleButtons = computed<QuickInterventionButton[]>(() => {
  if (!props.progress) return []
  
  return QUICK_INTERVENTION_BUTTONS.filter(btn => {
    if (!btn.showWhen) return true
    return btn.showWhen(props.progress!)
  }).slice(0, 4) // 最多显示4个
})

// 发送快捷干预
function handleQuickIntervene(btn: QuickInterventionButton) {
  emit('intervene', {
    type: btn.type,
    content: btn.content,
    timestamp: new Date().toISOString(),
  })
}

// 发送自定义干预
function handleCustomIntervene() {
  if (!customInput.value.trim()) return
  
  emit('intervene', {
    type: 'custom',
    content: customInput.value.trim(),
    timestamp: new Date().toISOString(),
  })
  
  customInput.value = ''
}

// 键盘事件处理
function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleCustomIntervene()
  }
}
</script>

<template>
  <div 
    class="intervention-panel"
    :class="{ collapsed: props.collapsed }"
  >
    <!-- Header -->
    <div 
      class="panel-header"
      @click="emit('toggleCollapse')"
    >
      <div class="header-content">
        <Lightbulb class="w-4 h-4 text-[var(--exec-accent)]" />
        <span class="header-title">研究进行中，您可以引导方向</span>
      </div>
      <button class="collapse-btn">
        <ChevronUp 
          v-if="!props.collapsed" 
          class="w-4 h-4" 
        />
        <ChevronDown 
          v-else 
          class="w-4 h-4" 
        />
      </button>
    </div>

    <!-- Content (collapsible) -->
    <div 
      v-show="!props.collapsed"
      class="panel-content"
    >
      <!-- Quick Buttons -->
      <div 
        v-if="visibleButtons.length > 0"
        class="quick-buttons"
      >
        <button
          v-for="btn in visibleButtons"
          :key="btn.id"
          class="quick-btn"
          :disabled="props.sending"
          @click="handleQuickIntervene(btn)"
        >
          {{ btn.label }}
        </button>
      </div>

      <!-- Custom Input -->
      <div 
        v-if="isExpanded || visibleButtons.length === 0"
        class="custom-input-wrapper"
      >
        <input
          v-model="customInput"
          type="text"
          class="custom-input"
          placeholder="输入补充指令，如：更多关注技术细节..."
          :disabled="props.sending"
          @keydown="handleKeydown"
        >
        <button
          class="send-btn"
          :disabled="!customInput.trim() || props.sending"
          @click="handleCustomIntervene"
        >
          <Send class="w-4 h-4" />
        </button>
      </div>

      <!-- Expand/Collapse Custom Input -->
      <button
        v-if="visibleButtons.length > 0 && !isExpanded"
        class="expand-btn"
        @click="isExpanded = true"
      >
        或输入自定义指令...
      </button>
    </div>
  </div>
</template>

<style scoped>
.intervention-panel {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
  transition: all var(--any-duration-normal) var(--any-ease-out);
}

.intervention-panel.collapsed {
  border-color: transparent;
  background: var(--any-bg-secondary);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  transition: background var(--any-duration-fast) var(--any-ease-out);
}

.panel-header:hover {
  background: var(--any-bg-hover);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-secondary);
}

.collapse-btn {
  padding: 4px;
  border: none;
  background: none;
  color: var(--any-text-tertiary);
  cursor: pointer;
  border-radius: var(--any-radius-sm);
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.collapse-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.panel-content {
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Quick Buttons */
.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-btn {
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--any-text-secondary);
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-full);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.quick-btn:hover:not(:disabled) {
  background: var(--exec-accent);
  border-color: var(--exec-accent);
  color: var(--any-bg-primary);
}

.quick-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Custom Input */
.custom-input-wrapper {
  display: flex;
  gap: 8px;
}

.custom-input {
  flex: 1;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--any-text-primary);
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  outline: none;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.custom-input::placeholder {
  color: var(--any-text-muted);
}

.custom-input:focus {
  border-color: var(--exec-accent);
  box-shadow: 0 0 0 2px rgba(0, 217, 255, 0.1);
}

.custom-input:disabled {
  opacity: 0.5;
}

.send-btn {
  padding: 8px 12px;
  background: var(--exec-accent);
  border: none;
  border-radius: var(--any-radius-md);
  color: var(--any-bg-primary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.send-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Expand Button */
.expand-btn {
  padding: 8px;
  font-size: 12px;
  color: var(--any-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: color var(--any-duration-fast) var(--any-ease-out);
}

.expand-btn:hover {
  color: var(--any-text-secondary);
}
</style>
