<script setup lang="ts">
import { computed } from 'vue'
import {
  ArrowPathIcon,
  DocumentTextIcon,
  ClipboardDocumentIcon,
  ForwardIcon,
  PauseIcon,
  PlayIcon,
} from '@heroicons/vue/24/outline'

interface NodeData {
  id: string
  type: 'manus' | 'coworker'
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
  label: string
}

interface Props {
  visible: boolean
  node: NodeData | null
  x: number
  y: number
}

interface Emits {
  (e: 'close'): void
  (e: 'rerun', nodeId: string): void
  (e: 'view-logs', nodeId: string): void
  (e: 'copy-output', nodeId: string): void
  (e: 'skip', nodeId: string): void
  (e: 'pause', nodeId: string): void
  (e: 'resume', nodeId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const menuStyle = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`
}))

const menuItems = computed(() => {
  if (!props.node) return []
  
  const items = []
  
  // 根据状态显示不同菜单项
  if (props.node.status === 'active') {
    items.push({
      id: 'pause',
      icon: PauseIcon,
      label: '暂停执行',
      handler: () => emit('pause', props.node!.id),
      variant: 'warning'
    })
  }
  
  if (props.node.status === 'pending') {
    items.push({
      id: 'resume',
      icon: PlayIcon,
      label: '继续执行',
      handler: () => emit('resume', props.node!.id),
      variant: 'success'
    })
  }
  
  if (['success', 'error'].includes(props.node.status)) {
    items.push({
      id: 'rerun',
      icon: ArrowPathIcon,
      label: '重新执行',
      handler: () => emit('rerun', props.node!.id),
      variant: 'default'
    })
  }
  
  if (props.node.status === 'inactive') {
    items.push({
      id: 'skip',
      icon: ForwardIcon,
      label: '跳过此步',
      handler: () => emit('skip', props.node!.id),
      variant: 'muted'
    })
  }
  
  // 通用菜单项
  items.push(
    { id: 'divider' },
    {
      id: 'view-logs',
      icon: DocumentTextIcon,
      label: '查看详细日志',
      handler: () => emit('view-logs', props.node!.id),
      variant: 'default'
    },
    {
      id: 'copy-output',
      icon: ClipboardDocumentIcon,
      label: '复制输出',
      handler: () => emit('copy-output', props.node!.id),
      variant: 'default'
    }
  )
  
  return items
})

function handleClickOutside(event: MouseEvent) {
  if (!(event.target as HTMLElement).closest('.node-context-menu')) {
    emit('close')
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible && node" class="menu-backdrop" @click="handleClickOutside">
      <div class="node-context-menu" :style="menuStyle" @click.stop>
        <!-- Menu Header -->
        <div class="menu-header">
          <span class="menu-node-label">{{ node.label }}</span>
          <span class="menu-node-type" :class="`type-${node.type}`">
            {{ node.type === 'manus' ? 'Manus' : 'Coworker' }}
          </span>
        </div>
        
        <!-- Menu Items -->
        <div class="menu-items">
          <template v-for="item in menuItems" :key="item.id">
            <div v-if="item.id === 'divider'" class="menu-divider" />
            <button
              v-else
              class="menu-item"
              :class="`variant-${item.variant}`"
              @click="item.handler?.(); emit('close')"
            >
              <component :is="item.icon" class="w-4 h-4" />
              <span>{{ item.label }}</span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

.node-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 200px;
  background: rgba(28, 28, 30, 0.98);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow: hidden;
  animation: menuSlideIn 150ms ease-out;
}

@keyframes menuSlideIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.menu-node-label {
  font-size: 13px;
  font-weight: 600;
  color: #ffffff;
}

.menu-node-type {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: 4px;
}

.menu-node-type.type-manus {
  background: rgba(99, 102, 241, 0.2);
  color: #818CF8;
}

.menu-node-type.type-coworker {
  background: rgba(16, 185, 129, 0.2);
  color: #34D399;
}

.menu-items {
  padding: 6px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.85);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 150ms ease;
}

.menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.menu-item.variant-warning {
  color: #FFB800;
}

.menu-item.variant-warning:hover {
  background: rgba(255, 184, 0, 0.15);
}

.menu-item.variant-success {
  color: #00FF88;
}

.menu-item.variant-success:hover {
  background: rgba(0, 255, 136, 0.15);
}

.menu-item.variant-muted {
  color: rgba(255, 255, 255, 0.5);
}

.menu-item.variant-muted:hover {
  color: rgba(255, 255, 255, 0.8);
}

.menu-divider {
  height: 1px;
  margin: 6px 0;
  background: rgba(255, 255, 255, 0.1);
}
</style>
