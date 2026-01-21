<script setup lang="ts">
/**
 * PreferencePanel - 用户研究偏好设置面板
 * 
 * 允许用户配置研究偏好，包括：
 * - 专业背景
 * - 来源偏好
 * - 深度设置
 * - 报告风格
 */
import { ref, computed, onMounted } from 'vue'
import {
  Settings,
  GraduationCap,
  Globe,
  Gauge,
  FileText,
  Plus,
  X,
  Check,
  Shield,
  Ban,
} from 'lucide-vue-next'

// Types
interface UserPreference {
  user_id: string
  preferred_source_types: string[]
  trusted_domains: string[]
  blocked_domains: string[]
  preferred_languages: string[]
  default_depth: string
  default_breadth: number
  expertise_level: string
  expertise_domains: string[]
  preferred_report_style: string
  include_charts: boolean
  include_citations: boolean
  interaction_count: number
  updated_at: string | null
}

// Props
const props = withDefaults(defineProps<{
  userId: string
  preference?: UserPreference | null
  loading?: boolean
  compact?: boolean
}>(), {
  preference: null,
  loading: false,
  compact: false,
})

// Emits
const emit = defineEmits<{
  (e: 'update', updates: Partial<UserPreference>): void
  (e: 'add-trusted-domain', domain: string): void
  (e: 'add-blocked-domain', domain: string): void
  (e: 'remove-trusted-domain', domain: string): void
  (e: 'remove-blocked-domain', domain: string): void
}>()

// State
const newTrustedDomain = ref('')
const newBlockedDomain = ref('')
const newExpertiseDomain = ref('')
const isEditing = ref(false)
const localPreference = ref<Partial<UserPreference>>({})

// Constants
const SOURCE_TYPES = [
  { id: 'academic', label: '学术论文', icon: GraduationCap },
  { id: 'official', label: '官方文档', icon: Shield },
  { id: 'news', label: '新闻资讯', icon: Globe },
  { id: 'blog', label: '博客文章', icon: FileText },
]

const DEPTH_OPTIONS = [
  { id: 'quick', label: '快速', description: '3-5 个来源', sources: 5 },
  { id: 'standard', label: '标准', description: '8-10 个来源', sources: 10 },
  { id: 'deep', label: '深度', description: '15-20 个来源', sources: 18 },
]

const EXPERTISE_LEVELS = [
  { id: 'beginner', label: '入门', description: '基础概念解释' },
  { id: 'intermediate', label: '进阶', description: '适度专业深度' },
  { id: 'expert', label: '专家', description: '高度专业术语' },
]

const REPORT_STYLES = [
  { id: 'concise', label: '简洁', description: '要点概述' },
  { id: 'detailed', label: '详细', description: '完整分析' },
  { id: 'academic', label: '学术', description: '严谨引用' },
]

const LANGUAGES = [
  { id: 'zh', label: '中文' },
  { id: 'en', label: '英文' },
  { id: 'ja', label: '日文' },
]

// Computed
const currentPreference = computed(() => {
  return props.preference || {
    preferred_source_types: ['academic', 'official', 'news'],
    trusted_domains: [],
    blocked_domains: [],
    preferred_languages: ['zh', 'en'],
    default_depth: 'standard',
    default_breadth: 8,
    expertise_level: 'intermediate',
    expertise_domains: [],
    preferred_report_style: 'detailed',
    include_charts: true,
    include_citations: true,
  }
})

// Methods
const toggleSourceType = (typeId: string) => {
  const current = [...(currentPreference.value.preferred_source_types || [])]
  const index = current.indexOf(typeId)
  
  if (index === -1) {
    current.push(typeId)
  } else if (current.length > 1) {
    current.splice(index, 1)
  }
  
  emit('update', { preferred_source_types: current })
}

const toggleLanguage = (langId: string) => {
  const current = [...(currentPreference.value.preferred_languages || [])]
  const index = current.indexOf(langId)
  
  if (index === -1) {
    current.push(langId)
  } else if (current.length > 1) {
    current.splice(index, 1)
  }
  
  emit('update', { preferred_languages: current })
}

