<template>
  <div id="app" class="min-h-screen bg-bg-primary text-text-primary">
    <RouterView v-slot="{ Component, route }">
      <Transition :name="route.meta.transition || 'page-fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<style>
/* Page Transition Animations */

/* Fade transition (default) */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.25s ease-out;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

/* Slide up transition */
.page-slide-up-enter-active,
.page-slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.page-slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.page-slide-up-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* Scale transition */
.page-scale-enter-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.page-scale-leave-active {
  transition: all 0.2s ease-out;
}

.page-scale-enter-from,
.page-scale-leave-to {
  opacity: 0;
  transform: scale(0.96);
}

/* Slide left transition (for forward navigation) */
.page-slide-left-enter-active,
.page-slide-left-leave-active {
  transition: all 0.3s ease-out;
}

.page-slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.page-slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}
</style>
