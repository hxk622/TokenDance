<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { skillsApi, type SkillTemplate, type ScenePreset, type Category, type DiscoveryData } from '@/api/skills'
import { categoryIcons, getCategoryIcon } from '@/components/icons'

const router = useRouter()

// 状态
const loading = ref(true)
const error = ref<string | null>(null)
const discoveryData = ref<DiscoveryData | null>(null)
const selectedCategory = ref<string | null>(null)
const searchQuery = ref('')
const searchResults = ref<SkillTemplate[]>([])
const isSearching = ref(false)

// 获取分类图标组件
function getCategoryIconComponent(categoryId: string): Component {
  return getCategoryIcon(categoryId)
}

// 分类颜色映射
const categoryColors: Record<string, string> = {
  research: '#6366f1',
  writing: '#ec4899',
  data: '#14b8a6',
  visualization: '#f59e0b',
  coding: '#10b981',
  document: '#3b82f6',
  other: '#6b7280'
}

// 计算属性
const filteredTemplates = computed(() => {
  if (searchQuery.value) {
    return searchResults.value
  }
  if (!discoveryData.value) return []
  if (!selectedCategory.value) {
    return discoveryData.value.popular_templates
  }
  return discoveryData.value.popular_templates.filter(
    t => t.category === selectedCategory.value
  )
})

const filteredScenes = computed(() => {
  if (!discoveryData.value) return []
  if (!selectedCategory.value) {
    return discoveryData.value.popular_scenes
  }
  return discoveryData.value.popular_scenes.filter(
    s => s.category === selectedCategory.value
  )
})

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    error.value = null
    discoveryData.value = await skillsApi.getDiscoveryData()
  } catch (e) {
    error.value = '加载失败，请稍后重试'
    console.error('Failed to load discovery data:', e)
  } finally {
    loading.value = false
  }
}

// 搜索模板
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }

  try {
    isSearching.value = true
    searchResults.value = await skillsApi.listTemplates({
      search: searchQuery.value,
      limit: 20
    })
  } catch (e) {
    console.error('Search failed:', e)
  } finally {
    isSearching.value = false
  }
}

// 选择分类
const selectCategory = (categoryId: string | null) => {
  selectedCategory.value = categoryId
  searchQuery.value = ''
  searchResults.value = []
}

// 使用模板
const useTemplate = (template: SkillTemplate) => {
  router.push({
    path: '/chat',
    query: {
      template_id: template.id,
      skill_id: template.skill_id
    }
  })
}

// 使用场景
const useScene = (scene: ScenePreset) => {
  router.push({
    path: '/chat',
    query: {
      scene_id: scene.id
    }
  })
}

