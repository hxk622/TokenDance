<template>
  <div class="register-view">
    <!-- Background -->
    <div class="bg-layer">
      <div class="bg-gradient" />
      <div class="bg-pattern" />
      <!-- Floating orbs -->
      <div class="orb orb-1" />
      <div class="orb orb-2" />
      <div class="orb orb-3" />
    </div>

    <div class="register-container">
      <!-- Left: Branding -->
      <div class="branding-section">
        <div class="brand-content">
          <h1 class="brand-logo">TokenDance</h1>
          <p class="brand-tagline">可指挥的智能工作台</p>
          <div class="brand-features">
            <div class="feature-item">
              <svg class="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>全自动任务链，从 0 到 1 交付</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>安全可控的执行环境</span>
            </div>
            <div class="feature-item">
              <svg class="feature-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <span>团队协作与知识共享</span>
            </div>
          </div>
        </div>
        <p class="brand-footer">For the rest of the world</p>
      </div>

      <!-- Right: Register Form -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h2 class="form-title">创建账户</h2>
            <p class="form-subtitle">开始使用 TokenDance</p>
          </div>

          <form @submit.prevent="handleRegister" class="register-form">
            <!-- Error Alert -->
            <div v-if="error" class="error-alert">
              <svg class="error-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{{ error }}</span>
            </div>

            <!-- Username Field -->
            <div class="form-field">
              <label for="username" class="field-label">用户名</label>
              <div class="input-wrapper">
                <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <input
                  id="username"
                  v-model="form.username"
                  type="text"
                  required
                  autocomplete="username"
                  class="form-input"
                  placeholder="你的用户名"
                />
              </div>
              <p class="field-hint">4-20 个字符，支持字母、数字和下划线</p>
            </div>

            <!-- Email Field -->
            <div class="form-field">
              <label for="email" class="field-label">邮箱</label>
              <div class="input-wrapper">
                <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <input
                  id="email"
                  v-model="form.email"
                  type="email"
                  required
                  autocomplete="email"
                  class="form-input"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <!-- Password Field -->
            <div class="form-field">
              <label for="password" class="field-label">密码</label>
              <div class="input-wrapper">
                <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  required
                  autocomplete="new-password"
                  class="form-input"
                  placeholder="设置密码"
                />
              </div>
              <!-- Password Requirements -->
              <div class="password-requirements">
                <div class="req-item" :class="{ 'req-met': passwordRequirements.length }">
                  <svg class="req-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path v-if="passwordRequirements.length" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>至少 8 个字符</span>
                </div>
                <div class="req-item" :class="{ 'req-met': passwordRequirements.uppercase }">
                  <svg class="req-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path v-if="passwordRequirements.uppercase" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>包含大写字母</span>
                </div>
                <div class="req-item" :class="{ 'req-met': passwordRequirements.lowercase }">
                  <svg class="req-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path v-if="passwordRequirements.lowercase" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>包含小写字母</span>
                </div>
                <div class="req-item" :class="{ 'req-met': passwordRequirements.number }">
                  <svg class="req-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path v-if="passwordRequirements.number" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>包含数字</span>
                </div>
                <div class="req-item" :class="{ 'req-met': passwordRequirements.special }">
                  <svg class="req-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path v-if="passwordRequirements.special" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                    <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span>包含特殊字符</span>
                </div>
              </div>
            </div>

            <!-- Confirm Password Field -->
            <div class="form-field">
              <label for="confirmPassword" class="field-label">确认密码</label>
              <div class="input-wrapper">
                <svg class="input-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <input
                  id="confirmPassword"
                  v-model="form.confirmPassword"
                  type="password"
                  required
                  autocomplete="new-password"
                  class="form-input"
                  :class="{ 'input-error': passwordMismatch }"
                  placeholder="再次输入密码"
                />
              </div>
              <p v-if="passwordMismatch" class="field-error">两次密码不一致</p>
            </div>

            <!-- Terms Checkbox -->
            <div class="terms-field">
              <label class="terms-label">
                <input
                  v-model="form.agreeToTerms"
                  type="checkbox"
                  required
                  class="terms-checkbox"
                />
                <span class="terms-text">
                  我已阅读并同意
                  <a href="#" class="terms-link">服务条款</a>
                  和
                  <a href="#" class="terms-link">隐私政策</a>
                </span>
              </label>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="isLoading || passwordMismatch || !form.agreeToTerms || !isPasswordValid"
              class="submit-btn"
            >
              <svg v-if="isLoading" class="btn-spinner" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>{{ isLoading ? '创建中...' : '创建账户' }}</span>
            </button>
          </form>

          <!-- Login Link -->
          <p class="login-link">
            已有账户？
            <router-link to="/login" class="link-text">立即登录</router-link>
          </p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="register-footer">
      <p>随时接管 · 实时干预 · 沉淀复用</p>
    </footer>
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

