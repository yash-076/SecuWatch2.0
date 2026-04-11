import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, ensure_database_exists
from app.models import Alert, Device, Log, RefreshToken, User
from app.routes.ai import router as ai_router
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router
from app.routes.devices import router as devices_router
from app.routes.heartbeat import router as heartbeat_router
from app.routes.logs import router as logs_router
from app.routes.websocket import router as websocket_router
from app.services.kafka_producer import ensure_topics_exist
from app.services.websocket_manager import ws_manager

app = FastAPI(title="SecuWatch 2.0 API")
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    log_level = getattr(logging, settings.app_log_level.upper(), logging.DEBUG)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )

# Test frontend runs on a separate local origin, so enable broad CORS for dev/testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    _configure_logging()
    logger.info("Application logging configured at level=%s", settings.app_log_level.upper())

    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    ws_manager.set_event_loop(asyncio.get_running_loop())
    try:
        ensure_topics_exist()
    except Exception as exc:
        logger.warning(f"Kafka topic setup skipped: {exc}")


app.include_router(auth_router)
app.include_router(devices_router)
app.include_router(heartbeat_router)
app.include_router(alerts_router)
app.include_router(logs_router)
app.include_router(websocket_router)
app.include_router(ai_router)
