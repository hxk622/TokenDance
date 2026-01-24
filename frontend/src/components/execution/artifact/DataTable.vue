<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { 
  Download, Search, ArrowUpDown, ArrowUp, ArrowDown,
  ChevronLeft, ChevronRight, Table2, Filter, X
} from 'lucide-vue-next'

interface Column {
  key: string
  label: string
  width?: number
  sortable?: boolean
  filterable?: boolean
  align?: 'left' | 'center' | 'right'
}

interface Props {
  /** Table columns definition */
  columns: Column[]
  /** Table data rows */
  data: Record<string, any>[]
  /** Enable row selection */
  selectable?: boolean
  /** Rows per page */
  pageSize?: number
  /** Show pagination */
  pagination?: boolean
  /** Enable search */
  searchable?: boolean
  /** Table title */
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectable: false,
  pageSize: 50,
  pagination: true,
  searchable: true,
  title: ''
})

const emit = defineEmits<{
  'row-click': [row: Record<string, any>, index: number]
  'selection-change': [rows: Record<string, any>[]]
}>()

// State
const searchQuery = ref('')
const sortKey = ref<string | null>(null)
const sortOrder = ref<'asc' | 'desc'>('asc')
const currentPage = ref(1)
const selectedRows = ref<Set<number>>(new Set())
const filterVisible = ref<string | null>(null)
const columnFilters = ref<Record<string, string>>({})

// Computed
const filteredData = computed(() => {
  let result = [...props.data]
  
  // Global search
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(row => 
      Object.values(row).some(val => 
        String(val).toLowerCase().includes(query)
      )
    )
  }
  
  // Column filters
  for (const [key, filter] of Object.entries(columnFilters.value)) {
    if (filter) {
      result = result.filter(row => 
        String(row[key]).toLowerCase().includes(filter.toLowerCase())
      )
    }
  }
  
  return result
})

const sortedData = computed(() => {
  if (!sortKey.value) return filteredData.value
  
  return [...filteredData.value].sort((a, b) => {
    const aVal = a[sortKey.value!]
    const bVal = b[sortKey.value!]
    
    // Handle numbers
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortOrder.value === 'asc' ? aVal - bVal : bVal - aVal
    }
    
    // Handle strings
    const aStr = String(aVal).toLowerCase()
    const bStr = String(bVal).toLowerCase()
    
    if (sortOrder.value === 'asc') {
      return aStr.localeCompare(bStr)
    }
    return bStr.localeCompare(aStr)
  })
})

const paginatedData = computed(() => {
  if (!props.pagination) return sortedData.value
  
  const start = (currentPage.value - 1) * props.pageSize
  return sortedData.value.slice(start, start + props.pageSize)
})

const totalPages = computed(() => 
  Math.ceil(sortedData.value.length / props.pageSize)
)

const displayRange = computed(() => {
  const start = (currentPage.value - 1) * props.pageSize + 1
  const end = Math.min(currentPage.value * props.pageSize, sortedData.value.length)
  return `${start}-${end} / ${sortedData.value.length}`
})

// Methods
function toggleSort(key: string) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

function getSortIcon(key: string) {
  if (sortKey.value !== key) return ArrowUpDown
  return sortOrder.value === 'asc' ? ArrowUp : ArrowDown
}

function toggleFilter(key: string) {
  filterVisible.value = filterVisible.value === key ? null : key
}

function clearFilter(key: string) {
  delete columnFilters.value[key]
  filterVisible.value = null
}

function goToPage(page: number) {
  currentPage.value = Math.max(1, Math.min(page, totalPages.value))
}

function handleRowClick(row: Record<string, any>, index: number) {
  emit('row-click', row, index)
}

function toggleRowSelection(index: number) {
  if (selectedRows.value.has(index)) {
    selectedRows.value.delete(index)
  } else {
    selectedRows.value.add(index)
  }
  
  const selected = Array.from(selectedRows.value).map(i => paginatedData.value[i])
  emit('selection-change', selected)
}

