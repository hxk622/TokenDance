# -*- coding: utf-8 -*-
"""
金融分析引擎单元测试

测试覆盖:
1. FinancialAnalyzer - 财务分析
2. ValuationAnalyzer - 估值分析
3. TechnicalIndicators - 技术指标
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import asdict

from app.services.financial.analyzer import (
    FinancialAnalyzer,
    FinancialAnalysisResult,
    HealthLevel,
    ProfitabilityMetrics,
    GrowthMetrics,
    SolvencyMetrics,
    EfficiencyMetrics,
    CashFlowMetrics,
)
from app.services.financial.valuation import (
    ValuationAnalyzer,
    ValuationResult,
    ValuationLevel,
    RelativeValuation,
    HistoricalValuation,
    IndustryComparison,
    DCFValuation,
)
from app.services.financial.technical import (
    TechnicalIndicators,
    TechnicalAnalysisResult,
    TrendSignal,
    TrendIndicators,
    MomentumIndicators,
    VolatilityIndicators,
    VolumeIndicators,
)


# ============================================================
# FinancialAnalyzer Tests
# ============================================================

class TestFinancialAnalyzerDataClasses:
    """测试财务分析数据类"""
    
    def test_profitability_metrics_to_dict(self):
        """测试盈利能力指标序列化"""
        metrics = ProfitabilityMetrics(
            gross_margin=45.5,
            net_margin=12.3,
            roe=18.5,
            roa=8.2,
            score=75.0,
            grade="A",
            analysis="盈利能力良好"
        )
        result = metrics.to_dict()
        
        assert result["gross_margin"] == 45.5
        assert result["net_margin"] == 12.3
        assert result["roe"] == 18.5
        assert result["score"] == 75.0
        assert result["grade"] == "A"
    
    def test_growth_metrics_to_dict(self):
        """测试成长能力指标序列化"""
        metrics = GrowthMetrics(
            revenue_growth=15.5,
            net_income_growth=20.3,
            eps_growth=18.2,
            revenue_cagr_3y=12.5,
            score=70.0,
            grade="B+",
        )
        result = metrics.to_dict()
        
        assert result["revenue_growth"] == 15.5
        assert result["net_income_growth"] == 20.3
        assert result["score"] == 70.0
    
    def test_solvency_metrics_to_dict(self):
        """测试偿债能力指标序列化"""
        metrics = SolvencyMetrics(
            current_ratio=2.5,
            quick_ratio=1.8,
            debt_to_assets=0.45,
            debt_to_equity=0.82,
            interest_coverage=8.5,
            score=80.0,
        )
        result = metrics.to_dict()
        
        assert result["current_ratio"] == 2.5
        assert result["quick_ratio"] == 1.8
        assert result["debt_to_assets"] == 0.45
    
    def test_efficiency_metrics_to_dict(self):
        """测试运营效率指标序列化"""
        metrics = EfficiencyMetrics(
            inventory_turnover=8.5,
            inventory_days=43,
            receivables_turnover=12.0,
            asset_turnover=0.85,
            score=65.0,
        )
        result = metrics.to_dict()
        
        assert result["inventory_turnover"] == 8.5
        assert result["inventory_days"] == 43
    
    def test_cash_flow_metrics_to_dict(self):
        """测试现金流指标序列化"""
        metrics = CashFlowMetrics(
            operating_cash_flow=1000000,
            free_cash_flow=800000,
            ocf_to_net_income=1.2,
            score=72.0,
        )
        result = metrics.to_dict()
        
        assert result["operating_cash_flow"] == 1000000
        assert result["free_cash_flow"] == 800000
        assert result["ocf_to_net_income"] == 1.2
    
    def test_financial_analysis_result_to_dict(self):
        """测试财务分析结果完整序列化"""
        result = FinancialAnalysisResult(
            symbol="AAPL",
            company_name="Apple Inc.",
            market="us",
            overall_score=78.5,
            health_level=HealthLevel.GOOD,
            summary="财务状况良好",
            strengths=["盈利能力强", "现金流充裕"],
            weaknesses=["增速放缓"],
        )
        
        data = result.to_dict()
        
        assert data["symbol"] == "AAPL"
        assert data["company_name"] == "Apple Inc."
        assert data["overall_score"] == 78.5
        assert data["health_level"] == "good"
        assert len(data["strengths"]) == 2
        assert len(data["weaknesses"]) == 1


class TestHealthLevel:
    """测试健康等级枚举"""
    
    def test_health_level_values(self):
        """测试健康等级值"""
        assert HealthLevel.EXCELLENT.value == "excellent"
        assert HealthLevel.GOOD.value == "good"
        assert HealthLevel.FAIR.value == "fair"
        assert HealthLevel.POOR.value == "poor"
        assert HealthLevel.CRITICAL.value == "critical"


class TestFinancialAnalyzer:
    """测试财务分析器"""
    
    def test_weights_sum_to_one(self):
        """测试权重和为1"""
        analyzer = FinancialAnalyzer()
        total = sum(analyzer.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001
    
    def test_weights_all_positive(self):
        """测试权重都是正数"""
        analyzer = FinancialAnalyzer()
        for weight in analyzer.WEIGHTS.values():
            assert weight > 0
    
    @pytest.mark.asyncio
    async def test_analyze_with_mock_data(self):
        """测试使用模拟数据进行分析"""
        analyzer = FinancialAnalyzer()
        
        # Mock 金融数据工具
        mock_tool = MagicMock()
        mock_fundamental = MagicMock()
        mock_fundamental.success = True
        mock_fundamental.data = {
            "income_statement": {
                "revenue": 100000000,
                "cost_of_revenue": 60000000,
                "gross_profit": 40000000,
                "operating_income": 25000000,
                "net_income": 20000000,
            },
            "balance_sheet": {
                "total_assets": 200000000,
                "total_equity": 120000000,
                "current_assets": 80000000,
                "current_liabilities": 40000000,
            },
            "cash_flow_statement": {
                "operating_cash_flow": 25000000,
                "investing_cash_flow": -10000000,
                "financing_cash_flow": -5000000,
            },
        }
        mock_fundamental.source = "mock"
        mock_tool.get_fundamental = AsyncMock(return_value=mock_fundamental)
        
        mock_valuation = MagicMock()
        mock_valuation.success = True
        mock_valuation.data = {"pe": 25, "pb": 5}
        mock_tool.get_valuation = AsyncMock(return_value=mock_valuation)
        
        with patch.object(analyzer, '_get_financial_tool', return_value=mock_tool):
            result = await analyzer.analyze("AAPL")
        
        assert result.symbol == "AAPL"
        assert result.profitability.gross_margin is not None
        assert result.overall_score >= 0
        assert result.overall_score <= 100


# ============================================================
# ValuationAnalyzer Tests
# ============================================================

class TestValuationAnalyzerDataClasses:
    """测试估值分析数据类"""
    
    def test_relative_valuation_to_dict(self):
        """测试相对估值序列化"""
        valuation = RelativeValuation(
            pe_ttm=25.5,
            pe_forward=22.0,
            pb=5.2,
            ps=4.8,
            peg=1.5,
            market_cap=2500000000000,
        )
        result = valuation.to_dict()
        
        assert result["pe_ttm"] == 25.5
        assert result["pe_forward"] == 22.0
        assert result["pb"] == 5.2
        assert result["peg"] == 1.5
    
    def test_historical_valuation_to_dict(self):
        """测试历史估值序列化"""
        valuation = HistoricalValuation(
            pe_min_5y=15.0,
            pe_max_5y=40.0,
            pe_avg_5y=25.0,
            pe_percentile=65.0,
            pb_min_5y=3.0,
            pb_max_5y=8.0,
        )
        result = valuation.to_dict()
        
        assert result["pe"]["min_5y"] == 15.0
        assert result["pe"]["max_5y"] == 40.0
        assert result["pe"]["percentile"] == 65.0
    
    def test_industry_comparison_to_dict(self):
        """测试行业对比序列化"""
        comparison = IndustryComparison(
            industry="Technology",
            sector="Consumer Electronics",
            industry_pe_avg=22.0,
            pe_premium=15.0,
        )
        result = comparison.to_dict()
        
        assert result["industry"] == "Technology"
        assert result["industry_pe_avg"] == 22.0
        assert result["pe_premium"] == 15.0
    
    def test_dcf_valuation_to_dict(self):
        """测试 DCF 估值序列化"""
        dcf = DCFValuation(
            growth_rate_5y=0.15,
            terminal_growth=0.03,
            discount_rate=0.10,
            intrinsic_value=180.0,
            current_price=150.0,
            upside_potential=20.0,
        )
        result = dcf.to_dict()
        
        assert result["assumptions"]["growth_rate_5y"] == 0.15
        assert result["intrinsic_value"] == 180.0
        assert result["upside_potential"] == 20.0


class TestValuationLevel:
    """测试估值水平枚举"""
    
    def test_valuation_level_values(self):
        """测试估值水平值"""
        assert ValuationLevel.SEVERELY_UNDERVALUED.value == "severely_undervalued"
        assert ValuationLevel.UNDERVALUED.value == "undervalued"
        assert ValuationLevel.FAIRLY_VALUED.value == "fairly_valued"
        assert ValuationLevel.OVERVALUED.value == "overvalued"
        assert ValuationLevel.SEVERELY_OVERVALUED.value == "severely_overvalued"


class TestValuationAnalyzer:
    """测试估值分析器"""
    
    def test_weights_sum_to_one(self):
        """测试权重和为1"""
        analyzer = ValuationAnalyzer()
        total = sum(analyzer.WEIGHTS.values())
        assert abs(total - 1.0) < 0.001
    
    def test_percentile_thresholds_ordered(self):
        """测试分位数阈值有序"""
        analyzer = ValuationAnalyzer()
        thresholds = analyzer.PERCENTILE_THRESHOLDS
        
        assert thresholds["severely_undervalued"] < thresholds["undervalued"]
        assert thresholds["undervalued"] < thresholds["fairly_valued_low"]
        assert thresholds["fairly_valued_high"] < thresholds["overvalued"]
        assert thresholds["overvalued"] < thresholds["severely_overvalued"]
    
    @pytest.mark.asyncio
    async def test_analyze_with_mock_data(self):
        """测试使用模拟数据进行估值分析"""
        analyzer = ValuationAnalyzer()
        
        mock_tool = MagicMock()
        
        # Mock 估值数据
        mock_valuation = MagicMock()
        mock_valuation.success = True
        mock_valuation.data = {
            "pe": 25.0,
            "pb": 5.0,
            "ps": 6.0,
            "peg": 1.5,
            "market_cap": 2500000000000,
        }
        mock_valuation.source = "mock"
        mock_tool.get_valuation = AsyncMock(return_value=mock_valuation)
        
        # Mock 报价数据
        mock_quote = MagicMock()
        mock_quote.success = True
        mock_quote.data = {"price": 150.0}
        mock_tool.get_quote = AsyncMock(return_value=mock_quote)
        
        # Mock 基本面数据
        mock_fundamental = MagicMock()
        mock_fundamental.success = True
        mock_fundamental.data = {
            "cash_flow_statement": {"free_cash_flow": 100000000},
        }
        mock_tool.get_fundamental = AsyncMock(return_value=mock_fundamental)
        
        with patch.object(analyzer, '_get_financial_tool', return_value=mock_tool):
            result = await analyzer.analyze("AAPL")
        
        assert result.symbol == "AAPL"
        assert result.current_price == 150.0
        assert result.relative.pe_ttm == 25.0
        assert result.valuation_score >= 0
        assert result.valuation_score <= 100


# ============================================================
# TechnicalIndicators Tests
# ============================================================

class TestTechnicalIndicatorsDataClasses:
    """测试技术指标数据类"""
    
    def test_trend_indicators_to_dict(self):
        """测试趋势指标序列化"""
        trend = TrendIndicators(
            macd=0.5,
            macd_signal=0.3,
            macd_histogram=0.2,
            macd_signal_type="golden_cross",
            sma_5=150.0,
            sma_20=148.0,
            sma_60=145.0,
            ma_alignment="bullish",
            adx=25.0,
        )
        result = trend.to_dict()
        
        assert result["macd"]["value"] == 0.5
        assert result["macd"]["signal_type"] == "golden_cross"
        assert result["moving_averages"]["sma_5"] == 150.0
        assert result["moving_averages"]["alignment"] == "bullish"
    
    def test_momentum_indicators_to_dict(self):
        """测试动量指标序列化"""
        momentum = MomentumIndicators(
            rsi_14=65.0,
            rsi_signal="neutral",
            k=70.0,
            d=65.0,
            j=80.0,
            kdj_signal="overbought",
            willr=-25.0,
        )
        result = momentum.to_dict()
        
        assert result["rsi"]["rsi_14"] == 65.0
        assert result["kdj"]["k"] == 70.0
        assert result["kdj"]["signal"] == "overbought"
    
    def test_volatility_indicators_to_dict(self):
        """测试波动率指标序列化"""
        volatility = VolatilityIndicators(
            boll_upper=160.0,
            boll_middle=150.0,
            boll_lower=140.0,
            boll_width=0.13,
            boll_position=0.7,
            atr=3.5,
            atr_percent=2.3,
        )
        result = volatility.to_dict()
        
        assert result["bollinger_bands"]["upper"] == 160.0
        assert result["bollinger_bands"]["middle"] == 150.0
        assert result["bollinger_bands"]["position"] == 0.7
        assert result["atr"]["value"] == 3.5
    
    def test_volume_indicators_to_dict(self):
        """测试成交量指标序列化"""
        volume = VolumeIndicators(
            obv=1000000,
            obv_trend="rising",
            volume_ratio=1.5,
            turnover_rate=2.3,
        )
        result = volume.to_dict()
        
        assert result["obv"]["value"] == 1000000
        assert result["obv"]["trend"] == "rising"
        assert result["volume_ratio"] == 1.5


class TestTrendSignal:
    """测试趋势信号枚举"""
    
    def test_trend_signal_values(self):
        """测试趋势信号值"""
        assert TrendSignal.STRONG_BUY.value == "strong_buy"
        assert TrendSignal.BUY.value == "buy"
        assert TrendSignal.NEUTRAL.value == "neutral"
        assert TrendSignal.SELL.value == "sell"
        assert TrendSignal.STRONG_SELL.value == "strong_sell"


class TestTechnicalAnalysisResult:
    """测试技术分析结果"""
    
    def test_technical_analysis_result_to_dict(self):
        """测试技术分析结果序列化"""
        result = TechnicalAnalysisResult(
            symbol="AAPL",
            current_price=150.0,
            technical_score=65.0,
            overall_signal=TrendSignal.BUY,
            support_levels=[145.0, 140.0, 135.0],
            resistance_levels=[155.0, 160.0],
            buy_signals=["MACD 金叉", "RSI 超卖反弹"],
            sell_signals=[],
            summary="技术面偏多",
        )
        
        data = result.to_dict()
        
        assert data["symbol"] == "AAPL"
        assert data["current_price"] == 150.0
        assert data["technical_score"] == 65.0
        assert data["overall_signal"] == "buy"
        assert len(data["support_levels"]) == 3
        assert len(data["buy_signals"]) == 2


class TestTechnicalIndicators:
    """测试技术指标服务"""
    
    def test_initialization(self):
        """测试初始化"""
        service = TechnicalIndicators()
        assert service._financial_tool is None
    
    @pytest.mark.asyncio
    async def test_analyze_without_pandas(self):
        """测试无 pandas 时的分析"""
        service = TechnicalIndicators()
        
        # Mock pandas 不可用
        with patch('app.services.financial.technical.PANDAS_AVAILABLE', False):
            result = await service.analyze("AAPL")
        
        # 应该返回错误提示
        assert result.symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_analyze_with_mock_data(self):
        """测试使用模拟数据进行技术分析"""
        service = TechnicalIndicators()
        
        mock_tool = MagicMock()
        
        # Mock 历史数据
        mock_historical = MagicMock()
        mock_historical.success = True
        mock_historical.data = [
            {"date": "2024-01-01", "open": 145, "high": 148, "low": 144, "close": 147, "volume": 1000000},
            {"date": "2024-01-02", "open": 147, "high": 150, "low": 146, "close": 149, "volume": 1100000},
            {"date": "2024-01-03", "open": 149, "high": 152, "low": 148, "close": 151, "volume": 1200000},
        ] * 10  # 30 天数据
        mock_historical.source = "mock"
        mock_tool.get_historical = AsyncMock(return_value=mock_historical)
        
        with patch.object(service, '_get_financial_tool', return_value=mock_tool):
            result = await service.analyze("AAPL")
        
        assert result.symbol == "AAPL"
        # 数据足够时应该能计算出价格
        assert result.current_price is not None


# ============================================================
# Integration Tests
# ============================================================

class TestAnalysisEngineIntegration:
    """分析引擎集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_analysis_pipeline(self):
        """测试完整分析流程"""
        # 创建三个分析器
        financial_analyzer = FinancialAnalyzer()
        valuation_analyzer = ValuationAnalyzer()
        technical_service = TechnicalIndicators()
        
        # Mock 共享的金融工具
        mock_tool = MagicMock()
        
        # 设置 mock 返回值
        mock_fundamental = MagicMock()
        mock_fundamental.success = True
        mock_fundamental.data = {
            "income_statement": {"revenue": 100000000, "net_income": 15000000},
            "balance_sheet": {"total_assets": 200000000, "total_equity": 100000000},
            "cash_flow_statement": {"operating_cash_flow": 20000000},
        }
        mock_fundamental.source = "mock"
        
        mock_valuation = MagicMock()
        mock_valuation.success = True
        mock_valuation.data = {"pe": 20, "pb": 3, "ps": 5}
        mock_valuation.source = "mock"
        
        mock_quote = MagicMock()
        mock_quote.success = True
        mock_quote.data = {"price": 150.0}
        
        mock_historical = MagicMock()
        mock_historical.success = True
        mock_historical.data = [
            {"date": f"2024-01-{i:02d}", "open": 145+i, "high": 148+i, "low": 144+i, "close": 147+i, "volume": 1000000+i*10000}
            for i in range(1, 31)
        ]
        mock_historical.source = "mock"
        
        mock_tool.get_fundamental = AsyncMock(return_value=mock_fundamental)
        mock_tool.get_valuation = AsyncMock(return_value=mock_valuation)
        mock_tool.get_quote = AsyncMock(return_value=mock_quote)
        mock_tool.get_historical = AsyncMock(return_value=mock_historical)
        
        # 执行三种分析
        with patch.object(financial_analyzer, '_get_financial_tool', return_value=mock_tool), \
             patch.object(valuation_analyzer, '_get_financial_tool', return_value=mock_tool), \
             patch.object(technical_service, '_get_financial_tool', return_value=mock_tool):
            
            financial_result = await financial_analyzer.analyze("AAPL")
            valuation_result = await valuation_analyzer.analyze("AAPL")
            technical_result = await technical_service.analyze("AAPL")
        
        # 验证结果
        assert financial_result.symbol == "AAPL"
        assert valuation_result.symbol == "AAPL"
        assert technical_result.symbol == "AAPL"
        
        # 结果应该可以序列化
        assert isinstance(financial_result.to_dict(), dict)
        assert isinstance(valuation_result.to_dict(), dict)
        assert isinstance(technical_result.to_dict(), dict)


