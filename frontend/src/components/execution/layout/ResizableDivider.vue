<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  direction: 'vertical' | 'horizontal'  // vertical: 左右分隔, horizontal: 上下分隔
}

const props = defineProps<Props>()
const emit = defineEmits<{
  drag: [delta: number]
  'double-click': []
}>()

const isDragging = ref(false)
const startPosition = ref(0)

function handleMouseDown(e: MouseEvent) {
  isDragging.value = true
  startPosition.value = props.direction === 'vertical' ? e.clientX : e.clientY
  
  // Add global event listeners
  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.body.style.cursor = props.direction === 'vertical' ? 'col-resize' : 'row-resize'
  document.body.style.userSelect = 'none'
  
  e.preventDefault()
}

function handleMouseMove(e: MouseEvent) {
  if (!isDragging.value) return
  
  const currentPosition = props.direction === 'vertical' ? e.clientX : e.clientY
  const delta = currentPosition - startPosition.value
  
  if (delta !== 0) {
    emit('drag', delta)
    startPosition.value = currentPosition
  }
}

function handleMouseUp() {
  if (!isDragging.value) return
  
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

function handleDoubleClick() {
  emit('double-click')
}
</script>

<template>
  <div
    :class="[
      'resizable-divider',
      direction,
      { dragging: isDragging }
    ]"
    @mousedown="handleMouseDown"
    @dblclick="handleDoubleClick"
  >
    <div class="divider-handle">
      <div class="handle-indicator" />
    </div>
  </div>
</template>

<style scoped>
.resizable-divider {
  position: relative;
  background: var(--divider-color, rgba(255, 255, 255, 0.1));
  transition: background var(--transition-hover, all 120ms ease-out);
  flex-shrink: 0;
  z-index: 10;
}

/* Vertical Divider (left-right split) */
.resizable-divider.vertical {
  width: 8px;
  cursor: col-resize;
  height: 100%;
}

.resizable-divider.vertical .divider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resizable-divider.vertical .handle-indicator {
  width: 4px;
  height: 40px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.2);
  opacity: 0;
  transition: opacity 120ms ease-out;
}

/* Horizontal Divider (top-bottom split) */
.resizable-divider.horizontal {
  height: 8px;
  cursor: row-resize;
  width: 100%;
}

.resizable-divider.horizontal .divider-handle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resizable-divider.horizontal .handle-indicator {
  width: 40px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.2);
  opacity: 0;
  transition: opacity 120ms ease-out;
}

/* Hover State */
.resizable-divider:hover {
  background: var(--divider-hover, rgba(0, 217, 255, 0.5));
}

.resizable-divider:hover .handle-indicator {
  opacity: 1;
}

/* Dragging State */
.resizable-divider.dragging {
  background: var(--color-node-active, #00D9FF);
}

.resizable-divider.dragging .handle-indicator {
  opacity: 1;
  background: rgba(255, 255, 255, 0.8);
}

/* CSS Variables */
:root {
  --divider-color: rgba(255, 255, 255, 0.1);
  --divider-hover: rgba(0, 217, 255, 0.5);
  --color-node-active: #00D9FF;
  --transition-hover: all 120ms ease-out;
}
</style>
