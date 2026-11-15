from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_security_headers_on_api_response() -> None:
    response = client.get("/api/v1/users/me")  # 401, তবু header থাকবে
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert response.headers["cache-control"] == "no-store"


def test_docs_page_is_not_broken_by_csp() -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    assert "content-security-policy" not in response.headers


def test_health_has_headers_but_is_cacheable_policy_untouched() -> None:
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "cache-control" not in response.headers
