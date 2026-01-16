<template>
  <div class="stock-search">
    <!-- Search Input -->
    <div class="search-input-wrapper">
      <div 
        class="search-input-container"
        :class="{ 'is-focused': isFocused, 'has-error': searchError }"
        @drop.prevent="handleDrop"
        @dragover.prevent
      >
        <input
          ref="inputRef"
          v-model="searchQuery"
          type="text"
          placeholder="输入股票代码或名称（如：600519 或 茅台）"
          class="search-input"
          @focus="handleFocus"
          @blur="handleBlur"
          @input="handleInput"
          @keydown.enter="handleEnter"
          @keydown.down.prevent="handleArrowDown"
          @keydown.up.prevent="handleArrowUp"
        />
        
        <!-- Clear Button -->
        <button
          v-if="searchQuery"
          class="clear-button"
          @click="clearSearch"
          aria-label="Clear search"
        >
          <svg class="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        <!-- Loading Indicator -->
        <div v-if="isSearching" class="loading-indicator">
          <svg class="spinner" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      </div>
      
      <!-- Error Message -->
      <p v-if="searchError" class="error-message">
        {{ searchError }}
      </p>
    </div>
    
    <!-- Suggestions Dropdown -->
    <div v-if="showSuggestions" class="suggestions-dropdown">
      <div
        v-for="(stock, index) in filteredSuggestions"
        :key="stock.symbol"
        class="suggestion-item"
        :class="{ 'is-active': index === selectedIndex }"
        @click="selectStock(stock)"
        @mouseenter="selectedIndex = index"
      >
        <div class="suggestion-content">
          <span class="stock-symbol">{{ stock.symbol }}</span>
          <span class="stock-name">{{ stock.name }}</span>
        </div>
        <span v-if="stock.market" class="stock-market">{{ stock.market }}</span>
      </div>
      
      <div v-if="filteredSuggestions.length === 0" class="no-results">
        未找到匹配的股票
      </div>
    </div>
    
    <!-- Quick Select (Hot Stocks) -->
    <div v-if="!searchQuery && !isFocused && showHotStocks" class="hot-stocks">
      <div class="hot-stocks-header">
        <span class="hot-stocks-title">热门股票</span>
      </div>
      <div class="hot-stocks-list">
        <button
          v-for="stock in hotStocks"
          :key="stock.symbol"
          class="hot-stock-button"
          @click="selectStock(stock)"
        >
          <span class="stock-symbol">{{ stock.symbol }}</span>
          <span class="stock-name">{{ stock.name }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useFinancialStore } from '@/stores/financial'

// Props
interface Props {
  showHotStocks?: boolean
  autoFocus?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showHotStocks: true,
  autoFocus: false,
})

// Emits
const emit = defineEmits<{
  select: [stock: StockItem]
  search: [query: string]
}>()

// Types
interface StockItem {
  symbol: string
  name: string
  market?: string
}

// Store
const financialStore = useFinancialStore()

// Refs
const inputRef = ref<HTMLInputElement>()
const searchQuery = ref('')
const isFocused = ref(false)
const isSearching = ref(false)
const searchError = ref('')
const selectedIndex = ref(-1)

// Hot stocks (常见股票)
const hotStocks = ref<StockItem[]>([
  { symbol: '600519', name: '贵州茅台', market: 'SH' },
  { symbol: '000858', name: '五粮液', market: 'SZ' },
  { symbol: '601318', name: '中国平安', market: 'SH' },
  { symbol: '600036', name: '招商银行', market: 'SH' },
  { symbol: '000001', name: '平安银行', market: 'SZ' },
  { symbol: '601888', name: '中国中免', market: 'SH' },
])

// All stocks database (simplified - in real app, fetch from API)
const stocksDatabase = ref<StockItem[]>([
  ...hotStocks.value,
  { symbol: '600030', name: '中信证券', market: 'SH' },
  { symbol: '600276', name: '恒瑞医药', market: 'SH' },
  { symbol: '600887', name: '伊利股份', market: 'SH' },
  { symbol: '000333', name: '美的集团', market: 'SZ' },
  { symbol: '002594', name: '比亚迪', market: 'SZ' },
  { symbol: '000651', name: '格力电器', market: 'SZ' },
])

// Computed
const showSuggestions = computed(() => {
  return isFocused.value && searchQuery.value.length > 0
})

const filteredSuggestions = computed(() => {
  if (!searchQuery.value) return []
  
  const query = searchQuery.value.toLowerCase().trim()
  
  return stocksDatabase.value.filter(stock => {
    return (
      stock.symbol.toLowerCase().includes(query) ||
      stock.name.toLowerCase().includes(query)
    )
  }).slice(0, 8) // Limit to 8 results
})

// Methods
function handleFocus() {
  isFocused.value = true
  selectedIndex.value = -1
}

