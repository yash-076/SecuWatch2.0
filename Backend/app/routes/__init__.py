from app.routes.ai import router as ai_router
from app.routes.alerts import router as alerts_router
from app.routes.auth import router as auth_router
from app.routes.devices import router as devices_router
from app.routes.logs import router as logs_router
from app.routes.websocket import router as websocket_router

__all__ = ["ai_router", "alerts_router", "auth_router", "devices_router", "logs_router", "websocket_router"]
