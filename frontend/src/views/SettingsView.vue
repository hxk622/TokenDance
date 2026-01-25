<script setup lang="ts">
/**
 * SettingsView - 设置页面
 */
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore, type ThemeMode } from '@/stores/theme'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import { 
  Settings, Shield, Bell, Palette, Globe, Key, Smartphone, 
  Sun, Moon, Monitor, Check
} from 'lucide-vue-next'

// Props for initial tab
interface Props {
  initialTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  initialTab: 'general'
})

const route = useRoute()
const authStore = useAuthStore()
const themeStore = useThemeStore()

// Tabs
const tabs = [
  { id: 'general', label: '通用', icon: Settings },
  { id: 'security', label: '安全', icon: Shield },
  { id: 'notifications', label: '通知', icon: Bell },
  { id: 'appearance', label: '外观', icon: Palette },
]

// Active tab
const activeTab = ref(props.initialTab)

// Theme options
const themeOptions: { mode: ThemeMode; label: string; icon: any }[] = [
  { mode: 'light', label: '浅色', icon: Sun },
  { mode: 'dark', label: '深色', icon: Moon },
  { mode: 'system', label: '跟随系统', icon: Monitor },
]

// Language options
const languageOptions = [
  { code: 'zh-CN', label: '简体中文' },
  { code: 'en-US', label: 'English' },
]

// Settings state
const settings = ref({
  language: 'zh-CN',
  emailNotifications: true,
  pushNotifications: false,
  marketingEmails: false,
  twoFactorEnabled: false,
})

// Methods
function selectTab(tabId: string) {
  activeTab.value = tabId
}

function selectTheme(mode: ThemeMode) {
  themeStore.setMode(mode)
}

function toggleSetting(key: keyof typeof settings.value) {
  if (typeof settings.value[key] === 'boolean') {
    (settings.value[key] as boolean) = !settings.value[key]
  }
}

onMounted(() => {
  // Check route for initial tab
  if (route.name === 'SecuritySettings') {
    activeTab.value = 'security'
  }
})
</script>

<template>
  <div class="settings-page">
    <AnyHeader />
    <AnySidebar />
    
    <main class="settings-main">
      <div class="settings-container">
        <h1 class="page-title">
          设置
        </h1>

        <div class="settings-layout">
          <!-- Sidebar navigation -->
          <nav class="settings-nav">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              :class="['nav-item', { active: activeTab === tab.id }]"
              @click="selectTab(tab.id)"
            >
              <component
                :is="tab.icon"
                class="w-4 h-4"
              />
              <span>{{ tab.label }}</span>
            </button>
          </nav>

          <!-- Content area -->
          <div class="settings-content">
            <!-- General Settings -->
            <div
              v-if="activeTab === 'general'"
              class="settings-section"
            >
              <h2 class="section-title">
                通用设置
              </h2>
              
              <!-- Language -->
              <div class="setting-item">
                <div class="setting-info">
                  <Globe class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">语言</span>
                    <span class="setting-desc">选择界面显示语言</span>
                  </div>
                </div>
                <select
                  v-model="settings.language"
                  class="setting-select"
                >
                  <option
                    v-for="lang in languageOptions"
                    :key="lang.code"
                    :value="lang.code"
                  >
                    {{ lang.label }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Security Settings -->
            <div
              v-if="activeTab === 'security'"
              class="settings-section"
            >
              <h2 class="section-title">
                安全设置
              </h2>
              
              <!-- Change Password -->
              <div class="setting-item clickable">
                <div class="setting-info">
                  <Key class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">修改密码</span>
                    <span class="setting-desc">定期更改密码以保护账户安全</span>
                  </div>
                </div>
                <button class="setting-btn">
                  修改
                </button>
              </div>

              <!-- Two-Factor Auth -->
              <div class="setting-item">
                <div class="setting-info">
                  <Smartphone class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">两步验证</span>
                    <span class="setting-desc">为您的账户添加额外的安全保护</span>
                  </div>
                </div>
                <button
                  :class="['toggle-btn', { active: settings.twoFactorEnabled }]"
                  @click="toggleSetting('twoFactorEnabled')"
                >
                  <span class="toggle-slider" />
                </button>
              </div>

              <!-- Active Sessions -->
              <div class="setting-item clickable">
                <div class="setting-info">
                  <Shield class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">活跃会话</span>
                    <span class="setting-desc">查看和管理您的登录设备</span>
                  </div>
                </div>
                <button class="setting-btn">
                  查看
                </button>
              </div>
            </div>

            <!-- Notification Settings -->
            <div
              v-if="activeTab === 'notifications'"
              class="settings-section"
            >
              <h2 class="section-title">
                通知设置
              </h2>
              
              <!-- Email Notifications -->
              <div class="setting-item">
                <div class="setting-info">
                  <Bell class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">邮件通知</span>
                    <span class="setting-desc">接收任务完成、系统更新等邮件通知</span>
                  </div>
                </div>
                <button
                  :class="['toggle-btn', { active: settings.emailNotifications }]"
                  @click="toggleSetting('emailNotifications')"
                >
                  <span class="toggle-slider" />
                </button>
              </div>

              <!-- Push Notifications -->
              <div class="setting-item">
                <div class="setting-info">
                  <Bell class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">推送通知</span>
                    <span class="setting-desc">接收浏览器推送通知</span>
                  </div>
                </div>
                <button
                  :class="['toggle-btn', { active: settings.pushNotifications }]"
                  @click="toggleSetting('pushNotifications')"
                >
                  <span class="toggle-slider" />
                </button>
              </div>

              <!-- Marketing -->
              <div class="setting-item">
                <div class="setting-info">
                  <Bell class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">营销邮件</span>
                    <span class="setting-desc">接收产品更新和优惠信息</span>
                  </div>
                </div>
                <button
                  :class="['toggle-btn', { active: settings.marketingEmails }]"
                  @click="toggleSetting('marketingEmails')"
                >
                  <span class="toggle-slider" />
                </button>
              </div>
            </div>

            <!-- Appearance Settings -->
            <div
              v-if="activeTab === 'appearance'"
              class="settings-section"
            >
              <h2 class="section-title">
                外观设置
              </h2>
              
              <!-- Theme -->
              <div class="setting-item vertical">
                <div class="setting-info">
                  <Palette class="w-5 h-5" />
                  <div class="setting-text">
                    <span class="setting-label">主题</span>
                    <span class="setting-desc">选择界面主题风格</span>
                  </div>
                </div>
                <div class="theme-options">
                  <button
                    v-for="opt in themeOptions"
                    :key="opt.mode"
                    :class="['theme-option', { active: themeStore.mode === opt.mode }]"
                    @click="selectTheme(opt.mode)"
                  >
                    <component
                      :is="opt.icon"
                      class="w-5 h-5"
                    />
                    <span>{{ opt.label }}</span>
                    <Check
                      v-if="themeStore.mode === opt.mode"
                      class="w-4 h-4 check-icon"
                    />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: var(--any-bg-primary);
}

