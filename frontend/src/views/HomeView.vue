<template>
  <div class="home-view flex items-center justify-center min-h-screen">
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">
        Welcome to TokenDance
      </h1>
      <p class="text-lg text-gray-600 mb-8">
        Universal AI Agent Platform
      </p>
      <div class="space-x-4">
        <button 
          class="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          @click="handleGetStarted"
        >
          Get Started
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const handleGetStarted = () => {
  console.log('Get Started clicked')
  // TODO: Navigate to registration or workspace creation
}
</script>

<style scoped>
.home-view {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>