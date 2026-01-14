<template>
  <div class="workflow-graph">
    <div class="placeholder">
      <div class="icon">🎨</div>
      <h3>Workflow Graph</h3>
      <p>Meego式DAG可视化 - 开发中</p>
      <div class="mock-nodes">
        <div 
          v-for="node in mockNodes" 
          :key="node.id"
          :class="['node', `status-${node.status}`]"
          @click="handleNodeClick(node.id)"
          @dblclick="handleNodeDoubleClick(node.id)"
        >
          {{ node.label }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  sessionId: string
}

interface Emits {
  (e: 'node-click', nodeId: string): void
  (e: 'node-double-click', nodeId: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

// Mock nodes for testing
const mockNodes = ref([
  { id: '1', label: 'Start', status: 'success' },
  { id: '2', label: 'Research', status: 'active' },
  { id: '3', label: 'Analysis', status: 'pending' },
  { id: '4', label: 'Report', status: 'inactive' },
  { id: '5', label: 'Complete', status: 'inactive' },
])

function handleNodeClick(nodeId: string) {
  emit('node-click', nodeId)
}

function handleNodeDoubleClick(nodeId: string) {
  emit('node-double-click', nodeId)
}
</script>

<style scoped>
.workflow-graph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(28, 28, 30, 0.5);
}

.placeholder {
  text-align: center;
  padding: 40px;
}

.icon {
  font-size: 48px;
  margin-bottom: 16px;
}

h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--text-primary, #ffffff);
}

p {
  font-size: 14px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  margin: 0 0 24px 0;
}

.mock-nodes {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.node {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

.node:hover {
  transform: scale(1.1);
}

.node.status-active {
  background: #00D9FF;
  color: #000;
  animation: pulse-breath 1.5s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(0, 217, 255, 0.5);
}

.node.status-success {
  background: #00FF88;
  color: #000;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.3);
}

.node.status-pending {
  background: #FFB800;
  color: #000;
  box-shadow: 0 0 10px rgba(255, 184, 0, 0.4);
}

.node.status-error {
  background: #FF3B30;
  color: #fff;
  box-shadow: 0 0 10px rgba(255, 59, 48, 0.5);
}

.node.status-inactive {
  background: #8E8E93;
  color: #fff;
  box-shadow: 0 0 5px rgba(142, 142, 147, 0.2);
}

@keyframes pulse-breath {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.9;
  }
}
</style>
