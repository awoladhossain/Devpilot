from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-only-insecure-secret-do-not-use-in-prod"

REFRESH_TOKEN_EXPIRE_DAYS: int = 14


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://devpilot:devpilot@localhost:5432/devpilot"
    secret_key: str = DEV_SECRET_KEY
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 30  # 30 days
    refresh_token_expire_days: int = 14

    @model_validator(mode="after")
    def check_secret_key(self) -> Self:
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        if self.app_env != "local" and self.secret_key == DEV_SECRET_KEY:
            raise ValueError(
                "Secret key must be different from DEV_SECRET_KEY in non-local environment"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
