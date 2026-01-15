<template>
  <div class="trust-settings">
    <!-- Header -->
    <div class="settings-header">
      <div class="header-content">
        <h2 class="settings-title">信任配置</h2>
        <p class="settings-description">
          配置 Agent 操作的自动授权策略，减少确认打断，提升工作效率
        </p>
      </div>
      <div class="header-stats" v-if="config">
        <div class="stat-item">
          <span class="stat-value">{{ config.total_auto_approved }}</span>
          <span class="stat-label">自动授权</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ config.total_manual_approved }}</span>
          <span class="stat-label">手动确认</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ config.total_rejected }}</span>
          <span class="stat-label">已拒绝</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{{ error }}</span>
      <button @click="loadConfig" class="retry-btn">重试</button>
    </div>

    <!-- Settings Content -->
    <div v-else-if="config" class="settings-content">
      <!-- Enable/Disable Toggle -->
      <div class="setting-section">
        <div class="section-header">
          <h3 class="section-title">启用信任机制</h3>
          <label class="toggle-switch">
            <input
              type="checkbox"
              v-model="config.enabled"
              @change="handleToggleEnabled"
            />
            <span class="toggle-slider"></span>
          </label>
        </div>
        <p class="section-description">
          {{ config.enabled ? '已启用：符合条件的操作将自动执行' : '已禁用：所有操作都需要手动确认' }}
        </p>
      </div>

      <!-- Auto Approve Level -->
      <div class="setting-section" :class="{ disabled: !config.enabled }">
        <h3 class="section-title">自动授权等级</h3>
        <p class="section-description">
          设置自动执行的最高风险等级，超过此等级的操作需要手动确认
        </p>
        <div class="risk-level-selector">
          <button
            v-for="level in riskLevels"
            :key="level.level"
            :class="[
              'level-btn',
              `level-${level.level}`,
              { active: config.auto_approve_level === level.level }
            ]"
            :disabled="!config.enabled"
            @click="handleLevelChange(level.level)"
          >
            <span class="level-name">{{ getLevelLabel(level.level) }}</span>
            <span class="level-desc">{{ level.description }}</span>
          </button>
        </div>
      </div>

      <!-- Pre-authorized Operations -->
      <div class="setting-section" :class="{ disabled: !config.enabled }">
        <h3 class="section-title">预授权操作</h3>
        <p class="section-description">
          选择始终自动执行的操作类别（即使超出自动授权等级）
        </p>
        <div class="operation-grid">
          <label
            v-for="op in operationCategories"
            :key="op.category"
            class="operation-checkbox"
            :class="{ checked: isPreAuthorized(op.category) }"
          >
            <input
              type="checkbox"
              :checked="isPreAuthorized(op.category)"
              :disabled="!config.enabled"
              @change="togglePreAuthorized(op.category)"
            />
            <div class="checkbox-content">
              <span class="op-name">{{ op.description }}</span>
              <span class="op-risk" :class="`risk-${op.default_risk_level}`">
                {{ getLevelLabel(op.default_risk_level) }}
              </span>
            </div>
          </label>
        </div>
      </div>

      <!-- Blacklisted Operations -->
      <div class="setting-section" :class="{ disabled: !config.enabled }">
        <h3 class="section-title">黑名单操作</h3>
        <p class="section-description">
          选择始终需要确认的操作类别（即使在自动授权等级内）
        </p>
        <div class="operation-grid">
          <label
            v-for="op in operationCategories"
            :key="op.category"
            class="operation-checkbox blacklist"
            :class="{ checked: isBlacklisted(op.category) }"
          >
            <input
              type="checkbox"
              :checked="isBlacklisted(op.category)"
              :disabled="!config.enabled"
              @change="toggleBlacklisted(op.category)"
            />
            <div class="checkbox-content">
              <span class="op-name">{{ op.description }}</span>
              <span class="op-risk" :class="`risk-${op.default_risk_level}`">
                {{ getLevelLabel(op.default_risk_level) }}
              </span>
            </div>
          </label>
        </div>
      </div>

      <!-- Audit Logs -->
      <div class="setting-section">
        <div class="section-header">
          <h3 class="section-title">授权历史</h3>
          <button @click="loadAuditLogs" class="refresh-btn" :disabled="logsLoading">
            <svg class="w-4 h-4" :class="{ spinning: logsLoading }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        <div class="audit-logs">
          <div v-if="auditLogs.length === 0" class="empty-logs">
            暂无授权记录
          </div>
          <div
            v-for="log in auditLogs"
            :key="log.id"
            class="log-item"
            :class="`decision-${log.decision}`"
          >
            <div class="log-icon">
              <svg v-if="log.decision === 'auto_approved'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <svg v-else-if="log.decision === 'manual_approved'" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div class="log-content">
              <div class="log-header">
                <span class="log-tool">{{ log.tool_name }}</span>
                <span class="log-decision">{{ getDecisionLabel(log.decision) }}</span>
              </div>
              <div class="log-meta">
                <span class="log-category">{{ getCategoryLabel(log.operation_category) }}</span>
                <span class="log-time">{{ formatTime(log.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="auditLogs.length > 0" class="logs-pagination">
          <button
            @click="loadAuditLogs(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="page-btn"
          >
            上一页
          </button>
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
          <button
            @click="loadAuditLogs(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="page-btn"
          >
            下一页
          </button>
        </div>
      </div>
    </div>

    <!-- Save Indicator -->
    <Transition name="fade">
      <div v-if="saving" class="save-indicator">
        <div class="save-spinner"></div>
        <span>保存中...</span>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  trustApi,
  type TrustConfig,
  type TrustAuditLog,
  type RiskLevelInfo,
  type OperationCategoryInfo,
} from '@/api/trust'

const props = defineProps<{
  workspaceId: string
}>()

// State
const config = ref<TrustConfig | null>(null)
const riskLevels = ref<RiskLevelInfo[]>([])
const operationCategories = ref<OperationCategoryInfo[]>([])
const auditLogs = ref<TrustAuditLog[]>([])
const loading = ref(true)
const saving = ref(false)
const logsLoading = ref(false)
const error = ref<string | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)

// Methods
const loadConfig = async () => {
  loading.value = true
  error.value = null
  try {
    const [configData, metadata] = await Promise.all([
      trustApi.getConfig(props.workspaceId),
      trustApi.getMetadata(),
    ])
    config.value = configData
    riskLevels.value = metadata.risk_levels
    operationCategories.value = metadata.operation_categories
    await loadAuditLogs()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载配置失败'
  } finally {
    loading.value = false
  }
}

const loadAuditLogs = async (page = 1) => {
  logsLoading.value = true
  try {
    const result = await trustApi.getAuditLogs(props.workspaceId, {
      page,
      page_size: 10,
    })
    auditLogs.value = result.items
    currentPage.value = result.page
    totalPages.value = Math.ceil(result.total / result.page_size)
  } catch (e) {
    console.error('Failed to load audit logs:', e)
  } finally {
    logsLoading.value = false
  }
}

const saveConfig = async (update: Partial<TrustConfig>) => {
  if (!config.value) return
  saving.value = true
  try {
    const updated = await trustApi.updateConfig(props.workspaceId, update)
    config.value = updated
  } catch (e) {
    console.error('Failed to save config:', e)
    // Revert on error
    await loadConfig()
  } finally {
    saving.value = false
  }
}

const handleToggleEnabled = () => {
  if (config.value) {
    saveConfig({ enabled: config.value.enabled })
  }
}

const handleLevelChange = (level: string) => {
  if (config.value && config.value.enabled) {
    config.value.auto_approve_level = level
    saveConfig({ auto_approve_level: level })
  }
}

const isPreAuthorized = (category: string): boolean => {
  return config.value?.pre_authorized_operations.includes(category) ?? false
}

const isBlacklisted = (category: string): boolean => {
  return config.value?.blacklisted_operations.includes(category) ?? false
}

const togglePreAuthorized = (category: string) => {
  if (!config.value || !config.value.enabled) return

  const ops = [...config.value.pre_authorized_operations]
  const index = ops.indexOf(category)
  if (index >= 0) {
    ops.splice(index, 1)
  } else {
    ops.push(category)
    // Remove from blacklist if adding to pre-authorized
    const blacklist = config.value.blacklisted_operations.filter(
      (op) => op !== category
    )
    if (blacklist.length !== config.value.blacklisted_operations.length) {
      config.value.blacklisted_operations = blacklist
    }
  }
  config.value.pre_authorized_operations = ops
  saveConfig({
    pre_authorized_operations: ops,
    blacklisted_operations: config.value.blacklisted_operations,
  })
}

const toggleBlacklisted = (category: string) => {
  if (!config.value || !config.value.enabled) return

  const ops = [...config.value.blacklisted_operations]
  const index = ops.indexOf(category)
  if (index >= 0) {
    ops.splice(index, 1)
  } else {
    ops.push(category)
    // Remove from pre-authorized if adding to blacklist
    const preAuth = config.value.pre_authorized_operations.filter(
      (op) => op !== category
    )
    if (preAuth.length !== config.value.pre_authorized_operations.length) {
      config.value.pre_authorized_operations = preAuth
    }
  }
  config.value.blacklisted_operations = ops
  saveConfig({
    blacklisted_operations: ops,
    pre_authorized_operations: config.value.pre_authorized_operations,
  })
}

const getLevelLabel = (level: string): string => {
  const labels: Record<string, string> = {
    none: '无风险',
    low: '低风险',
    medium: '中风险',
    high: '高风险',
    critical: '极高风险',
  }
  return labels[level] || level
}

const getCategoryLabel = (category: string): string => {
  const op = operationCategories.value.find((o) => o.category === category)
  return op?.description || category
}

const getDecisionLabel = (decision: string): string => {
  const labels: Record<string, string> = {
    auto_approved: '自动授权',
    manual_approved: '手动确认',
    rejected: '已拒绝',
    timeout: '超时',
  }
  return labels[decision] || decision
}

const formatTime = (timestamp: string): string => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Lifecycle
onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.trust-settings {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.settings-title {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

.settings-description {
  margin: 0;
  font-size: 14px;
  color: #6b7280;
}

.header-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: #6b7280;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.error-state svg {
  color: #dc2626;
}

.retry-btn {
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
  color: white;
  background: #6366f1;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

/* Settings Sections */
.settings-content {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.setting-section {
  padding: 24px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  transition: opacity 0.2s;
}

.setting-section.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.section-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}

.section-description {
  margin: 0 0 16px;
  font-size: 14px;
  color: #6b7280;
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #d1d5db;
  border-radius: 24px;
  transition: 0.3s;
}

.toggle-slider::before {
  position: absolute;
  content: '';
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}

.toggle-switch input:checked + .toggle-slider {
  background: #10b981;
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(24px);
}

/* Risk Level Selector */
.risk-level-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 12px 16px;
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.level-btn:hover:not(:disabled) {
  background: #f3f4f6;
}

.level-btn.active {
  border-color: currentColor;
}

.level-btn:disabled {
  cursor: not-allowed;
}

.level-none { color: #16a34a; }
.level-none.active { background: #f0fdf4; }
.level-low { color: #d97706; }
.level-low.active { background: #fffbeb; }
.level-medium { color: #ea580c; }
.level-medium.active { background: #fff7ed; }
.level-high { color: #dc2626; }
.level-high.active { background: #fef2f2; }
.level-critical { color: #b91c1c; }
.level-critical.active { background: #fef2f2; }

.level-name {
  font-size: 14px;
  font-weight: 600;
}

.level-desc {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

/* Operation Grid */
.operation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}

.operation-checkbox {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border: 2px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.operation-checkbox:hover {
  background: #f3f4f6;
}

.operation-checkbox.checked {
  background: #f0fdf4;
  border-color: #10b981;
}

.operation-checkbox.blacklist.checked {
  background: #fef2f2;
  border-color: #dc2626;
}

.operation-checkbox input {
  width: 16px;
  height: 16px;
  accent-color: #10b981;
}

.operation-checkbox.blacklist input {
  accent-color: #dc2626;
}

.checkbox-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.op-name {
  font-size: 13px;
  font-weight: 500;
  color: #111827;
}

.op-risk {
  font-size: 11px;
  font-weight: 500;
}

.risk-none { color: #16a34a; }
.risk-low { color: #d97706; }
.risk-medium { color: #ea580c; }
.risk-high { color: #dc2626; }
.risk-critical { color: #b91c1c; }

/* Audit Logs */
.refresh-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #e5e7eb;
  color: #111827;
}

.refresh-btn:disabled {
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

.audit-logs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.empty-logs {
  padding: 32px;
  text-align: center;
  color: #9ca3af;
  font-size: 14px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
}

.log-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  flex-shrink: 0;
}

.decision-auto_approved .log-icon {
  background: #dbeafe;
  color: #2563eb;
}

.decision-manual_approved .log-icon {
  background: #dcfce7;
  color: #16a34a;
}

.decision-rejected .log-icon,
.decision-timeout .log-icon {
  background: #fecaca;
  color: #dc2626;
}

.log-content {
  flex: 1;
  min-width: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.log-tool {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.log-decision {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
}

.decision-auto_approved .log-decision {
  background: #dbeafe;
  color: #2563eb;
}

.decision-manual_approved .log-decision {
  background: #dcfce7;
  color: #16a34a;
}

.decision-rejected .log-decision,
.decision-timeout .log-decision {
  background: #fecaca;
  color: #dc2626;
}

.log-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.logs-pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

.page-btn {
  padding: 6px 12px;
  font-size: 13px;
  color: #374151;
  background: #f3f4f6;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #6b7280;
}

/* Save Indicator */
.save-indicator {
  position: fixed;
  bottom: 24px;
  right: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #111827;
  color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 14px;
}

.save-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* Animations */
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
