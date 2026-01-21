<script setup lang="ts">
/**
 * QuickPreferencePopup - 快速偏好调整弹窗
 * 
 * 在研究开始前快速调整关键设置
 */
import { ref, computed } from 'vue'
import {
  Gauge,
  Brain,
  FileText,
  Settings,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-vue-next'

// Types
interface QuickPreferences {
  depth: 'quick' | 'standard' | 'deep'
  expertise: 'beginner' | 'intermediate' | 'expert'
  style: 'concise' | 'detailed' | 'academic'
}

// Props
const props = withDefaults(defineProps<{
  visible: boolean
  initialPreferences?: Partial<QuickPreferences>
}>(), {
  visible: false,
  initialPreferences: () => ({}),
})

// Emits
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'confirm', preferences: QuickPreferences): void
  (e: 'open-full-settings'): void
}>()

// State
const selectedDepth = ref<QuickPreferences['depth']>(
  props.initialPreferences.depth || 'standard'
)
const selectedExpertise = ref<QuickPreferences['expertise']>(
  props.initialPreferences.expertise || 'intermediate'
)
const selectedStyle = ref<QuickPreferences['style']>(
  props.initialPreferences.style || 'detailed'
)
const showAdvanced = ref(false)

// Constants
const DEPTH_OPTIONS = [
  { id: 'quick' as const, label: '快速', description: '3-5 来源，约 2 分钟' },
  { id: 'standard' as const, label: '标准', description: '8-10 来源，约 5 分钟' },
  { id: 'deep' as const, label: '深度', description: '15+ 来源，约 10 分钟' },
]

const EXPERTISE_OPTIONS = [
  { id: 'beginner' as const, label: '入门', description: '详细解释概念' },
  { id: 'intermediate' as const, label: '进阶', description: '适度专业深度' },
  { id: 'expert' as const, label: '专家', description: '假设专业背景' },
]

const STYLE_OPTIONS = [
  { id: 'concise' as const, label: '简洁', description: '关键要点' },
  { id: 'detailed' as const, label: '详细', description: '完整分析' },
  { id: 'academic' as const, label: '学术', description: '严谨引用' },
]

// Methods
const confirm = () => {
  emit('confirm', {
    depth: selectedDepth.value,
    expertise: selectedExpertise.value,
    style: selectedStyle.value,
  })
}

const close = () => {
  emit('close')
}

const openFullSettings = () => {
  emit('open-full-settings')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="popup">
      <div 
        v-if="visible" 
        class="popup-overlay"
        @click.self="close"
      >
        <div class="popup-container">
          <!-- Header -->
          <div class="popup-header">
            <div class="header-left">
              <Settings class="w-4 h-4 text-[var(--exec-accent)]" />
              <span class="header-title">研究设置</span>
            </div>
            <button
              class="close-btn"
              @click="close"
            >
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Content -->
          <div class="popup-content">
            <!-- Depth Selection -->
            <div class="setting-section">
              <div class="setting-label">
                <Gauge class="w-4 h-4" />
                研究深度
              </div>
              <div class="option-group">
                <button
                  v-for="option in DEPTH_OPTIONS"
                  :key="option.id"
                  class="option-btn"
                  :class="{ 'option-btn--active': selectedDepth === option.id }"
                  @click="selectedDepth = option.id"
                >
                  <span class="option-label">{{ option.label }}</span>
                  <span class="option-desc">{{ option.description }}</span>
                </button>
              </div>
            </div>

            <!-- Expertise Selection -->
            <div class="setting-section">
              <div class="setting-label">
                <Brain class="w-4 h-4" />
                专业程度
              </div>
              <div class="option-group">
                <button
                  v-for="option in EXPERTISE_OPTIONS"
                  :key="option.id"
                  class="option-btn"
                  :class="{ 'option-btn--active': selectedExpertise === option.id }"
                  @click="selectedExpertise = option.id"
                >
                  <span class="option-label">{{ option.label }}</span>
                  <span class="option-desc">{{ option.description }}</span>
                </button>
              </div>
            </div>

            <!-- Style Selection (Advanced) -->
            <div
              class="advanced-toggle"
              @click="showAdvanced = !showAdvanced"
            >
              <span>更多设置</span>
              <component 
                :is="showAdvanced ? ChevronUp : ChevronDown" 
                class="w-4 h-4"
              />
            </div>

            <Transition name="slide">
              <div
                v-if="showAdvanced"
                class="setting-section"
              >
                <div class="setting-label">
                  <FileText class="w-4 h-4" />
                  报告风格
                </div>
                <div class="option-group">
                  <button
                    v-for="option in STYLE_OPTIONS"
                    :key="option.id"
                    class="option-btn"
                    :class="{ 'option-btn--active': selectedStyle === option.id }"
                    @click="selectedStyle = option.id"
                  >
                    <span class="option-label">{{ option.label }}</span>
                    <span class="option-desc">{{ option.description }}</span>
                  </button>
                </div>
              </div>
            </Transition>
          </div>

          <!-- Footer -->
          <div class="popup-footer">
            <button
              class="text-btn"
              @click="openFullSettings"
            >
              完整设置
            </button>
            <div class="footer-actions">
              <button
                class="cancel-btn"
                @click="close"
              >
                取消
              </button>
              <button
                class="confirm-btn"
                @click="confirm"
              >
                开始研究
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.popup-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(4px);
}

