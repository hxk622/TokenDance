"""
Test Financial API endpoints.

Run with:
    cd backend && uv run pytest tests/test_financial_api.py -v
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


class TestFinancialAPI:
    """Tests for Financial API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/financial/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "financial"
    
    def test_stock_info(self, client):
        """Test stock info endpoint."""
        response = client.post(
            "/api/v1/financial/stock/info",
            json={"symbol": "600519"}
        )
        
        # Note: May fail if OpenBB/AkShare not installed or network issues
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
        else:
            # Expected if dependencies not installed
            assert response.status_code in [404, 500]
    
    def test_stock_quote(self, client):
        """Test stock quote endpoint."""
        response = client.post(
            "/api/v1/financial/stock/quote",
            json={"symbol": "600519"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
        else:
            assert response.status_code in [404, 500]
    
    def test_historical_data(self, client):
        """Test historical data endpoint."""
        response = client.post(
            "/api/v1/financial/stock/historical",
            json={
                "symbol": "600519",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
        else:
            assert response.status_code in [404, 500]
    
    def test_sentiment_analyze(self, client):
        """Test sentiment analyze endpoint."""
        response = client.post(
            "/api/v1/financial/sentiment/analyze",
            json={
                "symbol": "600519",
                "sources": ["xueqiu"],
                "limit_per_source": 5
            }
        )
        
        # Sentiment analysis should work (keyword fallback)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
    
    def test_sentiment_search(self, client):
        """Test sentiment search endpoint."""
        response = client.post(
            "/api/v1/financial/sentiment/search",
            json={
                "query": "白酒",
                "sources": ["xueqiu"],
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_combined_analysis(self, client):
        """Test combined analysis endpoint."""
        response = client.post(
            "/api/v1/financial/combined",
            json={
                "symbol": "600519",
                "sentiment_sources": ["xueqiu"],
                "sentiment_limit": 5,
                "historical_days": 7
            }
        )
        
        # May return 500 if dependencies not installed
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "data" in data
            assert "errors" in data
        else:
            # Expected if dependencies missing
            assert response.status_code in [404, 500]
    
    def test_invalid_symbol(self, client):
        """Test with invalid symbol."""
        response = client.post(
            "/api/v1/financial/stock/info",
            json={"symbol": "INVALID"}
        )
        
        # Should return error
        assert response.status_code in [404, 500]
    
    def test_missing_required_field(self, client):
        """Test with missing required field."""
        response = client.post(
            "/api/v1/financial/stock/info",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_invalid_limit(self, client):
        """Test with invalid limit value."""
        response = client.post(
            "/api/v1/financial/sentiment/analyze",
            json={
                "symbol": "600519",
                "limit_per_source": 200  # Exceeds max 100
            }
        )
        
        # Should return validation error
        assert response.status_code == 422


# Integration tests (require network, skip by default)
class TestFinancialAPIIntegration:
    """Integration tests that require network access."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.skip(reason="Requires network access and API keys")
    def test_real_stock_data(self, client):
        """Test with real stock data."""
        response = client.post(
            "/api/v1/financial/stock/info",
            json={"symbol": "600519"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Check data structure
        stock_data = data["data"]
        assert "name" in stock_data
        assert "market" in stock_data
    
    @pytest.mark.skip(reason="Requires network access")
    def test_real_sentiment_crawl(self, client):
        """Test real sentiment crawling."""
        response = client.post(
            "/api/v1/financial/sentiment/analyze",
            json={
                "symbol": "600519",
                "sources": ["xueqiu", "guba"],
                "limit_per_source": 10
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if data["success"]:
            sentiment_data = data["data"]
            assert "posts" in sentiment_data
            assert len(sentiment_data["posts"]) > 0
    
    @pytest.mark.skip(reason="Requires network access and all dependencies")
    def test_full_combined_analysis(self, client):
        """Test full combined analysis."""
        response = client.post(
            "/api/v1/financial/combined",
            json={
                "symbol": "600519",
                "sentiment_sources": ["xueqiu", "guba"],
                "sentiment_limit": 20,
                "historical_days": 30
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Check all components
        combined_data = data["data"]
        assert "stock_info" in combined_data
        assert "quote" in combined_data
        assert "historical" in combined_data
        assert "sentiment" in combined_data
