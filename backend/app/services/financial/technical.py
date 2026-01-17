# -*- coding: utf-8 -*-
"""
TechnicalIndicators - 技术指标计算服务

实现常用技术指标计算：
1. 趋势指标 (MACD, 均线)
2. 动量指标 (RSI, KDJ, WILLR)
3. 波动率指标 (布林带, ATR)
4. 成交量指标 (OBV, 量比)
5. 综合技术评分

使用方法：
    service = TechnicalIndicators()
    result = await service.analyze("AAPL")
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入 pandas 和 pandas-ta
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    PANDAS_TA_AVAILABLE = False
    ta = None


class TrendSignal(str, Enum):
    """趋势信号"""
    STRONG_BUY = "strong_buy"      # 强烈看多
    BUY = "buy"                     # 看多
    NEUTRAL = "neutral"             # 中性
    SELL = "sell"                   # 看空
    STRONG_SELL = "strong_sell"    # 强烈看空


@dataclass
class TrendIndicators:
    """趋势类指标"""
    # MACD
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    macd_signal_type: str = ""  # "golden_cross", "death_cross", "above_zero", "below_zero"
    
    # 均线
    sma_5: Optional[float] = None
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_60: Optional[float] = None
    sma_120: Optional[float] = None
    sma_250: Optional[float] = None
    
    # EMA
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    
    # 均线排列
    ma_alignment: str = ""  # "bullish" (多头排列), "bearish" (空头排列), "mixed"
    
    # 趋势强度 ADX
    adx: Optional[float] = None
    plus_di: Optional[float] = None
    minus_di: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "macd": {
                "value": self.macd,
                "signal": self.macd_signal,
                "histogram": self.macd_histogram,
                "signal_type": self.macd_signal_type,
            },
            "moving_averages": {
                "sma_5": self.sma_5,
                "sma_10": self.sma_10,
                "sma_20": self.sma_20,
                "sma_60": self.sma_60,
                "sma_120": self.sma_120,
                "sma_250": self.sma_250,
                "ema_12": self.ema_12,
                "ema_26": self.ema_26,
                "alignment": self.ma_alignment,
            },
            "adx": {
                "value": self.adx,
                "plus_di": self.plus_di,
                "minus_di": self.minus_di,
            },
        }


@dataclass
class MomentumIndicators:
    """动量类指标"""
    # RSI (相对强弱指数)
    rsi_6: Optional[float] = None
    rsi_14: Optional[float] = None
    rsi_signal: str = ""  # "overbought", "oversold", "neutral"
    
    # KDJ (随机指标)
    k: Optional[float] = None
    d: Optional[float] = None
    j: Optional[float] = None
    kdj_signal: str = ""
    
    # 威廉指标
    willr: Optional[float] = None
    willr_signal: str = ""
    
    # CCI (商品通道指数)
    cci: Optional[float] = None
    
    # ROC (变动率)
    roc: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rsi": {
                "rsi_6": self.rsi_6,
                "rsi_14": self.rsi_14,
                "signal": self.rsi_signal,
            },
            "kdj": {
                "k": self.k,
                "d": self.d,
                "j": self.j,
                "signal": self.kdj_signal,
            },
            "willr": {
                "value": self.willr,
                "signal": self.willr_signal,
            },
            "cci": self.cci,
            "roc": self.roc,
        }


@dataclass
class VolatilityIndicators:
    """波动率类指标"""
    # 布林带
    boll_upper: Optional[float] = None
    boll_middle: Optional[float] = None
    boll_lower: Optional[float] = None
    boll_width: Optional[float] = None
    boll_position: Optional[float] = None  # 当前价格在布林带中的位置 (0-1)
    boll_signal: str = ""  # "near_upper", "near_lower", "middle"
    
    # ATR (平均真实波幅)
    atr: Optional[float] = None
    atr_percent: Optional[float] = None  # ATR 占价格的百分比
    
    # 历史波动率
    volatility_20d: Optional[float] = None
    volatility_60d: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bollinger_bands": {
                "upper": self.boll_upper,
                "middle": self.boll_middle,
                "lower": self.boll_lower,
                "width": self.boll_width,
                "position": self.boll_position,
                "signal": self.boll_signal,
            },
            "atr": {
                "value": self.atr,
                "percent": self.atr_percent,
            },
            "volatility": {
                "20d": self.volatility_20d,
                "60d": self.volatility_60d,
            },
        }


@dataclass
class VolumeIndicators:
    """成交量类指标"""
    # OBV (能量潮)
    obv: Optional[float] = None
    obv_trend: str = ""  # "rising", "falling", "flat"
    
    # 量比
    volume_ratio: Optional[float] = None
    
    # 成交量均线
    volume_sma_5: Optional[float] = None
    volume_sma_20: Optional[float] = None
    
    # 换手率
    turnover_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "obv": {
                "value": self.obv,
                "trend": self.obv_trend,
            },
            "volume_ratio": self.volume_ratio,
            "volume_ma": {
                "sma_5": self.volume_sma_5,
                "sma_20": self.volume_sma_20,
            },
            "turnover_rate": self.turnover_rate,
        }


@dataclass
class TechnicalAnalysisResult:
    """技术分析结果"""
    symbol: str
    current_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 各类指标
    trend: TrendIndicators = field(default_factory=TrendIndicators)
    momentum: MomentumIndicators = field(default_factory=MomentumIndicators)
    volatility: VolatilityIndicators = field(default_factory=VolatilityIndicators)
    volume: VolumeIndicators = field(default_factory=VolumeIndicators)
    
    # 综合评分
    technical_score: float = 50.0  # 0-100, >60 偏多, <40 偏空
    overall_signal: TrendSignal = TrendSignal.NEUTRAL
    
    # 支撑位和阻力位
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # 信号汇总
    buy_signals: List[str] = field(default_factory=list)
    sell_signals: List[str] = field(default_factory=list)
    summary: str = ""
    
    # 元数据
    data_source: str = ""
    data_period: str = ""  # 数据周期
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "timestamp": self.timestamp.isoformat(),
            "trend": self.trend.to_dict(),
            "momentum": self.momentum.to_dict(),
            "volatility": self.volatility.to_dict(),
            "volume": self.volume.to_dict(),
            "technical_score": self.technical_score,
            "overall_signal": self.overall_signal.value,
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "buy_signals": self.buy_signals,
            "sell_signals": self.sell_signals,
            "summary": self.summary,
            "data_source": self.data_source,
            "data_period": self.data_period,
        }


class TechnicalIndicators:
    """
    技术指标服务
    
    计算股票的各类技术指标并生成综合评估。
    """
    
    def __init__(self):
        """初始化技术指标服务"""
        self._financial_tool = None
        
        if not PANDAS_AVAILABLE:
            logger.warning("pandas is not installed. Technical analysis will be limited.")
        if not PANDAS_TA_AVAILABLE:
            logger.warning("pandas-ta is not installed. Some indicators may not be available.")
    
    def _get_financial_tool(self):
        """懒加载金融数据工具"""
        if self._financial_tool is None:
            from app.agent.tools.builtin.financial import get_financial_tool
            self._financial_tool = get_financial_tool()
        return self._financial_tool
    
    async def analyze(
        self,
        symbol: str,
        market: str = "auto",
        period: str = "1y",
    ) -> TechnicalAnalysisResult:
        """
        执行技术分析
        
        Args:
            symbol: 股票代码
            market: 市场类型
            period: 分析周期
            
        Returns:
            TechnicalAnalysisResult: 技术分析结果
        """
        logger.info(f"Starting technical analysis for {symbol}")
        
        result = TechnicalAnalysisResult(symbol=symbol)
        result.data_period = period
        
        if not PANDAS_AVAILABLE:
            result.summary = "技术分析需要 pandas 库，请安装: pip install pandas"
            return result
        
        try:
            tool = self._get_financial_tool()
            
            # 获取历史价格数据
            historical_data = await tool.get_historical(symbol, market=market)
            
            if not historical_data.success or not historical_data.data:
                result.summary = f"无法获取历史数据: {historical_data.error}"
                return result
            
            # 转换为 DataFrame
            df = self._to_dataframe(historical_data.data)
            
            if df.empty or len(df) < 20:
                result.summary = "历史数据不足，无法进行技术分析"
                return result
            
            # 获取当前价格
            result.current_price = float(df['close'].iloc[-1])
            
            # 计算各类指标
            result.trend = self._calculate_trend_indicators(df)
            result.momentum = self._calculate_momentum_indicators(df)
            result.volatility = self._calculate_volatility_indicators(df)
            result.volume = self._calculate_volume_indicators(df)
            
            # 计算支撑位和阻力位
            result.support_levels = self._find_support_levels(df)
            result.resistance_levels = self._find_resistance_levels(df)
            
            # 综合评分
            result.technical_score = self._calculate_technical_score(result)
            result.overall_signal = self._determine_signal(result)
            
            # 汇总信号
            result.buy_signals = self._collect_buy_signals(result)
            result.sell_signals = self._collect_sell_signals(result)
            
            # 生成总结
            result.summary = self._generate_summary(result)
            
            result.data_source = historical_data.source
            
            logger.info(
                f"Technical analysis completed for {symbol}, "
                f"score: {result.technical_score}, signal: {result.overall_signal.value}"
            )
            
        except Exception as e:
            logger.error(f"Technical analysis failed for {symbol}: {e}")
            result.summary = f"技术分析失败: {str(e)}"
        
        return result
    
    def _to_dataframe(self, data: List[Dict[str, Any]]) -> "pd.DataFrame":
        """将数据转换为 DataFrame"""
        df = pd.DataFrame(data)
        
        # 标准化列名
        column_mapping = {
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close',
        }
        
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                # 尝试小写匹配
                for orig_col in df.columns:
                    if orig_col.lower() == col:
                        df[col] = df[orig_col]
                        break
        
        # 转换数值类型
        for col in required_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期排序
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _calculate_trend_indicators(self, df: "pd.DataFrame") -> TrendIndicators:
        """计算趋势指标"""
        indicators = TrendIndicators()
        
        try:
            close = df['close']
            
            # 均线
            indicators.sma_5 = float(close.rolling(5).mean().iloc[-1])
            indicators.sma_10 = float(close.rolling(10).mean().iloc[-1])
            indicators.sma_20 = float(close.rolling(20).mean().iloc[-1])
            
            if len(df) >= 60:
                indicators.sma_60 = float(close.rolling(60).mean().iloc[-1])
            if len(df) >= 120:
                indicators.sma_120 = float(close.rolling(120).mean().iloc[-1])
            if len(df) >= 250:
                indicators.sma_250 = float(close.rolling(250).mean().iloc[-1])
            
            # EMA
            indicators.ema_12 = float(close.ewm(span=12).mean().iloc[-1])
            indicators.ema_26 = float(close.ewm(span=26).mean().iloc[-1])
            
            # MACD
            if PANDAS_TA_AVAILABLE:
                macd_result = ta.macd(close)
                if macd_result is not None and not macd_result.empty:
                    indicators.macd = float(macd_result.iloc[-1, 0])
                    indicators.macd_signal = float(macd_result.iloc[-1, 1])
                    indicators.macd_histogram = float(macd_result.iloc[-1, 2])
                    
                    # 判断 MACD 信号
                    if len(macd_result) >= 2:
                        prev_macd = macd_result.iloc[-2, 0]
                        prev_signal = macd_result.iloc[-2, 1]
                        
                        if indicators.macd > indicators.macd_signal and prev_macd <= prev_signal:
                            indicators.macd_signal_type = "golden_cross"
                        elif indicators.macd < indicators.macd_signal and prev_macd >= prev_signal:
                            indicators.macd_signal_type = "death_cross"
                        elif indicators.macd > 0:
                            indicators.macd_signal_type = "above_zero"
                        else:
                            indicators.macd_signal_type = "below_zero"
                
                # ADX
                adx_result = ta.adx(df['high'], df['low'], close)
                if adx_result is not None and not adx_result.empty:
                    indicators.adx = float(adx_result.iloc[-1, 0])
                    indicators.plus_di = float(adx_result.iloc[-1, 1])
                    indicators.minus_di = float(adx_result.iloc[-1, 2])
            else:
                # 手动计算 MACD
                exp1 = close.ewm(span=12, adjust=False).mean()
                exp2 = close.ewm(span=26, adjust=False).mean()
                macd_line = exp1 - exp2
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                
                indicators.macd = float(macd_line.iloc[-1])
                indicators.macd_signal = float(signal_line.iloc[-1])
                indicators.macd_histogram = float(macd_line.iloc[-1] - signal_line.iloc[-1])
            
            # 判断均线排列
            current_price = float(close.iloc[-1])
            if (indicators.sma_5 and indicators.sma_10 and indicators.sma_20 and
                current_price > indicators.sma_5 > indicators.sma_10 > indicators.sma_20):
                indicators.ma_alignment = "bullish"
            elif (indicators.sma_5 and indicators.sma_10 and indicators.sma_20 and
                  current_price < indicators.sma_5 < indicators.sma_10 < indicators.sma_20):
                indicators.ma_alignment = "bearish"
            else:
                indicators.ma_alignment = "mixed"
            
        except Exception as e:
            logger.warning(f"Trend indicators calculation error: {e}")
        
        return indicators
    
    def _calculate_momentum_indicators(self, df: "pd.DataFrame") -> MomentumIndicators:
        """计算动量指标"""
        indicators = MomentumIndicators()
        
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            
            if PANDAS_TA_AVAILABLE:
                # RSI
                rsi_6 = ta.rsi(close, length=6)
                rsi_14 = ta.rsi(close, length=14)
                
                if rsi_6 is not None and not rsi_6.empty:
                    indicators.rsi_6 = float(rsi_6.iloc[-1])
                if rsi_14 is not None and not rsi_14.empty:
                    indicators.rsi_14 = float(rsi_14.iloc[-1])
                
                # 判断 RSI 信号
                if indicators.rsi_14:
                    if indicators.rsi_14 > 70:
                        indicators.rsi_signal = "overbought"
                    elif indicators.rsi_14 < 30:
                        indicators.rsi_signal = "oversold"
                    else:
                        indicators.rsi_signal = "neutral"
                
                # KDJ (Stochastic)
                stoch = ta.stoch(high, low, close)
                if stoch is not None and not stoch.empty:
                    indicators.k = float(stoch.iloc[-1, 0])
                    indicators.d = float(stoch.iloc[-1, 1])
                    indicators.j = 3 * indicators.k - 2 * indicators.d
                    
                    if indicators.k > 80 and indicators.d > 80:
                        indicators.kdj_signal = "overbought"
                    elif indicators.k < 20 and indicators.d < 20:
                        indicators.kdj_signal = "oversold"
                    else:
                        indicators.kdj_signal = "neutral"
                
                # Williams %R
                willr = ta.willr(high, low, close)
                if willr is not None and not willr.empty:
                    indicators.willr = float(willr.iloc[-1])
                    if indicators.willr > -20:
                        indicators.willr_signal = "overbought"
                    elif indicators.willr < -80:
                        indicators.willr_signal = "oversold"
                    else:
                        indicators.willr_signal = "neutral"
                
                # CCI
                cci = ta.cci(high, low, close)
                if cci is not None and not cci.empty:
                    indicators.cci = float(cci.iloc[-1])
                
                # ROC
                roc = ta.roc(close, length=12)
                if roc is not None and not roc.empty:
                    indicators.roc = float(roc.iloc[-1])
            
            else:
                # 手动计算 RSI
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators.rsi_14 = float(rsi.iloc[-1])
                
                if indicators.rsi_14 > 70:
                    indicators.rsi_signal = "overbought"
                elif indicators.rsi_14 < 30:
                    indicators.rsi_signal = "oversold"
                else:
                    indicators.rsi_signal = "neutral"
            
        except Exception as e:
            logger.warning(f"Momentum indicators calculation error: {e}")
        
        return indicators
    
    def _calculate_volatility_indicators(self, df: "pd.DataFrame") -> VolatilityIndicators:
        """计算波动率指标"""
        indicators = VolatilityIndicators()
        
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            current_price = float(close.iloc[-1])
            
            if PANDAS_TA_AVAILABLE:
                # 布林带
                bbands = ta.bbands(close, length=20, std=2)
                if bbands is not None and not bbands.empty:
                    indicators.boll_lower = float(bbands.iloc[-1, 0])
                    indicators.boll_middle = float(bbands.iloc[-1, 1])
                    indicators.boll_upper = float(bbands.iloc[-1, 2])
                    indicators.boll_width = float(bbands.iloc[-1, 3])
                    
                    # 计算价格在布林带中的位置
                    if indicators.boll_upper != indicators.boll_lower:
                        indicators.boll_position = (
                            (current_price - indicators.boll_lower) /
                            (indicators.boll_upper - indicators.boll_lower)
                        )
                    
                    if indicators.boll_position and indicators.boll_position > 0.9:
                        indicators.boll_signal = "near_upper"
                    elif indicators.boll_position and indicators.boll_position < 0.1:
                        indicators.boll_signal = "near_lower"
                    else:
                        indicators.boll_signal = "middle"
                
                # ATR
                atr = ta.atr(high, low, close, length=14)
                if atr is not None and not atr.empty:
                    indicators.atr = float(atr.iloc[-1])
                    indicators.atr_percent = indicators.atr / current_price * 100
            
            else:
                # 手动计算布林带
                sma = close.rolling(20).mean()
                std = close.rolling(20).std()
                indicators.boll_upper = float((sma + 2 * std).iloc[-1])
                indicators.boll_middle = float(sma.iloc[-1])
                indicators.boll_lower = float((sma - 2 * std).iloc[-1])
            
            # 历史波动率
            returns = close.pct_change()
            indicators.volatility_20d = float(returns.rolling(20).std().iloc[-1] * (252 ** 0.5) * 100)
            if len(df) >= 60:
                indicators.volatility_60d = float(returns.rolling(60).std().iloc[-1] * (252 ** 0.5) * 100)
            
        except Exception as e:
            logger.warning(f"Volatility indicators calculation error: {e}")
        
        return indicators
    
    def _calculate_volume_indicators(self, df: "pd.DataFrame") -> VolumeIndicators:
        """计算成交量指标"""
        indicators = VolumeIndicators()
        
        try:
            close = df['close']
            volume = df['volume']
            
            if PANDAS_TA_AVAILABLE:
                # OBV
                obv = ta.obv(close, volume)
                if obv is not None and not obv.empty:
                    indicators.obv = float(obv.iloc[-1])
                    
                    # 判断 OBV 趋势
                    obv_sma = obv.rolling(10).mean()
                    if obv.iloc[-1] > obv_sma.iloc[-1]:
                        indicators.obv_trend = "rising"
                    else:
                        indicators.obv_trend = "falling"
            
            # 成交量均线
            indicators.volume_sma_5 = float(volume.rolling(5).mean().iloc[-1])
            indicators.volume_sma_20 = float(volume.rolling(20).mean().iloc[-1])
            
            # 量比
            if indicators.volume_sma_5 and indicators.volume_sma_5 > 0:
                indicators.volume_ratio = float(volume.iloc[-1]) / indicators.volume_sma_5
            
        except Exception as e:
            logger.warning(f"Volume indicators calculation error: {e}")
        
        return indicators
    
    def _find_support_levels(self, df: "pd.DataFrame") -> List[float]:
        """寻找支撑位"""
        supports = []
        
        try:
            low = df['low']
            
            # 简单方法：使用最近的低点
            recent_lows = low.tail(60).nsmallest(5).values
            supports = [round(float(x), 2) for x in sorted(recent_lows)]
            
        except Exception as e:
            logger.warning(f"Support level calculation error: {e}")
        
        return supports[:3]
    
    def _find_resistance_levels(self, df: "pd.DataFrame") -> List[float]:
        """寻找阻力位"""
        resistances = []
        
        try:
            high = df['high']
            
            # 简单方法：使用最近的高点
            recent_highs = high.tail(60).nlargest(5).values
            resistances = [round(float(x), 2) for x in sorted(recent_highs, reverse=True)]
            
        except Exception as e:
            logger.warning(f"Resistance level calculation error: {e}")
        
        return resistances[:3]
    
    def _calculate_technical_score(self, result: TechnicalAnalysisResult) -> float:
        """计算综合技术评分"""
        score = 50.0
        
        # MACD 贡献 (权重 20%)
        if result.trend.macd_signal_type == "golden_cross":
            score += 10
        elif result.trend.macd_signal_type == "death_cross":
            score -= 10
        elif result.trend.macd_signal_type == "above_zero":
            score += 5
        elif result.trend.macd_signal_type == "below_zero":
            score -= 5
        
        # 均线排列 (权重 15%)
        if result.trend.ma_alignment == "bullish":
            score += 8
        elif result.trend.ma_alignment == "bearish":
            score -= 8
        
        # RSI 贡献 (权重 15%)
        if result.momentum.rsi_signal == "oversold":
            score += 8
        elif result.momentum.rsi_signal == "overbought":
            score -= 8
        
        # KDJ 贡献 (权重 10%)
        if result.momentum.kdj_signal == "oversold":
            score += 5
        elif result.momentum.kdj_signal == "overbought":
            score -= 5
        
        # 布林带位置 (权重 10%)
        if result.volatility.boll_signal == "near_lower":
            score += 5
        elif result.volatility.boll_signal == "near_upper":
            score -= 5
        
        # OBV 趋势 (权重 10%)
        if result.volume.obv_trend == "rising":
            score += 5
        elif result.volume.obv_trend == "falling":
            score -= 5
        
        # ADX 趋势强度 (权重 10%)
        if result.trend.adx and result.trend.adx > 25:
            if result.trend.plus_di and result.trend.minus_di:
                if result.trend.plus_di > result.trend.minus_di:
                    score += 5
                else:
                    score -= 5
        
        return round(max(0, min(100, score)), 1)
    
    def _determine_signal(self, result: TechnicalAnalysisResult) -> TrendSignal:
        """确定综合信号"""
        score = result.technical_score
        
        if score >= 70:
            return TrendSignal.STRONG_BUY
        elif score >= 55:
            return TrendSignal.BUY
        elif score >= 45:
            return TrendSignal.NEUTRAL
        elif score >= 30:
            return TrendSignal.SELL
        else:
            return TrendSignal.STRONG_SELL
    
    def _collect_buy_signals(self, result: TechnicalAnalysisResult) -> List[str]:
        """收集买入信号"""
        signals = []
        
        if result.trend.macd_signal_type == "golden_cross":
            signals.append("MACD 金叉")
        if result.trend.ma_alignment == "bullish":
            signals.append("均线多头排列")
        if result.momentum.rsi_signal == "oversold":
            signals.append("RSI 超卖")
        if result.momentum.kdj_signal == "oversold":
            signals.append("KDJ 超卖")
        if result.volatility.boll_signal == "near_lower":
            signals.append("触及布林带下轨")
        if result.volume.obv_trend == "rising":
            signals.append("OBV 上升")
        
        return signals
    
    def _collect_sell_signals(self, result: TechnicalAnalysisResult) -> List[str]:
        """收集卖出信号"""
        signals = []
        
        if result.trend.macd_signal_type == "death_cross":
            signals.append("MACD 死叉")
        if result.trend.ma_alignment == "bearish":
            signals.append("均线空头排列")
        if result.momentum.rsi_signal == "overbought":
            signals.append("RSI 超买")
        if result.momentum.kdj_signal == "overbought":
            signals.append("KDJ 超买")
        if result.volatility.boll_signal == "near_upper":
            signals.append("触及布林带上轨")
        if result.volume.obv_trend == "falling":
            signals.append("OBV 下降")
        
        return signals
    
    def _generate_summary(self, result: TechnicalAnalysisResult) -> str:
        """生成技术分析总结"""
        signal_text = {
            TrendSignal.STRONG_BUY: "强烈看多",
            TrendSignal.BUY: "偏多",
            TrendSignal.NEUTRAL: "中性观望",
            TrendSignal.SELL: "偏空",
            TrendSignal.STRONG_SELL: "强烈看空",
        }
        
        summary = f"{result.symbol} 技术面{signal_text.get(result.overall_signal, '未知')}"
        summary += f"，综合评分 {result.technical_score}"
        
        if result.buy_signals:
            summary += f"。买入信号：{', '.join(result.buy_signals[:3])}"
        
        if result.sell_signals:
            summary += f"。卖出信号：{', '.join(result.sell_signals[:3])}"
        
        summary += "。技术分析仅供参考，不构成投资建议。"
        
        return summary


# 单例实例
_technical_instance: Optional[TechnicalIndicators] = None


def get_technical_indicators() -> TechnicalIndicators:
    """获取技术指标服务实例"""
    global _technical_instance
    if _technical_instance is None:
        _technical_instance = TechnicalIndicators()
    return _technical_instance


__all__ = [
    "TechnicalIndicators",
    "TechnicalAnalysisResult",
    "TrendIndicators",
    "MomentumIndicators",
    "VolatilityIndicators",
    "VolumeIndicators",
    "TrendSignal",
    "get_technical_indicators",
]
