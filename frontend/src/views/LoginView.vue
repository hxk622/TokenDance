<template>
  <div class="login-view">
    <!-- Background -->
    <div class="bg-layer">
      <div class="bg-gradient" />
      <div class="bg-pattern" />
      <!-- Animated orbs with status colors -->
      <div class="orb orb-active" />
      <div class="orb orb-success" />
      <div class="orb orb-pending" />
    </div>

    <div class="login-container">
      <!-- Left: Branding -->
      <div class="branding-section">
        <div class="brand-content">
          <h1 class="brand-logo">
            TokenDance
          </h1>
          <p class="brand-tagline">
            可指挥的智能工作台
          </p>
          <div class="brand-features">
            <div class="feature-item">
              <div class="feature-icon-wrapper feature-icon--transparency">
                <svg
                  class="feature-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                  />
                </svg>
              </div>
              <div class="feature-text">
                <span class="feature-title">Transparency</span>
                <span class="feature-desc">透明可见的执行过程</span>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon-wrapper feature-icon--controllability">
                <svg
                  class="feature-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <div class="feature-text">
                <span class="feature-title">Controllability</span>
                <span class="feature-desc">随时接管和干预</span>
              </div>
            </div>
            <div class="feature-item">
              <div class="feature-icon-wrapper feature-icon--persistence">
                <svg
                  class="feature-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </div>
              <div class="feature-text">
                <span class="feature-title">Persistence</span>
                <span class="feature-desc">经验沉淀与复用</span>
              </div>
            </div>
          </div>
        </div>
        <p class="brand-footer">
          和 Agent 一起完成任务，而不是让 Agent 帮你
        </p>
      </div>

      <!-- Right: Login Form -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <h2 class="form-title">
              登录账户
            </h2>
            <p class="form-subtitle">
              继续使用 TokenDance
            </p>
          </div>

          <form
            class="login-form"
            @submit.prevent="handleLogin"
          >
            <!-- Error Alert -->
            <div
              v-if="error"
              class="error-alert"
            >
              <svg
                class="error-icon"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>{{ error }}</span>
            </div>

            <!-- Email Field -->
            <div class="form-field">
              <label
                for="email"
                class="field-label"
              >邮箱</label>
              <div class="input-wrapper">
                <svg
                  class="input-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
                <input
                  id="email"
                  v-model="form.email"
                  type="email"
                  required
                  autocomplete="email"
                  class="form-input"
                  placeholder="you@example.com"
                >
              </div>
            </div>

            <!-- Password Field -->
            <div class="form-field">
              <label
                for="password"
                class="field-label"
              >密码</label>
              <div class="input-wrapper">
                <svg
                  class="input-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
                <input
                  id="password"
                  v-model="form.password"
                  type="password"
                  required
                  autocomplete="current-password"
                  class="form-input"
                  placeholder="输入密码"
                >
              </div>
            </div>

            <!-- Submit Button -->
            <button
              type="submit"
              :disabled="isLoading"
              class="submit-btn"
            >
              <svg
                v-if="isLoading"
                class="btn-spinner"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                  fill="none"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>{{ isLoading ? '登录中...' : '登录' }}</span>
            </button>

            <!-- Divider -->
            <div class="divider">
              <span class="divider-text">或使用第三方登录</span>
            </div>

            <!-- OAuth Buttons -->
            <div class="oauth-buttons">
              <button
                type="button"
                :disabled="isLoading"
                class="oauth-btn oauth-btn--wechat"
                @click="handleWeChatLogin"
              >
                <svg
                  class="oauth-icon"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05a5.79 5.79 0 01-.271-1.74c0-3.562 3.4-6.446 7.562-6.446.197 0 .391.012.585.025-.798-3.328-4.282-5.771-8.685-5.771zm-2.11 4.96a.925.925 0 11.002-1.85.925.925 0 01-.001 1.85zm4.877 0a.925.925 0 110-1.85.925.925 0 010 1.85z" />
                  <path d="M23.636 14.576c0-3.263-3.268-5.913-7.295-5.913-4.025 0-7.293 2.65-7.293 5.913s3.268 5.912 7.293 5.912c.858 0 1.68-.11 2.454-.308a.725.725 0 01.6.082l1.6.937a.27.27 0 00.14.045.243.243 0 00.242-.244c0-.06-.024-.12-.04-.178l-.327-1.244a.496.496 0 01.179-.558c1.537-1.137 2.447-2.814 2.447-4.444zm-9.782-1.061a.777.777 0 110-1.554.777.777 0 010 1.554zm4.974 0a.777.777 0 110-1.554.777.777 0 010 1.554z" />
                </svg>
                <span>微信</span>
              </button>
              <button
                type="button"
                :disabled="isLoading"
                class="oauth-btn oauth-btn--google"
                @click="handleGmailLogin"
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
            </div>
          </form>

          <!-- Register Link -->
          <p class="register-link">
            还没有账户？
            <router-link
              to="/register"
              class="link-text"
            >
              立即注册
            </router-link>
          </p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="login-footer">
      <p>随时接管 · 实时干预 · 沉淀复用</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'
