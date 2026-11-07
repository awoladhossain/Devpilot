import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    settings = get_settings()
    level = settings.log_level.upper()
    logging.basicConfig(level=level)
    logging.getLogger().setLevel(level)
    logger.info("DevPilot starting (env=%s)", settings.app_env)


configure_logging()

app = FastAPI(title="DevPilot", version="0.1.0")
app.include_router(health_router)