// 查看场景详情
const viewSceneDetail = async (scene: ScenePreset) => {
  // 可以展开显示场景包含的模板
  router.push({
    path: '/discover/scene',
    query: { id: scene.id }
  })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="skill-discovery">
    <!-- Header -->
    <header class="discovery-header">
      <div class="header-content">
        <h1 class="header-title">发现技能</h1>
        <p class="header-desc">选择一个模板快速开始，或浏览场景找到适合你的工作流</p>
      </div>

      <!-- Search -->
      <div class="search-wrapper">
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索模板..."
          @input="handleSearch"
        />
        <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner" />
      <p>加载中...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button class="retry-btn" @click="loadData">重试</button>
    </div>

    <!-- Content -->
    <main v-else class="discovery-content">
      <!-- Categories -->
      <section class="categories-section">
        <div class="categories-list">
          <button
            class="category-chip"
            :class="{ active: !selectedCategory }"
            @click="selectCategory(null)"
          >
            全部
          </button>
          <button
            v-for="cat in discoveryData?.categories"
            :key="cat.id"
            class="category-chip"
            :class="{ active: selectedCategory === cat.id }"
            @click="selectCategory(cat.id)"
          >
            <component :is="getCategoryIconComponent(cat.id)" class="category-icon w-4 h-4" />
            {{ cat.name }}
            <span class="category-count">{{ cat.template_count }}</span>
          </button>
        </div>
      </section>

      <!-- Scenes -->
      <section v-if="filteredScenes.length > 0 && !searchQuery" class="scenes-section">
        <h2 class="section-title">场景预设</h2>
        <div class="scenes-grid">
          <button
            v-for="scene in filteredScenes"
            :key="scene.id"
            class="scene-card"
            :style="{ '--scene-color': scene.color }"
            @click="useScene(scene)"
          >
            <div class="scene-icon">{{ scene.icon }}</div>
            <div class="scene-content">
              <h3 class="scene-name">{{ scene.name }}</h3>
              <p class="scene-desc">{{ scene.description }}</p>
              <div class="scene-meta">
                <span class="scene-templates">{{ scene.template_ids.length }} 个模板</span>
                <span class="scene-skills">{{ scene.recommended_skills.length }} 个技能</span>
              </div>
            </div>
            <svg class="scene-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </section>

      <!-- Templates -->
      <section class="templates-section">
        <h2 class="section-title">
          {{ searchQuery ? '搜索结果' : (selectedCategory ? '分类模板' : '热门模板') }}
          <span v-if="isSearching" class="searching-indicator">搜索中...</span>
        </h2>

        <div v-if="filteredTemplates.length === 0" class="empty-state">
          <p>{{ searchQuery ? '没有找到匹配的模板' : '暂无模板' }}</p>
        </div>

        <div v-else class="templates-grid">
          <button
            v-for="template in filteredTemplates"
            :key="template.id"
            class="template-card"
            @click="useTemplate(template)"
          >
            <div class="template-header">
              <span class="template-icon">{{ template.icon }}</span>
              <span
                class="template-category"
                :style="{ backgroundColor: categoryColors[template.category] + '20', color: categoryColors[template.category] }"
              >
                {{ categoryIcons[template.category] }} {{ template.category }}
              </span>
            </div>
            <h3 class="template-name">{{ template.name }}</h3>
            <p class="template-desc">{{ template.description }}</p>
            <div class="template-footer">
              <div class="template-tags">
                <span v-for="tag in template.tags.slice(0, 3)" :key="tag" class="template-tag">
                  {{ tag }}
                </span>
              </div>
              <div class="template-vars" v-if="template.variables.length > 0">
                <span class="vars-count">{{ template.variables.length }} 个参数</span>
              </div>
            </div>
            <div class="template-example" v-if="template.example_input">
              <span class="example-label">示例：</span>
              <span class="example-text">{{ template.example_input }}</span>
            </div>
          </button>
        </div>
      </section>

      <!-- Stats -->
      <section class="stats-section">
        <div class="stats-grid">
          <div class="stat-item">
            <span class="stat-value">{{ discoveryData?.total_templates || 0 }}</span>
            <span class="stat-label">模板</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ discoveryData?.total_scenes || 0 }}</span>
            <span class="stat-label">场景</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ discoveryData?.categories.length || 0 }}</span>
            <span class="stat-label">分类</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
/* ============================================
   SkillDiscovery - Dark Theme (TokenDance Design System)
   ============================================ */

.skill-discovery {
  @apply min-h-screen;
  background: #0a0a0b;
}

/* Header */
.discovery-header {
  @apply px-6 py-8;
  background: rgba(20, 20, 21, 0.8);
  backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.header-content {
  @apply max-w-4xl mx-auto text-center mb-6;
}

.header-title {
  @apply text-2xl font-semibold text-white mb-2;
  font-family: 'Space Grotesk', sans-serif;
}

.header-desc {
  color: rgba(255, 255, 255, 0.5);
}

.search-wrapper {
  @apply max-w-xl mx-auto relative;
}

.search-input {
  @apply w-full px-12 py-3 text-base rounded-xl transition-all;
  background: rgba(28, 28, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
  outline: none;
  border-color: rgba(139, 92, 246, 0.5);
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.search-icon {
  @apply absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5;
  color: rgba(255, 255, 255, 0.4);
}

/* Loading & Error */
.loading-state,
.error-state {
  @apply flex flex-col items-center justify-center py-20;
  color: rgba(255, 255, 255, 0.5);
}

.loading-spinner {
  @apply w-8 h-8 rounded-full animate-spin mb-4;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #00D9FF;
}

.retry-btn {
  @apply mt-4 px-4 py-2 rounded-lg transition-all duration-200;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
}

.retry-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.4);
}

/* Content */
.discovery-content {
  @apply max-w-6xl mx-auto px-6 py-8;
}

/* Categories */
.categories-section {
  @apply mb-8;
}

.categories-list {
  @apply flex flex-wrap gap-2;
}

.category-chip {
  @apply inline-flex items-center gap-1.5 px-4 py-2
         text-sm rounded-full transition-all duration-200 cursor-pointer;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
}

.category-chip:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  color: #ffffff;
}

