/**
 * Financial data types for TokenDance.
 * 
 * Matches backend API responses.
 */

export interface StockInfo {
  symbol: string
  name: string
  market: string
  price?: number
  market_cap?: string
  industry?: string
  description?: string
}

export interface StockQuote {
  symbol: string
  current_price: number
  change: number
  change_percent: number
  open: number
  high: number
  low: number
  volume: number
  timestamp?: string
}

export interface HistoricalRecord {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface HistoricalData {
  symbol: string
  records: HistoricalRecord[]
  period: string
  start_date: string
  end_date: string
}

export interface SentimentPost {
  id: string
  content: string
  author: string
  timestamp: string | null
  url: string
  likes: number
  comments: number
  reposts: number
  source: string
  symbol: string
  sentiment_score?: number
  sentiment_label?: 'bullish' | 'bearish' | 'neutral'
  key_points?: string[]
}

export interface SentimentAnalysis {
  overall_score: number  // -1 (bearish) to 1 (bullish)
  overall_label: 'bullish' | 'bearish' | 'neutral'
  confidence: number  // 0 to 1
  bullish_count: number
  bearish_count: number
  neutral_count: number
  key_bullish_points: string[]
  key_bearish_points: string[]
  trending_topics: string[]
  analyzed_count: number
  error?: string
}

export interface SentimentResult {
  success: boolean
  symbol: string
  analysis: SentimentAnalysis | null
  posts: SentimentPost[]
  sources_used: string[]
  errors: string[]
  timestamp: string
  disclaimer: string
}

export interface CombinedAnalysis {
  stock_info: StockInfo | null
  quote: StockQuote | null
  historical: HistoricalData | null
  sentiment: SentimentResult | null
}

// API Request types
export interface StockInfoRequest {
  symbol: string
}

export interface StockQuoteRequest {
  symbol: string
}

export interface HistoricalDataRequest {
  symbol: string
  start_date?: string
  end_date?: string
  period?: '1d' | '1wk' | '1mo'
}

export interface SentimentAnalyzeRequest {
  symbol: string
  sources?: ('xueqiu' | 'guba')[]
  limit_per_source?: number
  analyze?: boolean
}

export interface SentimentSearchRequest {
  query: string
  sources?: ('xueqiu' | 'guba')[]
  limit?: number
}

export interface CombinedAnalysisRequest {
  symbol: string
  sentiment_sources?: ('xueqiu' | 'guba')[]
  sentiment_limit?: number
  historical_days?: number
}

// API Response types
export interface APIResponse<T> {
  success: boolean
  data?: T
  error?: string
  errors?: string[]
  disclaimer?: string
}
