<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="visible"
        class="login-overlay"
        @click.self="handleClose"
      >
        <div class="login-modal">
          <!-- Close Button -->
          <button
            class="close-btn"
            aria-label="Close"
            @click="handleClose"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>

          <!-- Logo & Title -->
          <div class="modal-header">
            <div class="logo-section">
              <svg
                class="logo-icon"
                viewBox="0 0 32 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M16 2L4 8v8c0 8 5.33 15.47 12 18 6.67-2.53 12-10 12-18V8L16 2z"
                  fill="currentColor"
                  opacity="0.1"
                />
                <path
                  d="M16 4L6 9v7c0 6.8 4.27 13.17 10 15.4 5.73-2.23 10-8.6 10-15.4V9L16 4z"
                  stroke="currentColor"
                  stroke-width="1.5"
                  fill="none"
                />
                <circle
                  cx="16"
                  cy="14"
                  r="4"
                  stroke="currentColor"
                  stroke-width="1.5"
                />
                <path
                  d="M12 22c0-2.2 1.8-4 4-4s4 1.8 4 4"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                />
              </svg>
              <h1 class="logo-text">
                TokenDance
              </h1>
            </div>
          <h2 class="modal-title">
            登录
          </h2>
          <p class="modal-subtitle">
            {{ props.message || '登录后可使用完整的 AI 智能工作台功能' }}
          </p>
          </div>

          <!-- OAuth Buttons -->
          <div class="oauth-section">
            <button
              :disabled="isLoading"
              class="oauth-btn oauth-google"
              @click="handleGoogleLogin"
            >
              <svg
                class="oauth-icon"
                viewBox="0 0 24 24"
              >
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              <span>Google</span>
            </button>

            <button
              :disabled="isLoading"
              class="oauth-btn oauth-wechat"
              @click="handleWeChatLogin"
            >
              <svg
                class="oauth-icon"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178A1.17 1.17 0 014.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178 1.17 1.17 0 01-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 01.598.082l1.584.926a.272.272 0 00.14.045c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 01-.023-.156.49.49 0 01.201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.01-.269-.027-.407-.03zm-2.53 3.274c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.97-.982zm4.844 0c.535 0 .969.44.969.982a.976.976 0 01-.969.983.976.976 0 01-.969-.983c0-.542.434-.982.969-.982z" />
              </svg>
              <span>微信</span>
            </button>
          </div>

          <!-- Divider -->
          <div class="divider">
            <span>或使用邮箱登录</span>
          </div>

          <!-- Email Form -->
          <form
            class="email-form"
            @submit.prevent="handleEmailLogin"
          >
            <div class="form-group">
              <label
                for="login-email"
                class="form-label"
              >邮箱地址</label>
              <input
                id="login-email"
                v-model="form.email"
                type="email"
                required
                autocomplete="email"
                class="form-input"
                placeholder="you@example.com"
              >
            </div>

            <div class="form-group">
              <label
                for="login-password"
                class="form-label"
              >密码</label>
              <input
                id="login-password"
                v-model="form.password"
                type="password"
                required
                autocomplete="current-password"
                class="form-input"
                placeholder="••••••••"
              >
            </div>

            <!-- Error Message -->
            <div
              v-if="error"
              class="error-message"
            >
              {{ error }}
            </div>

            <button
              type="submit"
              :disabled="isLoading || !form.email || !form.password"
              class="submit-btn"
            >
              <span v-if="isLoading">登录中...</span>
              <span v-else>登录</span>
            </button>
          </form>

          <!-- Footer -->
          <div class="modal-footer">
            <p>
              还没有账号？
              <router-link
                to="/register"
                class="link"
                @click="handleClose"
              >
                立即注册
              </router-link>
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
console.log('[LoginPromptModal] Script setup start')

import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import type { LoginRequest } from '@/api/auth'
import { getApiErrorMessage } from '@/utils/errorMessages'

console.log('[LoginPromptModal] Imports done')

const props = defineProps<{
  visible: boolean
  message?: string  // Custom message for context-aware prompts
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'success'): void
}>()

const authStore = useAuthStore()

