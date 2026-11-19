"""
Unit and integration tests for FastAPI backend foundation.
"""

from fastapi.testclient import TestClient
from omnix.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify root status endpoint returns 200 and online status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "OMNIX Agent"
    assert data["status"] == "online"


def test_health_check():
    """Verify health endpoint returns valid schema and status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "OMNIX Agent"
    assert "version" in data
    assert "timestamp" in data


def test_custom_exception_handler():
    """Verify that domain exceptions trigger standardized JSON error payloads."""
    from omnix.core.exceptions import NotFoundException

    @app.get("/test-not-found-route")
    async def sample_route():
        raise NotFoundException(message="Item not found in inventory", details={"sku": "SKU-999"})

    response = client.get("/test-not-found-route")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True
    assert data["error_code"] == "RESOURCE_NOT_FOUND"
    assert data["message"] == "Item not found in inventory"
    assert data["details"]["sku"] == "SKU-999"
