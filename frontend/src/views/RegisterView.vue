<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-8">
    <div class="max-w-md w-full">
      <!-- Logo -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">TokenDance</h1>
        <p class="mt-2 text-gray-600">Create your account</p>
      </div>

      <!-- Register Form -->
      <form @submit.prevent="handleRegister" class="bg-white rounded-lg shadow-md p-8">
        <!-- Error Alert -->
        <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-sm text-red-600">{{ error }}</p>
        </div>

        <!-- Username Field -->
        <div class="mb-4">
          <label for="username" class="block text-sm font-medium text-gray-700 mb-2">
            Username
          </label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            required
            autocomplete="username"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="johndoe"
          />
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
        <div class="mb-4">
          <label for="password" class="block text-sm font-medium text-gray-700 mb-2">
            Password
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            autocomplete="new-password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="••••••••"
          />
          <p class="mt-1 text-xs text-gray-500">
            Minimum 8 characters
          </p>
        </div>

        <!-- Confirm Password Field -->
        <div class="mb-6">
          <label for="confirmPassword" class="block text-sm font-medium text-gray-700 mb-2">
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            v-model="form.confirmPassword"
            type="password"
            required
            autocomplete="new-password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="••••••••"
          />
          <p v-if="passwordMismatch" class="mt-1 text-xs text-red-600">
            Passwords do not match
          </p>
        </div>

        <!-- Terms Checkbox -->
        <div class="mb-6">
          <label class="flex items-start">
            <input
              v-model="form.agreeToTerms"
              type="checkbox"
              required
              class="mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span class="ml-2 text-sm text-gray-600">
              I agree to the
              <a href="#" class="text-blue-600 hover:text-blue-700">Terms of Service</a>
              and
              <a href="#" class="text-blue-600 hover:text-blue-700">Privacy Policy</a>
            </span>
          </label>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          :disabled="isLoading || passwordMismatch || !form.agreeToTerms"
          class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="isLoading">Creating account...</span>
          <span v-else>Create account</span>
        </button>
      </form>

      <!-- Login Link -->
      <p class="mt-6 text-center text-sm text-gray-600">
        Already have an account?
        <router-link to="/login" class="text-blue-600 hover:text-blue-700 font-medium">
          Sign in
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { RegisterRequest } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref<RegisterRequest & { confirmPassword: string; agreeToTerms: boolean }>({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreeToTerms: false
})

const isLoading = ref(false)
const error = ref<string | null>(null)

const passwordMismatch = computed(() => {
  return form.value.password && form.value.confirmPassword && 
         form.value.password !== form.value.confirmPassword
})

async function handleRegister() {
  if (passwordMismatch.value) {
    error.value = 'Passwords do not match'
    return
  }

  isLoading.value = true
  error.value = null

  try {
    await authStore.register({
      username: form.value.username,
      email: form.value.email,
      password: form.value.password
    })
    // Redirect to home page
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
