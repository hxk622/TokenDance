<script setup lang="ts">
/**
 * BlockContent - Block 展开内容组件
 * 
 * 根据不同的研究阶段渲染对应内容：
 * - planning: 规划笔记
 * - searching: 搜索查询列表
 * - reading/analyzing: 来源卡片列表
 * - writing: 写作大纲
 */
import { computed } from 'vue'
import SearchQueryList from '../SearchQueryList.vue'
import SourceCard from '../SourceCard.vue'
import type { ResearchBlock } from './types'
import type { ResearchSource } from '../types'
import { Lightbulb, ListChecks } from 'lucide-vue-next'

const props = defineProps<{
  block: ResearchBlock
}>()

const emit = defineEmits<{
  (e: 'source-click', source: ResearchSource): void
  (e: 'open-url', url: string): void
}>()

// 是否有内容可显示
const hasContent = computed(() => {
  switch (props.block.phase) {
    case 'planning':
      return props.block.planningNotes && props.block.planningNotes.length > 0
    case 'searching':
      return props.block.queries.length > 0
    case 'reading':
    case 'analyzing':
      return props.block.sources.length > 0
    case 'writing':
      return props.block.writingOutline && props.block.writingOutline.length > 0
    default:
      return false
  }
})

// 来源统计
const sourceStats = computed(() => {
  const sources = props.block.sources
  const done = sources.filter(s => s.status === 'done').length
  return { done, total: sources.length }
})

function handleSourceClick(source: ResearchSource) {
  emit('source-click', source)
}

function handleOpenUrl(url: string) {
  emit('open-url', url)
}
</script>

<template>
  <div class="block-content">
    <!-- Planning Phase: Notes -->
    <div
      v-if="block.phase === 'planning'"
      class="planning-content"
    >
      <div 
        v-if="block.planningNotes && block.planningNotes.length > 0"
        class="notes-list"
      >
        <div 
          v-for="(note, index) in block.planningNotes" 
          :key="index"
          class="note-item"
        >
          <Lightbulb class="note-icon" />
          <span class="note-text">{{ note }}</span>
        </div>
      </div>
      <div
        v-else
        class="empty-state"
      >
        <span>正在分析主题并制定研究策略...</span>
      </div>
    </div>
    
    <!-- Searching Phase: Queries -->
    <div
      v-else-if="block.phase === 'searching'"
      class="searching-content"
    >
      <SearchQueryList 
        v-if="block.queries.length > 0"
        :queries="block.queries"
        :max-visible="8"
      />
      <div
        v-else
        class="empty-state"
      >
        <span>正在生成搜索查询...</span>
      </div>
    </div>
    
    <!-- Reading/Analyzing Phase: Sources -->
    <div
      v-else-if="block.phase === 'reading' || block.phase === 'analyzing'"
      class="sources-content"
    >
      <template v-if="block.sources.length > 0">
        <div class="sources-header">
          <span class="sources-count">
            {{ sourceStats.done }}/{{ sourceStats.total }} 个来源
          </span>
        </div>
        <div class="sources-list">
          <SourceCard
            v-for="source in block.sources.slice(0, 8)"
            :key="source.id"
            :source="source"
            compact
            @click="handleSourceClick"
            @open-url="handleOpenUrl"
          />
          <div 
            v-if="block.sources.length > 8"
            class="more-sources"
          >
            还有 {{ block.sources.length - 8 }} 个来源
          </div>
        </div>
      </template>
      <div
        v-else
        class="empty-state"
      >
        <span>{{ block.phase === 'reading' ? '正在阅读来源内容...' : '正在分析信息...' }}</span>
      </div>
    </div>
    
    <!-- Writing Phase: Outline -->
    <div
      v-else-if="block.phase === 'writing'"
      class="writing-content"
    >
      <div 
        v-if="block.writingOutline && block.writingOutline.length > 0"
        class="outline-list"
      >
        <div 
          v-for="(section, index) in block.writingOutline" 
          :key="index"
          class="outline-item"
        >
          <ListChecks class="outline-icon" />
          <span class="outline-text">{{ section }}</span>
        </div>
      </div>
      <div
        v-else
        class="empty-state"
      >
        <span>正在生成研究报告...</span>
      </div>
    </div>
    
    <!-- Default Empty -->
    <div
      v-else-if="!hasContent"
      class="empty-state"
    >
      <span>等待开始...</span>
    </div>
  </div>
</template>

<style scoped>
.block-content {
  padding: 0 14px 14px;
}

/* Planning Notes */
.planning-content {
  /* Layout handled by notes-list */
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border-radius: 8px;
  border: 1px solid var(--any-border);
}

.note-icon {
  width: 16px;
  height: 16px;
  color: var(--exec-accent);
  flex-shrink: 0;
  margin-top: 2px;
}

.note-text {
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.5;
}

/* Searching Queries */
.searching-content {
  /* SearchQueryList handles its own layout */
}

/* Sources */
.sources-content {
  /* Layout */
}

.sources-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.sources-count {
  font-size: 12px;
  color: var(--any-text-muted);
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.more-sources {
  font-size: 12px;
  color: var(--any-text-muted);
  text-align: center;
  padding: 8px;
}

/* Writing Outline */
.writing-content {
  /* Layout handled by outline-list */
}

.outline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border-radius: 8px;
  border: 1px solid var(--any-border);
}

.outline-icon {
  width: 16px;
  height: 16px;
  color: var(--exec-success);
  flex-shrink: 0;
  margin-top: 2px;
}

.outline-text {
  font-size: 13px;
  color: var(--any-text-primary);
  line-height: 1.5;
}

/* Empty State */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  color: var(--any-text-muted);
  font-size: 13px;
}
</style>
