"""Basic health check and warmup tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify health probe returns status ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ml-api"}


def test_warmup_endpoint() -> None:
    """Verify warmup probe returns ready."""
    response = client.post("/api/v1/health/warmup")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
