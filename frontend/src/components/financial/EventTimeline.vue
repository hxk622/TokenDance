<template>
  <div class="event-timeline">
    <!-- Header -->
    <div class="timeline-header">
      <div class="header-left">
        <Calendar
          class="header-icon"
          :size="20"
        />
        <h3 class="header-title">
          事件日历
        </h3>
        <span class="event-count">{{ events.length }} 个事件</span>
      </div>
      <div class="header-right">
        <!-- Filter Dropdown -->
        <div
          v-if="showFilters"
          class="filter-dropdown"
        >
          <select
            v-model="selectedImportance"
            class="importance-select"
          >
            <option value="all">
              全部重要性
            </option>
            <option value="critical">
              关键
            </option>
            <option value="high">
              高
            </option>
            <option value="medium">
              中
            </option>
            <option value="low">
              低
            </option>
          </select>
        </div>
        <!-- Days Range -->
        <span class="days-range">未来 {{ daysAhead }} 天</span>
      </div>
    </div>

    <!-- Next Critical Event Banner -->
    <div
      v-if="nextCriticalEvent"
      class="critical-banner"
    >
      <AlertTriangle
        class="critical-icon"
        :size="18"
      />
      <div class="critical-content">
        <span class="critical-label">最近重要事件</span>
        <span class="critical-title">{{ nextCriticalEvent.title }}</span>
        <span class="critical-days">{{ nextCriticalEvent.days_until }} 天后</span>
      </div>
    </div>

    <!-- Timeline Axis -->
    <div class="timeline-container">
      <!-- Month Labels -->
      <div class="timeline-axis">
        <div
          v-for="month in visibleMonths"
          :key="month.key"
          class="month-label"
          :style="{ left: month.position + '%' }"
        >
          {{ month.label }}
        </div>
        <div class="axis-line" />
      </div>

      <!-- Events -->
      <div class="timeline-events">
        <div
          v-for="event in sortedEvents"
          :key="`${event.symbol}-${event.event_type}-${event.event_date}`"
          class="event-marker"
          :style="{ left: getEventPosition(event) + '%' }"
          :class="[`importance-${event.importance}`, { 'is-selected': selectedEvent === event }]"
          @click="selectEvent(event)"
        >
          <div
            class="marker-dot"
            :style="{ backgroundColor: getEventColor(event.event_type) }"
          />
          <component
            :is="getEventIcon(event.event_type)"
            class="marker-icon"
            :size="14"
            :style="{ color: getEventColor(event.event_type) }"
          />
        </div>
      </div>

      <!-- Today Marker -->
      <div class="today-marker">
        <div class="today-line" />
        <span class="today-label">今天</span>
      </div>
    </div>

    <!-- Event Detail Card -->
    <Transition name="slide-up">
      <div
        v-if="selectedEvent"
        class="event-card"
      >
        <div class="card-header">
          <div
            class="card-type"
            :style="{ backgroundColor: getEventColor(selectedEvent.event_type) + '20' }"
          >
            <component
              :is="getEventIcon(selectedEvent.event_type)"
              :size="16"
              :style="{ color: getEventColor(selectedEvent.event_type) }"
            />
            <span :style="{ color: getEventColor(selectedEvent.event_type) }">
              {{ getEventTypeName(selectedEvent.event_type) }}
            </span>
          </div>
          <button
            class="close-btn"
            @click="selectedEvent = null"
          >
            <X :size="16" />
          </button>
        </div>

        <h4 class="card-title">
          {{ selectedEvent.title }}
        </h4>

        <div class="card-meta">
          <div class="meta-item">
            <Calendar :size="14" />
            <span>{{ formatDate(selectedEvent.event_date) }}</span>
          </div>
          <div class="meta-item">
            <Clock :size="14" />
            <span>{{ selectedEvent.days_until }} 天后</span>
          </div>
          <div
            class="importance-badge"
            :class="`importance-${selectedEvent.importance}`"
          >
            {{ getImportanceName(selectedEvent.importance) }}
          </div>
        </div>

        <p
          v-if="selectedEvent.description"
          class="card-description"
        >
          {{ selectedEvent.description }}
        </p>

        <!-- Metadata -->
        <div
          v-if="Object.keys(selectedEvent.metadata || {}).length > 0"
          class="card-metadata"
        >
          <div
            v-for="(value, key) in selectedEvent.metadata"
            :key="key"
            class="metadata-item"
          >
            <span class="metadata-key">{{ formatMetadataKey(key as string) }}</span>
            <span class="metadata-value">{{ formatMetadataValue(value) }}</span>
          </div>
        </div>

        <!-- Historical Impact -->
        <div
          v-if="selectedEvent.historical_impact"
          class="historical-impact"
        >
          <div class="impact-header">
            <TrendingUp :size="14" />
            <span>历史影响参考</span>
          </div>
          <div class="impact-grid">
            <div class="impact-item">
              <span class="impact-label">1日</span>
              <span
                class="impact-value"
                :class="getChangeClass(selectedEvent.historical_impact.price_change_1d)"
              >
                {{ formatChange(selectedEvent.historical_impact.price_change_1d) }}
              </span>
            </div>
            <div class="impact-item">
              <span class="impact-label">5日</span>
              <span
                class="impact-value"
                :class="getChangeClass(selectedEvent.historical_impact.price_change_5d)"
              >
                {{ formatChange(selectedEvent.historical_impact.price_change_5d) }}
              </span>
            </div>
            <div class="impact-item">
              <span class="impact-label">20日</span>
              <span
                class="impact-value"
                :class="getChangeClass(selectedEvent.historical_impact.price_change_20d)"
              >
                {{ formatChange(selectedEvent.historical_impact.price_change_20d) }}
              </span>
            </div>
            <div class="impact-item">
              <span class="impact-label">成交量</span>
              <span class="impact-value volume">
                +{{ selectedEvent.historical_impact.volume_change_pct.toFixed(0) }}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Event Type Legend -->
    <div class="event-legend">
      <div
        v-for="eventType in visibleEventTypes"
        :key="eventType"
        class="legend-item"
        :class="{ dimmed: filteredTypes.length > 0 && !filteredTypes.includes(eventType) }"
        @click="toggleEventTypeFilter(eventType)"
      >
        <div
          class="legend-dot"
          :style="{ backgroundColor: getEventColor(eventType) }"
        />
        <span class="legend-label">{{ getEventTypeName(eventType) }}</span>
        <span class="legend-count">{{ getEventCountByType(eventType) }}</span>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-if="events.length === 0"
      class="empty-state"
    >
      <Calendar
        class="empty-icon"
        :size="48"
      />
      <p class="empty-text">
        暂无即将发生的事件
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Calendar,
  Clock,
  TrendingUp,
  AlertTriangle,
  X,
  DollarSign,
  Unlock,
  Target,
  FileText,
  Users,
  CalendarDays,
  Mic,
  Rocket
} from 'lucide-vue-next'