function toggleAllSelection() {
  if (selectedRows.value.size === paginatedData.value.length) {
    selectedRows.value.clear()
  } else {
    selectedRows.value = new Set(paginatedData.value.map((_, i) => i))
  }
  
  const selected = Array.from(selectedRows.value).map(i => paginatedData.value[i])
  emit('selection-change', selected)
}

// Export functions
function exportCSV() {
  const headers = props.columns.map(c => c.label).join(',')
  const rows = sortedData.value.map(row => 
    props.columns.map(c => {
      const val = row[c.key]
      // Escape commas and quotes
      if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
        return `"${val.replace(/"/g, '""')}"`
      }
      return val
    }).join(',')
  )
  
  const csv = [headers, ...rows].join('\n')
  downloadFile(csv, 'table-export.csv', 'text/csv')
}

function downloadFile(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

// Reset page when filter changes
watch([searchQuery, columnFilters], () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="data-table">
    <!-- Toolbar -->
    <div class="table-toolbar">
      <div class="toolbar-left">
        <Table2 class="w-4 h-4 text-muted" />
        <span
          v-if="title"
          class="table-title"
        >{{ title }}</span>
        <span class="row-count">{{ displayRange }}</span>
      </div>
      
      <div class="toolbar-right">
        <!-- Search -->
        <div
          v-if="searchable"
          class="search-box"
        >
          <Search class="search-icon" />
          <input 
            v-model="searchQuery"
            type="text"
            placeholder="搜索..."
            class="search-input"
          >
        </div>
        
        <!-- Export -->
        <button
          class="action-btn"
          title="导出 CSV"
          @click="exportCSV"
        >
          <Download class="w-4 h-4" />
        </button>
      </div>
    </div>

    <!-- Table Container -->
    <div class="table-container">
      <table class="table">
        <!-- Header -->
        <thead>
          <tr>
            <th
              v-if="selectable"
              class="th-checkbox"
            >
              <input 
                type="checkbox"
                :checked="selectedRows.size === paginatedData.length && paginatedData.length > 0"
                :indeterminate="selectedRows.size > 0 && selectedRows.size < paginatedData.length"
                @change="toggleAllSelection"
              >
            </th>
            <th 
              v-for="col in columns" 
              :key="col.key"
              :style="{ width: col.width ? `${col.width}px` : 'auto', textAlign: col.align || 'left' }"
              class="th-cell"
            >
              <div class="th-content">
                <span>{{ col.label }}</span>
                
                <div class="th-actions">
                  <!-- Sort -->
                  <button 
                    v-if="col.sortable !== false"
                    :class="['sort-btn', { active: sortKey === col.key }]"
                    @click="toggleSort(col.key)"
                  >
                    <component
                      :is="getSortIcon(col.key)"
                      class="w-3.5 h-3.5"
                    />
                  </button>
                  
                  <!-- Filter -->
                  <div
                    v-if="col.filterable"
                    class="filter-wrapper"
                  >
                    <button 
                      :class="['filter-btn', { active: columnFilters[col.key] }]"
                      @click="toggleFilter(col.key)"
                    >
                      <Filter class="w-3.5 h-3.5" />
                    </button>
                    
                    <div
                      v-if="filterVisible === col.key"
                      class="filter-dropdown"
                    >
                      <input 
                        v-model="columnFilters[col.key]"
                        type="text"
                        :placeholder="`筛选 ${col.label}...`"
                        class="filter-input"
                      >
                      <button 
                        v-if="columnFilters[col.key]"
                        class="clear-filter"
                        @click="clearFilter(col.key)"
                      >
                        <X class="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </th>
          </tr>
        </thead>
        
        <!-- Body -->
        <tbody>
          <tr 
            v-for="(row, index) in paginatedData" 
            :key="index"
            :class="{ selected: selectedRows.has(index) }"
            @click="handleRowClick(row, index)"
          >
            <td
              v-if="selectable"
              class="td-checkbox"
            >
              <input 
                type="checkbox"
                :checked="selectedRows.has(index)"
                @click.stop
                @change="toggleRowSelection(index)"
              >
            </td>
            <td 
              v-for="col in columns" 
              :key="col.key"
              :style="{ textAlign: col.align || 'left' }"
              class="td-cell"
            >
              {{ row[col.key] }}
            </td>
          </tr>
          
          <!-- Empty State -->
          <tr v-if="paginatedData.length === 0">
            <td
              :colspan="columns.length + (selectable ? 1 : 0)"
              class="empty-state"
            >
              暂无数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div
      v-if="pagination && totalPages > 1"
      class="table-pagination"
    >
      <button 
        class="page-btn"
        :disabled="currentPage === 1"
        @click="goToPage(currentPage - 1)"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>
      
      <span class="page-info">
        {{ currentPage }} / {{ totalPages }}
      </span>
      
      <button 
        class="page-btn"
        :disabled="currentPage === totalPages"
        @click="goToPage(currentPage + 1)"
      >
        <ChevronRight class="w-4 h-4" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.data-table {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--any-bg-primary);
  border-radius: var(--any-radius-lg);
  overflow: hidden;
}

/* Toolbar */
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--any-text-primary);
}

