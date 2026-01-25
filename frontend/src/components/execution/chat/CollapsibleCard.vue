<script setup lang="ts">
/**
 * CollapsibleCard - AnyGen 风格的可折叠卡片
 * 
 * 特点:
 * - 左侧图标 (slot 或 Lucide icon)
 * - 标题 + 可选描述
 * - 右侧操作区 (来源组、展开按钮等)
 * - 平滑折叠动画
 */
import { ref, watch, computed } from 'vue'
import { ChevronDown } from 'lucide-vue-next'

interface Props {
  title?: string
  collapsed?: boolean
  showCollapseButton?: boolean
  /** 是否显示边框 */
  bordered?: boolean
  /** 内边距大小 */
  padding?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  collapsed: false,
  showCollapseButton: true,
  bordered: true,
  padding: 'md'
})

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  toggle: []
}>()

const isCollapsed = ref(props.collapsed)

// Sync with prop
watch(() => props.collapsed, (val) => {
  isCollapsed.value = val
})

function toggle() {
  isCollapsed.value = !isCollapsed.value
  emit('update:collapsed', isCollapsed.value)
  emit('toggle')
}

const paddingClass = computed(() => {
  const map = {
    sm: 'padding-sm',
    md: 'padding-md',
    lg: 'padding-lg'
  }
  return map[props.padding]
})
</script>

<template>
  <div
    :class="[
      'collapsible-card',
      paddingClass,
      { 
        bordered: bordered,
        collapsed: isCollapsed 
      }
    ]"
  >
    <!-- Header -->
    <div
      class="card-header"
      :class="{ clickable: showCollapseButton }"
      @click="showCollapseButton && toggle()"
    >
      <!-- Left: Icon slot -->
      <div class="header-left">
        <slot name="icon" />
        <span class="header-title">{{ title }}</span>
      </div>

      <!-- Right: Actions + Collapse button -->
      <div class="header-right">
        <slot name="actions" />
        <button
          v-if="showCollapseButton"
          class="collapse-btn"
          :aria-expanded="!isCollapsed"
          @click.stop="toggle"
        >
          <ChevronDown
            :class="['collapse-icon', { rotated: !isCollapsed }]"
          />
        </button>
      </div>
    </div>

    <!-- Content -->
    <Transition name="collapse">
      <div
        v-show="!isCollapsed"
        class="card-content"
      >
        <slot />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.collapsible-card {
  border-radius: 12px;
  background: var(--any-bg-secondary);
  overflow: hidden;
}

.collapsible-card.bordered {
  border: 1px solid var(--any-border);
}

/* Padding variants */
.collapsible-card.padding-sm .card-header {
  padding: 6px 8px;
}
.collapsible-card.padding-sm .card-content {
  padding: 0 8px 8px;
}

.collapsible-card.padding-md .card-header {
  padding: 8px;
}
.collapsible-card.padding-md .card-content {
  padding: 0 8px 8px;
}

.collapsible-card.padding-lg .card-header {
  padding: 12px 14px;
}
.collapsible-card.padding-lg .card-content {
  padding: 0 14px 14px;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  cursor: default;
  user-select: none;
}

.card-header.clickable {
  cursor: pointer;
}

.card-header.clickable:hover {
  background: var(--any-bg-hover);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.header-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
  line-height: 24px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* Collapse button */
.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  margin-right: -3px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
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
.card-content {
  position: relative;
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
  max-height: 0 !important;
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