const setDepth = (depthId: string) => {
  const depth = DEPTH_OPTIONS.find(d => d.id === depthId)
  emit('update', { 
    default_depth: depthId,
    default_breadth: depth?.sources || 8
  })
}

const setExpertiseLevel = (level: string) => {
  emit('update', { expertise_level: level })
}

const setReportStyle = (style: string) => {
  emit('update', { preferred_report_style: style })
}

const toggleCharts = () => {
  emit('update', { include_charts: !currentPreference.value.include_charts })
}

const toggleCitations = () => {
  emit('update', { include_citations: !currentPreference.value.include_citations })
}

const addTrustedDomain = () => {
  if (!newTrustedDomain.value.trim()) return
  emit('add-trusted-domain', newTrustedDomain.value.trim())
  newTrustedDomain.value = ''
}

const addBlockedDomain = () => {
  if (!newBlockedDomain.value.trim()) return
  emit('add-blocked-domain', newBlockedDomain.value.trim())
  newBlockedDomain.value = ''
}

const removeTrustedDomain = (domain: string) => {
  emit('remove-trusted-domain', domain)
}

const removeBlockedDomain = (domain: string) => {
  emit('remove-blocked-domain', domain)
}

const addExpertiseDomain = () => {
  if (!newExpertiseDomain.value.trim()) return
  const current = [...(currentPreference.value.expertise_domains || [])]
  if (!current.includes(newExpertiseDomain.value.trim())) {
    current.push(newExpertiseDomain.value.trim())
    emit('update', { expertise_domains: current })
  }
  newExpertiseDomain.value = ''
}

const removeExpertiseDomain = (domain: string) => {
  const current = [...(currentPreference.value.expertise_domains || [])]
  const index = current.indexOf(domain)
  if (index !== -1) {
    current.splice(index, 1)
    emit('update', { expertise_domains: current })
  }
}
</script>

