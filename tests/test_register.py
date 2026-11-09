import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User

pytestmark = pytest.mark.integration

URL = "/api/v1/auth/register"
VALID = {"email": "Awolad@Example.com", "password": "correct-horse-battery"}


def test_register_success(client) -> None:
    response = client.post(URL, json=VALID)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "awolad@example.com"
    assert "password" not in body and "password_hash" not in body


def test_register_stores_argon2_hash(client, db: Session) -> None:
    client.post(URL, json=VALID)
    user = db.scalar(select(User))
    assert user is not None
    assert user.password_hash.startswith("$argon2id$")
    assert VALID["password"] not in user.password_hash


def test_register_duplicate_email_conflicts(client) -> None:
    client.post(URL, json=VALID)
    response = client.post(URL, json={**VALID, "email": "awolad@example.com"})
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


@pytest.mark.parametrize(
    "payload",
    [
        {"email": "not-an-email", "password": "correct-horse-battery"},
        {"email": "a@example.com", "password": "short"},
        {"email": "a@example.com", "password": "x" * 129},
        {"email": "a@example.com"},
    ],
)
def test_register_invalid_input(client, payload) -> None:
    assert client.post(URL, json=payload).status_code == 422
