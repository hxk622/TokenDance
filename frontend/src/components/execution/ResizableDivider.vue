<template>
  <div
    :class="[
      'resizable-divider',
      `divider-${direction}`,
      { dragging: isDragging }
    ]"
    @mousedown="handleMouseDown"
    @dblclick="handleDoubleClick"
  >
    <div class="divider-handle"></div>
    
    <!-- 实时比例提示 (拖拽时显示) -->
    <div v-if="isDragging && showRatioHint" class="ratio-hint">
      {{ ratioHintText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  direction: 'horizontal' | 'vertical'
  minBefore?: number  // 分隔条前部最小尺寸
  minAfter?: number   // 分隔条后部最小尺寸
  showRatioHint?: boolean  // 是否显示比例提示
}

interface Emits {
  (e: 'resize', delta: number): void
  (e: 'reset'): void
}

const props = withDefaults(defineProps<Props>(), {
  minBefore: 300,
  minAfter: 400,
  showRatioHint: true
})

const emit = defineEmits<Emits>()

// 状态
const isDragging = ref(false)
const startPos = ref(0)
const currentDelta = ref(0)

// 计算比例提示文本（由父组件传入实际比例）
const ratioHintText = computed(() => {
  // 父组件可以通过slot传入具体比例
  // 这里先显示移动距离
  return `${currentDelta.value > 0 ? '+' : ''}${currentDelta.value}px`
})

/**
 * 鼠标按下 - 开始拖拽
 */
function handleMouseDown(e: MouseEvent) {
  e.preventDefault()
  isDragging.value = true
  startPos.value = props.direction === 'horizontal' ? e.clientX : e.clientY
  currentDelta.value = 0

  // 监听全局鼠标移动和释放
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  
  // 拖拽时禁止文本选择
  document.body.style.userSelect = 'none'
  document.body.style.cursor = props.direction === 'horizontal' ? 'col-resize' : 'row-resize'
}

/**
 * 鼠标移动 - 计算位移
 */
function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return

  const currentPos = props.direction === 'horizontal' ? e.clientX : e.clientY
  const delta = currentPos - startPos.value
  currentDelta.value = delta

  // 发射resize事件，由父组件验证边界
  emit('resize', delta)
}

/**
 * 鼠标释放 - 结束拖拽
 */
function handleMouseUp() {
  if (!isDragging.value) return

  isDragging.value = false
  currentDelta.value = 0

  // 移除全局监听
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  
  // 恢复样式
  document.body.style.userSelect = ''
  document.body.style.cursor = ''
}

/**
 * 双击 - 恢复默认比例
 */
function handleDoubleClick() {
  emit('reset')
}
</script>

<style scoped>
/* 通用样式 */
.resizable-divider {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--divider-color, rgba(255, 255, 255, 0.1));
  transition: background 120ms ease-out;
  z-index: 10;
}

.resizable-divider:hover {
  background: var(--divider-hover, rgba(0, 217, 255, 0.5));
}

.resizable-divider.dragging {
  background: var(--color-node-active, #00D9FF);
  z-index: 1000;
}

/* 水平分隔条（调整左右比例）*/
.divider-horizontal {
  width: 8px;
  height: 100%;
  cursor: col-resize;
  /* 扩大可交互区域 */
  padding: 0 4px;
  margin: 0 -4px;
}

/* 垂直分隔条（调整上下比例）*/
.divider-vertical {
  width: 100%;
  height: 8px;
  cursor: row-resize;
  /* 扩大可交互区域 */
  padding: 4px 0;
  margin: -4px 0;
}

/* 分隔条把手（视觉指示器）*/
.divider-handle {
  pointer-events: none;
}

.divider-horizontal .divider-handle {
  width: 2px;
  height: 40px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 2px;
}

.divider-vertical .divider-handle {
  width: 40px;
  height: 2px;
  background: rgba(255, 255, 255, 0.4);
  border-radius: 2px;
}

.resizable-divider:hover .divider-handle {
  background: rgba(255, 255, 255, 0.8);
}

.resizable-divider.dragging .divider-handle {
  background: white;
}

/* 实时比例提示 */
.ratio-hint {
  position: absolute;
  padding: 4px 12px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  font-size: 12px;
  font-weight: 600;
  border-radius: 4px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 1001;
}

.divider-horizontal .ratio-hint {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.divider-vertical .ratio-hint {
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 拖拽动画 */
.resizable-divider {
  transition: background 120ms ease-out;
}

.resizable-divider.dragging {
  transition: none;
}

/* 暗色主题适配 */
@media (prefers-color-scheme: dark) {
  .resizable-divider {
    --divider-color: rgba(255, 255, 255, 0.1);
    --divider-hover: rgba(0, 217, 255, 0.5);
    --color-node-active: #00D9FF;
  }
}
</style>
