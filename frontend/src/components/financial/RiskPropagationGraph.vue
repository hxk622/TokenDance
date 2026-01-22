<template>
  <div class="risk-propagation">
    <!-- Header -->
    <div class="risk-header">
      <div class="header-left">
        <Shield
          class="header-icon"
          :size="20"
        />
        <h3 class="header-title">
          风险传导分析
        </h3>
      </div>
      <div class="header-right">
        <div
          class="risk-score-badge"
          :class="`level-${overallRiskLevel}`"
        >
          <span class="score-value">{{ totalRiskScore.toFixed(0) }}</span>
          <span class="score-label">综合风险</span>
        </div>
      </div>
    </div>

    <!-- Risk Overview -->
    <div class="risk-overview">
      <div class="overview-item">
        <AlertTriangle
          class="overview-icon critical"
          :size="18"
        />
        <span class="overview-value">{{ criticalRiskCount }}</span>
        <span class="overview-label">严重</span>
      </div>
      <div class="overview-item">
        <AlertCircle
          class="overview-icon high"
          :size="18"
        />
        <span class="overview-value">{{ highRiskCount }}</span>
        <span class="overview-label">高危</span>
      </div>
      <div class="overview-item">
        <ArrowDownToLine
          class="overview-icon incoming"
          :size="18"
        />
        <span class="overview-value">{{ incomingRisks.length }}</span>
        <span class="overview-label">传入</span>
      </div>
      <div class="overview-item">
        <ArrowUpFromLine
          class="overview-icon outgoing"
          :size="18"
        />
        <span class="overview-value">{{ outgoingRisks.length }}</span>
        <span class="overview-label">传出</span>
      </div>
    </div>

    <!-- Key Insights -->
    <div
      v-if="keyInsights.length > 0"
      class="insights-section"
    >
      <div class="insights-header">
        <Lightbulb
          class="insights-icon"
          :size="16"
        />
        <span>核心洞察</span>
      </div>
      <ul class="insights-list">
        <li
          v-for="(insight, idx) in keyInsights"
          :key="idx"
          class="insight-item"
        >
          {{ insight }}
        </li>
      </ul>
    </div>

    <!-- Risk Graph Visualization -->
    <div class="risk-graph">
      <!-- Center Node (Target Company) -->
      <div
        class="center-node"
        :class="`level-${overallRiskLevel}`"
      >
        <Building
          class="node-icon"
          :size="24"
        />
        <span class="node-name">{{ name }}</span>
        <span class="node-symbol">{{ symbol }}</span>
      </div>

      <!-- Incoming Risks (Left) -->
      <div class="risk-column incoming">
        <div class="column-header">
          <ArrowDownToLine :size="14" />
          <span>传导风险</span>
        </div>
        <div class="risk-nodes">
          <div
            v-for="(risk, idx) in incomingRisks"
            :key="`in-${idx}`"
            class="risk-node"
            :class="`level-${risk.risk_level}`"
            @click="selectRisk(risk)"
          >
            <component
              :is="getEntityIcon(risk.entity.entity_type)"
              class="entity-icon"
              :size="16"
            />
            <div class="node-info">
              <span class="node-name">{{ risk.entity.name }}</span>
              <span class="risk-type">{{ getRiskTypeName(risk.risk_type) }}</span>
            </div>
            <div
              class="risk-score"
              :class="`level-${risk.risk_level}`"
            >
              {{ risk.risk_score.toFixed(0) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Self Risks (Bottom) -->
      <div class="risk-column self">
        <div class="column-header">
          <Target :size="14" />
          <span>自身风险</span>
        </div>
        <div class="risk-nodes horizontal">
          <div
            v-for="(risk, idx) in selfRisks"
            :key="`self-${idx}`"
            class="risk-node self"
            :class="`level-${risk.risk_level}`"
            @click="selectRisk(risk)"
          >
            <component
              :is="getRiskTypeIcon(risk.risk_type)"
              class="risk-icon"
              :size="18"
            />
            <div class="node-info">
              <span class="risk-type">{{ getRiskTypeName(risk.risk_type) }}</span>
              <span class="risk-level-text">{{ getRiskLevelName(risk.risk_level) }}</span>
            </div>
            <div
              class="risk-score"
              :class="`level-${risk.risk_level}`"
            >
              {{ risk.risk_score.toFixed(0) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Outgoing Risks (Right) -->
      <div class="risk-column outgoing">
        <div class="column-header">
          <ArrowUpFromLine :size="14" />
          <span>输出风险</span>
        </div>
        <div class="risk-nodes">
          <div
            v-for="(risk, idx) in outgoingRisks"
            :key="`out-${idx}`"
            class="risk-node"
            :class="`level-${risk.risk_level}`"
            @click="selectRisk(risk)"
          >
            <component
              :is="getEntityIcon(risk.entity.entity_type)"
              class="entity-icon"
              :size="16"
            />
            <div class="node-info">
              <span class="node-name">{{ risk.entity.name }}</span>
              <span class="risk-type">{{ getRiskTypeName(risk.risk_type) }}</span>
            </div>
            <div
              class="risk-score"
              :class="`level-${risk.risk_level}`"
            >
              {{ risk.risk_score.toFixed(0) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Risk Detail Card -->
    <Transition name="slide-up">
      <div
        v-if="selectedRisk"
        class="risk-detail-card"
      >
        <div class="detail-header">
          <div
            class="detail-type"
            :class="`level-${selectedRisk.risk_level}`"
          >
            <component
              :is="getRiskTypeIcon(selectedRisk.risk_type)"
              :size="16"
            />
            <span>{{ getRiskTypeName(selectedRisk.risk_type) }}</span>
          </div>
          <button
            class="close-btn"
            @click="selectedRisk = null"
          >
            <X :size="16" />
          </button>
        </div>

        <div class="detail-entity">
          <span class="entity-name">{{ selectedRisk.entity.name }}</span>
          <span class="propagation-badge">
            {{ selectedRisk.is_source ? '风险源' : `传导层级 ${selectedRisk.propagation_depth}` }}
          </span>
        </div>

        <p class="detail-description">
          {{ selectedRisk.description }}
        </p>

        <div class="detail-mitigation">
          <Lightbulb :size="14" />
          <span>{{ selectedRisk.mitigation }}</span>
        </div>

        <!-- Propagation Path -->
        <div
          v-if="selectedRisk.propagation_path.length > 1"
          class="propagation-path"
        >
          <span class="path-label">传导路径:</span>
          <div class="path-nodes">
            <span
              v-for="(nodeId, idx) in selectedRisk.propagation_path"
              :key="nodeId"
              class="path-node"
            >
              {{ getNodeName(nodeId) }}
              <ArrowRight
                v-if="idx < selectedRisk.propagation_path.length - 1"
                :size="12"
              />
            </span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Risk Type Distribution -->
    <div class="risk-distribution">
      <div class="distribution-header">
        <span>风险类型分布</span>
      </div>
      <div class="distribution-bars">
        <div
          v-for="(count, riskType) in riskByType"
          :key="riskType"
          class="distribution-item"
        >
          <span class="type-label">{{ getRiskTypeName(riskType as string) }}</span>
          <div class="type-bar">
            <div
              class="type-fill"
              :style="{ width: getTypePercent(count) + '%' }"
              :class="getRiskTypeClass(riskType as string)"
            />
          </div>
          <span class="type-count">{{ count }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  ArrowDownToLine,
  ArrowUpFromLine,
  Lightbulb,
  Building,
  Target,
  X,
  ArrowRight,
  Users,
  Briefcase,
  Factory,
  CreditCard,
  Droplets,
  Settings,
  TrendingDown,
  Scale,
  Share2
} from 'lucide-vue-next'

// Types
interface Entity {
  entity_id: string
  name: string
  entity_type: string
  properties: Record<string, unknown>
}

interface RiskNode {
  entity: Entity
  risk_type: string
  risk_level: string
  risk_score: number
  is_source: boolean
  propagation_depth: number
  propagation_path: string[]
  description: string
  mitigation: string
}

// Props
const props = defineProps<{
  symbol: string
  name: string
  totalRiskScore: number
  overallRiskLevel: string
  highRiskCount: number
  criticalRiskCount: number
  selfRisks: RiskNode[]
  incomingRisks: RiskNode[]
  outgoingRisks: RiskNode[]
  riskByType: Record<string, number>
  keyInsights: string[]
}>()

// State
const selectedRisk = ref<RiskNode | null>(null)

// Computed
const totalRiskCount = computed(() => {
  return Object.values(props.riskByType).reduce((a, b) => a + b, 0)
})

// Methods
function selectRisk(risk: RiskNode) {
  selectedRisk.value = selectedRisk.value === risk ? null : risk
}

function getRiskTypeName(riskType: string): string {
  const names: Record<string, string> = {
    credit: '信用',
    liquidity: '流动性',
    operational: '运营',
    market: '市场',
    regulatory: '监管',
    contagion: '传导'
  }
  return names[riskType] || riskType
}

function getRiskLevelName(level: string): string {
  const names: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重'
  }
  return names[level] || level
}

function getRiskTypeIcon(riskType: string) {
  const icons: Record<string, typeof CreditCard> = {
    credit: CreditCard,
    liquidity: Droplets,
    operational: Settings,
    market: TrendingDown,
    regulatory: Scale,
    contagion: Share2
  }
  return icons[riskType] || AlertCircle
}

function getRiskTypeClass(riskType: string): string {
  const classes: Record<string, string> = {
    credit: 'credit',
    liquidity: 'liquidity',
    operational: 'operational',
    market: 'market',
    regulatory: 'regulatory',
    contagion: 'contagion'
  }
  return classes[riskType] || ''
}

function getEntityIcon(entityType: string) {
  const icons: Record<string, typeof Building> = {
    company: Building,
    person: Users,
    industry: Factory,
    product: Briefcase
  }
  return icons[entityType] || Building
}

function getTypePercent(count: number): number {
  return totalRiskCount.value > 0 ? (count / totalRiskCount.value) * 100 : 0
}

function getNodeName(nodeId: string): string {
  // Try to find in risks
  const allRisks = [...props.selfRisks, ...props.incomingRisks, ...props.outgoingRisks]
  const found = allRisks.find(r => r.entity.entity_id === nodeId)
  if (found) return found.entity.name

  // Check if it's the center node
  if (nodeId === props.symbol) return props.name

  return nodeId
}
</script>

<style scoped>
.risk-propagation {
  --risk-bg: var(--any-bg-secondary);
  --risk-border: var(--any-border);
  --risk-text: var(--any-text-primary);
  --risk-text-secondary: var(--any-text-secondary);
  --risk-text-muted: var(--any-text-muted);
  --risk-low: #00FF88;
  --risk-medium: #FFB800;
  --risk-high: #FF6B00;
  --risk-critical: #FF3B30;

  background: var(--risk-bg);
  border: 1px solid var(--risk-border);
  border-radius: 12px;
  padding: 20px;
}

/* Header */
.risk-header {
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
  color: #00D9FF;
}

.header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--risk-text);
  margin: 0;
}

.risk-score-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  border-radius: 8px;
}

.risk-score-badge.level-low {
  background: rgba(0, 255, 136, 0.1);
}

.risk-score-badge.level-medium {
  background: rgba(255, 184, 0, 0.1);
}

.risk-score-badge.level-high {
  background: rgba(255, 107, 0, 0.1);
}

.risk-score-badge.level-critical {
  background: rgba(255, 59, 48, 0.1);
}

.risk-score-badge .score-value {
  font-size: 24px;
  font-weight: 700;
}

.risk-score-badge.level-low .score-value { color: var(--risk-low); }
.risk-score-badge.level-medium .score-value { color: var(--risk-medium); }
.risk-score-badge.level-high .score-value { color: var(--risk-high); }
.risk-score-badge.level-critical .score-value { color: var(--risk-critical); }

.risk-score-badge .score-label {
  font-size: 10px;
  color: var(--risk-text-muted);
}

/* Overview */
.risk-overview {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.overview-icon.critical { color: var(--risk-critical); }
.overview-icon.high { color: var(--risk-high); }
.overview-icon.incoming { color: #00D9FF; }
.overview-icon.outgoing { color: #8B5CF6; }

.overview-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--risk-text);
}

.overview-label {
  font-size: 11px;
  color: var(--risk-text-muted);
}

/* Insights */
.insights-section {
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(255, 184, 0, 0.05);
  border: 1px solid rgba(255, 184, 0, 0.2);
  border-radius: 8px;
}

.insights-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: #FFB800;
  margin-bottom: 8px;
}

.insights-icon {
  color: #FFB800;
}

.insights-list {
  margin: 0;
  padding-left: 20px;
}

.insight-item {
  font-size: 13px;
  color: var(--risk-text-secondary);
  line-height: 1.5;
  margin-bottom: 4px;
}

.insight-item:last-child {
  margin-bottom: 0;
}

/* Risk Graph */
.risk-graph {
  position: relative;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto 1fr;
  gap: 16px;
  padding: 20px;
  background: var(--any-bg-tertiary);
  border-radius: 12px;
  margin-bottom: 16px;
}

.center-node {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 24px;
  background: var(--any-bg-primary);
  border: 2px solid var(--risk-border);
  border-radius: 12px;
  text-align: center;
}

.center-node.level-low { border-color: var(--risk-low); }
.center-node.level-medium { border-color: var(--risk-medium); }
.center-node.level-high { border-color: var(--risk-high); }
.center-node.level-critical { border-color: var(--risk-critical); }

.center-node .node-icon {
  color: var(--risk-text-secondary);
  margin-bottom: 8px;
}

.center-node .node-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--risk-text);
}

