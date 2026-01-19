<script setup lang="ts">
import { computed } from 'vue'
import { PauseIcon, ForwardIcon } from '@heroicons/vue/24/solid'

interface Props {
  visible: boolean
  nodeId: string
  status: 'pending' | 'running' | 'success' | 'error'
  x: number
  y: number
}

interface Emits {
  (e: 'pause', nodeId: string): void
  (e: 'resume', nodeId: string): void
  (e: 'skip', nodeId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const controlsStyle = computed(() => ({
  left: `${props.x + 45}px`,
  top: `${props.y - 15}px`
}))

const showPause = computed(() => props.status === 'running')
const showSkip = computed(() => props.status === 'pending')
</script>

<template>
  <Teleport to="body">
    <Transition name="controls-fade">
      <div 
        v-if="visible && (showPause || showSkip)"
        class="node-hover-controls"
        :style="controlsStyle"
      >
        <button 
          v-if="showPause"
          class="control-btn control-pause"
          title="暂停执行"
          @click.stop="emit('pause', nodeId)"
        >
          <PauseIcon class="w-3.5 h-3.5" />
        </button>
        
        <button 
          v-if="showSkip"
          class="control-btn control-skip"
          title="跳过此步"
          @click.stop="emit('skip', nodeId)"
        >
          <ForwardIcon class="w-3.5 h-3.5" />
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.node-hover-controls {
  position: fixed;
  z-index: 9998;
  display: flex;
  flex-direction: column;
  gap: 4px;
  pointer-events: auto;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 150ms ease;
}

.control-btn:hover {
  transform: scale(1.1);
}

.control-pause {
  color: var(--td-state-waiting);
}

.control-pause:hover {
  background: var(--td-state-waiting-bg);
  border-color: var(--td-state-waiting);
}

.control-resume {
  color: var(--td-state-executing);
}

.control-resume:hover {
  background: var(--td-state-executing-bg);
  border-color: var(--td-state-executing);
}

.control-skip {
  color: var(--any-text-tertiary);
}

.control-skip:hover {
  background: var(--any-bg-hover);
  border-color: var(--any-border-hover);
  color: var(--any-text-primary);
}

/* Transition */
.controls-fade-enter-active,
.controls-fade-leave-active {
  transition: all 100ms ease;
}

.controls-fade-enter-from,
.controls-fade-leave-to {
  opacity: 0;
  transform: translateX(-4px);
}
</style>
