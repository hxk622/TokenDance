"""
Notifications API Tests

Ensure notification routes are registered.
"""
import pytest
from fastapi.testclient import TestClient


class TestNotificationRoutes:
    """Test notifications API routes registration."""

    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)

    def test_notifications_list_route_registered(self, client):
        response = client.get("/api/v1/notifications")
        # Auth required; should not be 404
        assert response.status_code in {401, 403}

    def test_unread_count_route_registered(self, client):
        response = client.get("/api/v1/notifications/unread-count")
        assert response.status_code in {401, 403}

    def test_mark_read_route_registered(self, client):
        response = client.post("/api/v1/notifications/test-id/read")
        assert response.status_code in {401, 403}

    def test_mark_all_read_route_registered(self, client):
        response = client.post("/api/v1/notifications/read-all")
        assert response.status_code in {401, 403}

    def test_delete_route_registered(self, client):
        response = client.delete("/api/v1/notifications/test-id")
        assert response.status_code in {401, 403}