import type { LoginRequest } from '@/api/auth'
import { getApiErrorMessage } from '@/utils/errorMessages'

const router = useRouter()
const route = useRoute()
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
    router.push('/')
  } catch (err: any) {
    console.log('[LoginView] Login failed:', err)
    error.value = getApiErrorMessage(err, '登录失败，请重试')
  } finally {
    isLoading.value = false
  }
}

async function handleWeChatLogin() {
  isLoading.value = true
  error.value = null

  try {
    const { authorization_url } = await authApi.getWeChatAuthUrl()
    window.location.href = authorization_url
  } catch (err: any) {
    console.log('[LoginView] WeChat login failed:', err)
    error.value = getApiErrorMessage(err, '获取微信授权链接失败')
    isLoading.value = false
  }
}

async function handleGmailLogin() {
  isLoading.value = true
  error.value = null

  try {
    const { authorization_url } = await authApi.getGmailAuthUrl()
    window.location.href = authorization_url
  } catch (err: any) {
    console.log('[LoginView] Gmail login failed:', err)
    error.value = getApiErrorMessage(err, '获取 Google 授权链接失败')
    isLoading.value = false
  }
}

onMounted(async () => {
  const code = route.query.code as string
  const provider = route.query.provider as string

  if (code) {
    isLoading.value = true
    error.value = null

    try {
      if (provider === 'wechat') {
        await authStore.loginWithWeChat(code)
      } else if (provider === 'gmail') {
        await authStore.loginWithGmail(code)
      }
      router.push('/')
    } catch (err: any) {
      console.log('[LoginView] OAuth callback failed:', err)
      error.value = getApiErrorMessage(err, '第三方登录失败，请重试')
    } finally {
      isLoading.value = false
    }
  }
})
</script>

<style scoped>
/* ============================================
   Login View - TokenDance Design System v2.0.0
   Based on: DESIGN-SYSTEM.md & DESIGN-PRINCIPLES.md
   ============================================ */