function handleBlur() {
  // Delay to allow click on suggestions
  setTimeout(() => {
    isFocused.value = false
  }, 200)
}

function handleInput() {
  searchError.value = ''
  selectedIndex.value = -1
  
  if (searchQuery.value.length > 0) {
    emit('search', searchQuery.value)
  }
}

function handleEnter() {
  if (selectedIndex.value >= 0 && filteredSuggestions.value[selectedIndex.value]) {
    selectStock(filteredSuggestions.value[selectedIndex.value])
  } else if (searchQuery.value) {
    // Direct search by symbol
    searchBySymbol(searchQuery.value)
  }
}

function handleArrowDown() {
  if (selectedIndex.value < filteredSuggestions.value.length - 1) {
    selectedIndex.value++
  }
}

function handleArrowUp() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--
  }
}

function handleDrop(event: DragEvent) {
  const text = event.dataTransfer?.getData('text/plain')
  if (text) {
    searchQuery.value = text.trim()
    handleInput()
  }
}

function clearSearch() {
  searchQuery.value = ''
  searchError.value = ''
  selectedIndex.value = -1
  inputRef.value?.focus()
}

async function selectStock(stock: StockItem) {
  searchQuery.value = `${stock.symbol} ${stock.name}`
  emit('select', stock)
  
  // Fetch stock data
  isSearching.value = true
  searchError.value = ''
  
  try {
    await financialStore.fetchCombinedAnalysis(stock.symbol)
    isFocused.value = false
  } catch (error) {
    searchError.value = error instanceof Error ? error.message : '加载失败'
  } finally {
    isSearching.value = false
  }
}

async function searchBySymbol(symbol: string) {
  isSearching.value = true
  searchError.value = ''
  
  try {
    await financialStore.fetchCombinedAnalysis(symbol)
    emit('select', { symbol, name: symbol })
    isFocused.value = false
  } catch (error) {
    searchError.value = error instanceof Error ? error.message : '未找到该股票'
  } finally {
    isSearching.value = false
  }
}

// Lifecycle
onMounted(() => {
  if (props.autoFocus) {
    inputRef.value?.focus()
  }
})

// Keyboard shortcuts
function handleGlobalKeydown(event: KeyboardEvent) {
  // Ctrl/Cmd + K to focus search
  if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
    event.preventDefault()
    inputRef.value?.focus()
  }
  
  // Escape to blur
  if (event.key === 'Escape' && isFocused.value) {
    inputRef.value?.blur()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleGlobalKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style scoped>
.stock-search {
  position: relative;
  width: 100%;
}

/* Search Input */
.search-input-wrapper {
  margin-bottom: 0.5rem;
}

.search-input-container {
  position: relative;
  display: flex;
  align-items: center;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 200ms ease;
}

.search-input-container:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.search-input-container.is-focused {
  border-color: #111827;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.05);
}

.search-input-container.has-error {
  border-color: #ef4444;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.9375rem;
  color: #111827;
}

.search-input::placeholder {
  color: #9ca3af;
}

.clear-button {
  padding: 0.5rem;
  margin-right: 0.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #6b7280;
  transition: color 200ms ease;
}

.clear-button:hover {
  color: #111827;
}

.clear-button .icon {
  width: 1rem;
  height: 1rem;
}

.loading-indicator {
  padding: 0.5rem;
  margin-right: 0.5rem;
}

.spinner {
  width: 1rem;
  height: 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Error Message */
.error-message {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #ef4444;
}

/* Suggestions Dropdown */
.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 0.5rem;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  max-height: 20rem;
  overflow-y: auto;
  z-index: 50;
}

.suggestion-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background 200ms ease;
  border-bottom: 1px solid #f3f4f6;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-item:hover,
.suggestion-item.is-active {
  background: #f9fafb;
}

.suggestion-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stock-symbol {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #111827;
}

.stock-name {
  font-size: 0.875rem;
  color: #6b7280;
}

.stock-market {
  font-size: 0.75rem;
  padding: 0.125rem 0.5rem;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 4px;
}

.no-results {
  padding: 1.5rem;
  text-align: center;
  color: #9ca3af;
  font-size: 0.875rem;
}

/* Hot Stocks */
.hot-stocks {
  margin-top: 1rem;
}

.hot-stocks-header {
  margin-bottom: 0.75rem;
}

.hot-stocks-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
}

.hot-stocks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.hot-stock-button {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: #fafafa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 200ms ease;
  font-size: 0.875rem;
}

.hot-stock-button:hover {
  border-color: #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
}

.hot-stock-button:active {
  transform: scale(0.98);
}

.hot-stock-button .stock-symbol {
  font-weight: 600;
  color: #111827;
}

.hot-stock-button .stock-name {
  color: #6b7280;
}
</style>
