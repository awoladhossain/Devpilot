import uuid
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.rate_limit import InMemoryRateLimiter, get_rate_limiter
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

# auto_error=False to avoid raising an error if the token is invalid

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if token is None:
        raise UnauthorizedError("Not authenticated")
    subject = decode_access_token(token)
    if subject is None:
        raise UnauthorizedError("Invalid or expired token")
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        raise UnauthorizedError("Invalid or expired token") from None
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


ClientIP = Annotated[str, Depends(client_ip)]
Limiter = Annotated[InMemoryRateLimiter, Depends(get_rate_limiter)]
