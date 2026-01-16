<script setup lang="ts">
import { computed } from 'vue'
import { PauseIcon, PlayIcon, ForwardIcon } from '@heroicons/vue/24/solid'

interface Props {
  visible: boolean
  nodeId: string
  status: 'active' | 'success' | 'pending' | 'error' | 'inactive'
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

const showPause = computed(() => props.status === 'active')
const showResume = computed(() => props.status === 'pending')
const showSkip = computed(() => ['inactive', 'pending'].includes(props.status))
</script>

<template>
  <Teleport to="body">
    <Transition name="controls-fade">
      <div 
        v-if="visible && (showPause || showResume || showSkip)"
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
          v-if="showResume"
          class="control-btn control-resume"
          title="继续执行"
          @click.stop="emit('resume', nodeId)"
        >
          <PlayIcon class="w-3.5 h-3.5" />
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
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(28, 28, 30, 0.95);
  backdrop-filter: blur(8px);
  cursor: pointer;
  transition: all 150ms ease;
}

.control-btn:hover {
  transform: scale(1.1);
}

.control-pause {
  color: #FFB800;
}

.control-pause:hover {
  background: rgba(255, 184, 0, 0.2);
  border-color: #FFB800;
}

.control-resume {
  color: #00FF88;
}

.control-resume:hover {
  background: rgba(0, 255, 136, 0.2);
  border-color: #00FF88;
}

.control-skip {
  color: #8E8E93;
}

.control-skip:hover {
  background: rgba(142, 142, 147, 0.2);
  border-color: #8E8E93;
  color: #ffffff;
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
