/**
 * Financial Store
 * 
 * Manages stock data, sentiment results, and caching.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import dayjs from 'dayjs'
import financialService from '@/services/financial'
import type {
  StockInfo,
  StockQuote,
  HistoricalData,
  SentimentResult,
  CombinedAnalysis,
  FinancialAnalysisResult,
  ValuationAnalysisResult,
  TechnicalAnalysisResult,
  ComprehensiveAnalysisResult,
} from '@/types/financial'

interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresIn: number // milliseconds
}

export const useFinancialStore = defineStore('financial', () => {
  // ==================== State ====================
  
  // Current stock being analyzed
  const currentSymbol = ref<string>('')
  
  // Stock data
  const stockInfo = ref<StockInfo | null>(null)
  const stockQuote = ref<StockQuote | null>(null)
  const historicalData = ref<HistoricalData | null>(null)
  
  // Sentiment data
  const sentimentResult = ref<SentimentResult | null>(null)
  
  // Combined analysis
  const combinedAnalysis = ref<CombinedAnalysis | null>(null)
  
  // Loading states
  const loadingStockInfo = ref(false)
  const loadingStockQuote = ref(false)
  const loadingHistorical = ref(false)
  const loadingSentiment = ref(false)
  const loadingCombined = ref(false)
  const loadingFinancialAnalysis = ref(false)
  const loadingValuationAnalysis = ref(false)
  const loadingTechnicalAnalysis = ref(false)
  const loadingComprehensiveAnalysis = ref(false)
  
  // Error states
  const stockInfoError = ref<string | null>(null)
  const stockQuoteError = ref<string | null>(null)
  const historicalError = ref<string | null>(null)
  const sentimentError = ref<string | null>(null)
  const combinedError = ref<string | null>(null)
  const financialAnalysisError = ref<string | null>(null)
  const valuationAnalysisError = ref<string | null>(null)
  const technicalAnalysisError = ref<string | null>(null)
  const comprehensiveAnalysisError = ref<string | null>(null)
  
  // Cache (symbol -> data)
  const cache = ref<Map<string, CacheEntry<any>>>(new Map())
  
  // Watch list
  const watchList = ref<string[]>([])
  
  // ==================== Getters ====================
  
  const hasStockData = computed(() => {
    return stockInfo.value !== null || stockQuote.value !== null
  })
  
  const hasSentimentData = computed(() => {
    return sentimentResult.value !== null
  })
  
  const isLoading = computed(() => {
    return (
      loadingStockInfo.value ||
      loadingStockQuote.value ||
      loadingHistorical.value ||
      loadingSentiment.value ||
      loadingCombined.value ||
      loadingFinancialAnalysis.value ||
      loadingValuationAnalysis.value ||
      loadingTechnicalAnalysis.value ||
      loadingComprehensiveAnalysis.value
    )
  })
  
  const hasError = computed(() => {
    return (
      stockInfoError.value ||
      stockQuoteError.value ||
      historicalError.value ||
      sentimentError.value ||
      combinedError.value ||
      financialAnalysisError.value ||
      valuationAnalysisError.value ||
      technicalAnalysisError.value ||
      comprehensiveAnalysisError.value
    )
  })
  
  const hasAnalysisResults = computed(() => {
    return financialAnalysis.value || valuationAnalysis.value || technicalAnalysis.value
  })
  
  // ==================== Cache Helpers ====================
  
  function getCacheKey(symbol: string, type: string): string {
    return `${symbol}:${type}`
  }
  
  function getCached<T>(symbol: string, type: string): T | null {
    const key = getCacheKey(symbol, type)
    const entry = cache.value.get(key)
    
    if (!entry) return null
    
    const now = Date.now()
    if (now - entry.timestamp > entry.expiresIn) {
      cache.value.delete(key)
      return null
    }
    
    return entry.data as T
  }
  
  function setCached<T>(symbol: string, type: string, data: T, expiresIn: number = 5 * 60 * 1000) {
    const key = getCacheKey(symbol, type)
    cache.value.set(key, {
      data,
      timestamp: Date.now(),
      expiresIn,
    })
  }
  
  // ==================== Actions ====================
  
  /**
   * Fetch stock basic information
   */
  async function fetchStockInfo(symbol: string, useCache = true) {
    // Check cache
    if (useCache) {
      const cached = getCached<StockInfo>(symbol, 'info')
      if (cached) {
        stockInfo.value = cached
        return
      }
    }
    
    loadingStockInfo.value = true
    stockInfoError.value = null
    
    try {
      const response = await financialService.getStockInfo({ symbol })
      
      if (response.success && response.data) {
        stockInfo.value = response.data
        setCached(symbol, 'info', response.data, 10 * 60 * 1000) // 10 min cache
      } else {
        stockInfoError.value = response.error || 'Failed to fetch stock info'
      }
    } catch (error) {
      stockInfoError.value = error instanceof Error ? error.message : 'Unknown error'
    } finally {
      loadingStockInfo.value = false
    }
  }
  
  /**
   * Fetch real-time stock quote
   */
  async function fetchStockQuote(symbol: string, useCache = true) {
    // Check cache (shorter expiry for quote)
    if (useCache) {
      const cached = getCached<StockQuote>(symbol, 'quote')
      if (cached) {
        stockQuote.value = cached
        return
      }
    }
    
    loadingStockQuote.value = true
    stockQuoteError.value = null
    
    try {
      const response = await financialService.getStockQuote({ symbol })
      
      if (response.success && response.data) {
        stockQuote.value = response.data
        setCached(symbol, 'quote', response.data, 60 * 1000) // 1 min cache
      } else {
        stockQuoteError.value = response.error || 'Failed to fetch quote'
      }
    } catch (error) {
      stockQuoteError.value = error instanceof Error ? error.message : 'Unknown error'
    } finally {
      loadingStockQuote.value = false
    }
  }
  
  /**
   * Fetch historical data
   */
  async function fetchHistoricalData(
    symbol: string,
    days: number = 30,
    useCache = true
  ) {
    const cacheKey = `historical_${days}`
    
    if (useCache) {
      const cached = getCached<HistoricalData>(symbol, cacheKey)
      if (cached) {
        historicalData.value = cached
        return
      }
    }
    
    loadingHistorical.value = true
    historicalError.value = null
    
    try {
      const endDate = dayjs()
      const startDate = endDate.subtract(days, 'day')
      
      const response = await financialService.getHistoricalData({
        symbol,
        start_date: startDate.format('YYYY-MM-DD'),
        end_date: endDate.format('YYYY-MM-DD'),
      })
      
      if (response.success && response.data) {
        historicalData.value = response.data
        setCached(symbol, cacheKey, response.data, 30 * 60 * 1000) // 30 min cache
      } else {
        historicalError.value = response.error || 'Failed to fetch historical data'
      }
    } catch (error) {
      historicalError.value = error instanceof Error ? error.message : 'Unknown error'
    } finally {
      loadingHistorical.value = false
    }
  }
  
  /**
   * Analyze sentiment
   */
  async function analyzeSentiment(
    symbol: string,
    sources: ('xueqiu' | 'guba')[] = ['xueqiu', 'guba'],
    limit: number = 20
  ) {
    loadingSentiment.value = true
    sentimentError.value = null
    
    try {
      const response = await financialService.analyzeSentiment({
        symbol,
        sources,
        limit_per_source: limit,
      })
      
      if (response.success && response.data) {
        sentimentResult.value = response.data
      } else {
        sentimentError.value = response.error || 'Failed to analyze sentiment'
      }
    } catch (error) {
      sentimentError.value = error instanceof Error ? error.message : 'Unknown error'
    } finally {
      loadingSentiment.value = false
    }
  }
  
  /**
   * Fetch combined analysis
   */
  async function fetchCombinedAnalysis(
    symbol: string,
    sentimentSources: ('xueqiu' | 'guba')[] = ['xueqiu', 'guba'],
    sentimentLimit: number = 20,
    historicalDays: number = 30
  ) {
    currentSymbol.value = symbol
    loadingCombined.value = true
    combinedError.value = null
    
    try {
      const response = await financialService.getCombinedAnalysis({
        symbol,
        sentiment_sources: sentimentSources,
        sentiment_limit: sentimentLimit,
        historical_days: historicalDays,
      })
      
      if (response.success && response.data) {
        combinedAnalysis.value = response.data
        
        // Update individual states
        if (response.data.stock_info) stockInfo.value = response.data.stock_info
        if (response.data.quote) stockQuote.value = response.data.quote
        if (response.data.historical) historicalData.value = response.data.historical
        if (response.data.sentiment) sentimentResult.value = response.data.sentiment
      } else {
        combinedError.value = response.error || 'Failed to fetch combined analysis'
      }
    } catch (error) {
      combinedError.value = error instanceof Error ? error.message : 'Unknown error'
    } finally {
      loadingCombined.value = false
    }
  }
  
  /**
   * Reset current stock data
   */
  function resetCurrentStock() {
    currentSymbol.value = ''
    stockInfo.value = null
    stockQuote.value = null
    historicalData.value = null
    sentimentResult.value = null
    combinedAnalysis.value = null
    
    stockInfoError.value = null
    stockQuoteError.value = null
    historicalError.value = null
    sentimentError.value = null
    combinedError.value = null
  }
  
  /**
   * Add to watch list
   */
  function addToWatchList(symbol: string) {
    if (!watchList.value.includes(symbol)) {
      watchList.value.push(symbol)
      // Persist to localStorage
      localStorage.setItem('financial:watchList', JSON.stringify(watchList.value))
    }
  }
  
  /**
   * Remove from watch list
   */
  function removeFromWatchList(symbol: string) {
    const index = watchList.value.indexOf(symbol)
    if (index !== -1) {
      watchList.value.splice(index, 1)
      localStorage.setItem('financial:watchList', JSON.stringify(watchList.value))
    }
  }
  
  /**
   * Load watch list from localStorage
   */
  function loadWatchList() {
    const saved = localStorage.getItem('financial:watchList')
    if (saved) {
      try {
        watchList.value = JSON.parse(saved)
      } catch (error) {
        console.error('Failed to load watch list:', error)
      }
    }
  }
  
  /**
   * Clear cache
   */
  function clearCache() {
    cache.value.clear()
  }
  
  // ==================== 分析引擎 Actions ====================
  
  /**
   * 运行财务分析
   */
  async function runFinancialAnalysis(symbol: string, market?: string) {
    loadingFinancialAnalysis.value = true
    financialAnalysisError.value = null
    
    try {
      const response = await financialService.runFinancialAnalysis({ symbol, market })
      
      if (response.success && response.data) {
        financialAnalysis.value = response.data
      } else {
        financialAnalysisError.value = response.error || '财务分析失败'
      }
    } catch (error) {
      financialAnalysisError.value = error instanceof Error ? error.message : '未知错误'
    } finally {
      loadingFinancialAnalysis.value = false
    }
  }
  
  /**
   * 运行估值分析
   */
  async function runValuationAnalysis(symbol: string, market?: string) {
    loadingValuationAnalysis.value = true
    valuationAnalysisError.value = null
    
    try {
      const response = await financialService.runValuationAnalysis({ symbol, market })
      
      if (response.success && response.data) {
        valuationAnalysis.value = response.data
      } else {
        valuationAnalysisError.value = response.error || '估值分析失败'
      }
    } catch (error) {
      valuationAnalysisError.value = error instanceof Error ? error.message : '未知错误'
    } finally {
      loadingValuationAnalysis.value = false
    }
  }
  
  /**
   * 运行技术分析
   */
  async function runTechnicalAnalysis(symbol: string, market?: string) {
    loadingTechnicalAnalysis.value = true
    technicalAnalysisError.value = null
    
    try {
      const response = await financialService.runTechnicalAnalysis({ symbol, market })
      
      if (response.success && response.data) {
        technicalAnalysis.value = response.data
      } else {
        technicalAnalysisError.value = response.error || '技术分析失败'
      }
    } catch (error) {
      technicalAnalysisError.value = error instanceof Error ? error.message : '未知错误'
    } finally {
      loadingTechnicalAnalysis.value = false
    }
  }
  
  /**
   * 运行综合分析
   */
  async function runComprehensiveAnalysis(
    symbol: string,
    market?: string,
    includeTechnical = true
  ) {
    loadingComprehensiveAnalysis.value = true
    comprehensiveAnalysisError.value = null
    
    // 同时设置各个子分析的 loading
    loadingFinancialAnalysis.value = true
    loadingValuationAnalysis.value = true
    if (includeTechnical) loadingTechnicalAnalysis.value = true
    
    try {
      const response = await financialService.runComprehensiveAnalysis({
        symbol,
        market,
        include_technical: includeTechnical,
      })
      
      if (response.success && response.data) {
        comprehensiveAnalysis.value = response.data
        
        // 更新各个子分析结果
        if (response.data.financial && !('error' in response.data.financial)) {
          financialAnalysis.value = response.data.financial as FinancialAnalysisResult
        }
        if (response.data.valuation && !('error' in response.data.valuation)) {
          valuationAnalysis.value = response.data.valuation as ValuationAnalysisResult
        }
        if (response.data.technical && !('error' in response.data.technical)) {
          technicalAnalysis.value = response.data.technical as TechnicalAnalysisResult
        }
      } else {
        comprehensiveAnalysisError.value = response.error || '综合分析失败'
      }
    } catch (error) {
      comprehensiveAnalysisError.value = error instanceof Error ? error.message : '未知错误'
    } finally {
      loadingComprehensiveAnalysis.value = false
      loadingFinancialAnalysis.value = false
      loadingValuationAnalysis.value = false
      loadingTechnicalAnalysis.value = false
    }
  }
  
  /**
   * 清除分析结果
   */
  function clearAnalysisResults() {
    financialAnalysis.value = null
    valuationAnalysis.value = null
    technicalAnalysis.value = null
    comprehensiveAnalysis.value = null
    
    financialAnalysisError.value = null
    valuationAnalysisError.value = null
    technicalAnalysisError.value = null
    comprehensiveAnalysisError.value = null
  }
  
  // Load watch list on init
  loadWatchList()
  
  return {
    // State
    currentSymbol,
    stockInfo,
    stockQuote,
    historicalData,
    sentimentResult,
    combinedAnalysis,
    watchList,
    
    // 分析引擎结果
    financialAnalysis,
    valuationAnalysis,
    technicalAnalysis,
    comprehensiveAnalysis,
    
    // Loading states
    loadingStockInfo,
    loadingStockQuote,
    loadingHistorical,
    loadingSentiment,
    loadingCombined,
    loadingFinancialAnalysis,
    loadingValuationAnalysis,
    loadingTechnicalAnalysis,
    loadingComprehensiveAnalysis,
    isLoading,
    
    // Error states
    stockInfoError,
    stockQuoteError,
    historicalError,
    sentimentError,
    combinedError,
    financialAnalysisError,
    valuationAnalysisError,
    technicalAnalysisError,
    comprehensiveAnalysisError,
    hasError,
    
    // Getters
    hasStockData,
    hasSentimentData,
    hasAnalysisResults,
    
    // Actions
    fetchStockInfo,
    fetchStockQuote,
    fetchHistoricalData,
    analyzeSentiment,
    fetchCombinedAnalysis,
    resetCurrentStock,
    addToWatchList,
    removeFromWatchList,
    loadWatchList,
    clearCache,
    
    // 分析引擎 Actions
    runFinancialAnalysis,
    runValuationAnalysis,
    runTechnicalAnalysis,
    runComprehensiveAnalysis,
    clearAnalysisResults,
  }
})
