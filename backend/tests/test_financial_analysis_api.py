# -*- coding: utf-8 -*-
"""
金融分析 API 集成测试

测试覆盖 /api/v1/financial/analysis/* 端点:
1. /analysis/financial - 财务分析
2. /analysis/valuation - 估值分析
3. /analysis/technical - 技术分析
4. /analysis/comprehensive - 综合分析
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.financial import (
    router,
    AnalysisRequest,
    ComprehensiveAnalysisRequest,
    _detect_market,
)
from app.services.financial.analyzer import FinancialAnalysisResult, HealthLevel
from app.services.financial.valuation import ValuationResult, ValuationLevel
from app.services.financial.technical import TechnicalAnalysisResult, TrendSignal


# ============================================================
# Test Setup
# ============================================================

@pytest.fixture
def app():
    """Create test app with financial router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/financial")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_financial_result():
    """Create mock financial analysis result."""
    return FinancialAnalysisResult(
        symbol="AAPL",
        company_name="Apple Inc.",
        market="us",
        overall_score=78.5,
        health_level=HealthLevel.GOOD,
        summary="财务状况良好，盈利能力强。",
        strengths=["盈利能力强", "现金流充裕"],
        weaknesses=["增速放缓"],
        key_risks=["市场竞争加剧"],
    )


@pytest.fixture
def mock_valuation_result():
    """Create mock valuation analysis result."""
    return ValuationResult(
        symbol="AAPL",
        company_name="Apple Inc.",
        market="us",
        current_price=150.0,
        valuation_level=ValuationLevel.FAIRLY_VALUED,
        valuation_score=52.0,
        target_price=165.0,
        upside_potential=10.0,
        summary="估值处于合理区间。",
        key_points=["PE 处于历史中位"],
        risks=["增长放缓可能影响估值"],
    )


@pytest.fixture
def mock_technical_result():
    """Create mock technical analysis result."""
    return TechnicalAnalysisResult(
        symbol="AAPL",
        current_price=150.0,
        technical_score=65.0,
        overall_signal=TrendSignal.BUY,
        support_levels=[145.0, 140.0],
        resistance_levels=[155.0, 160.0],
        buy_signals=["MACD 金叉", "RSI 超卖反弹"],
        sell_signals=[],
        summary="技术面偏多，短期看涨。",
    )


# ============================================================
# Market Detection Tests
# ============================================================

class TestMarketDetection:
    """测试市场识别功能"""
    
    def test_detect_cn_market(self):
        """测试识别 A 股"""
        assert _detect_market("600519") == "cn"
        assert _detect_market("000001") == "cn"
        assert _detect_market("300001") == "cn"
    
    def test_detect_us_market(self):
        """测试识别美股"""
        assert _detect_market("AAPL") == "us"
        assert _detect_market("MSFT") == "us"
        assert _detect_market("GOOG") == "us"
    
    def test_detect_hk_market(self):
        """测试识别港股"""
        assert _detect_market("0700.HK") == "hk"
        assert _detect_market("9988.HK") == "hk"
    
    def test_detect_default_market(self):
        """测试默认市场"""
        # 无法识别的格式默认返回 cn
        assert _detect_market("INVALID123") == "cn"


# ============================================================
# Request Model Tests
# ============================================================

class TestRequestModels:
    """测试请求模型"""
    
    def test_analysis_request_validation(self):
        """测试分析请求验证"""
        request = AnalysisRequest(symbol="AAPL")
        assert request.symbol == "AAPL"
        assert request.market is None
    
    def test_analysis_request_with_market(self):
        """测试带市场的分析请求"""
        request = AnalysisRequest(symbol="600519", market="cn")
        assert request.symbol == "600519"
        assert request.market == "cn"
    
    def test_comprehensive_request_defaults(self):
        """测试综合分析请求默认值"""
        request = ComprehensiveAnalysisRequest(symbol="AAPL")
        assert request.symbol == "AAPL"
        assert request.include_technical is True


# ============================================================
# API Endpoint Tests
# ============================================================

