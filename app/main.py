import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handler

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    settings = get_settings()
    level = settings.log_level.upper()
    logging.basicConfig(level=level)
    logging.getLogger().setLevel(level)
    logger.info("DevPilot starting (env=%s)", settings.app_env)


configure_logging()

app = FastAPI(title="DevPilot", version="0.1.0")
register_exception_handler(app)
app.include_router(health_router)
app.include_router(api_router, prefix="/api/v1")
