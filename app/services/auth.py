import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

INVALID_CREDENTIALS = "Invalid email or password"
INVALID_REFRESH = "Invalid refresh token"


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)  # timing সমান রাখতে
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not verify_password(password, user.password_hash) or not user.is_active:
            raise UnauthorizedError(INVALID_CREDENTIALS)
        return user

    def issue_tokens(self, user: User) -> TokenResponse:
        response = self._build_response(user.id, family_id=uuid.uuid4())
        self.db.commit()
        return response

    issue_access_token = issue_tokens

    def refresh(self, raw_token: str) -> TokenResponse:
        now = datetime.now(UTC)
        row = self.tokens.get_by_hash_for_update(hash_token(raw_token))
        if row is None:
            raise UnauthorizedError(INVALID_REFRESH)

        if row.revoked_at is not None:
            # revoked token আবার এসেছে: চুরির সম্ভাবনা, পুরো family বন্ধ
            self.tokens.revoke_family(row.family_id, now)
            self.db.commit()
            raise UnauthorizedError(INVALID_REFRESH)

        user = self.users.get_by_id(row.user_id)
        if row.expires_at <= now or user is None or not user.is_active:
            self.tokens.revoke_family(row.family_id, now)
            self.db.commit()
            raise UnauthorizedError(INVALID_REFRESH)

        row.revoked_at = now  # rotation: পুরোনোটা শেষ
        response = self._build_response(user.id, family_id=row.family_id)
        self.db.commit()
        return response

    def logout(self, raw_token: str) -> None:
        row = self.tokens.get_by_hash_for_update(hash_token(raw_token))
        if row is not None and row.revoked_at is None:
            self.tokens.revoke_family(row.family_id, datetime.now(UTC))
            self.db.commit()

    def _build_response(self, user_id: uuid.UUID, family_id: uuid.UUID) -> TokenResponse:
        settings = get_settings()
        raw = generate_refresh_token()
        self.tokens.add(
            RefreshToken(
                user_id=user_id,
                family_id=family_id,
                token_hash=hash_token(raw),
                expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
            )
        )
        return TokenResponse(
            access_token=create_access_token(str(user_id)),
            refresh_token=raw,
            expires_in=settings.access_token_expire_minutes * 60,
        )
