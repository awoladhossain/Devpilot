import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration
client = TestClient(app)


def test_health_db_ok() -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