.popup-container {
  width: 100%;
  max-width: 400px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  box-shadow: var(--any-shadow-lg);
  overflow: hidden;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--any-radius-md);
  color: var(--any-text-muted);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.close-btn:hover {
  background: var(--any-bg-tertiary);
  color: var(--any-text-primary);
}

.popup-content {
  padding: 16px;
}

.setting-section {
  margin-bottom: 16px;
}

.setting-section:last-child {
  margin-bottom: 0;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-secondary);
  margin-bottom: 10px;
}

.option-group {
  display: flex;
  gap: 8px;
}

.option-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px;
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.option-btn:hover {
  border-color: var(--any-border-hover);
}

.option-btn--active {
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-color: var(--exec-accent);
}

.option-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.option-desc {
  font-size: 10px;
  color: var(--any-text-muted);
  text-align: center;
}

.advanced-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 8px;
  margin-bottom: 12px;
  font-size: 12px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: color var(--any-duration-fast) var(--any-ease-out);
}

.advanced-toggle:hover {
  color: var(--any-text-secondary);
}

.popup-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--any-border);
  background: var(--any-bg-secondary);
}

.text-btn {
  font-size: 13px;
  color: var(--any-text-muted);
  cursor: pointer;
  transition: color var(--any-duration-fast) var(--any-ease-out);
}

.text-btn:hover {
  color: var(--exec-accent);
}

.footer-actions {
  display: flex;
  gap: 8px;
}

.cancel-btn {
  padding: 8px 16px;
  font-size: 13px;
  color: var(--any-text-secondary);
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.cancel-btn:hover {
  border-color: var(--any-border-hover);
}

.confirm-btn {
  padding: 8px 20px;
  font-size: 13px;
  font-weight: 500;
  color: var(--any-bg-primary);
  background: var(--exec-accent);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.confirm-btn:hover {
  filter: brightness(1.1);
}

/* Transitions */
.popup-enter-active,
.popup-leave-active {
  transition: opacity 0.2s ease;
}

.popup-enter-active .popup-container,
.popup-leave-active .popup-container {
  transition: transform 0.2s ease;
}

.popup-enter-from,
.popup-leave-to {
  opacity: 0;
}

.popup-enter-from .popup-container,
.popup-leave-to .popup-container {
  transform: scale(0.95) translateY(-10px);
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
  margin-bottom: 0;
}

.slide-enter-to,
.slide-leave-from {
  opacity: 1;
  max-height: 100px;
}
</style>
