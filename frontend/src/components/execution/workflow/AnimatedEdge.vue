<script setup lang="ts">
/**
 * AnimatedEdge - 工作流连线动画组件
 * 
 * 显示节点间的数据流向，支持不同状态的动画效果
 */

import { computed, type PropType } from 'vue'

export type EdgeStatus = 'idle' | 'active' | 'completed' | 'error'

const props = defineProps({
  /** 起点坐标 */
  from: {
    type: Object as PropType<{ x: number; y: number }>,
    required: true
  },
  /** 终点坐标 */
  to: {
    type: Object as PropType<{ x: number; y: number }>,
    required: true
  },
  /** 连线状态 */
  status: {
    type: String as PropType<EdgeStatus>,
    default: 'idle'
  },
  /** 是否显示流动动画 */
  animated: {
    type: Boolean,
    default: true
  },
  /** 线条宽度 */
  strokeWidth: {
    type: Number,
    default: 2
  },
  /** 曲线偏移量 */
  curveOffset: {
    type: Number,
    default: 50
  }
})

// 计算贝塞尔曲线路径
const pathD = computed(() => {
  const { from, to, curveOffset } = props
  
  // 垂直方向的贝塞尔曲线
  const midY = (from.y + to.y) / 2
  
  return `M ${from.x} ${from.y} 
          C ${from.x} ${midY + curveOffset}, 
            ${to.x} ${midY - curveOffset}, 
            ${to.x} ${to.y}`
})

// 计算路径总长度（用于动画）
const pathLength = computed(() => {
  // 简化计算，实际长度会在 mounted 后通过 SVG API 获取
  const dx = props.to.x - props.from.x
  const dy = props.to.y - props.from.y
  return Math.sqrt(dx * dx + dy * dy) * 1.5
})

// 根据状态返回颜色
const strokeColor = computed(() => {
  switch (props.status) {
    case 'active':
      return 'var(--td-state-executing)'
    case 'completed':
      return 'var(--td-state-executing)'
    case 'error':
      return 'var(--td-state-error)'
    default:
      return 'var(--any-border)'
  }
})

// 动画类
const animationClass = computed(() => ({
  'edge-animated': props.animated && props.status === 'active',
  'edge-completed': props.status === 'completed',
  'edge-error': props.status === 'error'
}))
</script>

<template>
  <g
    class="animated-edge"
    :class="animationClass"
  >
    <!-- 背景线（静态） -->
    <path
      class="edge-bg"
      :d="pathD"
      :stroke-width="strokeWidth"
      fill="none"
      stroke="var(--any-border-light)"
    />
    
    <!-- 主线条 -->
    <path
      class="edge-main"
      :d="pathD"
      :stroke="strokeColor"
      :stroke-width="strokeWidth"
      fill="none"
      stroke-linecap="round"
      :style="{
        '--path-length': pathLength
      }"
    />
    
    <!-- 流动粒子效果 -->
    <circle
      v-if="animated && status === 'active'"
      class="edge-particle"
      r="3"
      :fill="strokeColor"
    >
      <animateMotion
        :dur="'1.5s'"
        repeatCount="indefinite"
        :path="pathD"
      />
    </circle>
    
    <!-- 完成时的闪光效果 -->
    <path
      v-if="status === 'completed'"
      class="edge-glow"
      :d="pathD"
      :stroke="strokeColor"
      :stroke-width="strokeWidth + 4"
      fill="none"
      stroke-linecap="round"
      opacity="0.3"
    />
  </g>
</template>

<style scoped>
.animated-edge {
  pointer-events: none;
}

.edge-bg {
  opacity: 0.3;
}

.edge-main {
  transition: stroke var(--any-duration-normal) var(--any-ease-out);
}

/* 流动动画 */
.edge-animated .edge-main {
  stroke-dasharray: 8 4;
  animation: edge-flow 1s linear infinite;
}

@keyframes edge-flow {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: -24;
  }
}

/* 完成状态 */
.edge-completed .edge-main {
  stroke-dasharray: none;
}

.edge-glow {
  animation: edge-glow-fade 0.5s ease-out forwards;
}

@keyframes edge-glow-fade {
  0% {
    opacity: 0.5;
  }
  100% {
    opacity: 0;
  }
}

/* 粒子效果 */
.edge-particle {
  filter: drop-shadow(0 0 4px currentColor);
}

/* 错误状态 */
.edge-error .edge-main {
  stroke-dasharray: 4 4;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .edge-animated .edge-main {
    animation: none;
  }
  
  .edge-particle {
    display: none;
  }
}
</style>