const passwordRequirements = computed(() => {
  const password = form.value.password
  return {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
  }
})

const isPasswordValid = computed(() => {
  return Object.values(passwordRequirements.value).every(req => req)
})

const passwordMismatch = computed(() => {
  return form.value.password && form.value.confirmPassword && 
         form.value.password !== form.value.confirmPassword
})

async function handleRegister() {
  if (passwordMismatch.value) {
    error.value = '两次密码不一致'
    return
  }

  if (!isPasswordValid.value) {
    error.value = '密码不符合要求'
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
    router.push('/')
  } catch (err: any) {
    error.value = err.response?.data?.detail || '注册失败，请重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* ============================================
   Register View - TokenDance Design System
   工业实用 + 赛博朋克元素
   ============================================ */

.register-view {
  @apply relative min-h-screen flex flex-col;
  background: #0a0a0b;
}

/* Background Layer */
.bg-layer {
  @apply absolute inset-0 -z-10 overflow-hidden;
}

.bg-gradient {
  @apply absolute inset-0;
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.12), transparent),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(139, 92, 246, 0.08), transparent),
    radial-gradient(ellipse 50% 30% at 20% 80%, rgba(6, 182, 212, 0.06), transparent);
}

.bg-pattern {
  @apply absolute inset-0 opacity-[0.03];
  background-image:
    linear-gradient(to right, #fff 1px, transparent 1px),
    linear-gradient(to bottom, #fff 1px, transparent 1px);
  background-size: 24px 24px;
}

/* Floating Orbs */
.orb {
  @apply absolute rounded-full;
  filter: blur(60px);
  animation: orb-float 8s ease-in-out infinite;
}

.orb-1 {
  @apply w-64 h-64 bg-indigo-500/20;
  top: 10%;
  left: 15%;
  animation-delay: 0s;
}

.orb-2 {
  @apply w-48 h-48 bg-cyan-500/15;
  top: 60%;
  right: 20%;
  animation-delay: -2s;
}

.orb-3 {
  @apply w-32 h-32 bg-violet-500/10;
  bottom: 20%;
  left: 40%;
  animation-delay: -4s;
}

@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -30px) scale(1.05); }
  50% { transform: translate(-10px, 20px) scale(0.95); }
  75% { transform: translate(15px, 10px) scale(1.02); }
}

