from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import ClientIP, Limiter
from app.db.session import get_db
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth import AuthService
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: Annotated[Session, Depends(get_db)]) -> UserService:
    return UserService(db)


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(
    data: UserCreate,
    ip: ClientIP,
    limiter: Limiter,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    limiter.check(f"register:ip:{ip}", limit=5, window_seconds=60)
    return UserRead.model_validate(service.register(data))


@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    ip: ClientIP,
    limiter: Limiter,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    limiter.check(f"login:ip:{ip}", limit=20, window_seconds=300)
    email = form.username.strip().lower()[:320]
    password = form.password.strip()[:256]
    limiter.check(f"login:email:{email}", limit=5, window_seconds=60)
    user = service.authenticate(email, password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return service.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshRequest,
    ip: ClientIP,
    limiter: Limiter,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    limiter.check(f"refresh:ip:{ip}", limit=10, window_seconds=60)
    return service.refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    data: RefreshRequest,
    ip: ClientIP,
    limiter: Limiter,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    limiter.check(f"logout:ip:{ip}", limit=10, window_seconds=60)
    service.logout(data.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