const form = ref<LoginRequest>({
  email: '',
  password: ''
})

const isLoading = ref(false)
const error = ref<string | null>(null)

// Reset form when modal opens
watch(() => props.visible, (visible) => {
  if (visible) {
    form.value = { email: '', password: '' }
    error.value = null
  }
})

function handleClose() {
  console.log('[LoginPromptModal] handleClose called')
  emit('close')
}

async function handleEmailLogin() {
  console.log('[LoginPromptModal] handleEmailLogin called')
  isLoading.value = true
  error.value = null

  try {
    await authStore.login(form.value)
    emit('success')
    emit('close')
  } catch (err: any) {
    console.log('[LoginPromptModal] Login failed:', err)
    error.value = getApiErrorMessage(err, '登录失败，请重试')
  } finally {
    isLoading.value = false
  }
}

async function handleGoogleLogin() {
  console.log('[LoginPromptModal] handleGoogleLogin called')
  isLoading.value = true
  error.value = null

  try {
    const { authorization_url } = await authApi.getGmailAuthUrl()
    window.location.href = authorization_url
  } catch (err: any) {
    console.log('[LoginPromptModal] Google login failed:', err)
    error.value = getApiErrorMessage(err, '获取 Google 授权链接失败')
    isLoading.value = false
  }
}

console.log('[LoginPromptModal] Script setup complete')

async function handleWeChatLogin() {
  console.log('[LoginPromptModal] handleWeChatLogin called')
  isLoading.value = true
  error.value = null

  try {
    const { authorization_url } = await authApi.getWeChatAuthUrl()
    window.location.href = authorization_url
  } catch (err: any) {
    console.log('[LoginPromptModal] WeChat login failed:', err)
    error.value = getApiErrorMessage(err, '获取微信授权链接失败')
    isLoading.value = false
  }
}
</script>

<style scoped>
.login-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 1000;
}

.login-modal {
  position: relative;
  width: 100%;
  max-width: 420px;
  margin: 16px;
  padding: 32px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 16px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.close-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: #888;
  background: #252525;
  border: 1px solid #333;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.close-btn:hover {
  color: #fff;
  background: #333;
  border-color: #444;
}

.modal-header {
  text-align: center;
  margin-bottom: 28px;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 20px;
}

.logo-icon {
  width: 32px;
  height: 32px;
  color: #10b981;
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  letter-spacing: -0.02em;
}

.modal-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #fff;
}

.modal-subtitle {
  margin: 0;
  font-size: 14px;
  color: #888;
}

.oauth-section {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.oauth-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex: 1;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.oauth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.oauth-icon {
  width: 20px;
  height: 20px;
}

.oauth-google {
  color: #333;
  background: #fff;
}

.oauth-google:hover:not(:disabled) {
  background: #f5f5f5;
  transform: translateY(-1px);
}

.oauth-wechat {
  color: #fff;
  background: #07c160;
}

.oauth-wechat:hover:not(:disabled) {
  background: #06ad56;
  transform: translateY(-1px);
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #333;
}

.divider span {
  padding: 0 16px;
  font-size: 13px;
  color: #666;
}

.email-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 13px;
  font-weight: 500;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.form-input {
  padding: 12px 14px;
  font-size: 15px;
  color: #fff;
  background: #252525;
  border: 1px solid #333;
  border-radius: 10px;
  outline: none;
  transition: all 0.2s ease;
}

.form-input::placeholder {
  color: #555;
}

.form-input:focus {
  border-color: #10b981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.error-message {
  padding: 12px;
  font-size: 13px;
  color: #f87171;
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.2);
  border-radius: 8px;
}

.submit-btn {
  padding: 14px 20px;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: #10b981;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.submit-btn:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-footer {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #333;
  text-align: center;
}

.modal-footer p {
  margin: 0;
  font-size: 14px;
  color: #888;
}

.link {
  color: #10b981;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.link:hover {
  color: #34d399;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .login-modal,
.fade-leave-active .login-modal {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.fade-enter-from .login-modal,
.fade-leave-to .login-modal {
  opacity: 0;
  transform: scale(0.95) translateY(10px);
}
</style>
