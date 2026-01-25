<script setup lang="ts">
/**
 * ProfileView - 个人资料页面
 */
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AnyHeader from '@/components/common/AnyHeader.vue'
import AnySidebar from '@/components/common/AnySidebar.vue'
import { 
  User, Mail, Phone, MapPin, Calendar, Edit2, Camera, Save, X
} from 'lucide-vue-next'

const authStore = useAuthStore()

// Edit mode
const isEditing = ref(false)
const isSaving = ref(false)

// Form data
const formData = ref({
  display_name: authStore.user?.display_name || '',
  bio: authStore.user?.bio || '',
  phone: authStore.user?.phone || '',
  location: authStore.user?.location || '',
})

// Avatar upload
const avatarInput = ref<HTMLInputElement | null>(null)

// User info computed
const joinDate = computed(() => {
  if (!authStore.user?.created_at) return '未知'
  return new Date(authStore.user.created_at).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
})

// Methods
function startEdit() {
  isEditing.value = true
  formData.value = {
    display_name: authStore.user?.display_name || '',
    bio: authStore.user?.bio || '',
    phone: authStore.user?.phone || '',
    location: authStore.user?.location || '',
  }
}

function cancelEdit() {
  isEditing.value = false
}

async function saveProfile() {
  isSaving.value = true
  try {
    // TODO: Call API to update profile
    console.log('Saving profile:', formData.value)
    await new Promise(resolve => setTimeout(resolve, 1000))
    isEditing.value = false
  } catch (error) {
    console.error('Failed to save profile:', error)
  } finally {
    isSaving.value = false
  }
}

function triggerAvatarUpload() {
  avatarInput.value?.click()
}

async function handleAvatarChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  
  // TODO: Upload avatar
  console.log('Uploading avatar:', file.name)
}
</script>

<template>
  <div class="profile-page">
    <AnyHeader />
    <AnySidebar />
    
    <main class="profile-main">
      <div class="profile-container">
        <h1 class="page-title">
          个人资料
        </h1>

        <!-- Profile Card -->
        <div class="profile-card">
          <!-- Avatar Section -->
          <div class="avatar-section">
            <div class="avatar-wrapper">
              <div
                v-if="authStore.user?.avatar_url"
                class="avatar-img"
              >
                <img
                  :src="authStore.user.avatar_url"
                  alt="avatar"
                >
              </div>
              <div
                v-else
                class="avatar-placeholder"
              >
                {{ authStore.user?.display_name?.charAt(0) || 'U' }}
              </div>
              <button
                class="avatar-edit-btn"
                title="更换头像"
                @click="triggerAvatarUpload"
              >
                <Camera class="w-4 h-4" />
              </button>
              <input
                ref="avatarInput"
                type="file"
                accept="image/*"
                class="hidden"
                @change="handleAvatarChange"
              >
            </div>
            <div class="avatar-info">
              <h2 class="user-display-name">
                {{ authStore.user?.display_name || authStore.user?.username }}
              </h2>
              <p class="user-email">
                {{ authStore.user?.email }}
              </p>
            </div>
          </div>

          <!-- Info Section -->
          <div class="info-section">
            <div class="section-header">
              <h3>基本信息</h3>
              <button
                v-if="!isEditing"
                class="edit-btn"
                @click="startEdit"
              >
                <Edit2 class="w-4 h-4" />
                <span>编辑</span>
              </button>
              <div
                v-else
                class="edit-actions"
              >
                <button
                  class="cancel-btn"
                  :disabled="isSaving"
                  @click="cancelEdit"
                >
                  <X class="w-4 h-4" />
                  <span>取消</span>
                </button>
                <button
                  class="save-btn"
                  :disabled="isSaving"
                  @click="saveProfile"
                >
                  <Save class="w-4 h-4" />
                  <span>{{ isSaving ? '保存中...' : '保存' }}</span>
                </button>
              </div>
            </div>

            <div class="info-grid">
              <!-- Display Name -->
              <div class="info-item">
                <div class="info-label">
                  <User class="w-4 h-4" />
                  <span>昵称</span>
                </div>
                <input
                  v-if="isEditing"
                  v-model="formData.display_name"
                  type="text"
                  class="info-input"
                  placeholder="输入昵称"
                >
                <span
                  v-else
                  class="info-value"
                >
                  {{ authStore.user?.display_name || '未设置' }}
                </span>
              </div>

              <!-- Email (read-only) -->
              <div class="info-item">
                <div class="info-label">
                  <Mail class="w-4 h-4" />
                  <span>邮箱</span>
                </div>
                <span class="info-value">
                  {{ authStore.user?.email }}
                  <span class="verified-badge">已验证</span>
                </span>
              </div>

              <!-- Phone -->
              <div class="info-item">
                <div class="info-label">
                  <Phone class="w-4 h-4" />
                  <span>手机</span>
                </div>
                <input
                  v-if="isEditing"
                  v-model="formData.phone"
                  type="tel"
                  class="info-input"
                  placeholder="输入手机号"
                >
                <span
                  v-else
                  class="info-value"
                >
                  {{ authStore.user?.phone || '未设置' }}
                </span>
              </div>

              <!-- Location -->
              <div class="info-item">
                <div class="info-label">
                  <MapPin class="w-4 h-4" />
                  <span>地区</span>
                </div>
                <input
                  v-if="isEditing"
                  v-model="formData.location"
                  type="text"
                  class="info-input"
                  placeholder="输入地区"
                >
                <span
                  v-else
                  class="info-value"
                >
                  {{ authStore.user?.location || '未设置' }}
                </span>
              </div>

              <!-- Join Date (read-only) -->
              <div class="info-item">
                <div class="info-label">
                  <Calendar class="w-4 h-4" />
                  <span>加入时间</span>
                </div>
                <span class="info-value">
                  {{ joinDate }}
                </span>
              </div>
            </div>

            <!-- Bio -->
            <div class="bio-section">
              <div class="info-label">
                <span>个人简介</span>
              </div>
              <textarea
                v-if="isEditing"
                v-model="formData.bio"
                class="bio-input"
                placeholder="介绍一下自己..."
                rows="3"
              />
              <p
                v-else
                class="bio-text"
              >
                {{ authStore.user?.bio || '这个人很懒，什么都没写...' }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: var(--any-bg-primary);
}