/* CSS Variables from Design System */
.login-view {
  /* Color System */
  --bg-primary: #0a0a0b;
  --bg-secondary: #141415;
  --bg-tertiary: #1c1c1e;
  --bg-elevated: #242426;
  
  --text-primary: #ffffff;
  --text-secondary: #a1a1aa;
  --text-tertiary: #71717a;
  
  --accent-primary: #00D9FF;  /* #00D9FF */
  --accent-hover: #33E1FF;
  --accent-gradient: linear-gradient(135deg, #00B8D9 0%, #00D9FF 100%);
  
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  
  --border-default: #27272a;
  --border-hover: #3f3f46;
  
  /* Status Colors (from EXECUTION-PAGE-LAYOUT.md) */
  --color-node-active: #00D9FF;
  --color-node-active-glow: rgba(0, 217, 255, 0.5);
  --color-node-success: #00FF88;
  --color-node-success-glow: rgba(0, 255, 136, 0.3);
  --color-node-pending: #FFB800;
  --color-node-pending-glow: rgba(255, 184, 0, 0.4);
  
  /* Spacing */
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
  
  /* Border Radius */
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* Transitions */
  --transition-fast: 150ms;
  --transition-standard: 200ms;
  --transition-slow: 300ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-bounce: cubic-bezier(0.34, 1.56, 0.64, 1);
  
  /* Glassmorphism */
  --glass-bg-dark: rgba(20, 20, 21, 0.8);
}

.login-view {
  @apply relative min-h-screen flex flex-col;
  background: var(--bg-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Background Layer */
.bg-layer {
  @apply absolute inset-0 -z-10 overflow-hidden;
}

.bg-gradient {
  @apply absolute inset-0;
  /* Using design system accent colors */
  background:
    radial-gradient(ellipse 80% 50% at 50% -20%, rgba(139, 92, 246, 0.12), transparent),
    radial-gradient(ellipse 60% 40% at 80% 50%, rgba(99, 102, 241, 0.08), transparent),
    radial-gradient(ellipse 50% 30% at 20% 80%, rgba(139, 92, 246, 0.06), transparent);
}

.bg-pattern {
  @apply absolute inset-0 opacity-[0.03];
  background-image:
    linear-gradient(to right, #fff 1px, transparent 1px),
    linear-gradient(to bottom, #fff 1px, transparent 1px);
  background-size: 24px 24px;
}

/* Floating Orbs - Using Status Colors */
.orb {
  @apply absolute rounded-full;
  filter: blur(60px);
  animation: orb-float 8s ease-in-out infinite;
}

/* Active node - Cyan pulse (Agent computing) */
.orb-active {
  width: 256px;
  height: 256px;
  top: 10%;
  left: 15%;
  background: var(--color-node-active);
  opacity: 0.2;
  animation: pulse-breath 1.5s ease-in-out infinite, orb-float 8s ease-in-out infinite;
}

/* Success node - Green lock (Completed) */
.orb-success {
  width: 192px;
  height: 192px;
  top: 60%;
  right: 20%;
  background: var(--color-node-success);
  opacity: 0.15;
  animation-delay: -2s;
}

/* Pending node - Amber pause (Waiting) */
.orb-pending {
  width: 128px;
  height: 128px;
  bottom: 20%;
  left: 40%;
  background: var(--color-node-pending);
  opacity: 0.1;
  animation-delay: -4s;
}

@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(20px, -30px) scale(1.05); }
  50% { transform: translate(-10px, 20px) scale(0.95); }
  75% { transform: translate(15px, 10px) scale(1.02); }
}

/* Pulse Breath Animation (from EXECUTION-PAGE-LAYOUT.md) */
@keyframes pulse-breath {
  0%, 100% {
    transform: scale(1);
    opacity: 0.2;
    box-shadow: 0 0 20px var(--color-node-active-glow);
  }
  50% {
    transform: scale(1.1);
    opacity: 0.15;
    box-shadow: 0 0 40px var(--color-node-active-glow);
  }
}

/* Main Container */
.login-container {
  @apply flex-1 flex items-center justify-center;
  @apply flex-col lg:flex-row gap-12 lg:gap-24;
  padding: var(--space-8) var(--space-6);
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
  font-size: 48px;  /* --text-2xl equivalent */
  line-height: 1.25;  /* --leading-tight */
  font-weight: 700;  /* --font-bold */
  color: var(--text-primary);
  letter-spacing: -0.02em;
  font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
}

@media (min-width: 1024px) {
  .brand-logo {
    font-size: 56px;
  }
}

.brand-tagline {
  font-size: 18px;  /* --text-lg */
  color: var(--text-secondary);
}

@media (min-width: 1024px) {
  .brand-tagline {
    font-size: 20px;  /* --text-xl */
  }
}

.brand-features {
  margin-top: var(--space-8);
  display: none;
}

@media (min-width: 1024px) {
  .brand-features {
    display: flex;
    flex-direction: column;
    gap: var(--space-6);
  }
}

/* Feature Items - Enhanced with design system */
.feature-item {
  @apply flex items-start gap-4;
  transition: transform var(--transition-standard) var(--ease-default);
}

.feature-item:hover {
  transform: translateX(4px);
}

.feature-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-slow) var(--ease-bounce);
}

.feature-icon-wrapper.feature-icon--transparency {
  background: rgba(0, 217, 255, 0.1);
  border: 1px solid rgba(0, 217, 255, 0.2);
}

.feature-icon-wrapper.feature-icon--controllability {
  background: rgba(139, 92, 246, 0.1);
  border: 1px solid rgba(139, 92, 246, 0.2);
}

.feature-icon-wrapper.feature-icon--persistence {
  background: rgba(0, 255, 136, 0.1);
  border: 1px solid rgba(0, 255, 136, 0.2);
}

.feature-item:hover .feature-icon-wrapper {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
}

.feature-icon-wrapper.feature-icon--transparency:hover {
  box-shadow: 0 0 20px var(--color-node-active-glow);
}

.feature-icon-wrapper.feature-icon--controllability:hover {
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
}

.feature-icon-wrapper.feature-icon--persistence:hover {
  box-shadow: 0 0 20px var(--color-node-success-glow);
}

.feature-icon {
  width: 20px;
  height: 20px;
  color: currentColor;
}

.feature-icon-wrapper.feature-icon--transparency .feature-icon {
  color: var(--color-node-active);
}

.feature-icon-wrapper.feature-icon--controllability .feature-icon {
  color: var(--accent-primary);
}

.feature-icon-wrapper.feature-icon--persistence .feature-icon {
  color: var(--color-node-success);
}

.feature-text {
  @apply flex flex-col gap-1;
}

.feature-title {
  font-size: 14px;  /* --text-sm */
  font-weight: 600;  /* --font-semibold */
  color: var(--text-primary);
}

.feature-desc {
  font-size: 14px;  /* --text-sm */
  color: var(--text-tertiary);
}

.brand-footer {
  font-size: 12px;  /* --text-xs */
  color: var(--text-tertiary);
  margin-top: var(--space-12);
  display: none;
}

@media (min-width: 1024px) {
  .brand-footer {
    display: block;
  }
}

/* Form Section */
.form-section {
  @apply w-full max-w-md;
}

.form-card {
  padding: var(--space-8);
  border-radius: var(--radius-xl);
  background: var(--glass-bg-dark);
  border: 1px solid var(--border-default);
  backdrop-filter: blur(20px) saturate(180%);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3);
}

