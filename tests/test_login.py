import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.user import User

pytestmark = pytest.mark.integration

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/users/me"
CREDS = {"email": "awolad@example.com", "password": "correct-horse-battery"}


@pytest.fixture
def user_id(client) -> str:
    return client.post(REGISTER, json=CREDS).json()["id"]


def do_login(client, password: str = CREDS["password"], email: str = CREDS["email"]):
    return client.post(LOGIN, data={"username": email, "password": password})


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client, user_id) -> None:
    response = do_login(client)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 900
    assert body["access_token"]


def test_wrong_password_and_unknown_email_look_identical(client, user_id) -> None:
    wrong_password = do_login(client, password="wrong-password-123")
    unknown_email = do_login(client, email="nobody@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_inactive_user_cannot_login(client, db: Session, user_id) -> None:
    user = db.scalar(select(User))
    user.is_active = False
    db.flush()
    assert do_login(client).status_code == 401


def test_me_requires_token(client) -> None:
    response = client.get(ME)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_with_valid_token(client, user_id) -> None:
    token = do_login(client).json()["access_token"]
    response = client.get(ME, headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["email"] == CREDS["email"]


def test_me_rejects_expired_token(client, user_id) -> None:
    token = create_access_token(user_id, timedelta(seconds=-1))
    assert client.get(ME, headers=bearer(token)).status_code == 401


def test_me_rejects_token_signed_with_other_secret(client, user_id) -> None:
    now = datetime.now(UTC)
    payload = {"sub": user_id, "exp": now + timedelta(minutes=5), "type": "access"}
    forged = jwt.encode(payload, "x" * 40, algorithm="HS256")
    assert client.get(ME, headers=bearer(forged)).status_code == 401


def test_me_rejects_alg_none_token(client, user_id) -> None:
    now = datetime.now(UTC)
    payload = {"sub": user_id, "exp": now + timedelta(minutes=5), "type": "access"}
    forged = jwt.encode(payload, key=None, algorithm="none")
    assert client.get(ME, headers=bearer(forged)).status_code == 401


def test_me_rejects_token_for_deleted_user(client) -> None:
    token = create_access_token(str(uuid.uuid4()))
    assert client.get(ME, headers=bearer(token)).status_code == 401
