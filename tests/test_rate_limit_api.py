import pytest

pytestmark = pytest.mark.integration

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
PASSWORD = "correct-horse-battery"


def attempt(client, email: str, password: str):
    return client.post(LOGIN, data={"username": email, "password": password})


def test_login_blocked_after_five_failures_per_email(client) -> None:
    client.post(REGISTER, json={"email": "a@example.com", "password": PASSWORD})
    for _ in range(5):
        assert attempt(client, "a@example.com", "wrong-password-123").status_code == 401
    blocked = attempt(client, "a@example.com", "wrong-password-123")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert blocked.json()["error"]["code"] == "rate_limited"
    # ঠিক password দিলেও এখন আটকাবে
    assert attempt(client, "a@example.com", PASSWORD).status_code == 429


def test_other_email_is_not_affected(client) -> None:
    for _ in range(5):
        attempt(client, "a@example.com", "wrong-password-123")
    assert attempt(client, "b@example.com", "wrong-password-123").status_code == 401


def test_register_is_rate_limited_per_ip(client) -> None:
    for i in range(5):
        response = client.post(REGISTER, json={"email": f"u{i}@example.com", "password": PASSWORD})
        assert response.status_code == 201
    response = client.post(REGISTER, json={"email": "u5@example.com", "password": PASSWORD})
    assert response.status_code == 429