.profile-main {
  margin-left: 56px;
  padding: 80px 24px 40px;
}

.profile-container {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin-bottom: 24px;
}

.profile-card {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: 16px;
  overflow: hidden;
}

/* Avatar Section */
.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: var(--any-bg-tertiary);
  border-bottom: 1px solid var(--any-border);
}

.avatar-wrapper {
  position: relative;
  width: 80px;
  height: 80px;
}

.avatar-img,
.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #00B8D9, #00D9FF);
}

.avatar-edit-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--any-bg-primary);
  border: 2px solid var(--any-bg-tertiary);
  border-radius: 50%;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.avatar-edit-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.avatar-info {
  flex: 1;
}

.user-display-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0 0 4px;
}

.user-email {
  font-size: 14px;
  color: var(--any-text-secondary);
  margin: 0;
}

/* Info Section */
.info-section {
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--any-text-primary);
  margin: 0;
}

.edit-btn,
.cancel-btn,
.save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 150ms ease;
}

.edit-btn {
  color: var(--any-text-secondary);
  background: transparent;
  border: 1px solid var(--any-border);
}

.edit-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.edit-actions {
  display: flex;
  gap: 8px;
}

.cancel-btn {
  color: var(--any-text-secondary);
  background: transparent;
  border: 1px solid var(--any-border);
}

.cancel-btn:hover {
  background: var(--any-bg-hover);
}

.save-btn {
  color: white;
  background: var(--td-state-thinking);
  border: none;
}

.save-btn:hover {
  opacity: 0.9;
}

.save-btn:disabled,
.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Info Grid */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.info-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--any-text-muted);
}

.info-value {
  font-size: 14px;
  color: var(--any-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-input {
  padding: 8px 12px;
  font-size: 14px;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  outline: none;
  transition: border-color 150ms ease;
}

.info-input:focus {
  border-color: var(--td-state-thinking);
}

.verified-badge {
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 500;
  color: var(--any-success, #22c55e);
  background: rgba(34, 197, 94, 0.1);
  border-radius: 4px;
}

/* Bio Section */
.bio-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--any-border);
}

.bio-input {
  width: 100%;
  padding: 12px;
  font-size: 14px;
  color: var(--any-text-primary);
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: 8px;
  outline: none;
  resize: vertical;
  font-family: inherit;
}

.bio-input:focus {
  border-color: var(--td-state-thinking);
}

.bio-text {
  font-size: 14px;
  color: var(--any-text-secondary);
  line-height: 1.6;
  margin: 8px 0 0;
}

.hidden {
  display: none;
}

/* Responsive */
@media (max-width: 768px) {
  .profile-main {
    margin-left: 0;
    padding: 72px 16px 24px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .avatar-section {
    flex-direction: column;
    text-align: center;
  }
}
</style>
