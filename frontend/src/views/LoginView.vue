<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4">
    <div class="max-w-md w-full">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">TokenDance</h1>
        <p class="mt-2 text-gray-600">Sign in to your account</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="bg-white rounded-lg shadow-md p-8">
        <!-- Error Alert -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-sm text-red-600">{{ error }}</p>
        </div>

        <!-- Email Field -->
        <div class="mb-4">
          <label for="email" class="block text-sm font-medium text-gray-700 mb-2">
            Email
          </label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            autocomplete="email"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="you@example.com"
          />
        </div>

        <!-- Password Field -->
        <div class="mb-6">
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
            Password
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            autocomplete="current-password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="••••••••"
          />
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isLoading"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign in</span>
        </button>
      </form>

      <!-- Register Link -->
      <p class="mt-6 text-center text-sm text-gray-600">
        Don't have an account?
        <router-link to="/register" class="text-blue-600 hover:text-blue-700 font-medium">
          Sign up
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { LoginRequest } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref<LoginRequest>({
  email: '',
  password: ''
})

const isLoading = ref(false)
const error = ref<string | null>(null)

async function handleLogin() {
  isLoading.value = true
  error.value = null

  try {
    await authStore.login(form.value)
    // Redirect to home page
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Login failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