.category-chip.active {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.category-icon {
  @apply text-base;
}

.category-count {
  @apply text-xs ml-1;
  color: rgba(255, 255, 255, 0.4);
}

.category-chip.active .category-count {
  color: rgba(255, 255, 255, 0.7);
}

/* Section Title */
.section-title {
  @apply text-lg font-medium text-white mb-4 flex items-center gap-2;
  font-family: 'Space Grotesk', sans-serif;
}

.searching-indicator {
  @apply text-sm font-normal;
  color: rgba(255, 255, 255, 0.4);
}

/* Scenes */
.scenes-section {
  @apply mb-10;
}

.scenes-grid {
  @apply grid grid-cols-1 md:grid-cols-2 gap-4;
}

.scene-card {
  @apply flex items-center gap-4 p-5 rounded-xl text-left cursor-pointer transition-all duration-200;
  background: linear-gradient(135deg, 
    rgba(var(--scene-rgb, 99, 102, 241), 0.15) 0%, 
    rgba(20, 20, 21, 0.9) 100%);
  border: 1px solid rgba(var(--scene-rgb, 99, 102, 241), 0.3);
}

.scene-card:hover {
  border-color: rgba(var(--scene-rgb, 99, 102, 241), 0.5);
  transform: translateX(4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.scene-icon {
  @apply w-12 h-12 rounded-xl flex items-center justify-center text-2xl flex-shrink-0;
  background: var(--scene-color, #6366f1);
  background: linear-gradient(135deg, var(--scene-color, #6366f1), color-mix(in srgb, var(--scene-color, #6366f1) 70%, black));
}

.scene-content {
  @apply flex-1 min-w-0;
}

.scene-name {
  @apply text-base font-medium text-white mb-1;
}

.scene-desc {
  @apply text-sm mb-2 line-clamp-2;
  color: rgba(255, 255, 255, 0.5);
}

.scene-meta {
  @apply flex items-center gap-3 text-xs;
  color: rgba(255, 255, 255, 0.4);
}

.scene-arrow {
  @apply w-5 h-5 flex-shrink-0 transition-all duration-200;
  color: rgba(255, 255, 255, 0.3);
}

.scene-card:hover .scene-arrow {
  color: rgba(255, 255, 255, 0.6);
  transform: translateX(4px);
}

/* Templates */
.templates-section {
  @apply mb-10;
}

.templates-grid {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.template-card {
  @apply flex flex-col p-5 rounded-xl text-left cursor-pointer transition-all duration-200;
  background: rgba(28, 28, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.template-card:hover {
  background: rgba(28, 28, 30, 1);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.template-header {
  @apply flex items-center justify-between mb-3;
}

.template-icon {
  @apply text-2xl;
}

.template-category {
  @apply text-xs px-2 py-1 rounded-full;
}

.template-name {
  @apply text-base font-medium text-white mb-2;
}

.template-desc {
  @apply text-sm mb-3 line-clamp-2 flex-1;
  color: rgba(255, 255, 255, 0.5);
}

.template-footer {
  @apply flex items-center justify-between;
}

.template-tags {
  @apply flex flex-wrap gap-1;
}

.template-tag {
  @apply text-xs px-2 py-0.5 rounded;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

.template-vars {
  @apply text-xs;
  color: rgba(255, 255, 255, 0.4);
}

.template-example {
  @apply mt-3 pt-3 text-xs;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.example-label {
  color: rgba(255, 255, 255, 0.4);
}

.example-text {
  @apply ml-1;
  color: rgba(255, 255, 255, 0.6);
}

/* Empty State */
.empty-state {
  @apply py-12 text-center;
  color: rgba(255, 255, 255, 0.4);
}

/* Stats */
.stats-section {
  @apply mt-12 pt-8;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.stats-grid {
  @apply flex justify-center gap-12;
}

.stat-item {
  @apply text-center;
}

.stat-value {
  @apply block text-3xl font-semibold;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  @apply text-sm;
  color: rgba(255, 255, 255, 0.5);
}
</style>
