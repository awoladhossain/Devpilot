from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import RefreshTokenRequest, TokenResponse
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
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    return UserRead.model_validate(service.register(data))


@router.post("/login", response_model=TokenResponse)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user = service.authenticate(form.username, form.password)
    return service.issue_access_token(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    data: RefreshTokenRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    return service.refresh(data.refresh_token)
