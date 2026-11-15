import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handler
from app.core.security_headers import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    settings = get_settings()
    level = settings.log_level.upper()
    logging.basicConfig(level=level)
    logging.getLogger().setLevel(level)
    logger.info("DevPilot starting (env=%s)", settings.app_env)


configure_logging()

docs_enabled = get_settings().app_env == "local"
app = FastAPI(
    title="DevPilot",
    version="0.1.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if docs_enabled else None,
)
app.add_middleware(SecurityHeadersMiddleware)
register_exception_handler(app)
app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