// Types
interface EventImpact {
  event_type: string
  event_date: string
  price_change_1d: number
  price_change_5d: number
  price_change_20d: number
  excess_return_1d: number
  excess_return_5d: number
  volume_change_pct: number
  direction: 'positive' | 'negative' | 'neutral'
}

interface UpcomingEvent {
  symbol: string
  name: string
  event_type: string
  event_date: string
  importance: 'low' | 'medium' | 'high' | 'critical'
  title: string
  description: string
  metadata: Record<string, unknown>
  historical_impact: EventImpact | null
  days_until: number
}

// Props
const props = withDefaults(defineProps<{
  events: UpcomingEvent[]
  nextCriticalEvent?: UpcomingEvent | null
  daysAhead?: number
  showFilters?: boolean
}>(), {
  daysAhead: 90,
  showFilters: true
})

// State
const selectedEvent = ref<UpcomingEvent | null>(null)
const selectedImportance = ref<string>('all')
const filteredTypes = ref<string[]>([])

// Event type configuration
const EVENT_CONFIG: Record<string, { icon: typeof Calendar; color: string; name: string }> = {
  earnings: { icon: TrendingUp, color: '#00D9FF', name: '财报' },
  dividend: { icon: DollarSign, color: '#00FF88', name: '分红' },
  equity_unlock: { icon: Unlock, color: '#FFB800', name: '解禁' },
  guidance: { icon: Target, color: '#00D9FF', name: '指引' },
  annual_report: { icon: FileText, color: '#6366F1', name: '年报' },
  shareholder_meeting: { icon: Users, color: '#8B5CF6', name: '股东会' },
  bond_maturity: { icon: CalendarDays, color: '#F59E0B', name: '债务' },
  analyst_meeting: { icon: Mic, color: '#10B981', name: '分析师会' },
  product_launch: { icon: Rocket, color: '#EC4899', name: '发布会' }
}

// Computed
const sortedEvents = computed(() => {
  let filtered = [...props.events]

  // Filter by importance
  if (selectedImportance.value !== 'all') {
    filtered = filtered.filter(e => e.importance === selectedImportance.value)
  }

  // Filter by event type
  if (filteredTypes.value.length > 0) {
    filtered = filtered.filter(e => filteredTypes.value.includes(e.event_type))
  }

  return filtered.sort((a, b) => a.days_until - b.days_until)
})

