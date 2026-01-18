<script setup lang="ts">
/**
 * ProgressRing - 增强版进度环组件
 * 
 * 特性:
 * - 主进度环: 显示整体完成进度
 * - 内环: 显示当前步骤进度 (可选)
 * - 颜色渐变: cyan → green (随进度变化)
 * - 完成时粒子爆发效果
 * - 支持 reduced-motion
 */

import { computed, ref, watch } from 'vue'

const props = withDefaults(defineProps<{
  /** 主进度 0-100 */
  progress: number
  /** 当前步骤进度 0-100 (可选) */
  stepProgress?: number
  /** 尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否显示百分比文字 */
  showPercent?: boolean
  /** 是否显示完成动画 */
  showCompletionEffect?: boolean
}>(), {
  stepProgress: 0,
  size: 'md',
  showPercent: true,
  showCompletionEffect: true
})

const emit = defineEmits<{
  (e: 'complete'): void
}>()

// 尺寸配置
const sizeConfig = {
  sm: { width: 32, strokeWidth: 3, fontSize: 10 },
  md: { width: 44, strokeWidth: 3, fontSize: 12 },
  lg: { width: 64, strokeWidth: 4, fontSize: 16 }
}

const config = computed(() => sizeConfig[props.size])
const radius = computed(() => (config.value.width - config.value.strokeWidth) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)

// 主进度弧长
const mainDashOffset = computed(() => {
  const progress = Math.min(100, Math.max(0, props.progress))
  return circumference.value - (progress / 100) * circumference.value
})

// 步骤进度弧长 (内环)
const stepDashOffset = computed(() => {
  const progress = Math.min(100, Math.max(0, props.stepProgress))
  return circumference.value - (progress / 100) * circumference.value
})

// 根据进度计算颜色 (cyan → green)
const progressColor = computed(() => {
  const progress = props.progress / 100
  // 从 cyan (#00D9FF) 到 green (#00FF88)
  const r = 0
  const g = Math.round(217 + (255 - 217) * progress)
  const b = Math.round(255 + (136 - 255) * progress)
  return `rgb(${r}, ${g}, ${b})`
})

// 完成状态
const isComplete = computed(() => props.progress >= 100)
const showParticles = ref(false)

// 监听完成状态
watch(isComplete, (complete) => {
  if (complete && props.showCompletionEffect) {
    showParticles.value = true
    emit('complete')
    setTimeout(() => {
      showParticles.value = false
    }, 1000)
  }
})

// 粒子位置
const particles = computed(() => {
  const count = 8
  return Array.from({ length: count }, (_, i) => ({
    angle: (i / count) * 360,
    delay: i * 50
  }))
})
</script>

<template>
  <div 
    class="progress-ring-container"
    :class="[`size-${size}`, { complete: isComplete }]"
    :style="{ width: `${config.width}px`, height: `${config.width}px` }"
  >
    <svg 
      class="progress-svg"
      :viewBox="`0 0 ${config.width} ${config.width}`"
    >
      <defs>
        <!-- 主进度渐变 -->
        <linearGradient
          id="progress-gradient"
          x1="0%"
          y1="0%"
          x2="100%"
          y2="0%"
        >
          <stop
            offset="0%"
            stop-color="var(--td-state-thinking)"
          />
          <stop
            offset="100%"
            :stop-color="progressColor"
          />
        </linearGradient>
        
        <!-- 发光滤镜 -->
        <filter
          id="glow"
          x="-50%"
          y="-50%"
          width="200%"
          height="200%"
        >
          <feGaussianBlur
            stdDeviation="2"
            result="coloredBlur"
          />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      
      <!-- 背景环 -->
      <circle
        class="ring-bg"
        :cx="config.width / 2"
        :cy="config.width / 2"
        :r="radius"
        :stroke-width="config.strokeWidth"
        fill="none"
        stroke="var(--any-border)"
      />
      
      <!-- 步骤进度环 (内环，较细) -->
      <circle
        v-if="stepProgress > 0"
        class="ring-step"
        :cx="config.width / 2"
        :cy="config.width / 2"
        :r="radius - 4"
        :stroke-width="config.strokeWidth - 1"
        fill="none"
        stroke="var(--any-border-hover)"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="stepDashOffset"
        stroke-linecap="round"
        transform="rotate(-90)"
        :transform-origin="`${config.width / 2} ${config.width / 2}`"
      />
      
      <!-- 主进度环 -->
      <circle
        class="ring-main"
        :cx="config.width / 2"
        :cy="config.width / 2"
        :r="radius"
        :stroke-width="config.strokeWidth"
        fill="none"
        stroke="url(#progress-gradient)"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="mainDashOffset"
        stroke-linecap="round"
        transform="rotate(-90)"
        :transform-origin="`${config.width / 2} ${config.width / 2}`"
        :filter="isComplete ? 'url(#glow)' : undefined"
      />
    </svg>
    
    <!-- 百分比文字 -->
    <span 
      v-if="showPercent" 
      class="percent-text"
      :style="{ fontSize: `${config.fontSize}px`, color: progressColor }"
    >
      {{ Math.round(progress) }}%
    </span>
    
    <!-- 完成粒子效果 -->
    <Transition name="particles">
      <div
        v-if="showParticles"
        class="particles-container"
      >
        <div
          v-for="(particle, i) in particles"
          :key="i"
          class="particle"
          :style="{
            '--angle': `${particle.angle}deg`,
            '--delay': `${particle.delay}ms`,
            background: progressColor
          }"
        />
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.progress-ring-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-svg {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.ring-bg {
  opacity: 0.3;
}

.ring-main {
  transition: stroke-dashoffset var(--any-duration-slow) var(--any-ease-smooth);
}

.ring-step {
  opacity: 0.5;
  transition: stroke-dashoffset var(--any-duration-normal) var(--any-ease-out);
}

.percent-text {
  position: absolute;
  font-weight: 700;
  letter-spacing: -0.02em;
  transition: color var(--any-duration-normal) var(--any-ease-out);
}

/* 完成状态 */
.complete .ring-main {
  animation: ring-glow 1s ease-out;
}

@keyframes ring-glow {
  0%, 100% { filter: none; }
  50% { filter: url(#glow); }
}

/* 粒子容器 */
.particles-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  animation: particle-burst 0.6s ease-out forwards;
  animation-delay: var(--delay);
}

@keyframes particle-burst {
  0% {
    transform: translate(-50%, -50%) rotate(var(--angle)) translateY(0);
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) rotate(var(--angle)) translateY(-24px);
    opacity: 0;
  }
}

/* 粒子过渡 */
.particles-enter-active,
.particles-leave-active {
  transition: opacity 0.3s;
}

.particles-enter-from,
.particles-leave-to {
  opacity: 0;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .ring-main,
  .ring-step {
    transition: none;
  }
  
  .complete .ring-main {
    animation: none;
  }
  
  .particle {
    animation: none;
    display: none;
  }
}
</style>
