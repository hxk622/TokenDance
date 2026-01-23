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
  pe_ratio?: number
}

export interface StockQuote {
  symbol: string
  current_price: number
  change: number
  change_percent: number
  change_amount?: number
  open: number
  high: number
  low: number
  volume: number
  turnover_rate?: number
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

// Alias for backward compatibility
export type HistoricalDataPoint = HistoricalRecord

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

// ==================== 分析引擎类型 ====================

/**
 * 分析请求
 */
export interface AnalysisRequest {
  symbol: string
  market?: 'cn' | 'us' | 'hk'
}

/**
 * 综合分析请求
 */
export interface ComprehensiveAnalysisRequest {
  symbol: string
  market?: 'cn' | 'us' | 'hk'
  include_technical?: boolean
}

/**
 * 财务健康度等级
 */
export type HealthLevel = 'excellent' | 'good' | 'fair' | 'poor' | 'critical'

/**
 * 财务分析结果
 */
export interface FinancialAnalysisResult {
  symbol: string
  market: string
  overall_score: number  // 0-100
  health_level: HealthLevel
  dimension_scores: {
    profitability: number
    growth: number
    solvency: number
    efficiency: number
    cash_flow: number
  }
  profitability: {
    roe: number | null
    roa: number | null
    gross_margin: number | null
    net_margin: number | null
    score: number
  }
  growth: {
    revenue_growth: number | null
    net_income_growth: number | null
    eps_growth: number | null
    score: number
  }
  solvency: {
    debt_to_assets: number | null
    current_ratio: number | null
    quick_ratio: number | null
    interest_coverage: number | null
    score: number
  }
  efficiency: {
    asset_turnover: number | null
    inventory_turnover: number | null
    receivables_turnover: number | null
    score: number
  }
  cash_flow: {
    operating_cf: number | null
    free_cf: number | null
    cf_to_net_income: number | null
    score: number
  }
  strengths: string[]
  key_risks: string[]
  summary: string
  analyzed_at: string
}

/**
 * 估值水平
 */
export type ValuationLevel = 'extremely_low' | 'low' | 'fair' | 'high' | 'extremely_high'

/**
 * 估值分析结果
 */
export interface ValuationAnalysisResult {
  symbol: string
  market: string
  valuation_level: ValuationLevel
  current_price: number
  relative: {
    pe_ttm: number | null
    pb: number | null
    ps: number | null
    ev_ebitda: number | null
    peg: number | null
    market_cap: number | null
  }
  historical: {
    pe_percentile: number | null
    pb_percentile: number | null
    ps_percentile: number | null
    pe_5y_avg: number | null
    pb_5y_avg: number | null
  } | null
  industry: {
    industry_name: string | null
    pe_vs_industry: number | null
    pb_vs_industry: number | null
    premium_discount: number | null
  } | null
  dcf: {
    intrinsic_value: number | null
    discount_rate: number | null
    terminal_growth: number | null
    margin_of_safety: number | null
  } | null
  target_price_range: {
    low: number
    mid: number
    high: number
    confidence: 'low' | 'medium' | 'high'
  }
  key_points: string[]
  risks: string[]
  summary: string
  analyzed_at: string
}

/**
 * 技术信号
 */
export type TechnicalSignal = 'strong_buy' | 'buy' | 'neutral' | 'sell' | 'strong_sell'

/**
 * 技术分析结果
 */
export interface TechnicalAnalysisResult {
  symbol: string
  market: string
  overall_signal: TechnicalSignal
  score: number  // 0-100
  trend: {
    macd: {
      value: number | null
      signal: number | null
      histogram: number | null
      signal_type: 'bullish' | 'bearish' | 'neutral'
    }
    moving_averages: {
      sma_20: number | null
      sma_50: number | null
      sma_200: number | null
      ema_12: number | null
      ema_26: number | null
      golden_cross: boolean
      death_cross: boolean
    }
    adx: number | null
  }
  momentum: {
    rsi: {
      value: number | null
      signal: 'overbought' | 'oversold' | 'neutral'
    }
    kdj: {
      k: number | null
      d: number | null
      j: number | null
      signal: 'bullish' | 'bearish' | 'neutral'
    }
    williams_r: number | null
    cci: number | null
    roc: number | null
  }
  volatility: {
    bollinger: {
      upper: number | null
      middle: number | null
      lower: number | null
      position: 'above_upper' | 'upper_half' | 'lower_half' | 'below_lower'
    }
    atr: number | null
    historical_volatility: number | null
  }
  volume: {
    obv: number | null
    obv_trend: 'rising' | 'falling' | 'flat'
    volume_ratio: number | null
  }
  support_levels: number[]
  resistance_levels: number[]
  buy_signals: string[]
  sell_signals: string[]
  summary: string
  analyzed_at: string
}

/**
 * 综合分析结果
 */
export interface ComprehensiveAnalysisResult {
  symbol: string
  market: string
  financial: FinancialAnalysisResult | { error: string } | null
  valuation: ValuationAnalysisResult | { error: string } | null
  technical: TechnicalAnalysisResult | { error: string } | null
  summary: string
  generated_at: string
}