const visibleEventTypes = computed(() => {
  const types = new Set(props.events.map(e => e.event_type))
  return Array.from(types)
})

const visibleMonths = computed(() => {
  const months: { key: string; label: string; position: number }[] = []
  const today = new Date()

  for (let i = 0; i <= 3; i++) {
    const monthDate = new Date(today)
    monthDate.setMonth(today.getMonth() + i)
    const daysFromToday = Math.floor((monthDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))

    if (daysFromToday <= props.daysAhead) {
      months.push({
        key: `${monthDate.getFullYear()}-${monthDate.getMonth()}`,
        label: `${monthDate.getMonth() + 1}月`,
        position: Math.min(100, (daysFromToday / props.daysAhead) * 100)
      })
    }
  }

  return months
})

// Methods
function getEventPosition(event: UpcomingEvent): number {
  return Math.min(100, (event.days_until / props.daysAhead) * 100)
}

function getEventColor(eventType: string): string {
  return EVENT_CONFIG[eventType]?.color || '#6B7280'
}

function getEventIcon(eventType: string) {
  return EVENT_CONFIG[eventType]?.icon || Calendar
}

function getEventTypeName(eventType: string): string {
  return EVENT_CONFIG[eventType]?.name || eventType
}

function getImportanceName(importance: string): string {
  const names: Record<string, string> = {
    critical: '关键',
    high: '高',
    medium: '中',
    low: '低'
  }
  return names[importance] || importance
}

function selectEvent(event: UpcomingEvent) {
  selectedEvent.value = selectedEvent.value === event ? null : event
}

function toggleEventTypeFilter(eventType: string) {
  const idx = filteredTypes.value.indexOf(eventType)
  if (idx > -1) {
    filteredTypes.value.splice(idx, 1)
  } else {
    filteredTypes.value.push(eventType)
  }
}

