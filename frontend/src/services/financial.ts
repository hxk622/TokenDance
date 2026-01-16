/**
 * Financial API Service
 * 
 * Wraps all Financial API calls with proper error handling and caching.
 */

import type {
  StockInfo,
  StockQuote,
  HistoricalData,
  SentimentResult,
  CombinedAnalysis,
  StockInfoRequest,
  StockQuoteRequest,
  HistoricalDataRequest,
  SentimentAnalyzeRequest,
  SentimentSearchRequest,
  CombinedAnalysisRequest,
  APIResponse,
} from '@/types/financial'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const FINANCIAL_API = `${API_BASE_URL}/financial`

/**
 * Generic API call wrapper with error handling
 */
async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<APIResponse<T>> {
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: `HTTP ${response.status}: ${response.statusText}`,
      }))
      return {
        success: false,
        error: error.error || error.detail || 'Request failed',
      }
    }

    const data = await response.json()
    return data
  } catch (error) {
    console.error('API call failed:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Financial API Service
 */
export const financialService = {
  /**
   * Get stock basic information
   */
  async getStockInfo(request: StockInfoRequest): Promise<APIResponse<StockInfo>> {
    return apiCall<StockInfo>(`${FINANCIAL_API}/stock/info`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Get real-time stock quote
   */
  async getStockQuote(request: StockQuoteRequest): Promise<APIResponse<StockQuote>> {
    return apiCall<StockQuote>(`${FINANCIAL_API}/stock/quote`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Get historical stock data
   */
  async getHistoricalData(
    request: HistoricalDataRequest
  ): Promise<APIResponse<HistoricalData>> {
    return apiCall<HistoricalData>(`${FINANCIAL_API}/stock/historical`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Analyze sentiment for a stock
   */
  async analyzeSentiment(
    request: SentimentAnalyzeRequest
  ): Promise<APIResponse<SentimentResult>> {
    return apiCall<SentimentResult>(`${FINANCIAL_API}/sentiment/analyze`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Search sentiment posts
   */
  async searchSentiment(
    request: SentimentSearchRequest
  ): Promise<APIResponse<SentimentResult>> {
    return apiCall<SentimentResult>(`${FINANCIAL_API}/sentiment/search`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Get combined analysis (data + sentiment)
   */
  async getCombinedAnalysis(
    request: CombinedAnalysisRequest
  ): Promise<APIResponse<CombinedAnalysis>> {
    return apiCall<CombinedAnalysis>(`${FINANCIAL_API}/combined`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<APIResponse<{ status: string; service: string }>> {
    return apiCall(`${FINANCIAL_API}/health`, {
      method: 'GET',
    })
  },
}

export default financialService
