import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import TokenResponse

INVALID_CREDENTIALS_MESSAGE = "Invalid credentials"


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def authenticate(self, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE)
        if not verify_password(password, user.password_hash) or not user.is_active:
            raise UnauthorizedError(INVALID_CREDENTIALS_MESSAGE)
        return user

    def issue_access_token(self, user: User) -> TokenResponse:
        minutes = get_settings().access_token_expire_minutes
        return TokenResponse(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
            expires_in=minutes * 60,  # convert to seconds
        )

    def refresh(self, refresh_token: str) -> TokenResponse:
        subject = decode_refresh_token(refresh_token)
        if subject is None:
            raise UnauthorizedError("Invalid or expired refresh token")
        try:
            user_id = uuid.UUID(subject)
        except ValueError:
            raise UnauthorizedError("Invalid or expired refresh token") from None
        user = self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Invalid or expired refresh token")
        return self.issue_access_token(user)