<template>
  <div 
    class="preference-panel"
    :class="{ 'preference-panel--compact': compact }"
  >
    <!-- Header -->
    <div class="panel-header">
      <div class="flex items-center gap-2">
        <Settings class="w-4 h-4 text-[var(--exec-accent)]" />
        <span class="header-title">研究偏好设置</span>
      </div>
    </div>

    <!-- Loading -->
    <div
      v-if="loading"
      class="loading-state"
    >
      <div class="spinner" />
      <span>加载中...</span>
    </div>

    <!-- Content -->
    <div
      v-else
      class="panel-content"
    >
      <!-- Expertise Level -->
      <section class="section">
        <h4 class="section-title">
          <GraduationCap class="w-4 h-4" />
          我的专业背景
        </h4>
        <div class="level-options">
          <button
            v-for="level in EXPERTISE_LEVELS"
            :key="level.id"
            class="level-btn"
            :class="{ 'level-btn--active': currentPreference.expertise_level === level.id }"
            @click="setExpertiseLevel(level.id)"
          >
            <span class="level-label">{{ level.label }}</span>
            <span class="level-desc">{{ level.description }}</span>
          </button>
        </div>

        <!-- Expertise Domains -->
        <div class="domain-tags">
          <span 
            v-for="domain in currentPreference.expertise_domains"
            :key="domain"
            class="domain-tag"
          >
            {{ domain }}
            <button
              class="tag-remove"
              @click="removeExpertiseDomain(domain)"
            >
              <X class="w-3 h-3" />
            </button>
          </span>
          <div class="add-domain">
            <input
              v-model="newExpertiseDomain"
              type="text"
              placeholder="添加领域"
              class="domain-input"
              @keyup.enter="addExpertiseDomain"
            >
            <button 
              class="add-btn"
              :disabled="!newExpertiseDomain.trim()"
              @click="addExpertiseDomain"
            >
              <Plus class="w-4 h-4" />
            </button>
          </div>
        </div>
      </section>

      <!-- Source Types -->
      <section class="section">
        <h4 class="section-title">
          <Globe class="w-4 h-4" />
          来源偏好
        </h4>
        <div class="source-options">
          <button
            v-for="source in SOURCE_TYPES"
            :key="source.id"
            class="source-btn"
            :class="{ 'source-btn--active': currentPreference.preferred_source_types?.includes(source.id) }"
            @click="toggleSourceType(source.id)"
          >
            <component
              :is="source.icon"
              class="w-4 h-4"
            />
            <span>{{ source.label }}</span>
            <Check 
              v-if="currentPreference.preferred_source_types?.includes(source.id)"
              class="w-4 h-4 check-icon"
            />
          </button>
        </div>

        <!-- Trusted Domains -->
        <div class="domain-section">
          <h5 class="domain-title">
            <Shield class="w-3.5 h-3.5 text-green-500" />
            信任的域名
          </h5>
          <div class="domain-list">
            <span 
              v-for="domain in currentPreference.trusted_domains"
              :key="domain"
              class="domain-chip domain-chip--trusted"
            >
              {{ domain }}
              <button @click="removeTrustedDomain(domain)">
                <X class="w-3 h-3" />
              </button>
            </span>
            <div class="domain-input-wrapper">
              <input
                v-model="newTrustedDomain"
                type="text"
                placeholder="添加域名"
                class="domain-input"
                @keyup.enter="addTrustedDomain"
              >
              <button 
                class="add-btn"
                :disabled="!newTrustedDomain.trim()"
                @click="addTrustedDomain"
              >
                <Plus class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Blocked Domains -->
        <div class="domain-section">
          <h5 class="domain-title">
            <Ban class="w-3.5 h-3.5 text-red-500" />
            屏蔽的域名
          </h5>
          <div class="domain-list">
            <span 
              v-for="domain in currentPreference.blocked_domains"
              :key="domain"
              class="domain-chip domain-chip--blocked"
            >
              {{ domain }}
              <button @click="removeBlockedDomain(domain)">
                <X class="w-3 h-3" />
              </button>
            </span>
            <div class="domain-input-wrapper">
              <input
                v-model="newBlockedDomain"
                type="text"
                placeholder="添加域名"
                class="domain-input"
                @keyup.enter="addBlockedDomain"
              >
              <button 
                class="add-btn"
                :disabled="!newBlockedDomain.trim()"
                @click="addBlockedDomain"
              >
                <Plus class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Research Depth -->
      <section class="section">
        <h4 class="section-title">
          <Gauge class="w-4 h-4" />
          默认深度
        </h4>
        <div class="depth-options">
          <button
            v-for="depth in DEPTH_OPTIONS"
            :key="depth.id"
            class="depth-btn"
            :class="{ 'depth-btn--active': currentPreference.default_depth === depth.id }"
            @click="setDepth(depth.id)"
          >
            <span class="depth-label">{{ depth.label }}</span>
            <span class="depth-desc">{{ depth.description }}</span>
          </button>
        </div>
      </section>

      <!-- Languages -->
      <section class="section">
        <h4 class="section-title">
          <Globe class="w-4 h-4" />
          语言偏好
        </h4>
        <div class="lang-options">
          <button
            v-for="lang in LANGUAGES"
            :key="lang.id"
            class="lang-btn"
            :class="{ 'lang-btn--active': currentPreference.preferred_languages?.includes(lang.id) }"
            @click="toggleLanguage(lang.id)"
          >
            <Check 
              v-if="currentPreference.preferred_languages?.includes(lang.id)"
              class="w-4 h-4"
            />
            <span>{{ lang.label }}</span>
          </button>
        </div>
      </section>

      <!-- Report Style -->
      <section class="section">
        <h4 class="section-title">
          <FileText class="w-4 h-4" />
          报告风格
        </h4>
        <div class="style-options">
          <button
            v-for="style in REPORT_STYLES"
            :key="style.id"
            class="style-btn"
            :class="{ 'style-btn--active': currentPreference.preferred_report_style === style.id }"
            @click="setReportStyle(style.id)"
          >
            <span class="style-label">{{ style.label }}</span>
            <span class="style-desc">{{ style.description }}</span>
          </button>
        </div>

        <!-- Toggles -->
        <div class="toggle-options">
          <label class="toggle-item">
            <input
              type="checkbox"
              :checked="currentPreference.include_charts"
              @change="toggleCharts"
            >
            <span>包含图表</span>
          </label>
          <label class="toggle-item">
            <input
              type="checkbox"
              :checked="currentPreference.include_citations"
              @change="toggleCitations"
            >
            <span>包含引用</span>
          </label>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.preference-panel {
  background: var(--any-bg-secondary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid var(--any-border);
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--any-text-primary);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: var(--any-text-muted);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--any-border);
  border-top-color: var(--exec-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.panel-content {
  padding: 16px;
}

.section {
  margin-bottom: 24px;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-secondary);
  margin: 0 0 12px 0;
}

