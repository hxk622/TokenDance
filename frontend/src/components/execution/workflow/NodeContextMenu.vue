<script setup lang="ts">
import { computed } from 'vue'
import {
  ArrowPathIcon,
  DocumentTextIcon,
  ClipboardDocumentIcon,
  ForwardIcon,
  PauseIcon,
} from '@heroicons/vue/24/outline'

interface NodeData {
  id: string
  status: 'pending' | 'running' | 'success' | 'error'
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

function statusText(status: string): string {
  const map: Record<string, string> = {
    pending: '未执行',
    running: '执行中',
    success: '已完成',
    error: '出错'
  }
  return map[status] || status
}

const menuStyle = computed(() => ({
  left: `${props.x}px`,
  top: `${props.y}px`
}))

const menuItems = computed(() => {
  if (!props.node) return []
  
  const items = []
  
  // 根据状态显示不同菜单项
  if (props.node.status === 'running') {
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
      id: 'skip',
      icon: ForwardIcon,
      label: '跳过此步',
      handler: () => emit('skip', props.node!.id),
      variant: 'muted'
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
    <div
      v-if="visible && node"
      class="menu-backdrop"
      @click="handleClickOutside"
    >
      <div
        class="node-context-menu"
        :style="menuStyle"
        @click.stop
      >
        <!-- Menu Header -->
        <div class="menu-header">
          <span class="menu-node-label">{{ node.label }}</span>
          <span
            class="menu-status-badge"
            :class="`status-${node.status}`"
          >
            {{ statusText(node.status) }}
          </span>
        </div>
        
        <!-- Menu Items -->
        <div class="menu-items">
          <template
            v-for="item in menuItems"
            :key="item.id"
          >
            <div
              v-if="item.id === 'divider'"
              class="menu-divider"
            />
            <button
              v-else
              class="menu-item"
              :class="`variant-${item.variant}`"
              @click="item.handler?.(); emit('close')"
            >
              <component
                :is="item.icon"
                class="w-4 h-4"
              />
              <span>{{ item.label }}</span>
            </button>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
/* NodeContextMenu - 使用全局主题变量 */
.menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 9998;
}

.node-context-menu {
  position: fixed;
  z-index: 9999;
  min-width: 200px;
  background: var(--any-bg-secondary);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-xl);
  box-shadow: var(--any-shadow-xl);
  overflow: hidden;
  animation: menuSlideIn var(--any-duration-fast) var(--any-ease-out);
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
  border-bottom: 1px solid var(--any-border);
}

.menu-node-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.menu-status-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  padding: 2px 6px;
  border-radius: var(--any-radius-sm);
}

.menu-status-badge.status-pending {
  background: rgba(142, 142, 147, 0.2);
  color: #8E8E93;
}

.menu-status-badge.status-running {
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
}

.menu-status-badge.status-success {
  background: rgba(0, 255, 136, 0.2);
  color: #00FF88;
}

.menu-status-badge.status-error {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
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
  color: var(--any-text-primary);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.menu-item:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.menu-item.variant-warning {
  color: var(--td-state-waiting);
}

.menu-item.variant-warning:hover {
  background: var(--td-state-waiting-bg);
}

.menu-item.variant-success {
  color: var(--td-state-executing);
}

.menu-item.variant-success:hover {
  background: var(--td-state-executing-bg);
}

.menu-item.variant-muted {
  color: var(--any-text-tertiary);
}

.menu-item.variant-muted:hover {
  color: var(--any-text-secondary);
}

.menu-divider {
  height: 1px;
  margin: 6px 0;
  background: var(--any-border);
}
</style>