class TestFinancialAnalysisAPI:
    """测试财务分析 API"""
    
    def test_financial_analysis_success(self, client, mock_financial_result):
        """测试财务分析成功"""
        with patch('app.api.v1.financial._get_financial_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_financial_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/financial",
                json={"symbol": "AAPL"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["overall_score"] == 78.5
        assert data["data"]["health_level"] == "good"
        assert "disclaimer" in data
    
    def test_financial_analysis_with_market(self, client, mock_financial_result):
        """测试指定市场的财务分析"""
        with patch('app.api.v1.financial._get_financial_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_financial_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/financial",
                json={"symbol": "600519", "market": "cn"}
            )
        
        assert response.status_code == 200
        mock_analyzer.analyze.assert_called_once_with(symbol="600519", market="cn")
    
    def test_financial_analysis_error(self, client):
        """测试财务分析错误处理"""
        with patch('app.api.v1.financial._get_financial_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(side_effect=Exception("API Error"))
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/financial",
                json={"symbol": "INVALID"}
            )
        
        assert response.status_code == 500


class TestValuationAnalysisAPI:
    """测试估值分析 API"""
    
    def test_valuation_analysis_success(self, client, mock_valuation_result):
        """测试估值分析成功"""
        with patch('app.api.v1.financial._get_valuation_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_valuation_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/valuation",
                json={"symbol": "AAPL"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["current_price"] == 150.0
        assert data["data"]["valuation_level"] == "fairly_valued"
        assert "disclaimer" in data
    
    def test_valuation_analysis_error(self, client):
        """测试估值分析错误处理"""
        with patch('app.api.v1.financial._get_valuation_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(side_effect=Exception("Valuation Error"))
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/valuation",
                json={"symbol": "INVALID"}
            )
        
        assert response.status_code == 500


class TestTechnicalAnalysisAPI:
    """测试技术分析 API"""
    
    def test_technical_analysis_success(self, client, mock_technical_result):
        """测试技术分析成功"""
        with patch('app.api.v1.financial._get_technical_indicators') as mock_get:
            mock_service = MagicMock()
            mock_service.analyze = AsyncMock(return_value=mock_technical_result)
            mock_get.return_value = mock_service
            
            response = client.post(
                "/api/v1/financial/analysis/technical",
                json={"symbol": "AAPL"}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["technical_score"] == 65.0
        assert data["data"]["overall_signal"] == "buy"
        assert len(data["data"]["buy_signals"]) == 2
        assert "disclaimer" in data
    
    def test_technical_analysis_error(self, client):
        """测试技术分析错误处理"""
        with patch('app.api.v1.financial._get_technical_indicators') as mock_get:
            mock_service = MagicMock()
            mock_service.analyze = AsyncMock(side_effect=Exception("Technical Error"))
            mock_get.return_value = mock_service
            
            response = client.post(
                "/api/v1/financial/analysis/technical",
                json={"symbol": "INVALID"}
            )
        
        assert response.status_code == 500


class TestComprehensiveAnalysisAPI:
    """测试综合分析 API"""
    
    def test_comprehensive_analysis_success(
        self, 
        client, 
        mock_financial_result, 
        mock_valuation_result, 
        mock_technical_result
    ):
        """测试综合分析成功"""
        # 直接 mock run_parallel_analysis 返回结果
        mock_result = {
            "symbol": "AAPL",
            "market": "us",
            "financial": mock_financial_result.to_dict(),
            "valuation": mock_valuation_result.to_dict(),
            "technical": mock_technical_result.to_dict(),
            "summary": "财务状况良好",
            "generated_at": "2026-01-17T00:00:00",
            "cache_hits": [],
            "elapsed_seconds": 0.5,
        }
        
        with patch('app.services.financial.cache.run_parallel_analysis', new_callable=AsyncMock) as mock_parallel:
            mock_parallel.return_value = mock_result
            
            response = client.post(
                "/api/v1/financial/analysis/comprehensive",
                json={"symbol": "AAPL", "include_technical": True}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["market"] == "us"
        assert data["data"]["financial"] is not None
        assert data["data"]["valuation"] is not None
        assert data["data"]["technical"] is not None
        assert "generated_at" in data["data"]
        assert "disclaimer" in data
    
    def test_comprehensive_analysis_without_technical(
        self, 
        client, 
        mock_financial_result, 
        mock_valuation_result
    ):
        """测试不包含技术分析的综合分析"""
        mock_result = {
            "symbol": "AAPL",
            "market": "us",
            "financial": mock_financial_result.to_dict(),
            "valuation": mock_valuation_result.to_dict(),
            "technical": None,
            "summary": "",
            "generated_at": "2026-01-17T00:00:00",
            "cache_hits": [],
            "elapsed_seconds": 0.3,
        }
        
        with patch('app.services.financial.cache.run_parallel_analysis', new_callable=AsyncMock) as mock_parallel:
            mock_parallel.return_value = mock_result
            
            response = client.post(
                "/api/v1/financial/analysis/comprehensive",
                json={"symbol": "AAPL", "include_technical": False}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # 结果中技术分析应为 None
        assert data["data"]["technical"] is None
        # 确认调用时 include_technical=False
        mock_parallel.assert_called_once()
        call_kwargs = mock_parallel.call_args[1]
        assert call_kwargs["include_technical"] is False
    
    def test_comprehensive_analysis_partial_failure(
        self, 
        client, 
        mock_financial_result
    ):
        """测试综合分析部分失败"""
        # 模拟部分分析失败的情况
        mock_result = {
            "symbol": "AAPL",
            "market": "us",
            "financial": mock_financial_result.to_dict(),
            "valuation": {"error": "Valuation Failed"},
            "technical": {"error": "Technical Failed"},
            "summary": "",
            "generated_at": "2026-01-17T00:00:00",
            "cache_hits": [],
            "elapsed_seconds": 0.2,
        }
        
        with patch('app.services.financial.cache.run_parallel_analysis', new_callable=AsyncMock) as mock_parallel:
            mock_parallel.return_value = mock_result
            
            response = client.post(
                "/api/v1/financial/analysis/comprehensive",
                json={"symbol": "AAPL", "include_technical": True}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # 即使部分失败，也应该返回成功
        assert data["success"] is True
        assert data["data"]["financial"] is not None
        assert data["data"]["valuation"].get("error") == "Valuation Failed"
        assert data["data"]["technical"].get("error") == "Technical Failed"


# ============================================================
# Integration Tests
# ============================================================

class TestAPIIntegration:
    """API 集成测试"""
    
    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/api/v1/financial/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["service"] == "financial"
        assert "timestamp" in data
    
    def test_invalid_request_body(self, client):
        """测试无效请求体"""
        response = client.post(
            "/api/v1/financial/analysis/financial",
            json={}  # 缺少必需的 symbol
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_request_with_extra_fields(self, client, mock_financial_result):
        """测试带额外字段的请求"""
        with patch('app.api.v1.financial._get_financial_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_financial_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/financial",
                json={
                    "symbol": "AAPL",
                    "extra_field": "should_be_ignored"
                }
            )
        
        # 额外字段应该被忽略
        assert response.status_code == 200


# ============================================================
# Response Format Tests
# ============================================================

class TestResponseFormat:
    """测试响应格式"""
    
    def test_financial_response_structure(self, client, mock_financial_result):
        """测试财务分析响应结构"""
        with patch('app.api.v1.financial._get_financial_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_financial_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/financial",
                json={"symbol": "AAPL"}
            )
        
        data = response.json()
        
        # 验证顶层结构
        assert "success" in data
        assert "data" in data
        assert "disclaimer" in data
        
        # 验证 data 结构
        result_data = data["data"]
        assert "symbol" in result_data
        assert "overall_score" in result_data
        assert "health_level" in result_data
        assert "profitability" in result_data
        assert "growth" in result_data
        assert "solvency" in result_data
        assert "efficiency" in result_data
        assert "cash_flow" in result_data
        assert "strengths" in result_data
        assert "weaknesses" in result_data
        assert "key_risks" in result_data
    
    def test_valuation_response_structure(self, client, mock_valuation_result):
        """测试估值分析响应结构"""
        with patch('app.api.v1.financial._get_valuation_analyzer') as mock_get:
            mock_analyzer = MagicMock()
            mock_analyzer.analyze = AsyncMock(return_value=mock_valuation_result)
            mock_get.return_value = mock_analyzer
            
            response = client.post(
                "/api/v1/financial/analysis/valuation",
                json={"symbol": "AAPL"}
            )
        
        data = response.json()
        result_data = data["data"]
        
        assert "valuation_level" in result_data
        assert "valuation_score" in result_data
        assert "current_price" in result_data
        assert "target_price" in result_data
        assert "relative" in result_data
        assert "historical" in result_data
        assert "dcf" in result_data
    
    def test_technical_response_structure(self, client, mock_technical_result):
        """测试技术分析响应结构"""
        with patch('app.api.v1.financial._get_technical_indicators') as mock_get:
            mock_service = MagicMock()
            mock_service.analyze = AsyncMock(return_value=mock_technical_result)
            mock_get.return_value = mock_service
            
            response = client.post(
                "/api/v1/financial/analysis/technical",
                json={"symbol": "AAPL"}
            )
        
        data = response.json()
        result_data = data["data"]
        
        assert "overall_signal" in result_data
        assert "technical_score" in result_data
        assert "trend" in result_data
        assert "momentum" in result_data
        assert "volatility" in result_data
        assert "volume" in result_data
        assert "support_levels" in result_data
        assert "resistance_levels" in result_data
        assert "buy_signals" in result_data
        assert "sell_signals" in result_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