.center-node .node-symbol {
  font-size: 11px;
  color: var(--risk-text-muted);
}

/* Risk Columns */
.risk-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-column.incoming {
  grid-column: 1;
  grid-row: 1 / 3;
}

.risk-column.outgoing {
  grid-column: 3;
  grid-row: 1 / 3;
}

.risk-column.self {
  grid-column: 1 / 4;
  grid-row: 2;
}

.column-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  color: var(--risk-text-muted);
  margin-bottom: 4px;
}

.risk-nodes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.risk-nodes.horizontal {
  flex-direction: row;
  flex-wrap: wrap;
}

/* Risk Node */
.risk-node {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--any-bg-primary);
  border: 1px solid var(--risk-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
}

.risk-node:hover {
  border-color: #00D9FF;
}

.risk-node.level-low { border-left: 3px solid var(--risk-low); }
.risk-node.level-medium { border-left: 3px solid var(--risk-medium); }
.risk-node.level-high { border-left: 3px solid var(--risk-high); }
.risk-node.level-critical { border-left: 3px solid var(--risk-critical); }

.risk-node.self {
  flex: 1;
  min-width: 150px;
  border-left: none;
  border-bottom: 3px solid;
}

.risk-node.self.level-low { border-bottom-color: var(--risk-low); }
.risk-node.self.level-medium { border-bottom-color: var(--risk-medium); }
.risk-node.self.level-high { border-bottom-color: var(--risk-high); }
.risk-node.self.level-critical { border-bottom-color: var(--risk-critical); }