.settings-main {
  margin-left: 56px;
  padding: 80px 24px 40px;
}

.settings-container {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin-bottom: 24px;
}

/* Layout */
.settings-layout {
  display: flex;
  gap: 32px;
}

/* Nav */
.settings-nav {
  width: 200px;
  flex-shrink: 0;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: transparent;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 150ms ease;
}

.nav-item:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.nav-item.active {
  background: var(--any-bg-secondary);
  color: var(--any-text-primary);
  font-weight: 500;
}

/* Content */
.settings-content {
  flex: 1;
  min-width: 0;
}

.settings-section {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  padding: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0 0 20px;
}

/* Setting items */
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid var(--any-border);
}

.setting-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.setting-item:first-of-type {
  padding-top: 0;
}

.setting-item.vertical {
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}

.setting-item.clickable {
  cursor: pointer;
  margin: 0 -16px;
  padding-left: 16px;
  padding-right: 16px;
  border-radius: 8px;
}

.setting-item.clickable:hover {
  background: var(--any-bg-hover);
}

.setting-info {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: var(--any-text-secondary);
}

.setting-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.setting-desc {
  font-size: 13px;
  color: var(--any-text-muted);
}

/* Select */
.setting-select {
  padding: 8px 12px;
  font-size: 14px;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  cursor: pointer;
}

/* Button */
.setting-btn {
  padding: 6px 14px;
  font-size: 13px;
  color: var(--any-text-secondary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 150ms ease;
}

.setting-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Toggle */
.toggle-btn {
  width: 44px;
  height: 24px;
  padding: 2px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 200ms ease;
}

.toggle-btn.active {
  background: var(--td-state-thinking);
  border-color: var(--td-state-thinking);
}

.toggle-slider {
  display: block;
  width: 18px;
  height: 18px;
  background: white;
  border-radius: 50%;
  transition: transform 200ms ease;
}

.toggle-btn.active .toggle-slider {
  transform: translateX(20px);
}

/* Theme options */
.theme-options {
  display: flex;
  gap: 12px;
  width: 100%;
}

.theme-option {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  font-size: 14px;
  color: var(--any-text-secondary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 150ms ease;
  position: relative;
}

.theme-option:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.theme-option.active {
  border-color: var(--td-state-thinking);
  background: rgba(0, 217, 255, 0.1);
  color: var(--td-state-thinking);
}

.check-icon {
  position: absolute;
  top: 8px;
  right: 8px;
  color: var(--td-state-thinking);
}

/* Responsive */
@media (max-width: 768px) {
  .settings-main {
    margin-left: 0;
    padding: 72px 16px 24px;
  }

  .settings-layout {
    flex-direction: column;
    gap: 16px;
  }

  .settings-nav {
    width: 100%;
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 8px;
  }

  .nav-item {
    flex-shrink: 0;
  }

  .theme-options {
    flex-direction: column;
  }
}
</style>