# ============================================================
# Edge Cases & Error Handling
# ============================================================

class TestEdgeCases:
    """边界情况测试"""
    
    def test_profitability_with_none_values(self):
        """测试盈利能力指标包含 None 值"""
        metrics = ProfitabilityMetrics()
        result = metrics.to_dict()
        
        assert result["gross_margin"] is None
        assert result["net_margin"] is None
        assert result["roe"] is None
    
    def test_health_level_all_values_covered(self):
        """测试所有健康等级值都被覆盖"""
        levels = list(HealthLevel)
        assert len(levels) == 5
        
        score_ranges = [
            (90, HealthLevel.EXCELLENT),
            (70, HealthLevel.GOOD),
            (50, HealthLevel.FAIR),
            (30, HealthLevel.POOR),
            (10, HealthLevel.CRITICAL),
        ]
        
        for score, expected in score_ranges:
            assert expected in levels
    
    def test_valuation_level_all_values_covered(self):
        """测试所有估值水平值都被覆盖"""
        levels = list(ValuationLevel)
        assert len(levels) == 5
    
    def test_trend_signal_all_values_covered(self):
        """测试所有趋势信号值都被覆盖"""
        signals = list(TrendSignal)
        assert len(signals) == 5
    
    @pytest.mark.asyncio
    async def test_analyzer_handles_api_failure(self):
        """测试分析器处理 API 失败"""
        analyzer = FinancialAnalyzer()
        
        mock_tool = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.data = None
        mock_result.error = "API Error"
        mock_tool.get_fundamental = AsyncMock(return_value=mock_result)
        mock_tool.get_valuation = AsyncMock(return_value=mock_result)
        
        with patch.object(analyzer, '_get_financial_tool', return_value=mock_tool):
            result = await analyzer.analyze("INVALID")
        
        # 应该返回结果但分数为 0
        assert result.symbol == "INVALID"
        assert result.overall_score == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
