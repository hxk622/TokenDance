<template>
  <div class="sentiment-pulse">
    <!-- Header -->
    <div class="pulse-header">
      <div class="header-left">
        <Activity
          class="header-icon"
          :size="20"
        />
        <h3 class="header-title">
          情绪脉冲
        </h3>
        <span
          class="heat-badge"
          :class="heatClass"
        >
          <Flame :size="12" />
          热度 {{ heatIndex.toFixed(0) }}
        </span>
      </div>
      <div class="header-right">
        <span class="days-label">近 {{ days }} 天</span>
      </div>
    </div>

    <!-- Current Sentiment Card -->
    <div
      class="current-sentiment"
      :class="`level-${currentLevel}`"
    >
      <div class="sentiment-gauge">
        <div class="gauge-track">
          <div
            class="gauge-fill"
            :style="{ width: gaugeWidth + '%' }"
          />
          <div
            class="gauge-indicator"
            :style="{ left: gaugeWidth + '%' }"
          />
        </div>
        <div class="gauge-labels">
          <span>极度悲观</span>
          <span>中性</span>
          <span>极度乐观</span>
        </div>
      </div>
      <div class="sentiment-info">
        <div class="sentiment-score">
          <span class="score-value">{{ (currentScore * 100).toFixed(0) }}</span>
          <span class="score-label">情绪指数</span>
        </div>
        <div
          class="sentiment-change"
          :class="changeClass"
        >
          <component
            :is="changeIcon"
            :size="16"
          />
          <span>{{ formatChange(scoreChange24h) }}</span>
          <span class="change-label">24h</span>
        </div>
        <div class="sentiment-level">
          <span
            class="level-badge"
            :class="`level-${currentLevel}`"
          >
            {{ getLevelName(currentLevel) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 7-Day Trend Chart -->
    <div class="trend-chart">
      <div class="chart-header">
        <span class="chart-title">情绪趋势</span>
        <div class="chart-legend">
          <span class="legend-item bullish">
            <span class="legend-dot" />看多
          </span>
          <span class="legend-item bearish">
            <span class="legend-dot" />看空
          </span>
        </div>
      </div>
      <div class="chart-container">
        <!-- Simplified bar chart -->
        <div class="bar-chart">
          <div
            v-for="(mood, index) in dailyMoods"
            :key="mood.date"
            class="bar-group"
            :class="{ selected: selectedDayIndex === index }"
            @click="selectDay(index)"
          >
            <div class="bar-stack">
              <div
                class="bar bullish"
                :style="{ height: (mood.bullish_ratio * 60) + 'px' }"
              />
              <div
                class="bar bearish"
                :style="{ height: (mood.bearish_ratio * 60) + 'px' }"
              />
            </div>
            <span class="bar-label">{{ formatDayLabel(mood.date) }}</span>
          </div>
        </div>
      </div>
      <!-- Day Detail -->
      <Transition name="fade">
        <div
          v-if="selectedDay"
          class="day-detail"
        >
          <div class="detail-header">
            <span>{{ formatFullDate(selectedDay.date) }}</span>
            <button
              class="close-btn"
              @click="selectedDayIndex = -1"
            >
              <X :size="14" />
            </button>
          </div>
          <div class="detail-grid">
            <div class="detail-item">
              <span
                class="detail-value"
                :class="getScoreClass(selectedDay.score)"
              >
                {{ (selectedDay.score * 100).toFixed(0) }}
              </span>
              <span class="detail-label">情绪指数</span>
            </div>
            <div class="detail-item">
              <span class="detail-value">{{ selectedDay.post_count }}</span>
              <span class="detail-label">帖子数</span>
            </div>
            <div class="detail-item">
              <span class="detail-value bullish">{{ (selectedDay.bullish_ratio * 100).toFixed(0) }}%</span>
              <span class="detail-label">看多</span>
            </div>
            <div class="detail-item">
              <span class="detail-value bearish">{{ (selectedDay.bearish_ratio * 100).toFixed(0) }}%</span>
              <span class="detail-label">看空</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Trending Topics -->
    <div
      v-if="trendingTopics.length > 0"
      class="trending-topics"
    >
      <div class="section-header">
        <Hash
          class="section-icon"
          :size="16"
        />
        <span>热门话题</span>
      </div>
      <div class="topics-grid">
        <div
          v-for="topic in trendingTopics"
          :key="topic.topic"
          class="topic-chip"
          :class="getTopicSentimentClass(topic.sentiment_score)"
        >
          <span class="topic-name"># {{ topic.topic }}</span>
          <span class="topic-count">{{ topic.count }}</span>
          <component
            :is="getTrendIcon(topic.trend)"
            class="topic-trend"
            :size="12"
          />
        </div>
      </div>
    </div>

    <!-- Key Opinions -->
    <div class="opinions-section">
      <!-- Bullish Opinions -->
      <div
        v-if="topBullishOpinions.length > 0"
        class="opinions-column bullish"
      >
        <div class="opinions-header">
          <TrendingUp
            class="opinions-icon"
            :size="16"
          />
          <span>看多观点 TOP {{ topBullishOpinions.length }}</span>
        </div>
        <div class="opinions-list">
          <div
            v-for="(opinion, index) in topBullishOpinions"
            :key="`bull-${index}`"
            class="opinion-card"
          >
            <p class="opinion-content">
              {{ opinion.content }}
            </p>
            <div class="opinion-meta">
              <span class="opinion-author">{{ opinion.author }}</span>
              <span class="opinion-likes">
                <ThumbsUp :size="12" />
                {{ opinion.likes }}
              </span>
              <span class="opinion-source">{{ opinion.source }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Bearish Opinions -->
      <div
        v-if="topBearishOpinions.length > 0"
        class="opinions-column bearish"
      >
        <div class="opinions-header">
          <TrendingDown
            class="opinions-icon"
            :size="16"
          />
          <span>看空观点 TOP {{ topBearishOpinions.length }}</span>
        </div>
        <div class="opinions-list">
          <div
            v-for="(opinion, index) in topBearishOpinions"
            :key="`bear-${index}`"
            class="opinion-card"
          >
            <p class="opinion-content">
              {{ opinion.content }}
            </p>
            <div class="opinion-meta">
              <span class="opinion-author">{{ opinion.author }}</span>
              <span class="opinion-likes">
                <ThumbsUp :size="12" />
                {{ opinion.likes }}
              </span>
              <span class="opinion-source">{{ opinion.source }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Source Distribution -->
    <div class="source-distribution">
      <div
        v-for="(count, source) in sourceDistribution"
        :key="source"
        class="source-item"
      >
        <span class="source-name">{{ getSourceName(source as string) }}</span>
        <div class="source-bar">
          <div
            class="source-fill"
            :style="{ width: getSourcePercent(count) + '%' }"
          />
        </div>
        <span class="source-count">{{ count }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Activity,
  Flame,
  TrendingUp,
  TrendingDown,
  Minus,
  Hash,
  ThumbsUp,
  ArrowUp,
  ArrowDown,
  X
} from 'lucide-vue-next'

// Types
interface DailyMood {
  date: string
  score: number
  level: string
  post_count: number
  bullish_ratio: number
  bearish_ratio: number
  volume_change: number
}

interface TrendingTopic {
  topic: string
  count: number
  sentiment_score: number
  trend: 'up' | 'down' | 'stable'
  examples: string[]
}

interface KeyOpinion {
  content: string
  source: string
  author: string
  likes: number
  sentiment: string
  published_at: string
}

// Props
const props = withDefaults(defineProps<{
  currentScore: number
  currentLevel: string
  scoreChange24h: number
  confidence: number
  dailyMoods: DailyMood[]
  trendingTopics: TrendingTopic[]
  topBullishOpinions: KeyOpinion[]
  topBearishOpinions: KeyOpinion[]
  heatIndex: number
  sourceDistribution: Record<string, number>
  days?: number
}>(), {
  days: 7
})

// State
const selectedDayIndex = ref(-1)

// Computed
const gaugeWidth = computed(() => {
  // Convert -1~1 to 0~100
  return ((props.currentScore + 1) / 2) * 100
})

const changeClass = computed(() => {
  if (props.scoreChange24h > 0.05) return 'positive'
  if (props.scoreChange24h < -0.05) return 'negative'
  return 'neutral'
})

const changeIcon = computed(() => {
  if (props.scoreChange24h > 0.05) return TrendingUp
  if (props.scoreChange24h < -0.05) return TrendingDown
  return Minus
})

const heatClass = computed(() => {
  if (props.heatIndex >= 80) return 'heat-high'
  if (props.heatIndex >= 50) return 'heat-medium'
  return 'heat-low'
})

const selectedDay = computed(() => {
  if (selectedDayIndex.value < 0 || selectedDayIndex.value >= props.dailyMoods.length) {
    return null
  }
  return props.dailyMoods[selectedDayIndex.value]
})

const totalPosts = computed(() => {
  return Object.values(props.sourceDistribution).reduce((a, b) => a + b, 0)
})

// Methods
function getLevelName(level: string): string {
  const names: Record<string, string> = {
    very_bearish: '极度悲观',
    bearish: '悲观',
    neutral: '中性',
    bullish: '乐观',
    very_bullish: '极度乐观'
  }
  return names[level] || level
}

function formatChange(value: number): string {
  const percent = (value * 100).toFixed(1)
  return value >= 0 ? `+${percent}` : percent
}

function formatDayLabel(dateStr: string): string {
  const date = new Date(dateStr)
  const day = date.getDate()
  return `${day}日`
}

function formatFullDate(dateStr: string): string {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function selectDay(index: number) {
  selectedDayIndex.value = selectedDayIndex.value === index ? -1 : index
}

function getScoreClass(score: number): string {
  if (score > 0.2) return 'bullish'
  if (score < -0.2) return 'bearish'
  return ''
}

function getTopicSentimentClass(score: number): string {
  if (score > 0.3) return 'bullish'
  if (score < -0.3) return 'bearish'
  return 'neutral'
}

function getTrendIcon(trend: string) {
  if (trend === 'up') return ArrowUp
  if (trend === 'down') return ArrowDown
  return Minus
}

function getSourceName(source: string): string {
  const names: Record<string, string> = {
    xueqiu: '雪球',
    guba: '股吧'
  }
  return names[source] || source
}

function getSourcePercent(count: number): number {
  return totalPosts.value > 0 ? (count / totalPosts.value) * 100 : 0
}
</script>

<style scoped>
.sentiment-pulse {
  --pulse-bg: var(--any-bg-secondary);
  --pulse-border: var(--any-border);
  --pulse-text: var(--any-text-primary);
  --pulse-text-secondary: var(--any-text-secondary);
  --pulse-text-muted: var(--any-text-muted);
  --pulse-bullish: #00FF88;
  --pulse-bearish: #FF3B30;
  --pulse-neutral: #00D9FF;

  background: var(--pulse-bg);
  border: 1px solid var(--pulse-border);
  border-radius: 12px;
  padding: 20px;
}

/* Header */
.pulse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  color: var(--pulse-neutral);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--pulse-text);
  margin: 0;
}

.heat-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.heat-badge.heat-high {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

.heat-badge.heat-medium {
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
}

.heat-badge.heat-low {
  background: var(--any-bg-tertiary);
  color: var(--pulse-text-muted);
}

.days-label {
  font-size: 12px;
  color: var(--pulse-text-muted);
}

/* Current Sentiment */
.current-sentiment {
  background: var(--any-bg-tertiary);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.sentiment-gauge {
  margin-bottom: 16px;
}

.gauge-track {
  position: relative;
  height: 8px;
  background: linear-gradient(
    to right,
    var(--pulse-bearish) 0%,
    var(--pulse-neutral) 50%,
    var(--pulse-bullish) 100%
  );
  border-radius: 4px;
  opacity: 0.3;
}

.gauge-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background: linear-gradient(
    to right,
    var(--pulse-bearish) 0%,
    var(--pulse-neutral) 50%,
    var(--pulse-bullish) 100%
  );
  border-radius: 4px;
}

.gauge-indicator {
  position: absolute;
  top: -4px;
  width: 16px;
  height: 16px;
  background: var(--any-bg-primary);
  border: 3px solid var(--pulse-neutral);
  border-radius: 50%;
  transform: translateX(-50%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.gauge-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 10px;
  color: var(--pulse-text-muted);
}

.sentiment-info {
  display: flex;
  align-items: center;
  gap: 24px;
}

.sentiment-score {
  display: flex;
  flex-direction: column;
}

.score-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--pulse-text);
  line-height: 1;
}

.score-label {
  font-size: 11px;
  color: var(--pulse-text-muted);
  margin-top: 4px;
}

.sentiment-change {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
}

.sentiment-change.positive {
  color: var(--pulse-bullish);
}

.sentiment-change.negative {
  color: var(--pulse-bearish);
}

.sentiment-change.neutral {
  color: var(--pulse-text-secondary);
}

.change-label {
  font-size: 11px;
  color: var(--pulse-text-muted);
}

.level-badge {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 16px;
  font-weight: 500;
}

.level-badge.level-very_bullish,
.level-badge.level-bullish {
  background: rgba(0, 255, 136, 0.2);
  color: var(--pulse-bullish);
}

.level-badge.level-very_bearish,
.level-badge.level-bearish {
  background: rgba(255, 59, 48, 0.2);
  color: var(--pulse-bearish);
}

.level-badge.level-neutral {
  background: rgba(0, 217, 255, 0.2);
  color: var(--pulse-neutral);
}

/* Trend Chart */
.trend-chart {
  margin-bottom: 16px;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--pulse-text-secondary);
}

.chart-legend {
  display: flex;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--pulse-text-muted);
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
}

.legend-item.bullish .legend-dot {
  background: var(--pulse-bullish);
}

.legend-item.bearish .legend-dot {
  background: var(--pulse-bearish);
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  height: 80px;
  padding: 8px 0;
}

.bar-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: opacity 200ms ease;
}