.entity-icon, .risk-icon {
  color: var(--risk-text-secondary);
  flex-shrink: 0;
}

.node-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.node-info .node-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--risk-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.node-info .risk-type {
  font-size: 10px;
  color: var(--risk-text-muted);
}

.node-info .risk-level-text {
  font-size: 10px;
  color: var(--risk-text-muted);
}

.risk-score {
  font-size: 14px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.risk-score.level-low { background: rgba(0, 255, 136, 0.2); color: var(--risk-low); }
.risk-score.level-medium { background: rgba(255, 184, 0, 0.2); color: var(--risk-medium); }
.risk-score.level-high { background: rgba(255, 107, 0, 0.2); color: var(--risk-high); }
.risk-score.level-critical { background: rgba(255, 59, 48, 0.2); color: var(--risk-critical); }

/* Risk Detail Card */
.risk-detail-card {
  background: var(--any-bg-tertiary);
  border: 1px solid var(--risk-border);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 16px;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.detail-type {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.detail-type.level-low { background: rgba(0, 255, 136, 0.2); color: var(--risk-low); }
.detail-type.level-medium { background: rgba(255, 184, 0, 0.2); color: var(--risk-medium); }
.detail-type.level-high { background: rgba(255, 107, 0, 0.2); color: var(--risk-high); }
.detail-type.level-critical { background: rgba(255, 59, 48, 0.2); color: var(--risk-critical); }

.close-btn {
  padding: 4px;
  border: none;
  background: transparent;
  color: var(--risk-text-muted);
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: var(--any-bg-hover);
}

.detail-entity {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.entity-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--risk-text);
}

.propagation-badge {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--any-bg-hover);
  border-radius: 4px;
  color: var(--risk-text-muted);
}

.detail-description {
  font-size: 13px;
  color: var(--risk-text-secondary);
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.detail-mitigation {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 10px 12px;
  background: rgba(0, 255, 136, 0.05);
  border: 1px solid rgba(0, 255, 136, 0.2);
  border-radius: 6px;
  font-size: 12px;
  color: var(--risk-text-secondary);
}

.detail-mitigation > svg {
  color: var(--risk-low);
  flex-shrink: 0;
  margin-top: 2px;
}

.propagation-path {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--risk-border);
}

.path-label {
  font-size: 11px;
  color: var(--risk-text-muted);
  margin-bottom: 8px;
  display: block;
}

.path-nodes {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.path-node {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--risk-text-secondary);
}

/* Risk Distribution */
.risk-distribution {
  padding: 12px;
  background: var(--any-bg-tertiary);
  border-radius: 8px;
}

.distribution-header {
  font-size: 12px;
  font-weight: 500;
  color: var(--risk-text-secondary);
  margin-bottom: 12px;
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.distribution-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-label {
  font-size: 11px;
  color: var(--risk-text-secondary);
  width: 50px;
}

.type-bar {
  flex: 1;
  height: 6px;
  background: var(--any-bg-primary);
  border-radius: 3px;
  overflow: hidden;
}

.type-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 300ms ease;
}

.type-fill.credit { background: #FF6B6B; }
.type-fill.liquidity { background: #4ECDC4; }
.type-fill.operational { background: #FFE66D; }
.type-fill.market { background: #95E1D3; }
.type-fill.regulatory { background: #DDA0DD; }
.type-fill.contagion { background: #00D9FF; }

.type-count {
  font-size: 11px;
  color: var(--risk-text-muted);
  width: 20px;
  text-align: right;
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
