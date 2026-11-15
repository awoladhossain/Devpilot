from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User

pytestmark = pytest.mark.integration

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/users/me"
CREDS = {"email": "awolad@example.com", "password": "correct-horse-battery"}


@pytest.fixture
def tokens(client) -> dict:
    client.post(REGISTER, json=CREDS)
    response = client.post(LOGIN, data={"username": CREDS["email"], "password": CREDS["password"]})
    return response.json()


def refresh(client, token: str):
    return client.post(REFRESH, json={"refresh_token": token})


def test_login_returns_refresh_token(tokens) -> None:
    assert tokens["refresh_token"]


def test_refresh_rotates_tokens(client, tokens) -> None:
    response = refresh(client, tokens["refresh_token"])
    assert response.status_code == 200
    new = response.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {new['access_token']}"}
    assert client.get(ME, headers=headers).status_code == 200


def test_only_hash_is_stored(client, db: Session, tokens) -> None:
    row = db.scalar(select(RefreshToken))
    assert row.token_hash == hash_token(tokens["refresh_token"])
    assert row.token_hash != tokens["refresh_token"]


def test_reusing_old_token_revokes_whole_family(client, tokens) -> None:
    new = refresh(client, tokens["refresh_token"]).json()
    assert refresh(client, tokens["refresh_token"]).status_code == 401  # reuse
    assert refresh(client, new["refresh_token"]).status_code == 401  # family শেষ


def test_logout_revokes_token(client, tokens) -> None:
    response = client.post(LOGOUT, json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 204
    assert refresh(client, tokens["refresh_token"]).status_code == 401


def test_logout_is_idempotent_and_hides_unknown_tokens(client, tokens) -> None:
    body = {"refresh_token": tokens["refresh_token"]}
    assert client.post(LOGOUT, json=body).status_code == 204
    assert client.post(LOGOUT, json=body).status_code == 204
    assert client.post(LOGOUT, json={"refresh_token": "x" * 40}).status_code == 204


def test_unknown_refresh_token_rejected(client) -> None:
    assert refresh(client, "x" * 40).status_code == 401


def test_expired_refresh_token_rejected(client, db: Session, tokens) -> None:
    row = db.scalar(select(RefreshToken))
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.flush()
    assert refresh(client, tokens["refresh_token"]).status_code == 401


def test_deactivated_user_cannot_refresh(client, db: Session, tokens) -> None:
    db.scalar(select(User)).is_active = False
    db.flush()
    assert refresh(client, tokens["refresh_token"]).status_code == 401