.row-count {
  font-size: 12px;
  color: var(--any-text-muted);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Search */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 8px;
  width: 14px;
  height: 14px;
  color: var(--any-text-muted);
}

.search-input {
  padding: 6px 8px 6px 28px;
  width: 180px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-primary);
}

.search-input:focus {
  outline: none;
  border-color: var(--td-state-thinking, #00D9FF);
}

.action-btn {
  padding: 6px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.action-btn:hover {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

/* Table Container */
.table-container {
  flex: 1;
  overflow: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

/* Header */
.th-cell {
  position: sticky;
  top: 0;
  padding: 10px 12px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
  font-weight: 500;
  color: var(--any-text-primary);
  white-space: nowrap;
}

.th-checkbox {
  width: 40px;
  padding: 10px;
  background: var(--any-bg-secondary);
  border-bottom: 1px solid var(--any-border);
}

.th-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.th-actions {
  display: flex;
  gap: 2px;
}

.sort-btn,
.filter-btn {
  padding: 2px;
  background: transparent;
  border: none;
  border-radius: var(--any-radius-sm);
  color: var(--any-text-muted);
  cursor: pointer;
  opacity: 0.5;
  transition: all 150ms ease;
}

.sort-btn:hover,
.filter-btn:hover,
.sort-btn.active,
.filter-btn.active {
  opacity: 1;
  color: var(--td-state-thinking, #00D9FF);
}

/* Filter Dropdown */
.filter-wrapper {
  position: relative;
}

.filter-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  padding: 8px;
  background: var(--any-bg-primary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  z-index: 10;
}

.filter-input {
  width: 150px;
  padding: 6px 8px;
  background: var(--any-bg-tertiary);
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  font-size: 12px;
  color: var(--any-text-primary);
}

.clear-filter {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  padding: 2px;
  background: transparent;
  border: none;
  color: var(--any-text-muted);
  cursor: pointer;
}

/* Body */
.td-cell {
  padding: 10px 12px;
  border-bottom: 1px solid var(--any-border);
  color: var(--any-text-secondary);
}

.td-checkbox {
  width: 40px;
  padding: 10px;
  border-bottom: 1px solid var(--any-border);
}

tbody tr {
  cursor: pointer;
  transition: background 150ms ease;
}

tbody tr:hover {
  background: var(--any-bg-hover);
}

tbody tr.selected {
  background: var(--td-state-thinking-bg);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--any-text-muted);
}

/* Pagination */
.table-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--any-bg-secondary);
  border-top: 1px solid var(--any-border);
}

.page-btn {
  padding: 6px;
  background: transparent;
  border: 1px solid var(--any-border);
  border-radius: var(--any-radius-sm);
  color: var(--any-text-secondary);
  cursor: pointer;
  transition: all 150ms ease;
}

.page-btn:hover:not(:disabled) {
  background: var(--any-bg-hover);
  color: var(--any-text-primary);
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: var(--any-text-secondary);
}
</style>
