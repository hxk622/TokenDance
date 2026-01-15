<script setup lang="ts">
import { computed } from 'vue'

export interface TeamMember {
  id: string
  name: string
  avatar: string
  role: string
}

export interface Activity {
  id: string
  user: TeamMember
  title: string
  completedAt: Date
  type: 'research' | 'ppt' | 'code' | 'analysis'
}

const props = defineProps<{
  activities?: Activity[]
}>()

const defaultActivities: Activity[] = [
  {
    id: '1',
    user: { id: '1', name: '张三', avatar: '👨‍💼', role: '产品' },
    title: '2024 年中报告分析',
    completedAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    type: 'analysis'
  },
  {
    id: '2',
    user: { id: '2', name: '李四', avatar: '👩‍💻', role: '技术' },
    title: 'API 性能优化方案',
    completedAt: new Date(Date.now() - 5 * 60 * 60 * 1000),
    type: 'code'
  },
  {
    id: '3',
    user: { id: '3', name: '王五', avatar: '👨‍🔬', role: '研究' },
    title: '市场趋势预测 PPT',
    completedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
    type: 'ppt'
  }
]

const activities = computed(() => props.activities || defaultActivities)

const formatTime = (date: Date) => {
  const now = new Date()
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000)
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${Math.floor(diff / 86400)}天前`
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    research: '📊',
    ppt: '📽️',
    code: '💻',
    analysis: '📈'
  }
  return icons[type] || '📌'
}
</script>

<template>
  <div class="team-activity">
    <h3 class="activity-label">🤝 团队最近的工作</h3>
    
    <div class="activity-list">
      <div v-for="item in activities" :key="item.id" class="activity-item">
        <!-- 用户头像 -->
        <div class="item-avatar">{{ item.user.avatar }}</div>
        
        <!-- 活动信息 -->
        <div class="item-content">
          <div class="item-header">
            <span class="item-user">{{ item.user.name }}</span>
            <span class="item-role">{{ item.user.role }}</span>
          </div>
          <div class="item-action">
            <span class="action-icon">{{ getTypeIcon(item.type) }}</span>
            <span class="action-text">刚完成</span>
            <span class="action-title">{{ item.title }}</span>
          </div>
        </div>
        
        <!-- 时间戳 -->
        <div class="item-time">{{ formatTime(item.completedAt) }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.team-activity {
  @apply bg-white rounded-2xl border border-gray-100 p-6;
}

.activity-label {
  @apply text-xs font-medium text-gray-400 uppercase tracking-wider mb-4;
}

.activity-list {
  @apply space-y-3;
}

.activity-item {
  @apply flex items-center gap-3 px-4 py-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors;
}

.item-avatar {
  @apply text-2xl w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 flex-shrink-0;
}

.item-content {
  @apply flex-1;
}

.item-header {
  @apply flex items-center gap-2 mb-1;
}

.item-user {
  @apply text-sm font-medium text-gray-900;
}

.item-role {
  @apply text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full;
}

.item-action {
  @apply flex items-center gap-1 text-sm;
}

.action-icon {
  @apply text-lg;
}

.action-text {
  @apply text-gray-500;
}

.action-title {
  @apply text-gray-700 font-medium;
}

.item-time {
  @apply text-xs text-gray-400 flex-shrink-0;
}
</style>