.bar-group:hover {
  opacity: 0.8;
}

.bar-group.selected {
  opacity: 1;
}

.bar-group.selected .bar-stack {
  transform: scale(1.1);
}

.bar-stack {
  display: flex;
  flex-direction: column-reverse;
  width: 100%;
  max-width: 24px;
  gap: 1px;
  transition: transform 200ms ease;
}

.bar {
  border-radius: 2px;
  min-height: 2px;
}

.bar.bullish {
  background: var(--pulse-bullish);
}

.bar.bearish {
  background: var(--pulse-bearish);
}

.bar-label {
  font-size: 10px;
  color: var(--pulse-text-muted);
  margin-top: 4px;
}

/* Day Detail */
.day-detail {
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--pulse-text-secondary);
  margin-bottom: 8px;
}

.close-btn {
  padding: 2px;
  border: none;
  background: transparent;
  color: var(--pulse-text-muted);
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: var(--any-bg-hover);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.detail-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--pulse-text);
}

.detail-value.bullish {
  color: var(--pulse-bullish);
}

.detail-value.bearish {
  color: var(--pulse-bearish);
}

.detail-label {
  font-size: 10px;
  color: var(--pulse-text-muted);
}

/* Trending Topics */
.trending-topics {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--pulse-text-secondary);
  margin-bottom: 12px;
}