.form-header {
  margin-bottom: var(--space-8);
  text-align: center;
}

.form-title {
  font-size: 24px;  /* --text-2xl */
  font-weight: 600;  /* --font-semibold */
  color: var(--text-primary);
  margin-bottom: var(--space-2);
  font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
}

.form-subtitle {
  font-size: 14px;  /* --text-sm */
  color: var(--text-secondary);
}

/* Login Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;  /* --space-5 */
}

/* Error Alert */
.error-alert {
  @apply flex items-center gap-2;
  padding: 12px;  /* --space-3 */
  border-radius: var(--radius-md);
  font-size: 14px;  /* --text-sm */
  color: #fca5a5;  /* red-300 */
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* Form Field */
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  display: block;
  font-size: 14px;  /* --text-sm */
  font-weight: 500;  /* --font-medium */
  color: var(--text-secondary);
}

.input-wrapper {
  @apply relative flex items-center;
}

.input-icon {
  position: absolute;
  left: 12px;  /* --space-3 */
  width: 20px;
  height: 20px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.form-input {
  width: 100%;
  padding: 12px 16px 12px 40px;  /* --space-3 --space-4 */
  border-radius: var(--radius-lg);
  font-size: 16px;  /* --text-base */
  color: var(--text-primary);
  background: var(--bg-tertiary);
  border: 1px solid var(--border-default);
  transition: all var(--transition-standard) var(--ease-default);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.form-input:focus {
  outline: none;
  background: var(--bg-elevated);
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

/* Submit Button - Using accent gradient */
.submit-btn {
  @apply w-full flex items-center justify-center;
  gap: var(--space-2);
  padding: 12px var(--space-4);  /* --space-3 */
  border-radius: var(--radius-lg);
  font-size: 16px;  /* --text-base */
  font-weight: 500;  /* --font-medium */
  color: #ffffff;
  background: var(--accent-gradient);
  border: none;
  cursor: pointer;
  transition: all var(--transition-standard) var(--ease-default);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(139, 92, 246, 0.3);
  background: var(--accent-hover);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Divider */
.divider {
  @apply relative flex items-center;
  padding: var(--space-4) 0;
}

.divider::before,
.divider::after {
  content: '';
  @apply flex-1;
  height: 1px;
  background: var(--border-default);
}

.divider-text {
  padding: 0 var(--space-4);
  font-size: 14px;  /* --text-sm */
  color: var(--text-tertiary);
}

/* OAuth Buttons */
.oauth-buttons {
  @apply grid grid-cols-2;
  gap: 12px;  /* --space-3 */
}

.oauth-btn {
  @apply flex items-center justify-center;
  gap: var(--space-2);
  padding: 12px var(--space-4);  /* --space-3 */
  border-radius: var(--radius-lg);
  font-size: 14px;  /* --text-sm */
  font-weight: 500;  /* --font-medium */
  cursor: pointer;
  border: 1px solid var(--border-default);
  transition: all var(--transition-fast) var(--ease-default);
}

.oauth-btn:hover:not(:disabled) {
  border-color: var(--border-hover);
  transform: translateY(-1px);
}

.oauth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.oauth-btn--wechat {
  color: var(--text-primary);
  background: rgba(7, 193, 96, 0.1);
  border-color: rgba(7, 193, 96, 0.3);
}

.oauth-btn--wechat:hover:not(:disabled) {
  background: rgba(7, 193, 96, 0.2);
  border-color: rgba(7, 193, 96, 0.5);
}

.oauth-btn--google {
  color: var(--text-primary);
  background: var(--bg-tertiary);
}

.oauth-btn--google:hover:not(:disabled) {
  background: var(--bg-elevated);
  border-color: var(--border-hover);
}

.oauth-icon {
  width: 20px;
  height: 20px;
}

/* Register Link */
.register-link {
  margin-top: var(--space-6);
  text-align: center;
  font-size: 14px;  /* --text-sm */
  color: var(--text-secondary);
}

.link-text {
  font-weight: 500;  /* --font-medium */
  color: var(--accent-primary);
  transition: color var(--transition-fast) var(--ease-default);
}

.link-text:hover {
  color: var(--accent-hover);
}

/* Footer */
.login-footer {
  padding: var(--space-6) 0;
  text-align: center;
}

.login-footer p {
  font-size: 12px;  /* --text-xs */
  color: var(--text-tertiary);
}

/* Animations - Staggered reveal */
.form-card {
  animation: card-appear 0.5s var(--ease-default) forwards;
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
  animation: brand-appear 0.6s var(--ease-default) forwards;
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

/* Responsive Design (matching design system breakpoints) */

/* md: 768px - Tablet portrait */
@media (max-width: 768px) {
  .login-container {
    padding: var(--space-6) var(--space-4);
  }
  
  .brand-logo {
    font-size: 36px;
  }
  
  .brand-tagline {
    font-size: 16px;
    margin-bottom: var(--space-6);
  }
  
  .form-card {
    padding: var(--space-6);
  }
}

/* lg: 1024px - Tablet landscape/small notebook */
@media (min-width: 1024px) and (max-width: 1279px) {
  .login-container {
    gap: var(--space-8);
  }
}
</style>