/* Main Container */
.register-container {
  @apply flex-1 flex items-center justify-center px-6 py-8;
  @apply flex-col lg:flex-row gap-12 lg:gap-24;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

/* Branding Section */
.branding-section {
  @apply flex flex-col justify-between;
  @apply text-center lg:text-left;
}

.brand-content {
  @apply space-y-6;
}

.brand-logo {
  @apply text-4xl lg:text-5xl font-bold text-white tracking-tight;
  font-family: 'Satoshi', system-ui, sans-serif;
}

.brand-tagline {
  @apply text-lg lg:text-xl text-gray-400;
}

.brand-features {
  @apply space-y-4 mt-8;
  @apply hidden lg:block;
}

.feature-item {
  @apply flex items-center gap-3 text-gray-300;
}

.feature-icon {
  @apply w-5 h-5 text-indigo-400;
}

.brand-footer {
  @apply text-sm text-gray-500 mt-12;
  @apply hidden lg:block;
}

/* Form Section */
.form-section {
  @apply w-full max-w-md;
}

.form-card {
  @apply p-8 rounded-2xl;
  background: rgba(20, 20, 21, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
}

.form-header {
  @apply mb-6 text-center;
}

.form-title {
  @apply text-2xl font-semibold text-white mb-2;
  font-family: 'Satoshi', system-ui, sans-serif;
}

.form-subtitle {
  @apply text-sm text-gray-400;
}

/* Register Form */
.register-form {
  @apply space-y-4;
}

/* Error Alert */
.error-alert {
  @apply flex items-center gap-2 p-3 rounded-lg;
  @apply text-sm text-red-300;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-icon {
  @apply w-5 h-5 flex-shrink-0;
}

/* Form Field */
.form-field {
  @apply space-y-2;
}

.field-label {
  @apply block text-sm font-medium text-gray-300;
}

.input-wrapper {
  @apply relative flex items-center;
}

.input-icon {
  @apply absolute left-3 w-5 h-5 text-gray-500 pointer-events-none;
}

.form-input {
  @apply w-full pl-10 pr-4 py-2.5 rounded-xl;
  @apply text-white placeholder-gray-500;
  @apply transition-all duration-200;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.form-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(99, 102, 241, 0.5);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.form-input.input-error {
  border-color: rgba(239, 68, 68, 0.5);
}

.form-input.input-error:focus {
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
}

.field-hint {
  @apply text-xs text-gray-500;
}

.field-error {
  @apply text-xs text-red-400;
}

/* Password Requirements */
.password-requirements {
  @apply mt-3 space-y-1.5 pl-1;
}

.req-item {
  @apply flex items-center gap-2 text-xs text-gray-500;
  transition: color 0.2s ease;
}

.req-item.req-met {
  @apply text-emerald-400;
}

.req-icon {
  @apply w-3.5 h-3.5;
}

/* Terms Checkbox */
.terms-field {
  @apply pt-2;
}

.terms-label {
  @apply flex items-start gap-3 cursor-pointer;
}

.terms-checkbox {
  @apply mt-0.5 w-4 h-4 rounded;
  @apply bg-transparent border border-gray-600;
  @apply cursor-pointer;
  accent-color: #6366f1;
}

.terms-checkbox:checked {
  @apply bg-indigo-600 border-indigo-600;
}

.terms-text {
  @apply text-sm text-gray-400;
}

.terms-link {
  @apply text-white hover:text-indigo-300 transition-colors duration-200;
}

/* Submit Button */
.submit-btn {
  @apply w-full flex items-center justify-center gap-2;
  @apply py-3 px-4 rounded-xl;
  @apply text-base font-medium text-gray-900;
  @apply cursor-pointer transition-all duration-200;
  background: white;
}

.submit-btn:hover:not(:disabled) {
  background: #f3f4f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.15);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}

.btn-spinner {
  @apply w-5 h-5 animate-spin;
}

/* Login Link */
.login-link {
  @apply mt-6 text-center text-sm text-gray-400;
}

.link-text {
  @apply font-medium text-white hover:text-indigo-300 transition-colors duration-200;
}

/* Footer */
.register-footer {
  @apply py-6 text-center;
}

.register-footer p {
  @apply text-sm text-gray-500;
}

/* Animations */
.form-card {
  animation: card-appear 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes card-appear {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.branding-section {
  animation: brand-appear 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes brand-appear {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .register-container {
    @apply py-6;
  }
  
  .brand-logo {
    @apply text-3xl;
  }
  
  .brand-tagline {
    @apply text-base mb-4;
  }
  
  .form-card {
    @apply p-6;
  }
}
</style>