.section-icon {
  color: var(--pulse-neutral);
}

.topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 12px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--pulse-border);
  transition: all 200ms ease;
}

.topic-chip:hover {
  border-color: var(--pulse-neutral);
}

.topic-chip.bullish {
  border-color: rgba(0, 255, 136, 0.3);
}

.topic-chip.bearish {
  border-color: rgba(255, 59, 48, 0.3);
}

.topic-name {
  color: var(--pulse-text);
}

.topic-count {
  font-size: 10px;
  color: var(--pulse-text-muted);
  background: var(--any-bg-hover);
  padding: 1px 5px;
  border-radius: 8px;
}

.topic-trend {
  color: var(--pulse-text-muted);
}

.topic-chip.bullish .topic-trend {
  color: var(--pulse-bullish);
}

.topic-chip.bearish .topic-trend {
  color: var(--pulse-bearish);
}

/* Opinions Section */
.opinions-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .opinions-section {
    grid-template-columns: 1fr;
  }
}

.opinions-column {
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  padding: 12px;
}

.opinions-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 12px;
}

.opinions-column.bullish .opinions-header {
  color: var(--pulse-bullish);
}

.opinions-column.bearish .opinions-header {
  color: var(--pulse-bearish);
}

.opinions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.opinion-card {
  background: var(--any-bg-primary);
  border-radius: 6px;
  padding: 10px;
}

.opinion-content {
  font-size: 12px;
  color: var(--pulse-text);
  line-height: 1.5;
  margin: 0 0 8px 0;
}

.opinion-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--pulse-text-muted);
}

.opinion-likes {
  display: flex;
  align-items: center;
  gap: 2px;
}

.opinion-source {
  padding: 1px 5px;
  background: var(--any-bg-hover);
  border-radius: 4px;
}

/* Source Distribution */
.source-distribution {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-name {
  font-size: 11px;
  color: var(--pulse-text-secondary);
  width: 40px;
}

.source-bar {
  flex: 1;
  height: 6px;
  background: var(--any-bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.source-fill {
  height: 100%;
  background: var(--pulse-neutral);
  border-radius: 3px;
  transition: width 300ms ease;
}

.source-count {
  font-size: 11px;
  color: var(--pulse-text-muted);
  width: 40px;
  text-align: right;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: all 200ms ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