function getEventCountByType(eventType: string): number {
  return props.events.filter(e => e.event_type === eventType).length
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}月${date.getDate()}日`
}

function formatChange(value: number): string {
  if (value === 0) return '0%'
  const prefix = value > 0 ? '+' : ''
  return `${prefix}${value.toFixed(1)}%`
}

function getChangeClass(value: number): string {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

function formatMetadataKey(key: string): string {
  const keyMap: Record<string, string> = {
    period: '报告期',
    consensus_revenue: '预期营收',
    consensus_profit: '预期利润',
    cash_per_share: '每股派息',
    dividend_yield: '股息率',
    record_date: '登记日',
    pay_date: '派息日',
    unlock_shares: '解锁股数',
    unlock_ratio: '解锁比例',
    grant_price: '授予价格',
    current_price: '当前价格',
    potential_supply_pressure: '供给压力',
    meeting_type: '会议类型',
    key_proposals: '关键议案',
    report_type: '报告类型',
    fiscal_year: '财年'
  }
  return keyMap[key] || key
}

function formatMetadataValue(value: unknown): string {
  if (Array.isArray(value)) {
    return value.join('、')
  }
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  return String(value)
}
</script>

<style scoped>
.event-timeline {
  --timeline-bg: var(--any-bg-secondary);
  --timeline-border: var(--any-border);
  --timeline-text: var(--any-text-primary);
  --timeline-text-secondary: var(--any-text-secondary);
  --timeline-text-muted: var(--any-text-muted);

  background: var(--timeline-bg);
  border: 1px solid var(--timeline-border);
  border-radius: 12px;
  padding: 20px;
}

/* Header */
.timeline-header {
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
  color: var(--exec-accent, #00D9FF);
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--timeline-text);
  margin: 0;
}

.event-count {
  font-size: 12px;
  color: var(--timeline-text-muted);
  background: var(--any-bg-tertiary);
  padding: 2px 8px;
  border-radius: 10px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.importance-select {
  font-size: 12px;
  padding: 4px 8px;
  border: 1px solid var(--timeline-border);
  border-radius: 6px;
  background: var(--any-bg-primary);
  color: var(--timeline-text);
  cursor: pointer;
}

.days-range {
  font-size: 12px;
  color: var(--timeline-text-muted);
}

/* Critical Banner */
.critical-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(255, 184, 0, 0.1);
  border: 1px solid rgba(255, 184, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
}

.critical-icon {
  color: #FFB800;
  flex-shrink: 0;
}

.critical-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.critical-label {
  font-size: 12px;
  color: #FFB800;
  font-weight: 500;
}

.critical-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--timeline-text);
}

.critical-days {
  font-size: 12px;
  color: var(--timeline-text-secondary);
  background: var(--any-bg-tertiary);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Timeline Container */
.timeline-container {
  position: relative;
  height: 80px;
  margin: 24px 0;
  padding: 0 8px;
}

/* Timeline Axis */
.timeline-axis {
  position: relative;
  height: 24px;
}

.month-label {
  position: absolute;
  transform: translateX(-50%);
  font-size: 11px;
  color: var(--timeline-text-muted);
}

.axis-line {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(
    to right,
    var(--exec-accent) 0%,
    var(--timeline-border) 100%
  );
  border-radius: 1px;
}

/* Timeline Events */
.timeline-events {
  position: relative;
  height: 40px;
  margin-top: 8px;
}

.event-marker {
  position: absolute;
  bottom: 0;
  transform: translateX(-50%);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: transform 200ms ease;
}

.event-marker:hover {
  transform: translateX(-50%) scale(1.2);
}

.event-marker.is-selected {
  transform: translateX(-50%) scale(1.3);
}

.marker-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  box-shadow: 0 0 8px currentColor;
}

.marker-icon {
  opacity: 0;
  transition: opacity 200ms ease;
}

.event-marker:hover .marker-icon,
.event-marker.is-selected .marker-icon {
  opacity: 1;
}

/* Importance styles */
.event-marker.importance-critical .marker-dot {
  width: 12px;
  height: 12px;
  animation: pulse-critical 2s ease-in-out infinite;
}

.event-marker.importance-high .marker-dot {
  width: 10px;
  height: 10px;
}

@keyframes pulse-critical {
  0%, 100% { box-shadow: 0 0 4px currentColor; }
  50% { box-shadow: 0 0 12px currentColor, 0 0 20px currentColor; }
}

/* Today Marker */
.today-marker {
  position: absolute;
  left: 0;
  top: 24px;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.today-line {
  width: 2px;
  flex: 1;
  background: var(--exec-accent);
  opacity: 0.5;
}

.today-label {
  font-size: 10px;
  color: var(--exec-accent);
  margin-top: 4px;
}

/* Event Card */
.event-card {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--timeline-border);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-type {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.close-btn {
  padding: 4px;
  border: none;
  background: transparent;
  color: var(--timeline-text-muted);
  cursor: pointer;
  border-radius: 4px;
  transition: all 200ms ease;
}

.close-btn:hover {
  background: var(--any-bg-hover);
  color: var(--timeline-text);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--timeline-text);
  margin: 0 0 12px 0;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--timeline-text-secondary);
}

.importance-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.importance-badge.importance-critical {
  background: rgba(255, 59, 48, 0.2);
  color: #FF3B30;
}

.importance-badge.importance-high {
  background: rgba(255, 184, 0, 0.2);
  color: #FFB800;
}

.importance-badge.importance-medium {
  background: rgba(0, 217, 255, 0.2);
  color: #00D9FF;
}

.importance-badge.importance-low {
  background: var(--any-bg-hover);
  color: var(--timeline-text-muted);
}

.card-description {
  font-size: 13px;
  color: var(--timeline-text-secondary);
  line-height: 1.5;
  margin: 0 0 12px 0;
}

/* Metadata */
.card-metadata {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 8px;
  padding: 12px;
  background: var(--any-bg-primary);
  border-radius: 8px;
  margin-bottom: 12px;
}

.metadata-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.metadata-key {
  font-size: 11px;
  color: var(--timeline-text-muted);
}

.metadata-value {
  font-size: 13px;
  color: var(--timeline-text);
  font-weight: 500;
}

/* Historical Impact */
.historical-impact {
  background: var(--any-bg-primary);
  border-radius: 8px;
  padding: 12px;
}

.impact-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--timeline-text-muted);
  margin-bottom: 12px;
}

.impact-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.impact-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.impact-label {
  font-size: 11px;
  color: var(--timeline-text-muted);
}

.impact-value {
  font-size: 14px;
  font-weight: 600;
}

.impact-value.positive {
  color: #00FF88;
}

.impact-value.negative {
  color: #FF3B30;
}

.impact-value.neutral {
  color: var(--timeline-text-secondary);
}

.impact-value.volume {
  color: #00D9FF;
}

/* Event Legend */
.event-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--timeline-border);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--timeline-text-secondary);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 200ms ease;
}

.legend-item:hover {
  background: var(--any-bg-hover);
}

.legend-item.dimmed {
  opacity: 0.4;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-label {
  color: var(--timeline-text-secondary);
}

.legend-count {
  font-size: 10px;
  color: var(--timeline-text-muted);
  background: var(--any-bg-tertiary);
  padding: 1px 5px;
  border-radius: 8px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--timeline-text-muted);
}

.empty-icon {
  opacity: 0.3;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
  margin: 0;
}

/* Transitions */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 200ms ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
