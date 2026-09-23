"""
Health and startup tests for the CloudContextGuard backend.

Uses the project's actual portable configuration (app.core.paths /
app.core.config) - no machine-specific values, no mocked paths.
"""

from fastapi.testclient import TestClient

from app.core.paths import DATABASE_PATH
from app.db.database import is_database_connected
from app.main import app


def test_api_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "CloudContextGuard API"
    assert body["database"] == "connected"


def test_root_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["database"] == "connected"


def test_database_connectivity() -> None:
    assert is_database_connected() is True


def test_application_startup_creates_database() -> None:
    with TestClient(app):
        pass
    assert DATABASE_PATH.exists()


def test_swagger_docs_available() -> None:
    with TestClient(app) as client:
        docs_response = client.get("/api/docs")
        openapi_response = client.get("/api/openapi.json")
    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