/* Level Options */
.level-options {
  display: flex;
  gap: 8px;
}

.level-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.level-btn:hover {
  border-color: var(--any-border-hover);
}

.level-btn--active {
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-color: var(--exec-accent);
}

.level-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.level-desc {
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Domain Tags */
.domain-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.domain-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: var(--any-bg-tertiary);
  border-radius: var(--any-radius-full);
  font-size: 12px;
  color: var(--any-text-secondary);
}

.tag-remove {
  display: flex;
  padding: 2px;
  color: var(--any-text-muted);
  cursor: pointer;
}

.tag-remove:hover {
  color: var(--any-text-primary);
}

.add-domain {
  display: flex;
  align-items: center;
  gap: 4px;
}

.domain-input {
  width: 100px;
  padding: 4px 8px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-primary);
  outline: none;
}

.domain-input:focus {
  border-color: var(--exec-accent);
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: var(--exec-accent);
  border-radius: var(--any-radius-sm);
  color: var(--any-bg-primary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.add-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.add-btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

/* Source Options */
.source-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.source-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  font-size: 13px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.source-btn:hover {
  border-color: var(--any-border-hover);
}

.source-btn--active {
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-color: var(--exec-accent);
  color: var(--exec-accent);
}

.check-icon {
  margin-left: auto;
}

/* Domain Section */
.domain-section {
  margin-top: 12px;
}

.domain-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--any-text-secondary);
  margin: 0 0 8px 0;
}

.domain-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.domain-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--any-radius-full);
  font-size: 12px;
}

.domain-chip--trusted {
  background: color-mix(in srgb, #00c853 15%, transparent);
  color: #00c853;
}

.domain-chip--blocked {
  background: color-mix(in srgb, #ff3b30 15%, transparent);
  color: #ff3b30;
}

.domain-chip button {
  display: flex;
  padding: 2px;
  opacity: 0.7;
  cursor: pointer;
}

.domain-chip button:hover {
  opacity: 1;
}

.domain-input-wrapper {
  display: flex;
  gap: 4px;
}

/* Depth Options */
.depth-options {
  display: flex;
  gap: 8px;
}

.depth-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.depth-btn:hover {
  border-color: var(--any-border-hover);
}

.depth-btn--active {
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-color: var(--exec-accent);
}

.depth-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.depth-desc {
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Language Options */
.lang-options {
  display: flex;
  gap: 8px;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-full);
  font-size: 13px;
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.lang-btn:hover {
  border-color: var(--any-border-hover);
}

.lang-btn--active {
  background: var(--exec-accent);
  border-color: var(--exec-accent);
  color: var(--any-bg-primary);
}

/* Style Options */
.style-options {
  display: flex;
  gap: 8px;
}

.style-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  cursor: pointer;
  transition: all var(--any-duration-fast) var(--any-ease-out);
}

.style-btn:hover {
  border-color: var(--any-border-hover);
}

.style-btn--active {
  background: color-mix(in srgb, var(--exec-accent) 10%, transparent);
  border-color: var(--exec-accent);
}

.style-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.style-desc {
  font-size: 11px;
  color: var(--any-text-muted);
}

/* Toggle Options */
.toggle-options {
  display: flex;
  gap: 16px;
  margin-top: 12px;
}

.toggle-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--any-text-secondary);
  cursor: pointer;
}

.toggle-item input {
  accent-color: var(--exec-accent);
}

/* Compact Mode */
.preference-panel--compact .section {
  margin-bottom: 16px;
}

.preference-panel--compact .level-options,
.preference-panel--compact .depth-options,
.preference-panel--compact .style-options {
  flex-wrap: wrap;
}

.preference-panel--compact .level-btn,
.preference-panel--compact .depth-btn,
.preference-panel--compact .style-btn {
  padding: 8px;
}

.preference-panel--compact .source-options {
  grid-template-columns: 1fr;
}
</style>
