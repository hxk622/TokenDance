"""
Test Financial Aha Moment API endpoints.

Run with:
    cd backend && uv run pytest tests/api/test_financial_aha_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestFinancialAhaAPI:
    """Tests for Financial Aha Moment API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    # ============== Benchmark Percentile Tests ==============

    def test_benchmark_percentile_basic(self, client):
        """Test benchmark percentile endpoint."""
        response = client.post(
            "/api/v1/financial/benchmark/percentile",
            json={
                "symbol": "600519",
                "metrics": ["roe", "gross_margin"],
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # data structure: {symbol, benchmarks, dupont?}
        assert data["data"]["symbol"] == "600519"
        assert "benchmarks" in data["data"]
        assert isinstance(data["data"]["benchmarks"], list)
        assert len(data["data"]["benchmarks"]) == 2

    def test_benchmark_percentile_with_dupont(self, client):
        """Test benchmark percentile returns DuPont for ROE."""
        response = client.post(
            "/api/v1/financial/benchmark/percentile",
            json={
                "symbol": "600519",
                "metrics": ["roe"],
                "include_dupont": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # DuPont should be included when include_dupont=True
        assert "dupont" in data["data"]

    def test_benchmark_percentile_missing_symbol(self, client):
        """Test benchmark percentile with missing symbol."""
        response = client.post(
            "/api/v1/financial/benchmark/percentile",
            json={
                "metrics": ["roe"],
            }
        )

        assert response.status_code == 422  # Validation error

    def test_benchmark_percentile_empty_metrics(self, client):
        """Test benchmark percentile with empty metrics list."""
        response = client.post(
            "/api/v1/financial/benchmark/percentile",
            json={
                "symbol": "600519",
                "metrics": [],
            }
        )

        # Should either return error or empty result
        assert response.status_code in [200, 422]

    # ============== Peer Matrix Tests ==============

    def test_peer_matrix_basic(self, client):
        """Test peer comparison matrix endpoint."""
        response = client.post(
            "/api/v1/financial/peer/matrix",
            json={
                "symbol": "600519",
                "peer_symbols": ["000858", "000568"],
                "metrics": ["roe", "gross_margin", "revenue_growth"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_peer_matrix_auto_detect_peers(self, client):
        """Test peer matrix with auto-detected peers."""
        response = client.post(
            "/api/v1/financial/peer/matrix",
            json={
                "symbol": "600519",
                "peer_symbols": [],  # Auto-detect
                "metrics": ["roe", "gross_margin"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_peer_matrix_missing_metrics(self, client):
        """Test peer matrix with missing metrics."""
        response = client.post(
            "/api/v1/financial/peer/matrix",
            json={
                "symbol": "600519",
                "peer_symbols": ["000858"]
            }
        )

        # Should either use default metrics or return error
        assert response.status_code in [200, 422]

    # ============== Event Calendar Tests ==============

    def test_upcoming_events_basic(self, client):
        """Test upcoming events endpoint."""
        response = client.post(
            "/api/v1/financial/events/upcoming",
            json={
                "symbol": "600519",
                "days_ahead": 90
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        # data is EventCalendarResult.to_dict()
        assert "upcoming_events" in data["data"]

    def test_upcoming_events_with_filter(self, client):
        """Test upcoming events with event type filter."""
        response = client.post(
            "/api/v1/financial/events/upcoming",
            json={
                "symbol": "600519",
                "days_ahead": 90,
                "event_types": ["earnings", "dividend"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_upcoming_events_short_range(self, client):
        """Test upcoming events with short time range."""
        response = client.post(
            "/api/v1/financial/events/upcoming",
            json={
                "symbol": "600519",
                "days_ahead": 7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_historical_event_impact(self, client):
        """Test historical event impact endpoint."""
        response = client.post(
            "/api/v1/financial/events/historical-impact",
            json={
                "symbol": "600519",
                "event_type": "earnings",
                "lookback_years": 3
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_historical_impact_different_event_types(self, client):
        """Test historical impact with different event types."""
        event_types = ["earnings", "dividend", "guidance"]

        for event_type in event_types:
            response = client.post(
                "/api/v1/financial/events/historical-impact",
                json={
                    "symbol": "600519",
                    "event_type": event_type,
                    "lookback_years": 2
                }
            )

            assert response.status_code == 200

    # ============== Sentiment Pulse Tests ==============

    def test_sentiment_pulse_basic(self, client):
        """Test sentiment pulse endpoint."""
        response = client.post(
            "/api/v1/financial/sentiment/pulse",
            json={
                "symbol": "600519",
                "days": 7
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_sentiment_pulse_data_structure(self, client):
        """Test sentiment pulse returns correct data structure."""
        response = client.post(
            "/api/v1/financial/sentiment/pulse",
            json={
                "symbol": "600519",
                "days": 7
            }
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Check required fields - SentimentPulseResult.to_dict()
        assert "current_score" in data
        assert "current_level" in data

    def test_sentiment_pulse_different_periods(self, client):
        """Test sentiment pulse with different time periods."""
        periods = [3, 7, 14, 30]

        for days in periods:
            response = client.post(
                "/api/v1/financial/sentiment/pulse",
                json={
                    "symbol": "600519",
                    "days": days
                }
            )

            assert response.status_code == 200

    def test_sentiment_pulse_missing_symbol(self, client):
        """Test sentiment pulse with missing symbol."""
        response = client.post(
            "/api/v1/financial/sentiment/pulse",
            json={
                "days": 7
            }
        )

        assert response.status_code == 422

    # ============== Risk Propagation Tests ==============

    def test_risk_propagation_basic(self, client):
        """Test risk propagation endpoint."""
        response = client.post(
            "/api/v1/financial/risk/propagation",
            json={
                "symbol": "600519",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_risk_propagation_data_structure(self, client):
        """Test risk propagation returns correct data structure."""
        response = client.post(
            "/api/v1/financial/risk/propagation",
            json={
                "symbol": "600519",
            }
        )

        assert response.status_code == 200
        data = response.json()["data"]

        # Check required fields - RiskPropagationResult.to_dict()
        assert "total_risk_score" in data
        assert "incoming_risks" in data
        assert "outgoing_risks" in data

    def test_risk_propagation_multiple_symbols(self, client):
        """Test risk propagation with different symbols."""
        for symbol in ["600519", "000858"]:
            response = client.post(
                "/api/v1/financial/risk/propagation",
                json={
                    "symbol": symbol,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_risk_propagation_missing_symbol(self, client):
        """Test risk propagation with missing symbol."""
        response = client.post(
            "/api/v1/financial/risk/propagation",
            json={}
        )

        assert response.status_code == 422

    # ============== Cross-cutting Tests ==============

    def test_all_endpoints_handle_invalid_symbol(self, client):
        """Test all endpoints handle invalid symbol gracefully."""
        endpoints = [
            ("/api/v1/financial/benchmark/percentile", {
                "symbol": "INVALID",
                "metrics": ["roe"],
            }),
            ("/api/v1/financial/events/upcoming", {
                "symbol": "INVALID",
                "days_ahead": 30
            }),
            ("/api/v1/financial/sentiment/pulse", {
                "symbol": "INVALID",
                "days": 7
            }),
            ("/api/v1/financial/risk/propagation", {
                "symbol": "INVALID",
            }),
        ]

        for endpoint, payload in endpoints:
            response = client.post(endpoint, json=payload)
            # Should return either success (with mock data) or appropriate error
            assert response.status_code in [200, 400, 404, 500]

    def test_all_endpoints_handle_empty_body(self, client):
        """Test all endpoints handle empty request body."""
        endpoints = [
            "/api/v1/financial/benchmark/percentile",
            "/api/v1/financial/peer/matrix",
            "/api/v1/financial/events/upcoming",
            "/api/v1/financial/events/historical-impact",
            "/api/v1/financial/sentiment/pulse",
            "/api/v1/financial/risk/propagation",
        ]

        for endpoint in endpoints:
            response = client.post(endpoint, json={})
            # Should return validation error
            assert response.status_code == 422


class TestFinancialAhaAPIIntegration:
    """Integration tests that verify end-to-end flow."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_full_aha_moment_workflow(self, client):
        """Test complete Aha Moment data retrieval workflow."""
        symbol = "600519"

        # 1. Get benchmark percentiles
        response = client.post(
            "/api/v1/financial/benchmark/percentile",
            json={
            "symbol": symbol,
            "metrics": ["roe", "gross_margin"],
            }
        )
        assert response.status_code == 200
        percentiles = response.json()
        assert percentiles["success"] is True

        # 2. Get peer matrix
        response = client.post(
            "/api/v1/financial/peer/matrix",
            json={
                "symbol": symbol,
                "peer_symbols": ["000858"],
                "metrics": ["roe", "gross_margin"]
            }
        )
        assert response.status_code == 200
        peer_matrix = response.json()
        assert peer_matrix["success"] is True

        # 3. Get upcoming events
        response = client.post(
            "/api/v1/financial/events/upcoming",
            json={
                "symbol": symbol,
                "days_ahead": 90
            }
        )
        assert response.status_code == 200
        events = response.json()
        assert events["success"] is True

        # 4. Get sentiment pulse
        response = client.post(
            "/api/v1/financial/sentiment/pulse",
            json={
                "symbol": symbol,
                "days": 7
            }
        )
        assert response.status_code == 200
        sentiment = response.json()
        assert sentiment["success"] is True

        # 5. Get risk propagation
        response = client.post(
            "/api/v1/financial/risk/propagation",
            json={
                "symbol": symbol,
                "depth": 2
            }
        )
        assert response.status_code == 200
        risk = response.json()
        assert risk["success"] is True

        # All endpoints should work together
        print("✅ Full Aha Moment workflow completed successfully")
